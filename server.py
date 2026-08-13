from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import httpx
from fastapi import Cookie, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from config_loader import BASE_DIR, settings
from auth_store import AuthStore
from content import BUDGET_LABELS, PLACE_ROUTES, build_flow, city_content, social_relief
from services.amap_client import AmapClient, AmapError
from services.kimi_client import KimiClient, KimiError


STATIC_DIR = BASE_DIR / "static"
HELP_WALL_PATH = BASE_DIR / "data" / "help_wall.json"
DATABASE_PATH = BASE_DIR / "data" / "guicheng.db"
SESSION_COOKIE = "guicheng_session"

app = FastAPI(title="归程", version="4.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

amap_client = AmapClient(settings)
kimi_client = KimiClient(settings)
recommendation_cache: dict[str, tuple[float, dict[str, Any]]] = {}
recommendation_locks: dict[str, asyncio.Lock] = {}
community_cache: dict[str, tuple[float, dict[str, Any]]] = {}
community_locks: dict[str, asyncio.Lock] = {}
help_wall_lock = asyncio.Lock()
auth_store = AuthStore(DATABASE_PATH)


class FlowRequest(BaseModel):
    legal_confirmed: bool
    place: Literal["hospital", "home", "public", "care"]
    budget: Literal["relief", "under1000", "1000to5000", "over5000", "unsure"]
    city: str = Field(default=settings.default_city, min_length=1, max_length=30)
    note: str = Field(default="", max_length=500)
    personalize: bool = False

    @field_validator("city", "note")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.split())


class RecommendationRequest(BaseModel):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    city: str = Field(default=settings.default_city, min_length=1, max_length=30)
    budget: Literal["relief", "under1000", "1000to5000", "over5000", "unsure"]
    note: str = Field(default="", max_length=500)

    @field_validator("city", "note")
    @classmethod
    def clean_recommendation_text(cls, value: str) -> str:
        return " ".join(value.split())


class NearbyRequest(BaseModel):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    city: str = Field(default=settings.default_city, min_length=1, max_length=30)

    @field_validator("city")
    @classmethod
    def clean_city(cls, value: str) -> str:
        return " ".join(value.split())


class LocationNormalizeRequest(BaseModel):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)


class HelpPostRequest(BaseModel):
    alias: str = Field(default="一位家属", min_length=1, max_length=20)
    city: str = Field(default=settings.default_city, min_length=1, max_length=30)
    topic: Literal["跑腿陪同", "流程经验", "材料核对", "情绪支持", "其他"]
    content: str = Field(min_length=4, max_length=280)

    @field_validator("alias", "city", "content")
    @classmethod
    def clean_post_text(cls, value: str) -> str:
        return " ".join(value.split())


class HelpReplyRequest(BaseModel):
    alias: str = Field(default="一位同行者", min_length=1, max_length=20)
    content: str = Field(min_length=2, max_length=240)

    @field_validator("alias", "content")
    @classmethod
    def clean_reply_text(cls, value: str) -> str:
        return " ".join(value.split())


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        clean = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", clean):
            raise ValueError("请输入有效邮箱")
        return clean

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str) -> str:
        return " ".join(value.split())


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class ProgressRequest(BaseModel):
    city: str = Field(min_length=1, max_length=30)
    legal_confirmed: bool
    answers: Dict[str, Any]
    flow: Optional[Dict[str, Any]] = None
    completed: List[str] = Field(default_factory=list, max_length=20)
    checks: Dict[str, List[int]] = Field(default_factory=dict)
    mode: Literal["standard", "elder"] = "standard"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": "4.0.0",
        "services": {
            "amap": "configured" if settings.amap_ready else "missing",
            "kimi": "configured" if settings.kimi_ready else "missing",
        },
        "default_city": settings.default_city,
    }


def _session_response(payload: dict[str, Any], token: str, status_code: int = 200) -> JSONResponse:
    response = JSONResponse(payload, status_code=status_code)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return response


def _require_user(token: Optional[str]) -> dict[str, Any]:
    user = auth_store.user_for_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


@app.post("/api/auth/register", status_code=201)
async def register(payload: RegisterRequest) -> JSONResponse:
    try:
        user = await asyncio.to_thread(
            auth_store.create_user, payload.email, payload.password, payload.display_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    token = await asyncio.to_thread(auth_store.create_session, user["id"])
    return _session_response({"user": user}, token, status_code=201)


@app.post("/api/auth/login")
async def login(payload: LoginRequest) -> JSONResponse:
    user = await asyncio.to_thread(auth_store.authenticate, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码不正确")
    token = await asyncio.to_thread(auth_store.create_session, user["id"])
    return _session_response({"user": user}, token)


@app.post("/api/auth/logout")
async def logout(guicheng_session: Optional[str] = Cookie(default=None)) -> JSONResponse:
    await asyncio.to_thread(auth_store.delete_session, guicheng_session)
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@app.get("/api/auth/me")
async def current_user(guicheng_session: Optional[str] = Cookie(default=None)) -> dict[str, Any]:
    user = auth_store.user_for_session(guicheng_session)
    return {"user": user}


@app.get("/api/account/progress")
async def account_progress(guicheng_session: Optional[str] = Cookie(default=None)) -> dict[str, Any]:
    user = _require_user(guicheng_session)
    return {"progress": await asyncio.to_thread(auth_store.load_progress, user["id"])}


@app.put("/api/account/progress")
async def save_account_progress(
    payload: ProgressRequest,
    guicheng_session: Optional[str] = Cookie(default=None),
) -> dict[str, Any]:
    user = _require_user(guicheng_session)
    await asyncio.to_thread(auth_store.save_progress, user["id"], payload.model_dump())
    return {"saved": True, "updated_at": int(time.time())}


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' https://unpkg.com; "
        "style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; "
        "font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    return response


@app.post("/api/generate-flow")
async def generate_flow(payload: FlowRequest) -> dict[str, Any]:
    if not payload.legal_confirmed:
        raise HTTPException(status_code=400, detail="请先完成直系亲属或授权确认")
    flow = build_flow(payload.place, payload.budget, payload.city, payload.note)
    flow["note"] = ""
    fallback_personalization = {
        "summary": f"已按{flow['place_label']}和“{flow['budget_label']}”整理五步路径；机构与价格将在第 3 步结合位置联网核验。",
        "first_action": flow["nodes"][0]["intro"],
        "priority_node_ids": ["confirm", "certificate"],
        "generated_by": "rules",
    }
    flow["personalization"] = fallback_personalization
    if payload.personalize and settings.kimi_ready:
        try:
            personalized = await asyncio.wait_for(
                kimi_client.personalize_sop(
                    city=payload.city,
                    place_label=flow["place_label"],
                    budget_label=flow["budget_label"],
                    note=_redact_user_note(payload.note),
                    nodes=flow["nodes"],
                    city_facts=city_content(payload.city),
                ),
                timeout=58,
            )
            flow["personalization"] = personalized["personalization"]
            overrides = {item["id"]: item for item in personalized.get("nodes", [])}
            for node in flow["nodes"]:
                if node["id"] in overrides:
                    node["personalized"] = overrides[node["id"]]
        except (KimiError, asyncio.TimeoutError, httpx.HTTPError):
            pass
    return flow


@app.post("/api/recommendations")
async def recommendations(payload: RecommendationRequest) -> dict[str, Any]:
    key = "|".join(
        [
            f"{payload.longitude:.3f}",
            f"{payload.latitude:.3f}",
            payload.city,
            payload.budget,
            hashlib.sha256(payload.note.encode("utf-8")).hexdigest()[:16],
        ]
    )
    cached = recommendation_cache.get(key)
    if cached and cached[0] > time.time():
        return {**cached[1], "cache_hit": True}

    lock = recommendation_locks.setdefault(key, asyncio.Lock())
    async with lock:
        cached = recommendation_cache.get(key)
        if cached and cached[0] > time.time():
            return {**cached[1], "cache_hit": True}
        result = await _build_recommendations(payload)
        cache_seconds = (
            settings.recommendation_cache_seconds
            if result.get("verification_status") == "verified"
            else 60
        )
        recommendation_cache[key] = (
            time.time() + cache_seconds,
            result,
        )
        return {**result, "cache_hit": False}


@app.post("/api/facilities/nearby")
async def nearby_facilities(payload: NearbyRequest) -> dict[str, Any]:
    try:
        candidates = await amap_client.nearby_funeral_homes(
            payload.longitude, payload.latitude, payload.city, limit=6
        )
    except AmapError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="地图服务暂时不可用") from exc
    return {
        "generated_at": int(time.time()),
        "city": payload.city,
        "origin": {
            "longitude": payload.longitude,
            "latitude": payload.latitude,
        },
        "candidates": [
            {
                **candidate,
                "official_status": "unverified",
                "official_status_note": "正在联网核验",
                "price_status": "phone_required",
                "price_items": [],
                "fit_for_budget": "uncertain",
                "value_reason": "高德已返回位置与距离；政府记录和价目正在联网核验。",
                "call_to_confirm": [],
                "cautions": [],
            }
            for candidate in candidates
        ],
        "summary": "已按高德距离排列，Kimi 正在检索政府记录和价目。",
        "recommended_poi_id": None,
        "decision_basis": ["当前顺序仅根据高德直线距离"],
        "sources": [],
        "verification_status": "checking",
        "verification_notice": "候选已找到，请等待 Kimi 完成联网核验。",
    }


@app.get("/api/geocode")
async def geocode(
    address: str = Query(min_length=2, max_length=100),
    city: str = Query(default=settings.default_city, min_length=1, max_length=30),
) -> dict[str, Any]:
    try:
        return await amap_client.geocode(
            " ".join(address.split()), " ".join(city.split())
        )
    except AmapError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="地点查找暂时不可用") from exc


@app.post("/api/location/normalize")
async def normalize_location(payload: LocationNormalizeRequest) -> dict[str, Any]:
    try:
        return await amap_client.normalize_gps_location(
            payload.longitude, payload.latitude
        )
    except AmapError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="定位校正暂时不可用") from exc


async def _build_recommendations(payload: RecommendationRequest) -> dict[str, Any]:
    try:
        candidates = await amap_client.nearby_funeral_homes(
            payload.longitude, payload.latitude, payload.city
        )
    except AmapError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="地图服务暂时不可用") from exc

    if not candidates:
        return {
            "generated_at": int(time.time()),
            "city": payload.city,
            "budget": payload.budget,
            "candidates": [],
            "summary": "附近未检索到名称明确的殡仪馆，请换一个定位或拨打当地政务热线查询。",
            "recommended_poi_id": None,
            "decision_basis": [],
            "sources": [],
            "verification_status": "no_candidates",
            "verification_notice": "高德附近搜索未返回可用候选。",
        }

    verification_status = "verified"
    verification_notice = "Kimi 已完成联网检索；页面会区分已核对证据与仍需电话确认的内容。"
    try:
        verification = await asyncio.wait_for(
            kimi_client.verify_facilities(
                candidates,
                payload.city,
                BUDGET_LABELS[payload.budget],
                _redact_user_note(payload.note),
            ),
            timeout=65,
        )
    except (KimiError, asyncio.TimeoutError) as exc:
        try:
            verification = await asyncio.wait_for(
                kimi_client.verify_official_sources_only(
                    candidates, payload.city
                ),
                timeout=25,
            )
            has_official_evidence = any(
                item.get("official_status") == "verified"
                for item in verification.get("recommendations", [])
            )
        except (KimiError, asyncio.TimeoutError, httpx.HTTPError):
            has_official_evidence = False
            verification = {
                "summary": "已按距离列出候选机构；政府记录和价格尚未完成联网核验。",
                "recommended_poi_id": None,
                "decision_basis": ["候选顺序仅按高德返回的直线距离"],
                "recommendations": [],
                "sources": [],
            }
        verification_status = "official_only" if has_official_evidence else "map_only"
        if has_official_evidence:
            verification_notice = (
                f"Kimi 个性化解读暂未完成：{_public_error(str(exc))}；"
                "程序已独立打开政府来源，以下单项价目仍可核对。"
            )
        else:
            verification_notice = (
                f"AI 核验暂未完成：{_public_error(str(exc))}。"
                "当前只显示高德距离，不显示未核实价格。"
            )

    details_by_id = {
        item["poi_id"]: item for item in verification.get("recommendations", [])
    }
    merged = []
    for candidate in candidates[:6]:
        detail = details_by_id.get(candidate["id"], {})
        merged.append(
            {
                **candidate,
                "official_status": detail.get("official_status", "unverified"),
                "official_status_note": detail.get(
                    "official_status_note", "待通过民政部门或机构官方渠道核实"
                ),
                "price_status": detail.get("price_status", "phone_required"),
                "price_items": detail.get("price_items", []),
                "comparable_basic_total_yuan": detail.get("comparable_basic_total_yuan"),
                "fit_for_budget": detail.get("fit_for_budget", "uncertain"),
                "value_reason": detail.get(
                    "value_reason", "仅根据距离排序，价格需要电话逐项确认。"
                ),
                "call_to_confirm": detail.get(
                    "call_to_confirm",
                    ["基本必选服务分项价目", "可选项与取消规则", "符合哪些减免条件"],
                ),
                "cautions": detail.get("cautions", []),
            }
        )

    for item in merged:
        if item["price_items"]:
            item["value_reason"] = (
                f"高德显示直线距离约 {item['distance_m'] / 1000:.1f} 公里；"
                f"政府页面已核对 {len(item['price_items'])} 个单项计价。"
                "不同项目按天、按公里或按档次计费，不能直接相加为套餐总价。"
            )
            item["call_to_confirm"] = [
                "请确认这些政府价目当前是否仍执行",
                "按实际里程、天数和炉型计算后分别多少钱",
                "还有哪些自选项目，哪些可以拒绝",
            ]
            item["cautions"] = [
                "页面展示的是单项政府定价或指导价，不是最终套餐总额",
                "市场调节价项目应当明码标价，并由家属自愿选择",
            ]
            continue
        if item["official_status"] == "verified":
            item["value_reason"] = (
                f"高德显示直线距离约 {item['distance_m'] / 1000:.1f} 公里，机构名称已在政府页面核对；"
                "当前没有可直接比较的政府价目，需电话索取分项报价。"
            )
        else:
            item["value_reason"] = (
                f"高德显示直线距离约 {item['distance_m'] / 1000:.1f} 公里；"
                "未在已打开的政府页面完成机构名称核对，政府记录和价目都需电话确认。"
            )
        item["call_to_confirm"] = [
            "请报基本必选服务的分项价目和总额",
            "哪些项目是可以拒绝的自选服务",
            "我的情况符合哪些减免，需要哪些材料",
        ]

    comparable = [
        item
        for item in merged
        if item["official_status"] == "verified"
        and item["comparable_basic_total_yuan"] is not None
    ]
    if len(comparable) >= 2:
        within = [item for item in comparable if item["fit_for_budget"] == "within"]
        pool = within or comparable
        recommended_id = min(
            pool,
            key=lambda item: (
                item["comparable_basic_total_yuan"], item["distance_m"]
            ),
        )["id"]
        summary = verification.get("summary")
        decision_basis = verification.get("decision_basis", [])
    else:
        official_candidates = [
            item for item in merged if item["official_status"] == "verified"
        ]
        recommended_id = (
            min(official_candidates, key=lambda item: item["distance_m"])["id"]
            if official_candidates
            else None
        )
        summary = (
            "已核对候选机构的距离与政府来源；当前没有至少两家同口径、可打开原始来源的基本服务总价，"
            "因此无法准确判断哪家最便宜。页面先推荐距离最近且政府页面有记录的机构，请电话索取分项价目后再决定。"
        )
        decision_basis = [
            "高德返回当前位置到候选机构的直线距离",
            "机构名称已在可打开的当地政府页面中核对",
            "价格证据不可比，不对“最便宜”做无证据结论",
        ]

    return {
        "generated_at": int(time.time()),
        "city": payload.city,
        "budget": payload.budget,
        "origin": {"longitude": payload.longitude, "latitude": payload.latitude},
        "candidates": merged,
        "summary": summary,
        "recommended_poi_id": recommended_id,
        "decision_basis": decision_basis,
        "sources": verification.get("sources", []),
        "verification_status": verification_status,
        "verification_notice": verification_notice,
    }


def _public_error(message: str) -> str:
    if "401" in message or "403" in message:
        return "核验服务鉴权失败"
    if "429" in message:
        return "核验服务当前繁忙"
    if "timeout" in message.lower() or "timed out" in message.lower():
        return "核验超时"
    return "核验服务暂时不可用"


def _redact_user_note(note: str) -> str:
    text = re.sub(r"(?<!\d)\d{7,18}(?!\d)", "[号码已隐藏]", note)
    return re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "[邮箱已隐藏]",
        text,
    )


@app.get("/api/static-map")
async def static_map(
    longitude: float = Query(ge=-180, le=180),
    latitude: float = Query(ge=-90, le=90),
    points: str = Query(default="", max_length=600),
) -> Response:
    markers: list[tuple[float, float, str]] = []
    if points:
        for index, raw_point in enumerate(points.split("|"), start=1):
            values = raw_point.split(",")
            if len(values) != 2:
                continue
            try:
                lng, lat = float(values[0]), float(values[1])
            except ValueError:
                continue
            if -180 <= lng <= 180 and -90 <= lat <= 90:
                markers.append((lng, lat, str(index)))
    try:
        content, media_type = await amap_client.static_map(
            longitude, latitude, markers
        )
    except (AmapError, Exception) as exc:
        raise HTTPException(status_code=502, detail="地图图片暂时无法加载") from exc
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=1800"},
    )


@app.get("/api/social-relief")
async def relief(city: str = Query(default=settings.default_city, max_length=30)) -> dict[str, Any]:
    return social_relief(" ".join(city.split()) or settings.default_city)


@app.get("/api/community-info")
async def community_info(
    city: str = Query(default=settings.default_city, min_length=1, max_length=30)
) -> dict[str, Any]:
    clean_city = " ".join(city.split()) or settings.default_city
    result = social_relief(clean_city)
    result["search_status"] = "curated" if result["status"] == "curated" else "national_fallback"
    result["verification_notice"] = (
        f"{result['city']}资料已预先整理，页面不会调用 AI 临时检索。"
        if result["status"] == "curated"
        else "该城市资料尚未录入，当前仅显示全国公共渠道。"
    )
    result["generated_at"] = int(time.time())
    result["cache_hit"] = True
    return result


@app.get("/api/help-wall")
async def help_wall() -> dict[str, Any]:
    posts = await asyncio.to_thread(auth_store.list_help_posts)
    return {"posts": posts, "privacy_notice": "请勿发布姓名、身份证号、住址、病历、电话或银行信息。"}


@app.post("/api/help-wall", status_code=201)
async def create_help_post(payload: HelpPostRequest, guicheng_session: Optional[str] = Cookie(default=None)) -> dict[str, Any]:
    if _contains_sensitive_pattern(
        " ".join([payload.alias, payload.city, payload.content])
    ):
        raise HTTPException(status_code=400, detail="内容中可能包含电话或身份证号，请删除后再发布")
    user = auth_store.user_for_session(guicheng_session)
    alias = user["display_name"] if user else payload.alias
    return await asyncio.to_thread(auth_store.create_help_post, user["id"] if user else None, alias, payload.city, payload.topic, payload.content)


@app.post("/api/help-wall/{post_id}/replies", status_code=201)
async def create_help_reply(post_id: str, payload: HelpReplyRequest, guicheng_session: Optional[str] = Cookie(default=None)) -> dict[str, Any]:
    if _contains_sensitive_pattern(" ".join([payload.alias, payload.content])):
        raise HTTPException(status_code=400, detail="回应中可能包含联系方式或身份证号，请删除后再发布")
    match = re.fullmatch(r"post-(\d+)", post_id)
    if not match:
        raise HTTPException(status_code=404, detail="这条求助不存在或已被移除")
    user = auth_store.user_for_session(guicheng_session)
    alias = user["display_name"] if user else payload.alias
    try:
        return await asyncio.to_thread(auth_store.create_help_reply, int(match.group(1)), user["id"] if user else None, alias, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _read_posts() -> list[dict[str, Any]]:
    async with help_wall_lock:
        return await _read_posts_unlocked()


async def _read_posts_unlocked() -> list[dict[str, Any]]:
    if not HELP_WALL_PATH.exists():
        return [
            {
                "id": "welcome",
                "alias": "归程志愿者",
                "city": "北京",
                "topic": "材料核对",
                "content": "可以帮忙把要带的材料按办理地点再核对一遍。请不要在这里留个人证件或电话信息。",
                "created_at": 0,
                "replies": [],
            }
        ]
    try:
        data = json.loads(HELP_WALL_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _contains_sensitive_pattern(content: str) -> bool:
    digits = "".join(character for character in content if character.isdigit())
    lowered = content.lower()
    return len(digits) >= 7 or "@" in lowered or "微信" in content or "vx" in lowered


@app.get("/{path:path}")
async def spa_fallback(path: str) -> FileResponse:
    candidate = STATIC_DIR / path
    if candidate.is_file() and STATIC_DIR in candidate.resolve().parents:
        return FileResponse(candidate)
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from config_loader import settings
import server
from auth_store import AuthStore
from server import RecommendationRequest, _build_recommendations, _redact_user_note, app, amap_client, kimi_client
from services.kimi_client import KimiError
from services.amap_client import AmapClient
from services.kimi_client import KimiClient
from content import social_relief


client = TestClient(app)


def test_health_never_exposes_keys() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    text = response.text
    assert "sk-" not in text
    assert settings.amap_api_key not in text
    assert response.json()["services"] == {"amap": "configured", "kimi": "configured"}


def test_flow_requires_legal_confirmation() -> None:
    response = client.post(
        "/api/generate-flow",
        json={
            "legal_confirmed": False,
            "place": "hospital",
            "budget": "under1000",
            "city": "北京",
            "note": "",
        },
    )
    assert response.status_code == 400


def test_flow_has_five_actionable_nodes_without_fixed_facility_price() -> None:
    response = client.post(
        "/api/generate-flow",
        json={
            "legal_confirmed": True,
            "place": "home",
            "budget": "relief",
            "city": "北京",
            "note": "希望优先了解减免",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 5
    assert data["nodes"][0]["id"] == "confirm"
    assert "110" in data["nodes"][0]["intro"]
    facility = next(node for node in data["nodes"] if node["id"] == "facility")
    assert facility["cost"] == "AI 联网核验后显示"
    assert "200 元" not in str(facility)


def test_city_specific_relief_does_not_leak_beijing_channels() -> None:
    beijing = social_relief("北京市")
    shanghai = social_relief("上海")
    assert any(item["phone"] == "96101" for item in beijing["contacts"])
    assert all(item["phone"] != "96101" for item in shanghai["contacts"])
    assert shanghai["status"] == "curated"
    assert any(item["publisher"] == "上海市民政局" for item in shanghai["references"])


def test_city_suffix_is_not_duplicated() -> None:
    response = client.post(
        "/api/generate-flow",
        json={
            "legal_confirmed": True,
            "place": "hospital",
            "budget": "unsure",
            "city": "上海市",
            "note": "",
        },
    )
    assert response.status_code == 200
    burial = next(node for node in response.json()["nodes"] if node["id"] == "burial")
    assert burial["location"].startswith("上海市民政")
    assert "上海市市" not in burial["location"]


def test_flow_can_include_guarded_kimi_personalization(monkeypatch) -> None:
    personalized_sop = {
        "personalization": {
            "summary": "已按医院场景和费用需求整理办理重点。",
            "first_action": "先联系护士站，确认由哪个部门开具证明。",
            "priority_node_ids": ["confirm", "certificate"],
            "generated_by": "kimi",
        },
        "nodes": [
            {
                "id": "certificate",
                "now": "先联系护士站，确认开具窗口。",
                "location": "医院护士站或医务处",
                "cost_note": "以医院正式告知为准",
                "materials": ["办理人身份证"],
                "actions": ["现场核对证明信息"],
                "visual_cards": [],
                "warning": "不要交给私人代办。",
                "reference_ids": [],
            }
        ],
    }
    monkeypatch.setattr(
        kimi_client, "personalize_sop", AsyncMock(return_value=personalized_sop)
    )
    response = client.post(
        "/api/generate-flow",
        json={
            "legal_confirmed": True,
            "place": "hospital",
            "budget": "under1000",
            "city": "北京",
            "note": "希望先办证明",
            "personalize": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["personalization"] == personalized_sop["personalization"]
    certificate = next(node for node in response.json()["nodes"] if node["id"] == "certificate")
    assert certificate["personalized"]["location"] == "医院护士站或医务处"
    assert response.json()["note"] == ""


def test_community_info_uses_prebuilt_city_references_without_kimi(monkeypatch) -> None:
    search = AsyncMock(side_effect=AssertionError("community content must not call Kimi"))
    monkeypatch.setattr(kimi_client, "search_community_info", search)
    response = client.get("/api/community-info?city=上海")
    assert response.status_code == 200
    data = response.json()
    assert data["search_status"] == "curated"
    assert data["references"]
    search.assert_not_awaited()


def test_real_local_account_login_and_progress(monkeypatch, tmp_path: Path) -> None:
    store = AuthStore(tmp_path / "accounts.db")
    monkeypatch.setattr(server, "auth_store", store)
    account_client = TestClient(app)
    registration = account_client.post(
        "/api/auth/register",
        json={"email": "family@example.com", "password": "long-pass-123", "display_name": "林女士"},
    )
    assert registration.status_code == 201
    assert registration.json()["user"]["display_name"] == "林女士"
    assert account_client.get("/api/auth/me").json()["user"]["email"] == "family@example.com"

    saved = account_client.put(
        "/api/account/progress",
        json={
            "city": "上海",
            "legal_confirmed": True,
            "answers": {"place": "hospital", "budget": "under1000"},
            "flow": None,
            "completed": ["confirm"],
            "checks": {"confirm": [0]},
            "mode": "standard",
        },
    )
    assert saved.status_code == 200
    assert account_client.get("/api/account/progress").json()["progress"]["city"] == "上海"

    assert account_client.post("/api/auth/logout").status_code == 200
    assert account_client.get("/api/account/progress").status_code == 401
    login = account_client.post(
        "/api/auth/login",
        json={"email": "family@example.com", "password": "long-pass-123"},
    )
    assert login.status_code == 200
    assert account_client.get("/api/account/progress").json()["progress"]["completed"] == ["confirm"]

    with store._connect() as db:
        row = db.execute("SELECT password_hash FROM users WHERE email = ?", ("family@example.com",)).fetchone()
    assert row["password_hash"] != "long-pass-123"


def test_amap_filter_rejects_halls_and_service_desks() -> None:
    amap = AmapClient(settings)
    assert amap._looks_like_funeral_home(
        {"name": "北京市东郊殡仪馆", "type": "生活服务;丧葬设施;殡仪馆"}
    )
    assert not amap._looks_like_funeral_home(
        {"name": "北京市八宝山殡仪馆梅厅", "type": "生活服务;丧葬设施;丧葬设施"}
    )
    assert not amap._looks_like_funeral_home(
        {"name": "大兴殡仪馆服务站", "type": "生活服务;丧葬设施;殡仪馆"}
    )


def test_evidence_guards_require_government_origin_and_page_match() -> None:
    page = "北京市八宝山殡仪馆 骨灰寄存 50 元/年 大兴区殡仪馆"
    assert KimiClient._name_matches_page("北京市八宝山殡仪馆", page)
    assert KimiClient._name_matches_page("大兴殡仪馆", page)
    assert not KimiClient._name_matches_page("昌平殡仪馆", page)
    assert KimiClient._amount_in_page(50, page)
    assert not KimiClient._amount_in_page(500, page)
    assert KimiClient._is_price_source(
        {"url": "https://mzj.beijing.gov.cn/page", "source_type": "government"}
    )
    assert not KimiClient._is_price_source(
        {"url": "https://xinwen.bjd.com.cn/page", "source_type": "government"}
    )
    distant_page = "北京市八宝山殡仪馆" + ("其他内容" * 500) + "骨灰寄存 50 元/年"
    close_page = "北京市八宝山殡仪馆办理项目：骨灰寄存 50 元/年"
    assert KimiClient._price_matches_context("北京市八宝山殡仪馆", 50, close_page)
    assert not KimiClient._price_matches_context("北京市八宝山殡仪馆", 50, distant_page)
    source = "北京市八宝山殡仪馆 接尸车运输费 起价50元。火化费380元/次。"
    assert KimiClient._price_evidence_excerpt(
        "北京市八宝山殡仪馆", "接尸车运输费", 50, source
    )
    assert not KimiClient._price_evidence_excerpt(
        "北京市八宝山殡仪馆", "火化费", 50, source
    )
    assert KimiClient._price_evidence_excerpt(
        "北京市八宝山殡仪馆", "火化费", 380, source
    )


def test_help_wall_rejects_contact_numbers() -> None:
    response = client.post(
        "/api/help-wall",
        json={
            "alias": "家属",
            "city": "北京",
            "topic": "材料核对",
            "content": "请联系 13800138000 帮忙核对材料",
        },
    )
    assert response.status_code == 400


def test_help_wall_rejects_contact_number_in_alias() -> None:
    response = client.post(
        "/api/help-wall",
        json={
            "alias": "联系13800138000",
            "city": "北京",
            "topic": "材料核对",
            "content": "想请人帮忙核对材料",
        },
    )
    assert response.status_code == 400


def test_user_note_redacts_obvious_contacts_before_ai() -> None:
    redacted = _redact_user_note("请联系13800138000，邮箱 a@example.com，预算不高")
    assert "13800138000" not in redacted
    assert "a@example.com" not in redacted
    assert "预算不高" in redacted


def test_pdf_extractor_handles_valid_empty_pdf() -> None:
    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(buffer)
    assert KimiClient._extract_pdf_text(buffer.getvalue()) == ""


def test_core_price_extractor_keeps_units_separate() -> None:
    page = """
    北京市东郊殡仪馆殡仪服务价目表
    接尸车运输费 遗体接运 起价50元，10公里以上5元/公里。
    冷冻存尸费 遗体冷藏 3日以内(含3日)每具每日30元；3日至7日每具每日40元；7日以上每具每日50元。
    火化费 一类进口炉 遗体火化700元/次；二类合资炉550元/次；三类自动炉380元/次。
    骨灰堂骨灰寄存费 骨灰临时寄存50元/年。
    """
    items = KimiClient._extract_core_price_items(
        "北京市东郊殡仪馆", "TEST", page
    )
    pairs = {(item["item"], item["amount_yuan"]) for item in items}
    assert ("遗体接运（中档车起价）", 50) in pairs
    assert ("遗体接运（10公里以上每公里）", 5) in pairs
    assert ("遗体冷藏（3日以内每日）", 30) in pairs
    assert ("遗体火化（一类进口炉）", 700) in pairs
    assert ("骨灰临时寄存（每年）", 50) in pairs


def test_beijing_official_source_index_uses_candidate_specific_pages() -> None:
    sources = KimiClient._official_sources_for_name("北京市八宝山殡仪馆")
    assert sources
    assert sources[0]["url"].endswith(".pdf")
    assert KimiClient._source_specific_to_candidate(
        {
            "title": "北京市八宝山殡仪馆殡仪服务价目表",
            "url": sources[0]["url"],
        },
        "北京市八宝山殡仪馆",
    )
    assert not KimiClient._source_specific_to_candidate(
        {"title": "北京市殡仪馆名单", "url": "https://mzj.beijing.gov.cn/list"},
        "北京市八宝山殡仪馆",
    )
    assert not KimiClient._source_specific_to_candidate(
        {
            "title": "北京市东郊殡仪馆告别厅服务采购项目中标公告",
            "url": "https://ggzyfw.beijing.gov.cn/procurement",
        },
        "北京市东郊殡仪馆",
    )


def test_kimi_failure_keeps_independently_verified_official_prices(monkeypatch) -> None:
    candidate = {
        "id": "east",
        "name": "北京市东郊殡仪馆",
        "address": "北京市朝阳区",
        "longitude": 116.54,
        "latitude": 39.95,
        "distance_m": 1200,
        "phone": "010-12345678",
        "type": "生活服务;丧葬设施;殡仪馆",
        "source": "amap",
    }
    official = {
        "summary": "政府来源已核对",
        "recommended_poi_id": None,
        "decision_basis": ["政府来源"],
        "recommendations": [
            {
                "poi_id": "east",
                "official_status": "verified",
                "official_status_note": "政府页面有记录",
                "price_status": "partial",
                "price_items": [
                    {
                        "item": "火化费",
                        "amount_yuan": 380,
                        "display": "¥380",
                        "conditions": "政府原文",
                        "source_ids": ["S1"],
                    }
                ],
                "comparable_basic_total_yuan": None,
                "fit_for_budget": "uncertain",
                "value_reason": "政府价目已核对",
                "call_to_confirm": [],
                "cautions": [],
            }
        ],
        "sources": [],
    }
    monkeypatch.setattr(
        amap_client, "nearby_funeral_homes", AsyncMock(return_value=[candidate])
    )
    monkeypatch.setattr(
        kimi_client,
        "verify_facilities",
        AsyncMock(side_effect=KimiError("temporary")),
    )
    monkeypatch.setattr(
        kimi_client,
        "verify_official_sources_only",
        AsyncMock(return_value=official),
    )
    result = asyncio.run(
        _build_recommendations(
            RecommendationRequest(
                longitude=116.4,
                latitude=39.9,
                city="北京",
                budget="under1000",
                note="",
            )
        )
    )
    assert result["verification_status"] == "official_only"
    assert result["candidates"][0]["price_items"][0]["amount_yuan"] == 380

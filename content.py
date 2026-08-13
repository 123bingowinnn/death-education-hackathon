from __future__ import annotations

from typing import Any


PLACE_ROUTES = {
    "hospital": {
        "label": "在医院",
        "first_action": "联系医院护士站或医务处，由医疗机构按流程确认并开具相应证明。",
        "location": "所在医院",
        "materials": ["逝者身份证", "办理人身份证", "逝者就诊资料"],
        "urgent": False,
    },
    "home": {
        "label": "在家中",
        "first_action": "如为明确的正常死亡，先联系辖区社区卫生服务机构；死因不明、意外或有任何疑问时，立即拨打 110，不要移动现场物品。",
        "location": "辖区社区卫生服务机构 / 公安机关",
        "materials": ["逝者身份证", "办理人身份证", "户口簿", "既往病历（如有）"],
        "urgent": True,
    },
    "public": {
        "label": "公共场所",
        "first_action": "立即拨打 110，保护现场，由公安机关按法定程序处理。不要自行联系车辆转运。",
        "location": "公安机关",
        "materials": ["报警回执或案件编号", "逝者身份证（如有）", "办理人身份证"],
        "urgent": True,
    },
    "care": {
        "label": "养老机构",
        "first_action": "联系机构值班负责人和医务人员，由机构配合完成确认与证明开具。",
        "location": "所在养老机构",
        "materials": ["逝者身份证", "办理人身份证", "入住与医疗记录"],
        "urgent": False,
    },
}


BUDGET_LABELS = {
    "relief": "需要费用减免",
    "under1000": "1000 元以内",
    "1000to5000": "1000-5000 元",
    "over5000": "5000 元以上",
    "unsure": "还不确定",
}


NATIONAL_CONTACTS = [
    {"name": "政务服务便民热线", "phone": "12345", "use": "询问当期政策和主管部门", "scope": "全国"},
    {"name": "公共法律服务热线", "phone": "12348", "use": "处理继承、授权与合同纠纷", "scope": "全国"},
]


CITY_CONTENT: dict[str, dict[str, Any]] = {
    "北京": {
        "updated_at": "2026-08-13",
        "status": "curated",
        "policies": [
            {
                "title": "北京市殡葬基本服务保障政策",
                "summary": "基本服务保障、适用对象与办理材料以北京市当期文件为准。",
                "applies_to": "在北京办理相关事项的家庭；具体资格按文件核对",
                "reference_id": "BJ-P1",
            },
            {
                "title": "北京市节地生态安葬服务信息",
                "summary": "查看当期生态安葬服务单位、报名和办理安排。",
                "applies_to": "考虑海葬、自然葬等节地生态安葬的家庭",
                "reference_id": "BJ-P2",
            },
        ],
        "contacts": [
            {"name": "北京市殡葬服务咨询", "phone": "96101", "use": "核实服务机构、办理事项和公开渠道", "scope": "北京", "reference_id": "BJ-P1"},
        ],
        "references": [
            {"id": "BJ-P1", "title": "北京市殡葬基本服务保障政策", "url": "https://www.beijing.gov.cn/zhengce/zhengcefagui/202605/t20260506_4638107.html", "publisher": "北京市人民政府", "note": "核对当期基本服务保障和咨询渠道"},
            {"id": "BJ-P2", "title": "北京市节地生态安葬服务单位信息", "url": "https://mzj.beijing.gov.cn/art/2026/7/8/art_371_692396.html", "publisher": "北京市民政局", "note": "核对当期服务单位和办理安排"},
            {"id": "BJ-P3", "title": "北京市政务服务网", "url": "https://banshi.beijing.gov.cn/", "publisher": "北京市人民政府", "note": "查询户口注销、社保和其他政务事项"},
        ],
        "sop_context": {
            "certificate_location": "按离世地点向医院、社区卫生机构或公安机关确认",
            "facility_rule": "通过北京市民政部门公布信息核对机构，并要求书面分项价目",
            "burial_location": "北京市民政部门公布的殡葬服务机构",
            "cost_rule": "基本服务、选择性服务和减免资格分开核对，不预填无来源套餐总价",
        },
    },
    "上海": {
        "updated_at": "2026-08-13",
        "status": "curated",
        "policies": [
            {"title": "上海市属殡仪馆收费信息集中公示", "summary": "市属殡仪馆分项目公开收费及咨询电话，价格会动态更新。", "applies_to": "在上海选择市属殡仪馆的家庭", "reference_id": "SH-P1"},
            {"title": "上海市骨灰海葬服务意见", "summary": "了解海葬服务、预约与当期补贴管理要求。", "applies_to": "考虑骨灰海葬的家庭", "reference_id": "SH-P2"},
        ],
        "contacts": [
            {"name": "上海殡葬服务咨询", "phone": "021-962840", "use": "咨询上海殡葬服务和一件事办理", "scope": "上海", "reference_id": "SH-P3"},
        ],
        "references": [
            {"id": "SH-P1", "title": "市属殡仪馆收费信息集中公示", "url": "https://mzj.sh.gov.cn/bzfwjgsfgs/20251031/a2f8be6d595343c2988c86fa23b8b000.html", "publisher": "上海市民政局", "note": "核对殡仪馆分项收费和咨询电话"},
            {"id": "SH-P2", "title": "关于积极推进骨灰海葬服务的意见", "url": "https://www.shanghai.gov.cn/gwk/affairs/content/0034%408b92afdf44c043ca9f1fb43d533b6c64", "publisher": "上海市人民政府", "note": "核对海葬服务与当期政策"},
            {"id": "SH-P3", "title": "身故后需要办理的事项", "url": "https://english.shanghai.gov.cn/en-Death/20231216/58eb550bc0b34515a3cf13c7ff2d9238.html", "publisher": "上海市人民政府", "note": "一件事入口和公开咨询渠道"},
        ],
        "sop_context": {"certificate_location": "按离世地点向医疗机构或公安机关确认", "facility_rule": "优先核对上海市民政局收费集中公示，并索取当期分项清单", "burial_location": "上海市殡葬服务平台公布的服务机构", "cost_rule": "以集中公示及机构当期明码标价为准"},
    },
    "广州": {
        "updated_at": "2026-08-13",
        "status": "curated",
        "policies": [
            {"title": "羊城白事一本通", "summary": "汇总广州殡葬办理路径、服务机构和咨询渠道。", "applies_to": "在广州办理身后事的家庭", "reference_id": "GZ-P1"},
        ],
        "contacts": [
            {"name": "广州市殡葬管理咨询", "phone": "020-87053456", "use": "殡葬政策法规咨询及投诉举报", "scope": "广州", "reference_id": "GZ-P1"},
        ],
        "references": [
            {"id": "GZ-P1", "title": "羊城白事一本通", "url": "https://mzj.gz.gov.cn/attachment/7/7794/7794452/10205217.pdf", "publisher": "广州市民政局", "note": "核对广州办理流程、机构与公开电话"},
        ],
        "sop_context": {"certificate_location": "按离世地点向医疗机构或公安机关确认", "facility_rule": "按羊城白事一本通核对正规服务机构与公开事项", "burial_location": "广州市民政部门公布的服务机构", "cost_rule": "按政府公开项目与机构明码标价逐项确认"},
    },
    "深圳": {
        "updated_at": "2026-08-13",
        "status": "curated",
        "policies": [
            {"title": "深圳市殡葬服务公开信息", "summary": "从深圳市民政局查询当期政策、服务标准与通知。", "applies_to": "在深圳办理相关事项的家庭", "reference_id": "SZ-P1"},
        ],
        "contacts": [],
        "references": [
            {"id": "SZ-P1", "title": "深圳市民政局", "url": "https://mzj.sz.gov.cn/", "publisher": "深圳市民政局", "note": "核对当期政策、服务机构与公开通知"},
        ],
        "sop_context": {"certificate_location": "按离世地点向医疗机构或公安机关确认", "facility_rule": "通过深圳市民政局公开信息核对服务机构", "burial_location": "深圳市民政部门公布的服务机构", "cost_rule": "按政府公开项目与机构书面价目逐项确认"},
    },
}


def _is_beijing(city: str) -> bool:
    return city.strip().removesuffix("市") == "北京"


def normalize_city(city: str) -> str:
    return city.strip().removesuffix("市")


def city_content(city: str) -> dict[str, Any]:
    clean = normalize_city(city)
    package = CITY_CONTENT.get(clean)
    if package:
        return {"city": clean, **package, "contacts": [*package["contacts"], *NATIONAL_CONTACTS]}
    return {
        "city": clean or "当前城市",
        "updated_at": "2026-08-13",
        "status": "national_fallback",
        "policies": [],
        "contacts": list(NATIONAL_CONTACTS),
        "references": [],
        "sop_context": {"certificate_location": "按离世地点向医疗机构或公安机关确认", "facility_rule": "向当地民政部门核对正规服务机构", "burial_location": f"{city_with_suffix(clean or '当地')}民政部门公布的服务机构", "cost_rule": "当地资料尚未录入，费用仅通过官方窗口和书面价目确认"},
    }


def sources_for_city(city: str) -> list[dict[str, str]]:
    return [
        {"title": item["title"], "url": item["url"], "note": item["note"]}
        for item in city_content(city)["references"]
    ]


def city_with_suffix(city: str) -> str:
    clean = city.strip()
    return clean if clean.endswith("市") else f"{clean}市"


def build_flow(place: str, budget: str, city: str, note: str = "") -> dict[str, Any]:
    route = PLACE_ROUTES.get(place, PLACE_ROUTES["hospital"])
    budget_label = BUDGET_LABELS.get(budget, BUDGET_LABELS["unsure"])
    low_budget = budget in {"relief", "under1000"}
    nodes: list[dict[str, Any]] = [
        {
            "id": "confirm",
            "number": 1,
            "title": "确认死亡与性质",
            "short_title": "确认死亡",
            "location": route["location"],
            "time": "请尽快处理" if route["urgent"] else "当日办理",
            "cost": "以办理机构告知为准",
            "intro": route["first_action"],
            "materials": route["materials"],
            "actions": [
                "记录接待人员、办理部门和时间",
                "只接受医疗机构或公安机关的正式指引",
                "如死因不明或涉及意外，先报警后处理",
            ],
            "warning": "在死因尚未明确时，不要自行转运、擦洗或签署不明合同。",
        },
        {
            "id": "certificate",
            "number": 2,
            "title": "办理死亡证明",
            "short_title": "死亡证明",
            "location": route["location"],
            "time": "材料齐全后现场咨询",
            "cost": "证明开具费用待办理机构确认",
            "intro": "先确认由哪个机构开具。领取时逐项核对姓名、证件号和时间，并询问后续事项所需的原件与复印件数量。",
            "materials": list(dict.fromkeys(route["materials"] + ["逝者户口簿（如可取得）"])),
            "actions": [
                "当场核对证明上的全部信息",
                "询问原件份数、补开地点和联系方式",
                "拍照留存电子备份，原件分开保管",
            ],
            "warning": "“加急代办死亡证明”不应通过医院门口的私人拉客人员办理。",
        },
        {
            "id": "facility",
            "number": 3,
            "title": "选择正规殡仪服务机构",
            "short_title": "选机构",
            "location": "根据当前位置搜索",
            "time": "建议至少比较 2 家",
            "cost": "AI 联网核验后显示",
            "intro": "先用实时地图找到附近候选，再核对政府记录、服务价目与减免条件。距离和价格分开取证，避免把地图 POI 当成价格来源。",
            "materials": ["死亡证明", "逝者身份证", "办理人身份证", "户口簿（以机构要求为准）"],
            "actions": [
                "先询“基本必选服务的分项价格”",
                "要求对方说明每个可选项，不接受只报总价",
                "确认车辆、冷藏、告别、火化和骨灰寄存是否分别计价",
                "签约前索取书面价目与项目清单",
            ],
            "warning": "不要向医院门口主动搭讪者支付定金，也不要签署没有分项价格的“全包”合同。",
            "substeps": ["遗体接运", "冷藏与告别", "火化", "骨灰领取或寄存"],
        },
        {
            "id": "burial",
            "number": 4,
            "title": "选择安放方式",
            "short_title": "安放骨灰",
            "location": f"{city_with_suffix(city)}民政部门公布的服务机构",
            "time": "不必当天决定",
            "cost": "根据安放方式和当期政策确认",
            "intro": "骨灰可先合规寄存，家人不需要在情绪最紧绷时立即购买墓位。再对比节地生态安葬、海葬、公墓或继续寄存。",
            "materials": ["火化证明或相关凭证", "骨灰领取凭证", "办理人身份证"],
            "actions": [
                "确认当前可报名的节地生态安葬项目",
                "询问补贴对象、户籍条件和申请时限",
                "购买墓位时确认管理期、维护费和续费条款",
            ],
            "warning": "“政府有补贴”并不代表每个人都符合条件，必须核对当期文件。",
            "substeps": ["骨灰寄存", "节地生态安葬", "海葬", "公墓安葬"],
        },
        {
            "id": "accounts",
            "number": 5,
            "title": "处理销户与权益",
            "short_title": "销户与权益",
            "location": "派出所、社保经办机构、公积金中心与相关金融机构",
            "time": "按各事项时限分开办理",
            "cost": "官方窗口核实",
            "intro": "把户口、社保、医保、公积金、银行与数字账户分开记录。先列全部资产和债务，再办销户，避免遗漏信息。",
            "materials": ["死亡证明", "逝者户口簿与身份证", "办理人身份证", "亲属关系或继承权证明（按事项要求）"],
            "actions": [
                "查询当地政务服务网上的材料与时限",
                "建立账户清单，保留每次办理的回执",
                "金额或继承关系复杂时，先咨询法律服务",
            ],
            "warning": "不要向任何非官方人员提供手机验证码、支付密码或完整银行卡信息。",
            "substeps": ["户口注销", "社保与医保", "公积金", "银行与其他账户", "遗产处理"],
        },
    ]
    return {
        "city": city,
        "place": place,
        "place_label": route["label"],
        "budget": budget,
        "budget_label": budget_label,
        "note": note[:500],
        "nodes": nodes,
        "show_relief": low_budget,
        "show_fraud": low_budget or budget == "unsure",
        "sources": sources_for_city(city),
        "notice": "流程用于办事整理，不替代医疗、公安、民政或法律机关的正式意见。",
    }


def social_relief(city: str) -> dict[str, Any]:
    package = city_content(city)
    return {
        "city": package["city"],
        "status": package["status"],
        "updated_at": package["updated_at"],
        "intro": "减免、补贴和节地生态安葬项目会随户籍、人员类别和当期政策变化，不用固定数字做承诺。",
        "checks": [
            "是否为低保、特困供养、重度残疾或其他民政救助对象",
            "逝者户籍地与办理地是否一致",
            "是否选择当期政府组织的节地生态安葬",
            "申请时限、必需材料和费用结算方式",
        ],
        "policies": package["policies"],
        "contacts": package["contacts"],
        "references": package["references"],
        "sources": sources_for_city(city),
    }

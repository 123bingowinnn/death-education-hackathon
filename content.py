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


BURIAL_METHODS: list[dict[str, Any]] = [
    {
        "id": "sea",
        "category": "中国常见",
        "name": "海葬",
        "idea": "魂归大海，真正零占地。",
        "cost": "免费-5000元",
        "eco": "高",
        "legal": "中国多地民政部门组织或支持",
        "mood": "海面、雾气、白花和远处的航线。它不强调拥有一块墓地，而强调把告别交给流动的水。",
        "source_note": "综合 burial at sea 条目中关于海上处置、撒放骨灰、海上纪念仪式的通用描述，并结合中国节地生态安葬语境整理。",
        "gallery": [
            {"url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=900&h=1200&fit=crop", "alt": "安静海面与浅色浪线"},
            {"url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=900&h=1200&fit=crop", "alt": "湖海交界处的日落倒影"},
            {"url": "https://images.unsplash.com/photo-1471922694854-ff1b63b20054?w=900&h=1200&fit=crop", "alt": "海上船只与蓝色水面"},
            {"url": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?w=900&h=1200&fit=crop", "alt": "浪花与海岸"},
            {"url": "https://images.unsplash.com/photo-1505142468610-359e7d316be0?w=900&h=1200&fit=crop", "alt": "深蓝海面和远处天空"},
        ],
        "process": ["咨询当地民政部门或殡葬服务机构", "按批次报名并提交火化证明等材料", "参加集体或委托式海撒仪式"],
        "faq": ["骨灰通常需由合规机构统一处理。", "是否补贴以户籍和当期政策为准。", "家人可用纪念证书或线上祭扫延续纪念。"],
        "questions": [
            {"q": "骨灰可以直接撒进海里吗？", "a": "在很多地区，个人随意撒放并不被鼓励。更稳妥的做法是通过民政部门或合规机构组织的海葬服务，确认海域、容器、仪式和证明。"},
            {"q": "海葬证书有什么用？", "a": "它通常不是财产证明，而是纪念和办理记录。对家属来说，它把一个没有墓碑的告别变成可以被保存、被讲述的一件事。"},
            {"q": "以后怎么祭奠？", "a": "可以在海边、线上纪念馆、家庭相册或每年的纪念日完成。海葬把固定地点变弱，但也让纪念从墓地扩展到更大的生活场景。"},
        ],
        "story": "海葬的古老感来自航行：人在海上去世时，船队会用可行的方式把遗体交还给海。现代海葬更多面对的是骨灰，仪式可能很轻：一束花、一段默念、船慢下来，亲人把最后的重量交给水面。它的动人之处在于不占有，不圈定，只让告别慢慢被潮汐带走。",
        "heritage": "在中国当代语境里，海葬常被放在节地生态安葬中理解。它既是环保选择，也是一种观念转换：不是为死亡购买一块永久的土地，而是承认生命可以回到公共的、流动的自然里。",
        "reflection": "如果海葬是免费的或低成本的，为什么不是所有人都选它？",
    },
    {
        "id": "tree",
        "category": "中国常见",
        "name": "树葬",
        "idea": "以树为碑，让生命回到生长之中。",
        "cost": "2000-20000元",
        "eco": "高",
        "legal": "多地节地生态安葬项目支持",
        "mood": "林下的光、泥土的气味和一棵逐年长大的树。它不是消失，而是把纪念变成季节。",
        "source_note": "参考 natural burial 对自然分解、可降解容器、浅层土壤生态活动和树荚葬概念的描述，并结合中国树葬实践整理。",
        "gallery": [
            {"url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=900&h=1200&fit=crop", "alt": "阳光穿过森林"},
            {"url": "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=900&h=1200&fit=crop", "alt": "绿色山谷与树木"},
            {"url": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=900&h=1200&fit=crop", "alt": "密林树干"},
            {"url": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=900&h=1200&fit=crop", "alt": "高耸树冠"},
            {"url": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=900&h=1200&fit=crop", "alt": "森林小路与晨光"},
        ],
        "process": ["选择有资质的生态安葬园区", "确认是否使用可降解容器", "举行简短安放或纪念仪式"],
        "faq": ["通常不设传统墓碑。", "价格差异来自园区、树种和维护服务。", "部分地区有生态安葬奖励。"],
        "questions": [
            {"q": "树就是墓碑吗？", "a": "很多树葬弱化传统墓碑，只保留小型铭牌、电子纪念码或园区统一标识。真正的纪念对象变成那棵树和它所在的季节。"},
            {"q": "家属以后可以去看吗？", "a": "通常可以，但要看园区规则。有些生态葬区域强调公共绿地属性，不鼓励大量祭品和焚烧。"},
            {"q": "树死了怎么办？", "a": "这要在购买或办理前问清维护协议：树木补植、管理年限、铭牌保留方式，都应写进服务说明。"},
        ],
        "story": "树葬最打动人的地方，是它把死亡从一个封闭石碑变成开放的生长。春天发芽，夏天成荫，秋天落叶，冬天安静。亲人来看望时，面对的不是一块冷硬的边界，而是一棵仍在参与世界的树。",
        "heritage": "自然葬并不是现代人突然发明的概念。许多文化都曾用不防腐、不隔绝土壤的方式安葬逝者。现代树葬把这种古老的“归土”愿望重新组织成城市可理解、可管理的生态安葬形式。",
        "reflection": "如果一棵树替你留下名字，你希望它开花、常青，还是结果？",
    },
    {
        "id": "sky_burial",
        "category": "中国少数民族",
        "name": "藏族天葬",
        "idea": "布施飞禽，灵魂升天。",
        "cost": "宗教习俗",
        "eco": "高",
        "legal": "尊重民族宗教习俗，非旅游观摩项目",
        "mood": "高原、风、经幡和遥远的鸟影。这个页面不展示血腥画面，只解释它背后的无常、布施与地理现实。",
        "source_note": "参考 sky burial 条目中关于藏传佛教、尸陀林、高原地理、鸟葬含义和现代监管的通用描述整理。",
        "gallery": [
            {"url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=900&h=1200&fit=crop", "alt": "高原山地与空旷天空"},
            {"url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=900&h=1200&fit=crop", "alt": "雪山和云层"},
            {"url": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=900&h=1200&fit=crop", "alt": "星空下的山脉"},
            {"url": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=900&h=1200&fit=crop", "alt": "山谷与远山"},
            {"url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=900&h=1200&fit=crop", "alt": "雾气中的山林"},
        ],
        "process": ["由当地宗教和社区习俗安排", "家属遵循仪轨与禁忌", "不公开围观或拍摄"],
        "faq": ["不适合作为普通城市安葬选择。", "核心是宗教布施观念。", "应尊重当地文化边界。"],
        "questions": [
            {"q": "天葬为什么不是“残忍”？", "a": "在藏传佛教语境中，死亡后的身体已不再是自我，把它布施给其他生命，是无常观和慈悲观的一部分。离开语境观看，容易误读。"},
            {"q": "普通人可以选择天葬吗？", "a": "不建议把它理解成可自由购买的旅行式体验。它属于特定地区、宗教、族群和社区规范中的丧葬实践。"},
            {"q": "为什么在高原形成？", "a": "高原冻土、岩石、木柴匮乏等条件，使土葬和火葬都不容易；宗教观念又赋予这种处理方式精神意义。"},
        ],
        "story": "天葬让很多外来者震惊，但在它自己的世界里，重点并不是奇观，而是无常。人已经离开，身体成为最后一次布施。风把诵经声带走，鸟群完成自然的循环。它提醒人：身体不是永恒的容器，关系和慈悲才是留下来的东西。",
        "heritage": "天葬与藏传佛教的尸陀林观念、高原自然条件和社区仪轨密切相关。现代社会中，它也面临保护秃鹫、限制围观、维护逝者尊严等现实议题。",
        "reflection": "如果死亡不是占有身体，而是最后一次给予，你会怎样理解“留下”？",
    },
    {"id": "flower_lawn", "category": "中国常见", "name": "花坛葬/草坪葬", "idea": "与花草相伴，减少硬质墓位占用。", "cost": "1.2万-3.5万元", "eco": "高", "legal": "多地经营性公墓或公益性公墓可办理", "process": ["咨询公墓或生态葬专区", "确认管理期、维护费与标识方式", "完成骨灰安放"], "faq": ["通常占地少于传统墓位。", "维护方式由园区统一管理。", "需核对续费与管理期。"]},
    {"id": "wall", "category": "中国常见", "name": "壁葬", "idea": "壁龛寄存，集约安放。", "cost": "1480-4万元", "eco": "高", "legal": "多地合法常见", "process": ["选择骨灰堂或壁葬区", "核对龛位规格、年限和管理费", "办理安放手续"], "faq": ["适合希望有固定祭扫地点的家庭。", "龛位位置和期限会影响费用。", "购买前应索取书面价目。"]},
    {"id": "deposit", "category": "中国常见", "name": "骨灰寄存", "idea": "集中寄存，经济简便，也给家人留下缓冲时间。", "cost": "免费-数百元/年", "eco": "高", "legal": "殡仪馆、骨灰堂等合规机构可办理", "process": ["领取骨灰后咨询寄存窗口", "提交火化证明和办理人证件", "按年或按期续存"], "faq": ["不必当天决定长期安葬方式。", "寄存费通常较低。", "需保存好寄存凭证。"]},
    {"id": "cremation", "category": "中国常见", "name": "火葬", "idea": "以火化完成遗体处理，节约土地。", "cost": "1000-5000元", "eco": "中", "legal": "中国大多数城市普遍执行", "process": ["取得死亡证明", "预约正规殡仪馆", "完成接运、火化和骨灰领取"], "faq": ["基本服务和自选服务要分开报价。", "炉型和告别服务会影响价格。", "不要接受无分项的全包合同。"]},
    {"id": "earth", "category": "中国常见", "name": "土葬", "idea": "入土为安，回归大地。", "cost": "数千-数十万元", "eco": "中", "legal": "中国多地受火葬区政策限制", "process": ["先核对当地是否允许", "确认墓地资质和使用期限", "按当地规定办理安葬"], "faq": ["城市地区通常限制较多。", "墓位费用差异很大。", "需警惕非法墓地销售。"]},
    {"id": "mongolian_secret", "category": "中国少数民族", "name": "蒙古族密葬", "idea": "魂归长生天，来去无痕。", "cost": "宗教习俗", "eco": "高", "legal": "属于民族传统习俗", "process": ["由家族和当地习俗决定", "不设显著标记", "以追思仪式延续纪念"], "faq": ["强调自然与无痕。", "不同地区实践差异很大。", "需尊重当地规范。"]},
    {"id": "water_tradition", "category": "中国少数民族", "name": "水葬", "idea": "随水而去，净化归途。", "cost": "宗教习俗", "eco": "中", "legal": "现代公共卫生和水域管理限制较多", "process": ["先核对当地法律和民族习俗", "不得私自在公共水域处理遗体或骨灰", "以合规替代仪式表达纪念"], "faq": ["与现代海葬不是一回事。", "水源保护要求优先。", "多数城市不可自行实施。"]},
    {"id": "stupa", "category": "中国少数民族", "name": "塔葬", "idea": "高僧舍利供奉塔中。", "cost": "宗教习俗", "eco": "高", "legal": "主要用于特定宗教身份", "process": ["由寺院和宗教共同体判断资格", "按仪轨火化或处理舍利", "供奉于塔中"], "faq": ["并非普通公众可自由选择。", "与宗教身份密切相关。", "应避免商业化误导。"]},
    {"id": "nor", "category": "国际新兴", "name": "人体堆肥(NOR)", "idea": "化为土壤，反哺大地。", "cost": "约5万元", "eco": "极高", "legal": "美国部分州已合法，中国大陆尚未开放", "process": ["遗体置入有机材料容器", "经数周自然转化为土壤", "土壤交还家属或用于生态修复"], "faq": ["也称自然有机还原。", "目前在中国不可作为常规服务。", "环保优势来自低能耗和土壤回归。"]},
    {"id": "alkaline", "category": "国际新兴", "name": "碱水解(水葬)", "idea": "以水代火，温和水解。", "cost": "1.3万-3.6万元", "eco": "高", "legal": "美国、加拿大等部分地区合法", "process": ["遗体置于密闭设备", "用水和碱性溶液加温分解", "骨骼处理为骨灰状遗存"], "faq": ["不等同传统水葬。", "能耗通常低于火化。", "中国大陆尚非普遍服务。"]},
    {"id": "space", "category": "国际新兴", "name": "太空葬", "idea": "以星辰为墓，永恒航行。", "cost": "2万-9万元", "eco": "高", "legal": "由商业航天服务按国家地区规范执行", "process": ["取少量骨灰封装", "搭载火箭或航天载具", "进入亚轨道、地球轨道或深空纪念路径"], "faq": ["通常只发射少量骨灰。", "更像纪念服务而非完整安葬。", "需核对服务商资质。"]},
    {"id": "reef", "category": "国际新兴", "name": "珊瑚礁葬", "idea": "化为礁石，孕育海洋。", "cost": "2.8万-6.3万元", "eco": "高", "legal": "美国等地部分海域可办理", "process": ["骨灰混入环保礁体材料", "制成人工礁球", "投放到许可海域"], "faq": ["核心是海洋生态修复。", "需获得海域许可。", "中国大陆目前不是常规殡葬服务。"]},
    {"id": "diamond", "category": "国际新兴", "name": "钻石葬", "idea": "骨灰成钻，永恒随身。", "cost": "1万-24万元", "eco": "高", "legal": "作为纪念品加工在多国存在", "process": ["提取骨灰或毛发中的碳元素", "高温高压培育钻石", "切割镶嵌为纪念物"], "faq": ["情感价值高但费用跨度大。", "不是传统安葬替代品。", "要核对检测和交付凭证。"]},
    {"id": "promession", "category": "国际新兴", "name": "冰葬(Promession)", "idea": "冻干碎粉，如落叶归根。", "cost": "未商业化", "eco": "极高", "legal": "仍属概念或试验阶段", "process": ["遗体低温冷冻", "振动粉碎并干燥", "可降解容器入土"], "faq": ["商业可得性有限。", "常见于未来殡葬讨论。", "不能当作当前可办理服务。"]},
    {"id": "islamic", "category": "宗教", "name": "伊斯兰土葬", "idea": "速葬简葬，归于尘土。", "cost": "因地区而异", "eco": "高", "legal": "按宗教习俗和当地法规办理", "process": ["净身裹尸", "尽快完成礼拜与安葬", "墓穴和仪式从简"], "faq": ["通常不火化。", "强调平等和简朴。", "需与当地宗教场所和管理部门确认。"]},
    {"id": "hindu", "category": "宗教", "name": "印度教火葬+河葬", "idea": "火焚解脱，圣河归源。", "cost": "数百-数千元", "eco": "中", "legal": "印度等地依宗教和水域规定执行", "process": ["举行火化仪式", "收集骨灰", "按习俗撒入圣河或指定水域"], "faq": ["与恒河信仰相关。", "现代城市有环保约束。", "不同地区费用差异明显。"]},
    {"id": "jewish", "category": "宗教", "name": "犹太教土葬", "idea": "纯洁归土，人人平等。", "cost": "2万-7万元", "eco": "高", "legal": "按当地墓园和宗教规范办理", "process": ["尽快安排宗教仪式", "使用简朴棺木", "完成土葬和守丧"], "faq": ["通常避免火化。", "强调身体完整和简朴。", "需由当地社群指导。"]},
    {"id": "natural", "category": "生态葬", "name": "自然葬", "idea": "无痕归土，生态馈赠。", "cost": "7000-2.8万元", "eco": "极高", "legal": "部分国家和地区设有自然墓园", "process": ["选择自然墓园", "使用可降解材料", "以植物或坐标纪念"], "faq": ["通常不使用传统墓碑。", "管理规则强调生态保护。", "国内可参考节地生态葬政策。"]},
    {"id": "mushroom", "category": "生态葬", "name": "蘑菇葬", "idea": "菌丝净化，快速降解。", "cost": "1万-3万元", "eco": "极高", "legal": "多为国外概念产品或小范围实践", "process": ["使用菌丝材料制成裹尸衣或容器", "入土后促进分解", "减少污染残留"], "faq": ["不是中国常规殡葬服务。", "环保叙事强，需辨别商业宣传。", "适合作为死亡教育讨论。"]},
    {"id": "capsula", "category": "生态葬", "name": "树荚葬", "idea": "入蛋归土，化为大树。", "cost": "1.4万-2.8万元", "eco": "极高", "legal": "多为海外设计概念或有限实践", "process": ["遗体或骨灰放入可降解荚舱", "荚舱入土", "上方种植纪念树"], "faq": ["完整遗体树荚葬受法规限制更大。", "骨灰树葬更接近国内可行方案。", "应区分概念设计与可购买服务。"]},
]


def burial_methods() -> list[dict[str, Any]]:
    return BURIAL_METHODS


def burial_method(method_id: str) -> dict[str, Any] | None:
    for item in BURIAL_METHODS:
        if item["id"] == method_id:
            return item
    return None


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

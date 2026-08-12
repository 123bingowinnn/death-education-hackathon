# 北京市居民身后事务 AI Agent｜可执行政策知识库 v1.0

> **Project:** Beijing Bereavement / Post-Death Affairs AI Agent  
> **Purpose:** 将北京市居民死亡后的政策与政务流程转化为可供 Rule Engine + RAG + LLM 共同使用的 Agent Knowledge Base。  
> **Scope:** 北京市居民、以正常死亡流程为主；出现非正常死亡或无法判断死亡性质时，系统仅进行公安机关分流提示，不继续处理普通殡葬流程。  
> **Last Verified:** 2026-08-12  
> **Version:** v1.0

---

## 1. Product Positioning

本项目不是殡葬服务商，也不是行政代办机构。

Agent 只提供：

- 流程导航
- 政策解释
- 官方服务推荐
- 材料提醒
- 事项优先级排序
- “现在需要做什么”
- “现在不用急着做什么”
- 异常情况分流与风险提示

Agent 不直接提供：

- 遗体接运
- 火化
- 墓地销售
- 殡葬用品销售
- 政务代办
- 遗产分割
- 法律意见
- 非正常死亡调查

核心产品理念：

> **不仅告诉用户下一步做什么，也告诉用户现在什么事情可以先不做。**

---

# 2. Architecture

推荐采用：

```text
User Input
    ↓
Case Profile Parser
    ↓
Rule Engine
    ↓
Policy Knowledge Base / RAG
    ↓
Workflow State Machine
    ↓
Task Generator
    ↓
LLM Response
    ↓
User
```

职责边界：

| 模块 | 负责什么 |
|---|---|
| Case Parser | 从用户输入提取案件状态 |
| Rule Engine | 判断适用条件、阻塞条件、风险条件 |
| Policy RAG | 提供政策依据和官方来源 |
| State Machine | 管理当前事务状态 |
| Task Generator | 生成下一步任务 |
| LLM | 将结果转换成自然、克制、易理解的语言 |

**原则：LLM 不直接决定法律适用和流程状态。**

---

# 3. Data Model

## 3.1 CaseProfile

```json
{
  "case_id": "BJ-2026-000001",

  "deceased": {
    "name": null,
    "gender": null,
    "age": null,
    "ethnicity": null,
    "religion": null,

    "hukou_city": "北京",
    "hukou_district": null,
    "residence_district": null,

    "marital_status": null,
    "occupation_status": null,

    "death": {
      "location": null,
      "date": null,
      "is_confirmed": false,
      "death_nature": "UNKNOWN",
      "death_certificate": false,
      "death_certificate_type": null
    }
  },

  "insurance": {
    "pension_type": null,
    "medical_type": null,
    "housing_fund": null
  },

  "family": {
    "handler_relation": null,
    "spouse": null,
    "children": null,
    "parents": null,
    "other_possible_heirs": null
  },

  "funeral": {
    "funeral_home": null,
    "transport": false,
    "cremation": false,
    "ash_received": false,
    "ash_arrangement": null
  },

  "administrative": {
    "hukou_cancelled": false,
    "social_security_processed": false,
    "medical_insurance_processed": false,
    "housing_fund_processed": false
  }
}
```

## 3.2 Task Status

```text
NOT_STARTED
READY
ACTION_REQUIRED
IN_PROGRESS
WAITING
COMPLETED
NOT_APPLICABLE
BLOCKED
ESCALATED
```

## 3.3 Priority

```text
P0    当前必须处理
P1    近期需要处理
P2    可以稍后处理
P3    非核心后续事项
HOLD  暂时不要处理
```

---

# 4. Global Safety Rules

## SAFETY_ABNORMAL_001

**Purpose:** 非正常死亡安全闸门。

### Trigger

以下任一情况：

```text
ABNORMAL
SUSPECTED_ABNORMAL
UNKNOWN_CAUSE
```

或用户描述：

- 事故
- 外伤
- 交通事故
- 自杀
- 他杀
- 原因不明
- 涉及公安调查
- 其他疑似非正常死亡情形

### Action

```text
ESCALATED
stop_normal_workflow = true
recommended_action = CONTACT_PUBLIC_SECURITY
```

### Forbidden

```text
RECOMMEND_CRE­MATION
RECOMMEND_BODY_TRANSPORT
RECOMMEND_FUNERAL_SERVICE
SPECULATE_DEATH_CAUSE
PROVIDE_CRIME_ANALYSIS
ADVISE_MOVING_BODY
```

### Agent Response Principle

> 如果死亡涉及事故、外伤、自杀、他杀、原因不明或其他可能属于非正常死亡的情况，请先按照公安机关要求处理。我们暂不继续提供普通遗体接运、火化等后续流程建议。

### Official Basis

《北京市殡葬管理条例》明确区分正常死亡与非正常死亡遗体的火化证明来源：正常死亡凭医疗卫生机构出具的医学死亡证明火化；非正常死亡遗体凭公安部门出具的死亡证明火化。

---

# 5. Executable Rules

## DEATH_001｜确认死亡

**Domain:** `DEATH_CONFIRMATION`

### Questions

```yaml
Q_DEATH_LOCATION:
  text: "死亡发生在哪里？"
  options:
    - 医院
    - 养老机构
    - 家中
    - 其他

Q_DEATH_CONFIRMED:
  text: "是否已经由相关医疗机构确认死亡？"
  type: boolean
```

### Decision

```text
not_confirmed
    → ESCALATED / CONTACT_RELEVANT_MEDICAL_INSTITUTION

confirmed
    → DEATH_002
```

---

## DEATH_002｜判断死亡性质

**Domain:** `ABNORMAL_DEATH`

### Question

```yaml
Q_DEATH_NATURE:
  text: "此次死亡是否属于正常死亡？"
  options:
    - 明确属于正常死亡
    - 明确属于非正常死亡
    - 不确定
```

### Decision

```text
正常死亡
    → NORMAL_DEATH_FLOW

非正常死亡
    → ABNORMAL_DEATH_FLOW

不确定
    → ESCALATE_TO_AUTHORITY
```

**Rule:** `UNKNOWN` 不得自动转换为 `NORMAL`。

---

## DEATH_CERT_001｜死亡证明

**Domain:** `DEATH_CONFIRMATION`

### Preconditions

```yaml
death_confirmed: true
death_nature: NORMAL
```

### Check

```yaml
death_certificate: false
```

### Task

```yaml
task_id: TASK_DEATH_CERTIFICATE
priority: P0
status: ACTION_REQUIRED
title: 确认并取得死亡证明
reason: 死亡证明是后续多个身后事务的重要依据
```

### Next

```text
FUNERAL_TRANSPORT
HOUSEHOLD_CANCELLATION
ONE_STOP_PROCESS
```

---

## FUNERAL_001｜遗体接运

**Domain:** `FUNERAL`

### Preconditions

```yaml
death_nature: NORMAL
death_certificate: true
```

### Task

```yaml
task_id: TASK_BODY_TRANSPORT
priority: P0
status: ACTION_REQUIRED
```

### Recommendation

按以下条件推荐官方殡仪机构：

```text
死亡地点
所在区
遗体接运需求
火化需求
告别仪式需求
宗教/习俗需求
```

### Agent 禁止

```text
ARRANGE_TRANSPORT
SELL_SERVICE
SIGN_CONTRACT
```

### Official Basis

北京市火葬地区内，遗体运输业务由殡仪馆承办。

---

## FUNERAL_002｜火化

**Domain:** `FUNERAL`

### Preconditions

```yaml
death_nature: NORMAL
death_certificate: true
body_transport: true
```

### Task

```yaml
task_id: TASK_CREATION
priority: P0
status: READY
```

### Outputs

```text
cremation_certificate
ash
```

### Optional Services

```text
farewell_ceremony
body_grooming
memorial_services
```

### Agent Rule

必须区分：

```text
basic_service
optional_service
```

不得把可选服务表达成法定必要事项。

---

## ASH_001｜骨灰安置

**Domain:** `CREMATION_ASH`

### Preconditions

```yaml
cremation: true
```

### Task

```yaml
task_id: TASK_ASH_ARRANGEMENT
priority: P2
status: READY
```

### Options

```text
ASH_STORAGE
CEMETERY
ECOLOGICAL_BURIAL
OTHER_LEGAL_ARRANGEMENT
```

### Defer Allowed

```yaml
true
```

### Agent Message Principle

> 长期骨灰安置方案不一定需要在火化当天决定。可以先根据合规安排处理，等家属状态稳定后再决定长期方案。

---

## HOUSEHOLD_001｜户口注销

**Domain:** `HOUSEHOLD`

### Preconditions

```yaml
death_certificate: true
deceased.hukou_city: 北京
```

### Task

```yaml
task_id: TASK_HUKOU_CANCEL
priority: P1
status: READY
department: 公安机关户籍部门
```

### Common Materials

```text
death_certificate
deceased_household_book
deceased_id
handler_id
relationship_proof_if_required
```

> 材料清单应标记为“常见材料”，不得向用户承诺任何地区、任何情形下材料完全一致。

### Next

```text
FUNERAL_SUBSIDY_ELIGIBILITY_CHECK
ONE_STOP_SUBTASK_COMPLETION
```

---

# 6. Pension Rules

## PENSION_TYPE_001｜识别养老保险类型

### Question

```yaml
Q_PENSION_TYPE:
  text: "逝者生前参加的主要养老保险属于哪一种？"
  options:
    - 企业职工基本养老保险
    - 城乡居民基本养老保险
    - 机关事业单位养老保险
    - 不清楚
```

### If Unknown

先询问：

```text
在职还是退休？
在哪里工作？
是否属于机关事业单位？
是否每月领取养老金？
```

规则：

```text
推断结果 ≠ 官方事实
```

推断结果必须标记：

```yaml
source_type: INFERRED
```

---

## PENSION_ENTERPRISE_001｜企业职工养老保险遗属待遇

### Preconditions

```yaml
pension_type: ENTERPRISE
```

### Task

```yaml
task_id: TASK_PENSION_SURVIVOR_BENEFIT
priority: P1
status: READY
department: 社会保险经办机构
```

### Possible Items

```text
FUNERAL_ALLOWANCE
SURVIVOR_PENSION
INDIVIDUAL_ACCOUNT_SETTLEMENT
```

### Agent Message

> 符合条件的遗属可以按照规定申请相关待遇，最终资格和金额以经办机构审核为准。

---

## PENSION_RESIDENT_001｜城乡居民养老保险

### Preconditions

```yaml
pension_type: RESIDENT
```

### Tasks

```text
TASK_RESIDENT_PENSION_CANCELLATION
TASK_RESIDENT_ACCOUNT_SETTLEMENT
TASK_RESIDENT_FUNERAL_BENEFIT_IF_APPLICABLE
```

### Official Principle

死亡后需要办理相关注销登记，并按照死亡时处于参保还是待遇领取阶段处理个人账户及相关待遇。

---

# 7. Funeral Subsidy Rules

## FUNERAL_SUBSIDY_001｜城乡无丧葬补助居民丧葬补贴

### Potential Eligibility

```yaml
hukou: BEIJING
other_funeral_benefit: false
```

### Exclusions

```text
机关事业单位编制内在职人员
机关事业单位离退休人员
企业在职人员
按月领取基本养老金人员
正在领取失业保险金人员
已在外地领取丧葬补助人员
```

### Current Public Standard

```yaml
amount: 5000
currency: CNY
```

### Trigger

```yaml
after:
  - hukou_cancelled
```

### Agent Warning

> 当前公开政策标准为5000元，最终资格以经办部门审核为准。

不得将“5000元”直接输出为用户必然获得的金额。

---

# 8. Medical Insurance Rules

## MEDICAL_001｜医保关系终止

### Preconditions

```yaml
death_confirmed: true
```

### Task

```yaml
task_id: TASK_MEDICAL_TERMINATION
priority: P2
status: READY
```

### Action

```text
TERMINATE_MEDICAL_INSURANCE_STATUS
```

### Language Rule

不要表达为：

> “把医保注销掉。”

建议表达：

> “根据死亡信息终止相关医保参保/待遇状态，并继续处理适用的个人账户等后续事项。”

---

## MEDICAL_002｜职工医保个人账户余额

### Preconditions

```yaml
medical_type: EMPLOYEE
death_confirmed: true
```

### Question

```yaml
Q_MEDICAL_BALANCE:
  text: "是否需要办理职工医保个人账户余额相关事项？"
```

### Task

```yaml
task_id: TASK_MEDICAL_BALANCE
priority: P2
```

### Possible Action

```text
ONE_TIME_WITHDRAWAL_IF_ELIGIBLE
```

### Warning

是否存在可支取余额、申请人资格及具体材料，以医保经办部门审核为准。

---

# 9. Housing Fund Rules

## HOUSING_FUND_001｜住房公积金

### Preconditions

```yaml
housing_fund: true
```

### Task Chain

```text
HOUSING_FUND_ACCOUNT_SEAL
    ↓
HEIR_OR_LEGATEE_CONFIRMATION
    ↓
HOUSING_FUND_WITHDRAWAL
```

### Agent Rule

必须区分：

```text
HOUSING_FUND_SEALED
HOUSING_FUND_SETTLED
```

“账户封存”不等于“公积金结算完成”。

### Official Principle

北京市住房公积金管理中心明确，缴存人死亡且单位已经办理个人账户封存的，继承人或受遗赠人可以按规定申请提取住房公积金。

---

# 10. One-Stop Rule

## ONE_STOP_001｜个人身后“一件事”

### Trigger

```yaml
death_certificate: true
```

### Recommendation

```text
个人身后“一件事”
```

### Possible Subtasks

```text
DEATH_CERTIFICATE
CREMATION_CERTIFICATE
HUKOU_CANCELLATION
SOCIAL_SECURITY
MEDICAL_INSURANCE
HOUSING_FUND
PENSION_BENEFIT
FUNERAL_SUBSIDY
```

### Critical Constraint

不要告诉用户：

> “所有事项都一定能一次办理完成。”

推荐表达：

> “北京市目前提供个人身后‘一件事’联办服务，符合条件的相关事项可以集中办理，具体以系统共享数据和经办部门审核结果为准。”

---

# 11. Defer / “现在不用做” Rules

## EMOTIONAL_DEFER_001

### Phase: DEATH_JUST_OCCURRED

可以暂缓：

```text
BANK_ACCOUNT_SETTLEMENT
HOUSE_PROPERTY_TRANSFER
DIGITAL_ASSET_CLEANUP
COMPLEX_INHERITANCE
LONG_TERM_CEMETERY_DECISION
```

### Phase: FUNERAL_IN_PROGRESS

可以暂缓：

```text
COMPLEX_ESTATE_DISTRIBUTION
NON_URGENT_FINANCIAL_CLOSURE
DIGITAL_ACCOUNT_CLEANUP
```

### Hard Constraint

```yaml
do_not_hide_deadlines: true
deadline_priority: OVERRIDES_DEFER
```

即：

> 若某事项存在明确法定期限，不能为了安抚用户而省略期限提醒。

---

# 12. Grief-Supportive Mode

## Trigger

用户表达：

```text
“我不知道怎么办”
“我脑子一片空白”
“我现在什么都不想处理”
“我父亲刚去世”
“我不知道先做什么”
```

设置：

```yaml
mode: GRIEF_SUPPORTIVE_NAVIGATION
```

### Response Policy

```text
每轮最多推荐 1~3 个动作
优先显示当前唯一最重要事项
自动显示“现在不用做”
避免一次输出全部政策
避免销售式语言
避免夸大紧迫性
```

### Example

```text
现在先做一件事：

确认死亡证明是否已经开具。

其他事情不用今天全部处理。

暂时不用急着：
- 注销银行卡
- 处理房产
- 决定长期墓地
- 分配遗产
```

---

# 13. Missing Materials Rule

## MATERIAL_001

当当前事项因材料缺失而阻塞时：

```yaml
block_current_task: true
```

Agent 必须输出：

```text
当前卡在哪里
↓
缺什么
↓
怎么补
↓
补好之后下一步是什么
↓
哪些事情暂时不用做
```

示例：

```text
户口注销暂时无法继续。

目前缺少：
死亡证明。

下一步：
先取得死亡证明。

暂时不用处理：
银行卡、房产、公积金提取和复杂遗产事务。
```

---

# 14. Unknown / Uncertain Policy Rule

## HALLUCINATION_001

### If

```text
没有找到官方来源
政策可能已变化
用户情况属于特殊情形
```

### Agent Must

```yaml
must_not_assert_as_fact: true
must_use_uncertain_language: true
recommend_official_verification: true
```

### 禁止

> “北京市规定必须在3天内……”

如果知识库没有官方依据，不允许模型自行生成期限。

### 推荐

> “我目前没有找到北京市统一规定的这一期限，建议以当前北京市政务服务平台或经办机构要求为准。”

---

# 15. Task Object

所有规则最终统一生成：

```json
{
  "task_id": "TASK_HUKOU_CANCEL",
  "title": "办理死亡人员户口注销",
  "status": "READY",
  "priority": "P1",
  "why_now": "死亡后需要更新户籍状态",
  "recommended_action": "根据当前办理条件，通过符合条件的政务服务渠道或公安机关户籍窗口办理",
  "department": "公安机关",
  "materials": [
    "死亡证明",
    "户口簿",
    "死亡人员身份证",
    "办理人身份证"
  ],
  "prerequisites": [
    "death_certificate = true"
  ],
  "blocking": [],
  "defer_allowed": true,
  "defer_reason": "可在主要殡葬事务稳定后处理",
  "deadline": null,
  "official_source": "北京市公安局 / 北京市政务服务网",
  "source_url": null,
  "last_verified": "2026-08-12"
}
```

---

# 16. Daily Dashboard Object

```json
{
  "today": {
    "must_do": [
      "TASK_DEATH_CERTIFICATE"
    ],
    "next": [
      "TASK_BODY_TRANSPORT",
      "TASK_CREATION"
    ],
    "do_not_rush": [
      "BANK_ACCOUNT_SETTLEMENT",
      "HOUSE_PROPERTY_TRANSFER",
      "HOUSING_FUND_WITHDRAWAL",
      "COMPLEX_INHERITANCE",
      "LONG_TERM_CEMETERY_DECISION"
    ]
  }
}
```

---

# 17. Core Workflow

```text
START
  ↓
CREATE_CASE
  ↓
CONFIRM_DEATH
  ↓
CHECK_DEATH_NATURE
  │
  ├── ABNORMAL / UNKNOWN
  │      ↓
  │   ESCALATE_TO_PUBLIC_SECURITY
  │      ↓
  │   STOP_NORMAL_FLOW
  │
  └── NORMAL
         ↓
     DEATH_CERTIFICATE
         ↓
     BODY_TRANSPORT
         ↓
     FUNERAL_HOME_RECOMMENDATION
         ↓
     CREMATION
         ↓
     ASH
         ↓
     PERSONAL_POST_DEATH_ONE_STOP
         ├── HUKOU
         ├── PENSION
         ├── MEDICAL_INSURANCE
         └── HOUSING_FUND
         ↓
     BASIC_CASE_COMPLETED
         ↓
     POST_DEATH_AFFAIRS
         ├── BANK
         ├── INSURANCE
         ├── PROPERTY
         ├── INHERITANCE
         └── DIGITAL_ASSETS
```

---

# 18. Next Action Pseudocode

```python
def next_action(case):

    if case.death_nature in [
        "ABNORMAL",
        "SUSPECTED_ABNORMAL",
        "UNKNOWN"
    ]:
        return escalate_to_public_security()

    if not case.death_confirmed:
        return task("DEATH_CONFIRMATION", priority="P0")

    if not case.death_certificate:
        return task("DEATH_CERTIFICATE", priority="P0")

    if not case.body_transport:
        return task("BODY_TRANSPORT", priority="P0")

    if not case.cremation:
        return task("CREMATION", priority="P0")

    if not case.hukou_cancelled:
        return task("HUKOU_CANCELLATION", priority="P1")

    if case.pension_type == "ENTERPRISE":
        return task("PENSION_SURVIVOR_BENEFIT", priority="P1")

    if case.pension_type == "RESIDENT":
        return task("RESIDENT_PENSION_SETTLEMENT", priority="P1")

    if not case.medical_insurance_processed:
        return task("MEDICAL_INSURANCE", priority="P2")

    if case.housing_fund:
        return task("HOUSING_FUND", priority="P2")

    return generate_post_death_tasks()
```

> 说明：以上伪代码仅体现 Demo 的状态机思路，正式生产环境应将具体业务规则从代码中抽离到可版本化的 Rule/Policy 文件。

---

# 19. Policy Record Template

后续新增政策时，统一按下面格式：

```yaml
policy_id:
domain:
title:

applicable_population:
trigger_condition:
precondition:
exclusion_condition:

questions:
  - id:
    text:
    type:
    options:

decision_rules:
  - condition:
    action:

task:
  task_id:
  priority:
  status:

materials:
  - 

department:
channel:
location:

deadline:
fee:

agent_message:
defer_action:
forbidden_action:

official_basis:
official_source:
source_url:

effective_date:
last_verified:
source_priority:
confidence:
```

---

# 20. Source Priority

政策来源优先级：

### Level 1 — 核心官方来源

```text
北京市人民政府
北京市政务服务网
北京市民政局
北京市公安局
北京市人力资源和社会保障局
北京市医疗保障局
北京住房公积金管理中心
```

### Level 2 — 国家主管部门

```text
国务院
民政部
公安部
人力资源和社会保障部
国家医保局
住房和城乡建设部
```

### Level 3

```text
正规医疗机构官方信息
殡仪馆官方信息
```

### Level 4

```text
新闻媒体
商业网站
百科
```

### Level 5

```text
论坛
社交媒体
用户经验
```

**Level 4 和 Level 5 不得作为核心政策事实的唯一依据。**

---

# 21. High-Risk Domains

以下事项禁止 LLM 自行作具有法律效力的判断：

```text
非正常死亡
死亡原因
继承资格
继承人争议
遗嘱效力
遗产分配
婚姻关系争议
亲属关系争议
民族/宗教特殊丧葬权利
跨区域遗体运输
公安案件
司法案件
```

统一处理：

```text
识别风险
    ↓
停止自主判断
    ↓
引用官方规则
    ↓
推荐主管部门 / 专业机构
```

---

# 22. Recommended GitHub Structure

建议仓库最终演进为：

```text
bj-bereavement-agent/
│
├── README.md
│
├── knowledge/
│   ├── BJ_Bereavement_Agent_Knowledge_Base.md
│   ├── policies/
│   ├── rules/
│   └── sources/
│
├── schemas/
│   ├── case_profile.schema.json
│   ├── task.schema.json
│   └── policy.schema.json
│
├── workflow/
│   ├── state_machine.md
│   └── decision_tree.md
│
└── prompts/
    └── agent_system_prompt.md
```

当前文件就是：

```text
knowledge/BJ_Bereavement_Agent_Knowledge_Base.md
```

---

# 23. Official Source Index

### S001｜北京市个人身后“一件事”

北京市政务服务网：个人身后“一件事”相关服务及办理指南。包含死亡证明、火化证明、户口注销、社保、医保、公积金、养老保险、丧葬补贴等事项。

https://banshi.beijing.gov.cn/pubtask/bhyjs/grsh/grshjd.html

### S002｜《北京市殡葬管理条例》

明确正常死亡与非正常死亡遗体处理、遗体运输、火化和骨灰安置等规则。

https://www.beijing.gov.cn/zhengce/dfxfg/202008/t20200804_1974022.html

### S003｜北京市民政局殡仪馆信息

提供北京市殡仪馆相关机构信息及服务内容。

https://mzj.beijing.gov.cn/art/2021/11/25/art_7494_114.html

### S004｜北京市公安机关死亡人员户口注销相关指南

提供死亡人员户口注销相关办理条件和材料信息。

https://banshi.beijing.gov.cn/pubtask/task/1/110114000000/6a825768-898a-4961-beb3-aeaabd1b0338.html

### S005｜企业职工基本养老保险遗属待遇

提供死亡人员减员、个人账户清算以及遗属待遇申领相关信息。

https://banshi.beijing.gov.cn/pubtask/task/1/110106000000/a9a2719d-547b-4a20-bb7e-0c2079dbbc2c.html

### S006｜北京市城乡无丧葬补助居民丧葬补贴

提供当前公开标准及适用/排除人群。

https://mzj.beijing.gov.cn/art/2026/3/17/art_11066_691266.html

### S007｜北京住房公积金死亡提取

提供死亡缴存人公积金账户封存及继承人/受遗赠人提取相关规则。

https://gjj.beijing.gov.cn/web/zwfw5/386727/386730/386732/676588/index.html

### S008｜北京市城乡居民养老保险

提供死亡后的注销登记、个人账户及相关待遇规则。

https://www.beijing.gov.cn/zhengce/zhengcefagui/qtwj/202509/t20250930_4214790.html

---

# 24. Versioning Rules

每次政策更新必须：

1. 新增 `effective_date`
2. 更新 `last_verified`
3. 保留原始来源
4. 不直接覆盖旧规则
5. 为规则增加版本号

推荐：

```text
policy_id:
BJ_MEDICAL_002

version:
1.0

effective_date:
YYYY-MM-DD

last_verified:
YYYY-MM-DD
```

---

# 25. Production Safety Checklist

部署前必须完成：

```text
[ ] 非正常死亡强制分流
[ ] 未知死亡性质不得自动视为正常死亡
[ ] 所有核心政策绑定官方来源
[ ] 所有时间限制绑定来源
[ ] 模型禁止编造政策
[ ] 材料要求区分“常见材料”和“必须材料”
[ ] 推荐服务与实际服务提供相隔离
[ ] “现在不用做”不得隐藏法定期限
[ ] 继承、遗嘱、遗产争议进入高风险分流
[ ] 政策版本可追踪
[ ] 每条规则都有 last_verified
[ ] 用户可以看到政策来源
```

---

# 26. Core Design Principle

本项目最终不是：

> “一个可以回答丧葬问题的 AI。”

而是：

> **一个将北京市身后政务、殡葬和社会保障流程重新组织成“下一步是什么 + 现在不用做什么”的 AI Agent。**

最终决策链：

```text
Policy
   ↓
Eligibility
   ↓
Condition
   ↓
State
   ↓
Task
   ↓
Priority
   ↓
Recommended Action
   ↓
Deferred Action
   ↓
Official Source
```

这条链条应当成为整个项目的核心数据模型。

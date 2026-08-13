(() => {
  "use strict";

  const STORAGE_KEY = "guicheng_state_v7";
  const API_TIMEOUT = 85000;
  const BUDGET_LABELS = {
    relief: "需要费用减免",
    under1000: "1000 元以内",
    "1000to5000": "1000-5000 元",
    over5000: "5000 元以上",
    unsure: "还不确定",
  };
  const OFFICIAL_LABELS = {
    verified: "政府页面有记录",
    likely: "政府记录待确认",
    unverified: "政府记录待确认",
  };
  const PRICE_LABELS = {
    verified: "价目有来源",
    partial: "部分价目可核验",
    phone_required: "价格待电话确认",
  };
  const FIT_LABELS = {
    within: "符合所选预算",
    uncertain: "预算适配待确认",
    over: "超出所选预算",
  };
  const NODE_ICONS = {
    confirm: "phone",
    certificate: "file-check-2",
    facility: "landmark",
    burial: "archive",
    accounts: "shield-check",
  };
  const NODE_COLORS = ["blue", "apricot", "lavender", "coral", "blue"];
  const FIRST_ACTIONS = {
    confirm: "先联系现场的医疗或负责人员，确认下一步由谁处理",
    certificate: "先联系医院护士站或医务处，问清开具窗口与材料",
    burial: "先确认合规寄存方式，不需要在当天做长期决定",
    accounts: "先列好资产、债务和账户清单，再逐项办理",
  };

  let recommendationRequestId = 0;
  let flowRequestId = 0;
  let questionAdvanceTimer = null;
  let communityLoadedCity = "";
  let authMode = "login";
  let accountSaveTimer = null;

  const state = {
    activeTab: "process",
    processView: "intake",
    questionStep: 0,
    legalConfirmed: false,
    answers: { place: null, budget: null },
    city: "北京",
    note: "",
    mode: "standard",
    tapSpeech: false,
    profileAlias: "",
    flow: null,
    completed: [],
    checks: {},
    currentNodeId: null,
    recommendations: null,
    location: null,
    locationLabel: "",
    user: null,
    portrait: { image: null, filter: "color", zoom: 1, y: 0 },
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    hydrateState();
    bindStaticEvents();
    applyMode();
    updateCityUI();
    if (state.flow) {
      state.processView = "home";
      showProcessView("home", false);
      renderHome();
    } else {
      renderQuestion(state.questionStep);
      showProcessView("intake", false);
    }
    showTab(state.activeTab, false);
    updateProfile();
    updateIcons();
    initializeAccount();
  }

  function hydrateState() {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (!stored || typeof stored !== "object") return;
      state.activeTab = ["info", "process", "profile"].includes(stored.activeTab) ? stored.activeTab : "process";
      state.mode = stored.mode === "elder" ? "elder" : "standard";
      state.tapSpeech = Boolean(stored.tapSpeech);
      state.profileAlias = typeof stored.profileAlias === "string" ? stored.profileAlias.slice(0, 12) : "";
      state.legalConfirmed = Boolean(stored.legalConfirmed);
      state.answers = {
        place: ["hospital", "home", "public", "care"].includes(stored.answers?.place) ? stored.answers.place : null,
        budget: Object.hasOwn(BUDGET_LABELS, stored.answers?.budget) ? stored.answers.budget : null,
      };
      state.questionStep = Number.isInteger(stored.questionStep) ? Math.min(2, Math.max(0, stored.questionStep)) : 0;
      if (!state.legalConfirmed) state.questionStep = 0;
      if (state.questionStep > 1 && !state.answers.place) state.questionStep = 1;
      state.flow = stored.flow?.nodes && Array.isArray(stored.flow.nodes) ? { ...stored.flow, note: "" } : null;
      state.city = String(stored.city || state.flow?.city || "北京").trim().slice(0, 30) || "北京";
      state.completed = Array.isArray(stored.completed) ? stored.completed.filter((item) => typeof item === "string") : [];
      state.checks = stored.checks && typeof stored.checks === "object" ? stored.checks : {};
    } catch (_error) {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  function persistState() {
    const serializable = {
      activeTab: state.activeTab,
      mode: state.mode,
      tapSpeech: state.tapSpeech,
      profileAlias: state.profileAlias,
      legalConfirmed: state.legalConfirmed,
      answers: state.answers,
      questionStep: state.questionStep,
      city: state.city,
      flow: state.flow ? { ...state.flow, note: "" } : null,
      completed: state.completed,
      checks: state.checks,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(serializable));
    scheduleAccountSave();
  }

  function bindStaticEvents() {
    $$('[data-tab]').forEach((button) => button.addEventListener("click", () => showTab(button.dataset.tab)));
    $$('[data-info-panel]').forEach((button) => button.addEventListener("click", () => showInfoPanel(button.dataset.infoPanel)));
    $$('[data-mode]').forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));
    $("#brand-home").addEventListener("click", () => showTab("process"));
    $("#global-city").addEventListener("click", openCityDialog);
    $("#profile-city").addEventListener("click", openCityDialog);
    $("#city-form").addEventListener("submit", submitCity);
    $("#question-card").addEventListener("click", handleQuestionClick);
    $("#question-card").addEventListener("input", (event) => {
      if (event.target.id === "note-input") state.note = event.target.value;
    });
    $("#flow-path").addEventListener("click", (event) => {
      const button = event.target.closest("[data-node-id]");
      if (button) openNode(button.dataset.nodeId);
    });
    $("#open-next-node").addEventListener("click", () => openNode(nextIncompleteId()));
    $("#home-current-action").addEventListener("click", () => openNode(nextIncompleteId()));
    $("#home-view-all").addEventListener("click", () => {
      showProcessView("overview");
      renderOverview();
    });
    $("#home-customize").addEventListener("click", restartFlow);
    $("#home-next-list").addEventListener("click", (event) => {
      const button = event.target.closest("[data-node-id]");
      if (button) openNode(button.dataset.nodeId);
    });
    $("#overview-back").addEventListener("click", () => {
      showProcessView("home");
      renderHome();
    });
    $("#back-to-overview").addEventListener("click", () => {
      showProcessView("overview");
      renderOverview();
    });
    $("#restart-flow").addEventListener("click", restartFlow);
    $("#toggle-node-complete").addEventListener("click", toggleCurrentNode);
    $("#detail-main").addEventListener("change", handleChecklistChange);
    $("#detail-main").addEventListener("click", handleDetailClick);
    document.addEventListener("click", handleDelegatedClick);
    $("#open-help-dialog").addEventListener("click", () => openDialog("#help-dialog"));
    $("#refresh-help").addEventListener("click", loadHelpWall);
    $("#help-form").addEventListener("submit", submitHelpPost);
    $("#help-posts").addEventListener("submit", submitHelpReply);
    $("#login-button").addEventListener("click", () => {
      setAuthMode("login");
      openDialog("#login-dialog");
    });
    $$('[data-auth-mode]').forEach((button) => button.addEventListener("click", () => setAuthMode(button.dataset.authMode)));
    $("#logout-button").addEventListener("click", logoutAccount);
    $("#login-form").addEventListener("submit", submitLogin);
    $("#tap-speech").addEventListener("change", (event) => {
      state.tapSpeech = event.target.checked;
      applyMode();
      persistState();
    });
    $("#read-page").addEventListener("click", readCurrentPage);
    $("#clear-local-data").addEventListener("click", clearProgress);
    bindPortraitEvents();
  }

  function handleDelegatedClick(event) {
    const nodeLink = event.target.closest("[data-open-node]");
    if (nodeLink) openNode(nodeLink.dataset.openNode);
    const cityLink = event.target.closest("[data-open-city]");
    if (cityLink) openCityDialog();
    const action = event.target.closest("[data-profile-action]")?.dataset.profileAction;
    if (action === "progress") {
      showTab("process");
      if (state.flow) {
        showProcessView("overview");
        renderOverview();
      }
    } else if (action === "portrait") {
      $("#profile-home").hidden = true;
      $("#profile-portrait").hidden = false;
      drawPortrait();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (event.target.closest("#back-profile")) {
      $("#profile-portrait").hidden = true;
      $("#profile-home").hidden = false;
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    handleTapSpeech(event);
  }

  function showTab(name, focus = true) {
    if (!["info", "process", "profile"].includes(name)) return;
    state.activeTab = name;
    $("#app").classList.remove("tab-info", "tab-process", "tab-profile");
    $("#app").classList.add(`tab-${name}`);
    $$('[data-tab-page]').forEach((page) => {
      const active = page.dataset.tabPage === name;
      page.hidden = !active;
      page.classList.toggle("is-active", active);
    });
    $$('[data-tab]').forEach((button) => {
      const active = button.dataset.tab === name;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-current", active ? "page" : "false");
    });
    if (name === "info") loadInfoPanel();
    if (name === "profile") updateProfile();
    persistState();
    if (focus) {
      window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
      setTimeout(() => $("#main-content").focus({ preventScroll: true }), 40);
    }
    updateIcons();
  }

  function showInfoPanel(name) {
    $$('[data-info-view]').forEach((panel) => { panel.hidden = panel.dataset.infoView !== name; });
    $$('[data-info-panel]').forEach((button) => {
      const active = button.dataset.infoPanel === name;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    });
    loadInfoPanel();
    updateIcons();
  }

  function loadInfoPanel() {
    const active = $('[data-info-panel].is-active')?.dataset.infoPanel || "help";
    if (active === "help") loadHelpWall();
    if (active === "policy" || active === "phone") loadCommunityInfo();
  }

  function showProcessView(name, focus = true) {
    state.processView = name;
    $("#app").classList.remove("process-intake", "process-generating", "process-home", "process-overview", "process-detail");
    $("#app").classList.add(`process-${name}`);
    ["intake", "generating", "home", "overview", "detail"].forEach((view) => {
      const element = $(`#process-${view}`);
      if (element) element.hidden = view !== name;
    });
    if (focus) window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    updateIcons();
  }

  function renderQuestion(step) {
    clearTimeout(questionAdvanceTimer);
    state.questionStep = Math.min(2, Math.max(0, step));
    const progress = $("#question-progress");
    progress.innerHTML = [0, 1, 2].map((index) => `<span class="${index === state.questionStep ? "is-current" : index < state.questionStep ? "is-done" : ""}"></span>`).join("");
    const card = $("#question-card");
    if (state.questionStep === 0) {
      card.innerHTML = `
        <div class="question-card-top"><span class="question-count">1 / 3</span><span class="question-symbol">${iconHtml("shield-check")}</span></div>
        <p class="question-label">办理权限确认</p>
        <h2>开始前，请先确认您可以办理这些事项</h2>
        <p class="question-copy">归程会按照逝者的直系亲属，或已获授权办理人的情况整理流程。</p>
        <div class="answer-list single-answer">
          <button type="button" data-question-answer="legal" data-value="true"><span>${iconHtml("check")}<strong>我是直系亲属，或已获得直系亲属授权</strong></span>${iconHtml("arrow-right")}</button>
        </div>
        <p class="question-footnote">本指引用于办事整理，不替代医疗、公安、民政或法律机关的正式意见。</p>`;
    } else if (state.questionStep === 1) {
      card.innerHTML = `
        <div class="question-card-top"><button class="question-back" type="button" data-question-back>${iconHtml("arrow-left")}上一步</button><span class="question-count">2 / 3</span></div>
        <p class="question-label">当前情况</p>
        <h2>亲人是在哪里离世的？</h2>
        <p class="question-copy">请选择最符合的情况</p>
        <div class="answer-grid">
          ${questionOption("place", "hospital", "hospital", "医院内", "先联系护士站或医务处")}
          ${questionOption("place", "home", "house", "家中", "正常死亡联系社区卫生；情况不明先拨 110")}
          ${questionOption("place", "public", "building-2", "公共场所", "先拨 110，并保护现场")}
          ${questionOption("place", "care", "heart-handshake", "养老机构", "由机构值班人员与医务人员衔接")}
        </div>`;
    } else {
      card.innerHTML = `
        <div class="question-card-top"><button class="question-back" type="button" data-question-back>${iconHtml("arrow-left")}上一步</button><span class="question-count">3 / 3</span></div>
        <div class="question-context">
          <button type="button" data-open-city>${iconHtml("map-pin")}<span><small>办理城市</small><strong>${escapeHtml(state.city)}</strong></span>${iconHtml("chevron-right")}</button>
          <details class="note-capture">
            <summary>${iconHtml("message-square-more")}<span><small>补充情况</small><strong>可选</strong></span>${iconHtml("chevron-down")}</summary>
            <label for="note-input" class="sr-only">补充情况</label>
            <textarea id="note-input" maxlength="500" rows="3" placeholder="例如：已经拿到死亡证明，希望优先看收费透明的机构。">${escapeHtml(state.note)}</textarea>
            <p>请勿填写姓名、证件号、详细病历、电话或银行信息。本次整理后不在浏览器长期保存。</p>
          </details>
        </div>
        <p class="question-label">费用需求</p>
        <h2>您希望怎样控制办理支出？</h2>
        <div class="answer-list budget-answers">
          ${questionOption("budget", "relief", "hand-heart", "需要费用减免", "优先核对救助条件和基本服务")}
          ${questionOption("budget", "under1000", "wallet-minimal", "1000 元以内", "只看基本必选项")}
          ${questionOption("budget", "1000to5000", "receipt-text", "1000-5000 元", "基本服务与必要告别项目")}
          ${questionOption("budget", "over5000", "badge-dollar-sign", "5000 元以上", "仍会区分必选与自选项目")}
          ${questionOption("budget", "unsure", "list-checks", "还不确定", "先看完整信息，不替您决定支出")}
        </div>`;
    }
    $("#question-error").hidden = true;
    persistState();
    updateIcons();
  }

  function questionOption(kind, value, icon, title, copy) {
    const selected = state.answers[kind] === value;
    return `<button class="answer-option ${selected ? "is-selected" : ""}" type="button" data-question-answer="${kind}" data-value="${value}"><span class="answer-icon">${iconHtml(icon)}</span><span><strong>${escapeHtml(title)}</strong><small>${escapeHtml(copy)}</small></span>${iconHtml("arrow-right")}</button>`;
  }

  function handleQuestionClick(event) {
    if (event.target.closest("[data-question-back]")) {
      renderQuestion(state.questionStep - 1);
      return;
    }
    const answer = event.target.closest("[data-question-answer]");
    if (!answer) return;
    $$("[data-question-answer]", $("#question-card")).forEach((button) => {
      button.disabled = true;
      button.classList.toggle("is-selected", button === answer);
    });
    const kind = answer.dataset.questionAnswer;
    if (kind === "legal") {
      state.legalConfirmed = true;
      persistState();
      questionAdvanceTimer = setTimeout(() => renderQuestion(1), 360);
    } else if (kind === "place") {
      state.answers.place = answer.dataset.value;
      persistState();
      questionAdvanceTimer = setTimeout(() => renderQuestion(2), 360);
    } else if (kind === "budget") {
      state.answers.budget = answer.dataset.value;
      state.note = $("#note-input")?.value.trim() || state.note;
      persistState();
      questionAdvanceTimer = setTimeout(generateFlow, 460);
    }
  }

  async function generateFlow() {
    if (!state.legalConfirmed || !state.answers.place || !state.answers.budget) {
      renderQuestion(!state.legalConfirmed ? 0 : !state.answers.place ? 1 : 2);
      return;
    }
    const requestId = ++flowRequestId;
    const requestCity = state.city;
    showProcessView("generating");
    const steps = $$(".generating-steps li");
    const timers = [
      setTimeout(() => { steps[0]?.classList.remove("is-active"); steps[0]?.classList.add("is-done"); steps[1]?.classList.add("is-active"); updateIcons(); }, 520),
      setTimeout(() => { steps[1]?.classList.remove("is-active"); steps[1]?.classList.add("is-done"); steps[2]?.classList.add("is-active"); updateIcons(); }, 1080),
    ];
    try {
      const [flow] = await Promise.all([
        apiFetch("/api/generate-flow", {
          method: "POST",
          body: JSON.stringify({
            legal_confirmed: true,
            place: state.answers.place,
            budget: state.answers.budget,
            city: state.city,
            note: state.note,
            personalize: true,
          }),
        }),
        delay(1650),
      ]);
      if (requestId !== flowRequestId || requestCity !== state.city) return;
      state.flow = flow;
      state.currentNodeId = null;
      state.completed = [];
      state.checks = {};
      state.recommendations = null;
      state.location = null;
      state.locationLabel = "";
      persistState();
      showProcessView("home");
      renderHome();
      updateProfile();
    } catch (error) {
      if (requestId !== flowRequestId) return;
      showProcessView("intake");
      renderQuestion(2);
      const message = $("#question-error");
      message.textContent = error.message;
      message.hidden = false;
    } finally {
      timers.forEach(clearTimeout);
    }
  }

  function renderHome() {
    if (!state.flow) return;
    const nextId = nextIncompleteId();
    const nextNode = nodeById(nextId) || state.flow.nodes[0];
    const completedCount = state.flow.nodes.filter((node) => state.completed.includes(node.id)).length;
    $("#home-current-title").textContent = nextNode.title;
    $("#home-current-action").innerHTML = `${completedCount === state.flow.nodes.length ? "回顾办理步骤" : "查看怎么做"}${iconHtml("chevron-right")}`;
    $("#home-progress").innerHTML = state.flow.nodes.map((node, index) => {
      const complete = state.completed.includes(node.id);
      const current = node.id === nextId && !complete;
      const shortLabels = ["确认", "证明", "机构", "安放", "权益"];
      return `<button class="${complete ? "is-complete" : ""} ${current ? "is-current" : ""}" type="button" data-node-id="${escapeAttr(node.id)}"><b>${complete ? iconHtml("check") : node.number}</b><span>${shortLabels[index]}</span></button>`;
    }).join("");
    $("#home-progress").querySelectorAll("[data-node-id]").forEach((button) => button.addEventListener("click", () => openNode(button.dataset.nodeId)));
    $("#home-next-list").innerHTML = state.flow.nodes.filter((node) => node.id !== nextId).slice(0, 2).map((node, index) => `
      <button class="home-next-row" type="button" data-node-id="${escapeAttr(node.id)}">
        <span class="home-next-icon is-${NODE_COLORS[(node.number - 1) % NODE_COLORS.length]}">${iconHtml(NODE_ICONS[node.id] || "circle")}</span>
        <span><strong>${escapeHtml(node.title)}</strong><small>${escapeHtml(node.time)} · ${escapeHtml(node.location)}</small></span>
        ${iconHtml("chevron-right")}
      </button>`).join("");
    updateProfile();
    updateIcons();
  }

  function renderOverview() {
    if (!state.flow) return;
    const completedCount = state.flow.nodes.filter((node) => state.completed.includes(node.id)).length;
    $("#flow-context").textContent = `${state.flow.city} · ${state.flow.place_label} · ${state.flow.budget_label}`;
    $("#progress-count").textContent = `${completedCount}/${state.flow.nodes.length}`;
    $("#progress-bar").style.width = `${(completedCount / state.flow.nodes.length) * 100}%`;
    const nextId = nextIncompleteId();
    const nextNode = nodeById(nextId);
    $("#next-action-text").textContent = nextNode ? `第 ${nextNode.number} 步 · ${nextNode.title}` : "五个节点都已完成";
    $("#open-next-node").textContent = nextNode ? "查看" : "回顾";
    $("#flow-path").innerHTML = state.flow.nodes.map((node) => {
      const complete = state.completed.includes(node.id);
      const current = node.id === nextId && !complete;
      const materialsDone = (state.checks[node.id] || []).length;
      const substepText = node.substeps?.length ? `${node.substeps.length} 个子事项` : `${node.materials.length} 项材料`;
      return `
        <button class="route-node tone-${NODE_COLORS[(node.number - 1) % NODE_COLORS.length]} ${complete ? "is-complete" : ""} ${current ? "is-current" : ""}" type="button" data-node-id="${escapeAttr(node.id)}">
          <span class="route-pin">${complete ? iconHtml("check") : node.number}</span>
          <span class="route-icon">${iconHtml(NODE_ICONS[node.id] || "circle")}</span>
          <span class="route-copy">
            <strong>${escapeHtml(node.title)}</strong>
            <small>${escapeHtml(node.location)}</small>
            <span class="route-status">${complete ? "已完成" : current ? "进行中" : "待开始"}</span>
          </span>
          <span class="route-open">${iconHtml("chevron-right")}</span>
        </button>`;
    }).join("");
    const existingPersonal = $("#personalized-overview");
    if (existingPersonal) existingPersonal.remove();
    const personalization = state.flow.personalization;
    const evidenceBand = $(".evidence-band");
    if (personalization && evidenceBand) {
      evidenceBand.insertAdjacentHTML("beforebegin", `
        <section class="personalized-overview" id="personalized-overview">
          <span>${iconHtml(personalization.generated_by === "kimi" ? "sparkles" : "list-checks")}</span>
          <div><small>${personalization.generated_by === "kimi" ? "Kimi 已整理" : "按规则整理"}</small><strong>${escapeHtml(personalization.first_action)}</strong><p>${escapeHtml(personalization.summary)}</p></div>
        </section>`);
    }
    updateProfile();
    updateIcons();
  }

  function openNode(nodeId) {
    if (!state.flow) {
      showTab("process");
      return;
    }
    const node = nodeById(nodeId) || nodeById(nextIncompleteId()) || state.flow.nodes[0];
    state.currentNodeId = node.id;
    showTab("process", false);
    showProcessView("detail");
    renderDetail(node);
  }

  function renderDetail(node) {
    const personalized = node.personalized || {};
    $("#detail-kicker").textContent = `节点 ${node.number} / ${state.flow.nodes.length}`;
    $("#detail-step-label").textContent = `步骤 ${node.number} / ${state.flow.nodes.length}`;
    $("#detail-title").textContent = node.title;
    $("#detail-intro").textContent = node.intro;
    $("#detail-orbit").className = `detail-orbit tone-${NODE_COLORS[(node.number - 1) % NODE_COLORS.length]}`;
    $("#detail-orbit").innerHTML = `${iconHtml(NODE_ICONS[node.id] || "circle-dot")}`;
    $("#detail-facts").innerHTML = `
      <span>${iconHtml("map-pin")}<small>办理地点</small><strong>${escapeHtml(personalized.location || node.location)}</strong></span>
      <span>${iconHtml("clock-3")}<small>办理时机</small><strong>${escapeHtml(node.time)}</strong></span>
      <span>${iconHtml("wallet-cards")}<small>费用口径</small><strong>${escapeHtml(personalized.cost_note || node.cost)}</strong></span>`;
    renderCompleteButton(node);
    if (node.id === "facility") renderFacilityDetail(node);
    else renderStandardDetail(node);
    updateIcons();
  }

  function renderStandardDetail(node) {
    const personalized = node.personalized;
    const materials = personalized?.materials?.length ? personalized.materials : node.materials;
    const actions = personalized?.actions?.length ? personalized.actions : node.actions;
    const viewCards = (personalized?.visual_cards || []).map((card) => `<article class="sop-visual-card tone-${escapeAttr(card.tone)}"><small>${escapeHtml(card.label)}</small><strong>${escapeHtml(card.title)}</strong><p>${escapeHtml(card.detail)}</p></article>`).join("");
    $("#detail-main").innerHTML = `
      ${node.substeps?.length ? `<section class="service-ribbon"><div class="section-title"><p class="section-index">路径</p><h2>这一步包含</h2></div><div>${node.substeps.map((item, index) => `<span><b>${String(index + 1).padStart(2, "0")}</b>${escapeHtml(item)}</span>`).join("")}</div></section>` : ""}
      <section class="first-action-card">
        <span class="first-action-icon">${iconHtml(node.id === "certificate" ? "phone" : NODE_ICONS[node.id] || "circle-check")}</span>
        <div><small>先做这件事</small><strong>${escapeHtml(personalized?.now || FIRST_ACTIONS[node.id] || node.actions[0])}</strong><p>${escapeHtml(personalized?.location || node.location)} · ${escapeHtml(personalized?.cost_note || node.time)}</p></div>
      </section>
      ${viewCards ? `<section class="sop-visual-grid">${viewCards}</section>` : ""}
      <section class="detail-section material-section">
        <div class="section-title"><p class="section-index">材料</p><h2>出发前带好</h2><small>${(state.checks[node.id] || []).length}/${materials.length} 已核对</small></div>
        <div class="checklist">${renderChecklist({...node, materials})}</div>
      </section>
      <section class="warning-band"><i data-lucide="heart"></i><div><strong>温馨提示</strong><p>${escapeHtml(personalized?.warning || node.warning)}</p></div></section>
      <section class="detail-section action-section">
        <div class="section-title"><p class="section-index">行动</p><h2>接下来按这几步</h2></div>
        <ol class="visual-actions">${actions.map((action, index) => `<li><span>${index + 1}</span><div><small>动作 ${String(index + 1).padStart(2, "0")}</small><strong>${escapeHtml(action)}</strong></div></li>`).join("")}</ol>
      </section>`;
    $("#detail-side").innerHTML = renderSideContent(node);
  }

  function renderChecklist(node) {
    const checked = new Set(state.checks[node.id] || []);
    return node.materials.map((material, index) => `
      <label class="check-item">
        <input type="checkbox" data-material-index="${index}" ${checked.has(index) ? "checked" : ""} />
        <span class="check-box">${iconHtml("check")}</span><span>${escapeHtml(material)}</span>
      </label>`).join("");
  }

  function renderSideContent(node) {
    const sources = state.flow.sources || [];
    const personalized = node.personalized || {};
    return `
      <section class="side-section"><p class="section-index">地点</p><h2>去哪里办</h2><p>${escapeHtml(personalized.location || node.location)}</p><div class="side-facts"><span>${iconHtml("clock-3")}${escapeHtml(node.time)}</span><span>${iconHtml("wallet-cards")}${escapeHtml(personalized.cost_note || node.cost)}</span></div></section>
      <section class="side-section"><p class="section-index">来源</p><h2>官方查询入口</h2><ul class="source-list">${sources.map((source) => `<li><a href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title)}${iconHtml("arrow-up-right")}</a><small>${escapeHtml(source.note)}</small></li>`).join("") || "<li>当地入口待主管部门确认</li>"}</ul></section>`;
  }

  function renderFacilityDetail(node) {
    const personalized = node.personalized || {};
    const materials = personalized.materials?.length ? personalized.materials : node.materials;
    const visualCards = (personalized.visual_cards || []).map((card) => `<article class="sop-visual-card tone-${escapeAttr(card.tone)}"><small>${escapeHtml(card.label)}</small><strong>${escapeHtml(card.title)}</strong><p>${escapeHtml(card.detail)}</p></article>`).join("");
    $("#detail-main").innerHTML = `
      <section class="first-action-card">
        <span class="first-action-icon">${iconHtml("landmark")}</span>
        <div><small>先做这件事</small><strong>${escapeHtml(personalized.now || "先查附近候选，再逐项核对正规记录与书面价格")}</strong><p>${escapeHtml(personalized.location || node.location)} · ${escapeHtml(personalized.cost_note || node.cost)}</p></div>
      </section>
      ${visualCards ? `<section class="sop-visual-grid">${visualCards}</section>` : ""}
      <section class="facility-search-stage">
        <div><p class="section-index">实时核验</p><h2>查找附近正规服务机构</h2><p>高德先计算距离，Kimi 再快速打开政府页面核对机构记录、公开价目与适用条件。</p></div>
        <div class="facility-search-actions">
          <button class="primary-button" id="locate-facilities" type="button">${iconHtml("locate-fixed")}使用我的位置</button>
          <button class="secondary-button" id="manual-location-toggle" type="button">${iconHtml("map-pinned")}输入附近地标</button>
        </div>
        <form id="manual-location-form" class="manual-location-form" hidden>
          <label for="manual-location" class="sr-only">附近地标或区域</label>
          <input id="manual-location" type="text" maxlength="100" placeholder="例如：北京肿瘤医院 / 朝阳区大望路" required />
          <button class="secondary-button" type="submit">开始查找</button>
        </form>
        <div class="search-status" id="facility-search-status" role="status"></div>
      </section>
      <div id="facility-map"></div>
      <div id="facility-results" aria-live="polite">${state.recommendations ? renderRecommendationResults(state.recommendations) : renderFacilityEmpty()}</div>
      <section class="detail-section material-section">
        <div class="section-title"><p class="section-index">材料</p><h2>出发前带好</h2><small>${(state.checks[node.id] || []).length}/${materials.length} 已核对</small></div>
        <div class="checklist">${renderChecklist({...node, materials})}</div>
      </section>
      <section class="warning-band"><i data-lucide="triangle-alert"></i><div><strong>不要先付“全包”定金</strong><p>${escapeHtml(personalized.warning || node.warning)}</p></div></section>`;
    $("#detail-side").innerHTML = `
      <section class="side-section"><p class="section-index">电话清单</p><h2>逐项问这 4 句</h2><ol class="phone-script"><li>基本必选项分别多少钱？</li><li>哪些是可以拒绝的自选项？</li><li>冷藏按什么口径计费？</li><li>符合哪些减免，需要什么材料？</li></ol></section>
      <section class="side-section"><p class="section-index">证据边界</p><h2>推荐不等于报价</h2><p>距离由地图计算；价格必须另有可打开的政府来源。没有两家同口径总价时，归程不会声称某家“最便宜”。</p></section>`;
    bindFacilityEvents();
    if (state.recommendations) renderMap(state.recommendations);
  }

  function renderFacilityEmpty() {
    return `<div class="empty-state">${iconHtml("map-pinned")}<div><strong>还没有查询附近机构</strong><span>允许位置访问，或输入附近医院、街道或地标。</span></div></div>`;
  }

  function bindFacilityEvents() {
    $("#locate-facilities")?.addEventListener("click", locateAndRecommend);
    $("#manual-location-toggle")?.addEventListener("click", () => {
      const form = $("#manual-location-form");
      form.hidden = !form.hidden;
      if (!form.hidden) $("#manual-location").focus();
    });
    $("#manual-location-form")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const value = $("#manual-location").value.trim();
      if (!value) return;
      setFacilityStatus("正在查找这个地点……", true);
      try {
        const location = await apiFetch(`/api/geocode?address=${encodeURIComponent(value)}&city=${encodeURIComponent(state.city)}`);
        if (!sameCity(location.city, state.city)) throw new Error(`这个地点位于${location.city || "其他城市"}，与办理城市${state.city}不一致。`);
        state.location = { longitude: location.longitude, latitude: location.latitude };
        state.locationLabel = location.formatted_address || value;
        await fetchRecommendations();
      } catch (error) {
        setFacilityStatus(error.message, false, true);
      }
    });
  }

  async function locateAndRecommend() {
    if (!navigator.geolocation) {
      setFacilityStatus("当前浏览器不支持定位，请输入附近地标。", false, true);
      $("#manual-location-form").hidden = false;
      return;
    }
    setFacilityStatus("正在获取当前位置……", true);
    navigator.geolocation.getCurrentPosition(async (position) => {
      try {
        setFacilityStatus("正在用高德校正位置并识别城市……", true);
        const location = await apiFetch("/api/location/normalize", {
          method: "POST",
          body: JSON.stringify({ longitude: position.coords.longitude, latitude: position.coords.latitude }),
        });
        if (!sameCity(location.city, state.city)) {
          const shouldSwitch = window.confirm(`定位显示您在${location.city || "其他城市"}，当前办理城市是${state.city}。是否改为${location.city}后继续？`);
          if (!shouldSwitch) {
            setFacilityStatus("已取消查询。可更改办理城市，或输入该城市的地标。", false, true);
            $("#manual-location-form").hidden = false;
            return;
          }
          await applyCity(location.city);
        }
        state.location = { longitude: location.longitude, latitude: location.latitude };
        state.locationLabel = location.formatted_address || "当前位置";
        await fetchRecommendations();
      } catch (error) {
        setFacilityStatus(error.message, false, true);
        $("#manual-location-form").hidden = false;
      }
    }, (error) => {
      const messages = { 1: "未获得位置权限，请输入附近医院、街道或地标。", 2: "暂时无法确定位置，请输入附近地标。", 3: "定位超时，可以重试或输入附近地标。" };
      setFacilityStatus(messages[error.code] || "定位失败，请输入附近地标。", false, true);
      $("#manual-location-form").hidden = false;
    }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 300000 });
  }

  async function fetchRecommendations() {
    if (!validLocation(state.location) || !state.flow) return;
    const requestId = ++recommendationRequestId;
    const context = {
      location: { ...state.location },
      locationLabel: state.locationLabel,
      city: state.city,
      budget: state.flow.budget,
      note: state.note,
    };
    let nearbyData = null;
    setFacilitySearchBusy(true);
    setFacilityStatus("正在用高德搜索附近机构……", true);
    const results = $("#facility-results");
    results.innerHTML = `<div class="loading-state">${iconHtml("loader-circle", "spin")}<div><strong>正在核验候选机构</strong><span>地图搜索完成后，Kimi 会快速查找可核验来源。</span></div></div>`;
    updateIcons();
    try {
      const nearby = await apiFetch("/api/facilities/nearby", {
        method: "POST",
        body: JSON.stringify({ longitude: context.location.longitude, latitude: context.location.latitude, city: context.city }),
      });
      if (requestId !== recommendationRequestId) return;
      nearbyData = nearby;
      state.recommendations = nearby;
      results.innerHTML = renderRecommendationResults(nearby);
      renderMap(nearby);
      setFacilityStatus(`找到 ${nearby.candidates.length} 家候选，Kimi 正在联网核验……`, true);
      updateIcons();
      const data = await apiFetch("/api/recommendations", {
        method: "POST",
        timeoutMs: 105000,
        body: JSON.stringify({ longitude: context.location.longitude, latitude: context.location.latitude, city: context.city, budget: context.budget, note: context.note }),
      });
      if (requestId !== recommendationRequestId) return;
      state.recommendations = data;
      results.innerHTML = renderRecommendationResults(data);
      setFacilityStatus(`核验完成 · ${context.locationLabel || "当前位置"}`, false);
      renderMap(data);
      updateProfile();
      updateIcons();
    } catch (error) {
      if (requestId !== recommendationRequestId) return;
      if (nearbyData) {
        nearbyData.verification_notice = `地图距离仍可使用；Kimi 核验未完成：${error.message}`;
        state.recommendations = nearbyData;
        results.innerHTML = `${renderRecommendationResults(nearbyData)}<div class="retry-strip"><span>上方距离结果仍可使用。</span><button class="secondary-button" type="button" id="retry-recommendations">重新核验</button></div>`;
      } else {
        results.innerHTML = `<div class="empty-state">${iconHtml("circle-alert")}<div><strong>这次没有完成查找</strong><span>${escapeHtml(error.message)}</span><button class="secondary-button" type="button" id="retry-recommendations">重试</button></div></div>`;
      }
      setFacilityStatus(error.message, false, true);
      updateIcons();
    } finally {
      if (requestId === recommendationRequestId) setFacilitySearchBusy(false);
    }
  }

  function renderRecommendationResults(data) {
    if (!data.candidates?.length) return `<div class="empty-state">${iconHtml("map-pin-off")}<div><strong>附近没有找到可用候选</strong><span>${escapeHtml(data.summary || "请换一个定位后重试。")}</span></div></div>`;
    const officialCount = data.candidates.filter((candidate) => candidate.official_status === "verified").length;
    const priceCount = data.candidates.filter((candidate) => (candidate.price_items || []).length > 0).length;
    const evidenceFinished = ["verified", "official_only"].includes(data.verification_status);
    const warning = data.verification_status !== "verified" || priceCount === 0;
    const budgetLabel = BUDGET_LABELS[data.budget || state.flow?.budget] || "未指定";
    const generatedTime = data.generated_at ? new Date(data.generated_at * 1000).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "刚刚";
    const cards = data.candidates.map((candidate, index) => renderFacilityCard(candidate, data.recommended_poi_id, index)).join("");
    const sources = (data.sources || []).map((source) => `<li id="source-${escapeAttr(source.id)}"><a href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title)}${iconHtml("arrow-up-right")}</a><small>${escapeHtml(source.publisher || "官方来源")} · ${escapeHtml(source.published_at || "日期见原文")}<br>${escapeHtml(source.scope || "")}</small></li>`).join("");
    return `
      <div class="evidence-notice ${warning ? "is-warning" : ""}">${iconHtml(warning ? "triangle-alert" : "shield-check")}<span>${escapeHtml(data.verification_notice || "")}${evidenceFinished ? ` 已核对 ${officialCount} 家政府记录，${priceCount ? `${priceCount} 家有价格证据` : "未找到可比价格证据"}。` : ""}</span></div>
      <section class="recommendation-summary"><p class="section-index">对比结论</p><h2>${data.recommended_poi_id ? "当前更值得先咨询" : "候选已按距离排列"}</h2><p>${escapeHtml(data.summary || "")}</p><small>所选预算：${escapeHtml(budgetLabel)} · 核验时间：${escapeHtml(generatedTime)}</small>${(data.decision_basis || []).length ? `<ul>${data.decision_basis.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}</section>
      <section class="facility-results-section"><div class="section-title"><p class="section-index">候选</p><h2>附近机构</h2><small>${data.candidates.length} 家</small></div><div class="facility-list">${cards}</div></section>
      ${sources ? `<section class="source-index"><details><summary>查看本次核验来源（${data.sources.length}）</summary><ol>${sources}</ol></details></section>` : ""}`;
  }

  function renderFacilityCard(candidate, recommendedId, index) {
    const recommended = candidate.id === recommendedId;
    const officialClass = candidate.official_status === "verified" ? "verified" : candidate.official_status === "likely" ? "partial" : "";
    const priceClass = candidate.price_status === "verified" ? "verified" : candidate.price_status === "partial" ? "partial" : "";
    const hasComparableTotal = candidate.comparable_basic_total_yuan != null && Number.isFinite(Number(candidate.comparable_basic_total_yuan));
    const fitStatus = hasComparableTotal && ["within", "over"].includes(candidate.fit_for_budget) ? candidate.fit_for_budget : "uncertain";
    const fitClass = fitStatus === "within" ? "verified" : fitStatus === "over" ? "over" : "";
    const priceItems = (candidate.price_items || []).map((price) => {
      const refs = (price.source_ids || []).map((id) => `<a href="#source-${escapeAttr(id)}">${escapeHtml(id)}</a>`).join(" / ");
      return `<div class="price-row"><span>${escapeHtml(price.item)}</span><strong>${price.amount_yuan == null ? escapeHtml(price.display || "条件性收费") : `¥${formatAmount(price.amount_yuan)}`}</strong><small>${escapeHtml(price.conditions || price.display || "")}${refs ? ` · 来源 ${refs}` : ""}</small></div>`;
    }).join("");
    const navigation = `https://uri.amap.com/marker?position=${encodeURIComponent(`${candidate.longitude},${candidate.latitude}`)}&name=${encodeURIComponent(candidate.name)}&coordinate=gaode&callnative=1`;
    return `
      <article class="facility-card ${recommended ? "is-recommended" : ""}">
        ${recommended ? `<span class="recommended-badge">${iconHtml("sparkles")}建议先咨询</span>` : ""}
        <div class="facility-card-head"><span class="facility-rank">${String(index + 1).padStart(2, "0")}</span><div><h3>${escapeHtml(candidate.name)}</h3><p>${escapeHtml(candidate.address)}</p></div><strong class="distance-tag">${formatDistance(candidate.distance_m)}</strong></div>
        <div class="status-row"><span class="status-badge ${officialClass}">${escapeHtml(OFFICIAL_LABELS[candidate.official_status] || OFFICIAL_LABELS.unverified)}</span><span class="status-badge ${priceClass}">${escapeHtml(PRICE_LABELS[candidate.price_status] || PRICE_LABELS.phone_required)}</span><span class="status-badge ${fitClass}">${escapeHtml(FIT_LABELS[fitStatus])}</span></div>
        <p class="value-reason">${escapeHtml(candidate.value_reason || "距离已确认，价格与资质还需电话核实。")}</p>
        ${hasComparableTotal ? `<div class="comparable-total"><span>同口径基本服务总额</span><strong>¥${formatAmount(candidate.comparable_basic_total_yuan)}</strong></div>` : ""}
        ${priceItems ? `<div class="price-table">${priceItems}</div>` : `<div class="price-missing">${iconHtml("phone-call")}<span>没有可直接绑定到该机构的可比价目，请电话索取分项报价。</span></div>`}
        <div class="facility-card-actions"><a href="${safeUrl(navigation)}" target="_blank" rel="noopener noreferrer">${iconHtml("navigation")}高德导航</a>${candidate.phone ? `<a href="tel:${escapeAttr(candidate.phone.split(/[;\/]/)[0].replace(/[^0-9-]/g, ""))}">${iconHtml("phone")}拨打电话</a>` : ""}</div>
        <details class="facility-details"><summary>核验说明与电话问法</summary><p>${escapeHtml(candidate.official_status_note || "")}</p><h4>逐项确认</h4><ul>${(candidate.call_to_confirm || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>${(candidate.cautions || []).length ? `<h4>还要注意</h4><ul>${candidate.cautions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}</details>
      </article>`;
  }

  function renderMap(data) {
    const container = $("#facility-map");
    if (!container || !data.origin || !data.candidates?.length) return;
    const points = data.candidates.slice(0, 5).map((item) => `${item.longitude},${item.latitude}`).join("|");
    const src = `/api/static-map?longitude=${encodeURIComponent(data.origin.longitude)}&latitude=${encodeURIComponent(data.origin.latitude)}&points=${encodeURIComponent(points)}`;
    container.innerHTML = `<figure class="map-frame"><img src="${src}" alt="你的位置与附近候选殡仪馆示意图" loading="lazy" /></figure>`;
    container.querySelector("img").addEventListener("error", () => {
      container.innerHTML = `<div class="map-frame map-placeholder">${iconHtml("map")}<span>地图图片暂时无法加载<br><small>下方距离与导航仍可使用</small></span></div>`;
      updateIcons();
    });
  }

  function setFacilityStatus(message, loading = false, isError = false) {
    const element = $("#facility-search-status");
    if (!element) return;
    element.classList.toggle("is-error", isError);
    element.innerHTML = `${iconHtml(loading ? "loader-circle" : isError ? "circle-alert" : "circle-check", loading ? "spin" : "")}<span>${escapeHtml(message)}</span>`;
    updateIcons();
  }

  function setFacilitySearchBusy(busy) {
    ["#locate-facilities", "#manual-location-toggle", "#manual-location", "#manual-location-form button"].forEach((selector) => {
      const control = $(selector);
      if (control) control.disabled = busy;
    });
  }

  function handleChecklistChange(event) {
    const input = event.target.closest("[data-material-index]");
    if (!input || !state.currentNodeId) return;
    const index = Number(input.dataset.materialIndex);
    const checks = new Set(state.checks[state.currentNodeId] || []);
    input.checked ? checks.add(index) : checks.delete(index);
    state.checks[state.currentNodeId] = Array.from(checks).sort((a, b) => a - b);
    persistState();
    const node = nodeById(state.currentNodeId);
    const count = $("#detail-main .material-section .section-title > small");
    const materialCount = node?.personalized?.materials?.length || node?.materials?.length || 0;
    if (count && node) count.textContent = `${checks.size}/${materialCount} 已核对`;
    updateProfile();
  }

  function handleDetailClick(event) {
    if (event.target.closest("#retry-recommendations")) fetchRecommendations();
  }

  function toggleCurrentNode() {
    if (!state.currentNodeId) return;
    const complete = state.completed.includes(state.currentNodeId);
    state.completed = complete ? state.completed.filter((item) => item !== state.currentNodeId) : [...state.completed, state.currentNodeId];
    persistState();
    renderCompleteButton(nodeById(state.currentNodeId));
    updateProfile();
    toast(complete ? "已改为待办理" : "已标记完成");
  }

  function renderCompleteButton(node) {
    if (!node) return;
    const complete = state.completed.includes(node.id);
    $("#complete-label").textContent = complete ? "这一步已完成" : "这一步办完了吗？";
    const button = $("#toggle-node-complete");
    button.classList.toggle("is-complete", complete);
    button.innerHTML = complete ? `${iconHtml("rotate-ccw")}改为待办理` : `${iconHtml("circle-check")}这一步已经办好`;
    updateIcons();
  }

  async function loadHelpWall() {
    const container = $("#help-posts");
    container.innerHTML = `<div class="loading-state">${iconHtml("loader-circle", "spin")}<span>正在载入求助</span></div>`;
    updateIcons();
    try {
      const data = await apiFetch("/api/help-wall");
      container.innerHTML = data.posts.length ? data.posts.map(renderHelpPost).join("") : `<div class="empty-state">${iconHtml("message-circle-more")}<div><strong>还没有求助</strong><span>可以发布第一条，等待社区回应。</span></div></div>`;
    } catch (error) {
      container.innerHTML = `<div class="empty-state">${iconHtml("circle-alert")}<div><strong>暂时无法载入</strong><span>${escapeHtml(error.message)}</span></div></div>`;
    }
    updateIcons();
  }

  function renderHelpPost(post) {
    const time = post.created_at ? new Date(post.created_at * 1000).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "示例";
    const initial = String(post.alias || "家").trim().slice(0, 1);
    const replies = Array.isArray(post.replies) ? post.replies : [];
    const replyItems = replies.map((reply) => {
      const replyTime = reply.created_at ? new Date(reply.created_at * 1000).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "刚刚";
      return `<div class="help-reply"><strong>${escapeHtml(reply.alias)}</strong><span>${escapeHtml(replyTime)}</span><p>${escapeHtml(reply.content)}</p></div>`;
    }).join("");
    return `<article class="help-post"><div class="post-avatar">${escapeHtml(initial)}</div><div><div class="post-meta"><strong>${escapeHtml(post.alias)}</strong><span>${escapeHtml(post.city)} · ${escapeHtml(time)}</span></div><span class="topic-tag">${escapeHtml(post.topic)}</span><p>${escapeHtml(post.content)}</p><details class="reply-thread"><summary>${iconHtml("message-circle-reply")} ${replies.length ? `${replies.length} 条回应` : "回应这条求助"}</summary>${replyItems}<form class="reply-form" data-post-id="${escapeAttr(post.id)}"><label>称呼<input name="alias" maxlength="20" value="一位同行者" required /></label><label>回应<textarea name="content" minlength="2" maxlength="240" rows="3" placeholder="分享可以核对的流程经验，不要留下联系方式。" required></textarea></label><p class="form-error" hidden></p><button class="secondary-button" type="submit">${iconHtml("send")}发布回应</button></form></details></div></article>`;
  }

  async function submitHelpReply(event) {
    const formElement = event.target.closest(".reply-form");
    if (!formElement) return;
    event.preventDefault();
    const form = new FormData(formElement);
    const errorElement = formElement.querySelector(".form-error");
    const button = formElement.querySelector('button[type="submit"]');
    errorElement.hidden = true;
    setButtonLoading(button, true, "正在发布");
    try {
      await apiFetch(`/api/help-wall/${encodeURIComponent(formElement.dataset.postId)}/replies`, {
        method: "POST",
        body: JSON.stringify({ alias: String(form.get("alias") || "一位同行者"), content: String(form.get("content") || "") }),
      });
      toast("回应已发布");
      await loadHelpWall();
    } catch (error) {
      errorElement.textContent = error.message;
      errorElement.hidden = false;
    } finally {
      setButtonLoading(button, false);
    }
  }

  async function submitHelpPost(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const errorElement = $("#help-error");
    errorElement.hidden = true;
    const button = event.currentTarget.querySelector('button[type="submit"]');
    setButtonLoading(button, true, "正在发布");
    try {
      await apiFetch("/api/help-wall", {
        method: "POST",
        body: JSON.stringify({ alias: String(form.get("alias") || "一位家属"), city: state.city, topic: String(form.get("topic") || "其他"), content: String(form.get("content") || "") }),
      });
      event.currentTarget.querySelector("textarea").value = "";
      $("#help-dialog").close();
      toast("求助已发布");
      await loadHelpWall();
    } catch (error) {
      errorElement.textContent = error.message;
      errorElement.hidden = false;
    } finally {
      setButtonLoading(button, false);
    }
  }

  async function loadCommunityInfo() {
    if (communityLoadedCity === state.city && $("#policy-content").children.length) return;
    const policy = $("#policy-content");
    const phone = $("#phone-content");
    policy.innerHTML = phone.innerHTML = `<div class="loading-state">${iconHtml("loader-circle", "spin")}<span>正在整理${escapeHtml(state.city)}的公开渠道</span></div>`;
    updateIcons();
    try {
      const data = await apiFetch(`/api/community-info?city=${encodeURIComponent(state.city)}`, { timeoutMs: 65000 });
      communityLoadedCity = state.city;
      const references = new Map((data.references || []).map((item) => [item.id, item]));
      const policies = (data.policies || []).map((item, index) => {
        const source = references.get(item.reference_id);
        return `<article class="policy-item"><span>${String(index + 1).padStart(2, "0")}</span><div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.summary)}</p><p><b>适用对象</b>${escapeHtml(item.applies_to)}</p>${source ? `<a href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer">查看政府 reference${iconHtml("arrow-up-right")}</a>` : ""}</div></article>`;
      }).join("");
      policy.innerHTML = `
        <div class="verification-strip ${data.search_status === "curated" ? "is-verified" : ""}">${iconHtml(data.search_status === "curated" ? "book-check" : "triangle-alert")}<span>${escapeHtml(data.verification_notice || "")}<small>资料更新：${escapeHtml(data.updated_at || "待更新")}</small></span></div>
        <section class="policy-notice"><span class="policy-city">${escapeHtml(data.city)}</span><div><strong>费用减免与政策</strong><p>${escapeHtml(data.intro)}</p></div></section>
        ${policies ? `<div class="policy-results"><h3>当地公开政策</h3>${policies}</div>` : `<div class="policy-empty"><strong>当地资料尚未录入</strong><p>当前不展示猜测政策，请使用 12345 向主管部门确认。</p></div>`}
        <div class="policy-checks"><h3>办理前先核对这 4 项</h3>${data.checks.map((item, index) => `<div><span>${String(index + 1).padStart(2, "0")}</span><p>${escapeHtml(item)}</p></div>`).join("")}</div>
        <section class="official-entry"><h3>政府 reference</h3><div>${(data.references || []).map((source) => `<a href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer"><span>${iconHtml("landmark")}</span><div><strong>${escapeHtml(source.title)}</strong><small>${escapeHtml(source.publisher)} · ${escapeHtml(source.note)}</small></div>${iconHtml("arrow-up-right")}</a>`).join("") || `<p>当地官方入口尚未录入。</p>`}</div></section>
        <p class="source-footnote">不直接承诺固定补贴金额；对象、户籍、申请期和结算方式以当期官方文件为准。</p>`;
      phone.innerHTML = `
        <div class="verification-strip ${data.search_status === "curated" ? "is-verified" : ""}">${iconHtml("book-check")}<span>${escapeHtml(data.verification_notice || "")}<small>资料更新：${escapeHtml(data.updated_at || "待更新")}</small></span></div>
        <p class="urgent-line"><i data-lucide="siren"></i>死因不明、涉及意外或发生在公共场所时，请先拨 110，不要自行转运。</p>
        <div class="phone-list">${data.contacts.map((contact, index) => { const source = references.get(contact.reference_id); return `<article><span class="phone-index">${String(index + 1).padStart(2, "0")}</span><div><small>${escapeHtml(contact.name)}</small><strong>${escapeHtml(contact.phone)}</strong><p>${escapeHtml(contact.use)}</p><em>${escapeHtml(contact.scope || data.city)}${source ? ` · <a href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer">reference</a>` : " · 全国公共渠道"}</em></div><a href="tel:${escapeAttr(contact.phone.replace(/[^0-9-]/g, ""))}" aria-label="拨打 ${escapeAttr(contact.phone)}">${iconHtml("phone")}</a></article>`; }).join("")}</div>
        <p class="source-footnote">本页来自预置城市资料，不调用 Kimi 临时检索。</p>`;
    } catch (error) {
      const failed = `<div class="empty-state">${iconHtml("circle-alert")}<div><strong>暂时无法载入</strong><span>${escapeHtml(error.message)}</span></div></div>`;
      policy.innerHTML = failed;
      phone.innerHTML = failed;
    }
    updateIcons();
  }

  function openCityDialog() {
    $("#city-input").value = state.city;
    openDialog("#city-dialog");
  }

  async function submitCity(event) {
    event.preventDefault();
    const city = $("#city-input").value.replace(/\s+/g, "").slice(0, 30);
    if (!city) return;
    const button = event.currentTarget.querySelector('button[type="submit"]');
    setButtonLoading(button, true, "正在保存");
    try {
      await applyCity(city);
      $("#city-dialog").close();
      toast(`办理城市已改为${city}`);
    } catch (error) {
      toast(error.message);
    } finally {
      setButtonLoading(button, false);
    }
  }

  async function applyCity(city) {
    recommendationRequestId += 1;
    flowRequestId += 1;
    let refreshedFlow = null;
    if (state.flow) {
      refreshedFlow = await apiFetch("/api/generate-flow", {
        method: "POST",
        body: JSON.stringify({ legal_confirmed: true, place: state.flow.place, budget: state.flow.budget, city, note: state.note }),
      });
    }
    state.city = city;
    if (refreshedFlow) state.flow = refreshedFlow;
    state.recommendations = null;
    state.location = null;
    state.locationLabel = "";
    communityLoadedCity = "";
    updateCityUI();
    persistState();
    if (state.processView === "overview") renderOverview();
    if (state.processView === "detail" && state.currentNodeId) renderDetail(nodeById(state.currentNodeId));
    if (state.activeTab === "info") loadInfoPanel();
  }

  function updateCityUI() {
    $("#global-city span").textContent = state.city;
    $("#info-city-label").textContent = state.city;
    $("#profile-city small").textContent = state.city;
  }

  async function submitLogin(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = event.currentTarget.querySelector('button[type="submit"]');
    const errorElement = $("#auth-error");
    errorElement.hidden = true;
    setButtonLoading(button, true, authMode === "register" ? "正在注册" : "正在登录");
    try {
      const path = authMode === "register" ? "/api/auth/register" : "/api/auth/login";
      const payload = { email: String(form.get("email") || ""), password: String(form.get("password") || "") };
      if (authMode === "register") payload.display_name = String(form.get("display_name") || "");
      const data = await apiFetch(path, { method: "POST", body: JSON.stringify(payload) });
      state.user = data.user;
      state.profileAlias = data.user.display_name;
      await mergeAccountProgress();
      updateProfile();
      $("#login-dialog").close();
      toast(authMode === "register" ? "账户已创建" : "登录成功");
    } catch (error) {
      errorElement.textContent = error.message;
      errorElement.hidden = false;
    } finally {
      setButtonLoading(button, false);
    }
  }

  function setAuthMode(mode) {
    authMode = mode === "register" ? "register" : "login";
    $$('[data-auth-mode]').forEach((button) => button.classList.toggle("is-active", button.dataset.authMode === authMode));
    $$(".register-only").forEach((element) => { element.hidden = authMode !== "register"; });
    $("#profile-alias").required = authMode === "register";
    $("#login-dialog-title").textContent = authMode === "register" ? "创建账户" : "登录";
    $("#login-form button[type='submit']").textContent = authMode === "register" ? "创建账户" : "登录";
    $("#auth-error").hidden = true;
  }

  async function initializeAccount() {
    try {
      const data = await apiFetch("/api/auth/me");
      state.user = data.user;
      if (state.user) {
        state.profileAlias = state.user.display_name;
        await mergeAccountProgress(false);
      }
    } catch (_error) {
      state.user = null;
    }
    updateProfile();
  }

  async function mergeAccountProgress(saveLocalWhenMissing = true) {
    const data = await apiFetch("/api/account/progress");
    const progress = data.progress;
    if (progress?.flow?.nodes) {
      state.city = progress.city || state.city;
      state.legalConfirmed = Boolean(progress.legal_confirmed);
      state.answers = progress.answers || state.answers;
      state.flow = progress.flow;
      state.completed = progress.completed || [];
      state.checks = progress.checks || {};
      state.mode = progress.mode === "elder" ? "elder" : "standard";
      showProcessView("home", false);
      renderHome();
      updateCityUI();
      applyMode();
      persistState();
    } else if (saveLocalWhenMissing) {
      await saveAccountProgress();
    }
  }

  function scheduleAccountSave() {
    if (!state.user) return;
    clearTimeout(accountSaveTimer);
    accountSaveTimer = setTimeout(saveAccountProgress, 450);
  }

  async function saveAccountProgress() {
    if (!state.user) return;
    try {
      await apiFetch("/api/account/progress", { method: "PUT", body: JSON.stringify({ city: state.city, legal_confirmed: state.legalConfirmed, answers: state.answers, flow: state.flow, completed: state.completed, checks: state.checks, mode: state.mode }) });
    } catch (_error) {
      toast("账户进度暂未保存");
    }
  }

  async function logoutAccount() {
    await apiFetch("/api/auth/logout", { method: "POST", body: "{}" });
    state.user = null;
    state.profileAlias = "";
    updateProfile();
    toast("已退出登录");
  }

  function updateProfile() {
    const completed = state.flow ? state.completed.filter((id) => state.flow.nodes.some((node) => node.id === id)).length : 0;
    const materials = Object.values(state.checks).reduce((total, values) => total + (Array.isArray(values) ? values.length : 0), 0);
    $("#profile-name").textContent = state.user?.display_name || "访客用户";
    $("#profile-state").textContent = state.user ? state.user.email : "当前为本机访客模式";
    $("#profile-avatar").textContent = (state.user?.display_name || state.profileAlias || "访").slice(0, 1);
    $("#login-button").textContent = state.user ? "已登录" : "登录";
    $("#login-button").disabled = Boolean(state.user);
    $("#logout-button").hidden = !state.user;
    $("#profile-storage-note").textContent = state.user ? "办理进度已保存到这个账户。" : "访客进度保存在本机，登录后可保存到本地账户。";
    $("#stat-progress").textContent = `${completed}/${state.flow?.nodes.length || 5}`;
    $("#stat-materials").textContent = String(materials);
    $("#progress-row-label").textContent = state.flow ? `${completed}/${state.flow.nodes.length} 已完成` : "尚未生成";
  }

  function setMode(mode) {
    state.mode = mode === "elder" ? "elder" : "standard";
    state.tapSpeech = state.mode === "elder";
    applyMode();
    persistState();
    toast(state.mode === "elder" ? "已切换到老年版" : "已切换到普通版");
  }

  function applyMode() {
    document.body.classList.toggle("elder-mode", state.mode === "elder");
    $$('[data-mode]').forEach((button) => {
      const active = button.dataset.mode === state.mode;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-checked", String(active));
    });
    $("#tap-speech").checked = state.tapSpeech;
    $("#read-page").hidden = state.mode !== "elder" && !state.tapSpeech;
  }

  function handleTapSpeech(event) {
    if (!state.tapSpeech || event.defaultPrevented) return;
    if (event.target.closest("input, textarea, select, dialog")) return;
    const textElement = event.target.closest("h1, h2, h3, p, li, strong, small, em, button, a, summary, label");
    if (!textElement || !textElement.closest("main") || textElement.offsetParent === null) return;
    speak(textElement.innerText.trim());
  }

  function readCurrentPage() {
    const activePage = $('[data-tab-page]:not([hidden])');
    if (!activePage) return;
    if (window.speechSynthesis?.speaking) {
      window.speechSynthesis.cancel();
      toast("已停止朗读");
      return;
    }
    speak(activePage.innerText.replace(/\s+/g, " ").trim().slice(0, 5000));
  }

  function speak(text) {
    if (!text || !("speechSynthesis" in window)) {
      toast("当前浏览器不支持朗读");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text.slice(0, 5000));
    utterance.lang = "zh-CN";
    utterance.rate = 0.84;
    window.speechSynthesis.speak(utterance);
  }

  function clearProgress() {
    if (!window.confirm("清除后，办理路径、完成状态和材料勾选将无法恢复。确定清除吗？")) return;
    recommendationRequestId += 1;
    flowRequestId += 1;
    state.legalConfirmed = false;
    state.answers = { place: null, budget: null };
    state.questionStep = 0;
    state.note = "";
    state.flow = null;
    state.completed = [];
    state.checks = {};
    state.currentNodeId = null;
    state.recommendations = null;
    state.location = null;
    state.locationLabel = "";
    persistState();
    renderQuestion(0);
    showProcessView("intake", false);
    updateProfile();
    toast("本机办理进度已清除");
  }

  function restartFlow() {
    if (!window.confirm("重新填写会清除当前完成状态和材料勾选。确定继续吗？")) return;
    clearTimeout(questionAdvanceTimer);
    recommendationRequestId += 1;
    flowRequestId += 1;
    state.legalConfirmed = false;
    state.answers = { place: null, budget: null };
    state.questionStep = 0;
    state.note = "";
    state.flow = null;
    state.completed = [];
    state.checks = {};
    state.currentNodeId = null;
    state.recommendations = null;
    state.location = null;
    state.locationLabel = "";
    persistState();
    renderQuestion(0);
    showProcessView("intake");
    updateProfile();
  }

  function bindPortraitEvents() {
    $("#portrait-file").addEventListener("change", (event) => {
      const file = event.target.files?.[0];
      if (!file) return;
      if (!file.type.startsWith("image/") || file.size > 15 * 1024 * 1024) {
        toast("请选择 15MB 以内的 JPG、PNG 或 WebP 照片");
        return;
      }
      const url = URL.createObjectURL(file);
      const image = new Image();
      image.onload = () => {
        if (state.portrait.image?.src?.startsWith("blob:")) URL.revokeObjectURL(state.portrait.image.src);
        state.portrait.image = image;
        state.portrait.zoom = 1;
        state.portrait.y = 0;
        $("#portrait-zoom").value = "1";
        $("#portrait-y").value = "0";
        $("#portrait-empty").hidden = true;
        $("#download-portrait").disabled = false;
        drawPortrait();
      };
      image.onerror = () => toast("这张照片无法读取");
      image.src = url;
    });
    $$('[data-filter]').forEach((button) => button.addEventListener("click", () => {
      state.portrait.filter = button.dataset.filter;
      $$('[data-filter]').forEach((item) => item.classList.toggle("is-active", item === button));
      drawPortrait();
    }));
    $("#portrait-zoom").addEventListener("input", (event) => { state.portrait.zoom = Number(event.target.value); drawPortrait(); });
    $("#portrait-y").addEventListener("input", (event) => { state.portrait.y = Number(event.target.value); drawPortrait(); });
    $("#download-portrait").addEventListener("click", downloadPortrait);
  }

  function drawPortrait() {
    const canvas = $("#portrait-canvas");
    const context = canvas.getContext("2d");
    context.fillStyle = "#e7ede9";
    context.fillRect(0, 0, canvas.width, canvas.height);
    const image = state.portrait.image;
    if (!image) return;
    const baseScale = Math.max(canvas.width / image.naturalWidth, canvas.height / image.naturalHeight);
    const scale = baseScale * state.portrait.zoom;
    const width = image.naturalWidth * scale;
    const height = image.naturalHeight * scale;
    const x = (canvas.width - width) / 2;
    const maxY = Math.max(0, (height - canvas.height) / 2);
    const y = (canvas.height - height) / 2 + state.portrait.y * maxY * 2;
    context.save();
    context.filter = state.portrait.filter === "grayscale" ? "grayscale(1) contrast(1.05)" : "none";
    context.drawImage(image, x, y, width, height);
    context.restore();
  }

  function downloadPortrait() {
    if (!state.portrait.image) return;
    const link = document.createElement("a");
    link.download = `归程-整理后照片-${new Date().toISOString().slice(0, 10)}.jpg`;
    link.href = $("#portrait-canvas").toDataURL("image/jpeg", 0.92);
    link.click();
  }

  function openDialog(selector) {
    const dialog = $(selector);
    if (dialog?.showModal) dialog.showModal();
    updateIcons();
  }

  function nextIncompleteId() {
    if (!state.flow) return null;
    return state.flow.nodes.find((node) => !state.completed.includes(node.id))?.id || null;
  }

  function nodeById(id) {
    return state.flow?.nodes.find((node) => node.id === id) || null;
  }

  async function apiFetch(url, options = {}) {
    const controller = new AbortController();
    const { timeoutMs = API_TIMEOUT, ...fetchOptions } = options;
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers: { "Content-Type": "application/json", ...(fetchOptions.headers || {}) },
        signal: controller.signal,
      });
      const contentType = response.headers.get("content-type") || "";
      const payload = contentType.includes("application/json") ? await response.json() : await response.text();
      if (!response.ok) {
        const detail = typeof payload === "object" ? payload.detail : payload;
        throw new Error(typeof detail === "string" ? detail : "请求没有成功，请稍后重试。");
      }
      return payload;
    } catch (error) {
      if (error.name === "AbortError") throw new Error("处理时间超过预期，请重试。");
      if (error instanceof TypeError) throw new Error("无法连接服务，请检查网络后重试。");
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  function setButtonLoading(button, loading, label = "") {
    if (!button) return;
    if (loading) {
      button.dataset.originalHtml = button.innerHTML;
      button.disabled = true;
      button.innerHTML = `${iconHtml("loader-circle", "spin")} ${escapeHtml(label)}`;
    } else {
      button.disabled = false;
      if (button.dataset.originalHtml) button.innerHTML = button.dataset.originalHtml;
      delete button.dataset.originalHtml;
    }
    updateIcons();
  }

  function updateIcons() {
    if (window.lucide?.createIcons) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  function iconHtml(name, className = "") {
    return `<i data-lucide="${escapeAttr(name)}"${className ? ` class="${escapeAttr(className)}"` : ""} aria-hidden="true"></i>`;
  }

  function toast(message) {
    const element = document.createElement("div");
    element.className = "toast";
    element.textContent = message;
    $("#toast-region").appendChild(element);
    setTimeout(() => element.remove(), 2800);
  }

  function formatDistance(meters) {
    const value = Number(meters);
    if (!Number.isFinite(value)) return "距离未知";
    return value < 1000 ? `${Math.round(value)} 米` : `${(value / 1000).toFixed(value < 10000 ? 1 : 0)} 公里`;
  }

  function formatAmount(value) {
    return Number(value).toLocaleString("zh-CN", { maximumFractionDigits: 2 });
  }

  function validLocation(location) {
    return Boolean(location && Number.isFinite(Number(location.longitude)) && Number.isFinite(Number(location.latitude)));
  }

  function sameCity(first, second) {
    const normalize = (value) => String(value || "").trim().replace(/[市省]$/, "");
    return Boolean(normalize(first) && normalize(first) === normalize(second));
  }

  function safeUrl(value) {
    try {
      const url = new URL(String(value), window.location.origin);
      return url.protocol === "http:" || url.protocol === "https:" ? escapeAttr(url.href) : "#";
    } catch (_error) {
      return "#";
    }
  }

  function escapeHtml(value) {
    return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
  }

  function delay(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
  }

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }
})();

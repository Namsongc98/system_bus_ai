"use strict";

// Review text is untrusted: everything goes through text nodes, never innerHTML.
const POLL_MS = 5000;
const STALE_MS = 120000;
const TABS = [
  { id: "overview", label: "Tổng quan", icon: "▦" },
  { id: "agents", label: "Đội agent", icon: "◎" },
  { id: "exchange", label: "Trao đổi", icon: "⇄" },
  { id: "tasks", label: "Task", icon: "☑" },
];
const AGENT_STATUS = {
  running: ["Đang chạy", "tone-info"],
  done: ["Hoàn tất", "tone-accent"],
  idle: ["Nhàn rỗi", "tone-muted"],
  unknown: ["Không rõ", "tone-warn"],
  waiting: ["Chờ bạn", "tone-warn"],
};
const TASK_STATUS = {
  done: ["Xong", "tone-accent"],
  paused: ["Tạm dừng", "tone-muted"],
  waiting_user: ["Chờ bạn duyệt", "tone-warn"],
  reviewing: ["Đang review", "tone-info"],
  in_progress: ["Đang làm", "tone-info"],
  not_started: ["Chưa bắt đầu", "tone-muted"],
};
const STAGES = {
  empty: "Trống",
  scoped: "Đã chốt phạm vi",
  reviewing: "Reviewer đã ghi kết quả",
  verifying: "Đang kiểm chứng",
  summarized: "Đã tổng hợp",
};
const SEVERITY_TONE = { high: "tone-danger", medium: "tone-warn", low: "tone-muted" };
const VERDICT_TONE = { confirmed: "tone-accent", refuted: "tone-muted", uncertain: "tone-warn", unverified: "tone-muted" };
const GATES = ["spec", "implement", "test", "review", "lead-review"];
const SVG_NS = "http://www.w3.org/2000/svg";

const state = {
  snapshot: null, signature: "", paused: false, selected: null, roundKey: null,
  phase: "all", status: "all", lastOk: null, error: null, timer: null,
};

function apply(element, props) {
  for (const [key, value] of Object.entries(props || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key.startsWith("on")) element.addEventListener(key.slice(2).toLowerCase(), value);
    else element.setAttribute(key, value === true ? "" : value);
  }
}

function fill(element, kids) {
  element.append(...kids.flat(Infinity).filter((kid) => kid !== null && kid !== undefined && kid !== false)
    .map((kid) => (kid.nodeType ? kid : String(kid))));
  return element;
}

function h(tag, props, ...kids) {
  const element = document.createElement(tag);
  apply(element, props);
  return fill(element, kids);
}

function s(tag, props, ...kids) {
  const element = document.createElementNS(SVG_NS, tag);
  apply(element, props);
  return fill(element, kids);
}

function pad(value) { return String(value).padStart(2, "0"); }

function formatTime(iso) {
  if (!iso) return "không có dữ liệu";
  const date = new Date(iso);
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())} ${pad(date.getDate())}-${pad(date.getMonth() + 1)}`;
}

function formatAge(ms) {
  const minutes = Math.floor(ms / 60000);
  if (minutes < 60) return `${minutes} phút`;
  const hours = Math.floor(minutes / 60);
  return hours < 24 ? `${hours} giờ` : `${Math.floor(hours / 24)} ngày`;
}

function shortName(agent) { return agent.replace("-reviewer", ""); }
function pill([label, tone]) { return h("span", { class: `pill ${tone}` }, label); }
// Own keys only (a status named "constructor" must not hit Object.prototype). An unknown value from a
// newer server shows its raw key instead of breaking the whole render. test_collect runs these in node.
function lookup(table, key) { return Object.hasOwn(table, key) ? table[key] : null; }
function statusPill(table, key) { return pill(lookup(table, key) || [String(key ?? "không rõ"), "tone-warn"]); }
function stageLabel(stage) { return lookup(STAGES, stage) ?? String(stage ?? "không rõ"); }
function currentTab() {
  const id = location.hash.slice(1);
  return TABS.some((tab) => tab.id === id) ? id : "overview";
}

function bar(value, max, label) {
  const percent = max > 0 ? Math.round((value * 100) / max) : 0;
  const inner = h("div", { class: "bar-fill" });
  inner.style.width = `${percent}%`;
  return h("div", { class: "bar", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": 100, "aria-valuenow": percent, "aria-label": label }, inner);
}

function panel(eyebrow, title, right, ...body) {
  return h("section", { class: "panel" },
    h("div", { class: "panel-head" },
      h("div", {}, h("p", { class: "panel-eyebrow" }, eyebrow), h("h2", {}, title)),
      right),
    body);
}

function selectAgent(id) {
  state.selected = state.selected === id ? null : id;
  renderPage();
}

function clearButton() {
  return state.selected
    ? h("button", { type: "button", class: "link-btn", "data-key": "clear", onClick: () => selectAgent(state.selected) }, "Bỏ chọn")
    : h("span", { class: "hint" }, "Chọn agent để lọc");
}

function cardModels(data) {
  const orchestrator = data.orchestrator;
  const first = data.waiting[0];
  return [
    {
      id: "orchestrator", initials: "ĐP", role: "Điều phối & tổng hợp", sub: "session chính",
      status: orchestrator.status,
      note: data.latestRound ? `Vòng review mới nhất: ${data.latestRound.replace("/", " vòng ")}` : "Chưa có vòng review",
      value: orchestrator.roundsSummarized, max: orchestrator.roundsTotal, unit: "vòng đã tổng hợp",
    },
    ...data.agents.map((agent) => {
      const checked = agent.verified.confirmed + agent.verified.refuted + agent.verified.uncertain;
      return {
        id: agent.id, initials: agent.initials, role: agent.role, sub: agent.id, status: agent.status, note: agent.note,
        value: agent.verified.confirmed, max: checked, unit: "finding được xác nhận",
      };
    }),
    {
      id: "human", initials: "B", role: "Bạn", sub: "cổng người duyệt",
      status: data.waiting.length ? "waiting" : "idle",
      note: first ? `${first.id}: ${first.reason}` : "Không có cổng nào đang chờ bạn",
      value: data.counts.tasksDone, max: data.counts.tasksTotal, unit: "task đủ 5 cổng",
    },
  ];
}

function agentCard(model) {
  return h("button", { type: "button", class: "card", "aria-pressed": String(state.selected === model.id), "data-key": `card-${model.id}`, onClick: () => selectAgent(model.id) },
    h("span", { class: "card-head" },
      h("span", { class: "avatar", "aria-hidden": "true" }, model.initials),
      h("span", { class: "card-title" }, h("strong", {}, model.role), h("span", { class: "mono" }, model.sub)),
      statusPill(AGENT_STATUS, model.status)),
    h("span", { class: "card-note" }, model.note),
    model.max > 0
      ? [h("span", { class: "card-foot" }, h("span", {}, `${model.value}/${model.max} ${model.unit}`), h("strong", {}, `${Math.round((model.value * 100) / model.max)}%`)),
        bar(model.value, model.max, model.unit)]
      : h("span", { class: "card-foot" }, h("span", {}, `Chưa có dữ liệu ${model.unit}`)));
}

function renderOverview(data) {
  const progress = data.progress;
  const counts = data.counts;
  const round = data.rounds.find((item) => item.key === data.latestRound);
  const kpi = (value, label, attention) => h("div", { class: `kpi${attention ? " kpi-attention" : ""}` },
    h("div", { class: "kpi-value" }, value ?? "—"), h("div", { class: "kpi-label" }, label));
  return [
    h("section", { class: "panel hero" },
      h("div", { class: "hero-main" },
        h("div", { class: "hero-label" },
          pill(counts.running ? AGENT_STATUS.running : AGENT_STATUS.idle),
          h("span", { class: "panel-eyebrow" }, "Tiến độ tổng")),
        h("div", { class: "percent-row" },
          h("span", { class: "percent" }, progress.percent === null ? "—" : `${progress.percent}%`),
          h("span", {}, `${progress.done}/${progress.total} cổng hoàn tất`)),
        bar(progress.done, progress.total, "Tiến độ tổng"),
        h("p", { class: "hint hero-note" }, `Mỗi cổng ledger có trọng số bằng nhau. Không tính phase tạm dừng: ${progress.activeDone}/${progress.activeTotal}.`)),
      kpi(counts.agents + 2, "Thành viên, gồm điều phối và bạn"),
      kpi(counts.running, "Subagent đang chạy"),
      kpi(counts.waiting, "Chờ bạn duyệt", counts.waiting > 0),
      kpi(counts.latestFindings, "Finding vòng mới nhất")),
    h("div", { class: "meta-row" },
      h("span", {}, "Dữ liệu suy ra từ file của harness"),
      h("span", {}, `Thay đổi mới nhất: ${formatTime(data.lastChangeAt)}`),
      h("span", { id: "connection" }, `Lần kết nối: ${formatTime(state.lastOk)}`)),
    h("div", { class: "two-col" },
      panel("Ai phụ trách việc gì", "Đội thực hiện", clearButton(), h("div", { class: "cards" }, cardModels(data).map(agentCard))),
      panel("Luồng phối hợp", round ? `${round.id} vòng ${round.round}` : "Finding đi qua đâu?", null, graph(round))),
    h("div", { class: "stack" }, reposPanel(data)),
  ];
}

function reposPanel(data) {
  if (!data.repos.length) return null;
  return panel("Mã nguồn", "Trạng thái repo", null, h("div", { class: "repo-list" }, data.repos.map((repo) => h("div", {},
    h("strong", {}, repo.name),
    h("div", { class: "mono" }, repo.branch ?? "không có dữ liệu"),
    h("div", { class: "hint" }, `${repo.dirty} file chưa commit`),
    repo.commit && h("div", { class: "hint" }, `${repo.commit.hash} ${repo.commit.subject}`)))));
}

function graph(round) {
  if (!round) return h("p", { class: "empty" }, "Không có vòng review nào trong _workspace.");
  const reviewers = round.flow.reviewers;
  const width = 460;
  const nodeW = 88;
  const nodeH = 52;
  const rowY = { top: 8, reviewers: 104, gate: 212, summary: 320, lead: 416, human: 512 };
  const spacing = reviewers.length > 1 ? Math.min(150, (width - nodeW) / (reviewers.length - 1)) : 0;
  const slot = (index) => width / 2 + spacing * (index - (reviewers.length - 1) / 2);
  const nodes = [
    { id: "orchestrator", x: width / 2, y: rowY.top, title: "Điều phối", sub: "giao phạm vi", pick: true },
    ...reviewers.map((row, index) => ({ id: row.agent, x: slot(index), y: rowY.reviewers, title: shortName(row.agent), sub: row.done ? "đã ghi" : "chưa có", pick: true })),
    { id: "finding-verifier", x: 145, y: rowY.gate, title: "verifier", sub: round.verifierRan ? "high, medium" : "không chạy", pick: true },
    { id: "low", x: 315, y: rowY.gate, title: "Mức low", sub: "không kiểm" },
    { id: "summary", x: width / 2, y: rowY.summary, title: "Tổng hợp", sub: round.stage === "summarized" ? "đã ghi" : "chưa xong" },
    { id: "lead", x: width / 2, y: rowY.lead, title: "Lead review", sub: round.lead ? round.lead.verdict ?? "chưa rõ" : "không có" },
    { id: "human", x: width / 2, y: rowY.human, title: "Bạn", sub: "duyệt cổng", pick: true },
  ];
  const position = Object.fromEntries(nodes.map((node) => [node.id, node]));
  const flow = round.flow;
  const lowTotal = reviewers.reduce((sum, row) => sum + row.direct, 0);
  const edges = [
    ...reviewers.map((row) => ({ from: "orchestrator", to: row.agent })),
    ...reviewers.filter((row) => row.toVerifier > 0).map((row) => ({ from: row.agent, to: "finding-verifier", label: row.toVerifier })),
    ...reviewers.filter((row) => row.direct > 0).map((row) => ({ from: row.agent, to: "low", label: row.direct })),
    round.verifierRan && { from: "finding-verifier", to: "summary", label: `${flow.confirmed} đúng · ${flow.refuted} bác` },
    lowTotal > 0 && { from: "low", to: "summary", label: lowTotal },
    { from: "summary", to: "lead", label: flow.summaryRows ?? "—", dashed: flow.summaryRows === null },
    { from: "lead", to: "human", label: round.lead && round.lead.needsUser ? `${round.lead.needsUser} cần bạn` : null, dashed: !round.lead },
  ].filter(Boolean);
  const related = new Set();
  if (state.selected) {
    related.add(state.selected);
    edges.forEach((edge) => {
      if (edge.from === state.selected) related.add(edge.to);
      if (edge.to === state.selected) related.add(edge.from);
    });
  }
  const isDim = (id) => state.selected && !related.has(id);
  const edgeNodes = edges.map((edge) => {
    const from = position[edge.from];
    const to = position[edge.to];
    const y1 = from.y + nodeH;
    const y2 = to.y - 5;
    const middle = (y1 + y2) / 2;
    const touches = !state.selected || edge.from === state.selected || edge.to === state.selected;
    const label = edge.label === null || edge.label === undefined ? null : String(edge.label);
    const labelW = label ? label.length * 7 + 12 : 0;
    const midX = (from.x + to.x) / 2;
    return s("g", { class: touches ? "" : "dim" },
      s("path", { class: `edge${edge.dashed ? " edge-dashed" : ""}`, d: `M${from.x},${y1} C${from.x},${middle} ${to.x},${middle} ${to.x},${y2}`, "marker-end": "url(#arrow)" }),
      label && s("rect", { class: "edge-label-bg", x: midX - labelW / 2, y: middle - 9, width: labelW, height: 18, rx: 4 }),
      label && s("text", { class: "edge-label", x: midX, y: middle }, label));
  });
  const nodeEls = nodes.map((node) => {
    const classes = ["node", node.pick && "node-pickable", state.selected === node.id && "node-selected", isDim(node.id) && "dim"].filter(Boolean).join(" ");
    const props = { class: classes, transform: `translate(${node.x - nodeW / 2},${node.y})` };
    if (node.pick) {
      Object.assign(props, {
        role: "button", tabindex: 0, "aria-label": `Lọc theo ${node.title}`, "data-key": `node-${node.id}`,
        onClick: () => selectAgent(node.id),
        onKeydown: (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectAgent(node.id); } },
      });
    }
    return s("g", props,
      s("rect", { width: nodeW, height: nodeH, rx: 9 }),
      s("text", { class: "node-title", x: nodeW / 2, y: 24 }, node.title),
      s("text", { class: "node-sub", x: nodeW / 2, y: 42 }, node.sub));
  });
  const arrow = s("marker", { id: "arrow", viewBox: "0 0 8 8", refX: 6, refY: 4, markerWidth: 7, markerHeight: 7, orient: "auto" },
    s("path", { d: "M0,0 L8,4 L0,8 z", fill: "#4c6480" }));
  return h("div", { class: "graph-wrap" },
    s("svg", { viewBox: `0 0 ${width} ${rowY.human + nodeH + 6}`, role: "group", "aria-label": `Luồng finding của ${round.id} vòng ${round.round}` },
      s("defs", {}, arrow), edgeNodes, nodeEls));
}

function renderAgents(data) {
  const rows = data.agents.map((agent) => h("tr", { class: state.selected === agent.id ? "row-selected" : null },
    h("td", {}, h("strong", {}, agent.role), h("div", { class: "mono" }, agent.id)),
    h("td", {}, agent.model ?? "—"),
    h("td", { class: "num" }, agent.rounds),
    h("td", { class: "num" }, agent.severity.high),
    h("td", { class: "num" }, agent.severity.medium),
    h("td", { class: "num" }, agent.severity.low),
    h("td", { class: "num" }, agent.verified.confirmed),
    h("td", { class: "num" }, agent.verified.refuted),
    h("td", { class: "num" }, agent.verified.uncertain),
    h("td", { class: "num" }, agent.liveRuns)));
  return [
    h("div", { class: "stack" },
      panel("Đội", "Trạng thái từng thành viên", clearButton(), h("div", { class: "cards" }, cardModels(data).map(agentCard))),
      panel("Thống kê", "Kết quả theo agent", h("span", { class: "hint" }, "Chỉ tính các vòng còn trong _workspace (từ 2026-11-03)"),
        h("div", { class: "table-wrap" }, h("table", {},
          h("thead", {}, h("tr", {}, ["Agent", "Model"].map((title) => h("th", { scope: "col" }, title)),
            ["Vòng", "High", "Medium", "Low", "Confirmed", "Refuted", "Uncertain", "Lần chạy ghi nhận"].map((title) => h("th", { scope: "col", class: "num" }, title)))),
          h("tbody", {}, rows))))),
  ];
}

function renderExchange(data) {
  if (!data.rounds.length) return panel("Trao đổi", "Vòng review", null, h("p", { class: "empty" }, "Không có vòng review nào trong _workspace."));
  if (!data.rounds.some((item) => item.key === state.roundKey)) state.roundKey = data.latestRound;
  const round = data.rounds.find((item) => item.key === state.roundKey);
  const steps = [
    ["00", "Chốt phạm vi"], ["01", "Reviewer ghi kết quả"],
    ["02", round.verifierRan ? "Kiểm chứng" : "Kiểm chứng (không chạy)"], ["03", "Tổng hợp"],
  ];
  const rows = round.rows.filter((row) => !state.selected || row.agents.includes(state.selected));
  const picker = h("label", {}, "Vòng",
    h("select", { "data-key": "round", onChange: (event) => { state.roundKey = event.target.value; renderPage(); } },
      data.rounds.map((item) => h("option", { value: item.key, selected: item.key === state.roundKey }, `${item.id} vòng ${item.round}${item.outOfPlan ? " (ngoài kế hoạch)" : ""}`))));
  return h("div", { class: "stack" },
    panel("Trao đổi", round.title, h("div", { class: "filters" }, picker, clearButton()),
      h("div", { class: "steps" }, steps.map(([key, label]) => h("div", { class: `step${round.steps[key] ? "" : " step-off"}` },
        h("strong", {}, label), h("span", {}, round.steps[key] ? formatTime(round.steps[key]) : "chưa có file")))),
      round.missing.length > 0 && h("p", { class: "alert alert-warn" }, `Chưa có kết quả từ: ${round.missing.join(", ")}`),
      h("div", { class: "two-col" },
        h("div", { class: "table-wrap" }, rows.length
          ? h("table", {},
            h("thead", {}, h("tr", {}, ["ID", "Mức", "Nguồn", "Vị trí", "Finding", "Kết luận"].map((title) => h("th", { scope: "col" }, title)))),
            h("tbody", {}, rows.map((row) => h("tr", {},
              h("td", {}, row.id ?? "—"),
              h("td", {}, pill([row.severity, SEVERITY_TONE[row.severity]])),
              h("td", {}, row.source),
              h("td", { class: "mono" }, row.file),
              h("td", {}, row.finding),
              h("td", {}, row.verdict ? pill([row.verdict, VERDICT_TONE[row.verdict]]) : "chưa kết luận")))))
          : h("p", { class: "empty" }, "Không có finding phù hợp."),
          round.refuted.length > 0 && [h("h3", {}, "Đã bị bác"), h("ul", { class: "refuted" }, round.refuted.map((item) => h("li", {}, item.text)))]),
        graph(round))));
}

function renderTasks(data) {
  const phases = [...new Set(data.tasks.map((task) => task.phase))];
  const shown = data.tasks.filter((task) => (state.phase === "all" || task.phase === state.phase) && (state.status === "all" || task.status === state.status));
  const pick = (label, key, value, options) => h("label", {}, label,
    h("select", { "data-key": key, onChange: (event) => { state[key] = event.target.value; renderPage(); } },
      options.map(([optionValue, text]) => h("option", { value: optionValue, selected: optionValue === value }, text))));
  const outOfPlan = data.rounds.filter((item) => item.outOfPlan);
  return h("div", { class: "stack" },
    data.waiting.length > 0 && panel("Cổng người duyệt", "Chờ bạn", null,
      h("ul", { class: "waiting-list" }, data.waiting.map((item) => h("li", {}, h("strong", {}, item.id), h("span", {}, item.title), h("span", { class: "tone-warn" }, item.reason))))),
    panel("Ledger", `${data.counts.tasksDone}/${data.counts.tasksTotal} task đủ 5 cổng`,
      h("div", { class: "filters" },
        pick("Phase", "phase", state.phase, [["all", "Tất cả"], ...phases.map((phase) => [phase, `Phase ${phase}${data.pausedPhases.includes(phase) ? " (tạm dừng)" : ""}`])]),
        pick("Trạng thái", "status", state.status, [["all", "Tất cả"], ...Object.entries(TASK_STATUS).map(([key, value]) => [key, value[0]])])),
      h("div", { class: "table-wrap" }, h("table", {},
        h("thead", {}, h("tr", {}, h("th", { scope: "col" }, "ID"), h("th", { scope: "col" }, "Task"),
          GATES.map((gate) => h("th", { scope: "col", class: "gate" }, gate)),
          h("th", { scope: "col" }, "Trạng thái"), h("th", { scope: "col" }, "Lead review"))),
        h("tbody", {}, shown.map((task) => h("tr", {},
          h("td", {}, h("strong", {}, task.id)),
          h("td", {}, task.title),
          GATES.map((gate) => h("td", { class: `gate ${task.gates[gate] ? "gate-on" : "gate-off"}`, "aria-label": `${gate}: ${task.gates[gate] ? "đã tick" : "chưa tick"}` }, task.gates[gate] ? "✓" : "○")),
          h("td", {}, statusPill(TASK_STATUS, task.status)),
          h("td", {}, task.report ? `vòng ${task.report.round}, ${task.report.verdict}` : "không có dữ liệu"))))))),
    outOfPlan.length > 0 && panel("Ngoài kế hoạch", "Review không gắn với ledger", null,
      h("ul", { class: "waiting-list" }, outOfPlan.map((item) => h("li", {}, h("strong", {}, `${item.id} vòng ${item.round}`), h("span", {}, stageLabel(item.stage)))))));
}

function renderNav() {
  const tab = currentTab();
  document.getElementById("nav").replaceChildren(...TABS.map((item) => h("a", { class: "nav-link", href: `#${item.id}`, "aria-current": item.id === tab ? "page" : null },
    h("span", { class: "nav-icon", "aria-hidden": "true" }, item.icon), item.label)));
}

function renderChrome() {
  const data = state.snapshot;
  const pause = document.getElementById("pause");
  pause.textContent = state.paused ? "Tiếp tục cập nhật" : "Tạm dừng cập nhật";
  const alerts = [];
  if (state.error) alerts.push(h("div", { class: "alert alert-danger", role: "alert" }, state.error));
  if (data) {
    const mission = [data.mission.branch && `Nhánh ${data.mission.branch}`, data.mission.latestRound && `Vòng review mới nhất ${data.mission.latestRound.replace("/", " vòng ")}`].filter(Boolean).join(" · ");
    document.getElementById("mission").textContent = mission || "Không có dữ liệu nhánh";
    const age = data.lastChangeAt ? Date.now() - new Date(data.lastChangeAt).getTime() : null;
    if (age !== null && age > STALE_MS) {
      alerts.push(h("div", { class: "alert alert-warn", role: "status" }, `Chưa có thay đổi mới trong hơn ${formatAge(age)}. Đây là thời điểm file được ghi, không phải bằng chứng agent đã dừng làm việc.`));
    }
    if (data.warnings.length) {
      alerts.push(h("details", { class: "warnings" }, h("summary", {}, `${data.warnings.length} cảnh báo khi đọc dữ liệu`), h("ul", {}, data.warnings.map((warning) => h("li", {}, warning)))));
    }
  }
  const open = document.querySelector("details.warnings")?.open;
  document.getElementById("alerts").replaceChildren(...alerts);
  if (open) document.querySelector("details.warnings").open = true;
  const connection = document.getElementById("connection");
  if (connection) connection.textContent = `Lần kết nối: ${formatTime(state.lastOk)}`;
}

function renderPage() {
  renderNav();
  const data = state.snapshot;
  if (!data) return;
  const focusKey = document.activeElement?.getAttribute?.("data-key");
  const views = { overview: renderOverview, agents: renderAgents, exchange: renderExchange, tasks: renderTasks };
  document.getElementById("page").replaceChildren(...[views[currentTab()](data)].flat(Infinity).filter(Boolean));
  if (focusKey) document.querySelector(`[data-key="${CSS.escape(focusKey)}"]`)?.focus();
}

async function load() {
  try {
    const response = await fetch("/api/snapshot", { cache: "no-store" });
    if (!response.ok) {
      const code = response.status === 503 ? "Không nạp được bộ quét secret nên dashboard từ chối hiển thị dữ liệu." : `Server trả lỗi ${response.status}. Đang giữ dữ liệu cũ.`;
      throw new Error(code);
    }
    const data = await response.json();
    state.lastOk = new Date().toISOString();
    state.error = null;
    const { generatedAt, orchestrator, ...rest } = data;
    const signature = JSON.stringify({ rest, status: orchestrator.status });
    const changed = signature !== state.signature;
    state.snapshot = data;
    state.signature = signature;
    if (changed && document.activeElement?.tagName !== "SELECT") renderPage();
  } catch (error) {
    state.error = error instanceof TypeError ? "Mất kết nối tới server dashboard. Đang giữ dữ liệu cũ." : error.message;
  }
  renderChrome();
}

function schedule() {
  clearInterval(state.timer);
  if (!state.paused) state.timer = setInterval(load, POLL_MS);
}

function start() {
  document.getElementById("pause").addEventListener("click", () => {
    state.paused = !state.paused;
    schedule();
    renderChrome();
  });
  document.getElementById("refresh").addEventListener("click", load);
  window.addEventListener("hashchange", renderPage);
  renderNav();
  schedule();
  load();
}

// Not started outside a browser, so the unit tests can load this file in node.
if (typeof window !== "undefined") start();

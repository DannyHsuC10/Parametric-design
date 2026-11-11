const state = {
  rows: [],
  metrics: [],
  selectedMetric: "total_score",
  selectedTeams: new Set(),
  plottedPoints: [],
};

const els = {
  csvFile: document.querySelector("#csvFile"),
  metricSelect: document.querySelector("#metricSelect"),
  eventSelect: document.querySelector("#eventSelect"),
  teamSearch: document.querySelector("#teamSearch"),
  teamLimit: document.querySelector("#teamLimit"),
  yearFrom: document.querySelector("#yearFrom"),
  yearTo: document.querySelector("#yearTo"),
  teamList: document.querySelector("#teamList"),
  stats: document.querySelector("#stats"),
  chart: document.querySelector("#chart"),
  tooltip: document.querySelector("#tooltip"),
  dataTable: document.querySelector("#dataTable"),
  valueHeader: document.querySelector("#valueHeader"),
  selectAll: document.querySelector("#selectAll"),
  clearAll: document.querySelector("#clearAll"),
  downloadFiltered: document.querySelector("#downloadFiltered"),
};

const ctx = els.chart.getContext("2d");
const colors = [
  "#126b82", "#ce5a36", "#6a5acd", "#268c54", "#b35388", "#8f6b12",
  "#2364aa", "#d22f27", "#008f8c", "#6b7f18", "#9b5de5", "#cc7722",
  "#34495e", "#d1495b", "#0077b6", "#5c8001", "#a44a3f", "#58508d",
];

const metricDefinitions = [
  ["place", "Rank", "rank", true],
  ["total_score", "Total score", "pts", false],
  ["business_plan", "Business Plan", "rank", true],
  ["cost", "Cost / CM", "rank", true],
  ["engineering_design", "Engineering Design", "rank", true],
  ["skidpad", "Skidpad", "rank", true],
  ["acceleration", "Acceleration", "rank", true],
  ["autocross", "Autocross", "rank", true],
  ["endurance", "Endurance", "rank", true],
  ["fuel_efficiency", "Efficiency", "rank", true],
  ["penalties", "Penalties", "pts", false],
  ["teams_count", "Teams entered", "teams", false],
  ["world_ranking", "World ranking", "rank", true],
];

const eventCountries = {
  "FS AA": "Croatia / Alpe Adria",
  "FS AT": "Austria",
  "FS BA": "Bosnia and Herzegovina",
  "FS CH": "Switzerland",
  "FS CN": "China",
  "FS CZ": "Czech Republic",
  "FS DE": "Germany",
  "FS East": "Hungary",
  "FS ES": "Spain",
  "FS FR": "France",
  "FS GR": "Greece",
  "FS HU": "Hungary",
  "FS KR": "South Korea",
  "FS NL": "Netherlands",
  "FS PL": "Poland",
  "FS PT": "Portugal",
  "FS RO": "Romania",
  "FS RU": "Russia",
  "FS TH": "Thailand",
  "FS TR": "Turkey",
  "FS UK": "United Kingdom",
  "FSAE AU": "Australia",
  "FSAE BR": "Brazil",
  "FSAE IT": "Italy",
  "FSAE LN": "United States / Lincoln",
  "FSAE MI": "United States / Michigan",
  "FSAE North": "Canada",
  "F Bharat": "India",
  "JP SF": "Japan",
  "SSAE IN": "India",
};

function eventLabel(event) {
  return eventCountries[event] ? `${event} - ${eventCountries[event]}` : event;
}

function parseCSV(text) {
  const cleaned = text.replace(/^\uFEFF/, "");
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;

  for (let i = 0; i < cleaned.length; i += 1) {
    const char = cleaned[i];
    const next = cleaned[i + 1];
    if (char === '"' && quoted && next === '"') {
      value += '"';
      i += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(value);
      value = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(value);
      if (row.some((cell) => cell.trim() !== "")) rows.push(row);
      row = [];
      value = "";
    } else {
      value += char;
    }
  }

  if (value || row.length) {
    row.push(value);
    if (row.some((cell) => cell.trim() !== "")) rows.push(row);
  }

  if (!rows.length) return [];
  const headers = rows[0].map((header) => header.replace(/^\uFEFF/, "").trim());
  return rows.slice(1).map((cells) => {
    const item = {};
    headers.forEach((header, index) => {
      item[header] = (cells[index] || "").trim();
    });
    return item;
  });
}

function numericValue(raw) {
  if (raw == null) return null;
  const text = String(raw).trim();
  if (!text || /^(-|n\/a|na|n\.a\.|\/)$/i.test(text)) return null;
  const match = text.replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function dateValue(row) {
  return numericValue(row.date);
}

function yearValue(row) {
  const value = dateValue(row);
  return value == null ? null : Math.floor(value);
}

function metricInfo(metricId = state.selectedMetric) {
  const found = state.metrics.find((metric) => metric.id === metricId);
  return found || { id: metricId, label: metricId, unit: "", lowerIsBetter: false };
}

function getMetricValue(row, metricId = state.selectedMetric) {
  return numericValue(row[metricId]);
}

function baseFilteredRows() {
  const event = els.eventSelect.value;
  const from = numericValue(els.yearFrom.value);
  const to = numericValue(els.yearTo.value);
  return state.rows.filter((row) => {
    const year = yearValue(row);
    if (event !== "all" && row.event !== event) return false;
    if (from != null && (year == null || year < from)) return false;
    if (to != null && (year == null || year > to)) return false;
    return true;
  });
}

function teamSummary() {
  const teams = new Map();
  baseFilteredRows().forEach((row) => {
    const team = row.team || "Unknown";
    if (!teams.has(team)) teams.set(team, { team, count: 0, best: null, latest: null });
    const item = teams.get(team);
    const value = getMetricValue(row);
    const date = dateValue(row);
    item.count += 1;
    if (value != null) {
      if (item.best == null) item.best = value;
      else if (metricInfo().lowerIsBetter) item.best = Math.min(item.best, value);
      else item.best = Math.max(item.best, value);
    }
    if (date != null && (item.latest == null || date > item.latest)) item.latest = date;
  });
  return [...teams.values()].sort((a, b) => (
    (b.count - a.count) ||
    ((b.latest || 0) - (a.latest || 0)) ||
    a.team.localeCompare(b.team)
  ));
}

function filteredRows() {
  return baseFilteredRows()
    .map((row) => ({
      row,
      team: row.team || "Unknown",
      index: dateValue(row),
      value: getMetricValue(row),
    }))
    .filter((item) => state.selectedTeams.has(item.team) && item.index != null && item.value != null)
    .sort((a, b) => a.team.localeCompare(b.team) || a.index - b.index);
}

function groupByTeam(items) {
  const grouped = new Map();
  items.forEach((item) => {
    if (!grouped.has(item.team)) grouped.set(item.team, []);
    grouped.get(item.team).push(item);
  });
  return grouped;
}

function setupAfterLoad(rows) {
  state.rows = rows.filter((row) => row.team && dateValue(row) != null);
  state.metrics = discoverMetrics(state.rows);
  state.selectedMetric = state.metrics.some((metric) => metric.id === "total_score") ? "total_score" : state.metrics[0]?.id || "";
  renderMetricOptions();
  renderEventOptions();
  setDefaultYearRange();
  state.selectedTeams = new Set(teamSummary().slice(0, 10).map((team) => team.team));
  renderTeamList();
  renderAll();
}

function discoverMetrics(rows) {
  return metricDefinitions
    .map(([id, label, unit, lowerIsBetter]) => ({
      id,
      label,
      unit,
      lowerIsBetter,
      count: rows.reduce((sum, row) => sum + (numericValue(row[id]) != null ? 1 : 0), 0),
    }))
    .filter((metric) => metric.count > 0);
}

function renderMetricOptions() {
  els.metricSelect.innerHTML = "";
  state.metrics.forEach((metric) => {
    const option = document.createElement("option");
    option.value = metric.id;
    option.textContent = `${metric.label} (${metric.count})`;
    option.selected = metric.id === state.selectedMetric;
    els.metricSelect.append(option);
  });
}

function renderEventOptions() {
  const events = [...new Set(state.rows.map((row) => row.event).filter(Boolean))].sort();
  els.eventSelect.innerHTML = '<option value="all">All events</option>';
  events.forEach((event) => {
    const option = document.createElement("option");
    option.value = event;
    option.textContent = eventLabel(event);
    els.eventSelect.append(option);
  });
}

function setDefaultYearRange() {
  const years = state.rows.map(yearValue).filter((value) => value != null);
  if (!years.length) return;
  els.yearFrom.value = String(Math.min(...years));
  els.yearTo.value = String(Math.max(...years));
}

function renderTeamList() {
  const search = els.teamSearch.value.trim().toLowerCase();
  const limit = els.teamLimit.value;
  let teams = teamSummary().filter((team) => team.team.toLowerCase().includes(search));
  if (limit !== "all") teams = teams.slice(0, Number(limit));

  els.teamList.innerHTML = "";
  if (!teams.length) {
    els.teamList.innerHTML = '<div class="empty">No matching teams.</div>';
    return;
  }

  teams.forEach((team) => {
    const id = `team-${team.team.replace(/[^a-z0-9_-]/gi, "_")}`;
    const label = document.createElement("label");
    label.className = "team-item";
    label.htmlFor = id;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = id;
    checkbox.checked = state.selectedTeams.has(team.team);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) state.selectedTeams.add(team.team);
      else state.selectedTeams.delete(team.team);
      renderAll();
    });

    const name = document.createElement("span");
    name.className = "team-name";
    name.textContent = team.team;

    const count = document.createElement("span");
    count.className = "team-count";
    count.textContent = `${team.count} ${team.count === 1 ? "record" : "records"}`;

    label.append(checkbox, name, count);
    els.teamList.append(label);
  });
}

function renderStats(items) {
  const values = items.map((item) => item.value);
  const teams = new Set(items.map((item) => item.team));
  const events = new Set(items.map((item) => item.row.event).filter(Boolean));
  const info = metricInfo();
  const best = values.length
    ? (info.lowerIsBetter ? Math.min(...values) : Math.max(...values))
    : NaN;
  const average = values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : NaN;
  const cards = [
    ["Records", items.length],
    ["Teams", teams.size],
    ["Events", events.size],
    [info.lowerIsBetter ? "Best rank" : "Maximum", formatValue(best, info.unit)],
    ["Average", formatValue(average, info.unit)],
    ["Year range", yearRangeText(items)],
  ];

  els.stats.innerHTML = cards.map(([label, value]) => (
    `<div class="stat"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`
  )).join("");
}

function yearRangeText(items) {
  const years = items.map((item) => yearValue(item.row)).filter((value) => value != null);
  if (!years.length) return "-";
  return `${Math.min(...years)} - ${Math.max(...years)}`;
}

function formatValue(value, unit = "") {
  if (!Number.isFinite(value)) return "-";
  const rounded = Math.abs(value) >= 100 ? value.toFixed(1).replace(/\.0$/, "") : value.toFixed(2).replace(/\.?0+$/, "");
  return unit ? `${rounded} ${unit}` : rounded;
}

function resizeCanvas() {
  const rect = els.chart.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  els.chart.width = Math.max(640, Math.floor(rect.width * scale));
  els.chart.height = Math.max(380, Math.floor(rect.height * scale));
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
}

function renderChart(items) {
  resizeCanvas();
  const rect = els.chart.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  ctx.clearRect(0, 0, width, height);
  state.plottedPoints = [];

  const padding = { top: 34, right: 32, bottom: 62, left: 78 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  if (!items.length) {
    ctx.fillStyle = "#647184";
    ctx.font = "16px Microsoft JhengHei, Arial";
    ctx.textAlign = "center";
    ctx.fillText("Select a team and a metric with data.", width / 2, height / 2, width - 24);
    return;
  }

  const info = metricInfo();
  const xs = items.map((item) => item.index);
  const ys = items.map((item) => item.value);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const yPad = maxY === minY ? Math.max(1, maxY * 0.1) : (maxY - minY) * 0.12;
  const y0 = minY - yPad;
  const y1 = maxY + yPad;
  const xScale = (value) => padding.left + ((value - minX) / Math.max(1, maxX - minX)) * plotW;
  const yScale = (value) => {
    const normalized = (value - y0) / Math.max(1, y1 - y0);
    const oriented = info.lowerIsBetter ? normalized : 1 - normalized;
    return padding.top + oriented * plotH;
  };

  drawGrid(width, height, padding, plotW, plotH, y0, y1, minX, maxX, info);

  const grouped = groupByTeam(items);
  let colorIndex = 0;
  grouped.forEach((points, team) => {
    const color = colors[colorIndex % colors.length];
    colorIndex += 1;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    points.forEach((point, index) => {
      const x = xScale(point.index);
      const y = yScale(point.value);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    points.forEach((point) => {
      const x = xScale(point.index);
      const y = yScale(point.value);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
      state.plottedPoints.push({ ...point, x, y, color });
    });
  });

  drawLegend([...grouped.keys()]);
}

function drawGrid(width, height, padding, plotW, plotH, y0, y1, minX, maxX, info) {
  ctx.strokeStyle = "#d8dee7";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#647184";
  ctx.font = "12px Microsoft JhengHei, Arial";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";

  for (let i = 0; i <= 5; i += 1) {
    const y = padding.top + (plotH / 5) * i;
    const ratio = i / 5;
    const value = info.lowerIsBetter ? y0 + (y1 - y0) * ratio : y1 - (y1 - y0) * ratio;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillText(formatValue(value, info.unit), padding.left - 10, y);
  }

  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  const xTicks = Math.max(1, Math.min(8, Math.ceil(maxX - minX + 1)));
  for (let i = 0; i < xTicks; i += 1) {
    const ratio = xTicks === 1 ? 0 : i / (xTicks - 1);
    const x = padding.left + plotW * ratio;
    const value = minX + (maxX - minX) * ratio;
    ctx.beginPath();
    ctx.moveTo(x, padding.top);
    ctx.lineTo(x, height - padding.bottom);
    ctx.stroke();
    ctx.fillText(formatDateAxis(value), x, height - padding.bottom + 12);
  }

  ctx.strokeStyle = "#18202a";
  ctx.beginPath();
  ctx.moveTo(padding.left, padding.top);
  ctx.lineTo(padding.left, height - padding.bottom);
  ctx.lineTo(width - padding.right, height - padding.bottom);
  ctx.stroke();

  ctx.fillStyle = "#18202a";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.font = "13px Microsoft JhengHei, Arial";
  ctx.fillText(`${info.label}${info.lowerIsBetter ? " (lower is better)" : ""}`, padding.left, 12);
}

function formatDateAxis(value) {
  const year = Math.floor(value);
  const month = Math.round((value - year) * 100);
  return month ? `${year}.${String(month).padStart(2, "0")}` : String(year);
}

function drawLegend(teams) {
  const width = els.chart.getBoundingClientRect().width;
  let x = 90;
  let y = 38;
  ctx.font = "12px Microsoft JhengHei, Arial";
  ctx.textBaseline = "middle";
  teams.slice(0, 18).forEach((team, index) => {
    const color = colors[index % colors.length];
    const labelWidth = Math.min(150, ctx.measureText(team).width + 24);
    if (x + labelWidth > width - 24) {
      x = 90;
      y += 20;
    }
    ctx.fillStyle = color;
    ctx.fillRect(x, y - 5, 10, 10);
    ctx.fillStyle = "#18202a";
    ctx.fillText(team, x + 15, y);
    x += labelWidth + 16;
  });
}

function renderTable(items) {
  els.valueHeader.textContent = metricInfo().label;
  els.dataTable.innerHTML = "";
  const fragment = document.createDocumentFragment();
  items.forEach((item) => {
    const tr = document.createElement("tr");
    [
      item.team,
      item.row.date,
      eventLabel(item.row.event),
      formatValue(item.value, metricInfo().unit),
      item.row.teams_count || "-",
      item.row.total_score || "-",
    ].forEach((text) => {
      const td = document.createElement("td");
      td.textContent = text;
      tr.append(td);
    });
    fragment.append(tr);
  });

  if (!items.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 6;
    td.className = "empty";
    td.textContent = "No data to display.";
    tr.append(td);
    fragment.append(tr);
  }
  els.dataTable.append(fragment);
}

function renderAll() {
  const items = filteredRows();
  renderStats(items);
  renderChart(items);
  renderTable(items);
}

function nearestPoint(event) {
  const rect = els.chart.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  let closest = null;
  let distance = Infinity;
  state.plottedPoints.forEach((point) => {
    const d = Math.hypot(point.x - x, point.y - y);
    if (d < distance) {
      distance = d;
      closest = point;
    }
  });
  return distance <= 18 ? closest : null;
}

function handleHover(event) {
  const point = nearestPoint(event);
  if (!point) {
    els.tooltip.hidden = true;
    return;
  }
  els.tooltip.hidden = false;
  els.tooltip.style.left = `${Math.min(point.x + 14, els.chart.clientWidth - 210)}px`;
  els.tooltip.style.top = `${Math.max(12, point.y - 48)}px`;
  const team = document.createElement("strong");
  team.textContent = point.team;
  els.tooltip.replaceChildren(team,
    document.createElement("br"), `${point.row.date} ${eventLabel(point.row.event)}`,
    document.createElement("br"), `${metricInfo().label}: ${formatValue(point.value, metricInfo().unit)}`,
    document.createElement("br"), `Total: ${point.row.total_score || "-"}`);
}

function updateTeamsAfterFilterChange() {
  const visibleTeams = new Set(teamSummary().map((team) => team.team));
  state.selectedTeams = new Set([...state.selectedTeams].filter((team) => visibleTeams.has(team)));
  if (!state.selectedTeams.size) {
    teamSummary().slice(0, 10).forEach((team) => state.selectedTeams.add(team.team));
  }
  renderTeamList();
  renderAll();
}

function downloadFilteredCSV() {
  const items = filteredRows();
  const header = ["team", "date", "event", metricInfo().label, "teams_count", "total_score"];
  const lines = [header, ...items.map((item) => [
    item.team,
    item.row.date,
    item.row.event,
    item.value,
    item.row.teams_count,
    item.row.total_score,
  ])]
    .map((row) => row.map((cell) => `"${String(cell ?? "").replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([`\uFEFF${lines}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `fse_filtered_${state.selectedMetric}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function loadDefaultCSV() {
  try {
    const response = await fetch("data/fse_historical_results.csv", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    setupAfterLoad(parseCSV(await response.text()));
  } catch (error) {
    els.teamList.innerHTML = '<div class="empty">Could not load the default data. Select Import CSV to load a file.</div>';
    renderAll();
  }
}

els.metricSelect.addEventListener("change", () => {
  state.selectedMetric = els.metricSelect.value;
  renderTeamList();
  renderAll();
});
els.eventSelect.addEventListener("change", updateTeamsAfterFilterChange);
els.teamSearch.addEventListener("input", renderTeamList);
els.teamLimit.addEventListener("change", renderTeamList);
els.yearFrom.addEventListener("input", updateTeamsAfterFilterChange);
els.yearTo.addEventListener("input", updateTeamsAfterFilterChange);
els.selectAll.addEventListener("click", () => {
  teamSummary().forEach((team) => state.selectedTeams.add(team.team));
  renderTeamList();
  renderAll();
});
els.clearAll.addEventListener("click", () => {
  state.selectedTeams.clear();
  renderTeamList();
  renderAll();
});
els.csvFile.addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (!file) return;
  setupAfterLoad(parseCSV(await file.text()));
});
els.chart.addEventListener("mousemove", handleHover);
els.chart.addEventListener("mouseleave", () => {
  els.tooltip.hidden = true;
});
els.downloadFiltered.addEventListener("click", downloadFilteredCSV);
window.addEventListener("resize", renderAll);

loadDefaultCSV();

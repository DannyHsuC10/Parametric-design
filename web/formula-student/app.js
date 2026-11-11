const state = {
  rows: [],
  metrics: [],
  selectedMetric: "Wheelbase",
  selectedTeams: new Set(),
  vehicleFilters: {
    electric: false,
    hoosier: false,
    tenInch: false,
  },
  hoveredPoint: null,
  plottedPoints: [],
};

const els = {
  csvFile: document.querySelector("#csvFile"),
  metricSelect: document.querySelector("#metricSelect"),
  teamSearch: document.querySelector("#teamSearch"),
  teamLimit: document.querySelector("#teamLimit"),
  teamList: document.querySelector("#teamList"),
  stats: document.querySelector("#stats"),
  chart: document.querySelector("#chart"),
  tooltip: document.querySelector("#tooltip"),
  dataTable: document.querySelector("#dataTable"),
  valueHeader: document.querySelector("#valueHeader"),
  selectAll: document.querySelector("#selectAll"),
  clearAll: document.querySelector("#clearAll"),
  downloadFiltered: document.querySelector("#downloadFiltered"),
  filterElectric: document.querySelector("#filterElectric"),
  filterHoosier: document.querySelector("#filterHoosier"),
  filterTenInch: document.querySelector("#filterTenInch"),
};

const ctx = els.chart.getContext("2d");
const colors = [
  "#126b82", "#ce5a36", "#6a5acd", "#268c54", "#b35388", "#8f6b12",
  "#2364aa", "#d22f27", "#008f8c", "#6b7f18", "#9b5de5", "#cc7722",
  "#34495e", "#d1495b", "#0077b6", "#5c8001", "#a44a3f", "#58508d",
];

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

  if (rows.length === 0) return [];
  const headers = rows[0].map((header) => normalizeHeader(header));
  return rows.slice(1).map((cells) => {
    const item = {};
    headers.forEach((header, index) => {
      item[header] = (cells[index] || "").trim();
    });
    return item;
  });
}

function normalizeHeader(header) {
  return header.replace(/^\uFEFF/, "").replace(/\*/g, "").trim();
}

function numericValue(raw) {
  if (raw == null) return null;
  const text = String(raw).trim();
  if (!text || /^(-|n\/a|na|n\.a\.|\/)$/i.test(text)) return null;
  const match = text.replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function getMetricValue(row, metric) {
  if (metric === "__total_weight") {
    const front = numericValue(row["Weight with 68kg driver (Fr)"]);
    const rear = numericValue(row["Weight with 68kg driver (Rr)"]);
    return front != null && rear != null ? front + rear : null;
  }

  if (metric === "__average_track") {
    const front = numericValue(row["Track (Fr)"]);
    const rear = numericValue(row["Track (Rr)"]);
    return front != null && rear != null ? (front + rear) / 2 : null;
  }

  if (metric === "__track_ratio") {
    const front = numericValue(row["Track (Fr)"]);
    const rear = numericValue(row["Track (Rr)"]);
    return front != null && rear ? front / rear : null;
  }

  if (metric === "__weight_ratio") {
    const front = numericValue(row["Weight with 68kg driver (Fr)"]);
    const rear = numericValue(row["Weight with 68kg driver (Rr)"]);
    return front != null && rear ? front / rear : null;
  }

  return numericValue(row[metric]);
}

function getMetricRaw(row, metric) {
  if (metric === "__total_weight") {
    return `${row["Weight with 68kg driver (Fr)"] || "-"} + ${row["Weight with 68kg driver (Rr)"] || "-"}`;
  }

  if (metric === "__average_track") {
    return `${row["Track (Fr)"] || "-"} / ${row["Track (Rr)"] || "-"}`;
  }

  if (metric === "__track_ratio") {
    return `${row["Track (Fr)"] || "-"} / ${row["Track (Rr)"] || "-"}`;
  }

  if (metric === "__weight_ratio") {
    return `${row["Weight with 68kg driver (Fr)"] || "-"} / ${row["Weight with 68kg driver (Rr)"] || "-"}`;
  }

  return row[metric] || "-";
}

function metricLabel(metric) {
  const labels = {
    "__total_weight": "Total weight with 68 kg driver",
    "__average_track": "Average track width",
    "__track_ratio": "Front/rear track ratio",
    "__weight_ratio": "Front/rear weight ratio",
  };
  return labels[metric] || metric;
}

function metricUnit(metric) {
  if (metric === "__track_ratio" || metric === "__weight_ratio") return "x";
  const name = metricLabel(metric).toLowerCase();
  if (name.includes("weight")) return "kg";
  if (name.includes("wheelbase") || name.includes("track") || name.includes("overall")) return "mm";
  if (name.includes("voltage")) return "V";
  if (name.includes("capacity")) return "kWh";
  if (name.includes("power")) return "kW";
  if (name.includes("rpm")) return "rpm";
  return "";
}

function discoverMetrics(rows) {
  if (rows.length === 0) return [];
  const numericHeaders = [
    "Overall L",
    "Overall W",
    "Overall H",
    "Wheelbase",
    "Track (Fr)",
    "Track (Rr)",
    "Weight with 68kg driver (Fr)",
    "Weight with 68kg driver (Rr)",
    "Number of Motors",
    "Max Motor Power (per motor)",
    "Max Motor RPM (highest)",
    "Max System Voltage",
    "Combined Accumulator Capacity",
    "Transmission Ratio (Primary)",
    "Transmission Ratio (Secondary)",
    "Floating Point Operations Per Second of all processing units that are working for the DV system",
    "Power consumption of all processing units that are working for the DV system",
    "Bore",
    "Stroke",
    "Cylinders",
    "Displacement",
    "Compression Ratio",
    "Max Power Design",
    "Max Torque Design",
  ];
  const headers = numericHeaders.filter((header) => Object.hasOwn(rows[0], header));
  const metrics = headers
    .map((header) => ({
      id: header,
      label: header,
      count: rows.reduce((sum, row) => sum + (numericValue(row[header]) != null ? 1 : 0), 0),
    }))
    .filter((metric) => metric.count > 0);

  metrics.unshift(
    metricSummary(rows, "__total_weight"),
    metricSummary(rows, "__average_track"),
    metricSummary(rows, "__track_ratio"),
    metricSummary(rows, "__weight_ratio"),
  );

  return metrics;
}

function metricSummary(rows, id) {
  return {
    id,
    label: metricLabel(id),
    count: rows.reduce((sum, row) => sum + (getMetricValue(row, id) != null ? 1 : 0), 0),
  };
}

function vehicleText(row) {
  return [
    row["Tyres (Fr / Rr)"],
    row["Wheels (Fr / Rr)"],
    row["Drive Type"],
    row["Motor Type"],
    row["Motor Controller"],
    row["Max System Voltage"],
    row["Combined Accumulator Capacity"],
    row["Electrode Materials"],
  ].filter(Boolean).join(" ").toLowerCase();
}

function isElectricVehicle(row) {
  return (
    numericValue(row["Number of Motors"]) != null ||
    numericValue(row["Max System Voltage"]) != null ||
    numericValue(row["Combined Accumulator Capacity"]) != null ||
    Boolean(row["Electrode Materials"])
  );
}

function hasHoosier(row) {
  return vehicleText(row).includes("hoosier");
}

function hasTenInchWheelOrTyre(row) {
  const text = vehicleText(row);
  return /(^|[^0-9])10(?:\s*(?:in|inch|["']))?([^0-9]|$)|[-x]\s*10\b/i.test(text);
}

function rowMatchesVehicleFilters(row) {
  if (state.vehicleFilters.electric && !isElectricVehicle(row)) return false;
  if (state.vehicleFilters.hoosier && !hasHoosier(row)) return false;
  if (state.vehicleFilters.tenInch && !hasTenInchWheelOrTyre(row)) return false;
  return true;
}

function vehicleFilteredRows() {
  return state.rows.filter(rowMatchesVehicleFilters);
}

function teamSummary() {
  const teams = new Map();
  vehicleFilteredRows().forEach((row) => {
    const team = row.team || "Unknown";
    if (!teams.has(team)) teams.set(team, { team, count: 0 });
    teams.get(team).count += 1;
  });
  return [...teams.values()].sort((a, b) => b.count - a.count || a.team.localeCompare(b.team));
}

function timelineValue(row) {
  const year = numericValue(row.year);
  return year != null ? year : numericValue(row.car_index);
}

function timelineLabel() {
  return state.rows.some((row) => numericValue(row.year) != null) ? "Year" : "Car index";
}

function setupAfterLoad(rows) {
  state.rows = rows.filter((row) => row.team && timelineValue(row) != null);
  state.metrics = discoverMetrics(state.rows);
  const defaultMetric = state.metrics.find((metric) => metric.id === "Wheelbase") || state.metrics[0];
  state.selectedMetric = defaultMetric ? defaultMetric.id : "";

  const defaultTeams = teamSummary().slice(0, 10).map((team) => team.team);
  state.selectedTeams = new Set(defaultTeams);

  renderMetricOptions();
  renderTeamList();
  renderAll();
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

function renderTeamList() {
  const search = els.teamSearch.value.trim().toLowerCase();
  const limit = els.teamLimit.value;
  let teams = teamSummary().filter((team) => team.team.toLowerCase().includes(search));
  if (limit !== "all") teams = teams.slice(0, Number(limit));

  els.teamList.innerHTML = "";
  if (teams.length === 0) {
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

function filteredRows() {
  return vehicleFilteredRows()
    .map((row) => ({
      row,
      team: row.team || "Unknown",
      index: timelineValue(row),
      value: getMetricValue(row, state.selectedMetric),
      raw: getMetricRaw(row, state.selectedMetric),
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

function renderStats(items) {
  const values = items.map((item) => item.value);
  const teams = new Set(items.map((item) => item.team));
  const unit = metricUnit(state.selectedMetric);
  const grouped = groupByTeam(items);
  const oldestValues = [];
  const latestValues = [];
  grouped.forEach((points) => {
    const sorted = [...points].sort((a, b) => a.index - b.index);
    if (sorted[0]) oldestValues.push(sorted[0].value);
    if (sorted[sorted.length - 1]) latestValues.push(sorted[sorted.length - 1].value);
  });

  const totalAverage = averageOf(values);
  const oldestAverage = averageOf(oldestValues);
  const latestAverage = averageOf(latestValues);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 0;
  const cards = [
    ["Records", items.length],
    ["Teams", teams.size],
    ["Latest per team (avg.)", formatValue(latestAverage, unit)],
    ["Earliest per team (avg.)", formatValue(oldestAverage, unit)],
    ["Overall average", formatValue(totalAverage, unit)],
    ["Range", values.length ? `${formatValue(min, unit)} - ${formatValue(max, unit)}` : "-"],
  ];

  els.stats.innerHTML = cards.map(([label, value]) => (
    `<div class="stat"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`
  )).join("");
}

function averageOf(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : NaN;
}

function formatValue(value, unit = "") {
  if (!Number.isFinite(value)) return "-";
  const rounded = Math.abs(value) >= 100 ? value.toFixed(0) : value.toFixed(2).replace(/\.?0+$/, "");
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
  const yScale = (value) => padding.top + (1 - ((value - y0) / Math.max(1, y1 - y0))) * plotH;
  const unit = metricUnit(state.selectedMetric);

  drawGrid(width, height, padding, plotW, plotH, y0, y1, minX, maxX, unit);

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

function drawGrid(width, height, padding, plotW, plotH, y0, y1, minX, maxX, unit) {
  ctx.strokeStyle = "#d8dee7";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#647184";
  ctx.font = "12px Microsoft JhengHei, Arial";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";

  for (let i = 0; i <= 5; i += 1) {
    const y = padding.top + (plotH / 5) * i;
    const value = y1 - ((y1 - y0) / 5) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillText(formatValue(value, unit), padding.left - 10, y);
  }

  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  const xTicks = Math.max(1, Math.min(8, Math.ceil(maxX - minX + 1)));
  for (let i = 0; i < xTicks; i += 1) {
    const ratio = xTicks === 1 ? 0 : i / (xTicks - 1);
    const x = padding.left + plotW * ratio;
    const value = Math.round(minX + (maxX - minX) * ratio);
    ctx.beginPath();
    ctx.moveTo(x, padding.top);
    ctx.lineTo(x, height - padding.bottom);
    ctx.stroke();
    ctx.fillText(String(value), x, height - padding.bottom + 12);
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
  ctx.fillText(metricLabel(state.selectedMetric), padding.left, 12);
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
  els.valueHeader.textContent = metricLabel(state.selectedMetric);
  const timelineHeader = document.querySelector("thead th:nth-child(2)");
  if (timelineHeader) timelineHeader.textContent = timelineLabel();
  els.dataTable.innerHTML = "";
  const fragment = document.createDocumentFragment();

  items.forEach((item) => {
    const tr = document.createElement("tr");
    [item.team, item.index, formatValue(item.value, metricUnit(state.selectedMetric)), item.raw].forEach((text) => {
      const td = document.createElement("td");
      td.textContent = text;
      tr.append(td);
    });
    fragment.append(tr);
  });

  if (!items.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 4;
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
  els.tooltip.style.left = `${Math.min(point.x + 14, els.chart.clientWidth - 180)}px`;
  els.tooltip.style.top = `${Math.max(12, point.y - 42)}px`;
  const team = document.createElement("strong");
  team.textContent = point.team;
  els.tooltip.replaceChildren(team,
    document.createElement("br"), `${timelineLabel()}: ${point.index}`,
    document.createElement("br"), `${metricLabel(state.selectedMetric)}: ${formatValue(point.value, metricUnit(state.selectedMetric))}`);
}

function downloadFilteredCSV() {
  const items = filteredRows();
  const header = ["team", timelineLabel(), metricLabel(state.selectedMetric), "raw_value"];
  const lines = [header, ...items.map((item) => [item.team, item.index, item.value, item.raw])]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([`\uFEFF${lines}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `filtered_${state.selectedMetric.replace(/[^a-z0-9]+/gi, "_")}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function loadDefaultCSV() {
  try {
    const response = await fetch("data/FSG_EV_vehicle_database.csv", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    setupAfterLoad(parseCSV(await response.text()));
  } catch (error) {
    els.teamList.innerHTML = '<div class="empty">Could not load the default data. Select Import CSV to load a file.</div>';
    renderAll();
  }
}

els.metricSelect.addEventListener("change", () => {
  state.selectedMetric = els.metricSelect.value;
  renderAll();
});

els.teamSearch.addEventListener("input", renderTeamList);
els.teamLimit.addEventListener("change", renderTeamList);

function updateVehicleFilters() {
  state.vehicleFilters.electric = els.filterElectric.checked;
  state.vehicleFilters.hoosier = els.filterHoosier.checked;
  state.vehicleFilters.tenInch = els.filterTenInch.checked;
  renderTeamList();
  renderAll();
}

els.filterElectric.addEventListener("change", updateVehicleFilters);
els.filterHoosier.addEventListener("change", updateVehicleFilters);
els.filterTenInch.addEventListener("change", updateVehicleFilters);

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

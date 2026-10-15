const state = {
  rows: [],
  parameters: [],
  selectedParameter: "Wheelbase",
  summaryRows: [],
};

const els = {
  csvFile: document.querySelector("#csvFile"),
  parameterSelect: document.querySelector("#parameterSelect"),
  eventSelect: document.querySelector("#eventSelect"),
  yearFrom: document.querySelector("#yearFrom"),
  yearTo: document.querySelector("#yearTo"),
  weightMode: document.querySelector("#weightMode"),
  yearWeightMode: document.querySelector("#yearWeightMode"),
  filterTenInchElectric: document.querySelector("#filterTenInchElectric"),
  stats: document.querySelector("#stats"),
  countedTeams: document.querySelector("#countedTeams"),
  chart: document.querySelector("#chart"),
  statsTable: document.querySelector("#statsTable"),
  downloadStats: document.querySelector("#downloadStats"),
};

const ctx = els.chart.getContext("2d");

const parameters = [
  { name: "Overall length", columns: ["vehicle_Overall L"], unit: "mm", method: "first", min: 1000, max: 4000 },
  { name: "Overall width", columns: ["vehicle_Overall W"], unit: "mm", method: "first", min: 800, max: 2500 },
  { name: "Overall height", columns: ["vehicle_Overall H"], unit: "mm", method: "first", min: 500, max: 2500 },
  { name: "Wheelbase", columns: ["vehicle_Wheelbase"], unit: "mm", method: "first", min: 1000, max: 3000 },
  { name: "Front track", columns: ["vehicle_Track (Fr)"], unit: "mm", method: "first", min: 700, max: 2000 },
  { name: "Rear track", columns: ["vehicle_Track (Rr)"], unit: "mm", method: "first", min: 700, max: 2000 },
  { name: "Front/rear track ratio", columns: ["vehicle_Track (Fr)", "vehicle_Track (Rr)"], unit: "ratio", method: "ratio", min: 0.75, max: 1.35 },
  { name: "Front weight with driver", columns: ["vehicle_Weight with 68kg driver (Fr)"], unit: "kg", method: "first", min: 40, max: 350 },
  { name: "Rear weight with driver", columns: ["vehicle_Weight with 68kg driver (Rr)"], unit: "kg", method: "first", min: 40, max: 350 },
  { name: "Total weight with driver", columns: ["vehicle_Weight with 68kg driver (Fr)", "vehicle_Weight with 68kg driver (Rr)"], unit: "kg", method: "sum", min: 150, max: 700 },
  { name: "Front/rear weight ratio", columns: ["vehicle_Weight with 68kg driver (Fr)", "vehicle_Weight with 68kg driver (Rr)"], unit: "ratio", method: "ratio", min: 0.3, max: 2.5 },
  { name: "Number of motors", columns: ["vehicle_Number of Motors"], unit: "count", method: "first", min: 1, max: 8 },
  { name: "Max motor power per motor", columns: ["vehicle_Max Motor Power (per motor)"], unit: "kW", method: "max", min: 5, max: 300 },
  { name: "Max motor RPM", columns: ["vehicle_Max Motor RPM (highest)"], unit: "rpm", method: "first", min: 1000, max: 50000 },
  { name: "Max system voltage", columns: ["vehicle_Max System Voltage"], unit: "V", method: "first", min: 20, max: 900 },
  { name: "Accumulator capacity", columns: ["vehicle_Combined Accumulator Capacity"], unit: "kWh", method: "first", min: 0.5, max: 20 },
  {
    name: "DV processing performance",
    columns: ["vehicle_Floating Point Operations Per Second of all processing units that are working for the DV system"],
    unit: "GigaFLOPS",
    method: "max",
    min: 1,
    max: 20000,
  },
  {
    name: "DV processing power consumption",
    columns: ["vehicle_Power consumption of all processing units that are working for the DV system"],
    unit: "W",
    method: "first",
    min: 1,
    max: 2000,
  },
  { name: "Engine bore", columns: ["vehicle_Bore"], unit: "mm", method: "first", min: 10, max: 150 },
  { name: "Engine stroke", columns: ["vehicle_Stroke"], unit: "mm", method: "first", min: 10, max: 150 },
  { name: "Cylinders", columns: ["vehicle_Cylinders"], unit: "count", method: "first", min: 1, max: 8 },
  { name: "Displacement", columns: ["vehicle_Displacement"], unit: "cc", method: "first", min: 50, max: 1500 },
  { name: "Compression ratio", columns: ["vehicle_Compression Ratio"], unit: "ratio", method: "first", min: 5, max: 20 },
  { name: "Max power design", columns: ["vehicle_Max Power Design"], unit: "kW", method: "first", min: 1, max: 300 },
  { name: "Max torque design", columns: ["vehicle_Max Torque Design"], unit: "Nm", method: "first", min: 1, max: 500 },
];

const fieldRanges = new Map([
  ["vehicle_Track (Fr)", [700, 2000]],
  ["vehicle_Track (Rr)", [700, 2000]],
  ["vehicle_Weight with 68kg driver (Fr)", [40, 350]],
  ["vehicle_Weight with 68kg driver (Rr)", [40, 350]],
]);

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

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
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

function cleanNumberToken(token) {
  const trimmed = String(token || "").trim();
  if (!trimmed) return null;
  let normalized = trimmed;

  if (trimmed.includes(",") && trimmed.includes(".")) {
    normalized = trimmed.replace(/,/g, "");
  } else if (trimmed.includes(",")) {
    const [left, right] = trimmed.split(",", 2);
    normalized = right.length === 3 && left.length >= 1 && left.length <= 3 ? `${left}${right}` : `${left}.${right}`;
  } else if (trimmed.includes(".")) {
    const [left, right] = trimmed.split(".", 2);
    if (right.length === 3 && left.length >= 1 && left.length <= 3) {
      const decimalValue = Number(`${left}.${right}`);
      return decimalValue < 100 ? Number(`${left}${right}`) : decimalValue;
    }
  }

  const value = Number(normalized);
  return Number.isFinite(value) ? value : null;
}

function numberTokens(raw) {
  const text = String(raw ?? "").trim();
  if (!text || /^(-|n\/a|na|n\.a\.|\/)$/i.test(text)) return [];
  const matches = text.match(/-?\d+(?:[,.]\d+)?/g) || [];
  return matches.map(cleanNumberToken).filter((value) => value != null);
}

function inRange(value, min, max) {
  if (value == null || !Number.isFinite(value)) return false;
  if (min != null && value < min) return false;
  if (max != null && value > max) return false;
  return true;
}

function firstValidForColumn(row, column) {
  const [min, max] = fieldRanges.get(column) || [null, null];
  return numberTokens(row[column]).find((value) => inRange(value, min, max)) ?? null;
}

function parameterValue(row, parameter) {
  if (parameter.method === "sum") {
    const values = parameter.columns.map((column) => firstValidForColumn(row, column));
    if (values.some((value) => value == null)) return null;
    const total = values.reduce((sum, value) => sum + value, 0);
    return inRange(total, parameter.min, parameter.max) ? total : null;
  }

  if (parameter.method === "ratio") {
    const values = parameter.columns.map((column) => firstValidForColumn(row, column));
    if (values.some((value) => value == null) || values[1] === 0) return null;
    const ratio = values[0] / values[1];
    return inRange(ratio, parameter.min, parameter.max) ? ratio : null;
  }

  const values = [];
  parameter.columns.forEach((column) => {
    numberTokens(row[column]).forEach((value) => {
      if (inRange(value, parameter.min, parameter.max)) values.push(value);
    });
  });
  if (!values.length) return null;
  return parameter.method === "max" ? Math.max(...values) : values[0];
}

function parseRank(row) {
  const values = numberTokens(row.place);
  const rank = values[0];
  return rank > 0 ? rank : null;
}

function weightFromRank(rank, mode = els.weightMode.value) {
  if (rank == null) return null;
  if (mode === "inverse_rank") return 1 / rank;
  if (mode === "inverse_sqrt_rank") return 1 / Math.sqrt(rank);
  return 1;
}

function weightFromYear(year, latestYear, mode = els.yearWeightMode.value) {
  if (year == null || latestYear == null) return 1;
  const age = Math.max(0, Math.floor(latestYear) - Math.floor(year));
  if (mode === "recency_inverse_age") return 1 / (1 + age);
  if (mode === "recency_exp_5") return 0.5 ** (age / 5);
  return 1;
}

function numericValue(raw) {
  return numberTokens(raw)[0] ?? null;
}

function yearValue(row) {
  return numericValue(row.match_year || row.date);
}

function annualKey(row) {
  const team = String(row.team || "").trim().toLowerCase().replace(/\s+/g, " ");
  const year = yearValue(row);
  if (!team || year == null) return null;
  return `${team}::${Math.floor(year)}`;
}

function isElectricVehicle(row) {
  return (
    numberTokens(row["vehicle_Number of Motors"]).some((value) => value > 0) ||
    numberTokens(row["vehicle_Max System Voltage"]).length > 0 ||
    numberTokens(row["vehicle_Combined Accumulator Capacity"]).length > 0 ||
    Boolean(row["vehicle_Electrode Materials"])
  );
}

function hasTenInchTyre(row) {
  const tyreAndWheelText = [row["vehicle_Tyres (Fr / Rr)"], row["vehicle_Wheels (Fr / Rr)"]]
    .filter(Boolean)
    .join(" ");
  return /\b\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?\s*[-/]\s*10\b|\b10\s*(?:in(?:ch(?:es)?)?|["″”])/i.test(tyreAndWheelText);
}

function filteredBaseRows() {
  const event = els.eventSelect.value;
  const from = numericValue(els.yearFrom.value);
  const to = numericValue(els.yearTo.value);
  return state.rows.filter((row) => {
    const year = yearValue(row);
    if (event !== "all" && row.event !== event) return false;
    if (from != null && (year == null || year < from)) return false;
    if (to != null && (year == null || year > to)) return false;
    if (els.filterTenInchElectric.checked && (!isElectricVehicle(row) || !hasTenInchTyre(row))) return false;
    return true;
  });
}

function samplesForParameter(parameter, rows = filteredBaseRows()) {
  const groups = new Map();
  const latestYear = rows
    .map(yearValue)
    .filter((value) => value != null)
    .reduce((latest, year) => Math.max(latest, Math.floor(year)), null);

  rows.forEach((row) => {
    const key = annualKey(row);
    const rank = parseRank(row);
    const value = parameterValue(row, parameter);
    if (!key || rank == null || value == null) return;

    if (!groups.has(key)) {
      groups.set(key, {
        values: [],
        bestRank: rank,
        team: row.team || "",
        year: yearValue(row),
        events: new Set(),
      });
    }

    const group = groups.get(key);
    group.values.push(value);
    group.bestRank = Math.min(group.bestRank, rank);
    if (row.event) group.events.add(row.event);
  });

  return Array.from(groups.values()).map((group) => {
    const value = mean(group.values);
    const rankWeight = weightFromRank(group.bestRank);
    const yearWeight = weightFromYear(group.year, latestYear);
    const weight = rankWeight == null ? null : rankWeight * yearWeight;
    if (weight == null || weight <= 0) return null;
    return {
      value,
      weight,
      rankWeight,
      yearWeight,
      rank: group.bestRank,
      team: group.team,
      year: group.year,
      event: Array.from(group.events).join(", "),
      eventCount: group.events.size,
    };
  }).filter(Boolean);
}

function mean(values) {
  if (!values.length) return NaN;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function std(values, center = mean(values)) {
  if (!values.length) return NaN;
  const variance = values.reduce((sum, value) => sum + (value - center) ** 2, 0) / values.length;
  return Math.sqrt(Math.max(variance, 0));
}

function weightedStats(samples) {
  const totalWeight = samples.reduce((sum, sample) => sum + sample.weight, 0);
  if (!samples.length || totalWeight <= 0) return { mean: NaN, std: NaN, totalWeight: 0 };
  const weightedMean = samples.reduce((sum, sample) => sum + sample.value * sample.weight, 0) / totalWeight;
  const variance = samples.reduce((sum, sample) => sum + sample.weight * (sample.value - weightedMean) ** 2, 0) / totalWeight;
  return { mean: weightedMean, std: Math.sqrt(Math.max(variance, 0)), totalWeight };
}

function statsForParameter(parameter) {
  const samples = samplesForParameter(parameter);
  const values = samples.map((sample) => sample.value);
  const unweightedMean = mean(values);
  const unweightedStd = std(values, unweightedMean);
  const weighted = weightedStats(samples);
  return {
    parameter,
    samples,
    count: samples.length,
    observedMin: Math.min(...values),
    observedMax: Math.max(...values),
    unweightedMean,
    unweightedStd,
    weightedMean: weighted.mean,
    weightedStd: weighted.std,
    totalWeight: weighted.totalWeight,
  };
}

function fmt(value, digits = 2) {
  if (!Number.isFinite(value)) return "-";
  if (Math.abs(value) >= 1000) return value.toFixed(0);
  if (Math.abs(value) >= 100) return value.toFixed(1);
  return value.toFixed(digits).replace(/\.?0+$/, "");
}

function rangeText(center, deviation, unit) {
  if (!Number.isFinite(center) || !Number.isFinite(deviation)) return "-";
  return `${fmt(center - 1 * deviation)} - ${fmt(center + 1 * deviation)} ${unit}`;
}

function clippedRange(center, deviation, parameter) {
  if (!Number.isFinite(center) || !Number.isFinite(deviation)) return null;
  let lower = center - 1 * deviation;
  let upper = center + 1 * deviation;
  if (parameter.min != null) lower = Math.max(lower, parameter.min);
  if (parameter.max != null) upper = Math.min(upper, parameter.max);
  return { lower, upper };
}

function clippedRangeText(center, deviation, parameter) {
  const range = clippedRange(center, deviation, parameter);
  if (!range) return "-";
  return `${fmt(range.lower)} - ${fmt(range.upper)} ${parameter.unit}`;
}

function normalPdf(x, center, deviation) {
  if (!Number.isFinite(deviation) || deviation <= 0) return 0;
  const exponent = -0.5 * ((x - center) / deviation) ** 2;
  return Math.exp(exponent) / (deviation * Math.sqrt(2 * Math.PI));
}

function setupAfterLoad(rows) {
  state.rows = rows.filter((row) => row.team && yearValue(row) != null);
  state.parameters = parameters.filter((parameter) => samplesForParameter(parameter, state.rows).length >= 5);
  state.selectedParameter = state.parameters.some((parameter) => parameter.name === "Wheelbase")
    ? "Wheelbase"
    : state.parameters[0]?.name || "";
  renderParameterOptions();
  renderEventOptions();
  setDefaultYearRange();
  renderAll();
}

function renderParameterOptions() {
  els.parameterSelect.innerHTML = "";
  state.parameters.forEach((parameter) => {
    const option = document.createElement("option");
    option.value = parameter.name;
    option.textContent = `${parameter.name} (${parameter.unit})`;
    option.selected = parameter.name === state.selectedParameter;
    els.parameterSelect.append(option);
  });
}

function renderEventOptions() {
  const events = [...new Set(state.rows.map((row) => row.event).filter(Boolean))].sort();
  els.eventSelect.innerHTML = '<option value="all">全部賽事</option>';
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

function renderStatsCards(summary) {
  const unit = summary.parameter.unit;
  const diff = summary.weightedMean - summary.unweightedMean;
  els.stats.innerHTML = [
    ["年度樣本數", `${summary.count}`, `weighted n = ${fmt(summary.totalWeight, 3)}`],
    ["未加權平均 / σ", `${fmt(summary.unweightedMean)} ${unit}`, `σ = ${fmt(summary.unweightedStd)}`],
    ["加權平均 / σ", `${fmt(summary.weightedMean)} ${unit}`, `σ = ${fmt(summary.weightedStd)}`],
    ["加權 - 未加權", `${diff >= 0 ? "+" : ""}${fmt(diff)} ${unit}`, "同車隊同年只算一次"],
    ["未加權 1σ", rangeText(summary.unweightedMean, summary.unweightedStd, unit), "mean ± 1σ"],
    ["加權 1σ", rangeText(summary.weightedMean, summary.weightedStd, unit), "mean ± 1σ"],
    ["加權建議範圍", clippedRangeText(summary.weightedMean, summary.weightedStd, summary.parameter), "以合理上下限截斷"],
    ["觀測範圍", `${fmt(summary.observedMin)} - ${fmt(summary.observedMax)} ${unit}`, "CSV 實際值"],
    ["排名權重", els.weightMode.options[els.weightMode.selectedIndex].textContent, "年度最佳 place 計算"],
    ["年度權重", els.yearWeightMode.options[els.yearWeightMode.selectedIndex].textContent, "越舊年度權重越低"],
  ].map(([label, value, detail]) => `
    <div class="stat">
      <span class="stat-label">${label}</span>
      <span class="stat-value">${value}</span>
      <span class="stat-detail">${detail}</span>
    </div>
  `).join("");
}

function renderCountedTeams(summary) {
  if (!els.countedTeams) return;

  const teamCounts = new Map();
  summary.samples.forEach((sample) => {
    const team = sample.team || "Unknown";
    teamCounts.set(team, (teamCounts.get(team) || 0) + 1);
  });

  const teams = [...teamCounts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  if (!teams.length) {
    els.countedTeams.innerHTML = '<div class="empty">沒有車隊被納入目前統計</div>';
    return;
  }

  els.countedTeams.innerHTML = teams.map(([team, count]) => (
    `<span class="team-chip">${escapeHtml(team)} <small>${count} 年</small></span>`
  )).join("");
}

function canvasScale(canvas) {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(rect.width * dpr));
  canvas.height = Math.max(1, Math.round(rect.height * dpr));
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { width: rect.width, height: rect.height };
}

function makeHistogram(values, minX, maxX) {
  const binCount = Math.max(8, Math.min(26, Math.round(Math.sqrt(values.length) * 1.7)));
  const binWidth = (maxX - minX) / binCount || 1;
  const bins = Array.from({ length: binCount }, (_, index) => ({
    x0: minX + index * binWidth,
    x1: minX + (index + 1) * binWidth,
    count: 0,
    density: 0,
  }));
  values.forEach((value) => {
    const index = Math.min(binCount - 1, Math.max(0, Math.floor((value - minX) / binWidth)));
    bins[index].count += 1;
  });
  bins.forEach((bin) => {
    bin.density = bin.count / (values.length * binWidth);
  });
  return bins;
}

function drawChart(summary) {
  const { width, height } = canvasScale(els.chart);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, width, height);

  if (!summary.samples.length) {
    ctx.fillStyle = "#647184";
    ctx.font = "16px sans-serif";
    ctx.fillText("沒有可用資料", 28, 42);
    return;
  }

  const unit = summary.parameter.unit;
  const values = summary.samples.map((sample) => sample.value);
  const sigmaMin = Math.min(summary.observedMin, summary.unweightedMean - summary.unweightedStd, summary.weightedMean - summary.weightedStd);
  const sigmaMax = Math.max(summary.observedMax, summary.unweightedMean + summary.unweightedStd, summary.weightedMean + summary.weightedStd);
  const spread = sigmaMax - sigmaMin || 1;
  const minX = sigmaMin - spread * 0.04;
  const maxX = sigmaMax + spread * 0.04;
  const bins = makeHistogram(values, minX, maxX);
  const curvePoints = 180;
  const densityMax = Math.max(
    ...bins.map((bin) => bin.density),
    ...Array.from({ length: curvePoints + 1 }, (_, index) => {
      const x = minX + (maxX - minX) * (index / curvePoints);
      return Math.max(normalPdf(x, summary.unweightedMean, summary.unweightedStd), normalPdf(x, summary.weightedMean, summary.weightedStd));
    }),
  ) || 1;

  const padding = { top: 34, right: 28, bottom: 64, left: 76 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;
  const xScale = (value) => padding.left + ((value - minX) / (maxX - minX)) * plotW;
  const yScale = (value) => padding.top + plotH - (value / densityMax) * plotH;

  ctx.strokeStyle = "#d8dee7";
  ctx.lineWidth = 1;
  ctx.strokeRect(padding.left, padding.top, plotW, plotH);

  const drawBand = (center, deviation, color) => {
    const x0 = xScale(center - 1 * deviation);
    const x1 = xScale(center + 1 * deviation);
    ctx.fillStyle = color;
    ctx.fillRect(Math.max(padding.left, x0), padding.top, Math.min(padding.left + plotW, x1) - Math.max(padding.left, x0), plotH);
  };
  drawBand(summary.unweightedMean, summary.unweightedStd, "rgba(206, 90, 54, 0.09)");
  drawBand(summary.weightedMean, summary.weightedStd, "rgba(18, 107, 130, 0.11)");

  bins.forEach((bin) => {
    const x = xScale(bin.x0) + 1;
    const y = yScale(bin.density);
    const barW = Math.max(1, xScale(bin.x1) - xScale(bin.x0) - 2);
    ctx.fillStyle = "rgba(52, 73, 94, 0.24)";
    ctx.fillRect(x, y, barW, padding.top + plotH - y);
  });

  function drawCurve(center, deviation, color, dash = []) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.setLineDash(dash);
    ctx.beginPath();
    for (let index = 0; index <= curvePoints; index += 1) {
      const xValue = minX + (maxX - minX) * (index / curvePoints);
      const x = xScale(xValue);
      const y = yScale(normalPdf(xValue, center, deviation));
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.restore();
  }

  drawCurve(summary.unweightedMean, summary.unweightedStd, "#ce5a36", [7, 5]);
  drawCurve(summary.weightedMean, summary.weightedStd, "#126b82");

  function drawMean(value, color, label) {
    const x = xScale(value);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, padding.top);
    ctx.lineTo(x, padding.top + plotH);
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.font = "12px sans-serif";
    ctx.textAlign = x > width - 180 ? "right" : "left";
    ctx.fillText(label, x + (x > width - 180 ? -6 : 6), padding.top + 16);
  }
  drawMean(summary.unweightedMean, "#ce5a36", `未加權 μ ${fmt(summary.unweightedMean)}`);
  drawMean(summary.weightedMean, "#126b82", `加權 μ ${fmt(summary.weightedMean)}`);

  ctx.fillStyle = "#647184";
  ctx.strokeStyle = "#e7ecf2";
  ctx.lineWidth = 1;
  ctx.font = "12px sans-serif";
  ctx.textAlign = "center";
  const tickCount = width < 700 ? 4 : 6;
  for (let i = 0; i <= tickCount; i += 1) {
    const value = minX + (maxX - minX) * (i / tickCount);
    const x = xScale(value);
    ctx.beginPath();
    ctx.moveTo(x, padding.top + plotH);
    ctx.lineTo(x, padding.top + plotH + 6);
    ctx.stroke();
    ctx.fillText(fmt(value), x, padding.top + plotH + 24);
  }

  ctx.save();
  ctx.translate(18, padding.top + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.textAlign = "center";
  ctx.fillText("Density", 0, 0);
  ctx.restore();

  ctx.fillStyle = "#18202a";
  ctx.font = "15px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(`${summary.parameter.name} (${unit})`, padding.left + plotW / 2, height - 18);

  const legend = [
    ["Histogram", "rgba(52, 73, 94, 0.4)", "bar"],
    ["Normal unweighted", "#ce5a36", "dash"],
    ["Normal weighted", "#126b82", "line"],
  ];
  let lx = padding.left;
  legend.forEach(([label, color, kind]) => {
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    if (kind === "bar") ctx.fillRect(lx, 14, 18, 10);
    else {
      ctx.save();
      if (kind === "dash") ctx.setLineDash([7, 5]);
      ctx.beginPath();
      ctx.moveTo(lx, 20);
      ctx.lineTo(lx + 24, 20);
      ctx.stroke();
      ctx.restore();
    }
    ctx.fillStyle = "#18202a";
    ctx.font = "13px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(label, lx + 30, 24);
    lx += ctx.measureText(label).width + 60;
  });
}

function computeAllSummaries() {
  state.summaryRows = state.parameters
    .map(statsForParameter)
    .filter((summary) => summary.count >= 5)
    .sort((a, b) => a.parameter.name.localeCompare(b.parameter.name));
}

function renderStatsTable() {
  if (!state.summaryRows.length) {
    els.statsTable.innerHTML = '<tr><td colspan="10" class="empty">沒有可用統計資料</td></tr>';
    return;
  }

  els.statsTable.innerHTML = state.summaryRows.map((summary) => {
    const unit = summary.parameter.unit;
    const diff = summary.weightedMean - summary.unweightedMean;
    return `
      <tr>
        <td>${summary.parameter.name}</td>
        <td>${unit}</td>
        <td>${summary.count}</td>
        <td>${fmt(summary.unweightedMean)} ± ${fmt(summary.unweightedStd)}</td>
        <td>${fmt(summary.weightedMean)} ± ${fmt(summary.weightedStd)}</td>
        <td>${diff >= 0 ? "+" : ""}${fmt(diff)}</td>
        <td>${rangeText(summary.unweightedMean, summary.unweightedStd, unit)}</td>
        <td>${rangeText(summary.weightedMean, summary.weightedStd, unit)}</td>
        <td>${clippedRangeText(summary.weightedMean, summary.weightedStd, summary.parameter)}</td>
        <td>${fmt(summary.observedMin)} - ${fmt(summary.observedMax)} ${unit}</td>
      </tr>
    `;
  }).join("");
}

function renderAll() {
  const parameter = state.parameters.find((item) => item.name === state.selectedParameter) || state.parameters[0];
  if (!parameter) return;
  state.selectedParameter = parameter.name;
  computeAllSummaries();
  const summary = statsForParameter(parameter);
  renderStatsCards(summary);
  renderCountedTeams(summary);
  drawChart(summary);
  renderStatsTable();
}

function downloadStats() {
  const header = [
    "parameter",
    "unit",
    "sample_count",
    "unweighted_mean",
    "unweighted_std",
    "unweighted_lower_1sigma",
    "unweighted_upper_1sigma",
    "weighted_mean",
    "weighted_std",
    "weighted_lower_1sigma",
    "weighted_upper_1sigma",
    "weighted_recommended_lower",
    "weighted_recommended_upper",
    "mean_difference",
    "observed_min",
    "observed_max",
    "weight_mode",
    "year_weight_mode",
    "weight_basis",
  ];
  const rows = state.summaryRows.map((summary) => {
    const recommended = clippedRange(summary.weightedMean, summary.weightedStd, summary.parameter) || {};
    return [
      summary.parameter.name,
      summary.parameter.unit,
      summary.count,
      summary.unweightedMean,
      summary.unweightedStd,
      summary.unweightedMean - summary.unweightedStd,
      summary.unweightedMean + summary.unweightedStd,
      summary.weightedMean,
      summary.weightedStd,
      summary.weightedMean - summary.weightedStd,
      summary.weightedMean + summary.weightedStd,
      recommended.lower ?? "",
      recommended.upper ?? "",
      summary.weightedMean - summary.unweightedMean,
      summary.observedMin,
      summary.observedMax,
      els.weightMode.value,
      els.yearWeightMode.value,
      "one sample per team-year, annual best place x recency year weight",
    ];
  });
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell ?? "").replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "vehicle_parameter_distribution_stats.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function loadDefaultCSV() {
  try {
    const response = await fetch("../FSG_data_statistics/computed_statistics/fsg_results_vehicle_year_intersection.csv", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    setupAfterLoad(parseCSV(await response.text()));
  } catch (error) {
    els.stats.innerHTML = `<div class="empty">讀取 FSG_data_statistics/computed_statistics/fsg_results_vehicle_year_intersection.csv 失敗：${error.message}</div>`;
  }
}

els.parameterSelect.addEventListener("change", () => {
  state.selectedParameter = els.parameterSelect.value;
  renderAll();
});

[els.eventSelect, els.yearFrom, els.yearTo, els.weightMode, els.yearWeightMode].forEach((el) => {
  el.addEventListener("change", renderAll);
  el.addEventListener("input", renderAll);
});
els.filterTenInchElectric.addEventListener("change", renderAll);

els.csvFile.addEventListener("change", async () => {
  const file = els.csvFile.files[0];
  if (!file) return;
  setupAfterLoad(parseCSV(await file.text()));
});

els.downloadStats.addEventListener("click", downloadStats);
window.addEventListener("resize", () => renderAll());

loadDefaultCSV();

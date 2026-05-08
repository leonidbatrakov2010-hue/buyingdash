import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
from functools import wraps

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
DATA_FILE = Path("reports_data.json")
API_SECRET = os.getenv("API_SECRET", "buyingteam2024")

# ── Storage helpers ────────────────────────────────────────────────────────────
def load_all_reports():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_all_reports(reports):
    DATA_FILE.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

def require_secret(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        secret = request.headers.get("X-API-Secret") or request.args.get("secret")
        if secret != API_SECRET:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ── API endpoints ──────────────────────────────────────────────────────────────
@app.route("/api/report", methods=["POST"])
@require_secret
def receive_report():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    reports = load_all_reports()
    data["received_at"] = datetime.now().isoformat()
    reports.append(data)
    save_all_reports(reports)
    return jsonify({"ok": True, "total": len(reports)})

@app.route("/api/reports", methods=["GET"])
@require_secret
def get_reports():
    days = int(request.args.get("days", 30))
    cutoff = datetime.now() - timedelta(days=days)
    reports = load_all_reports()
    filtered = []
    for r in reports:
        try:
            ts = datetime.fromisoformat(r.get("created_at") or r.get("received_at", ""))
            if ts >= cutoff:
                filtered.append(r)
        except Exception:
            filtered.append(r)
    return jsonify(filtered)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# ── Dashboard HTML ─────────────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buying Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
:root {
  --bg: #080810;
  --s1: #0f0f1a;
  --s2: #161625;
  --s3: #1e1e30;
  --border: #252540;
  --accent: #6c63ff;
  --accent2: #ff6584;
  --accent3: #43e97b;
  --yellow: #f9ca24;
  --text: #e8e8f4;
  --muted: #5a5a7a;
  --font: 'Syne', sans-serif;
  --mono: 'DM Mono', monospace;
}
* { margin:0; padding:0; box-sizing:border-box; }
html { scroll-behavior: smooth; }
body { background:var(--bg); color:var(--text); font-family:var(--font); min-height:100vh; overflow-x:hidden; }

/* Background grid */
body::before {
  content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image: linear-gradient(rgba(108,99,255,0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(108,99,255,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

.wrap { position:relative; z-index:1; max-width:1440px; margin:0 auto; padding:32px 24px; }

/* Header */
header {
  display:flex; align-items:center; justify-content:space-between;
  padding:20px 32px; margin-bottom:40px;
  background:var(--s1); border:1px solid var(--border); border-radius:16px;
  backdrop-filter:blur(10px);
}
.logo { font-size:22px; font-weight:800; letter-spacing:-0.5px; }
.logo span { color:var(--accent); }
.logo-sub { font-family:var(--mono); font-size:11px; color:var(--muted); margin-top:3px; }
.header-right { display:flex; align-items:center; gap:16px; }
.live-dot { width:8px; height:8px; background:var(--accent3); border-radius:50%; animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.3)} }
.last-update { font-family:var(--mono); font-size:11px; color:var(--muted); }

/* Period filter */
.period-bar {
  display:flex; gap:8px; margin-bottom:32px; flex-wrap:wrap; align-items:center;
}
.period-btn {
  font-family:var(--mono); font-size:12px; padding:8px 18px;
  background:var(--s1); border:1px solid var(--border); color:var(--muted);
  border-radius:8px; cursor:pointer; transition:all 0.2s;
}
.period-btn:hover { border-color:var(--accent); color:var(--text); }
.period-btn.active { background:var(--accent); border-color:var(--accent); color:#fff; }
.refresh-btn {
  margin-left:auto; font-family:var(--mono); font-size:12px; padding:8px 18px;
  background:transparent; border:1px solid var(--border); color:var(--muted);
  border-radius:8px; cursor:pointer; transition:all 0.2s;
}
.refresh-btn:hover { border-color:var(--accent3); color:var(--accent3); }

/* KPI strip */
.kpi-strip { display:grid; grid-template-columns:repeat(6,1fr); gap:12px; margin-bottom:32px; }
.kpi-card {
  background:var(--s1); border:1px solid var(--border); border-radius:12px;
  padding:18px 20px; position:relative; overflow:hidden;
  animation: fadeUp 0.4s ease both;
}
.kpi-card::after {
  content:''; position:absolute; bottom:0; left:0; right:0; height:2px;
  background:var(--accent-color, var(--accent));
}
.kpi-label { font-family:var(--mono); font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; }
.kpi-value { font-size:28px; font-weight:800; line-height:1; }
.kpi-sub { font-family:var(--mono); font-size:10px; color:var(--muted); margin-top:6px; }

/* Charts row */
.charts-row { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:32px; }
.chart-card {
  background:var(--s1); border:1px solid var(--border); border-radius:16px; padding:24px;
  animation: fadeUp 0.5s ease both;
}
.chart-title { font-size:13px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:20px; }
.chart-wrap { position:relative; height:180px; }

/* Buyer cards */
.section-header {
  display:flex; align-items:center; gap:16px; margin-bottom:20px; margin-top:36px;
}
.section-title { font-size:13px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:2px; }
.section-line { flex:1; height:1px; background:var(--border); }
.section-count { font-family:var(--mono); font-size:11px; color:var(--muted); }

.buyers-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:16px; margin-bottom:8px; }
.buyer-card {
  background:var(--s1); border:1px solid var(--border); border-radius:16px; padding:24px;
  transition:border-color 0.2s, transform 0.2s;
  animation: fadeUp 0.4s ease both;
}
.buyer-card:hover { border-color:var(--accent); transform:translateY(-2px); }
.buyer-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.buyer-name { font-size:18px; font-weight:800; }
.buyer-score {
  font-family:var(--mono); font-size:12px; padding:4px 10px;
  border-radius:6px; font-weight:600;
}
.score-good { background:rgba(67,233,123,0.15); color:var(--accent3); border:1px solid rgba(67,233,123,0.3); }
.score-ok   { background:rgba(249,202,36,0.15); color:var(--yellow); border:1px solid rgba(249,202,36,0.3); }
.score-bad  { background:rgba(255,101,132,0.15); color:var(--accent2); border:1px solid rgba(255,101,132,0.3); }
.buyer-stats { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:16px; }
.buyer-stat { background:var(--s2); border-radius:8px; padding:10px 12px; text-align:center; }
.buyer-stat-val { font-size:16px; font-weight:700; }
.buyer-stat-label { font-family:var(--mono); font-size:9px; color:var(--muted); margin-top:3px; }
.buyer-channels { border-top:1px solid var(--border); padding-top:12px; }
.buyer-channel-row {
  display:flex; align-items:center; justify-content:space-between;
  padding:6px 0; font-family:var(--mono); font-size:11px;
  border-bottom:1px solid rgba(255,255,255,0.04);
}
.buyer-channel-row:last-child { border-bottom:none; }
.ch-name { color:var(--text); }
.ch-kpi { font-weight:600; }
.kpi-g { color:var(--accent3); }
.kpi-y { color:var(--yellow); }
.kpi-r { color:var(--accent2); }

/* Projects table */
.table-wrap {
  background:var(--s1); border:1px solid var(--border); border-radius:16px;
  overflow:hidden; overflow-x:auto; margin-bottom:8px;
  animation: fadeUp 0.5s ease both;
}
.table-filters { display:flex; gap:8px; padding:16px 20px; border-bottom:1px solid var(--border); flex-wrap:wrap; }
.tfilter {
  font-family:var(--mono); font-size:11px; padding:5px 12px;
  background:var(--s2); border:1px solid var(--border); color:var(--muted);
  border-radius:6px; cursor:pointer; transition:all 0.15s;
}
.tfilter:hover { border-color:var(--accent); color:var(--text); }
.tfilter.active { background:var(--accent); border-color:var(--accent); color:#fff; }
table { width:100%; border-collapse:collapse; }
thead th {
  background:var(--s2); padding:12px 16px; text-align:left;
  font-family:var(--mono); font-size:10px; text-transform:uppercase;
  letter-spacing:1px; color:var(--muted); white-space:nowrap;
  border-bottom:1px solid var(--border); cursor:pointer;
}
thead th:hover { color:var(--text); }
tbody tr { border-bottom:1px solid rgba(255,255,255,0.04); transition:background 0.15s; }
tbody tr:hover { background:var(--s2); }
tbody tr:last-child { border-bottom:none; }
td { padding:12px 16px; font-family:var(--mono); font-size:12px; vertical-align:middle; }
.num { text-align:right; }
.tag {
  display:inline-block; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:600;
  background:var(--s2); border:1px solid var(--border);
}
.tag-buyer { background:rgba(108,99,255,0.15); border-color:rgba(108,99,255,0.3); color:#a89ff9; }
.tag-t1 { background:rgba(108,99,255,0.15); border-color:rgba(108,99,255,0.3); color:#a89ff9; }
.tag-t2 { background:rgba(249,202,36,0.15); border-color:rgba(249,202,36,0.3); color:var(--yellow); }
.tag-t3 { background:rgba(67,233,123,0.15); border-color:rgba(67,233,123,0.3); color:var(--accent3); }
.tag-ru { background:rgba(255,101,132,0.15); border-color:rgba(255,101,132,0.3); color:var(--accent2); }
.verdict {
  display:inline-block; padding:3px 10px; border-radius:4px; font-size:10px; font-weight:700;
  text-transform:uppercase; letter-spacing:0.5px;
}
.v-scale { background:rgba(67,233,123,0.2); color:var(--accent3); }
.v-keep  { background:rgba(249,202,36,0.2); color:var(--yellow); }
.v-cut   { background:rgba(255,101,132,0.2); color:var(--accent2); }
.v-test  { background:rgba(108,99,255,0.2); color:#a89ff9; }
.v-pause { background:rgba(90,90,122,0.3); color:var(--muted); }
.date-cell { color:var(--muted); font-size:10px; }

/* Empty state */
.empty { text-align:center; padding:80px 20px; color:var(--muted); }
.empty-icon { font-size:48px; margin-bottom:16px; }
.empty-title { font-size:20px; font-weight:700; margin-bottom:8px; }
.empty-sub { font-family:var(--mono); font-size:12px; }

/* Animations */
@keyframes fadeUp {
  from { opacity:0; transform:translateY(16px); }
  to   { opacity:1; transform:translateY(0); }
}
.kpi-card:nth-child(1){animation-delay:0.05s}
.kpi-card:nth-child(2){animation-delay:0.1s}
.kpi-card:nth-child(3){animation-delay:0.15s}
.kpi-card:nth-child(4){animation-delay:0.2s}
.kpi-card:nth-child(5){animation-delay:0.25s}
.kpi-card:nth-child(6){animation-delay:0.3s}

/* Loading */
.loading { text-align:center; padding:60px; color:var(--muted); font-family:var(--mono); font-size:13px; }
.spinner { width:32px; height:32px; border:2px solid var(--border); border-top-color:var(--accent); border-radius:50%; animation:spin 0.8s linear infinite; margin:0 auto 16px; }
@keyframes spin { to { transform:rotate(360deg); } }

@media(max-width:768px) {
  .kpi-strip { grid-template-columns:repeat(3,1fr); }
  .charts-row { grid-template-columns:1fr; }
  .wrap { padding:16px; }
}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div>
      <div class="logo">BUYING <span>DASH</span></div>
      <div class="logo-sub">Арбитражная команда · Weekly Report System</div>
    </div>
    <div class="header-right">
      <div class="live-dot"></div>
      <div class="last-update" id="lastUpdate">Загрузка...</div>
    </div>
  </header>

  <div class="period-bar">
    <button class="period-btn" onclick="setPeriod(1)">Сегодня</button>
    <button class="period-btn active" onclick="setPeriod(7)">7 дней</button>
    <button class="period-btn" onclick="setPeriod(14)">14 дней</button>
    <button class="period-btn" onclick="setPeriod(30)">30 дней</button>
    <button class="refresh-btn" onclick="loadData()">↻ Обновить</button>
  </div>

  <div id="mainContent">
    <div class="loading"><div class="spinner"></div>Загружаем данные...</div>
  </div>

</div>

<script>
let currentDays = 7;
let allData = [];
let charts = {};

const SECRET = "{{ secret }}";

function setPeriod(days) {
  currentDays = days;
  document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  loadData();
}

async function loadData() {
  try {
    const res = await fetch(`/api/reports?days=${currentDays}&secret=${SECRET}`);
    allData = await res.json();
    render(allData);
    document.getElementById('lastUpdate').textContent = 'Обновлено: ' + new Date().toLocaleTimeString('ru');
  } catch(e) {
    document.getElementById('mainContent').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-title">Ошибка загрузки</div><div class="empty-sub">Проверьте подключение</div></div>';
  }
}

function parseNum(v) {
  if (!v) return null;
  const n = parseFloat(String(v).replace(/[^0-9.]/g, ''));
  return isNaN(n) ? null : n;
}

function safeDiv(a, b) { return (a && b && b !== 0) ? a / b : null; }
function fmtMoney(v) { return v == null ? '—' : (Number.isInteger(v) ? '$'+v : '$'+v.toFixed(2)); }
function fmtNum(v) { return v == null ? '—' : String(Math.round(v)); }

function getKpiClass(tier, cpa) {
  if (!cpa || !tier) return '';
  const rules = { 'ТИР1':[300,600], 'ТИР2':[150,300], 'ТИР3':[80,150], 'РУ':[300,700] };
  const r = rules[tier];
  if (!r) return '';
  if (cpa <= r[0]) return 'kpi-g';
  if (cpa <= r[1]) return 'kpi-y';
  return 'kpi-r';
}

function getKpiLabel(tier, cpa) {
  if (!cpa || !tier) return '—';
  const rules = { 'ТИР1':[300,600], 'ТИР2':[150,300], 'ТИР3':[80,150], 'РУ':[300,700] };
  const r = rules[tier];
  if (!r) return '—';
  if (cpa <= r[0]) return '✓ ОТЛИЧНО';
  if (cpa <= r[1]) return '~ ДОПУСТИМО';
  return '✗ ДОРОГО';
}

function extractProjects(reports) {
  const projects = [];
  for (const r of reports) {
    const buyer = r.buyer_name || '?';
    const state = r.state || {};
    const items = state.reports || r.channels || [];
    for (const item of items) {
      const a = item.answers || {};
      const spend = parseNum(a.spend);
      const ftd = parseNum(a.ftd);
      const dialogs = parseNum(a.dialogs);
      const regs = parseNum(a.regs);
      const cpa = safeDiv(spend, ftd);
      projects.push({
        buyer, date: (r.created_at||'').slice(0,10),
        channel: item.channel||'?',
        source: item.source||'?',
        crm: item.crm||'?',
        tier: item.tier||'?',
        spend, ftd, dialogs, regs, cpa,
        decision: a.decision||'—',
        verdict: r.ai_verdict || extractVerdict(r.ai_report||''),
        quality: extractQuality(r.ai_report||''),
      });
    }
    // fallback: if no state.reports, try to parse from raw_report text
  }
  return projects;
}

function extractVerdict(text) {
  if (!text) return '';
  if (text.includes('МАСШТАБИРОВАТЬ')) return 'МАСШТАБИРОВАТЬ';
  if (text.includes('СНИЗИТЬ БЮДЖЕТ')) return 'СНИЗИТЬ БЮДЖЕТ';
  if (text.includes('ТЕСТОВЫЙ')) return 'ТЕСТОВЫЙ';
  if (text.includes('ПАУЗА') || text.includes('СТОП')) return 'ПАУЗА';
  if (text.includes('ОСТАВИТЬ')) return 'ОСТАВИТЬ';
  return '';
}

function extractQuality(text) {
  if (!text) return null;
  const m = text.match(/Оценка[:\s]+(\d+)\s*\/\s*10/i);
  return m ? parseInt(m[1]) : null;
}

function verdictClass(v) {
  if (!v) return '';
  if (v.includes('МАСШ')) return 'v-scale';
  if (v.includes('СНИЗИТЬ')) return 'v-cut';
  if (v.includes('ТЕСТ')) return 'v-test';
  if (v.includes('ПАУЗА') || v.includes('СТОП')) return 'v-pause';
  return 'v-keep';
}

function tierClass(t) {
  const map = {'ТИР1':'tag-t1','ТИР2':'tag-t2','ТИР3':'tag-t3','РУ':'tag-ru'};
  return map[t] || '';
}

function render(reports) {
  if (!reports || reports.length === 0) {
    document.getElementById('mainContent').innerHTML = `
      <div class="empty">
        <div class="empty-icon">📭</div>
        <div class="empty-title">Отчетов пока нет</div>
        <div class="empty-sub">Отчеты появятся после того как баеры заполнят их в Telegram-боте</div>
      </div>`;
    return;
  }

  const projects = extractProjects(reports);
  const buyers = [...new Set(reports.map(r => r.buyer_name).filter(Boolean))];
  const totalSpend = projects.reduce((s,p) => s + (p.spend||0), 0);
  const totalFtd = projects.reduce((s,p) => s + (p.ftd||0), 0);
  const avgCpa = safeDiv(totalSpend, totalFtd);
  const totalDialogs = projects.reduce((s,p) => s + (p.dialogs||0), 0);

  // Destroy old charts
  Object.values(charts).forEach(c => c.destroy());
  charts = {};

  // Spend by buyer
  const spendByBuyer = {};
  for (const p of projects) {
    spendByBuyer[p.buyer] = (spendByBuyer[p.buyer]||0) + (p.spend||0);
  }

  // FTD by channel
  const ftdByChannel = {};
  for (const p of projects) {
    ftdByChannel[p.channel] = (ftdByChannel[p.channel]||0) + (p.ftd||0);
  }

  // CPA by tier
  const tierData = {};
  for (const p of projects) {
    if (!tierData[p.tier]) tierData[p.tier] = {spend:0, ftd:0};
    tierData[p.tier].spend += (p.spend||0);
    tierData[p.tier].ftd += (p.ftd||0);
  }

  // Build buyer cards
  let buyerCardsHtml = '';
  for (const buyer of buyers) {
    const bp = projects.filter(p => p.buyer === buyer);
    const bSpend = bp.reduce((s,p)=>s+(p.spend||0),0);
    const bFtd = bp.reduce((s,p)=>s+(p.ftd||0),0);
    const bCpa = safeDiv(bSpend, bFtd);
    const bReports = reports.filter(r => r.buyer_name === buyer);
    const qualities = bReports.map(r => extractQuality(r.ai_report||'')).filter(q=>q);
    const avgQ = qualities.length ? Math.round(qualities.reduce((a,b)=>a+b,0)/qualities.length) : null;
    const scoreClass = avgQ == null ? '' : avgQ >= 7 ? 'score-good' : avgQ >= 5 ? 'score-ok' : 'score-bad';

    let channelsHtml = '';
    for (const p of bp) {
      const kc = getKpiClass(p.tier, p.cpa);
      const kl = getKpiLabel(p.tier, p.cpa);
      channelsHtml += `
        <div class="buyer-channel-row">
          <span class="ch-name">${p.channel} / ${p.source}</span>
          <span class="ch-kpi ${kc}">${kl} ${p.cpa ? fmtMoney(p.cpa) : ''}</span>
        </div>`;
    }

    buyerCardsHtml += `
      <div class="buyer-card">
        <div class="buyer-header">
          <div class="buyer-name">${buyer}</div>
          ${avgQ ? `<span class="buyer-score ${scoreClass}">${avgQ}/10</span>` : ''}
        </div>
        <div class="buyer-stats">
          <div class="buyer-stat">
            <div class="buyer-stat-val">${fmtMoney(bSpend)}</div>
            <div class="buyer-stat-label">Spend</div>
          </div>
          <div class="buyer-stat">
            <div class="buyer-stat-val">${fmtNum(bFtd)}</div>
            <div class="buyer-stat-label">FTD</div>
          </div>
          <div class="buyer-stat">
            <div class="buyer-stat-val">${fmtMoney(bCpa)}</div>
            <div class="buyer-stat-label">CPA FTD</div>
          </div>
        </div>
        <div class="buyer-channels">${channelsHtml || '<div style="color:var(--muted);font-family:var(--mono);font-size:11px;padding:8px 0">Нет проектов</div>'}</div>
      </div>`;
  }

  // Build table rows
  let tableRows = '';
  for (const p of projects) {
    const kc = getKpiClass(p.tier, p.cpa);
    const kl = getKpiLabel(p.tier, p.cpa);
    const vc = verdictClass(p.verdict);
    tableRows += `
      <tr data-buyer="${p.buyer}">
        <td><span class="tag tag-buyer">${p.buyer}</span></td>
        <td>${p.channel}</td>
        <td><span class="tag">${p.source}</span></td>
        <td><span class="tag">${p.crm}</span></td>
        <td><span class="tag ${tierClass(p.tier)}">${p.tier}</span></td>
        <td class="num">${p.spend ? fmtMoney(p.spend) : '—'}</td>
        <td class="num">${fmtNum(p.ftd)}</td>
        <td class="num">${fmtMoney(p.cpa)}</td>
        <td><span class="${kc}">${kl}</span></td>
        ${p.verdict ? `<td><span class="verdict ${vc}">${p.verdict}</span></td>` : '<td>—</td>'}
        <td class="date-cell">${p.date}</td>
      </tr>`;
  }

  // Filter buttons
  const filterBtns = ['Все', ...buyers].map((b,i) =>
    `<button class="tfilter ${i===0?'active':''}" onclick="filterRows('${b}',this)">${b}</button>`
  ).join('');

  document.getElementById('mainContent').innerHTML = `
    <div class="kpi-strip">
      <div class="kpi-card" style="--accent-color:var(--accent)">
        <div class="kpi-label">Отчетов</div>
        <div class="kpi-value">${reports.length}</div>
        <div class="kpi-sub">за ${currentDays} дней</div>
      </div>
      <div class="kpi-card" style="--accent-color:var(--accent2)">
        <div class="kpi-label">Проектов</div>
        <div class="kpi-value">${projects.length}</div>
        <div class="kpi-sub">каналов заполнено</div>
      </div>
      <div class="kpi-card" style="--accent-color:var(--accent3)">
        <div class="kpi-label">Баеров</div>
        <div class="kpi-value">${buyers.length}</div>
        <div class="kpi-sub">${buyers.join(', ')}</div>
      </div>
      <div class="kpi-card" style="--accent-color:var(--yellow)">
        <div class="kpi-label">Total Spend</div>
        <div class="kpi-value">${fmtMoney(totalSpend)}</div>
        <div class="kpi-sub">суммарно</div>
      </div>
      <div class="kpi-card" style="--accent-color:var(--accent3)">
        <div class="kpi-label">Total FTD</div>
        <div class="kpi-value">${fmtNum(totalFtd)}</div>
        <div class="kpi-sub">конверсий</div>
      </div>
      <div class="kpi-card" style="--accent-color:var(--accent2)">
        <div class="kpi-label">Avg CPA FTD</div>
        <div class="kpi-value">${fmtMoney(avgCpa)}</div>
        <div class="kpi-sub">средняя цена</div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">Spend по баерам</div>
        <div class="chart-wrap"><canvas id="chartBuyer"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">FTD по каналам</div>
        <div class="chart-wrap"><canvas id="chartChannel"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">CPA FTD по ТИРам</div>
        <div class="chart-wrap"><canvas id="chartTier"></canvas></div>
      </div>
    </div>

    <div class="section-header">
      <div class="section-title">По баерам</div>
      <div class="section-line"></div>
      <div class="section-count">${buyers.length} баеров</div>
    </div>
    <div class="buyers-grid">${buyerCardsHtml}</div>

    <div class="section-header">
      <div class="section-title">Все проекты</div>
      <div class="section-line"></div>
      <div class="section-count">${projects.length} проектов</div>
    </div>
    <div class="table-wrap">
      <div class="table-filters">${filterBtns}</div>
      <table>
        <thead>
          <tr>
            <th>Баер</th><th>Канал</th><th>Источник</th><th>CRM</th><th>ТИР</th>
            <th>Spend</th><th>FTD</th><th>CPA FTD</th><th>KPI</th><th>AI-вердикт</th><th>Дата</th>
          </tr>
        </thead>
        <tbody id="tableBody">${tableRows}</tbody>
      </table>
    </div>
  `;

  // Charts
  const chartDefaults = {
    responsive:true, maintainAspectRatio:false,
    plugins:{ legend:{ display:false } },
  };
  const gridColor = 'rgba(255,255,255,0.05)';
  const tickColor = '#5a5a7a';

  charts.buyer = new Chart(document.getElementById('chartBuyer'), {
    type:'bar',
    data:{
      labels: Object.keys(spendByBuyer),
      datasets:[{ data: Object.values(spendByBuyer), backgroundColor:'rgba(108,99,255,0.7)', borderRadius:6 }]
    },
    options:{...chartDefaults, scales:{
      x:{ticks:{color:tickColor,font:{family:'DM Mono',size:10}},grid:{color:gridColor}},
      y:{ticks:{color:tickColor,font:{family:'DM Mono',size:10}},grid:{color:gridColor}}
    }}
  });

  charts.channel = new Chart(document.getElementById('chartChannel'), {
    type:'doughnut',
    data:{
      labels: Object.keys(ftdByChannel),
      datasets:[{ data: Object.values(ftdByChannel),
        backgroundColor:['rgba(67,233,123,0.8)','rgba(108,99,255,0.8)','rgba(255,101,132,0.8)','rgba(249,202,36,0.8)','rgba(100,200,255,0.8)','rgba(255,160,100,0.8)'],
        borderWidth:0 }]
    },
    options:{...chartDefaults, plugins:{legend:{display:true, position:'right', labels:{color:tickColor,font:{family:'DM Mono',size:10},boxWidth:10}}}}
  });

  const tierLabels = Object.keys(tierData);
  const tierCpas = tierLabels.map(t => safeDiv(tierData[t].spend, tierData[t].ftd) || 0);
  charts.tier = new Chart(document.getElementById('chartTier'), {
    type:'bar',
    data:{
      labels: tierLabels,
      datasets:[{ data: tierCpas, backgroundColor:'rgba(255,101,132,0.7)', borderRadius:6 }]
    },
    options:{...chartDefaults, scales:{
      x:{ticks:{color:tickColor,font:{family:'DM Mono',size:10}},grid:{color:gridColor}},
      y:{ticks:{color:tickColor,font:{family:'DM Mono',size:10},callback:v=>'$'+v},grid:{color:gridColor}}
    }}
  });
}

function filterRows(buyer, btn) {
  document.querySelectorAll('.tfilter').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('#tableBody tr').forEach(row => {
    row.style.display = (buyer==='Все' || row.dataset.buyer===buyer) ? '' : 'none';
  });
}

// Auto-refresh every 60 seconds
setInterval(loadData, 60000);
loadData();
</script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    secret = API_SECRET
    return render_template_string(DASHBOARD_HTML, secret=secret)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

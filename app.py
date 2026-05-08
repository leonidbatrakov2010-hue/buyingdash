import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
from functools import wraps

app = Flask(__name__)

DATA_FILE = Path("reports_data.json")
API_SECRET = os.getenv("API_SECRET", "buyingteam2024")

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

HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Buying Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#07070f;--s1:#0e0e1c;--s2:#151528;--s3:#1c1c35;--border:#222240;--accent:#6c63ff;--accent2:#ff6584;--green:#43e97b;--yellow:#f9ca24;--red:#ff6b6b;--blue:#4ecdc4;--text:#e8e8f4;--muted:#5a5a7a;--font:'Syne',sans-serif;--mono:'DM Mono',monospace}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;display:flex;flex-direction:column}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background-image:linear-gradient(rgba(108,99,255,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(108,99,255,.02) 1px,transparent 1px);background-size:48px 48px}
.header{position:sticky;top:0;z-index:100;background:rgba(7,7,15,.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);padding:0 28px;height:60px;display:flex;align-items:center;justify-content:space-between}
.logo{font-size:19px;font-weight:800;letter-spacing:-.5px}.logo span{color:var(--accent)}
.logo-sub{font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:2px}
.live{display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:11px;color:var(--muted)}
.live-dot{width:7px;height:7px;background:var(--green);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.btn{font-family:var(--mono);font-size:11px;padding:7px 16px;background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:8px;cursor:pointer;transition:all .2s}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.layout{display:flex;flex:1;position:relative;z-index:1}
.sidebar{width:250px;flex-shrink:0;background:var(--s1);border-right:1px solid var(--border);padding:20px 14px;position:sticky;top:60px;height:calc(100vh - 60px);overflow-y:auto}
.period-row{display:flex;gap:5px;margin-bottom:22px}
.pBtn{flex:1;font-family:var(--mono);font-size:11px;padding:6px 0;background:var(--s2);border:1px solid var(--border);color:var(--muted);border-radius:7px;cursor:pointer;transition:all .15s;text-align:center}
.pBtn:hover{border-color:var(--accent);color:var(--text)}
.pBtn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.sb-section{margin-bottom:22px}
.sb-label{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:8px;padding:0 6px}
.fBtn{display:block;width:100%;text-align:left;font-family:var(--mono);font-size:12px;padding:7px 10px;background:transparent;border:1px solid transparent;color:var(--muted);border-radius:7px;cursor:pointer;transition:all .15s;margin-bottom:3px}
.fBtn:hover{background:var(--s2);color:var(--text)}
.fBtn.active{background:rgba(108,99,255,.15);border-color:rgba(108,99,255,.35);color:#a89ff9}
.fCnt{float:right;background:var(--s3);border-radius:3px;padding:1px 5px;font-size:10px;color:var(--muted)}
.main{flex:1;padding:24px 28px;overflow-x:hidden}
.kpi-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:22px}
.kpi-card{background:var(--s1);border:1px solid var(--border);border-radius:11px;padding:14px 18px;position:relative;overflow:hidden}
.kpi-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;background:var(--c,var(--accent))}
.kpi-l{font-family:var(--mono);font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:7px}
.kpi-v{font-size:24px;font-weight:800;line-height:1}
.kpi-s{font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:4px}
.flags{background:rgba(255,107,107,.07);border:1px solid rgba(255,107,107,.22);border-radius:11px;padding:14px 18px;margin-bottom:20px;display:none}
.flags.on{display:block}
.flags-t{font-family:var(--mono);font-size:10px;color:var(--red);text-transform:uppercase;letter-spacing:1px;margin-bottom:9px}
.flag-i{font-family:var(--mono);font-size:12px;color:var(--text);padding:4px 0;border-bottom:1px solid rgba(255,107,107,.1)}
.flag-i:last-child{border-bottom:none}
.sec-hdr{display:flex;align-items:center;gap:10px;margin-bottom:14px;margin-top:6px}
.sec-t{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:2px;white-space:nowrap}
.sec-l{flex:1;height:1px;background:var(--border)}
.sec-c{font-family:var(--mono);font-size:11px;color:var(--muted);white-space:nowrap}
.cards{display:flex;flex-direction:column;gap:14px}
.card{background:var(--s1);border:1px solid var(--border);border-radius:15px;overflow:hidden;transition:border-color .2s}
.card:hover{border-color:rgba(108,99,255,.4)}
.card-hdr{display:flex;align-items:center;gap:14px;padding:18px 22px;cursor:pointer;user-select:none}
.verdict{flex-shrink:0;font-family:var(--mono);font-size:11px;font-weight:700;padding:4px 11px;border-radius:6px;text-transform:uppercase;letter-spacing:.5px}
.v-scale{background:rgba(67,233,123,.2);color:var(--green)}
.v-keep{background:rgba(249,202,36,.2);color:var(--yellow)}
.v-cut{background:rgba(255,107,107,.2);color:var(--red)}
.v-test{background:rgba(108,99,255,.2);color:#a89ff9}
.v-pause{background:rgba(90,90,122,.2);color:var(--muted)}
.card-meta{flex:1}
.card-name{font-size:15px;font-weight:700;margin-bottom:4px}
.card-tags{display:flex;gap:5px;flex-wrap:wrap}
.tag{font-family:var(--mono);font-size:10px;padding:2px 7px;border-radius:4px;background:var(--s2);border:1px solid var(--border)}
.tb{background:rgba(108,99,255,.13);border-color:rgba(108,99,255,.28);color:#a89ff9}
.t1{background:rgba(108,99,255,.1);border-color:rgba(108,99,255,.22);color:#a89ff9}
.t2{background:rgba(249,202,36,.1);border-color:rgba(249,202,36,.22);color:var(--yellow)}
.t3{background:rgba(67,233,123,.1);border-color:rgba(67,233,123,.22);color:var(--green)}
.tru{background:rgba(255,101,132,.1);border-color:rgba(255,101,132,.22);color:var(--accent2)}
.card-nums{display:flex;gap:20px;flex-shrink:0}
.cn{text-align:right}
.cn-v{font-size:17px;font-weight:700;line-height:1}
.cn-l{font-family:var(--mono);font-size:9px;color:var(--muted);margin-top:2px}
.kg{color:var(--green)}.ky{color:var(--yellow)}.kr{color:var(--red)}
.card-arr{color:var(--muted);font-size:16px;flex-shrink:0;transition:transform .2s}
.card-arr.open{transform:rotate(180deg)}
.card-body{display:none;border-top:1px solid var(--border)}
.card-body.open{display:block}
.card-inner{padding:22px;display:grid;grid-template-columns:1fr 1fr;gap:20px}
.met-row{grid-column:1/-1;display:grid;grid-template-columns:repeat(6,1fr);gap:8px}
.met{background:var(--s2);border-radius:9px;padding:11px 13px;text-align:center}
.met-v{font-size:16px;font-weight:700}
.met-l{font-family:var(--mono);font-size:9px;color:var(--muted);margin-top:3px}
.ib{}
.ib-t{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid var(--border)}
.ib-c{font-family:var(--mono);font-size:12px;line-height:1.7;color:var(--text)}
.ib-c strong{color:var(--accent)}
.dec{grid-column:1/-1;background:rgba(108,99,255,.07);border:1px solid rgba(108,99,255,.18);border-radius:11px;padding:14px 18px}
.dec-t{font-family:var(--mono);font-size:9px;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
.dec-items{display:flex;flex-wrap:wrap;gap:7px}
.dec-i{font-family:var(--mono);font-size:11px;padding:4px 11px;background:rgba(108,99,255,.13);border:1px solid rgba(108,99,255,.25);border-radius:5px;color:#c0b8ff}
.ai-box{grid-column:1/-1;background:var(--s2);border-radius:11px;padding:18px 22px}
.ai-box-t{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:13px;display:flex;align-items:center;gap:7px}
.ai-box-c{font-family:var(--mono);font-size:11px;line-height:1.8;color:#b0b0cc;white-space:pre-wrap;max-height:380px;overflow-y:auto}
.empty{text-align:center;padding:80px 20px;color:var(--muted)}
.empty-i{font-size:50px;margin-bottom:14px}
.empty-t{font-size:20px;font-weight:700;margin-bottom:7px}
.empty-s{font-family:var(--mono);font-size:12px;line-height:1.6}
::-webkit-scrollbar{width:3px}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
@media(max-width:860px){.sidebar{display:none}.kpi-strip{grid-template-columns:repeat(3,1fr)}.card-inner{grid-template-columns:1fr}.met-row{grid-template-columns:repeat(3,1fr)}}
</style>
</head>
<body>
<div class="header">
  <div><div class="logo">BUYING <span>DASH</span></div><div class="logo-sub">Арбитражная команда · Weekly Report System</div></div>
  <div style="display:flex;align-items:center;gap:14px">
    <div class="live"><div class="live-dot"></div><span id="upd">Загрузка...</span></div>
    <button class="btn" onclick="loadData()">↻ Обновить</button>
  </div>
</div>
<div class="layout">
  <div class="sidebar">
    <div class="period-row">
      <button class="pBtn" onclick="setPeriod(1,this)">1д</button>
      <button class="pBtn active" onclick="setPeriod(7,this)">7д</button>
      <button class="pBtn" onclick="setPeriod(14,this)">14д</button>
      <button class="pBtn" onclick="setPeriod(30,this)">30д</button>
    </div>
    <div class="sb-section"><div class="sb-label">Баер</div><div id="fBuyer"></div></div>
    <div class="sb-section"><div class="sb-label">Канал</div><div id="fChannel"></div></div>
    <div class="sb-section"><div class="sb-label">Источник</div><div id="fSource"></div></div>
    <div class="sb-section"><div class="sb-label">ТИР</div><div id="fTier"></div></div>
  </div>
  <div class="main" id="main"><div class="empty"><div class="empty-i">⏳</div><div class="empty-t">Загрузка...</div></div></div>
</div>
<script>
const SECRET="{{secret}}";
let days=7,projects=[],filters={buyer:'all',channel:'all',source:'all',tier:'all'};

function pn(v){if(!v)return null;const n=parseFloat(String(v).replace(/[^0-9.,]/g,'').replace(',','.'));return isNaN(n)?null:n}
function sd(a,b){return(a&&b&&b!==0)?a/b:null}
function fm(v){return v==null?'—':(v>=1000?'$'+Math.round(v).toLocaleString('ru'):'$'+v.toFixed(2))}
function fn(v){return v==null?'—':Math.round(v).toString()}
function fp(v){return v==null?'—':v.toFixed(1)+'%'}
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

function kpiStatus(tier,cpa){
  if(!cpa||!tier)return null;
  const r={ТИР1:[300,600],ТИР2:[150,300],ТИР3:[80,150],РУ:[300,700]}[tier];
  if(!r)return null;
  if(cpa<=r[0])return{cls:'kg',lbl:'✓ Отлично'};
  if(cpa<=r[1])return{cls:'ky',lbl:'~ Допустимо'};
  return{cls:'kr',lbl:'✗ Дорого'};
}

function vClass(t){
  if(!t)return 'v-keep';
  if(t.includes('МАСШТАБ'))return 'v-scale';
  if(t.includes('СНИЗИТЬ'))return 'v-cut';
  if(t.includes('ТЕСТОВ')||t.includes('ТЕСТОВЫЙ'))return 'v-test';
  if(t.includes('ПАУЗА')||t.includes('СТОП'))return 'v-pause';
  return 'v-keep';
}

function tClass(t){return{ТИР1:'t1',ТИР2:'t2',ТИР3:'t3',РУ:'tru'}[t]||''}

function extractVerdict(txt){
  if(!txt)return'';
  const m=txt.match(/AI-вердикт[:\s]+([^\n]+)/);
  return m?m[1].trim():'';
}
function extractQuality(txt){
  if(!txt)return null;
  const m=txt.match(/Оценка[:\s]+(\d+)\s*\/\s*10/i);
  return m?parseInt(m[1]):null;
}
function extractFlags(txt){
  if(!txt)return[];
  const m=txt.match(/ПРОТИВОРЕЧИЯ[^\n]*\n([\s\S]*?)(?:━━━|ОЦЕНКА|$)/);
  if(!m)return[];
  const sec=m[1];
  if(sec.includes('Явных противоречий нет'))return[];
  return sec.split('\n').filter(l=>l.trim().startsWith('-')).map(l=>l.replace(/^-\s*/,'').trim()).filter(Boolean);
}
function extractDecisions(txt){
  if(!txt)return[];
  const m=txt.match(/РЕШЕНИЯ РУКОВОДИТЕЛЯ[^\n]*\n([\s\S]*?)(?:━━━|$)/);
  if(!m)return[];
  return m[1].split('\n').filter(l=>l.trim().startsWith('-')).map(l=>l.replace(/^-\s*/,'').trim()).filter(Boolean);
}

function parseReports(reports){
  const out=[];
  for(const r of reports){
    const buyer=r.buyer_name||'?';
    const ai=r.ai_report||'';
    const verdict=extractVerdict(ai);
    const quality=extractQuality(ai);
    const flags=extractFlags(ai);
    const decisions=extractDecisions(ai);
    const state=r.state||{};
    const items=state.reports||r.channels||[];
    for(const item of items){
      const a=item.answers||{};
      const spend=pn(a.spend),ftd=pn(a.ftd),dialogs=pn(a.dialogs),regs=pn(a.regs);
      const cpa=sd(spend,ftd),cpl=sd(spend,dialogs),cpr=sd(spend,regs);
      const d2r=sd(regs,dialogs),r2f=sd(ftd,regs);
      out.push({buyer,date:(r.created_at||'').slice(0,10),
        channel:item.channel||'?',source:item.source||'?',crm:item.crm||'?',tier:item.tier||'?',
        spend,ftd,dialogs,regs,cpa,cpl,cpr,d2r,r2f,
        verdict,quality,flags,decisions,ai,
        work_done:a.work_done||'',tests:a.tests||'',
        worked_best:a.worked_best||'',worked_metrics:a.worked_metrics||'',
        stop_continue:a.stop_continue||'',main_problem:a.main_problem||'',
        blocker:a.blocker||'',dynamic:a.dynamic||'',dynamic_reason:a.dynamic_reason||'',
        budget_action:a.budget_action||'',budget_reason:a.budget_reason||'',
        next_plan:a.next_plan||'',success_criteria:a.success_criteria||'',
        needs:a.needs||'',main_focus:a.main_focus||''});
    }
  }
  return out;
}

function buildFilters(ps){
  const u=arr=>[...new Set(arr.filter(Boolean))].sort();
  const buyers=u(ps.map(p=>p.buyer)),channels=u(ps.map(p=>p.channel));
  const sources=u(ps.map(p=>p.source)),tiers=u(ps.map(p=>p.tier));
  function render(id,items,key){
    const el=document.getElementById(id);
    const all=`<button class="fBtn active" onclick="setF('${key}','all',this)">Все <span class="fCnt">${items.length}</span></button>`;
    el.innerHTML=all+items.map(v=>`<button class="fBtn" onclick="setF('${key}','${v}',this)">${v}</button>`).join('');
  }
  render('fBuyer',buyers,'buyer');render('fChannel',channels,'channel');
  render('fSource',sources,'source');render('fTier',tiers,'tier');
}

function setF(key,val,btn){
  filters[key]=val;
  btn.parentElement.querySelectorAll('.fBtn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  render();
}

function filtered(){
  return projects.filter(p=>{
    if(filters.buyer!=='all'&&p.buyer!==filters.buyer)return false;
    if(filters.channel!=='all'&&p.channel!==filters.channel)return false;
    if(filters.source!=='all'&&p.source!==filters.source)return false;
    if(filters.tier!=='all'&&p.tier!==filters.tier)return false;
    return true;
  });
}

function toggle(i){
  document.getElementById('b'+i).classList.toggle('open');
  document.getElementById('a'+i).classList.toggle('open');
}

function renderCard(p,i){
  const kpi=kpiStatus(p.tier,p.cpa);
  const vc=vClass(p.verdict);
  const vl=p.verdict||p.decisions[0]||'Нет вердикта';
  const decs=p.decisions.length?p.decisions.map(d=>`<div class="dec-i">${esc(d)}</div>`).join(''):'<div class="dec-i" style="color:var(--muted)">Нет данных</div>';
  const aiBox=p.ai?`<div class="ai-box"><div class="ai-box-t">🤖 Полный AI-разбор</div><div class="ai-box-c">${esc(p.ai)}</div></div>`:'';
  const qColor=p.quality?(p.quality>=7?'var(--green)':p.quality>=5?'var(--yellow)':'var(--red)'):'';

  return`<div class="card">
  <div class="card-hdr" onclick="toggle(${i})">
    <span class="verdict ${vc}">${esc(vl)}</span>
    <div class="card-meta">
      <div class="card-name">${esc(p.channel)}</div>
      <div class="card-tags">
        <span class="tag tb">${esc(p.buyer)}</span>
        <span class="tag">${esc(p.source)}</span>
        <span class="tag">${esc(p.crm)}</span>
        <span class="tag ${tClass(p.tier)}">${esc(p.tier)}</span>
        ${p.date?`<span class="tag">${p.date}</span>`:''}
      </div>
    </div>
    <div class="card-nums">
      <div class="cn"><div class="cn-v">${fm(p.spend)}</div><div class="cn-l">Spend</div></div>
      <div class="cn"><div class="cn-v">${fn(p.ftd)}</div><div class="cn-l">FTD</div></div>
      <div class="cn"><div class="cn-v ${kpi?kpi.cls:''}">${fm(p.cpa)}</div><div class="cn-l">CPA FTD${kpi?' · '+kpi.lbl:''}</div></div>
      ${p.quality?`<div class="cn"><div class="cn-v" style="color:${qColor}">${p.quality}/10</div><div class="cn-l">Отчет</div></div>`:''}
    </div>
    <div class="card-arr" id="a${i}">▾</div>
  </div>
  <div class="card-body" id="b${i}">
    <div class="card-inner">
      <div class="met-row">
        <div class="met"><div class="met-v">${fn(p.dialogs)}</div><div class="met-l">Диалоги</div></div>
        <div class="met"><div class="met-v">${fn(p.regs)}</div><div class="met-l">Регистрации</div></div>
        <div class="met"><div class="met-v">${fm(p.cpl)}</div><div class="met-l">Цена диалога</div></div>
        <div class="met"><div class="met-v">${fm(p.cpr)}</div><div class="met-l">Цена реги</div></div>
        <div class="met"><div class="met-v">${p.d2r?fp(p.d2r*100):'—'}</div><div class="met-l">Диалог→Рега</div></div>
        <div class="met"><div class="met-v">${p.r2f?fp(p.r2f*100):'—'}</div><div class="met-l">Рега→FTD</div></div>
      </div>
      <div class="ib"><div class="ib-t">Что делали</div><div class="ib-c">${esc(p.work_done)||'—'}</div></div>
      <div class="ib"><div class="ib-t">Что тестировали</div><div class="ib-c">${esc(p.tests)||'—'}</div></div>
      <div class="ib"><div class="ib-t">Что сработало</div><div class="ib-c">${esc(p.worked_best)||'—'}</div></div>
      <div class="ib"><div class="ib-t">Доказательство цифрами</div><div class="ib-c">${esc(p.worked_metrics)||'—'}</div></div>
      <div class="ib"><div class="ib-t">Главная проблема / Что мешает</div><div class="ib-c">${esc(p.main_problem)||'—'} · ${esc(p.blocker)||'—'}</div></div>
      <div class="ib"><div class="ib-t">Динамика</div><div class="ib-c">${esc(p.dynamic)||'—'}: ${esc(p.dynamic_reason)||'—'}</div></div>
      <div class="ib"><div class="ib-t">План на следующий период</div><div class="ib-c">${esc(p.next_plan)||'—'}</div></div>
      <div class="ib"><div class="ib-t">Критерий успеха</div><div class="ib-c">${esc(p.success_criteria)||'не указан'}</div></div>
      <div class="ib"><div class="ib-t">Бюджет</div><div class="ib-c">${esc(p.budget_action)||'—'}: ${esc(p.budget_reason)||'—'}</div></div>
      <div class="ib"><div class="ib-t">Нужно от руководителя</div><div class="ib-c">${esc(p.needs)||'—'}</div></div>
      <div class="dec"><div class="dec-t">✓ Решения руководителя (AI)</div><div class="dec-items">${decs}</div></div>
      ${aiBox}
    </div>
  </div>
</div>`;
}

function render(){
  const ps=filtered();
  const main=document.getElementById('main');
  if(!ps.length){
    main.innerHTML='<div class="empty"><div class="empty-i">📭</div><div class="empty-t">Нет отчетов</div><div class="empty-s">Измени фильтры или период.<br>Отчеты появятся после заполнения в боте.</div></div>';
    return;
  }
  const totalS=ps.reduce((s,p)=>s+(p.spend||0),0);
  const totalF=ps.reduce((s,p)=>s+(p.ftd||0),0);
  const totalD=ps.reduce((s,p)=>s+(p.dialogs||0),0);
  const avgCpa=sd(totalS,totalF);
  const buyers=[...new Set(ps.map(p=>p.buyer))];
  const allFlags=ps.flatMap(p=>p.flags.map(f=>`${p.buyer} / ${p.channel}: ${f}`));
  const flagsHtml=allFlags.length
    ?`<div class="flags on"><div class="flags-t">🚨 Красные флаги и противоречия</div>${allFlags.map(f=>`<div class="flag-i">⚠ ${esc(f)}</div>`).join('')}</div>`
    :'';
  const cards=ps.map((p,i)=>renderCard(p,i)).join('');
  main.innerHTML=`
<div class="kpi-strip">
  <div class="kpi-card" style="--c:var(--accent)"><div class="kpi-l">Проектов</div><div class="kpi-v">${ps.length}</div><div class="kpi-s">${buyers.length} баеров</div></div>
  <div class="kpi-card" style="--c:var(--yellow)"><div class="kpi-l">Total Spend</div><div class="kpi-v">${fm(totalS)}</div><div class="kpi-s">за период</div></div>
  <div class="kpi-card" style="--c:var(--green)"><div class="kpi-l">Total FTD</div><div class="kpi-v">${fn(totalF)}</div><div class="kpi-s">конверсий</div></div>
  <div class="kpi-card" style="--c:var(--accent2)"><div class="kpi-l">Avg CPA FTD</div><div class="kpi-v">${fm(avgCpa)}</div><div class="kpi-s">средняя цена</div></div>
  <div class="kpi-card" style="--c:var(--blue)"><div class="kpi-l">Диалогов</div><div class="kpi-v">${fn(totalD)}</div><div class="kpi-s">суммарно</div></div>
</div>
${flagsHtml}
<div class="sec-hdr"><div class="sec-t">Проекты</div><div class="sec-l"></div><div class="sec-c">${ps.length} проектов</div></div>
<div class="cards">${cards}</div>`;
}

function setPeriod(d,btn){
  days=d;
  document.querySelectorAll('.pBtn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  loadData();
}

async function loadData(){
  try{
    const res=await fetch(`/api/reports?days=${days}&secret=${SECRET}`);
    const data=await res.json();
    projects=parseReports(data);
    buildFilters(projects);
    render();
    document.getElementById('upd').textContent=new Date().toLocaleTimeString('ru');
  }catch(e){
    document.getElementById('main').innerHTML='<div class="empty"><div class="empty-i">⚠️</div><div class="empty-t">Ошибка загрузки</div></div>';
  }
}

setInterval(loadData,60000);
loadData();
</script>
</body>
</html>"""

@app.route("/")
def dashboard():
    return render_template_string(HTML, secret=API_SECRET)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

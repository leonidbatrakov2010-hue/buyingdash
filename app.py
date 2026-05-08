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
    if not DATA_FILE.exists(): return []
    try: return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except: return []

def save_all_reports(reports):
    DATA_FILE.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

def require_secret(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        secret = request.headers.get("X-API-Secret") or request.args.get("secret")
        if secret != API_SECRET: return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/api/report", methods=["POST"])
@require_secret
def receive_report():
    data = request.get_json()
    if not data: return jsonify({"error": "No data"}), 400
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
            if ts >= cutoff: filtered.append(r)
        except: filtered.append(r)
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#0f1117;color:#e2e8f0;font-size:14px;line-height:1.5}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:#2d3748;border-radius:4px}

/* Header */
.hdr{height:56px;background:#161b27;border-bottom:1px solid #1e2535;display:flex;align-items:center;justify-content:space-between;padding:0 24px;position:sticky;top:0;z-index:100}
.logo{font-size:16px;font-weight:700;color:#fff;letter-spacing:-.3px}.logo b{color:#7c6af7}
.hdr-r{display:flex;align-items:center;gap:12px}
.dot{width:7px;height:7px;background:#48bb78;border-radius:50%;animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}
.upd{font-size:12px;color:#718096}
.btn-sm{font-size:12px;font-weight:500;padding:6px 14px;border:1px solid #2d3748;background:transparent;color:#a0aec0;border-radius:6px;cursor:pointer;transition:all .15s}
.btn-sm:hover{border-color:#7c6af7;color:#7c6af7}

/* Layout */
.layout{display:flex;min-height:calc(100vh - 56px)}

/* Sidebar */
.sb{width:220px;flex-shrink:0;background:#161b27;border-right:1px solid #1e2535;padding:16px 12px;position:sticky;top:56px;height:calc(100vh - 56px);overflow-y:auto}
.period{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:20px}
.pb{font-size:12px;font-weight:500;padding:6px 0;background:#1a2035;border:1px solid #2d3748;color:#718096;border-radius:6px;cursor:pointer;text-align:center;transition:all .15s}
.pb:hover{color:#e2e8f0;border-color:#4a5568}
.pb.on{background:#7c6af7;border-color:#7c6af7;color:#fff}
.sb-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#4a5568;padding:0 6px;margin-bottom:6px}
.sb-sec{margin-bottom:18px}
.fb{display:block;width:100%;text-align:left;font-size:12px;font-weight:500;padding:6px 10px;background:transparent;border:1px solid transparent;color:#718096;border-radius:6px;cursor:pointer;transition:all .15s;margin-bottom:2px}
.fb:hover{background:#1a2035;color:#e2e8f0}
.fb.on{background:rgba(124,106,247,.15);border-color:rgba(124,106,247,.4);color:#a89ff7}
.fb-c{float:right;font-size:10px;color:#4a5568;background:#1a2035;padding:1px 5px;border-radius:3px}

/* Main */
.main{flex:1;padding:20px 24px;overflow-x:hidden}

/* KPI */
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}
.kpi{background:#161b27;border:1px solid #1e2535;border-radius:10px;padding:14px 16px}
.kpi-l{font-size:11px;font-weight:500;color:#718096;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.kpi-v{font-size:22px;font-weight:700;color:#fff;letter-spacing:-.5px}
.kpi-s{font-size:11px;color:#718096;margin-top:4px}

/* Flags */
.flags{background:rgba(245,101,101,.08);border:1px solid rgba(245,101,101,.2);border-radius:10px;padding:14px 16px;margin-bottom:16px;display:none}
.flags.on{display:block}
.flags-t{font-size:11px;font-weight:600;color:#fc8181;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}
.flag-i{font-size:12px;color:#e2e8f0;padding:5px 0;border-bottom:1px solid rgba(245,101,101,.1)}
.flag-i:last-child{border-bottom:none}

/* Section */
.sh{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.sh-t{font-size:11px;font-weight:600;color:#4a5568;text-transform:uppercase;letter-spacing:1px;white-space:nowrap}
.sh-l{flex:1;height:1px;background:#1e2535}
.sh-c{font-size:11px;color:#4a5568;white-space:nowrap}

/* Cards */
.cards{display:flex;flex-direction:column;gap:10px}
.card{background:#161b27;border:1px solid #1e2535;border-radius:10px;overflow:hidden;transition:border-color .2s}
.card:hover{border-color:#2d3748}

.card-hdr{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer;user-select:none}
.vd{flex-shrink:0;font-size:11px;font-weight:600;padding:4px 10px;border-radius:5px;text-transform:uppercase;letter-spacing:.3px;white-space:nowrap}
.vs{background:rgba(72,187,120,.15);color:#68d391;border:1px solid rgba(72,187,120,.3)}
.vk{background:rgba(237,191,79,.15);color:#f6c90e;border:1px solid rgba(237,191,79,.3)}
.vc{background:rgba(245,101,101,.15);color:#fc8181;border:1px solid rgba(245,101,101,.3)}
.vt{background:rgba(124,106,247,.15);color:#a89ff7;border:1px solid rgba(124,106,247,.3)}
.vp{background:rgba(74,85,104,.2);color:#718096;border:1px solid rgba(74,85,104,.3)}

.cm{flex:1;min-width:0}
.cn{font-size:15px;font-weight:600;color:#fff;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ct{display:flex;gap:5px;flex-wrap:wrap}
.tg{font-size:11px;font-weight:500;padding:2px 7px;border-radius:4px;background:#1a2035;border:1px solid #2d3748;color:#718096}
.tb{background:rgba(124,106,247,.12);border-color:rgba(124,106,247,.25);color:#a89ff7}
.t1{background:rgba(124,106,247,.1);border-color:rgba(124,106,247,.2);color:#a89ff7}
.t2{background:rgba(237,191,79,.1);border-color:rgba(237,191,79,.2);color:#f6c90e}
.t3{background:rgba(72,187,120,.1);border-color:rgba(72,187,120,.2);color:#68d391}
.tru{background:rgba(245,101,101,.1);border-color:rgba(245,101,101,.2);color:#fc8181}

.cnums{display:flex;gap:20px;flex-shrink:0}
.cnum{text-align:right}
.cnum-v{font-size:15px;font-weight:600;color:#fff;white-space:nowrap}
.cnum-l{font-size:10px;color:#718096;margin-top:2px;white-space:nowrap}
.g{color:#68d391}.y{color:#f6c90e}.r{color:#fc8181}

.arr{color:#4a5568;font-size:12px;flex-shrink:0;transition:transform .2s;margin-left:4px}
.arr.open{transform:rotate(180deg)}

/* Body */
.cb{display:none;border-top:1px solid #1e2535}
.cb.open{display:block}
.cb-inner{padding:18px;display:grid;grid-template-columns:1fr 1fr;gap:16px}

.mets{grid-column:1/-1;display:grid;grid-template-columns:repeat(6,1fr);gap:8px}
.met{background:#1a2035;border-radius:8px;padding:10px 12px;text-align:center}
.met-v{font-size:16px;font-weight:600;color:#fff}
.met-l{font-size:10px;color:#718096;margin-top:3px}

.ib-t{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#4a5568;margin-bottom:7px;padding-bottom:5px;border-bottom:1px solid #1e2535}
.ib-c{font-size:12px;color:#a0aec0;line-height:1.6}
.ib-c strong{color:#7c6af7}

.dec{grid-column:1/-1;background:rgba(124,106,247,.07);border:1px solid rgba(124,106,247,.18);border-radius:8px;padding:12px 16px}
.dec-t{font-size:10px;font-weight:600;color:#7c6af7;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}
.dec-items{display:flex;flex-wrap:wrap;gap:6px}
.dec-i{font-size:11px;padding:4px 10px;background:rgba(124,106,247,.12);border:1px solid rgba(124,106,247,.22);border-radius:5px;color:#c4b8ff}

.ai{grid-column:1/-1;background:#1a2035;border-radius:8px;padding:14px 16px}
.ai-t{font-size:10px;font-weight:600;color:#4a5568;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}
.ai-c{font-size:12px;color:#a0aec0;line-height:1.8;white-space:pre-wrap;max-height:360px;overflow-y:auto}

/* Empty */
.empty{text-align:center;padding:80px 20px;color:#4a5568}
.empty-i{font-size:44px;margin-bottom:14px}
.empty-t{font-size:18px;font-weight:600;color:#718096;margin-bottom:6px}
.empty-s{font-size:12px;line-height:1.6}

@media(max-width:860px){.sb{display:none}.kpis{grid-template-columns:repeat(3,1fr)}.cb-inner{grid-template-columns:1fr}.mets{grid-template-columns:repeat(3,1fr)}}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">Buying <b>Dashboard</b></div>
  <div class="hdr-r">
    <div class="dot"></div>
    <span class="upd" id="upd">Загрузка...</span>
    <button class="btn-sm" onclick="load()">↻ Обновить</button>
  </div>
</div>
<div class="layout">
  <div class="sb">
    <div class="period">
      <button class="pb" onclick="sp(1,this)">1д</button>
      <button class="pb on" onclick="sp(7,this)">7д</button>
      <button class="pb" onclick="sp(14,this)">14д</button>
      <button class="pb" onclick="sp(30,this)">30д</button>
    </div>
    <div class="sb-sec"><div class="sb-lbl">Баер</div><div id="fB"></div></div>
    <div class="sb-sec"><div class="sb-lbl">Канал</div><div id="fC"></div></div>
    <div class="sb-sec"><div class="sb-lbl">Источник</div><div id="fS"></div></div>
    <div class="sb-sec"><div class="sb-lbl">ТИР</div><div id="fT"></div></div>
  </div>
  <div class="main" id="main"><div class="empty"><div class="empty-i">⏳</div><div class="empty-t">Загрузка...</div></div></div>
</div>
<script>
const SEC="{{secret}}";
let days=7,projects=[],f={b:'all',c:'all',s:'all',t:'all'};

const pn=v=>{if(!v)return null;const n=parseFloat(String(v).replace(/[^0-9.,]/g,'').replace(',','.'));return isNaN(n)?null:n};
const sd=(a,b)=>(a&&b&&b!==0)?a/b:null;
const fm=v=>v==null?'—':(v>=1000?'$'+Math.round(v).toLocaleString('ru'):'$'+Number(v).toFixed(2));
const fn=v=>v==null?'—':Math.round(v).toString();
const fp=v=>v==null?'—':Number(v).toFixed(1)+'%';
const esc=s=>String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

function kpi(tier,cpa){
  if(!cpa||!tier)return null;
  const r={ТИР1:[300,600],ТИР2:[150,300],ТИР3:[80,150],РУ:[300,700]}[tier];
  if(!r)return null;
  if(cpa<=r[0])return{cl:'g',lb:'✓ Отлично'};
  if(cpa<=r[1])return{cl:'y',lb:'~ Допустимо'};
  return{cl:'r',lb:'✗ Дорого'};
}
function vc(t){if(!t)return'vk';if(t.includes('МАСШТАБ'))return'vs';if(t.includes('СНИЗИТЬ'))return'vc';if(t.includes('ТЕСТ'))return'vt';if(t.includes('ПАУЗА')||t.includes('СТОП'))return'vp';return'vk'}
function tc(t){return{ТИР1:'t1',ТИР2:'t2',ТИР3:'t3',РУ:'tru'}[t]||''}
function exV(txt){if(!txt)return'';const m=txt.match(/AI-вердикт[:\s]+([^\n]+)/);return m?m[1].trim():''}
function exQ(txt){if(!txt)return null;const m=txt.match(/Оценка[:\s]+(\d+)\s*\/\s*10/i);return m?parseInt(m[1]):null}
function exF(txt){
  if(!txt)return[];
  const m=txt.match(/ПРОТИВОРЕЧИЯ[^\n]*\n([\s\S]*?)(?:━━━|ОЦЕНКА|$)/);
  if(!m||m[1].includes('Явных'))return[];
  return m[1].split('\n').filter(l=>l.trim().startsWith('-')).map(l=>l.replace(/^-\s*/,'').trim()).filter(Boolean);
}
function exD(txt){
  if(!txt)return[];
  const m=txt.match(/РЕШЕНИЯ РУКОВОДИТЕЛЯ[^\n]*\n([\s\S]*?)(?:━━━|$)/);
  if(!m)return[];
  return m[1].split('\n').filter(l=>l.trim().startsWith('-')).map(l=>l.replace(/^-\s*/,'').trim()).filter(Boolean);
}

function parse(reports){
  const out=[];
  for(const r of reports){
    const buyer=r.buyer_name||'?';
    const ai=r.ai_report||'';
    const verdict=exV(ai),quality=exQ(ai),flags=exF(ai),decisions=exD(ai);
    const items=(r.state?.reports)||r.channels||[];
    for(const item of items){
      const a=item.answers||{};
      const spend=pn(a.spend),ftd=pn(a.ftd),dialogs=pn(a.dialogs),regs=pn(a.regs);
      out.push({buyer,date:(r.created_at||'').slice(0,10),
        channel:item.channel||'?',source:item.source||'?',crm:item.crm||'?',tier:item.tier||'?',
        spend,ftd,dialogs,regs,cpa:sd(spend,ftd),cpl:sd(spend,dialogs),cpr:sd(spend,regs),
        d2r:sd(regs,dialogs),r2f:sd(ftd,regs),
        verdict,quality,flags,decisions,ai,
        work_done:a.work_done||'',tests:a.tests||'',
        worked_best:a.worked_best||'',worked_metrics:a.worked_metrics||'',
        stop_continue:a.stop_continue||'',main_problem:a.main_problem||'',
        blocker:a.blocker||'',dynamic:a.dynamic||'',dynamic_reason:a.dynamic_reason||'',
        budget_action:a.budget_action||'',budget_reason:a.budget_reason||'',
        next_plan:a.next_plan||'',success_criteria:a.success_criteria||'',
        needs:a.needs||''});
    }
  }
  return out;
}

function buildFilters(ps){
  const u=arr=>[...new Set(arr.filter(Boolean))].sort();
  const render=(id,items,key)=>{
    const el=document.getElementById(id);
    el.innerHTML=`<button class="fb on" onclick="sf('${key}','all',this)">Все <span class="fb-c">${items.length}</span></button>`
      +items.map(v=>`<button class="fb" onclick="sf('${key}','${v}',this)">${v}</button>`).join('');
  };
  render('fB',u(ps.map(p=>p.buyer)),'b');
  render('fC',u(ps.map(p=>p.channel)),'c');
  render('fS',u(ps.map(p=>p.source)),'s');
  render('fT',u(ps.map(p=>p.tier)),'t');
}

function sf(key,val,btn){
  f[key]=val;
  btn.parentElement.querySelectorAll('.fb').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  render();
}

function filtered(){return projects.filter(p=>(f.b==='all'||p.buyer===f.b)&&(f.c==='all'||p.channel===f.c)&&(f.s==='all'||p.source===f.s)&&(f.t==='all'||p.tier===f.t))}

function toggle(i){
  document.getElementById('cb'+i).classList.toggle('open');
  document.getElementById('ar'+i).classList.toggle('open');
}

function card(p,i){
  const k=kpi(p.tier,p.cpa);
  const vl=p.verdict||'Нет вердикта';
  const decs=p.decisions.length?p.decisions.map(d=>`<div class="dec-i">${esc(d)}</div>`).join(''):'<span style="color:#4a5568;font-size:12px">Нет данных</span>';
  const qc=p.quality?(p.quality>=7?'g':p.quality>=5?'y':'r'):'';
  return`<div class="card">
  <div class="card-hdr" onclick="toggle(${i})">
    <span class="vd ${vc(p.verdict)}">${esc(vl)}</span>
    <div class="cm">
      <div class="cn">${esc(p.channel)}</div>
      <div class="ct">
        <span class="tg tb">${esc(p.buyer)}</span>
        <span class="tg">${esc(p.source)}</span>
        <span class="tg">${esc(p.crm)}</span>
        <span class="tg ${tc(p.tier)}">${esc(p.tier)}</span>
        ${p.date?`<span class="tg">${p.date}</span>`:''}
      </div>
    </div>
    <div class="cnums">
      <div class="cnum"><div class="cnum-v">${fm(p.spend)}</div><div class="cnum-l">Spend</div></div>
      <div class="cnum"><div class="cnum-v">${fn(p.ftd)}</div><div class="cnum-l">FTD</div></div>
      <div class="cnum"><div class="cnum-v ${k?k.cl:''}">${fm(p.cpa)}</div><div class="cnum-l">CPA FTD${k?' · '+k.lb:''}</div></div>
      ${p.quality?`<div class="cnum"><div class="cnum-v ${qc}">${p.quality}/10</div><div class="cnum-l">Отчёт</div></div>`:''}
    </div>
    <span class="arr" id="ar${i}">▾</span>
  </div>
  <div class="cb" id="cb${i}">
    <div class="cb-inner">
      <div class="mets">
        <div class="met"><div class="met-v">${fn(p.dialogs)}</div><div class="met-l">Диалоги</div></div>
        <div class="met"><div class="met-v">${fn(p.regs)}</div><div class="met-l">Регистрации</div></div>
        <div class="met"><div class="met-v">${fm(p.cpl)}</div><div class="met-l">Цена диалога</div></div>
        <div class="met"><div class="met-v">${fm(p.cpr)}</div><div class="met-l">Цена реги</div></div>
        <div class="met"><div class="met-v">${p.d2r?fp(p.d2r*100):'—'}</div><div class="met-l">Диалог→Рега</div></div>
        <div class="met"><div class="met-v">${p.r2f?fp(p.r2f*100):'—'}</div><div class="met-l">Рега→FTD</div></div>
      </div>
      <div><div class="ib-t">Что делали</div><div class="ib-c">${esc(p.work_done)||'—'}</div></div>
      <div><div class="ib-t">Что тестировали</div><div class="ib-c">${esc(p.tests)||'—'}</div></div>
      <div><div class="ib-t">Что сработало</div><div class="ib-c">${esc(p.worked_best)||'—'}</div></div>
      <div><div class="ib-t">Доказательство цифрами</div><div class="ib-c">${esc(p.worked_metrics)||'—'}</div></div>
      <div><div class="ib-t">Главная проблема / Что мешает</div><div class="ib-c">${esc(p.main_problem)||'—'} · ${esc(p.blocker)||'—'}</div></div>
      <div><div class="ib-t">Динамика и причина</div><div class="ib-c">${esc(p.dynamic)||'—'}: ${esc(p.dynamic_reason)||'—'}</div></div>
      <div><div class="ib-t">План на следующий период</div><div class="ib-c">${esc(p.next_plan)||'—'}</div></div>
      <div><div class="ib-t">Критерий успеха</div><div class="ib-c">${esc(p.success_criteria)||'не указан'}</div></div>
      <div><div class="ib-t">Бюджет</div><div class="ib-c">${esc(p.budget_action)||'—'}: ${esc(p.budget_reason)||'—'}</div></div>
      <div><div class="ib-t">Нужно от руководителя</div><div class="ib-c">${esc(p.needs)||'—'}</div></div>
      <div class="dec"><div class="dec-t">✓ Решения руководителя (AI)</div><div class="dec-items">${decs}</div></div>
      ${p.ai?`<div class="ai"><div class="ai-t">🤖 Полный AI-разбор</div><div class="ai-c">${esc(p.ai)}</div></div>`:''}
    </div>
  </div>
</div>`;
}

function render(){
  const ps=filtered();
  const main=document.getElementById('main');
  if(!ps.length){main.innerHTML='<div class="empty"><div class="empty-i">📭</div><div class="empty-t">Нет отчётов</div><div class="empty-s">Измени фильтры или период</div></div>';return}
  const tS=ps.reduce((s,p)=>s+(p.spend||0),0);
  const tF=ps.reduce((s,p)=>s+(p.ftd||0),0);
  const tD=ps.reduce((s,p)=>s+(p.dialogs||0),0);
  const buyers=[...new Set(ps.map(p=>p.buyer))];
  const allFlags=ps.flatMap(p=>p.flags.map(fl=>`${p.buyer} / ${p.channel}: ${fl}`));
  main.innerHTML=`
<div class="kpis">
  <div class="kpi"><div class="kpi-l">Проектов</div><div class="kpi-v">${ps.length}</div><div class="kpi-s">${buyers.length} баеров</div></div>
  <div class="kpi"><div class="kpi-l">Total Spend</div><div class="kpi-v">${fm(tS)}</div><div class="kpi-s">за период</div></div>
  <div class="kpi"><div class="kpi-l">Total FTD</div><div class="kpi-v">${fn(tF)}</div><div class="kpi-s">конверсий</div></div>
  <div class="kpi"><div class="kpi-l">Avg CPA FTD</div><div class="kpi-v">${fm(sd(tS,tF))}</div><div class="kpi-s">средняя цена</div></div>
  <div class="kpi"><div class="kpi-l">Диалогов</div><div class="kpi-v">${fn(tD)}</div><div class="kpi-s">суммарно</div></div>
</div>
${allFlags.length?`<div class="flags on"><div class="flags-t">🚨 Красные флаги</div>${allFlags.map(fl=>`<div class="flag-i">⚠ ${esc(fl)}</div>`).join('')}</div>`:''}
<div class="sh"><div class="sh-t">Проекты</div><div class="sh-l"></div><div class="sh-c">${ps.length} проектов</div></div>
<div class="cards">${ps.map((p,i)=>card(p,i)).join('')}</div>`;
}

function sp(d,btn){days=d;document.querySelectorAll('.pb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');load()}

async function load(){
  try{
    const r=await fetch(`/api/reports?days=${days}&secret=${SEC}`);
    const data=await r.json();
    projects=parse(data);
    buildFilters(projects);
    render();
    document.getElementById('upd').textContent=new Date().toLocaleTimeString('ru');
  }catch(e){document.getElementById('main').innerHTML='<div class="empty"><div class="empty-i">⚠️</div><div class="empty-t">Ошибка загрузки</div></div>'}
}
setInterval(load,60000);load();
</script>
</body>
</html>"""

@app.route("/")
def dashboard():
    return render_template_string(HTML, secret=API_SECRET)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

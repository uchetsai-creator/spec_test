#!/usr/bin/env python3
"""schema_to_html.py — Prisma/SQL → Crow's Foot ERD HTML with clickable relations"""
import sys, re, os, json

def detect_and_parse(content, ext):
    if ext == ".prisma" or re.search(r'\bmodel\s+\w+\s*\{', content):
        return parse_prisma(content)
    return parse_sql(content)

PRISMA_SCALARS = {"String","Int","Float","Boolean","DateTime","Json","Decimal","BigInt","Bytes"}
PRISMA_TYPE_MAP = {"String":"string","Int":"int","Float":"float","Boolean":"string","DateTime":"datetime","Json":"string","Decimal":"float","BigInt":"int","Bytes":"string"}
PRISMA_ANN_MAP  = {"Json":"json","Boolean":"boolean"}

def parse_prisma(content):
    tables = {}
    relation_fields = {}
    for model_name, block in re.findall(r'model\s+(\w+)\s*\{([^}]+)\}', content, re.DOTALL):
        cols = []
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('@@'): continue
            m = re.match(r'(\w+)\s+(\w+)(\?|\[\])?\s*(.*)', line)
            if not m: continue
            fname, ftype, mod, rest = m.group(1), m.group(2), m.group(3) or "", m.group(4)
            if ftype not in PRISMA_SCALARS and ftype[0].isupper():
                relation_fields.setdefault(model_name, []).append((fname, ftype, mod, rest))
                continue
            constraint = "PK" if "@id" in rest else ("UK" if "@unique" in rest else "")
            ann = PRISMA_ANN_MAP.get(ftype, "")
            if mod == "?": ann = (ann + " nullable").strip() if ann else "nullable"
            elif mod == "[]": ann = (ann + " array").strip() if ann else "array"
            cols.append({"name":fname,"type":PRISMA_TYPE_MAP.get(ftype,ftype.lower()),"constraint":constraint,"annotation":ann})
        tables[model_name] = cols
    for model_name, ref_list in relation_fields.items():
        if model_name not in tables: continue
        for (fname, ftype, mod, rest) in ref_list:
            fk_m = re.search(r'@relation\s*\(.*?fields:\s*\[([^\]]+)\]', rest)
            if fk_m:
                for fk_col in [c.strip() for c in fk_m.group(1).split(',')]:
                    for col in tables[model_name]:
                        if col["name"] == fk_col:
                            col["constraint"] = "PK,FK" if col["constraint"] == "PK" else "FK"
    relations, seen = [], set()
    for model_name, ref_list in relation_fields.items():
        for (fname, ftype, mod, rest) in ref_list:
            if ftype not in tables: continue
            key = tuple(sorted([model_name, ftype]))
            if key in seen: continue
            seen.add(key)
            is_array = mod == "[]"
            is_opt = mod == "?"
            if is_array:
                relations.append({"from":ftype,"to":model_name,"from_card":"one","to_card":"many","from_opt":False,"to_opt":True})
            else:
                relations.append({"from":ftype,"to":model_name,"from_card":"one","to_card":"one","from_opt":False,"to_opt":is_opt})
    return tables, relations

SQL_TYPE_MAP = {"VARCHAR":"string","CHAR":"string","TEXT":"string","UUID":"string","INT":"int","INTEGER":"int","BIGINT":"int","SMALLINT":"int","SERIAL":"int","BIGSERIAL":"int","FLOAT":"float","DOUBLE":"float","DECIMAL":"float","NUMERIC":"float","REAL":"float","BOOLEAN":"string","BOOL":"string","TIMESTAMP":"datetime","DATE":"datetime","DATETIME":"datetime","JSON":"string","JSONB":"string"}
SQL_ANN_MAP  = {"JSON":"json","JSONB":"json","BOOLEAN":"boolean","BOOL":"boolean"}

def parse_sql(content):
    content = re.sub(r'--[^\n]*','',content)
    content = re.sub(r'/\*.*?\*/','',content,flags=re.DOTALL)
    tables, relations, seen = {}, [], set()
    for table_name, block in re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s*\(([^;]+)\)', content, re.IGNORECASE|re.DOTALL):
        cols, pk_cols, fk_map = [], set(), {}
        pk_m = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', block, re.IGNORECASE)
        if pk_m:
            for c in pk_m.group(1).split(','): pk_cols.add(c.strip().strip('"`'))
        for m in re.finditer(r'FOREIGN\s+KEY\s*\(["`]?(\w+)["`]?\)\s+REFERENCES\s+["`]?(\w+)["`]?', block, re.IGNORECASE):
            fk_map[m.group(1)] = m.group(2)
            key = tuple(sorted([table_name, m.group(2)]))
            if key not in seen:
                seen.add(key)
                relations.append({"from":m.group(2),"to":table_name,"from_card":"one","to_card":"many","from_opt":False,"to_opt":True})
        for line in block.splitlines():
            line = line.strip().rstrip(',')
            if not line or re.match(r'(PRIMARY|FOREIGN|UNIQUE|KEY|INDEX|CONSTRAINT|CHECK)', line, re.IGNORECASE): continue
            m = re.match(r'["`]?(\w+)["`]?\s+(\w+(?:\s*\(\s*\d+\s*(?:,\s*\d+)?\s*\))?)(.*)', line)
            if not m: continue
            col_name, raw_type, rest = m.group(1), m.group(2).upper(), m.group(3)
            base = re.sub(r'\(.*\)','',raw_type).strip()
            constraint = ""
            if col_name in pk_cols or "PRIMARY KEY" in rest.upper(): constraint = "PK"
            if col_name in fk_map: constraint = "PK,FK" if constraint=="PK" else "FK"
            if "UNIQUE" in rest.upper() and not constraint: constraint = "UK"
            cols.append({"name":col_name,"type":SQL_TYPE_MAP.get(base,raw_type.lower()),"constraint":constraint,"annotation":SQL_ANN_MAP.get(base,"")})
        tables[table_name] = cols
    return tables, relations

HTML = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Segoe UI',Arial,sans-serif; background:#F0F7FF; overflow:hidden; }
#wrap { position:fixed; inset:0; overflow:hidden; cursor:grab; }
#wrap:active { cursor:grabbing; }
#stage { position:absolute; transform-origin:0 0; }
canvas#lines { position:absolute; top:0; left:0; pointer-events:none; }
.card { position:absolute; width:280px; border-radius:8px; overflow:hidden; box-shadow:0 3px 12px #0002; border:1.5px solid #BEE3F8; background:#fff; cursor:grab; z-index:1; transition: opacity 0.2s; }
.card:active { cursor:grabbing; }
.card-head { background:#1A365D; color:#fff; font-weight:bold; font-size:13px; padding:8px 12px; text-align:center; }
.col { display:flex; align-items:center; padding:3px 8px; min-height:26px; border-bottom:1px solid #EBF8FF; font-size:11px; }
.col:last-child { border-bottom:none; }
.col:nth-child(odd) { background:#F7FBFF; }
.col.highlighted { background:#FFF3CD !important; }
.badge { font-size:9px; font-weight:bold; padding:1px 5px; border-radius:3px; margin-right:6px; white-space:nowrap; }
.pk   { background:#FED7D7; color:#C53030; }
.fk   { background:#BEE3F8; color:#2B6CB0; }
.uk   { background:#C6F6D5; color:#276749; }
.pkfk { background:#E9D8FD; color:#553C9A; }
.col-name { flex:1; color:#2D3748; }
.col-type { color:#718096; font-size:10px; }
.card.dimmed { opacity: 0.2; }
#tooltip {
  position:fixed; background:#1A365D; color:#fff; font-size:12px;
  padding:6px 10px; border-radius:6px; pointer-events:none;
  display:none; z-index:999; white-space:nowrap;
}
#hint {
  position:fixed; bottom:16px; left:50%; transform:translateX(-50%);
  background:#1A365D; color:#90CDF4; font-size:12px;
  padding:6px 14px; border-radius:20px; pointer-events:none; z-index:999;
}
</style>
</head>
<body>
<div id="wrap">
  <div id="stage">
    <canvas id="lines" width="8000" height="6000"></canvas>
  </div>
</div>
<div id="tooltip"></div>
<div id="hint">點選關聯線查看詳情 · 點空白處取消</div>
<script>
const TABLES = {tables_json};
const RELATIONS = {relations_json};
const TW=280, TH=34, CH=26, COLS=4, PX=120, PY=80;
const pos = {};
let scale=1, px=60, py=60;
let panning=false, lmx=0, lmy=0;
let dragging=null, dox=0, doy=0;
let activeRel = null;

// Store computed line paths for hit detection
const linePaths = [];

function tableH(name) { return TH + (TABLES[name]||[]).length * CH; }

function initPos() {
  Object.keys(TABLES).forEach((n,i) => {
    pos[n] = { x:(i%COLS)*(TW+PX)+60, y:Math.floor(i/COLS)*580+60 };
  });
}

function badge(c) {
  if (!c) return '';
  const cls = c==='PK,FK'?'pkfk':c.toLowerCase();
  return `<span class="badge ${cls}">${c}</span>`;
}

function buildCards() {
  const stage = document.getElementById('stage');
  Object.entries(TABLES).forEach(([name, cols]) => {
    const d = document.createElement('div');
    d.className='card'; d.id='c-'+name;
    d.style.left=pos[name].x+'px'; d.style.top=pos[name].y+'px';
    let h=`<div class="card-head">${name}</div>`;
    cols.forEach(c => {
      const ann = c.annotation ? ` (${c.annotation})` : '';
      h += `<div class="col" id="col-${name}-${c.name}">${badge(c.constraint)}<span class="col-name">${c.name}</span><span class="col-type">${c.type}${ann}</span></div>`;
    });
    d.innerHTML=h;
    d.addEventListener('mousedown', e => {
      dragging=name; dox=e.clientX/scale-pos[name].x; doy=e.clientY/scale-pos[name].y;
      d.style.zIndex=99; e.stopPropagation();
    });
    stage.appendChild(d);
  });
}

function colY(tableName, colName) {
  const cols = TABLES[tableName] || [];
  const idx = cols.findIndex(c => c.name === colName);
  if (idx < 0) return pos[tableName].y + tableH(tableName)/2;
  return pos[tableName].y + TH + idx * CH + CH/2;
}

function pkCol(tableName) {
  const cols = TABLES[tableName] || [];
  const pk = cols.find(c => c.constraint === 'PK' || c.constraint === 'PK,FK');
  return pk ? pk.name : null;
}

function fkCol(tableName, refTable) {
  const cols = TABLES[tableName] || [];
  const refLower = refTable.toLowerCase();
  const fk = cols.find(c =>
    (c.constraint === 'FK' || c.constraint === 'PK,FK') &&
    (c.name.toLowerCase() === refLower + 'id' ||
     c.name.toLowerCase() === refLower + '_id' ||
     c.name.toLowerCase().startsWith(refLower))
  );
  return fk ? fk.name : null;
}

// Crow's foot drawing
const LW = 2, S = 14;
function drawOneEnd(ctx, x, y, a) {
  const px=-Math.sin(a), py=Math.cos(a);
  ctx.beginPath(); ctx.moveTo(x+px*S-Math.cos(a)*8, y+py*S-Math.sin(a)*8);
  ctx.lineTo(x-px*S-Math.cos(a)*8, y-py*S-Math.sin(a)*8); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x+px*S-Math.cos(a)*16, y+py*S-Math.sin(a)*16);
  ctx.lineTo(x-px*S-Math.cos(a)*16, y-py*S-Math.sin(a)*16); ctx.stroke();
}
function drawOneOptEnd(ctx, x, y, a) {
  const px=-Math.sin(a), py=Math.cos(a);
  const r=5;
  ctx.beginPath(); ctx.arc(x-Math.cos(a)*26, y-Math.sin(a)*26, r, 0, Math.PI*2);
  ctx.fillStyle=ctx._bg||'#F0F7FF'; ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x+px*S-Math.cos(a)*8, y+py*S-Math.sin(a)*8);
  ctx.lineTo(x-px*S-Math.cos(a)*8, y-py*S-Math.sin(a)*8); ctx.stroke();
}
function drawManyEnd(ctx, x, y, a) {
  const px=-Math.sin(a), py=Math.cos(a);
  ctx.beginPath(); ctx.moveTo(x-Math.cos(a)*6, y-Math.sin(a)*6);
  ctx.lineTo(x-Math.cos(a)*18, y-Math.sin(a)*18); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x-Math.cos(a)*6, y-Math.sin(a)*6);
  ctx.lineTo(x+px*S-Math.cos(a)*18, y+py*S-Math.sin(a)*18); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x-Math.cos(a)*6, y-Math.sin(a)*6);
  ctx.lineTo(x-px*S-Math.cos(a)*18, y-py*S-Math.sin(a)*18); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x+px*S-Math.cos(a)*22, y+py*S-Math.sin(a)*22);
  ctx.lineTo(x-px*S-Math.cos(a)*22, y-py*S-Math.sin(a)*22); ctx.stroke();
}
function drawManyOptEnd(ctx, x, y, a) {
  const px=-Math.sin(a), py=Math.cos(a), r=5;
  ctx.beginPath(); ctx.moveTo(x-Math.cos(a)*6, y-Math.sin(a)*6);
  ctx.lineTo(x-Math.cos(a)*18, y-Math.sin(a)*18); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x-Math.cos(a)*6, y-Math.sin(a)*6);
  ctx.lineTo(x+px*S-Math.cos(a)*18, y+py*S-Math.sin(a)*18); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x-Math.cos(a)*6, y-Math.sin(a)*6);
  ctx.lineTo(x-px*S-Math.cos(a)*18, y-py*S-Math.sin(a)*18); ctx.stroke();
  ctx.beginPath(); ctx.arc(x-Math.cos(a)*30, y-Math.sin(a)*30, r, 0, Math.PI*2);
  ctx.fillStyle=ctx._bg||'#F0F7FF'; ctx.fill(); ctx.stroke();
}
function drawSymbol(ctx, x, y, angle, card, opt) {
  if (card==='many') { opt ? drawManyOptEnd(ctx,x,y,angle) : drawManyEnd(ctx,x,y,angle); }
  else               { opt ? drawOneOptEnd(ctx,x,y,angle)  : drawOneEnd(ctx,x,y,angle);  }
}

function computeEndpoints(rel) {
  const s = pos[rel.from], t = pos[rel.to];
  if (!s || !t) return null;
  const fromPK = pkCol(rel.from);
  const toFK   = fkCol(rel.to, rel.from);
  const fromY  = fromPK ? colY(rel.from, fromPK) : s.y + tableH(rel.from)/2;
  const toY    = toFK   ? colY(rel.to,   toFK)   : t.y + tableH(rel.to)/2;
  let x1, y1, x2, y2;
  if      (s.x+TW+10 < t.x)                  { x1=s.x+TW; y1=fromY; x2=t.x;    y2=toY; }
  else if (t.x+TW+10 < s.x)                  { x1=s.x;    y1=fromY; x2=t.x+TW; y2=toY; }
  else if (s.y+tableH(rel.from)+10 < t.y)    { x1=s.x+TW/2; y1=s.y+tableH(rel.from); x2=t.x+TW/2; y2=t.y; }
  else                                         { x1=s.x+TW/2; y1=s.y; x2=t.x+TW/2; y2=t.y+tableH(rel.to); }
  return {x1, y1, x2, y2, fromPK, toFK};
}

function drawLines() {
  const canvas = document.getElementById('lines');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  linePaths.length = 0;

  RELATIONS.forEach((rel, idx) => {
    const ep = computeEndpoints(rel);
    if (!ep) return;
    const {x1, y1, x2, y2} = ep;
    const cx = (x1+x2)/2;

    const isActive = activeRel === idx;
    const isDimmed = activeRel !== null && !isActive;

    const color = isActive ? '#E53E3E' : '#4A5568';
    const alpha = isDimmed ? 0.15 : 1;

    ctx.globalAlpha = alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = isActive ? 2.5 : 1.5;
    ctx._bg = '#F0F7FF';

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.bezierCurveTo(cx, y1, cx, y2, x2, y2);
    ctx.stroke();

    const startAngle = Math.atan2(y2-y1, x2-x1);
    const endAngle   = Math.atan2(y1-y2, x1-x2);
    drawSymbol(ctx, x1, y1, endAngle,   rel.from_card, rel.from_opt);
    drawSymbol(ctx, x2, y2, startAngle, rel.to_card,   rel.to_opt);

    ctx.globalAlpha = 1;

    // Store path for hit detection
    linePaths.push({idx, x1, y1, x2, y2, cx});
  });
}

// Hit detection: check if click is near a bezier curve
function pointNearBezier(mx, my, x1, y1, cx, y2, x2, threshold=12) {
  for (let t=0; t<=1; t+=0.02) {
    const bx = (1-t)**3*x1 + 3*(1-t)**2*t*cx + 3*(1-t)*t**2*cx + t**3*x2;
    const by = (1-t)**3*y1 + 3*(1-t)**2*t*y1 + 3*(1-t)*t**2*y2 + t**3*y2;
    if (Math.hypot(mx-bx, my-by) < threshold) return true;
  }
  return false;
}

function highlightRelation(idx) {
  // Clear previous highlights
  document.querySelectorAll('.col.highlighted').forEach(el => el.classList.remove('highlighted'));
  document.querySelectorAll('.card').forEach(el => el.classList.remove('dimmed'));

  if (idx === null) { activeRel=null; drawLines(); return; }

  activeRel = idx;
  const rel = RELATIONS[idx];
  const ep  = computeEndpoints(rel);

  // Highlight FK and PK columns
  if (ep.toFK) {
    const el = document.getElementById('col-'+rel.to+'-'+ep.toFK);
    if (el) el.classList.add('highlighted');
  }
  if (ep.fromPK) {
    const el = document.getElementById('col-'+rel.from+'-'+ep.fromPK);
    if (el) el.classList.add('highlighted');
  }

  // Dim unrelated tables
  const related = new Set([rel.from, rel.to]);
  document.querySelectorAll('.card').forEach(card => {
    const name = card.id.replace('c-','');
    if (!related.has(name)) card.classList.add('dimmed');
  });

  drawLines();

  // Show tooltip
  const ep2 = computeEndpoints(rel);
  const tooltip = document.getElementById('tooltip');
  const label = `${rel.to}.${ep.toFK||'?'} → ${rel.from}.${ep.fromPK||'id'}  (${rel.from_card}:${rel.to_card})`;
  tooltip.textContent = label;
  tooltip.style.display = 'block';
}

// Canvas click handler (in stage coordinates)
const wrap = document.getElementById('wrap');
wrap.addEventListener('click', e => {
  if (dragging) return;
  const r = wrap.getBoundingClientRect();
  const mx = (e.clientX - r.left - px) / scale;
  const my = (e.clientY - r.top  - py) / scale;

  let hit = null;
  for (const lp of linePaths) {
    if (pointNearBezier(mx, my, lp.x1, lp.y1, lp.cx, lp.y2, lp.x2)) {
      hit = lp.idx; break;
    }
  }

  if (hit !== null) {
    highlightRelation(hit === activeRel ? null : hit);
  } else if (activeRel !== null) {
    highlightRelation(null);
    document.getElementById('tooltip').style.display='none';
  }
});

window.addEventListener('mousemove', e => {
  const r = wrap.getBoundingClientRect();
  const tooltip = document.getElementById('tooltip');
  if (tooltip.style.display === 'block') {
    tooltip.style.left = (e.clientX+14)+'px';
    tooltip.style.top  = (e.clientY-10)+'px';
  }
});

// Pan & Zoom
wrap.addEventListener('wheel', e => {
  e.preventDefault();
  const d=e.deltaY>0?0.9:1.1, ns=Math.min(Math.max(scale*d,0.1),4);
  const r=wrap.getBoundingClientRect();
  px=e.clientX-r.left-(e.clientX-r.left-px)*(ns/scale);
  py=e.clientY-r.top-(e.clientY-r.top-py)*(ns/scale);
  scale=ns; applyT();
}, {passive:false});

wrap.addEventListener('mousedown', e => {
  if (!dragging) { panning=true; lmx=e.clientX; lmy=e.clientY; }
});

window.addEventListener('mousemove', e => {
  if (panning) { px+=e.clientX-lmx; py+=e.clientY-lmy; lmx=e.clientX; lmy=e.clientY; applyT(); }
  if (dragging) {
    pos[dragging].x=e.clientX/scale-dox; pos[dragging].y=e.clientY/scale-doy;
    const c=document.getElementById('c-'+dragging);
    c.style.left=pos[dragging].x+'px'; c.style.top=pos[dragging].y+'px';
    drawLines();
  }
});

window.addEventListener('mouseup', () => {
  panning=false; dragging=null;
  document.querySelectorAll('.card').forEach(c=>c.style.zIndex='1');
});

function applyT() {
  document.getElementById('stage').style.transform=`translate(${px}px,${py}px) scale(${scale})`;
}

initPos(); buildCards(); drawLines(); applyT();
</script>
</body>
</html>"""

def build_html(tables, relations, title):
    return HTML.replace('{title}', title) \
               .replace('{tables_json}', json.dumps(tables, ensure_ascii=False)) \
               .replace('{relations_json}', json.dumps(relations, ensure_ascii=False))

def main():
    if len(sys.argv) < 2:
        print("用法: python3 schema_to_html.py <schema.prisma 或 schema.sql> [-o output.html]")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "-o" else None
    if not os.path.exists(input_path):
        print(f"找不到檔案: {input_path}"); sys.exit(1)
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()
    ext = os.path.splitext(input_path)[1].lower()
    tables, relations = detect_and_parse(content, ext)
    if not tables:
        print("找不到任何 table 定義"); sys.exit(1)
    title = os.path.splitext(os.path.basename(input_path))[0]
    html = build_html(tables, relations, title)
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已產生: {output_path} ({len(tables)} tables, {len(relations)} relations)")

if __name__ == "__main__":
    main()

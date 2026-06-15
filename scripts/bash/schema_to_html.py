#!/usr/bin/env python3
"""
schema_to_html.py — 從 Prisma schema 或 SQL 產出可拖曳的 ERD HTML

用法:
    python3 schema_to_html.py <schema.prisma>
    python3 schema_to_html.py <schema.sql>
    python3 schema_to_html.py <schema.prisma> -o output.html
"""

import sys, re, os, json

# ── Parsers ───────────────────────────────────────────────────────

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
            if not line or line.startswith('//') or line.startswith('@@'):
                continue
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
            if is_array:
                relations.append({"from":model_name,"symbol":"||--o{","to":ftype,"label":fname})
            else:
                relations.append({"from":ftype,"symbol":"|o--o{" if mod=="?" else "||--o{","to":model_name,"label":fname})
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
                relations.append({"from":m.group(2),"symbol":"||--o{","to":table_name,"label":m.group(1)})
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

# ── HTML ──────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:'Segoe UI',Arial,sans-serif; background:#F0F7FF; overflow:hidden; }}

#wrap {{ position:fixed; inset:0; overflow:hidden; cursor:grab; }}
#wrap:active {{ cursor:grabbing; }}
#stage {{ position:absolute; transform-origin:0 0; }}
svg#lines {{ position:absolute; top:0; left:0; pointer-events:none; width:5000px; height:4000px; }}

.card {{
  position:absolute; width:280px; border-radius:8px; overflow:hidden;
  box-shadow:0 3px 12px #0002; border:1.5px solid #BEE3F8;
  background:#fff; cursor:grab;
}}
.card:active {{ cursor:grabbing; }}
.card-head {{
  background:#1A365D; color:#fff; font-weight:bold;
  font-size:13px; padding:8px 12px; text-align:center;
}}
.col {{ display:flex; align-items:center; padding:3px 8px; min-height:26px; border-bottom:1px solid #EBF8FF; font-size:11px; }}
.col:last-child {{ border-bottom:none; }}
.col:nth-child(odd) {{ background:#F7FBFF; }}
.badge {{
  font-size:9px; font-weight:bold; padding:1px 5px; border-radius:3px;
  margin-right:6px; white-space:nowrap;
}}
.pk  {{ background:#FED7D7; color:#C53030; }}
.fk  {{ background:#BEE3F8; color:#2B6CB0; }}
.uk  {{ background:#C6F6D5; color:#276749; }}
.pkfk{{ background:#E9D8FD; color:#553C9A; }}
.col-name {{ flex:1; color:#2D3748; }}
.col-type {{ color:#718096; font-size:10px; }}
</style>
</head>
<body>
<div id="wrap">
  <div id="stage">
    <svg id="lines"><defs>
      <marker id="m-many" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
        <path d="M1,1 L10,6 L1,11" fill="none" stroke="#4A90D9" stroke-width="1.8"/>
        <line x1="5" y1="1" x2="5" y2="11" stroke="#4A90D9" stroke-width="1.8"/>
      </marker>
      <marker id="m-one" markerWidth="10" markerHeight="12" refX="8" refY="6" orient="auto">
        <line x1="4" y1="1" x2="4" y2="11" stroke="#4A90D9" stroke-width="1.8"/>
        <line x1="8" y1="1" x2="8" y2="11" stroke="#4A90D9" stroke-width="1.8"/>
      </marker>
    </defs></svg>
  </div>
</div>
<script>
const TABLES = {tables_json};
const RELATIONS = {relations_json};
const TW=280, TH=34, CH=26, COLS=4, PX=90, PY=70;
const pos = {{}};
let scale=1, px=40, py=40;
let panning=false, lmx=0, lmy=0;
let dragging=null, dox=0, doy=0;

function th(name) {{ return TH + (TABLES[name]||[]).length * CH; }}

function initPos() {{
  Object.keys(TABLES).forEach((n,i) => {{
    pos[n] = {{ x: (i%COLS)*(TW+PX)+60, y: Math.floor(i/COLS)*550+60 }};
  }});
}}

function badge(c) {{
  if (!c) return '';
  const cls = c==='PK,FK'?'pkfk':c.toLowerCase();
  return `<span class="badge ${{cls}}">${{c}}</span>`;
}}

function buildCards() {{
  const stage = document.getElementById('stage');
  Object.entries(TABLES).forEach(([name, cols]) => {{
    const d = document.createElement('div');
    d.className='card'; d.id='c-'+name;
    d.style.left=pos[name].x+'px'; d.style.top=pos[name].y+'px';
    let h=`<div class="card-head">${{name}}</div>`;
    cols.forEach(c => {{
      const ann = c.annotation ? ` (${{c.annotation}})` : '';
      h += `<div class="col">${{badge(c.constraint)}}<span class="col-name">${{c.name}}</span><span class="col-type">${{c.type}}${{ann}}</span></div>`;
    }});
    d.innerHTML=h;
    d.addEventListener('mousedown', e => {{
      dragging=name; dox=e.clientX/scale-pos[name].x; doy=e.clientY/scale-pos[name].y;
      d.style.zIndex=99; e.stopPropagation();
    }});
    stage.appendChild(d);
  }});
}}

function drawLines() {{
  const svg = document.getElementById('lines');
  // remove old paths/labels
  svg.querySelectorAll('.rel').forEach(e=>e.remove());
  RELATIONS.forEach(rel => {{
    const s=pos[rel.from], t=pos[rel.to];
    if (!s||!t) return;
    const sh=th(rel.from), tth=th(rel.to);
    let x1,y1,x2,y2;
    if (s.x+TW+10<t.x)      {{ x1=s.x+TW; y1=s.y+sh/2; x2=t.x;    y2=t.y+tth/2; }}
    else if (t.x+TW+10<s.x) {{ x1=s.x;    y1=s.y+sh/2; x2=t.x+TW; y2=t.y+tth/2; }}
    else if (s.y+sh+10<t.y) {{ x1=s.x+TW/2; y1=s.y+sh; x2=t.x+TW/2; y2=t.y; }}
    else                     {{ x1=s.x+TW/2; y1=s.y;    x2=t.x+TW/2; y2=t.y+tth; }}
    const cx=(x1+x2)/2;
    const sym=rel.symbol||'||--o{{';
    const sm=sym.startsWith('|o')?'m-one':'m-one';
    const em=sym.endsWith('o{{')?'m-many':'m-one';
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');
    g.className.baseVal='rel';
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d',`M${{x1}},${{y1}} C${{cx}},${{y1}} ${{cx}},${{y2}} ${{x2}},${{y2}}`);
    p.setAttribute('fill','none'); p.setAttribute('stroke','#4A90D9');
    p.setAttribute('stroke-width','1.5'); p.setAttribute('stroke-dasharray','6,3');
    p.setAttribute('marker-start',`url(#${{sm}})`); p.setAttribute('marker-end',`url(#${{em}})`);
    g.appendChild(p);
    const lx=(x1+x2)/2, ly=(y1+y2)/2;
    const lw=rel.label.length*7+12;
    const bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
    bg.setAttribute('x',lx-lw/2); bg.setAttribute('y',ly-12);
    bg.setAttribute('width',lw); bg.setAttribute('height',16);
    bg.setAttribute('rx',4); bg.setAttribute('fill','#EBF8FF'); bg.setAttribute('stroke','#BEE3F8');
    g.appendChild(bg);
    const lt=document.createElementNS('http://www.w3.org/2000/svg','text');
    lt.setAttribute('x',lx); lt.setAttribute('y',ly);
    lt.setAttribute('text-anchor','middle'); lt.setAttribute('fill','#2C5282');
    lt.setAttribute('font-size','10'); lt.setAttribute('font-family',"'Segoe UI',Arial,sans-serif");
    lt.textContent=rel.label;
    g.appendChild(lt);
    svg.appendChild(g);
  }});
}}

function applyT() {{
  document.getElementById('stage').style.transform=`translate(${{px}}px,${{py}}px) scale(${{scale}})`;
}}

const wrap=document.getElementById('wrap');
wrap.addEventListener('wheel',e=>{{
  e.preventDefault();
  const d=e.deltaY>0?0.9:1.1, ns=Math.min(Math.max(scale*d,0.15),3);
  const r=wrap.getBoundingClientRect();
  px=e.clientX-r.left-(e.clientX-r.left-px)*(ns/scale);
  py=e.clientY-r.top-(e.clientY-r.top-py)*(ns/scale);
  scale=ns; applyT();
}},{{passive:false}});

wrap.addEventListener('mousedown',e=>{{
  if (!dragging) {{ panning=true; lmx=e.clientX; lmy=e.clientY; }}
}});

window.addEventListener('mousemove',e=>{{
  if (panning) {{ px+=e.clientX-lmx; py+=e.clientY-lmy; lmx=e.clientX; lmy=e.clientY; applyT(); }}
  if (dragging) {{
    pos[dragging].x=e.clientX/scale-dox; pos[dragging].y=e.clientY/scale-doy;
    const c=document.getElementById('c-'+dragging);
    c.style.left=pos[dragging].x+'px'; c.style.top=pos[dragging].y+'px';
    drawLines();
  }}
}});

window.addEventListener('mouseup',()=>{{
  panning=false; dragging=null;
  document.querySelectorAll('.card').forEach(c=>c.style.zIndex='');
}});

initPos(); buildCards(); drawLines(); applyT();
</script>
</body>
</html>"""

def build_html(tables, relations, title):
    return HTML.format(
        title=title,
        tables_json=json.dumps(tables, ensure_ascii=False),
        relations_json=json.dumps(relations, ensure_ascii=False)
    )

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

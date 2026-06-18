#!/usr/bin/env python3
"""architecture_to_html.py — architecture.md YAML → Interactive System Architecture HTML"""
import sys, os, json, re
try:
    import yaml
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "--break-system-packages", "-q"])
    import yaml

COMPONENT_COLORS = {
    "gateway":  {"head": "#744210", "border": "#F6AD55", "badge_bg": "#FEEBC8", "badge_fg": "#744210"},
    "service":  {"head": "#1A365D", "border": "#BEE3F8", "badge_bg": "#EBF8FF", "badge_fg": "#2B6CB0"},
    "database": {"head": "#276749", "border": "#C6F6D5", "badge_bg": "#F0FFF4", "badge_fg": "#276749"},
    "cache":    {"head": "#553C9A", "border": "#E9D8FD", "badge_bg": "#FAF5FF", "badge_fg": "#553C9A"},
    "queue":    {"head": "#702459", "border": "#FED7E2", "badge_bg": "#FFF5F7", "badge_fg": "#702459"},
    "external": {"head": "#4A5568", "border": "#E2E8F0", "badge_bg": "#F7FAFC", "badge_fg": "#4A5568"},
}

PROTOCOL_COLORS = {
    "HTTP":   "#E53E3E",
    "REST":   "#3182CE",
    "AMQP":   "#805AD5",
    "TCP":    "#2F855A",
    "GRPC":   "#C05621",
    "WS":     "#00B5D8",
    "OTHER":  "#718096",
}

def parse_architecture(content):
    # Extract YAML block from markdown
    yaml_match = re.search(r'```yaml\s*(components:.*?)```', content, re.DOTALL)
    if yaml_match:
        raw = yaml_match.group(1)
    else:
        # Try to parse entire content as YAML
        raw = content

    data = yaml.safe_load(raw)
    components = data.get("components", [])
    data_flows = data.get("data_flows", [])

    nodes = {}
    for c in components:
        name = c.get("name", "Unknown")
        nodes[name] = {
            "type": c.get("type", "service").lower(),
            "responsibilities": c.get("responsibilities", []),
            "communicates_with": c.get("communicates_with", []),
            "protocol": c.get("protocol", "HTTP"),
        }

    edges = []
    seen = set()
    for f in data_flows:
        frm = f.get("from", "")
        to = f.get("to", "")
        protocol = f.get("protocol", f.get("trigger", "HTTP"))
        trigger = f.get("trigger", "")
        key = (frm, to)
        if key not in seen:
            seen.add(key)
            edges.append({"from": frm, "to": to, "protocol": protocol, "trigger": trigger})

    return nodes, edges


HTML = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Segoe UI',Arial,sans-serif; background:#1A202C; overflow:hidden; }
#wrap { position:fixed; inset:0; overflow:hidden; cursor:grab; }
#wrap:active { cursor:grabbing; }
#stage { position:absolute; transform-origin:0 0; }
canvas#lines { position:absolute; top:0; left:0; pointer-events:none; }

.card {
  position:absolute; width:240px;
  border-radius:10px; overflow:hidden;
  box-shadow:0 4px 16px #0004;
  cursor:grab; z-index:1;
  transition: opacity 0.2s, box-shadow 0.2s;
}
.card:active { cursor:grabbing; }
.card.dimmed { opacity:0.2; }
.card.active { box-shadow:0 0 0 3px #F6E05E, 0 4px 20px #0006; }

.card-head {
  color:#fff; font-weight:bold; font-size:12px;
  padding:8px 12px; text-align:center;
  display:flex; flex-direction:column; align-items:center; gap:3px;
}
.card-type-badge {
  font-size:9px; font-weight:normal; opacity:0.8;
  background:#ffffff22; padding:1px 6px; border-radius:10px;
  text-transform:uppercase; letter-spacing:0.5px;
}
.card-body { background:#2D3748; padding:6px 0; }
.resp-item {
  font-size:10px; color:#A0AEC0;
  padding:3px 12px;
  border-bottom:1px solid #3A4A5C;
}
.resp-item:last-child { border-bottom:none; }
.resp-dot { display:inline-block; width:5px; height:5px; border-radius:50%; background:#4A5568; margin-right:6px; }

#tooltip {
  position:fixed; background:#2D3748; color:#E2E8F0;
  font-size:11px; padding:6px 10px; border-radius:6px;
  pointer-events:none; display:none; z-index:999;
  border:1px solid #4A5568; white-space:nowrap;
  box-shadow:0 2px 8px #0004;
}

#legend {
  position:fixed; top:16px; right:16px;
  background:#2D3748; border:1px solid #4A5568;
  border-radius:8px; padding:12px 16px; z-index:100;
  font-size:11px; color:#A0AEC0;
}
#legend h4 { color:#E2E8F0; margin-bottom:8px; font-size:12px; }
.legend-row { display:flex; align-items:center; gap:8px; margin-bottom:4px; }
.legend-color { width:12px; height:12px; border-radius:3px; }
.legend-line { width:24px; height:2px; }

#hint {
  position:fixed; bottom:16px; left:50%; transform:translateX(-50%);
  background:#2D3748; color:#90CDF4; font-size:11px;
  padding:5px 14px; border-radius:20px; pointer-events:none;
  z-index:999; border:1px solid #4A5568;
}
</style>
</head>
<body>
<div id="wrap">
  <div id="stage">
    <canvas id="lines" width="10000" height="8000"></canvas>
  </div>
</div>
<div id="tooltip"></div>
<div id="legend">
  <h4>元件類型</h4>
  {legend_components}
  <h4 style="margin-top:10px;">通訊協定</h4>
  {legend_protocols}
</div>
<div id="hint">點選連線查看詳情 · 滾輪縮放 · 拖曳移動</div>
<script>
const NODES = {nodes_json};
const EDGES = {edges_json};
const COLORS = {colors_json};
const PROTO_COLORS = {proto_colors_json};

const TW = 240;
const COLS = 4;
const PX = 140, PY = 100;

const pos = {};
let scale = 1, px = 80, py = 60;
let panning = false, lmx = 0, lmy = 0;
let dragging = null, dox = 0, doy = 0;
let activeEdge = null;
const linePaths = [];

function cardH(name) {
  const n = NODES[name];
  if (!n) return 80;
  return 56 + (n.responsibilities || []).length * 22;
}

function buildLegend() {}

function initPos() {
  const names = Object.keys(NODES);
  // Group by type for better layout
  const typeOrder = ["gateway","service","database","cache","queue","external"];
  const grouped = {};
  typeOrder.forEach(t => grouped[t] = []);
  names.forEach(n => {
    const t = NODES[n].type;
    (grouped[t] || (grouped["external"] = grouped["external"] || []));
    (grouped[t] || grouped["external"]).push(n);
  });

  let col = 0, row = 0;
  typeOrder.forEach(type => {
    (grouped[type] || []).forEach(name => {
      pos[name] = { x: col * (TW + PX) + 60, y: row * 220 + 60 };
      col++;
      if (col >= COLS) { col = 0; row++; }
    });
  });
}

function buildCards() {
  const stage = document.getElementById('stage');
  Object.entries(NODES).forEach(([name, node]) => {
    const color = COLORS[node.type] || COLORS["service"];
    const d = document.createElement('div');
    d.className = 'card'; d.id = 'c-' + name;
    d.style.left = pos[name].x + 'px';
    d.style.top  = pos[name].y + 'px';
    d.style.border = '1.5px solid ' + color.border;

    const resps = (node.responsibilities || [])
      .map(r => `<div class="resp-item"><span class="resp-dot" style="background:${color.border}"></span>${r}</div>`)
      .join('');

    d.innerHTML = `
      <div class="card-head" style="background:${color.head}">
        <div>${name}</div>
        <div class="card-type-badge">${node.type}</div>
      </div>
      <div class="card-body">${resps}</div>
    `;

    d.addEventListener('mousedown', e => {
      dragging = name;
      dox = e.clientX / scale - pos[name].x;
      doy = e.clientY / scale - pos[name].y;
      d.style.zIndex = 99;
      e.stopPropagation();
    });
    stage.appendChild(d);
  });
}

function cardCenter(name) {
  const p = pos[name];
  if (!p) return null;
  return { x: p.x + TW / 2, y: p.y + cardH(name) / 2 };
}

function cardEdgePoint(name, toward) {
  const p = pos[name];
  const h = cardH(name);
  const cx = p.x + TW / 2, cy = p.y + h / 2;
  const tx = pos[toward].x + TW / 2, ty = pos[toward].y + cardH(toward) / 2;
  const dx = tx - cx, dy = ty - cy;
  const absDx = Math.abs(dx), absDy = Math.abs(dy);

  if (absDx / TW > absDy / h) {
    // Exit left or right
    return dx > 0
      ? { x: p.x + TW, y: cy }
      : { x: p.x,      y: cy };
  } else {
    // Exit top or bottom
    return dy > 0
      ? { x: cx, y: p.y + h }
      : { x: cx, y: p.y     };
  }
}

function drawArrow(ctx, x, y, angle, color) {
  const len = 10, width = 5;
  ctx.save();
  ctx.fillStyle = color;
  ctx.translate(x, y);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-len, -width);
  ctx.lineTo(-len,  width);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawLines() {
  const canvas = document.getElementById('lines');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  linePaths.length = 0;

  EDGES.forEach((edge, idx) => {
    if (!pos[edge.from] || !pos[edge.to]) return;

    const p1 = cardEdgePoint(edge.from, edge.to);
    const p2 = cardEdgePoint(edge.to,   edge.from);

    const isActive = activeEdge === idx;
    const isDimmed = activeEdge !== null && !isActive;

    const protoKey = (edge.protocol || "OTHER").toUpperCase().split("/")[0];
    const baseColor = PROTO_COLORS[protoKey] || PROTO_COLORS["OTHER"];

    ctx.globalAlpha = isDimmed ? 0.12 : (isActive ? 1 : 0.75);
    ctx.strokeStyle = baseColor;
    ctx.lineWidth   = isActive ? 2.5 : 1.5;

    if (isActive) {
      ctx.setLineDash([]);
    } else {
      ctx.setLineDash([5, 3]);
    }

    const cx = (p1.x + p2.x) / 2;
    const cy = (p1.y + p2.y) / 2;

    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.bezierCurveTo(cx, p1.y, cx, p2.y, p2.x, p2.y);
    ctx.stroke();
    ctx.setLineDash([]);

    // Arrow at destination
    const angle = Math.atan2(p2.y - cy, p2.x - cx);
    drawArrow(ctx, p2.x, p2.y, angle, baseColor);

    // Protocol label on active
    if (isActive) {
      ctx.globalAlpha = 1;
      ctx.font = 'bold 11px Segoe UI, Arial';
      ctx.fillStyle = baseColor;
      ctx.textAlign = 'center';
      ctx.fillText(edge.protocol, cx, Math.min(p1.y, p2.y) - 6);
    }

    ctx.globalAlpha = 1;
    linePaths.push({ idx, p1, p2, cx, cy: (p1.y + p2.y) / 2 });
  });
}

function pointNearBezier(mx, my, p1, p2, cx) {
  for (let t = 0; t <= 1; t += 0.02) {
    const bx = (1-t)**3*p1.x + 3*(1-t)**2*t*cx + 3*(1-t)*t**2*cx + t**3*p2.x;
    const by = (1-t)**3*p1.y + 3*(1-t)**2*t*p1.y + 3*(1-t)*t**2*p2.y + t**3*p2.y;
    if (Math.hypot(mx - bx, my - by) < 12) return true;
  }
  return false;
}

function highlightEdge(idx) {
  document.querySelectorAll('.card').forEach(el => {
    el.classList.remove('dimmed', 'active');
  });

  if (idx === null) {
    activeEdge = null;
    drawLines();
    document.getElementById('tooltip').style.display = 'none';
    return;
  }

  activeEdge = idx;
  const edge = EDGES[idx];
  const related = new Set([edge.from, edge.to]);

  document.querySelectorAll('.card').forEach(card => {
    const name = card.id.replace('c-', '');
    if (!related.has(name)) card.classList.add('dimmed');
    else card.classList.add('active');
  });

  drawLines();

  const tooltip = document.getElementById('tooltip');
  const trigger = edge.trigger ? ` — ${edge.trigger}` : '';
  tooltip.textContent = `${edge.from} → ${edge.to}  [${edge.protocol}]${trigger}`;
  tooltip.style.display = 'block';
}

// Events
const wrap = document.getElementById('wrap');

wrap.addEventListener('click', e => {
  if (dragging) return;
  const r = wrap.getBoundingClientRect();
  const mx = (e.clientX - r.left - px) / scale;
  const my = (e.clientY - r.top  - py) / scale;

  let hit = null;
  for (const lp of linePaths) {
    if (pointNearBezier(mx, my, lp.p1, lp.p2, lp.cx)) { hit = lp.idx; break; }
  }

  if (hit !== null) {
    highlightEdge(hit === activeEdge ? null : hit);
  } else if (activeEdge !== null) {
    highlightEdge(null);
  }
});

window.addEventListener('mousemove', e => {
  const tooltip = document.getElementById('tooltip');
  if (tooltip.style.display === 'block') {
    tooltip.style.left = (e.clientX + 14) + 'px';
    tooltip.style.top  = (e.clientY - 10) + 'px';
  }
  if (panning) {
    px += e.clientX - lmx; py += e.clientY - lmy;
    lmx = e.clientX; lmy = e.clientY; applyT();
  }
  if (dragging) {
    pos[dragging].x = e.clientX / scale - dox;
    pos[dragging].y = e.clientY / scale - doy;
    const c = document.getElementById('c-' + dragging);
    c.style.left = pos[dragging].x + 'px';
    c.style.top  = pos[dragging].y + 'px';
    drawLines();
  }
});

wrap.addEventListener('mousedown', e => {
  if (!dragging) { panning = true; lmx = e.clientX; lmy = e.clientY; }
});

window.addEventListener('mouseup', () => {
  panning = false; dragging = null;
  document.querySelectorAll('.card').forEach(c => c.style.zIndex = '1');
});

wrap.addEventListener('wheel', e => {
  e.preventDefault();
  const d = e.deltaY > 0 ? 0.9 : 1.1;
  const ns = Math.min(Math.max(scale * d, 0.1), 4);
  const r = wrap.getBoundingClientRect();
  px = e.clientX - r.left - (e.clientX - r.left - px) * (ns / scale);
  py = e.clientY - r.top  - (e.clientY - r.top  - py) * (ns / scale);
  scale = ns; applyT();
}, { passive: false });

function applyT() {
  document.getElementById('stage').style.transform =
    `translate(${px}px,${py}px) scale(${scale})`;
}

initPos(); buildCards(); drawLines(); applyT();
</script>
</body>
</html>"""

def build_legend_html(colors, proto_colors):
    comp_rows = ""
    for ctype, c in colors.items():
        comp_rows += f'<div class="legend-row"><div class="legend-color" style="background:{c["head"]}"></div><span>{ctype}</span></div>\n'

    proto_rows = ""
    for proto, color in proto_colors.items():
        proto_rows += f'<div class="legend-row"><div class="legend-line" style="background:{color}"></div><span>{proto}</span></div>\n'

    return comp_rows, proto_rows

def build_html(nodes, edges, title):
    comp_legend, proto_legend = build_legend_html(COMPONENT_COLORS, PROTOCOL_COLORS)
    return (HTML
        .replace('{title}', title)
        .replace('{nodes_json}', json.dumps(nodes, ensure_ascii=False))
        .replace('{edges_json}', json.dumps(edges, ensure_ascii=False))
        .replace('{colors_json}', json.dumps(COMPONENT_COLORS, ensure_ascii=False))
        .replace('{proto_colors_json}', json.dumps(PROTOCOL_COLORS, ensure_ascii=False))
        .replace('{legend_components}', comp_legend)
        .replace('{legend_protocols}', proto_legend)
    )

def main():
    if len(sys.argv) < 2:
        print("用法: python3 architecture_to_html.py <architecture.md> [-o output.html]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "-o" else None

    if not os.path.exists(input_path):
        print(f"找不到檔案: {input_path}"); sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    nodes, edges = parse_architecture(content)

    if not nodes:
        print("找不到任何元件定義，請確認 YAML 區塊格式正確"); sys.exit(1)

    title = os.path.splitext(os.path.basename(input_path))[0]
    html = build_html(nodes, edges, title)

    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"已產生: {output_path} ({len(nodes)} 元件, {len(edges)} 連線)")

if __name__ == "__main__":
    main()

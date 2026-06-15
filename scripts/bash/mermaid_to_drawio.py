#!/usr/bin/env python3
"""
mermaid_to_drawio.py — 將 erd-*.md 裡的 Mermaid ERD 轉成 .drawio 格式

用法:
    python3 mermaid_to_drawio.py <erd-file.md>

例如:
    python3 mermaid_to_drawio.py docs/specs/project/erd-smt-factory-console.md
"""

import sys
import re
import os
import xml.etree.ElementTree as ET

# ── 解析 Mermaid ────────────────────────────────────────────────

def extract_mermaid(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = r"```mermaid\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        print(f"找不到 Mermaid 區塊: {md_path}")
        sys.exit(1)
    return matches[0].strip()

def parse_mermaid(mermaid_code):
    tables = {}     # name -> list of (constraint, col_name, col_type)
    relations = []  # list of (from, rel, to, label)

    lines = mermaid_code.splitlines()
    current_table = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("erDiagram"):
            continue

        # Table start
        table_match = re.match(r'^(\w+)\s*\{', line)
        if table_match:
            current_table = table_match.group(1)
            tables[current_table] = []
            continue

        # Table end
        if line == "}":
            current_table = None
            continue

        # Column inside table
        if current_table:
            # e.g. string id PK
            # e.g. string roleId "PK,FK"
            # e.g. string lineScope "json"
            col_match = re.match(r'(\w+)\s+(\w+)(?:\s+(PK|FK|UK|"[^"]*"))?(?:\s+"([^"]*)")?', line)
            if col_match:
                col_type = col_match.group(1)
                col_name = col_match.group(2)
                constraint = col_match.group(3) or ""
                annotation = col_match.group(4) or ""
                # clean up constraint quotes
                constraint = constraint.strip('"')
                if annotation:
                    col_type = f'{col_type} "{annotation}"'
                tables[current_table].append((constraint, col_name, col_type))
            continue

        # Relation
        rel_match = re.match(r'(\w+)\s+([|o}{]+--[|o}{]+)\s+(\w+)\s*:\s*"?([^"]*)"?', line)
        if rel_match:
            relations.append((
                rel_match.group(1),
                rel_match.group(2),
                rel_match.group(3),
                rel_match.group(4).strip()
            ))

    return tables, relations

# ── 產生 Draw.io XML ────────────────────────────────────────────

CELL_W = 240
COL_H = 28
HEADER_H = 32
PADDING_X = 60
PADDING_Y = 60
COLS_PER_ROW = 4

def mermaid_rel_to_drawio(rel_symbol):
    mapping = {
        "||--||": ("ERmandOne", "ERmandOne"),
        "||--o{": ("ERmandOne", "ERmanyToOne"),
        "}o--o{": ("ERmanyToOne", "ERmanyToOne"),
        "|o--o{": ("ERzeroToOne", "ERmanyToOne"),
        "||--o|": ("ERmandOne", "ERzeroToOne"),
    }
    # normalize
    sym = rel_symbol.replace(" ", "")
    return mapping.get(sym, ("ERmandOne", "ERmanyToOne"))

def build_drawio(tables, relations):
    uid = [10]  # mutable counter

    def next_id():
        uid[0] += 1
        return str(uid[0])

    root_el = ET.Element("mxGraphModel")
    root_node = ET.SubElement(root_el, "root")

    ET.SubElement(root_node, "mxCell", id="0")
    ET.SubElement(root_node, "mxCell", id="1", parent="0")

    table_cell_ids = {}   # table_name -> table mxCell id
    col_row_ids = {}      # (table_name, col_name) -> row mxCell id

    table_names = list(tables.keys())
    positions = {}
    for i, name in enumerate(table_names):
        col = i % COLS_PER_ROW
        row = i // COLS_PER_ROW
        x = col * (CELL_W + PADDING_X) + 40
        y = row * (400 + PADDING_Y) + 40
        positions[name] = (x, y)

    for tname, cols in tables.items():
        tid = next_id()
        table_cell_ids[tname] = tid
        x, y = positions[tname]
        total_h = HEADER_H + len(cols) * COL_H

        tbl = ET.SubElement(root_node, "mxCell",
            id=tid,
            value=tname,
            style="shape=table;startSize=32;container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;fontSize=13;",
            vertex="1",
            parent="1"
        )
        ET.SubElement(tbl, "mxGeometry",
            x=str(x), y=str(y),
            width=str(CELL_W), height=str(total_h),
            **{"as": "geometry"}
        )

        for idx, (constraint, col_name, col_type) in enumerate(cols):
            row_id = next_id()
            col_row_ids[(tname, col_name)] = row_id
            row_y = HEADER_H + idx * COL_H

            row_cell = ET.SubElement(root_node, "mxCell",
                id=row_id,
                value="",
                style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;top=0;left=0;right=0;bottom=1;",
                vertex="1",
                parent=tid
            )
            ET.SubElement(row_cell, "mxGeometry",
                y=str(row_y),
                width=str(CELL_W), height=str(COL_H),
                **{"as": "geometry"}
            )

            # constraint cell
            left_id = next_id()
            left = ET.SubElement(root_node, "mxCell",
                id=left_id,
                value=constraint,
                style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontStyle=1;overflow=hidden;fontSize=11;",
                vertex="1",
                parent=row_id
            )
            ET.SubElement(left, "mxGeometry",
                width="50", height=str(COL_H),
                **{"as": "geometry"}
            )

            # column name + type cell
            right_id = next_id()
            right = ET.SubElement(root_node, "mxCell",
                id=right_id,
                value=f"{col_name} ({col_type})",
                style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=11;",
                vertex="1",
                parent=row_id
            )
            ET.SubElement(right, "mxGeometry",
                x="50", width=str(CELL_W - 50), height=str(COL_H),
                **{"as": "geometry"}
            )

    # Relations
    for (src, sym, tgt, label) in relations:
        start_arrow, end_arrow = mermaid_rel_to_drawio(sym)

        # connect table-level cells
        src_id = table_cell_ids.get(src)
        tgt_id = table_cell_ids.get(tgt)
        if not src_id or not tgt_id:
            continue

        eid = next_id()
        edge = ET.SubElement(root_node, "mxCell",
            id=eid,
            value=label,
            style=f"edgeStyle=entityRelationEdgeStyle;endArrow={end_arrow};startArrow={start_arrow};exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;fontSize=11;",
            edge="1",
            source=src_id,
            target=tgt_id,
            parent="1"
        )
        ET.SubElement(edge, "mxGeometry", relative="1", **{"as": "geometry"})

    return ET.tostring(root_el, encoding="unicode", xml_declaration=False)

# ── Main ────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法: python3 mermaid_to_drawio.py <erd-file.md>")
        sys.exit(1)

    md_path = sys.argv[1]
    if not os.path.exists(md_path):
        print(f"找不到檔案: {md_path}")
        sys.exit(1)

    mermaid_code = extract_mermaid(md_path)
    tables, relations = parse_mermaid(mermaid_code)
    xml_content = build_drawio(tables, relations)

    output_path = md_path.replace(".md", ".drawio")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_content)

    print(f"已產生: {output_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Update date columns in an .xlsx workbook using only the Python stdlib."""

from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import re
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"main": SPREADSHEET_NS, "rel": REL_NS}
HEADER_ROW_INDEX = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Update one row of an Excel sheet by matching column headers "
            "and writing new Target Start/End Date values."
        )
    )
    parser.add_argument("workbook", help="Path to the .xlsx workbook to edit")
    parser.add_argument(
        "--sheet",
        default="Sheet1",
        help="Worksheet name to update (default: Sheet1)",
    )
    parser.add_argument(
        "--row",
        type=int,
        default=2,
        help="1-based row number to update (default: 2 — the first data row)",
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="New Target Start Date value (parsed with --date-format)",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="New Target End Date value (parsed with --date-format)",
    )
    parser.add_argument(
        "--date-format",
        default="%Y-%m-%d",
        help="datetime.strptime format for parsing the inputs",
    )
    parser.add_argument(
        "--output",
        help="Optional path for the updated workbook. Default: edit in place",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating <workbook>.bak when editing in place",
    )
    return parser.parse_args()


def excel_serial(day: dt.date) -> int:
    """Convert a date into Excel's serial number (1900 date system)."""
    epoch = dt.date(1899, 12, 30)
    return (day - epoch).days


def load_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    try:
        raw = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    tree = ET.fromstring(raw)
    strings: List[str] = []
    for si in tree.findall("main:si", NS):
        text_chunks = [node.text or "" for node in si.findall(".//main:t", NS)]
        strings.append("".join(text_chunks))
    return strings


def resolve_sheet_path(zf: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    sheet_elem = None
    for elem in workbook.findall("main:sheets/main:sheet", NS):
        if elem.attrib.get("name") == sheet_name:
            sheet_elem = elem
            break
    if sheet_elem is None:
        available = [elem.attrib.get("name", "?") for elem in workbook.findall("main:sheets/main:sheet", NS)]
        raise ValueError(f"Worksheet '{sheet_name}' not found. Available: {available}")

    rel_id = sheet_elem.attrib.get(f"{{{REL_NS}}}id")
    if not rel_id:
        raise ValueError(f"Worksheet '{sheet_name}' missing relationship id")

    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    for rel in rels.findall("rel:Relationship", NS):
        if rel.attrib.get("Id") == rel_id:
            target = rel.attrib.get("Target")
            if not target:
                break
            if target.startswith("/"):
                return target.lstrip("/")
            return f"xl/{target}" if not target.startswith("xl/") else target
    raise ValueError(f"Could not resolve sheet path for '{sheet_name}'")


def column_letter(cell_ref: str) -> str:
    match = re.match(r"([A-Z]+)", cell_ref.upper())
    if not match:
        raise ValueError(f"Invalid cell reference '{cell_ref}'")
    return match.group(1)


def column_index(letter: str) -> int:
    idx = 0
    for ch in letter:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx


def read_cell_text(cell: ET.Element, shared_strings: List[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        t_elem = cell.find("main:is/main:t", NS)
        return t_elem.text if t_elem is not None else ""
    value_elem = cell.find("main:v", NS)
    if value_elem is None:
        return ""
    if cell_type == "s":
        idx = int(value_elem.text)
        return shared_strings[idx]
    return value_elem.text or ""


def build_header_map(sheet_root: ET.Element, shared_strings: List[str]) -> Dict[str, str]:
    sheet_data = sheet_root.find("main:sheetData", NS)
    if sheet_data is None:
        raise ValueError("Worksheet is missing <sheetData>")
    header_row = sheet_data.find(f"main:row[@r='{HEADER_ROW_INDEX}']", NS)
    if header_row is None:
        raise ValueError("Worksheet is missing a header row")
    mapping: Dict[str, str] = {}
    for cell in header_row.findall("main:c", NS):
        header = read_cell_text(cell, shared_strings).strip()
        if not header:
            continue
        mapping[header.lower()] = column_letter(cell.attrib.get("r", ""))
    return mapping


def find_or_create_row(sheet_root: ET.Element, row_number: int) -> ET.Element:
    sheet_data = sheet_root.find("main:sheetData", NS)
    if sheet_data is None:
        raise ValueError("Worksheet is missing <sheetData>")
    row = sheet_data.find(f"main:row[@r='{row_number}']", NS)
    if row is not None:
        return row
    row = ET.Element(f"{{{SPREADSHEET_NS}}}row", r=str(row_number))
    sheet_data.append(row)
    return row


def find_or_create_cell(row: ET.Element, column: str, row_number: int) -> ET.Element:
    target_ref = f"{column}{row_number}"
    for cell in row.findall("main:c", NS):
        if cell.attrib.get("r") == target_ref:
            return cell
    cell = ET.Element(f"{{{SPREADSHEET_NS}}}c", r=target_ref)
    row.append(cell)
    # keep cells sorted by column
    row[:] = sorted(row, key=lambda el: column_index(column_letter(el.attrib["r"])))
    return cell


def set_numeric_value(cell: ET.Element, value: int) -> None:
    cell.attrib.pop("t", None)
    v_elem = cell.find("main:v", NS)
    if v_elem is None:
        v_elem = ET.SubElement(cell, f"{{{SPREADSHEET_NS}}}v")
    v_elem.text = str(value)


def update_dates(sheet_root: ET.Element, header_map: Dict[str, str], row_number: int, start_serial: int, end_serial: int) -> None:
    row = find_or_create_row(sheet_root, row_number)
    start_col = header_map.get("target start date")
    end_col = header_map.get("target end date")
    if not start_col or not end_col:
        raise ValueError(
            "Required headers not found. Expected 'Target Start Date' and 'Target End Date'."
        )
    start_cell = find_or_create_cell(row, start_col, row_number)
    end_cell = find_or_create_cell(row, end_col, row_number)
    set_numeric_value(start_cell, start_serial)
    set_numeric_value(end_cell, end_serial)


def write_updated_workbook(zf: zipfile.ZipFile, sheet_path: str, sheet_root: ET.Element, output_path: str) -> None:
    temp_fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(temp_fd)
    try:
        buffer = io.BytesIO()
        ET.ElementTree(sheet_root).write(buffer, encoding="utf-8", xml_declaration=True)
        updated_sheet = buffer.getvalue()
        with zipfile.ZipFile(temp_path, "w") as zout:
            for item in zf.infolist():
                data = updated_sheet if item.filename == sheet_path else zf.read(item.filename)
                zout.writestr(item, data)
        shutil.move(temp_path, output_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def main() -> None:
    args = parse_args()
    workbook_path = os.path.abspath(args.workbook)
    if not os.path.exists(workbook_path):
        raise SystemExit(f"Workbook '{workbook_path}' does not exist")

    parsed_start = dt.datetime.strptime(args.start_date, args.date_format).date()
    parsed_end = dt.datetime.strptime(args.end_date, args.date_format).date()
    start_serial = excel_serial(parsed_start)
    end_serial = excel_serial(parsed_end)

    output_path = os.path.abspath(args.output) if args.output else workbook_path
    if output_path == workbook_path and not args.no_backup:
        backup_path = f"{workbook_path}.bak"
        shutil.copy2(workbook_path, backup_path)
        print(f"Backup saved to {backup_path}")

    with zipfile.ZipFile(workbook_path, "r") as zf:
        shared_strings = load_shared_strings(zf)
        sheet_path = resolve_sheet_path(zf, args.sheet)
        sheet_root = ET.fromstring(zf.read(sheet_path))
        header_map = build_header_map(sheet_root, shared_strings)
        update_dates(sheet_root, header_map, args.row, start_serial, end_serial)
        write_updated_workbook(zf, sheet_path, sheet_root, output_path)

    print(
        "Updated '{sheet}' row {row} in {dest}".format(
            sheet=args.sheet,
            row=args.row,
            dest=output_path,
        )
    )


if __name__ == "__main__":
    ET.register_namespace("", SPREADSHEET_NS)
    main()

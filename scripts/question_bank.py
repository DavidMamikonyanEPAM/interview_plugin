#!/usr/bin/env python3
"""Read the interview question bank (.xlsx) using only the Python standard library.

Commands:
  skills                                  list skills with question counts
  questions --skills A,B [--difficulty Basic,Core]
                                          questions only (no expected answers)
  answers --ids Q001,Q002                 expected answers for the given ids
"""
import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
SHEET_NAME = "Question Bank"
DEFAULT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "question-bank.xlsx"
)


def col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_sheet(path, sheet_name):
    with zipfile.ZipFile(path) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                strings.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))

        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rid = None
        for s in wb.find("m:sheets", NS):
            if s.get("name") == sheet_name:
                rid = s.get("{%s}id" % NS["r"])
        if rid is None:
            sys.exit("Sheet '%s' not found in %s" % (sheet_name, path))

        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels.findall("rel:Relationship", NS) if r.get("Id") == rid)
        target = target.lstrip("/")
        sheet_path = target if target.startswith("xl/") else "xl/" + target

        rows = []
        for row in ET.fromstring(z.read(sheet_path)).iter("{%s}row" % NS["m"]):
            cells = {}
            for c in row.findall("m:c", NS):
                t = c.get("t")
                if t == "s":
                    v = c.find("m:v", NS)
                    val = strings[int(v.text)] if v is not None else ""
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                else:
                    v = c.find("m:v", NS)
                    val = v.text if v is not None else ""
                cells[col_index(c.get("r"))] = val.strip()
            if cells:
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
        return rows


def load(path):
    rows = read_sheet(path, SHEET_NAME)
    header = rows[0]
    idx = {name: header.index(name) for name in header if name}
    need = ["ID", "Skill", "Topic", "Type", "Difficulty", "Question", "Expected answer / key points", "Follow-up"]
    missing = [n for n in need if n not in idx]
    if missing:
        sys.exit("Missing columns in '%s': %s" % (SHEET_NAME, ", ".join(missing)))

    def get(r, name):
        i = idx[name]
        return r[i] if i < len(r) else ""

    items = []
    for r in rows[1:]:
        if not get(r, "ID") or not get(r, "Question"):
            continue
        items.append({
            "id": get(r, "ID"),
            "skill": get(r, "Skill"),
            "topic": get(r, "Topic"),
            "type": get(r, "Type"),
            "difficulty": get(r, "Difficulty"),
            "question": get(r, "Question"),
            "followup": get(r, "Follow-up"),
            "expected": get(r, "Expected answer / key points"),
        })
    return items


def split(value):
    return [x.strip().lower() for x in value.split(",") if x.strip()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", default=os.environ.get("INTERVIEW_QUESTION_BANK", DEFAULT_FILE))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("skills")
    q = sub.add_parser("questions")
    q.add_argument("--skills", required=True)
    q.add_argument("--difficulty", default="")
    a = sub.add_parser("answers")
    a.add_argument("--ids", required=True)
    args = p.parse_args()

    items = load(args.file)

    if args.cmd == "skills":
        out = {}
        for it in items:
            s = out.setdefault(it["skill"], {"skill": it["skill"], "total": 0, "Basic": 0, "Core": 0, "Stretch": 0})
            s["total"] += 1
            if it["difficulty"] in s:
                s[it["difficulty"]] += 1
        result = sorted(out.values(), key=lambda s: (-s["total"], s["skill"]))
    elif args.cmd == "questions":
        skills = split(args.skills)
        diffs = split(args.difficulty)
        known = {it["skill"].lower() for it in items}
        unknown = [s for s in skills if s not in known]
        if unknown:
            sys.exit("Unknown skill(s): %s" % ", ".join(unknown))
        result = [
            {k: it[k] for k in ("id", "skill", "topic", "type", "difficulty", "question", "followup")}
            for it in items
            if it["skill"].lower() in skills and (not diffs or it["difficulty"].lower() in diffs)
        ]
    else:
        ids = {x.upper() for x in args.ids.split(",") if x.strip()}
        result = [{"id": it["id"], "expected": it["expected"]} for it in items if it["id"].upper() in ids]

    json.dump(result, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()

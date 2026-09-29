#!/usr/bin/env python3
"""허들링 디자인 하네스 — 게이트 판정 스크립트 (표준 라이브러리만).

사용:
  python3 scripts/gate.py G1..G7        # 판정 → work/7-audit/report.json, work/state.json 기록
  python3 scripts/gate.py status        # 다음에 실행할 단계 (재개용)
  옵션: --work <dir>  (기본: <repo>/work)

규칙 값은 rules/design-rules.json(SSOT)에서만 읽는다.
종료 코드: 0 = pass, 1 = fail, 2 = 사용법 오류
"""
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "rules" / "design-rules.json"

GATE_STEP = {"G1": "1", "G2": "2", "G3": "3", "G4": "4", "G5": "5", "G6": "6a", "G7": "6b"}
GATE_ORDER = list(GATE_STEP)
GATE_INPUTS = {
    "G1": ["1-reference/references.json"],
    "G2": ["1-reference/references.json", "2-analysis/points.json"],
    "G3": ["3-spec/screen-spec.md", "3-spec/required-layers.json", "3-spec/flows.json"],
    "G4": ["4-keyscreen/snapshot.json", "3-spec/required-layers.json"],
    "G5": ["5-concept/approval.json"],
    "G6": ["6a-system/tokens.json", "6a-system/components.json"],
    "G7": ["6b-screens/snapshot.json"],
}
KEYSCREENS = ["K1", "K2", "K3"]


# ---------- 공통 ----------

class Judge:
    def __init__(self, gate, rules, work):
        self.gate = gate
        self.rules = rules
        self.work = work
        self.counts = {rid: 0 for rid in rules["gates"][gate]["rules"]}
        self.details = []

    def hit(self, rule_id, message, screen=None, node=None):
        self.counts[rule_id] = self.counts.get(rule_id, 0) + 1
        d = {"rule": rule_id, "message": message}
        if screen:
            d["screen"] = screen
        if node:
            d["node"] = node
        self.details.append(d)

    def load(self, rel):
        path = self.work / rel
        if not path.exists():
            self.hit("INPUT", f"입력 파일 없음: work/{rel}")
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.hit("INPUT", f"JSON 파싱 실패: work/{rel} ({e})")
            return None


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def items_of(data, key):
    """최상위가 리스트이거나 {key: [...]} 인 경우 모두 허용."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get(key, [])
    return []


def norm_hex(c):
    if not isinstance(c, str):
        return None
    c = c.strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", c):
        c = "#" + "".join(ch * 2 for ch in c[1:])
    if re.fullmatch(r"#[0-9a-f]{8}", c):
        c = c[:7]
    return c if re.fullmatch(r"#[0-9a-f]{6}", c) else None


def rgba_to_hex(s):
    m = re.fullmatch(r"\s*rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)\s*", s)
    if not m:
        return None, None
    r, g, b = (int(m.group(i)) for i in (1, 2, 3))
    a = float(m.group(4)) if m.group(4) else 1.0
    return f"#{r:02x}{g:02x}{b:02x}", a


def hex_alpha(c):
    if isinstance(c, str) and re.fullmatch(r"#[0-9a-fA-F]{8}", c.strip()):
        return int(c.strip()[7:9], 16) / 255
    return None


def color_allowed(rules, hex_, opacity):
    tokens = rules["tokens"]
    if hex_ in {v.lower() for v in tokens["colors"].values()}:
        return True
    for ov in tokens.get("overlay_colors", []):
        if hex_ == ov["hex"].lower() and opacity is not None and abs(opacity - ov["opacity"]) <= 0.02:
            return True
    return False


def name_match(rules, key, name):
    return re.search(rules["layer_patterns"][key], (name or "").lower()) is not None


def walk(node, ancestors=()):
    yield node, ancestors
    for ch in node.get("children", []) or []:
        yield from walk(ch, ancestors + (node,))


def texts_of(node):
    return [n["text"] for n, _ in walk(node) if isinstance(n.get("text"), str)]


def screens_of(snapshot):
    return items_of(snapshot, "screens")


def fills(node):
    out = []
    for f in as_list(node.get("fills")):
        if isinstance(f, str):
            f = {"color": f}
        if not isinstance(f, dict) or f.get("visible") is False or "color" not in f:
            continue
        raw = f["color"]
        hex_, op = (rgba_to_hex(raw) if isinstance(raw, str) and raw.strip().startswith("rgb") else (norm_hex(raw), None))
        if op is None:
            op = f.get("opacity", hex_alpha(raw))
        out.append((hex_, op, raw))
    return out


def strokes(node):
    out = []
    for s in as_list(node.get("strokes")):
        if isinstance(s, str):
            s = {"color": s}
        if not isinstance(s, dict) or s.get("visible") is False or "color" not in s:
            continue
        raw = s["color"]
        hex_, op = (rgba_to_hex(raw) if isinstance(raw, str) and raw.strip().startswith("rgb") else (norm_hex(raw), None))
        if op is None:
            op = s.get("opacity", hex_alpha(raw))
        out.append((hex_, op, raw, s.get("weight", node.get("strokeWeight"))))
    return out


# ---------- CX (어기면 안 되는 것) ----------

def check_cx1(j, snapshot):
    cfg = j.rules["cx"]["CX-1"]
    for sc in screens_of(snapshot):
        for node, _ in walk(sc):
            t = node.get("text")
            if not isinstance(t, str):
                continue
            for kind, pat in cfg["patterns"].items():
                for m in re.findall(pat, t):
                    j.hit("CX-1", f"개인정보 패턴({kind}) 발견", sc.get("id"), node.get("name"))
            for company in cfg["company_names"]:
                if company in t:
                    j.hit("CX-1", f"실존 회사명 '{company}' 발견", sc.get("id"), node.get("name"))


def check_cx2(j, snapshot):
    cfg = j.rules["cx"]["CX-2"]
    for sc in screens_of(snapshot):
        for node, _ in walk(sc):
            if not name_match(j.rules, "asset_card", node.get("name")):
                continue
            joined = "\n".join(texts_of(node))
            status = [s for s in cfg["non_approved_status"] if s in joined]
            if not status:
                continue
            if any(m in joined for m in cfg["sale_markers"]) or re.search(cfg["price_pattern"], joined):
                j.hit("CX-2", f"미승인 자산({status[0]})에 판매 중/가격 노출", sc.get("id"), node.get("name"))


def check_cx3(j, flows):
    cfg = j.rules["cx"]["CX-3"]
    raw_nodes = flows.get("nodes", []) if isinstance(flows, dict) else []
    nodes = {n["id"] if isinstance(n, dict) else n for n in raw_nodes}
    edges = flows.get("edges", []) if isinstance(flows, dict) else []
    start, review, terminals = cfg["sale_request_node"], cfg["review_node"], cfg["terminal_nodes"]
    if start not in nodes:
        j.hit("CX-3", f"판매 신청 노드 '{start}' 없음 — 검수 경유 여부 판정 불가")
        return
    if review not in nodes:
        j.hit("CX-3", f"운영자 검수 노드 '{review}' 없음")
        return
    if not any(t in nodes for t in terminals):
        j.hit("CX-3", f"종착 노드 {terminals} 없음 — 판정 불가")
        return
    adj = {}
    for e in edges:
        a, b = (e["from"], e["to"]) if isinstance(e, dict) else (e[0], e[1])
        adj.setdefault(a, []).append(b)
    seen, stack = {start}, [start]
    while stack:
        cur = stack.pop()
        for nxt in adj.get(cur, []):
            if nxt == review or nxt in seen:
                continue
            seen.add(nxt)
            stack.append(nxt)
    for t in terminals:
        if t in seen:
            j.hit("CX-3", f"'{start}' → '{t}' 경로가 '{review}' 를 거치지 않음")


# ---------- 게이트별 판정 ----------

def gate_g1(j):
    cfg = j.rules["gates"]["G1"]["rules"]
    refs = items_of(j.load("1-reference/references.json"), "references")
    if not refs and j.counts.get("INPUT"):
        return
    if len(refs) != cfg["G1-1"]["equals"]:
        j.hit("G1-1", f"레퍼런스 {len(refs)}개 (기준 {cfg['G1-1']['equals']}개)")
    for k in KEYSCREENS:
        n = sum(1 for r in refs if r.get("keyscreen") == k)
        if n != cfg["G1-1"]["per_keyscreen"]:
            j.hit("G1-1", f"{k} 레퍼런스 {n}개 (기준 {cfg['G1-1']['per_keyscreen']}개)", k)
    for i, r in enumerate(refs):
        for f in cfg["G1-2"]["required_fields"]:
            if not str(r.get(f, "")).strip():
                j.hit("G1-2", f"{i + 1}번 항목 '{f}' 누락")
    per_app = {}
    for r in refs:
        per_app[r.get("app")] = per_app.get(r.get("app"), 0) + 1
    for app, n in per_app.items():
        if n > cfg["G1-3"]["max_per_app"]:
            j.hit("G1-3", f"'{app}' {n}개 (최대 {cfg['G1-3']['max_per_app']}개)")


def gate_g2(j):
    cfg = j.rules["gates"]["G2"]["rules"]
    refs = items_of(j.load("1-reference/references.json"), "references")
    points = items_of(j.load("2-analysis/points.json"), "points")
    urls = {r.get("ui_url") for r in refs}
    for k in KEYSCREENS:
        n = sum(1 for p in points if p.get("keyscreen") == k)
        if not cfg["C2-1"]["min"] <= n <= cfg["C2-1"]["max"]:
            j.hit("C2-1", f"{k} 반영 포인트 {n}개 (기준 {cfg['C2-1']['min']}~{cfg['C2-1']['max']})", k)
    for i, p in enumerate(points):
        label = f"{i + 1}번 포인트"
        refs_ = as_list(p.get("prd_ref"))
        if not refs_ or any(not re.fullmatch(cfg["C2-2"]["pattern"], str(r)) for r in refs_):
            j.hit("C2-2", f"{label} PRD 근거 번호 누락/형식 오류: {refs_}", p.get("keyscreen"))
        us = as_list(p.get("ui_url"))
        if not us or any(u not in urls for u in us):
            j.hit("C2-3", f"{label} ui_url 누락 또는 수집본에 없음: {us}", p.get("keyscreen"))
        for kw in cfg["C2-4"]["keywords"]:
            if kw in str(p.get("point", "")):
                j.hit("C2-4", f"{label} MVP 제외 키워드 '{kw}'", p.get("keyscreen"))


def gate_g3(j):
    for rel in j.rules["gates"]["G3"]["files"]:
        if not (j.work / rel).exists():
            j.hit("G3-1", f"파일 없음: work/{rel}")
    req_path, flows_path = j.work / "3-spec/required-layers.json", j.work / "3-spec/flows.json"
    if req_path.exists():
        req = j.load("3-spec/required-layers.json") or {}
        for k in KEYSCREENS:
            if not as_list(req.get(k)):
                j.hit("G3-2", f"{k} 필수 레이어 0개", k)
    if flows_path.exists():
        flows = j.load("3-spec/flows.json")
        if flows is not None:
            check_cx3(j, flows)
    else:
        j.hit("CX-3", "flows.json 없음 — 검수 경유 여부 판정 불가")


def gate_g4(j):
    cfg = j.rules["gates"]["G4"]["rules"]
    snap = j.load("4-keyscreen/snapshot.json")
    if snap is None:
        return
    screens = {s.get("id"): s for s in screens_of(snap)}
    c41 = cfg["C4-1"]
    for k in c41["screens"]:
        if k not in screens:
            j.hit("C4-1", f"키스크린 {k} 없음", k)
    for sid, s in screens.items():
        if (s.get("width"), s.get("height")) != (c41["width"], c41["height"]):
            j.hit("C4-1", f"프레임 {s.get('width')}×{s.get('height')} (기준 {c41['width']}×{c41['height']})", sid)

    req = {}
    if (j.work / "3-spec/required-layers.json").exists():
        req = j.load("3-spec/required-layers.json") or {}
    else:
        j.hit("C4-2", "required-layers.json 없음 — 대조 불가")
    for k, names in req.items():
        if k not in screens:
            continue
        have = {(n.get("name") or "").strip() for n, _ in walk(screens[k])}
        for name in as_list(names):
            if name.strip() not in have:
                j.hit("C4-2", f"필수 레이어 '{name}' 없음", k)

    def texts(sid):
        return texts_of(screens[sid]) if sid in screens else []

    for rid in ("C4-3", "C4-4"):
        c = cfg[rid]
        joined = "\n".join(texts(c["screen"]))
        for t in c["texts"]:
            if t not in joined:
                j.hit(rid, f"'{t}' 없음", c["screen"])

    c = cfg["C4-5"]
    joined = "\n".join(texts(c["screen"]))
    for kw in c["keywords"]:
        if kw not in joined:
            j.hit("C4-5", f"체크리스트 항목 '{kw}' 없음", c["screen"])

    c = cfg["C4-6"]
    button_texts = set()
    if c["screen"] in screens:
        for node, anc in walk(screens[c["screen"]]):
            if isinstance(node.get("text"), str) and any(name_match(j.rules, "button", a.get("name")) for a in anc + (node,)):
                button_texts.add(node["text"].strip())
    for t in c["button_texts"]:
        if t not in button_texts:
            j.hit("C4-6", f"버튼 '{t}' 없음", c["screen"])

    check_cx1(j, snap)
    check_cx2(j, snap)


def gate_g5(j):
    cfg = j.rules["gates"]["G5"]["rules"]
    appr = j.load("5-concept/approval.json")
    if appr is not None:
        for f in cfg["G5-1"]["required_fields"]:
            if not str(appr.get(f, "")).strip():
                j.hit("G5-1", f"'{f}' 누락")
    g4 = [r for r in load_state(j.work) if r.get("gate_id") == "G4"]
    if not g4:
        j.hit("G5-2", "G4 판정 기록 없음")
    elif g4[-1].get("gate") != "pass" or g4[-1].get("cx", 0) != 0:
        j.hit("G5-2", f"최근 G4 = {g4[-1].get('gate')}, CX = {g4[-1].get('cx')} — 사람 승인 진입 불가")


def classify(path):
    segs = [s.lower() for s in path if not str(s).startswith("$")]
    seg = segs[-1] if segs else ""
    full = ".".join(segs)
    if "letterspacing" in seg:
        return "letter"
    if "fontweight" in seg or seg == "weight":
        return "weight"
    if "fontfamily" in seg or seg == "family":
        return "family"
    if "shadow" in seg or "effect" in seg:
        return "shadow"
    if "radius" in seg or "rounded" in seg:
        return "radius"
    if any(k in seg for k in ("spacing", "padding", "gap", "margin")):
        return "spacing"
    if "shadow" in full or "effect" in full:
        return "shadow"
    if "radius" in full or "rounded" in full:
        return "radius"
    if any(k in full.replace("letterspacing", "") for k in ("spacing", "padding", "gap", "margin")):
        return "spacing"
    return None


def num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*(px)?\s*", v)
        if m:
            return float(m.group(1))
    return None


def gate_g6(j):
    tokens = j.rules["tokens"]
    shadow_ok = j.rules["gates"]["G7"]["rules"]["C7-1"]["allowed_layer_patterns"]
    sq = tokens["squircle"]

    def check(path, v, where):
        p = ".".join(str(s) for s in path)
        if isinstance(v, str) and v.strip().startswith("{"):
            return  # 토큰 참조 — 값 아님
        kind = classify(path)
        if kind == "shadow":
            empty = v in (None, "", "none", 0, [], {}) or (isinstance(v, str) and v.strip().lower() == "none")
            if not empty and not any(re.search(a, p.lower()) for a in shadow_ok):
                j.hit("G6-1", f"그림자 값 금지: {p} = {v}", node=where)
            return
        if isinstance(v, str) and (v.strip().startswith("#") or v.strip().startswith("rgb")):
            hex_, op = rgba_to_hex(v) if v.strip().startswith("rgb") else (norm_hex(v), hex_alpha(v))
            if not hex_ or not color_allowed(j.rules, hex_, op):
                j.hit("G6-1", f"허용 외 색상: {p} = {v}", node=where)
            return
        if kind == "family" and isinstance(v, str):
            first = v.split(",")[0].strip().strip("'\"")
            if not first.startswith(tokens["font_family"]):
                j.hit("G6-1", f"허용 외 폰트: {p} = {v}", node=where)
            return
        n = num(v)
        if kind == "letter" and n is not None and n != tokens["letter_spacing"]:
            j.hit("G6-1", f"자간 0 아님: {p} = {v}", node=where)
        elif kind == "weight" and n is not None and n not in tokens["font_weights"]:
            j.hit("G6-1", f"허용 외 굵기: {p} = {v}", node=where)
        elif kind == "radius":
            if isinstance(v, str) and v.strip().endswith("%"):
                if not (re.search(sq["layer_pattern"], p.lower()) and abs(float(v.strip()[:-1]) / 100 - sq["ratio"]) < 1e-6):
                    j.hit("G6-1", f"허용 외 radius: {p} = {v}", node=where)
            elif n is not None and n not in tokens["radius"]:
                j.hit("G6-1", f"허용 외 radius: {p} = {v}", node=where)
        elif kind == "spacing" and n is not None and n not in tokens["spacing"]:
            j.hit("G6-1", f"허용 외 간격: {p} = {v}", node=where)

    def rec(v, path, where):
        if isinstance(v, dict):
            for k, x in v.items():
                rec(x, path + [k], where)
        elif isinstance(v, list):
            for i, x in enumerate(v):
                rec(x, path, where)
        else:
            check(path, v, where)

    for rel in j.rules["gates"]["G6"]["files"]:
        data = j.load(rel)
        if data is not None:
            rec(data, [], rel)


def gate_g7(j):
    tokens = j.rules["tokens"]
    cfg = j.rules["gates"]["G7"]["rules"]
    snap = j.load("6b-screens/snapshot.json")
    if snap is None:
        return
    accent = tokens["colors"]["accent"].lower()
    f0 = cfg["C7-2"]["color"].lower()
    ink = cfg["C7-4"]["color"].lower()
    sq = tokens["squircle"]
    for sc in screens_of(snap):
        sid = sc.get("id")
        accent_n = 0
        for node, _ in walk(sc):
            name = node.get("name")
            fl, st = fills(node), strokes(node)
            for hex_, op, raw in fl + [s[:3] for s in st]:
                if not hex_ or not color_allowed(j.rules, hex_, op):
                    j.hit("T-1", f"허용 외 색상 {raw}", sid, name)
            if any(h == accent for h, _, _ in fl) or any(s[0] == accent for s in st):
                accent_n += 1
            if name_match(j.rules, "button", name) and any(h == accent for h, _, _ in fl):
                j.hit("A-2", "버튼 fill 에 액센트 색", sid, name)
            if any(h == f0 for h, _, _ in fl) and not name_match(j.rules, "text_input", name):
                j.hit("C7-2", f"{f0} fill 이 입력창 밖에서 사용", sid, name)
            if any(s[0] == f0 for s in st) and not name_match(j.rules, "card", name):
                j.hit("C7-3", f"{f0} stroke 가 카드 밖에서 사용", sid, name)
            if name_match(j.rules, "card", name) and any(h == ink for h, _, _ in fl):
                j.hit("C7-4", "카드 색 반전(ink fill)", sid, name)

            if "cornerRadius" in node:
                radii = [r for r in as_list(node["cornerRadius"]) if num(r) is not None]
                if re.search(sq["layer_pattern"], (name or "").lower()):
                    side = min(node.get("width") or 0, node.get("height") or 0)
                    for r in radii:
                        if abs(num(r) - side * sq["ratio"]) > sq["tolerance_px"]:
                            j.hit("T-2", f"app-icon radius {r} (기준 {side * sq['ratio']:.1f})", sid, name)
                else:
                    for r in radii:
                        if num(r) not in tokens["radius"]:
                            j.hit("T-2", f"허용 외 radius {r}", sid, name)

            for e in as_list(node.get("effects")):
                if isinstance(e, dict) and e.get("visible") is not False and "SHADOW" in str(e.get("type", "")).upper():
                    if not any(re.search(a, (name or "").lower()) for a in cfg["C7-1"]["allowed_layer_patterns"]):
                        j.hit("C7-1", f"그림자 {e.get('type')}", sid, name)

            if isinstance(node.get("text"), str):
                fam = node.get("fontFamily")
                for f in as_list(fam):
                    if not str(f).startswith(tokens["font_family"]):
                        j.hit("T-3", f"폰트 {f}", sid, name)
                for w in as_list(node.get("fontWeight")):
                    if num(w) not in tokens["font_weights"]:
                        j.hit("T-4", f"굵기 {w}", sid, name)
                for ls in as_list(node.get("letterSpacing")):
                    if num(ls) not in (None, tokens["letter_spacing"]):
                        j.hit("T-5", f"자간 {ls}", sid, name)

            for key in ("itemSpacing", "gap", "padding", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft"):
                for v in as_list(node.get(key)):
                    if num(v) is not None and num(v) not in tokens["spacing"]:
                        j.hit("T-6", f"{key} {v}", sid, name)
        if accent_n > cfg["A-1"]["max_per_screen"]:
            j.hit("A-1", f"액센트 요소 {accent_n}개 (최대 {cfg['A-1']['max_per_screen']})", sid)
    check_cx1(j, snap)
    check_cx2(j, snap)


GATES = {"G1": gate_g1, "G2": gate_g2, "G3": gate_g3, "G4": gate_g4, "G5": gate_g5, "G6": gate_g6, "G7": gate_g7}


# ---------- state / report ----------

def load_state(work):
    p = work / "state.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def input_hash(work, gate):
    h = hashlib.sha256(RULES_PATH.read_bytes())
    for rel in GATE_INPUTS[gate]:
        p = work / rel
        h.update(rel.encode())
        h.update(p.read_bytes() if p.exists() else b"<missing>")
    return h.hexdigest()[:16]


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def run_gate(gate, work):
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    j = Judge(gate, rules, work)
    GATES[gate](j)

    cx = {k: v for k, v in j.counts.items() if k.startswith("CX-")}
    cx_total = sum(cx.values())
    failed = any(v > 0 for v in j.counts.values())
    result = "fail" if failed else "pass"

    state = load_state(work)
    ihash = input_hash(work, gate)
    # 입력이 바뀌지 않은 재판정(자동 hook + 수동 호출 중복)은 시도로 세지 않는다
    duplicate = bool(state) and state[-1].get("gate_id") == gate and state[-1].get("input_hash") == ihash
    attempt = 0 if duplicate else 1
    for r in reversed(state):
        if r.get("gate_id") != gate or r.get("gate") == "pass":
            break
        attempt += 1
    attempt = max(attempt, 1)
    max_attempts = rules["retry"]["max_attempts"]

    report = {
        "gate": gate,
        "step": GATE_STEP[gate],
        "result": result,
        "cx_total": cx_total,
        "cx": cx,
        "cx_block": cx_total > 0,
        "attempt": attempt,
        "max_attempts": max_attempts,
        "stop": failed and attempt >= max_attempts,
        "counts": {k: v for k, v in j.counts.items() if not k.startswith("CX-")},
        "details": sorted(j.details, key=lambda d: (not d["rule"].startswith("CX-"), d["rule"])),
        "at": now(),
    }
    (work / "7-audit").mkdir(parents=True, exist_ok=True)
    (work / "7-audit" / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    record = {
        "step": GATE_STEP[gate], "gate_id": gate, "gate": result,
        "cx": cx_total, "input_hash": ihash, "at": report["at"],
    }
    if duplicate:
        state[-1] = record
    else:
        state.append(record)
    (work / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{gate}] {result.upper()}  CX={cx_total}"
          + (f"  attempt={attempt}/{max_attempts}" if failed else "")
          + ("  → STOP: 사람에게 알림" if report["stop"] else ""))
    for d in report["details"][:30]:
        loc = "/".join(x for x in (d.get("screen"), d.get("node")) if x)
        print(f"  - {d['rule']}: {d['message']}" + (f"  ({loc})" if loc else ""))
    if len(report["details"]) > 30:
        print(f"  ... 외 {len(report['details']) - 30}건 (work/7-audit/report.json)")
    return 0 if result == "pass" else 1


def status(work):
    state = load_state(work)
    latest = {}
    for r in state:
        latest[r.get("gate_id")] = r
    stale, nxt = [], None
    for g in GATE_ORDER:
        r = latest.get(g)
        if r and r.get("gate") == "pass" and r.get("input_hash") != input_hash(work, g):
            stale.append(g)
        if nxt is None and (not r or r.get("gate") != "pass" or g in stale):
            nxt = g
    out = {
        "next_gate": nxt,
        "next_step": GATE_STEP[nxt] if nxt else "done",
        "stale": stale,
        "latest": {g: latest[g].get("gate") for g in GATE_ORDER if g in latest},
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv):
    work = ROOT / "work"
    args = []
    i = 0
    while i < len(argv):
        if argv[i] == "--work" and i + 1 < len(argv):
            work = Path(argv[i + 1]).resolve()
            i += 2
            continue
        args.append(argv[i])
        i += 1
    if len(args) != 1 or (args[0] not in GATES and args[0] != "status"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    work.mkdir(parents=True, exist_ok=True)
    return status(work) if args[0] == "status" else run_gate(args[0], work)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

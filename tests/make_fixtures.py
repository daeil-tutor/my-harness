#!/usr/bin/env python3
"""tests/fixtures/{rule_id}/*pass*.json, *fail*.json 생성기.

fixture 형식:
  {"gate": "G4", "rule": "C4-1", "expect": "pass"|"fail",
   "files": {"<work 기준 경로>": <json 또는 문자열>}, "state": [...]}
pass fixture 는 해당 게이트 전체가 pass 여야 하고, fail fixture 는 해당 규칙 건수 > 0 이어야 한다.
규칙을 추가하면 여기에 pass/fail 케이스를 추가하고 `python3 tests/make_fixtures.py` 로 재생성한다.
"""
import copy
import json
import shutil
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fixtures"


# ---------- 유효한 기본 입력 ----------

def refs_ok():
    apps = ["앱A", "앱B", "앱C", "앱D", "앱E"]
    out = []
    for i in range(15):
        k = f"K{i // 5 + 1}"
        out.append({"app": apps[i % 5], "ui_url": f"https://www.uibowl.io/ui/{i + 1}",
                    "screen_type": "홈", "point": f"반영 포인트 {i + 1}", "keyscreen": k})
    return out


def points_ok():
    refs = refs_ok()
    out = []
    for k_i, k in enumerate(["K1", "K2", "K3"]):
        for n in range(3):
            out.append({"keyscreen": k, "point": f"{k} 카드 위계 정리 {n + 1}",
                        "prd_ref": ["6-5"], "ui_url": [refs[k_i * 5 + n]["ui_url"]]})
    return out


REQUIRED = {"K1": ["nav-pill", "home-hero"],
            "K2": ["visibility-segmented", "asset-card/approved"],
            "K3": ["review-checklist", "button-approve"]}

FLOWS = {
    "nodes": [{"id": "sale_request"}, {"id": "admin_review"}, {"id": "revision_requested"},
              {"id": "approved"}, {"id": "rejected"}],
    "edges": [["sale_request", "admin_review"], ["admin_review", "approved"],
              ["admin_review", "revision_requested"], ["revision_requested", "sale_request"],
              ["admin_review", "rejected"]],
}


def t(name, text, weight=400):
    return {"name": name, "type": "TEXT", "text": text, "fontFamily": "Pretendard",
            "fontWeight": weight, "fontSize": 15, "letterSpacing": 0, "fills": [{"color": "#141414"}]}


def frame(name, children, **kw):
    n = {"name": name, "type": "FRAME", "children": children}
    n.update(kw)
    return n


def screen(sid, children, w=390, h=844):
    return {"id": sid, "name": sid, "width": w, "height": h, "fills": [{"color": "#ffffff"}], "children": children}


def keyscreen_ok():
    k1 = screen("K1", [
        frame("nav-pill", [t("logo", "허들링", 700)], fills=[{"color": "#f3f3f3"}], cornerRadius=9999),
        frame("home-hero", [t("title", "AI 실무 실험실", 700), t("lead", "배우고, 적용하고, 자산으로", 300)]),
    ])
    k2 = screen("K2", [
        frame("visibility-segmented", [t("opt1", "비공개"), t("opt2", "멤버 공개"), t("opt3", "판매 신청")]),
        frame("status-legend", [t("s1", "임시저장"), t("s2", "검수 대기"), t("s3", "수정 요청"),
                                t("s4", "승인됨"), t("s5", "반려")]),
        frame("asset-card/approved", [t("title", "QA 자동화 스킬"), t("status", "승인됨"), t("price", "19,000원")]),
        frame("asset-card/pending", [t("title", "회의록 요약 프롬프트"), t("status", "검수 대기")]),
    ])
    k3 = screen("K3", [
        frame("review-checklist", [
            t("c1", "실제 업무에 써본 것"), t("c2", "결과 예시가 있는 것"), t("c3", "사용 방법이 명확한 것"),
            t("c4", "초보자가 따라할 수 있는 것"), t("c5", "툴/버전/환경 조건이 적혀 있는 것"),
            t("c6", "개인정보/고객정보/회사기밀이 없는 것"), t("c7", "저작권 문제가 없는 것"),
            t("c8", "구매자가 바로 써볼 수 있는 것"),
        ]),
        frame("button-approve", [t("label", "승인", 600)]),
        frame("button-revise", [t("label", "수정 요청", 600)]),
        frame("button-reject", [t("label", "반려", 600)]),
    ])
    return {"screens": [k1, k2, k3]}


def screens_ok():
    s = screen("S01", [
        frame("card/skill", [t("title", "스킬 카드", 700)],
              fills=[{"color": "#ffffff"}], strokes=[{"color": "#f0f0f0", "weight": 1}],
              cornerRadius=24, padding=[24, 24, 24, 24], itemSpacing=8),
        frame("text-input/search", [t("placeholder", "스킬 검색")],
              fills=[{"color": "#f0f0f0"}], cornerRadius=16, padding=[12, 16, 12, 16]),
        frame("button-primary", [{**t("label", "시작하기", 600), "fills": [{"color": "#ffffff"}]}],
              fills=[{"color": "#141414"}], cornerRadius=9999, padding=[0, 16, 0, 16]),
        frame("badge-popular", [{**t("label", "인기", 600), "fills": [{"color": "#ffffff"}]}],
              fills=[{"color": "#0066ff"}], cornerRadius=9999),
        frame("app-icon/figma", [], width=48, height=48, cornerRadius=14.4),
        frame("segmented-control-active", [t("label", "월간")],
              fills=[{"color": "#ffffff"}], cornerRadius=9999,
              effects=[{"type": "DROP_SHADOW", "visible": True}]),
        frame("badge-overlay", [{**t("label", "자동화", 600), "fills": [{"color": "#ffffff"}]}],
              fills=[{"color": "#737373", "opacity": 0.56}], cornerRadius=9999),
        frame("footer", [{**t("wordmark", "허들링", 700), "fills": [{"color": "#ffffff"}]}],
              fills=[{"color": "#141414"}], cornerRadius=[24, 24, 0, 0], padding=[48, 16, 48, 16]),
    ])
    return {"screens": [s]}


TOKENS_OK = {
    "colors": {"ink": {"$value": "#141414"}, "canvas": {"$value": "#ffffff"}, "accent": {"$value": "#0066ff"}},
    "rounded": {"sm": {"$value": 16}, "md": {"$value": 24}, "full": {"$value": 9999}},
    "spacing": {"xs": {"$value": "8px"}, "md": {"$value": "16px"}},
    "typography": {"heading-1": {"fontFamily": "Pretendard", "fontWeight": 700, "letterSpacing": 0}},
    "app-icon": {"radius": "30%"},
}
COMPONENTS_OK = {
    "button-primary": {"fill": "{colors.ink}", "radius": 9999, "padding": [0, 16]},
    "segmented-control-active": {"shadow": "0 1px 2px rgba(20,20,20,0.08)"},
    "card": {"stroke": "#f0f0f0", "radius": 24, "padding": 24, "shadow": "none"},
}


def base(gate):
    if gate == "G1":
        return {"1-reference/references.json": refs_ok()}
    if gate == "G2":
        return {"1-reference/references.json": refs_ok(), "2-analysis/points.json": points_ok()}
    if gate == "G3":
        return {"3-spec/screen-spec.md": "# 화면 설계서\n", "3-spec/required-layers.json": REQUIRED,
                "3-spec/flows.json": FLOWS}
    if gate == "G4":
        return {"4-keyscreen/snapshot.json": keyscreen_ok(), "3-spec/required-layers.json": REQUIRED}
    if gate == "G5":
        return {"5-concept/approval.json": {"approver": "운영자", "date": "2026-09-29", "chosen": "A안"}}
    if gate == "G6":
        return {"6a-system/tokens.json": TOKENS_OK, "6a-system/components.json": COMPONENTS_OK}
    if gate == "G7":
        return {"6b-screens/snapshot.json": screens_ok()}
    raise ValueError(gate)


G4_PASS_STATE = [{"step": "4", "gate_id": "G4", "gate": "pass", "cx": 0, "input_hash": "x", "at": "2026-09-29"}]


# ---------- 규칙별 실패 변형 ----------

def find(snapshot, sid, name):
    for sc in snapshot["screens"]:
        if sc["id"] != sid:
            continue
        stack = [sc]
        while stack:
            n = stack.pop()
            if n.get("name") == name:
                return n
            stack.extend(n.get("children", []))
    raise KeyError(name)


def s01(files):
    return files["6b-screens/snapshot.json"]["screens"][0]


def k(files):
    return files["4-keyscreen/snapshot.json"]


def mutate_g1_1(f): f["1-reference/references.json"].pop()
def mutate_g1_2(f): f["1-reference/references.json"][0]["ui_url"] = ""
def mutate_g1_3(f): f["1-reference/references.json"][1]["app"] = "앱A"; f["1-reference/references.json"][2]["app"] = "앱A"


def mutate_c2_1(f): f["2-analysis/points.json"] = [p for p in f["2-analysis/points.json"] if p["keyscreen"] != "K1"][:6] + f["2-analysis/points.json"][:2]
def mutate_c2_2(f): f["2-analysis/points.json"][0]["prd_ref"] = ["6장"]
def mutate_c2_3(f): f["2-analysis/points.json"][0]["ui_url"] = ["https://example.com/없는-화면"]
def mutate_c2_4(f): f["2-analysis/points.json"][0]["point"] = "결제 버튼을 카드 하단에 배치"


def mutate_g3_1(f): del f["3-spec/screen-spec.md"]
def mutate_g3_2(f): f["3-spec/required-layers.json"]["K3"] = []
def mutate_cx3(f): f["3-spec/flows.json"]["edges"].append(["sale_request", "approved"])


def mutate_c4_1(f): k(f)["screens"][0]["height"] = 800
def mutate_c4_2(f): find(k(f), "K1", "home-hero")["name"] = "hero"
def mutate_c4_3(f): find(k(f), "K2", "opt2")["text"] = "팀 공개"
def mutate_c4_4(f): find(k(f), "K2", "s5")["text"] = "보류"
def mutate_c4_5(f): find(k(f), "K3", "c7")["text"] = "출처가 명확한 것"
def mutate_c4_6(f): find(k(f), "K3", "button-reject")["children"][0]["text"] = "거절"


def mutate_cx1_g4(f): find(k(f), "K2", "asset-card/pending")["children"][0]["text"] = "문의: kim@example.com / 010-1234-5678"
def mutate_cx2_g4(f): find(k(f), "K2", "asset-card/pending")["children"].append(t("price", "19,000원"))


def mutate_g5_1(f): del f["5-concept/approval.json"]["approver"]


def mutate_g6_1(f):
    f["6a-system/tokens.json"]["rounded"]["xs"] = {"$value": 12}
    f["6a-system/components.json"]["card"]["shadow"] = "0 4px 12px rgba(0,0,0,0.1)"


def mutate_t1(f): s01(f)["children"][0]["fills"] = [{"color": "#ff0000"}]
def mutate_t2(f): s01(f)["children"][0]["cornerRadius"] = 12
def mutate_t3(f): s01(f)["children"][0]["children"][0]["fontFamily"] = "Inter"
def mutate_t4(f): s01(f)["children"][0]["children"][0]["fontWeight"] = 500
def mutate_t5(f): s01(f)["children"][0]["children"][0]["letterSpacing"] = -0.5
def mutate_t6(f): s01(f)["children"][0]["itemSpacing"] = 10


def mutate_a1(f):
    for i in range(2):
        s01(f)["children"].append(frame(f"badge-save-{i}", [], fills=[{"color": "#0066ff"}], cornerRadius=9999))


def mutate_a2(f): find(f["6b-screens/snapshot.json"], "S01", "button-primary")["fills"] = [{"color": "#0066ff"}]
def mutate_c7_1(f): s01(f)["children"][0]["effects"] = [{"type": "DROP_SHADOW", "visible": True}]
def mutate_c7_2(f): s01(f)["children"].append(frame("section-band", [], fills=[{"color": "#f0f0f0"}]))
def mutate_c7_3(f): s01(f)["children"].append(frame("divider", [], strokes=[{"color": "#f0f0f0", "weight": 1}]))
def mutate_c7_4(f): s01(f)["children"].append(frame("pricing-card-featured", [], fills=[{"color": "#141414"}], cornerRadius=24))
def mutate_cx1_g7(f): s01(f)["children"][0]["children"].append(t("owner", "삼성전자 고객 명단 정리 프롬프트"))


def mutate_cx2_g7(f):
    s01(f)["children"].append(frame("asset-card/revise", [t("status", "수정 요청"), t("sale", "판매 중")]))


CASES = [
    # (rule, gate, mutate, suffix)
    ("G1-1", "G1", mutate_g1_1, ""), ("G1-2", "G1", mutate_g1_2, ""), ("G1-3", "G1", mutate_g1_3, ""),
    ("C2-1", "G2", mutate_c2_1, ""), ("C2-2", "G2", mutate_c2_2, ""), ("C2-3", "G2", mutate_c2_3, ""),
    ("C2-4", "G2", mutate_c2_4, ""),
    ("G3-1", "G3", mutate_g3_1, ""), ("G3-2", "G3", mutate_g3_2, ""), ("CX-3", "G3", mutate_cx3, ""),
    ("C4-1", "G4", mutate_c4_1, ""), ("C4-2", "G4", mutate_c4_2, ""), ("C4-3", "G4", mutate_c4_3, ""),
    ("C4-4", "G4", mutate_c4_4, ""), ("C4-5", "G4", mutate_c4_5, ""), ("C4-6", "G4", mutate_c4_6, ""),
    ("CX-1", "G4", mutate_cx1_g4, "g4-"), ("CX-2", "G4", mutate_cx2_g4, "g4-"),
    ("G5-1", "G5", mutate_g5_1, ""), ("G5-2", "G5", None, ""),
    ("G6-1", "G6", mutate_g6_1, ""),
    ("T-1", "G7", mutate_t1, ""), ("T-2", "G7", mutate_t2, ""), ("T-3", "G7", mutate_t3, ""),
    ("T-4", "G7", mutate_t4, ""), ("T-5", "G7", mutate_t5, ""), ("T-6", "G7", mutate_t6, ""),
    ("A-1", "G7", mutate_a1, ""), ("A-2", "G7", mutate_a2, ""),
    ("C7-1", "G7", mutate_c7_1, ""), ("C7-2", "G7", mutate_c7_2, ""), ("C7-3", "G7", mutate_c7_3, ""),
    ("C7-4", "G7", mutate_c7_4, ""),
    ("CX-1", "G7", mutate_cx1_g7, "g7-"), ("CX-2", "G7", mutate_cx2_g7, "g7-"),
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    n = 0
    for rule, gate, mutate, suffix in CASES:
        d = OUT / rule
        d.mkdir(parents=True, exist_ok=True)
        ok = base(gate)
        state = G4_PASS_STATE if gate == "G5" else []
        fx_pass = {"gate": gate, "rule": rule, "expect": "pass", "files": ok, "state": state}
        bad = copy.deepcopy(ok)
        bad_state = state
        if rule == "G5-2":
            bad_state = [{**G4_PASS_STATE[0], "gate": "fail", "cx": 1}]
        else:
            mutate(bad)
        fx_fail = {"gate": gate, "rule": rule, "expect": "fail", "files": bad, "state": bad_state}
        for name, fx in ((f"{suffix}pass.json", fx_pass), (f"{suffix}fail.json", fx_fail)):
            (d / name).write_text(json.dumps(fx, ensure_ascii=False, indent=2), encoding="utf-8")
            n += 1
    print(f"fixtures {n}개 생성 → {OUT}")


if __name__ == "__main__":
    main()

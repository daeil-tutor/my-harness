#!/usr/bin/env python3
"""하네스 검증 (harness/r8-verify.md).

1. fixture — 규칙별 pass/fail 샘플을 scripts/gate.py 로 판정해 기대값과 대조
2. hook  — 편집 경계·Bash 제한 차단 테스트
3. 추적표 — 규칙 ID × {SSOT 키, gate.py, fixture pass/fail, 게이트}

사용: python3 tests/run.py   (불일치 0건이면 exit 0)
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
GATE = ROOT / "scripts" / "gate.py"
HOOKS = ROOT / "scripts" / "hooks"


def run_fixture(path):
    fx = json.loads(path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for rel, content in fx["files"].items():
            p = work / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False), encoding="utf-8")
        (work / "state.json").write_text(json.dumps(fx.get("state", [])), encoding="utf-8")
        subprocess.run([sys.executable, str(GATE), fx["gate"], "--work", str(work)], capture_output=True, text=True)
        report = json.loads((work / "7-audit" / "report.json").read_text(encoding="utf-8"))
    n = report["cx"].get(fx["rule"], 0) + report["counts"].get(fx["rule"], 0)
    if fx["expect"] == "pass":
        ok = report["result"] == "pass"
        why = f"gate={report['result']}, 위반 {[d['rule'] + ': ' + d['message'] for d in report['details']][:3]}"
    else:
        ok = n > 0 and report["result"] == "fail"
        why = f"{fx['rule']} 건수={n}"
    return ok, why


def hook(script, payload, env=None):
    e = dict(os.environ)
    e.pop("HARNESS_MAINTENANCE", None)
    e.update(env or {})
    p = subprocess.run([sys.executable, str(HOOKS / script)], input=json.dumps(payload),
                       capture_output=True, text=True, env=e)
    return p.returncode


def edit(agent, rel):
    d = {"tool_name": "Write", "cwd": str(ROOT), "tool_input": {"file_path": str(ROOT / rel)}}
    if agent:
        d["agent_type"] = agent
    return d


def bash(agent, cmd):
    d = {"tool_name": "Bash", "cwd": str(ROOT), "tool_input": {"command": cmd}}
    if agent:
        d["agent_type"] = agent
    return d


HOOK_CASES = [
    # (설명, 스크립트, payload, env, 기대 exit)
    ("analyst → rules/ 쓰기 차단", "guard_edit.py", edit("analyst", "rules/design-rules.json"), None, 2),
    ("analyst → 자기 폴더 허용", "guard_edit.py", edit("analyst", "work/2-analysis/points.json"), None, 0),
    ("analyst → 남의 폴더 차단", "guard_edit.py", edit("analyst", "work/1-reference/references.json"), None, 2),
    ("gate-judge → Edit 차단", "guard_edit.py", edit("gate-judge", "work/7-audit/report.json"), None, 2),
    ("keyscreen-designer → state.json 차단", "guard_edit.py", edit("keyscreen-designer", "work/state.json"), None, 2),
    ("Explore → scripts/ 차단", "guard_edit.py", edit("Explore", "scripts/gate.py"), None, 2),
    ("오케스트레이터 → approval.json 허용", "guard_edit.py", edit(None, "work/5-concept/approval.json"), None, 0),
    ("오케스트레이터 → state.json 차단", "guard_edit.py", edit(None, "work/state.json"), None, 2),
    ("오케스트레이터 → rules/ 차단", "guard_edit.py", edit(None, "rules/design-rules.json"), None, 2),
    ("오케스트레이터 → rules/ 유지보수 허용", "guard_edit.py", edit(None, "rules/design-rules.json"),
     {"HARNESS_MAINTENANCE": "1"}, 0),
    ("gate-judge → gate.py 실행 허용", "guard_bash.py", bash("gate-judge", "python3 scripts/gate.py G4"), None, 0),
    ("gate-judge → status 허용", "guard_bash.py", bash("gate-judge", "python3 scripts/gate.py status"), None, 0),
    ("gate-judge → 다른 명령 차단", "guard_bash.py", bash("gate-judge", "cat work/state.json"), None, 2),
    ("gate-judge → 명령 체이닝 차단", "guard_bash.py", bash("gate-judge", "python3 scripts/gate.py G4; rm -rf work"), None, 2),
    ("작업 에이전트 → Bash 차단", "guard_bash.py", bash("screen-designer", "ls"), None, 2),
    ("오케스트레이터 → 셸로 state.json 쓰기 차단", "guard_bash.py", bash(None, "echo [] > work/state.json"), None, 2),
    ("오케스트레이터 → gate.py 2>&1 허용", "guard_bash.py", bash(None, "python3 scripts/gate.py G1 2>&1"), None, 0),
]


def trace():
    rules = json.loads((ROOT / "rules" / "design-rules.json").read_text(encoding="utf-8"))
    gate_src = GATE.read_text(encoding="utf-8")
    rows = []
    ids = {}
    for g, cfg in rules["gates"].items():
        for rid in cfg["rules"]:
            ids.setdefault(rid, []).append(g)
    for rid in rules["cx"]:
        if not rid.startswith("_"):
            ids.setdefault(rid, [])
    for rid, gates in sorted(ids.items()):
        d = FIXTURES / rid
        has_pass = d.exists() and any("pass" in p.name for p in d.glob("*.json"))
        has_fail = d.exists() and any("fail" in p.name for p in d.glob("*.json"))
        row = {"rule": rid, "ssot": True, "gate_py": f'"{rid}"' in gate_src,
               "fixture": has_pass and has_fail, "gates": gates}
        row["ok"] = row["gate_py"] and row["fixture"] and bool(gates)
        rows.append(row)
    return rows


def main():
    bad = 0
    print("== 1. fixture ==")
    for path in sorted(FIXTURES.glob("*/*.json")):
        ok, why = run_fixture(path)
        bad += not ok
        print(f"  {'OK ' if ok else 'NG '} {path.parent.name}/{path.name}" + ("" if ok else f"  ← {why}"))

    print("== 2. hook ==")
    for desc, script, payload, env, want in HOOK_CASES:
        got = hook(script, payload, env)
        ok = got == want
        bad += not ok
        print(f"  {'OK ' if ok else 'NG '} {desc}" + ("" if ok else f"  (exit {got}, 기대 {want})"))

    print("== 3. 추적표 ==")
    for r in trace():
        bad += not r["ok"]
        print(f"  {'OK ' if r['ok'] else 'NG '} {r['rule']:<5} SSOT=Y gate.py={'Y' if r['gate_py'] else 'N'} "
              f"fixture={'Y' if r['fixture'] else 'N'} gates={','.join(r['gates']) or '-'}")

    print(f"\n불일치 {bad}건")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

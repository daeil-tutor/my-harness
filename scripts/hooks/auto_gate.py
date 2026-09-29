#!/usr/bin/env python3
"""SubagentStop — 작업 에이전트가 끝나면 해당 단계 게이트를 자동 실행 (harness/r7-orchestrator.md).

결과는 scripts/gate.py 가 work/state.json, work/7-audit/report.json 에 기록한다.
오케스트레이터는 에이전트 보고가 아니라 state.json 으로 다음 단계를 정한다.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENT_GATE = {
    "ref-collector": "G1",
    "analyst": "G2",
    "spec-writer": "G3",
    "keyscreen-designer": "G4",
    "system-builder": "G6",
    "screen-designer": "G7",
}


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    gate = AGENT_GATE.get(data.get("agent_type"))
    if not gate:
        return 0
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gate.py"), gate],
        cwd=ROOT, capture_output=True, text=True,
    )
    summary = (proc.stdout or proc.stderr).strip().splitlines()
    msg = f"자동 판정 {gate}: " + (summary[0] if summary else "출력 없음") + " — 상세: work/7-audit/report.json"
    print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

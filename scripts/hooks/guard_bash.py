#!/usr/bin/env python3
"""PreToolUse(Bash) — 셸을 통한 경계 우회 차단.

- gate-judge: `python3 scripts/gate.py G1~G7|status [--work DIR]` 만 허용
- 작업 에이전트: Bash 없음 (agent tools 에서 제외) — 혹시 호출되면 차단
- 그 외: 보호 경로/work 를 쓰는 셸 명령(>, tee, mv, cp, rm, sed -i, touch, mkdir) 차단
  (메인 세션은 HARNESS_MAINTENANCE=1 이면 보호 경로 허용, work/ 는 항상 gate.py 만)
휴리스틱 검사이며 1차 방어선은 Edit/Write 훅이다.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from guard_edit import AGENT_DIRS, PROTECTED  # noqa: E402

GATE_CMD = re.compile(r"^\s*python3\s+scripts/gate\.py\s+(G[1-7]|status)(\s+--work\s+\S+)?\s*$")
WRITE_OPS = re.compile(r"(>|\btee\b|\bmv\b|\bcp\b|\brm\b|\bsed\s+-i|\btouch\b|\bmkdir\b|\bln\b|\bchmod\b)")


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    agent = data.get("agent_type")
    maintenance = os.environ.get("HARNESS_MAINTENANCE") == "1"

    reason = None
    if agent == "gate-judge":
        if not GATE_CMD.match(cmd):
            reason = "gate-judge 는 `python3 scripts/gate.py G#|status` 만 실행할 수 있습니다"
    elif agent in AGENT_DIRS:
        reason = f"{agent} 에는 Bash 권한이 없습니다"
    elif WRITE_OPS.search(re.sub(r"\d?>&\d|\d?>\s*/dev/null", "", cmd)):
        touches_work = re.search(r"(^|[\s'\"/=])work/", cmd) is not None
        touches_protected = any(re.search(rf"(^|[\s'\"/=]){re.escape(p)}(/|\b)", cmd) for p in PROTECTED)
        if touches_work:
            reason = "work/ 는 셸로 쓸 수 없습니다 (판정 결과는 scripts/gate.py 만 기록)"
        elif touches_protected and (agent or not maintenance):
            reason = "보호 경로를 셸로 수정할 수 없습니다 (유지보수는 HARNESS_MAINTENANCE=1)"

    if reason:
        print(f"[harness guard] {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

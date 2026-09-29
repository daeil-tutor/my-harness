#!/usr/bin/env python3
"""PreToolUse(Edit|Write|NotebookEdit) — 에이전트별 편집 경계 (harness/r6-roles.md).

- 작업 에이전트: 자기 폴더 1곳만
- gate-judge: 편집 전부 차단
- 메인 세션(오케스트레이터): work/ 안에서는 work/5-concept/approval.json 만,
  보호 경로(rules/ scripts/ docs/ harness/ tests/ .claude/ CLAUDE.md)는 HARNESS_MAINTENANCE=1 일 때만
- 그 외 서브에이전트: 보호 경로·work/ 편집 차단
차단 = exit 2 + stderr 사유.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

AGENT_DIRS = {
    "ref-collector": "work/1-reference",
    "analyst": "work/2-analysis",
    "spec-writer": "work/3-spec",
    "keyscreen-designer": "work/4-keyscreen",
    "system-builder": "work/6a-system",
    "screen-designer": "work/6b-screens",
}
READ_ONLY_AGENTS = {"gate-judge"}
PROTECTED = ["rules", "scripts", "docs", "harness", "tests", ".claude", "CLAUDE.md"]
ORCHESTRATOR_WORK_FILES = ["work/5-concept/approval.json"]


def rel_to_root(path_str, cwd):
    p = Path(path_str)
    if not p.is_absolute():
        p = Path(cwd or ROOT) / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None  # 레포 밖


def under(rel, prefix):
    return rel == prefix or rel.startswith(prefix.rstrip("/") + "/")


def decide(agent, rel, maintenance):
    """차단 사유를 돌려준다. None 이면 허용."""
    if rel is None:
        return "레포 밖 경로는 편집할 수 없습니다" if agent else None
    if agent in READ_ONLY_AGENTS:
        return f"{agent} 는 읽기 전용 판정자입니다 — 편집 불가"
    if agent in AGENT_DIRS:
        own = AGENT_DIRS[agent]
        return None if under(rel, own) else f"{agent} 는 {own}/ 만 편집할 수 있습니다 (시도: {rel})"
    is_protected = any(under(rel, p) for p in PROTECTED)
    if agent:  # 하네스 밖 서브에이전트 (Explore 등)
        if is_protected or under(rel, "work"):
            return f"{agent} 는 하네스 보호 경로를 편집할 수 없습니다 (시도: {rel})"
        return None
    # 메인 세션 = 오케스트레이터
    if under(rel, "work"):
        return None if rel in ORCHESTRATOR_WORK_FILES else \
            f"오케스트레이터가 쓰는 work/ 파일은 {ORCHESTRATOR_WORK_FILES[0]} 뿐입니다 (시도: {rel})"
    if is_protected and not maintenance:
        return f"보호 경로입니다 (시도: {rel}). 하네스 유지보수는 HARNESS_MAINTENANCE=1 로 세션을 시작하세요"
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("notebook_path")
    if not path:
        return 0
    agent = data.get("agent_type")
    reason = decide(agent, rel_to_root(path, data.get("cwd")), os.environ.get("HARNESS_MAINTENANCE") == "1")
    if reason:
        print(f"[harness guard] {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

# R7 — 오케스트레이터

## 주체

- 메인 Claude Code 세션 = 오케스트레이터 (CLAUDE.md 로 동작 정의)
- 별도 오케스트레이터 에이전트 없음
- 하는 일: 트리거 해석 → 서브에이전트 위임 → gate-judge 호출 → state.json 확인 → 다음 단계 / 복귀 / 중단
- 하지 않는 일: 산출물 직접 작성 (예외: work/5-concept/approval.json)

## 단계 전환 규칙

1. 다음 단계 호출 조건 = state.json 에 직전 게이트 `pass`
2. 서브에이전트의 "완료" 보고는 근거가 아님
3. state.json 에 없는 단계 = 미실행
4. fail → r5-gates.md "실패 시 복귀" 표대로 복귀, 같은 단계 3회 초과 시 중단·사람 알림
5. CX ≥ 1 → 즉시 fail, G5 진입 차단

## CLAUDE.md 구성 (≤ 100줄)

| 섹션 | 내용 | 상세 위치 |
|---|---|---|
| 역할 | 오케스트레이터 정의·금지 | 본문 |
| 흐름 | 8단계 + G1~G7 표 | @harness/r2-flow.md, @harness/r5-gates.md |
| 트리거 | 자연어 → 동작 표 | @harness/r6-roles.md |
| 차단 규칙 | CX-1~3 | @harness/r3-criteria.md |
| 복귀 | 요약 3줄 | @harness/r5-gates.md |
| 규칙 값 | 참조만 | @rules/design-rules.json |

- 같은 내용 두 곳에 쓰지 않음 — 수치·목록은 SSOT·harness 파일에만

## 실행 환경

| 항목 | 값 |
|---|---|
| 판정 스크립트 | `python3 scripts/gate.py G1~G7` (표준 라이브러리만) |
| 출력 | work/7-audit/report.json, work/state.json |
| hook — 편집 경계 | `.claude/settings.json` PreToolUse(Edit\|Write) → 에이전트별 폴더 밖이면 차단 |
| hook — 자동 판정 | SubagentStop → 해당 단계 게이트 실행 |
| 사전 준비 | Figma MCP 인증 1회 (현재 미인증) |

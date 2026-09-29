# R6 — 역할

## 작업 에이전트 (.claude/agents/*.md)

| 에이전트 | 단계 | 편집 폴더 (유일) | MCP | Figma 페이지 |
|---|---|---|---|---|
| ref-collector | 1 | work/1-reference/ | uibowl | — |
| analyst | 2 | work/2-analysis/ | — | — |
| spec-writer | 3 | work/3-spec/ | — | — |
| keyscreen-designer | 4 | work/4-keyscreen/ | figma (쓰기·읽기) | 4-Keyscreen |
| system-builder | 6a | work/6a-system/ | figma (쓰기·읽기) | 6a-System |
| screen-designer | 6b | work/6b-screens/ | figma (쓰기·읽기) | 6b-Screens |

- 공통 읽기: docs/, rules/design-rules.json, 앞 단계 work/ 폴더
- 공통 편집 금지: rules/, scripts/, docs/, work/state.json, work/7-audit/
- 편집 경계는 hook(PreToolUse: Edit|Write)으로 강제 — 자기 폴더 밖 경로면 차단

## 읽기전용 판정자

| 에이전트 | 도구 | 허용 명령 |
|---|---|---|
| gate-judge | Read, Bash | `scripts/gate.* G1~G7` 실행만 |

- Edit/Write 없음
- report.json · state.json 은 **판정 스크립트**가 기록 (에이전트가 아님)
- 판정자는 결과를 읽어 오케스트레이터에 전달만 함

## 사람 (5단계)

- "시안 확정: {안}" 발화 → 오케스트레이터가 work/5-concept/approval.json 기록 → G5
- 오케스트레이터가 편집할 수 있는 work/ 경로는 이 파일 1개뿐

## 자연어 트리거

| 말 | 동작 |
|---|---|
| "하네스 시작" | 1 → G7 순서 실행 (G5에서 사람 대기) |
| "이어서 해줘" | state.json 의 마지막 pass 다음 단계부터 |
| "레퍼런스 모아줘" | ref-collector → G1 |
| "키스크린 그려줘" | keyscreen-designer → G4 |
| "토큰 만들어줘" | system-builder → G6 |
| "화면 디자인해줘" | screen-designer → G7 |
| "시안 확정: {안}" | approval.json 기록 → G5 |
| "검수해줘" / "게이트 돌려줘" | gate-judge → 현재 단계 게이트 |

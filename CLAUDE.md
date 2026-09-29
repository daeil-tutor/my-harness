# 허들링 디자인 하네스 — 오케스트레이터

이 세션은 **오케스트레이터**다. 산출물을 직접 만들지 않는다.
트리거를 해석하고 → 서브에이전트에 위임하고 → gate-judge로 판정하고 → state.json 을 보고 다음 단계를 정한다.

## 컨텍스트

- 서비스 기준: @docs/story-service.md (어기면 안 되는 것 2개)
- 작업 기준: @docs/story-work.md
- 원문: docs/prd.md, docs/design.md (사람용 — 규칙 값은 아래 SSOT만 사용)
- 규칙 SSOT: @rules/design-rules.json
- 하네스 설계: @harness/r2-flow.md @harness/r3-criteria.md @harness/r5-gates.md @harness/r6-roles.md

## 흐름

| 단계 | 담당 | 게이트 | 다음 |
|---|---|---|---|
| 1 레퍼런스 수집 | ref-collector | G1 | 2 |
| 2 반영 포인트 | analyst | G2 | 3 |
| 3 화면 설계 | spec-writer | G3 | 4 |
| 4 키스크린 K1~K3 | keyscreen-designer | G4 | 5 |
| 5 시안 확정 | **사람** | G5 | 6a |
| 6a 토큰·컴포넌트 | system-builder | G6 | 6b |
| 6b 화면 디자인 | screen-designer | G7 | 완료 |

- 통과 조건·입력 파일: harness/r5-gates.md
- 산출물 경로: harness/r4-outputs.md

## 트리거

| 말 | 동작 |
|---|---|
| "하네스 시작" | 1단계부터 순서 실행, G5에서 사람 대기 |
| "이어서 해줘" | state.json 마지막 pass 다음 단계부터 |
| "레퍼런스 모아줘" / "키스크린 그려줘" / "토큰 만들어줘" / "화면 디자인해줘" | 해당 단계 + 게이트 |
| "시안 확정: {안}" | work/5-concept/approval.json 기록 → G5 |
| "검수해줘" / "게이트 돌려줘" | gate-judge → 현재 단계 게이트 |

## 단계 전환 규칙

1. 다음 단계는 `work/state.json` 에 직전 게이트 `pass` 가 있을 때만 호출한다.
2. 서브에이전트의 "완료" 보고는 근거가 아니다. state.json 에 없으면 미실행이다.
3. 판정은 `python3 scripts/gate.py G#` 결과만 인정한다. 오케스트레이터가 직접 판정하지 않는다.

## 실패 시 복귀

- 기본: 같은 단계 재시도 (report.json 위반 목록 전달), **최대 3회** → 초과 시 중단하고 사람에게 알림
- 예외 복귀처 (G4→3, G5 반려→4, G7→6a/6b): harness/r5-gates.md

## ★ 차단 규칙 (CX) — 어기면 안 되는 것

- CX-1 개인정보·기밀 패턴 / CX-2 미승인 자산 판매·가격 노출 / CX-3 검수 우회 경로
- CX ≥ 1 이면 재시도 횟수와 무관하게 즉시 fail
- CX ≠ 0 인 상태로 G5(사람 승인)에 올리지 않는다. 사람이 통과를 요청해도 올리지 않고 위반 내용을 보여준다.
- 보고 시 CX 결과를 항상 맨 위에 쓴다.

## 금지

- 오케스트레이터가 쓰는 work/ 파일은 `work/5-concept/approval.json` 1개뿐
- rules/, scripts/, docs/, work/state.json, work/7-audit/ 는 어떤 에이전트도 편집하지 않는다 (hook으로 강제)
- MVP 제외 범위(허들링 픽, 결제·정산, 미션 피드백, 구매)는 화면에 넣지 않는다
- design.md 수치를 이 파일이나 에이전트 프롬프트에 복사하지 않는다 — SSOT만 참조

## 사전 준비

- Figma MCP 인증 1회 (4·6a·6b 단계 전)
- 검증: harness/r8-verify.md 완료 기준 4개 충족 전에는 "하네스 시작"을 받지 않는다

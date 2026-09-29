# R5 — 게이트

> 판정 기준값은 rules/design-rules.json (SSOT), 규칙 ID는 r3-criteria.md.
> 판정 결과는 work/state.json 에 기록.

## 게이트 목록

| 게이트 | 위치 | 판정 | 통과 조건 | 입력 파일 |
|---|---|---|---|---|
| G1 | 1 → 2 | 기계 | 항목 = 15, 필수 4필드 누락 0, 같은 앱 ≤ 3 | 1-reference/references.json |
| G2 | 2 → 3 | 기계 | C2-1~4 위반 0 | 2-analysis/points.json |
| G3 | 3 → 4 | 기계 | 3개 파일 존재, K1~K3 필수 레이어 각 ≥ 1, **CX-3** = 0 | 3-spec/* |
| G4 | 4 → 5 | 기계 | C4-1~6 위반 0, **CX-1·2** = 0 | 4-keyscreen/snapshot.json |
| G5 | 5 → 6a | **사람** | approval.json 에 approver·date·chosen 모두 존재 | 5-concept/approval.json |
| G6 | 6a → 6b | 기계 | tokens·components 값 ⊂ SSOT 허용값 | 6a-system/* |
| G7 | 6b → 완료 | 기계 | report.json 전 규칙 위반 0 (C7-*, **CX-1·2**, 색·radius·폰트·간격·액센트) | 6b-screens/snapshot.json |

## 사람 승인 지점 (1곳)

- G5 — 컨셉 시안 확정
- 진입 조건: G4 pass (CX = 0 포함)
- 2단계·4단계의 "멈칫함"은 R3 규칙으로 기계화 → 사람 판단 없음

## 실패 시 복귀

| 실패 | 복귀 단계 | 비고 |
|---|---|---|
| 기본 (모든 기계 게이트) | 같은 단계 | report 위반 목록 전달, 최대 3회 |
| 3회 초과 | 중단 | 사람에게 알림 |
| G4 — C4-2 기준 자체 오류 | 3 | required-layers.json 수정 |
| G5 — 반려 | 4 | 반려 사유 approval.json 에 기록 |
| G7 — 토큰 값 위반 | 6a | |
| G7 — 화면 레이아웃·텍스트 위반 | 6b | |

## ★ 차단 규칙 — 어기면 안 되는 것 (CX)

| 규칙 | 걸리는 게이트 | story-service 근거 |
|---|---|---|
| CX-1 개인정보·기밀 패턴 0건 | G4, G7 | 금지 1 |
| CX-2 미승인 자산 판매·가격 노출 0건 | G4, G7 | 금지 2 |
| CX-3 검수 우회 경로 0개 | G3 | 금지 2 |

- CX ≥ 1 → 재시도 횟수와 무관하게 즉시 fail
- CX ≠ 0 인 상태로 G5(사람 승인) 진입 불가 — 사람이 무시하고 통과시킬 수 없음
- report.json 최상단에 CX 결과 별도 표기

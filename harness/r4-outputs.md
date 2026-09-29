# R4 — 산출물

> 판정 대상은 Figma 원본이 아니라 레포 안의 JSON 스냅샷이다.

## 단계별 파일

| 단계 | 파일 | 형식 | 판정 규칙 |
|---|---|---|---|
| 1 | work/1-reference/references.json | `[{app, ui_url, screen_type, point, keyscreen}]` × 15 | 수집 기준(R2) |
| 2 | work/2-analysis/points.json | `[{keyscreen, point, prd_ref, ui_url}]` | C2-1~4 |
| 3 | work/3-spec/screen-spec.md | 마크다운 | — |
| 3 | work/3-spec/required-layers.json | `{K1:[...], K2:[...], K3:[...]}` | C4-2 기준값 |
| 3 | work/3-spec/flows.json | `{nodes:[...], edges:[[from,to]]}` | CX-3 |
| 4 | work/4-keyscreen/snapshot.json | Figma 노드 export | C4-1~6, CX-1~2 |
| 5 | work/5-concept/approval.json | `{approver, date, chosen}` | 사람 승인 |
| 6a | work/6a-system/tokens.json, components.json | 토큰/컴포넌트 정의 | SSOT 값 대조 |
| 6b | work/6b-screens/snapshot.json | Figma 노드 export | C7-1~4, CX-1~2 |
| 7 | work/7-audit/report.json | `{rule_id: 위반건수, details:[...]}` | 전 규칙 |

## 스냅샷 필수 필드 (4·6b)

frame(w,h) · layer name · fills · strokes(weight, color) · effects · cornerRadius · text · fontFamily · fontWeight · letterSpacing

## 규칙 SSOT

- 파일: `rules/design-rules.json` (1개)
- 키: R3 규칙 ID (C2-*, C4-*, C7-*, CX-*) + 토큰 허용값
  - colors(9) · radius[0,16,24,9999] + squircle 30% · font Pretendard · weight[300,400,600,700]
  - letterSpacing 0 · spacing[4,8,12,16,24,32,48,64] · accent ≤2/화면, 버튼 fill 0
- 에이전트·스크립트 모두 이 파일만 참조. design.md는 사람용 원문.
- 실물 생성: R8 이전

## 재개

- `work/state.json`: `[{step, gate: "pass"|"fail", at}]`
- 재시작 → 마지막 pass 단계의 다음 단계부터
- 이전 단계 산출물이 수정되면 → 그 단계부터 재판정

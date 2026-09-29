# R8 — 검증과 리뷰

## 1. 판정 스크립트 검증 (fixture)

- 위치: tests/fixtures/{rule_id}/pass.json, fail.json
- 규칙 ID마다 pass ≥ 1, fail ≥ 1
- 실행: `python3 tests/run.py` → 기대값 불일치 0건

### CX 심은 위반 (100% 검출 필수)

| 규칙 | fail fixture 내용 | 기대 |
|---|---|---|
| CX-1 | 더미 텍스트에 `kim@example.com`, `010-1234-5678` | G4·G7 fail |
| CX-2 | review_status = 검수 대기 자산에 가격 텍스트 노출 | G4·G7 fail |
| CX-3 | flows.json 에 판매 신청 → 승인됨 직행 edge | G3 fail |

## 2. 드라이런

| 차수 | 범위 | Figma | 통과 조건 |
|---|---|---|---|
| 1차 | G1~G7 스크립트 + hook | 사용 안 함 (fixture 스냅샷) | tests/run.py 불일치 0 |
| 2차 | 1단계 → G4 실제 실행 (K1~K3) | 사용 | G1~G4 pass, G5에서 정지 |

- 6a·6b 는 2차 통과 후 진행

## 3. 하네스 리뷰 — 규칙 추적표

| 확인 | 판정 |
|---|---|
| R3 규칙 ID × {SSOT 키, gate.py 함수, fixture, R5 게이트} | 누락 0건 |
| design.md Do's & Don'ts 16항목 → SSOT 규칙 매핑 또는 "기계 판정 불가(사람 확인)" 분류 | 미분류 0건 |

- 추적표 파일: harness/traceability.md (R8 실행 시 생성)

## 4. 완료 기준 (4개 모두)

1. tests/run.py 불일치 0건
2. hook 차단 테스트 통과
   - analyst → rules/ 쓰기 시도 → 차단
   - gate-judge → Edit 시도 → 차단
3. 2차 드라이런 G1~G4 pass
4. 추적표 누락 0건

## 운영 루프

- 사람이 발견했지만 스크립트가 놓친 위반 → 규칙 ID 추가(r3) → SSOT → gate.py → fixture → 재판정

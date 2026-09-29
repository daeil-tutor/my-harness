# 규칙 추적표 (R8)

> 자동 확인: `python3 tests/run.py` 3번 섹션 (규칙 ID × SSOT · gate.py · fixture · 게이트)
> 이 문서는 사람이 확인하는 부분 — design.md Do's & Don'ts 16항목의 매핑.

## 1. 규칙 ID → 게이트 (2026-09-29 run.py 결과: 33개 전부 OK)

| 출처 | 규칙 ID | 게이트 |
|---|---|---|
| r2 수집 기준 | G1-1 개수 · G1-2 필수 필드 · G1-3 앱당 최대 | G1 |
| r3 C2 | C2-1 ~ C2-4 | G2 |
| r5 G3 | G3-1 파일 존재 · G3-2 필수 레이어 ≥1 | G3 |
| r3 C4 | C4-1 ~ C4-6 | G4 |
| r5 G5 | G5-1 승인 필드 · G5-2 진입 조건(G4 pass, CX=0) | G5 |
| r5 G6 | G6-1 토큰 값 ⊂ SSOT | G6 |
| r4 SSOT 토큰 | T-1 색 · T-2 radius · T-3 폰트 · T-4 굵기 · T-5 자간 · T-6 간격 | G7 |
| r4 액센트 | A-1 화면당 ≤2 · A-2 버튼 fill 0 | G7 |
| r3 C7 | C7-1 ~ C7-4 | G7 |
| r3 CX ★ | CX-1 · CX-2 | G4, G7 |
| r3 CX ★ | CX-3 | G3 |

> G1-*, G3-*, G5-*, G6-1, T-*, A-* 는 r2·r4·r5 에서 확정한 조건에 구현 시 ID 를 붙인 것.

## 2. design.md Do's & Don'ts 16항목

| # | 항목 | 매핑 | 비고 |
|---|---|---|---|
| Do 1 | 캔버스 흰색, 채도는 콘텐츠만 | T-1 | 이미지 내부 색은 판정 제외 |
| Do 2 | 모든 인터랙티브 요소 `rounded.full` | **사람 확인** | 추가 후보: `button` 레이어 radius = 9999 |
| Do 3 | tint ladder 로 강조 | T-1, C7-3 | |
| Do 4 | 액센트는 상업 신호, 화면당 1~2개 | A-1, A-2 | "상업 신호" 여부는 사람 확인 |
| Do 5 | 헤딩 Bold 700, line-height 1.3–1.35 | T-4 (부분) | 추가 후보: 헤딩 line-height |
| Do 6 | 700 헤딩 + 300 리드 대비 | **사람 확인** | |
| Do 7 | 앱 아이콘 30% squircle, 인물 흑백 | T-2 (squircle) | 흑백 여부는 사람 확인 |
| Do 8 | ink 푸터, 상단 라운드 | **사람 확인** | |
| Don't 1 | 그림자 금지 | C7-1, G6-1 | 예외 segmented-control-active |
| Don't 2 | 액센트를 CTA 에 쓰지 않음 | A-2 | |
| Don't 3 | 추가 액센트·UI 그라디언트·컬러 밴드 금지 | T-1 (부분) | 추가 후보: GRADIENT fill 검출 |
| Don't 4 | featured 카드 outline 금지 | C7-4 (색 반전만) | outline 여부는 사람 확인 |
| Don't 5 | 자간·전부 대문자 금지 | T-5 | 대문자는 사람 확인 |
| Don't 6 | 입력창 기본 상태에 border 금지 | **사람 확인** | 추가 후보: `text-input` stroke 0 (focus 제외) |
| Don't 7 | 인물 사진 컬러 금지 | **사람 확인** | |
| Don't 8 | 작은 pill 도 각지게 하지 않음 | **사람 확인** | Do 2 와 같은 후보 규칙으로 해결 가능 |

미분류 0건. "추가 후보"는 r3 에 규칙 ID 를 추가하면 운영 루프(r8)로 편입한다.

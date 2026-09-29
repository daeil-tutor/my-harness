# 스냅샷 · 입력 파일 스키마

> scripts/gate.py 가 읽는 형식. 작업 에이전트는 이 형식 그대로 저장한다.
> 허용 값(색·radius·간격 등)은 rules/design-rules.json 만 참조한다.

## snapshot.json (4-keyscreen, 6b-screens)

Figma MCP로 프레임을 읽어 아래 형태로 정규화해 저장한다.

```json
{
  "figma_file": "<figma url>",
  "screens": [
    {
      "id": "K1", "name": "홈", "width": 390, "height": 844,
      "fills": [{"color": "#ffffff"}],
      "children": [
        {
          "name": "asset-card/draft", "type": "FRAME",
          "fills": [{"color": "#ffffff", "opacity": 1}],
          "strokes": [{"color": "#f0f0f0", "weight": 1}],
          "effects": [],
          "cornerRadius": 24,
          "itemSpacing": 8, "padding": [24, 24, 24, 24],
          "width": 358, "height": 160,
          "children": [
            {"name": "title", "type": "TEXT", "text": "QA 자동화 스킬",
             "fontFamily": "Pretendard", "fontWeight": 700, "fontSize": 20, "letterSpacing": 0,
             "fills": [{"color": "#141414"}]}
          ]
        }
      ]
    }
  ]
}
```

| 필드 | 규칙 |
|---|---|
| `id` | 키스크린은 K1·K2·K3. 6b 화면은 자유 (S01…) |
| `fills`/`strokes` | `color` 는 `#rrggbb` 또는 `rgba()`. 반투명이면 `opacity` |
| `effects` | Figma effect 그대로 (`type`: DROP_SHADOW 등) |
| `cornerRadius` | 숫자 또는 [tl,tr,br,bl]. **pill 은 9999** 로 기록 (높이/2 아님) |
| `padding` | [top,right,bottom,left] |
| 텍스트 | `text`, `fontFamily`, `fontWeight`, `letterSpacing` 필수 |

### 레이어 이름 규칙 (판정에 쓰임 — rules/design-rules.json `layer_patterns`)

| 대상 | 이름에 포함 |
|---|---|
| 버튼 | `button` / `btn` / `cta` |
| 입력창 | `text-input` / `input` / `field` |
| 카드 | `card` |
| 자산 카드 (상태·가격이 함께 보이는 단위) | `asset-card` |
| 앱 아이콘 (squircle) | `app-icon` |
| 그림자 허용 | `segmented-control-active` |

## references.json (1-reference)

```json
[{"app": "토스", "ui_url": "https://...", "screen_type": "홈", "point": "…", "keyscreen": "K1"}]
```

## points.json (2-analysis)

```json
[{"keyscreen": "K2", "point": "…", "prd_ref": ["6-5"], "ui_url": ["https://..."]}]
```

## required-layers.json · flows.json (3-spec)

```json
{"K1": ["nav-pill", "…"], "K2": ["visibility-segmented", "…"], "K3": ["review-checklist", "…"]}
```

```json
{
  "nodes": [{"id": "sale_request", "label": "판매 신청"}, {"id": "admin_review", "label": "운영자 검수"},
            {"id": "revision_requested"}, {"id": "approved"}, {"id": "rejected"}],
  "edges": [["sale_request", "admin_review"], ["admin_review", "approved"],
            ["admin_review", "revision_requested"], ["revision_requested", "sale_request"],
            ["admin_review", "rejected"]]
}
```

노드 id `sale_request` · `admin_review` · `approved` 는 필수 (CX-3 판정 기준).

## approval.json (5-concept) — 오케스트레이터가 기록

```json
{"approver": "이름", "date": "2026-09-29", "chosen": "A안", "note": "반려 시 사유"}
```

## tokens.json · components.json (6a-system)

자유 구조(W3C design tokens 형식 권장). 키 이름으로 판정한다:
`*radius*`/`rounded` → radius, `*spacing*`/`padding`/`gap`/`margin` → 간격, `fontWeight`, `fontFamily`, `letterSpacing`, `*shadow*`/`effect` → 그림자, `#hex`/`rgba()` 문자열 → 색. `{colors.ink}` 같은 참조는 판정 제외.

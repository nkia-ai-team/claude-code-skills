# Menu path 자동 검증 스크립트

`feature` frontmatter 값을 polestar10 통합 검색에 입력해서 메뉴 트리에 실제로 존재하는지 자동 검증하고, EXACT 매치인 경우 `menu_path_verified: true` 토글 + `menu_path_full` 필드를 추가합니다.

## 의존성

```bash
npm i playwright
npx playwright install chromium
```

## 환경변수

| 변수 | 설명 | 예 |
|---|---|---|
| `POLESTAR_BASE` | polestar10 호스트 root | `https://192.168.230.104/` |
| `POLESTAR_USER` | 로그인 ID | (시크릿) |
| `POLESTAR_PASS` | 로그인 비밀번호 | (시크릿) |
| `POLESTAR_REPO` | claude-code-skills 레포 root (생략 시 스크립트 위치 기준 자동 추론) | `/path/to/claude-code-skills` |
| `POLESTAR_OUT` | 출력 디렉토리 (JSONL 결과 + apply-report.json) | `/tmp/polestar10-validation` |

비밀번호는 절대 커밋하지 마세요. `.env` 또는 셸 export 로만 전달.

## 실행 순서

```bash
export POLESTAR_BASE=https://192.168.230.104/
export POLESTAR_USER=<id>
export POLESTAR_PASS=<pw>

# 1. 1차 검증 (모든 매뉴얼, ~9분)
node validate-menu-paths.mjs

# 2. 2차 검증 (NONE 항목에 prefix 변형 적용, ~6분)
node validate-menu-paths-retry.mjs

# 3. frontmatter 적용 (변경 미리보기는 --dry-run)
node apply-validation-results.mjs --dry-run
node apply-validation-results.mjs
```

## 산출물

- `$POLESTAR_OUT/dumps/validation-results-v2.jsonl` — 1차 검증 raw
- `$POLESTAR_OUT/dumps/validation-retry.jsonl` — 2차 검증 raw
- `$POLESTAR_OUT/dumps/apply-report.json` — 최종 분류 + 요약
- 매뉴얼 frontmatter: EXACT 항목에 `menu_path_verified: true` + `menu_path_full: "[A] > [B] > [C]"`

## 안전 규약

검증 스크립트는 **메뉴 검색창에 텍스트를 입력하는 동작만** 수행합니다. 검색 결과의 "바로가기" 버튼·등록·저장·수정·삭제 버튼을 클릭하지 않고, 대시보드 외 페이지로 이동하지도 않습니다. polestar10 사용자 데이터에 영향 0.

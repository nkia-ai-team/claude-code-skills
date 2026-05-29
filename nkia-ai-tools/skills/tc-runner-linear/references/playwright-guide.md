# Playwright 실행 가이드 (192.168.230.104)

테스트 서버 `https://192.168.230.104/` 에서 TC 절차를 자동 수행한다.
실행 베이스: `scripts/lib/tc-runner.mjs`, 이슈별 스펙: `scripts/generated/<LinearID>-<tcId>.spec.mjs`.

## 환경 (lucida-ui node_modules 재활용)

- Playwright 1.58.x + chromium 이 **`./lucida-ui/node_modules`** 에 설치되어 있어야 함.
- `tc-runner.mjs` 가 절대경로 동적 import → **별도 설치 불필요**.
- self-signed 인증서는 `ignoreHTTPSErrors: true` 로 무시.
- 브라우저 미설치 오류 시:
  ```bash
  cd "$LUCIDA_UI_DIR" && npx playwright install chromium
  ```

## 환경변수 (기본값 내장, 필요 시 덮어쓰기)

| 변수 | 기본값 |
|------|--------|
| `TC_BASE_URL` | `https://192.168.230.104/` (Polestar10, NKIA 공통 기본) |
| `TC_USER` / `TC_PASS` | credentials 또는 env 로 설정. 최초 setup 인터뷰 (SKILL.md Step -1) |
| `TC_ORG` | 조직 선택 화면에서 고를 조직. 기본 `MyOrganization` |
| `LUCIDA_UI_DIR` | credentials 또는 env 로 설정 (환경마다 다름, 예: `~/dev/lucida-ui`) |
| `TC_OUT_DIR` | `scripts/runs/latest` (스크린샷·results.json) |
| `TC_HEADLESS` | 기본 headless. `false` 면 창 표시(디버깅) |

## 스펙 작성 규칙

- `_example.spec.mjs` 를 복사해 시작.
- `run.step('<TC 절차 번호+문구>', async (page) => { ... })` — **이름을 TC 절차와 1:1**.
- 예상결과 검증은 step 콜백 안에서 단언 → 실패 시 자동 Fail + 스크린샷.
  - 간단: `await page.locator(sel).waitFor()`, `if ((await loc.count()) < 1) throw new Error('...')`
  - 정밀: lucida-ui 의 `@playwright/test` 에서 `expect` 동적 import.
- 셀렉터는 **`./lucida-ui` 소스에서 확인한 실제 값** (`ui-map.md` 참고).
- step 마다 자동 스크린샷이 `TC_OUT_DIR` 에 `NN-<이름>.png` 로 저장.

## 로그인 동작

`run.login()`:
1. `#loginId`/`#password` 입력 후 Enter.
2. 조직 선택 화면(`.login-body-org-content-body-list-box`)이 뜨면 `TC_ORG` (기본 `MyOrganization`) 자동 클릭.
3. `/login` 을 벗어나면 성공 (`results.login.ok === true`, 진입 후 보통 `/portal/ems`).

2차 인증 등 추가 화면이 있으면 `ok === false` 가 되고 폼이 남음. `01-login.png` 로 확인 후 generated 스펙에서 후속 단계 추가.

## 실행 & 결과

```bash
node scripts/generated/<LinearID>-<tcId>.spec.mjs
```

- 콘솔에 절차별 `[PASS]/[FAIL]` 출력.
- `TC_OUT_DIR/results.json` 에 `summary{total,pass,fail}` + step별 결과·스크린샷 경로.
- 이 results.json + 스크린샷으로 PIMS 댓글(note)을 구성.

## Positive / Negative 분리 실행

TC 가 쌍이면 스펙도 쌍으로 작성하고 출력 폴더 분리:
```bash
TC_OUT_DIR=scripts/runs/NKIAAI-498-positive \
  node scripts/generated/NKIAAI-498-positive.spec.mjs

TC_OUT_DIR=scripts/runs/NKIAAI-498-negative \
  node scripts/generated/NKIAAI-498-negative.spec.mjs
```

PIMS 댓글에는 둘 다 표로 기록.

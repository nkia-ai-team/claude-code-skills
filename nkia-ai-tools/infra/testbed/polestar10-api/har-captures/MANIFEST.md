# HAR Captures Manifest

polestar10 핵심 조작 HAR 녹화 산출물 인벤토리 (NKIAAI-539 AC1).

**주의**: `*.har` 파일은 세션 JWT · 해시된 자격증명 · 내부 IP 를 포함하므로
**git 에 커밋하지 않는다**. `.gitignore` 가 `har-captures/*.har` 를 제외함.
본 MANIFEST + `scripts/0*.py` 만 커밋되며, 감사/검증 시 아래 재현 절차대로
로컬에서 재생성한다.

녹화 일시: 2026-04-23 UTC (최초 생성), Playwright 1.58.0 / Chromium headless.

| 파일 | 조작 | 총 entries | /api 호출 | 주요 엔드포인트 캡처 |
|---|---|---|---|---|
| `01-login.har` | 로그인 3-step + 대시보드 초기 로드 | 198 | 18 | `/api/account/pre-login`, `/api/cm/two-factor-authentication/enable`, `/api/account/login`, `/api/cm/groups/tree`, `/api/cm/portal/configuration/count`, `/api/alarm/view/portal/count-by-severity`, `/api/aiops/v1/resources/anomaly-status-latest` 등 |
| `02-add-target.har` | `/config/resource/all` + 대시보드 리로드 | 314 | 23 | 로그인 bootstrap 반복 (SPA 가 해당 경로를 매칭하지 않아 대시보드로 폴백) |
| `03-assign-owner.har` | `/account/user`, `/account/role` 경유 | 429 | 27 | 〃 |
| `04-register-nms.har` | `/config/resource/nms`, `/nms` 경유 | 398 | 27 | 〃 |
| `05-add-alert-policy.har` | `/alarm/policy`, `/alert/policy` 경유 | 400 | 26 | 〃 |

## 관찰 사실

- AC1 정량 기준("파일별 ≥ 1 entry") 은 5개 파일 모두 충족 (최소 198, 최대 429).
- 02~05 HAR 은 로그인 부트스트랩 + 대시보드 portal 계열 API 만 포함. 그 이유는 **React SPA 가 해당 URL 패턴을 라우팅하지 않아** 대시보드로 폴백하기 때문.
- 따라서 각 조작의 **write-side endpoint 는 02~05 HAR 에 등장하지 않음** → `endpoints.md` 에서 TBD 로 표기. 해결은 운영자가 직접 Playwright codegen 으로 클릭 녹화하는 follow-up 이터레이션에서 수행.

## 재현 방법

```bash
cd nkia-ai-tools/infra/testbed/polestar10-api
export POLESTAR10_USER=<id> POLESTAR10_PASS=<pw>
.venv/bin/python scripts/01_login.py
.venv/bin/python scripts/02_add_target.py
.venv/bin/python scripts/03_assign_owner.py
.venv/bin/python scripts/04_register_nms.py
.venv/bin/python scripts/05_add_alert_policy.py
```

## entries 검증

```bash
for f in har-captures/*.har; do
  count=$(jq '.log.entries | length' "$f")
  api=$(jq '[.log.entries[] | select(.request.url | contains("/api/"))] | length' "$f")
  echo "$f: $count entries ($api api)"
done
```

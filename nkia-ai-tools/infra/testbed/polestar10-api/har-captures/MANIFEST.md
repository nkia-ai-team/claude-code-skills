# HAR Captures Manifest

polestar10 핵심 조작 HAR 녹화 결과물 (NKIAAI-539 AC1).

| 파일 | 조작 | 엔드포인트 수 | 녹화 일시 |
|---|---|---|---|
| `01-login.har` | 로그인 | TBD | TBD |
| `02-add-target.har` | 관리대상 추가 | TBD | TBD |
| `03-assign-owner.har` | 담당자 권한 부여 | TBD | TBD |
| `04-register-nms.har` | NMS 네트워크 등록 | TBD | TBD |
| `05-add-alert-policy.har` | 개별 알람 정책 등록 | TBD | TBD |

재현:

```bash
cd ../
export POLESTAR10_USER=<username>
export POLESTAR10_PASS=<password>
.venv/bin/python scripts/01_login.py
.venv/bin/python scripts/02_add_target.py
# ... 등
```

행 개수 확인:

```bash
for f in har-captures/*.har; do
  echo -n "$f: "
  jq '.log.entries | length' "$f"
done
```

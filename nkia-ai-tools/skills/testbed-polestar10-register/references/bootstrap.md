# Bootstrap — 세션 시작 시 환경 셋업

매 세션 첫 호출 시 한 번 실행. 이후에는 `source ~/.polestar10rc` + 쿠키 검증만.

---

## Step 0 — rc 파일 존재 체크

```bash
[ -f ~/.polestar10rc ] && echo EXISTS || echo MISSING
```

`EXISTS` 면 Step 4 로. `MISSING` 이면 Step 1~3.

---

## Step 1 — URL 인터뷰

사용자에게 다음 메시지 표시:

```
Polestar10 Web 주소를 알려주세요.
  1) https://198.51.100.104  (NKIA dev / polestar-app-itg-1)
  2) 자유 입력
선택:
```

- `1` → `URL=https://198.51.100.104`
- `2` → 사용자에게 URL 직접 입력받기 (https://… 형식 검증)

> 알려진 인스턴스 표는 [knowledge/polestar10/api/README.md "알려진 polestar10 인스턴스"](../../../knowledge/polestar10/api/README.md) 참조.

---

## Step 2 — URL 검증

`POST /api/account/pre-login` 으로 더미 자격증명 한 번 시도. polestar10 인스턴스 맞다면 `success:true` 또는 `success:false + errorCode:"INVALID_CREDENTIALS"` 응답.

```bash
curl -sk -X POST \
  -H 'Content-Type: application/json' \
  -d '{"loginId":"__probe__","password":"__probe__"}' \
  "$URL/api/account/pre-login"
```

**판정**:

| 응답 | 판정 | 처리 |
|---|---|---|
| `{"success":true,...}` 또는 `{"success":false,"errorCode":"INVALID_CREDENTIALS",...}` | OK | Step 3 진행 |
| `404` / HTML / `Connection refused` / 타임아웃 | NOT polestar10 | URL 다시 입력 prompt |
| `success:false` + 다른 errorCode | 인스턴스는 맞으나 다른 문제 | errorCode 그대로 표시 + 진행 여부 prompt |

---

## Step 3 — 자격증명 인터뷰 + rc 작성

사용자에게 다음 prompt 표시 (비밀번호는 `read -rs` 로 화면 노출 방지):

```bash
read -rp "POLESTAR10_USER (계정): " USER_VAR
read -rsp "POLESTAR10_PASS (비밀번호, 화면에 표시되지 않음): " PASS
echo
```

> 비밀번호는 **평문** 으로 받음. recipe 의 login 단계에서 sha512 해싱.
> `read -rs` 가 echo 차단해서 화면에 안 보임. `-r` 로 backslash 도 literal 처리.

`~/.polestar10rc` 작성 — **placeholder 치환 패턴** (Bash 툴):

> ⚠️ heredoc 안의 `__URL__` / `__USER__` / `__PASS__` 는 **placeholder**. quoted heredoc (`<<'EOF'`) 으로 안전하게 작성한 뒤 `sed` 로 치환. 비밀번호에 `$` / backtick 같은 셸 메타문자가 있어도 안전.

```bash
umask 077
cat > ~/.polestar10rc <<'EOF'
# polestar10 session env — managed by testbed-polestar10-register skill
export POLESTAR10_BASE_URL="__URL__"
export POLESTAR10_USER="__USER__"
export POLESTAR10_PASS="__PASS__"
export POLESTAR10_COOKIE_JAR="$HOME/.polestar10.cookies"
export POLESTAR10_CURL_OPTS="-sk"
EOF

# placeholder 치환 — 구분자에 % 사용 (URL 의 / 와 충돌 회피)
sed -i "s%__URL__%${URL}%; s%__USER__%${USER_VAR}%; s%__PASS__%${PASS}%" ~/.polestar10rc

chmod 600 ~/.polestar10rc
unset PASS  # 메모리에서 비밀번호 즉시 제거
```

> 보안 정책: rc 파일 권장하지만 사용자가 거부하면 세션 한정 env 만으로 진행 가능. 재로그인 때마다 자격증명 재입력 trade-off (handoff note §1).

---

## Step 4 — 환경 주입 + 로그인

```bash
source ~/.polestar10rc
```

이미 유효한 쿠키가 있으면 재로그인 skip:

```bash
if [ -s "$POLESTAR10_COOKIE_JAR" ]; then
  VALID=$(curl $POLESTAR10_CURL_OPTS -X POST \
    --cookie "$POLESTAR10_COOKIE_JAR" \
    "$POLESTAR10_BASE_URL/api/account/token/valid" \
    | jq -r .success)
  [ "$VALID" = "true" ] && echo "session reused" && exit 0
fi
```

유효하지 않으면 `recipes/login.md` 실행 (Read → bash 블록 추출 → Bash 실행).

---

## Step 5 — 캐시 워밍 (선택)

이후 인터뷰에서 자주 쓰일 메타를 미리 받아두면 응답이 빨라짐. handoff note §5 캐시 가능 항목:

- `cm/groups/list` → 그룹 dropdown
- `cm/tag/key/list` → tag 스키마
- `aiops/v1/anomaly-policies/names` → 이상감지 정책 dropdown
- `alarm/severity/find-all` → severity 메타

전부 read-only 이고 응답이 작음. 백그라운드로 한 번에 받아 세션 변수에 보관.

---

## Bootstrap 완료 후

세션 변수 상태 (이후 모든 시나리오의 사전조건):

```
POLESTAR10_BASE_URL  =  https://...
POLESTAR10_USER      =  ...
POLESTAR10_PASS      =  ...   (해싱은 login recipe 가)
POLESTAR10_COOKIE_JAR=  ~/.polestar10.cookies   (accessToken/refreshToken 심김)
```

이 상태가 되면 어떤 recipe 든 `source ~/.polestar10rc && <recipe bash>` 로 그대로 실행 가능.

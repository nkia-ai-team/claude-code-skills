# Recipe: 로그인

polestar10 웹 3단계 챌린지-리스폰스 로그인. 성공 시 세션 쿠키가 `$POLESTAR10_COOKIE_JAR` 에 심어지며, 이후 다른 recipe 에서 `--cookie "$POLESTAR10_COOKIE_JAR"` 로 재사용.

- **엔드포인트**: `POST /api/account/pre-login` → `POST /api/cm/two-factor-authentication/enable` → `POST /api/account/login`
- **인증 불필요** (세션 생성 자체)
- **실행 후 필요 파일**: `$POLESTAR10_COOKIE_JAR`

## 전제 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_USER:?POLESTAR10_USER 환경변수 설정 필요}"
: "${POLESTAR10_PASS:?POLESTAR10_PASS 환경변수 설정 필요}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

## 레시피

```bash
# 1) 비밀번호 sha512 해싱
PWD_HASH=$(printf '%s' "$POLESTAR10_PASS" | sha512sum | awk '{print $1}')

# 2) pre-login: challenge + organization 획득
PRE=$(curl $POLESTAR10_CURL_OPTS -X POST \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg u "$POLESTAR10_USER" --arg p "$PWD_HASH" \
        '{loginId:$u, password:$p}')" \
  "$POLESTAR10_BASE_URL/api/account/pre-login")

# 응답 성공 여부 체크
if [ "$(echo "$PRE" | jq -r .success)" != "true" ]; then
  echo "pre-login failed: $(echo "$PRE" | jq -r .errorCode)" >&2
  return 1 2>/dev/null || exit 1
fi

CHALLENGE=$(echo "$PRE" | jq -r .data.challenge)
ORG_ID=$(echo "$PRE"    | jq -r '.data.organizations[0].organizationId')

# 3) MFA 활성 여부 체크 (활성이면 recipe 중단)
MFA=$(curl $POLESTAR10_CURL_OPTS -X POST \
  -H 'Content-Type: application/json' \
  -d '{"parameter":"SECONDARY_CERTIFICATION"}' \
  "$POLESTAR10_BASE_URL/api/cm/two-factor-authentication/enable")

if [ "$(echo "$MFA" | jq -r '.data | [.enable, .email, .sms, .otp] | any')" = "true" ]; then
  echo "MFA enabled for $POLESTAR10_USER — TOTP 경로 필요 (UI fallback)" >&2
  return 2 2>/dev/null || exit 2
fi

# 4) challengeResponse 계산
CHALLENGE_RESP=$(printf '%s%s' "$PWD_HASH" "$CHALLENGE" | sha512sum | awk '{print $1}')

# 5) 실제 로그인 — 성공 시 accessToken/refreshToken 쿠키 저장
LOGIN=$(curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie-jar "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
        --arg u "$POLESTAR10_USER" \
        --arg c "$CHALLENGE" \
        --arg r "$CHALLENGE_RESP" \
        --arg o "$ORG_ID" \
        '{loginId:$u, challenge:$c, challengeResponse:$r, organizationId:$o}')" \
  "$POLESTAR10_BASE_URL/api/account/login")

if [ "$(echo "$LOGIN" | jq -r .success)" != "true" ]; then
  echo "login failed: $(echo "$LOGIN" | jq -r .errorCode)" >&2
  return 3 2>/dev/null || exit 3
fi

echo "login OK — userId=$(echo "$LOGIN" | jq -r .data.userId)"
```

## 성공 예시

```
login OK — userId=xxxxxxxxxxxxxxxxxxxxxxxx
```

이후 쿠키 파일 내용:

```
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
<POLESTAR_HOST>  FALSE  /  TRUE  <expiry>  accessToken  eyJ0eXAi...
<POLESTAR_HOST>  FALSE  /  TRUE  <expiry>  refreshToken eyJ0eXAi...
```

## 검증 — 로그인 성공 후 인증 유효성 체크

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/account/token/valid"
# → {"success":true,"data":{...},"errorCode":null,...}
```

## 실패 시나리오

| 증상 | 원인 | 대응 |
|---|---|---|
| `pre-login failed: INVALID_CREDENTIALS` | 아이디/비밀번호 불일치 | 자격증명 확인 |
| `MFA enabled for ...` | 해당 계정에 2FA 설정됨 | UI 로그인으로 우회 (UI Fallback 섹션) |
| `login failed: CHALLENGE_EXPIRED` | pre-login 과 login 사이 시간차 큼 (>60s 추정) | recipe 를 처음부터 재실행 |
| `login failed: ACCOUNT_LOCKED` | 실패 횟수 누적 | 관리자에게 잠금 해제 요청 |

## UI Fallback

API 로그인이 실패 — 사용자에게 다음 가이드 제공:

> 브라우저에서 `$POLESTAR10_BASE_URL/login` 접속 → 아이디/비밀번호 입력 → (MFA 활성 시 2차 인증) → 로그인. 이후 브라우저 DevTools `Application → Cookies` 에서 `accessToken` 값을 복사해 수동으로 `$POLESTAR10_COOKIE_JAR` 작성 가능하지만 권장하지 않음.

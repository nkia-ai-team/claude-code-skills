# Polestar10 에러 처리 표준 패턴

testbed-build 의 모든 phase + sub-skill 에서 공통.

## 에러 분류 (먼저 분기)

### A. Network error (인프라 영역)
- `connection refused`
- `no route to host`
- `connection timeout`
- `Could not resolve host`
- TCP RST

→ ask-polestar10 우회. 인프라 점검 안내. (매뉴얼이 도움 안 됨)

### B. API error (매뉴얼 영역)
- HTTP 200 + `success: false` + `errorCode`
- HTTP 4xx (400/401/403/404/422)
- HTTP 5xx (500/502/503)
- 응답 형식 예외 (예상 필드 누락)

→ ask-polestar10 호출 가치 있음. 매뉴얼이 errorCode 의미 + 화면 절차 알려줌.

### C. 자격증명 영역
- HTTP 401 (login 만료)
- HTTP 403 (권한 부족)

→ 자동 재로그인 1회 (recipes/login.md 다시 실행). 그래도 401 면 사용자 prompt: "자격증명 다시 입력?"

## Reachability precheck (Phase 2)

본격적인 phase 진입 전 — **server 도달성만** 검사. 실제 auth 검증은 testbed-polestar10-register 의 login.md recipe 가 처리 (그게 실제 endpoint `/api/account/pre-login` 사용). Polestar10 버전/배포 형태마다 auth path 가 다르므로 본 단계에서는 hardcode X.

```bash
# 10초 timeout, self-signed cert 무시 (-k), root URL 만 GET
HTTP_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" -m 10 \
  "$POLESTAR10_BASE_URL/")

case "$HTTP_CODE" in
  000)
    cat <<EOF
[precheck] Polestar10 도달 불가 (network).

조치:
  - $POLESTAR10_BASE_URL 가 정상 동작 중인지 확인
  - controller → Polestar10 네트워크 (방화벽 / VPN / DNS) 확인
  - bootstrap.yaml 의 polestar10.base_url 오타 확인
EOF
    update_manifest_phase "precheck" "failed"
    exit 1
    ;;
  *)
    # HTTP 200/3xx/4xx 모두 reachable 의미. 5xx 도 controller 입장에선 도달 가능.
    echo "[precheck] Polestar10 reachable (HTTP $HTTP_CODE)"
    ;;
esac
```

> 어떤 HTTP code 든 (000 만 빼고) "controller 가 host 에 도달 가능" 의미. 실제 auth endpoint 동작은 login.md 가 호출 시 검증.

## Sub-skill 안의 에러 처리 표준

testbed-polestar10-register / testbed-tune-alarms 가 Polestar10 호출 시:

```bash
# 1. recipe 실행
RESPONSE=$(curl -sS --cookie-jar "$JAR" "$POLESTAR10_BASE_URL/api/...")
SUCCESS=$(jq -r '.success' <<< "$RESPONSE")
ERROR_CODE=$(jq -r '.errorCode' <<< "$RESPONSE")

if [ "$SUCCESS" = "true" ]; then
  return 0
fi

# 2. 알려진 errorCode → recipe md 의 ## UI Fallback 섹션 참조
case "$ERROR_CODE" in
  "AUTH_EXPIRED")
    # 자동 재로그인
    bash recipes/login.md
    return 1   # caller 가 재호출
    ;;
  "RESOURCE_DUPLICATE")
    echo "이미 등록된 자원. skip."
    return 0
    ;;
  *)
    # 3. 알려지지 않은 errorCode → ask-polestar10 호출
    invoke_ask_polestar10 "<API path> 가 errorCode=$ERROR_CODE 반환. 매뉴얼에서 어디 보면 좋을까?"
    return 1
    ;;
esac
```

## ask-polestar10 자동 호출 패턴

```bash
invoke_ask_polestar10() {
  local question="$1"
  # Skill 도구로 ask-polestar10 호출
  local manual_answer=$(claude_invoke_skill "ask-polestar10" "$question")
  cat <<EOF

=== ask-polestar10 응답 ===
$manual_answer
EOF
  read -r -p "위 안내 따라 조치 후 재시도? [Y/n] " ANS
  [ "$ANS" != "n" ]
}
```

자동 재시도는 1회만. 두 번째도 실패 시 manual 지시 + phase failed.

## HTTP 5xx 분기

5xx 는 서버 일시 오류 가능. 자동 재시도 (지수 backoff):

```bash
retry_5xx() {
  local cmd="$1"
  local max=3
  local n=1
  while [ "$n" -le "$max" ]; do
    output=$(eval "$cmd")
    code=$(echo "$output" | jq -r '.success' 2>/dev/null)
    http=$(echo "$output" | jq -r '.httpCode // 200' 2>/dev/null)
    if [ "$code" = "true" ] || [ "$http" -lt 500 ]; then
      echo "$output"
      return 0
    fi
    echo "[retry] 5xx, attempt $n/$max, sleep $((n*5))s"
    sleep $((n*5))
    n=$((n+1))
  done
  return 1
}
```

3번 실패 시 ask-polestar10 호출.

## 비밀 정보 보호

에러 메시지 / 로그에 다음 정보 포함 X:
- Polestar10 password (~/.polestar10rc 의 POLESTAR10_PASS)
- SSH password (TESTBED_PASSWORD)
- git PAT (~/.git-credentials)

cookie jar 파일도 verbatim 출력 X. 디버깅 시 cookie 길이만 표시:
```bash
echo "cookie jar size: $(stat -c%s "$JAR") bytes"
```

## Polestar10 재로그인 자동 처리

세션 만료 (HTTP 401 또는 errorCode=AUTH_EXPIRED) 감지 시:

```bash
ensure_logged_in() {
  # 빠른 검사
  curl -sS --cookie-jar "$JAR" --cookie "$JAR" \
    "$POLESTAR10_BASE_URL/api/auth/me" \
    | jq -r '.success' | grep -q true \
    || {
      echo "[login] 세션 만료. 재로그인."
      bash "${CLAUDE_PLUGIN_ROOT}/knowledge/polestar10/api/recipes/login.md"   # bootstrap.md § Plugin install 경로 발견 패턴 따라 resolution
    }
}
```

각 sub-skill 진입 시 ensure_logged_in 호출 (idempotent).

## Polestar10 알려진 quirks 처리

(testbed-polestar10-register/SKILL.md 의 "Idempotency & Verification" 섹션 + infra/testbed/README.md "Caveats" 와 일관)

- **standby DB drift**: pod rolling update 후 옛 agent ID 가 polestar10 큐에 stale 상태로 남음. delete API 후 사용자 안내.
- **SMS agentId 갱신**: SMS install 마다 새 agentId. 이전 ID 등록 시 DOWN. testbed-polestar10-register 의 "옛 agentId 정리 → daemon 재시작 → 새 agentId 등록" 절차 사용.
- **스마트 cleanup**: 등록 시 이미 같은 이름 자원이 있으면 errorCode 보고 skip / overwrite 결정.

## Fallback: 사용자 직접 모드

interview.polestar10.registration_mode = "manual" 인 경우:
- testbed-build 가 register/tune 단계에서 사용자에게 "Polestar10 웹 UI 로 다음 작업 하세요:" 안내
- 사용자가 완료 후 "done" 입력하면 다음 phase 진행
- verify 단계는 동일 (백엔드 API 로 알람 history 조회는 가능)

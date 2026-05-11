# WPM `enabledAutoAddAgent` 토글 활성

WPM 서비스 등록 직후 호출하는 **강제 단계**. 본 toggle 이 OFF 면 신규 Pod 의
WPM agent 가 standby 에서 MANAGED 로 자동 승격되지 않아 TCP 31005 풀이
비활성으로 남고, collector 가 정상 처리 요청을 못 받아 `served=0` 으로 표시됨.

(round-12 dogfooding 진단 — `food-delivery-order` / `food-delivery-payment` 의
WPM 데이터 누락 원인 확정. HAR `agent-auto-plus.har` 으로 endpoint 확정.)

## Endpoint

```
POST /api/wpm/v1/setting/{serviceName}/update
Content-Type: application/json
Cookie: accessToken=...

Body:
{
  "serviceName": "<serviceName>",
  "enabledAutoAddAgent": true
}

Response:
{
  "success": true,
  "data": {"serviceName": "<serviceName>", "enabledAutoAddAgent": true},
  "errorCode": null
}
```

## 호출 시점

WPM agent register (`/api/apm/standby-agent/register`) 직후, **각 WPM 서비스마다 1회씩**.

```bash
for SVC in $(jq -r '.[].serviceName' <<< "$REG_PAYLOAD" | sort -u); do
  curl -fsS -X POST -H "Content-Type: application/json" -H "Cookie: accessToken=$P10_TOKEN" \
    -d "{\"serviceName\":\"$SVC\",\"enabledAutoAddAgent\":true}" \
    "$BASE/api/wpm/v1/setting/$SVC/update" | jq '{success,data,errorCode}'
done
```

## 멱등성

이미 `true` 인 상태에서 다시 호출 → 서버가 동일 응답으로 그대로 받음. 무해.

## 실패 시 fallback

API 가 5xx 또는 errorCode != null:
1. accessToken 만료 → bootstrap 재호출
2. serviceName 미존재 → register 시점에 사용한 serviceName 과 정확히 동일해야 함 (case-sensitive)
3. 그래도 실패 → **P10 UI 매뉴얼 활성화**:
   - 전체구성 > WPM > 서비스 목록 > 해당 서비스 클릭
   - 우측 드로어 > "에이전트 자동 추가" 토글 ON

## 본 toggle 없이 발생하는 증상

- UDP 31002 heartbeat 만 잠시 가다가 standby agent 가 INACTIVE/DOWN
- collector 측 `tcpConnected=false, lastTcpConnect=null`
- WPM 대시보드의 해당 서비스 `처리=-` 또는 `served=0`
- WPM-SCOUTER worker thread 가 1개 (정상은 SCOUTER1/2/3 + SCOUTER-TCP 의 4개)

## 진단

- collector 측: `docker logs polestar-app-wpm-1 | grep <serviceName>`
- agent 측: pod 의 `WPM-SCOUTER*` thread 수 (`jstack <pid> | grep WPM-SCOUTER`)
- P10 UI: WPM 서비스 상세 > 에이전트 탭 > managementStatus 가 `STANDBY` 면 toggle 미적용

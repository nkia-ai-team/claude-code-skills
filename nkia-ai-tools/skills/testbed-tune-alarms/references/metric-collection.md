# Polestar10 메트릭 수집 가이드

`testbed-tune-alarms` 가 임계치 결정 전 분포 추정을 위해 N분간 메트릭을 수집하는 방법.

> 정확한 endpoint 는 Polestar10 버전에 따라 변동. 본 문서는 표준 경로. 차이 발생 시 `<plugin_root>/knowledge/polestar10/api/recipes/` 또는 `endpoints.md` 우선.

---

## 도메인별 메트릭 카탈로그

### APM (Application Performance Monitoring)

```bash
curl -sS --cookie-jar "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/apm/metric/list?serviceGroup=$SG"
```

주요 measurement type — **알람 정의 시 measurementDefinitionId** (resource-type 카탈로그 호출 결과):

| measurementType (displayKey) | alias | unit | measurementDefinitionId (알람 정의 등록 시 사용) |
|---|---|---|---|
| `apm.response_time_avg` | 평균 응답시간 | μs (Polestar10 내부) | `apm.Agent_AvgResponseTime` |
| `apm.response_time_p95` | p95 응답시간 | μs | `apm.Agent_P95ResponseTime` |
| `apm.error_rate` | 에러율 | % | **`apm.Agent_ErrorRate`** (alias=ER) ← 알람 정의 권장 |
| `apm.tps` | Throughput | req/sec | `apm.Agent_TPS` |
| `apm.thread_pool_used` | Thread Pool 사용률 | % | `apm.Agent_ThreadPoolUsed` |

⚠️ **`apm.Agent_ApiErrorRate` 와 혼동 금지**: 두 metric 모두 카탈로그에 존재하나 alarm engine 이 평가하는 건 `apm.Agent_ErrorRate` (alias=ER, displayKey=apm.error_rate). plopvape-shop 의 fired alarm 156건 모두 이 metric 사용. `ApiErrorRate` (alias=ApiErrorRate, displayKey=apm.api_error_rate) 사용 시 alarm 정의는 등록되나 fire 0건.

metric 카탈로그 직접 조회:
```bash
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$JAR" \
  -H 'Content-Type: application/json' \
  -d '{"parameter":{"resourceType":"apm.Agent"}}' \
  "$POLESTAR10_BASE_URL/api/measurement/definitions/resource-type"
```

### DPM (Database Performance Monitoring)

```bash
curl -sS --cookie-jar "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/dpm/metric/list?resourceId=$RID"
```

| measurementType | alias | unit |
|---|---|---|
| `dpm.connection_count` | Active Connection 수 | count |
| `dpm.lock_count` | Lock 수 | count |
| `dpm.lock_wait_time` | Lock Wait Time | ms |
| `dpm.transaction_duration_max` | 최장 transaction 시간 | s |
| `dpm.slow_query_count` | Slow Query (1분당) | count |

### KCM (Kubernetes Container Monitoring)

```bash
curl -sS --cookie-jar "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/kcm/metric/list?clusterId=$CID"
```

| measurementType | alias | unit |
|---|---|---|
| `kcm.pod_cpu_usage_pct` | Pod CPU (limit 대비) | % |
| `kcm.pod_cpu_throttle_pct` | Pod CPU Throttling | % |
| `kcm.pod_memory_usage_pct` | Pod Memory | % |
| `kcm.pod_restart_count` | Pod Restart Count | count |

### SMS (System Monitoring System)

```bash
curl -sS --cookie-jar "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/sms/metric/list?agentId=$AID"
```

| measurementType | alias | unit |
|---|---|---|
| `sms.cpu_usage` | 호스트 CPU | % |
| `sms.memory_usage` | 호스트 Memory | % |
| `sms.disk_used` | Disk 사용량 | % |
| `sms.load_avg_1min` | 1분 Load Avg | (numeric) |
| `sms.process_cpu` | Process CPU | % |

---

## 시계열 수집 패턴

### N분 분량 수집

```bash
NOW_TS=$(date +%s)
FROM_TS=$((NOW_TS - COLLECTION_WINDOW_SEC))

curl -sS --cookie-jar "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/measurement/metric/timeseries" \
  -G \
  --data-urlencode "resourceId=$RID" \
  --data-urlencode "measurementType=apm.response_time_avg" \
  --data-urlencode "from=$FROM_TS" \
  --data-urlencode "to=$NOW_TS" \
  --data-urlencode "interval=60"
```

응답 형식 (예시):
```json
{
  "success": true,
  "data": {
    "timestamps": [1712345600, 1712345660, ...],
    "values": [820, 760, 910, ...]
  }
}
```

### 분포 통계 계산

수집한 values 배열로 클라이언트 측 계산:
```bash
# jq + datamash 조합 (Linux)
curl ... | jq -r '.data.values[]' | datamash mean 1 perc:50 1 perc:95 1 perc:99 1 max 1
```

또는 python 한 줄:
```bash
curl ... | jq -r '.data.values[]' | python3 -c "
import sys, statistics
v = [float(x) for x in sys.stdin if x.strip()]
v.sort()
print(f'p50={statistics.median(v):.1f} p95={v[int(len(v)*0.95)]:.1f} p99={v[int(len(v)*0.99)]:.1f} max={max(v):.1f}')
"
```

---

## 자원 식별자 매핑

### testbed (rca-scenario-runner) 와 Polestar10 자원 매핑

Polestar10 자원은 등록 시 ID 가 부여됨. testbed-polestar10-register 가 등록하면 결과에 ID 반환:
```bash
# register 결과 캐시 (testbed-build 가 만든 ~/.testbed-build/runs/<ts>/register.json)
cat ~/.testbed-build/runs/<ts>/register.json
# {
#   "apm_services": [
#     {"name": "order-service", "agentId": "...", "resourceId": "..."},
#     ...
#   ],
#   "dpm_resources": [
#     {"name": "postgres@rca-testbed", "resourceId": "..."}
#   ],
#   "kcm_cluster": {"clusterId": "..."},
#   "sms_host": {"agentId": "..."}
# }
```

이 매핑 없이는 어떤 자원의 메트릭을 fetch 할지 모름. testbed-build 흐름 안에서 호출되면 자동, 단독 호출 시 사용자 인터뷰 또는 Polestar10 API 자원 리스트 (`/api/sms/hosts/list` 등) 로 이름 검색.

---

## 수집 윈도우 가이드

| 목적 | 권고 윈도우 | 메모 |
|---|---|---|
| 평소 부하 baseline | 30~60분 | 짧으면 spike 영향 큼 |
| 시나리오 직후 분포 (verify 후 재튜닝) | 5~10분 | 시나리오 시간 + buffer |
| 장기 트렌드 (주간 업무 패턴) | 1~7일 | Polestar10 내부 retention 한계 확인 |

기본 default = 10분 (인터뷰 default).

---

## 메트릭 부재 / 0 응답 처리

수집 결과 비어있는 경우:
- 자원이 새로 등록돼서 데이터 누적 전 → "메트릭 데이터 X. M분 더 수집할까요?" 사용자 prompt
- 자원이 DOWN → Polestar10 자원 status 확인. DOWN 이면 임계치 결정 의미 X. 사용자에게 자원 상태 점검 안내.
- Polestar10 API 자체 5xx → ask-polestar10 호출 (스킬 본문 Polestar10 에러 처리 표준 패턴)

---

## 캐싱

같은 세션에서 여러 도메인 튜닝 시:
- 메트릭 카탈로그 (`/api/<domain>/metric/list`) 응답 → 세션 캐시 (변경 빈도 낮음)
- 자원 리스트 (`/api/sms/hosts/list` 등) → 세션 캐시 (등록 직후 한 번만)
- 시계열 자체 → 캐시 X (N분 윈도우는 호출마다 다름)

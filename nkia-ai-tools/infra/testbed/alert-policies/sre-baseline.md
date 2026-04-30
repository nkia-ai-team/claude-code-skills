# SRE Baseline — 알람 임계치 권고

`testbed-tune-alarms` 스킬이 LLM 추론할 때 prior knowledge 로 사용. Polestar10 알람 정책 4단계 (LEVEL1=정보 / LEVEL2=경고 / LEVEL3=중요 / LEVEL4=긴급) 기준.

본 baseline 은 **출발점**. 실제 임계치는 service domain 특성 + 측정 메트릭 분포 (p50/p95/p99) 보고 LLM 이 조정.

---

## APM (Application Performance Monitoring)

### 평균 응답시간 (ms 또는 s)
관측 단위: 서비스별 endpoint, 1분 측정 윈도우, 평균값.

| 도메인 카테고리 | LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 | 비고 |
|---|---|---|---|---|---|
| 결제·정산 (강한 SLA) | 500 ms | 1 s | 2 s | 5 s | p95 기준 권고 |
| 주문·예약 (사용자 대기 가능) | 1 s | 2 s | 5 s | 10 s | |
| 검색·조회 (read-heavy) | 300 ms | 800 ms | 2 s | 5 s | cache 깨졌을 때 |
| 배치·집계 (eventual) | 5 s | 30 s | 1 min | 5 min | 사용자 동기 호출 X |

### 에러율 (%)
관측 단위: 서비스별, 1분 윈도우, 5xx 비율.

| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 | 비고 |
|---|---|---|---|---|
| 1% | 5% | 10% | 25% | 평소 0.1~0.5% 인 도메인 |
| 5% | 10% | 25% | 50% | 평소 1~3% 인 도메인 (외부 의존도 큼) |

### Throughput (TPS) — 하한 알람
관측 단위: 서비스별, 1분 윈도우, request/sec.

급락 감지용 (서비스 죽음 또는 진입 차단 의심):
- 평소 평균의 **30% 이하** = LEVEL2
- 평소 평균의 **10% 이하** = LEVEL3
- **0** = LEVEL4

---

## DPM (Database Performance Monitoring)

### Connection 수
관측 단위: DB 인스턴스, 5분 윈도우, 동시 active connection.

DB max_connections 대비 비율:

| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 50% | 70% | 85% | 95% |

PostgreSQL default max_connections = 100. 즉 LEVEL2 ≈ 70 connection 권고 시작.

### Lock 수
관측 단위: DB 인스턴스, 1분 윈도우, lock count.

| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 | 비고 |
|---|---|---|---|---|
| 10 | 30 | 50 | 100 | 트랜잭션 도메인 (e-commerce, banking) |
| 5 | 15 | 30 | 60 | read-heavy 도메인 |

### Lock Wait Time (ms)
| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 100 ms | 500 ms | 2 s | 10 s |

### Transaction Duration (s)
관측 단위: 가장 긴 active transaction.

| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 1 s | 5 s | 30 s | 5 min |

### Slow Query Count (per minute)
| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 5 | 20 | 50 | 100 |

slow_query_threshold = `log_min_duration_statement` 또는 도메인 SLA 의 1.5배 권고.

---

## KCM (Kubernetes Container Monitoring)

### Pod CPU Usage (%)
관측 단위: pod, 1분 윈도우, request 또는 limit 대비.

limit 대비:
| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 60% | 75% | 85% | 95% |

> ⚠️ K3s metrics-server 미설치 시 측정 자체 안 됨 ([memory: K3s metrics-server 필수](../../../../.claude/projects/-home-sjbang-dev/memory/infra_k3s_metrics_server.md)). `--kubelet-insecure-tls` 플래그 필요.

### Pod CPU Throttling (%)
| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 5% | 25% | 50% | 80% |

### Pod Memory Usage (%)
limit 대비:
| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 70% | 80% | 90% | 95% |

> LEVEL4 = OOMKill 임박. K8s 의 OOM 은 hard, soft warning 단계 X.

### Pod Restart Count (per 10 min)
| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 1 | 3 | 5 | 10 |

LEVEL3 이상 = crashloop 의심.

### Container Status
- `ImagePullBackOff` / `ErrImagePull` → LEVEL3 (즉시)
- `CrashLoopBackOff` → LEVEL3 (즉시)
- `Pending > 5min` → LEVEL2

---

## SMS (System Monitoring System — Host)

### CPU Usage (%)
관측 단위: 호스트, 1분 윈도우, total %.

| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 60% | 75% | 85% | 95% |

### Memory Usage (%)
| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 70% | 80% | 90% | 95% |

### Disk Used (%)
관측 단위: 마운트 포인트별.

| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 70% | 80% | 90% | 95% |

> LEVEL4 = log rotation / cleanup 안 하면 곧 write fail.

### Load Average (1min)
관측 단위: 호스트, 1min load avg / CPU 코어 수 비율.

| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 1.0 | 2.0 | 4.0 | 8.0 |

(코어 수 normalize 후. 8 코어 호스트면 LEVEL2 = load 16)

### Process CPU (특정 process)
관측 단위: process 명, 1분 윈도우, CPU %.

도메인 특성에 따라 (예: postgres, java):
| LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|
| 30% | 50% | 70% | 90% |

---

## 도메인별 우선순위 가이드

LLM 이 정책 합성 시 도메인 메타로 우선순위 결정:

| 도메인 | 가장 중요한 알람 (LEVEL3+ 권고) |
|---|---|
| 결제 | APM 응답시간, APM 에러율, DPM lock wait, DPM transaction duration |
| 주문·재고 | APM 응답시간, DPM lock count, KCM pod restart |
| 인증 | APM 에러율, APM throughput 하한 (계정 잠김 등) |
| 검색·조회 | APM 응답시간, KCM pod CPU, 캐시 hit rate (해당 메트릭 별도) |
| 메시징 | KCM pod restart, queue 적체 (별도) |

---

## 측정 윈도우 가이드

| 메트릭 종류 | 권고 윈도우 | 발화 조건 (지속 시간) |
|---|---|---|
| 평균 응답시간 | 1 min | 3분 연속 |
| 에러율 | 1 min | 1분 (스파이크 즉시 알림) |
| Connection / Lock count | 5 min | 5분 연속 |
| Pod CPU throttling | 1 min | 3분 연속 |
| Disk used | 5 min | 1회 (점진적 증가, 즉시 알림) |
| Pod restart | 10 min | 1회 (1번이라도) |

---

## 출력 yaml 스키마 (testbed-tune-alarms → testbed-polestar10-register 입력)

```yaml
policies:
  - name: "RCA-Testbed PostgreSQL 임계치"
    description: "plopvape-shop postgres DPM 정책"
    domain: "postgresql"
    tagValue: "RCA-Testbed PostgreSQL 임계치"
    copy_from: "PostgreSQL 기본 임계치"   # 공통 정책: 기존 default 의 source
    role_id: "<24-hex>"                   # 권한 부여
    individual_alarms: []                  # 또는 개별 정의

individual_alarms:
  - resource_id: "<resource_id>"
    measurement_type: "lock_wait_time"
    measurement_alias: "Lock Wait Time"
    units: "ms"
    levels:
      level1: 100
      level2: 500
      level3: 2000
      level4: 10000
    max_alarms_per_min: 5
```

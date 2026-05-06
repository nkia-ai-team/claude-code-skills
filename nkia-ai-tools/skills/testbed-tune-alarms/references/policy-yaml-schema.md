# Policy YAML 스키마

`testbed-tune-alarms` 가 산출 → `testbed-polestar10-register` 가 등록.

---

## 전체 스키마

```yaml
# Polestar10 알람 정책 등록 입력
metadata:
  testbed_name: plopvape-shop
  generated_by: testbed-tune-alarms
  generated_at: 2026-04-30T15:32:11Z
  domain_filter: ["APM", "DPM"]   # 또는 "all"

common_policies:
  - name: "RCA-Testbed PostgreSQL 임계치"
    description: "plopvape-shop postgres DPM 공통 정책 (auto-tuned 2026-04-30)"
    domain: "postgresql"           # /api/alarm/resource/domain/options 응답 값
    tagValue: "RCA-Testbed PostgreSQL 임계치"
    copy_from: "PostgreSQL 기본 임계치"   # 기존 default 정책 이름
    role_id: ""                    # 비어있으면 register 가 default admin role 사용

  - name: "RCA-Testbed APM 임계치"
    description: "plopvape-shop APM 공통 정책 (auto-tuned)"
    domain: "apm"
    tagValue: "RCA-Testbed APM 임계치"
    copy_from: "APM 기본 임계치"
    role_id: ""

individual_alarms:
  - resource_name: "order-service"
    resource_id: "<24-hex>"        # register 가 미설정 시 이름으로 lookup
    measurement_type: "apm.response_time_avg"
    measurement_alias: "평균 응답시간"
    units: "ms"
    levels:
      level1: 1000
      level2: 2000
      level3: 3000
      level4: 5000
    max_alarms_per_min: 5
    enable: true
    comment: "p95=820ms p99=1.4s. 결제 도메인 SLA 보수적 권고."

  - resource_name: "postgres@rca-testbed"
    resource_id: "<24-hex>"
    measurement_type: "dpm.lock_count"
    measurement_alias: "Lock 수"
    units: "count"
    levels:
      level1: 5
      level2: 15
      level3: 30
      level4: 60
    max_alarms_per_min: 5
    enable: true
    comment: "평소 5~10. 트랜잭션 도메인 보수적."

# 변경 사항 요약 (사용자 승인 prompt 표시용)
diff_summary:
  total_policies: 2
  total_individual_alarms: 12
  changes:
    - resource: "order-service"
      measurement: "평균 응답시간"
      change: "level3 5000 → 3000 (보수적)"
    - resource: "postgres@rca-testbed"
      measurement: "Lock 수"
      change: "신규 정책 (현재 미설정)"
  spurious_warnings: []
```

---

## testbed-polestar10-register 의 변환 룰

register 스킬은 위 yaml 을 받아 [scenario_2_alarm_policy.md](../../testbed-polestar10-register/references/scenario_2_alarm_policy.md) flow 에 매핑:

### common_policies → Branch A (공통 정책)

각 common_policy 는 다음 API 시퀀스로 변환:

1. `GET /api/alarm/policys` → `copy_from` 이름의 default policy 의 `id` 찾기 (= `copyId`)
2. `POST /api/alarm/policys` 바디:
   ```json
   {
     "name": "<name>",
     "description": "<description>",
     "enable": true,
     "copyId": "<copyId>",
     "tagValue": "<tagValue>",
     "domain": "<domain>",
     "authorityInfos": [{"roleId": "<role_id 또는 default>", "permission": 15}]
   }
   ```
3. 등록 후 `tagValue` 가 자원에 자동 적용되도록 자원의 `alarmPolicy` 태그 갱신 (자원이 이미 등록된 상태여야 매칭됨)

### individual_alarms → Branch B (개별 알람)

각 individual_alarm 은:

1. `resource_id` 미설정이면 자원 이름으로 lookup (`/api/sms/hosts/list` 또는 도메인별 resource list)
2. `measurement_type` 으로 measurement catalog 의 `id` 찾기
3. `POST /api/alarm/individuals` 바디:
   ```json
   {
     "resourceId": "<resource_id>",
     "measurementType": "<measurement_type>",
     "measurementAlias": "<measurement_alias>",
     "activeAlarmPolicy": true,
     "maxAlarmsPerMin": 5,
     "condition": {
       "measurementType": "<measurement_type>",
       "conditionText": "<level1~4 텍스트화>",
       "units": "<units>"
     },
     "level1Value": 1000,
     "level2Value": 2000,
     "level3Value": 3000,
     "level4Value": 5000
   }
   ```

---

## 검증

yaml 작성 후 register 호출 전 자체 검증:

- [ ] 각 common_policy 의 `name` unique
- [ ] 각 common_policy 의 `tagValue` unique (충돌 시 Polestar10 에러)
- [ ] 각 individual_alarm 의 `(resource_name, measurement_type)` 조합 unique
- [ ] `levels` 가 monotonic 증가 (level1 < level2 < level3 < level4 또는 메트릭 종류에 맞게)
- [ ] `units` 가 measurement catalog 와 일치
- [ ] `comment` 가 사용자에게 권고 근거 명확

---

## 예시: plopvape-shop 4 도메인 권고 (요약)

```yaml
metadata:
  testbed_name: plopvape-shop
  generated_by: testbed-tune-alarms
  generated_at: 2026-04-30T15:32:11Z

common_policies:
  - name: "RCA-Testbed PostgreSQL 임계치"
    domain: "postgresql"
    copy_from: "PostgreSQL 기본 임계치"
    tagValue: "RCA-Testbed PostgreSQL 임계치"
    description: "plopvape-shop postgres DPM 정책"

individual_alarms:
  # APM
  - resource_name: "order-service"
    measurement_type: "apm.response_time_avg"
    levels: { level1: 1000, level2: 2000, level3: 3000, level4: 5000 }
    units: "ms"
  - resource_name: "payment-service"
    measurement_type: "apm.response_time_avg"
    levels: { level1: 2000, level2: 3500, level3: 5500, level4: 10000 }
    units: "ms"
    comment: "외부 PG 호출 도메인이라 보수적 baseline 보다 관대"
  # DPM
  - resource_name: "postgres@rca-testbed"
    measurement_type: "dpm.lock_count"
    levels: { level1: 5, level2: 15, level3: 30, level4: 60 }
    units: "count"
  - resource_name: "postgres@rca-testbed"
    measurement_type: "dpm.lock_wait_time"
    levels: { level1: 100, level2: 500, level3: 2000, level4: 10000 }
    units: "ms"
  # KCM
  - resource_name: "postgres-pod"
    measurement_type: "kcm.pod_cpu_throttle_pct"
    levels: { level1: 5, level2: 25, level3: 50, level4: 80 }
    units: "%"
  # SMS
  - resource_name: "203.0.113.109"
    measurement_type: "sms.cpu_usage"
    levels: { level1: 60, level2: 75, level3: 85, level4: 95 }
    units: "%"
```

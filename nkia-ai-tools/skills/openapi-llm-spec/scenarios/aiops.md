# aiops Examples 시나리오 카탈로그

## 도메인 정체성 (AIOps = ML 기반 이상감지/예측)

AIOps 도메인은 **ML 모델이 학습한 베이스라인**에서 벗어나는 패턴을 실시간 탐지(이상감지)하고, 과거 시계열 데이터로 미래 지표를 추론(예측)하는 시스템이다.
단순 임계치 초과 알람(정적 임계치)과 달리, 모델이 정상 범위를 동적으로 산출하므로 **"처음 보는 급증"도 이상으로 식별**한다.
핵심 서브도메인: 이상감지 정책/모델 관리 → 이상 차트/분석 → 근본 원인 분석(RCA) → 로그 이상감지 → 장기/단기 예측.

---

## 도메인 어휘 (15–20개)

| 용어 | 설명 |
|------|------|
| 이상감지 (Anomaly Detection) | ML 모델이 베이스라인 대비 비정상 패턴을 탐지하는 기능 |
| 베이스라인 (Baseline) | 정상 운영 기간 데이터로 학습된 기준 범위 |
| 이상 스코어 (Anomaly Score) | 각 지점이 베이스라인에서 벗어난 정도를 0~1로 표현한 값 |
| 이상 구간 (Anomaly Interval) | 이상 스코어가 임계값을 초과하는 연속 시간 구간 |
| 재학습 (Retrain) | 최신 데이터로 모델 파라미터를 다시 피팅하는 작업 |
| 지표 흐름 (Measurement Flow) | 이상 발생 전후 복수 지표의 상관 변화 흐름 |
| 수집 정책 (Collect Policy) | 모델 학습에 사용할 데이터 수집 주기·범위 설정 |
| 유사패턴 (Similar Pattern) | 과거 이상 구간과 파형이 유사한 히트맵 패턴 |
| 근본 원인 분석 (RCA, Root Cause Analysis) | 이상 발생 리소스와 연관 지표 인과관계를 순위화하는 분석 |
| RCA 랭크 테이블 (RCA Ranks Table) | 이상에 기여한 지표를 상관도 점수 기준으로 정렬한 표 |
| 예측 (Forecast) | 학습된 시계열 모델로 미래 지표값을 추정하는 기능 |
| 장기 예측 (Long-term Forecast) | 30일 이상 시계열 예측 (디스크 용량 소진 시점 등) |
| 단기 예측 (Short-term Forecast) | 수 시간~1일 이내 단기 추이 예측 |
| 예측 잔여 시간 (Remaining Time) | 용량/리소스가 임계치에 도달할 때까지 남은 시간 추정값 |
| 로그 이상감지 (Log Anomaly) | NLP 기반으로 로그 메시지 패턴을 학습해 희귀·이상 패턴을 탐지 |
| 희귀 패턴 (Rare Pattern) | 정상 로그에서 거의 등장하지 않는 드문 메시지 패턴 |
| FaucetType | 로그 이상감지 패턴 분류 — START/STOP/TIMING/FLOW/F_TIMING/RARE/NORMAL/ANOMALY |
| 정적 임계치 (Static Threshold) | ML 없이 고정 수치 조건(예: CPU > 80%)으로 알람을 발생시키는 규칙 |
| 자동 모드 (Auto Mode) | 이상감지 정책이 리소스 변화에 따라 모델을 자동으로 갱신하는 운영 모드 |
| 지표 정의 (Measurement Definition) | 수집 대상 지표의 식별자 및 메타데이터 (예: MD_CPU_UTIL) |

---

## 시나리오 카탈로그 (서브도메인별, 총 46개)

### 1. Anomaly Policy (이상감지 정책 관리)

> 이상감지 정책은 "어떤 리소스의 어떤 지표를 ML로 감시할지"를 정의하는 설정 단위.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `new_policy_cpu_mem` | "프로덕션 서버 CPU·메모리 이상감지 정책 신규 생성" | save (create) | 정책 이름 + 리소스 + 지표 포함 |
| `update_policy_name` | "정책 이름을 '운영팀-서버감시-v2'로 변경" | base-update (rename) | name 필드만 변경 |
| `enable_policy` | "야간 배포 후 이상감지 정책 즉시 활성화" | enabled=true | 배포 후 모니터링 재개 시나리오 |
| `disable_policy_maintenance` | "정기 점검 중 이상감지 정책 일시 비활성화" | enabled=false | 점검 윈도우 회피 목적 |
| `auto_mode_on` | "리소스 자동 편입을 위해 정책 자동 모드 활성화" | auto=true | 자동 모드로 신규 리소스 자동 추가 |
| `collect_policy_short_interval` | "5분 주기 수집 정책으로 변경 (고빈도 이상 탐지)" | collect-policy/update (interval) | 수집 주기 단축 |
| `add_resources_to_policy` | "DB 서버 3대를 이상감지 정책에 추가" | resources/save | resourceIds 다건 |
| `duplicate_check_policy_name` | "정책 이름 '신규-정책-2025' 중복 여부 확인" | check-duplicate | 이름 충돌 방지 |
| `list_policies_anomaly_score_filter` | "현재 활성화된 이상감지 정책 목록 조회" | list-filter (enabled=true) | 운영 중 정책 파악 |
| `delete_unused_policies` | "미사용 이상감지 정책 3건 일괄 삭제" | delete (multi) | 정리 작업 |

### 2. Anomaly Model (이상감지 모델 상태 및 재학습)

> ML 모델 단위. 리소스×지표 조합마다 독립 모델이 존재.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `retrain_cpu_spike_model` | "CPU 급증 이벤트 이후 이상감지 모델 재학습 트리거" | retrain (single) | 급증 후 베이스라인 재조정 |
| `retrain_all_after_upgrade` | "OS 업그레이드 후 전체 이상감지 모델 일괄 재학습" | retrain (all) | 베이스라인 드리프트 해소 |
| `check_model_exists` | "특정 리소스의 CPU 이상감지 모델 존재 여부 확인" | exist | 모델 미학습 리소스 점검 |
| `latest_anomaly_status_multi` | "5대 서버의 이상감지 최신 상태 일괄 조회" | anomaly-status-latest (ids) | 대시보드 현황 표시 |
| `metric_model_enable` | "메모리 누수 탐지를 위해 메모리 지표 모델 활성화" | anomaly-metric-model enabled=true | 특정 지표 모델만 ON |
| `metric_model_disable` | "노이즈 많은 네트워크 지표 모델 일시 비활성화" | anomaly-metric-model enabled=false | 오탐 억제 목적 |

### 3. Anomaly Chart & Analysis (이상 차트 및 분석)

> 이상 구간 시각화, 타임라인, 캘린더, 지표 흐름 분석.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `cpu_spike_anomaly_chart` | "CPU 사용률 50%→80% 급증 이상구간 차트 조회" | anomaly-charts (model-based, cpu) | 대표 ML 시나리오 |
| `memory_leak_chart_week` | "메모리 사용률 7일간 점진적 증가 이상감지 차트" | anomaly-charts (mem, week) | 메모리 누수 패턴 |
| `disk_io_anomaly_model_chart` | "디스크 I/O 이상감지 모델 기반 차트 (지표 정의 지정)" | anomaly-charts/model | measurementDefinitionId 지정 |
| `unlike_retrain_trigger` | "이상으로 잘못 탐지된 CPU 구간에 Unlike → 재학습 트리거" | reaction (unlike) | 피드백 기반 모델 개선 |
| `anomaly_timeline_today` | "오늘 이상감지 타임라인 조회 (이상 발생 시각 목록)" | timelines (today) | Time Navigator 사용 |
| `calendar_day_heatmap` | "지난 30일 일자별 이상 발생 히트맵 캘린더 조회" | calendar-day (month) | 월간 이상 패턴 파악 |
| `calendar_hourly_burst` | "오늘 시간별 이상 발생 빈도 캘린더 (시간대별 급증 확인)" | calendar-time (today) | 시간대 집중 이상 탐지 |
| `measurement_flow_cpu_mem` | "CPU 급증 전후 연관 지표 흐름 분석 (CPU·메모리·네트워크)" | measurement-flow | 다지표 상관관계 |
| `anomaly_occurrences_month` | "서버 리소스 최근 한 달 이상 발생 내역 전체 조회" | anomaly-occurrences (month) | 이력 조회 |
| `anomaly_count_week` | "이번 주 이상 감지 발생 건수 조회 (베이스라인 이탈 횟수)" | anomaly-count (week) | KPI 집계 |
| `resource_measurement_status_marker` | "이상 발생 마커 시점의 지표 상태 스냅샷 조회" | resource-measurement-status (marker) | 이상 발생 순간 상태 |

### 4. Anomaly Pattern & Heatmap (이상 패턴 유사도)

> 과거 이상 구간과 파형이 유사한 패턴을 히트맵으로 시각화하고 저장.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `heatmap_get_cpu` | "CPU 이상감지 히트맵 패턴 조회 (유사 구간 탐색)" | GET anomaly-heatmap | 유사 이상 패턴 시각화 |
| `save_similar_pattern_cpu_spike` | "CPU 급증 유사패턴 저장 (재발 감시 목적)" | POST anomaly-heatmap (save) | 패턴 라이브러리 구축 |
| `save_pattern_with_memo` | "디스크 I/O 폭증 패턴을 메모와 함께 유사패턴 저장" | POST anomaly-heatmap (save3) | 메모 포함 저장 |

### 5. RCA — 근본 원인 분석

> 이상 발생 시 어떤 지표가 원인인지 상관도 기반으로 순위화.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `rca_summary_cpu_spike` | "CPU 급증 이벤트에 대한 RCA 요약 조회" | rca/summary (today) | 운영자 최초 확인 |
| `rca_detail_marker` | "이상 마커 시점 RCA 상세 정보 조회 (원인 지표 목록)" | rca (marker) | 특정 시점 분석 |
| `rca_measurement_flow_week` | "이번 주 RCA 지표 흐름 — 선행 지표 변화 경로 추적" | rca-measurement-flow (week) | 선행 지표 인과 경로 |
| `rca_ranks_top10_week` | "이번 주 RCA 랭크 테이블 Top 10 원인 지표 조회" | ranks-table (week_top10) | 상위 원인 지표 |
| `rca_ranks_detail_category` | "특정 카테고리(프로세스) RCA 랭크 상세 목록" | ranks-table-detail (category) | 프로세스 그룹 분석 |
| `rca_process_java_detail` | "java 프로세스 단일 지표 RCA 상세 조회 (스레드·힙·CPU)" | single-process-measurements (java) | JVM 문제 원인 분석 |
| `rca_process_top5` | "이상 발생 시 상위 5개 프로세스 지표 조회" | process-measurements (top) | 프로세스 레벨 RCA |

### 6. Forecast Policy (예측 정책 관리)

> 예측 정책은 "어떤 리소스를 장기/단기 예측할지"를 정의.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `create_disk_forecast_policy` | "디스크 용량 소진 예측을 위한 장기 예측 정책 생성" | long-term (full) | 용량 계획 대표 시나리오 |
| `create_server_forecast_min` | "서버 CPU 예측 정책 최소 필드로 빠른 생성" | long-term (min) | 빠른 시작 |
| `enable_forecast_policy` | "비활성화된 디스크 예측 정책 활성화" | long-term/enabled=true | 예측 재개 |
| `disable_forecast_policy_test` | "테스트 환경 예측 정책 비활성화" | long-term/enabled=false | 운영 환경 분리 |
| `delete_obsolete_forecast_policies` | "폐기된 예측 정책 3건 일괄 삭제" | long-term/delete (multi) | 정리 작업 |
| `list_active_forecast_policies` | "현재 활성화된 예측 정책 목록 조회" | list-filter (enabled=true) | 운영 중 정책 파악 |
| `update_forecast_policy_period` | "장기 예측 정책 학습 기간을 3개월로 변경" | base-update (period) | 학습 데이터 범위 조정 |
| `check_forecast_policy_duplicate` | "예측 정책 이름 '서버-디스크-2025Q2' 중복 확인" | name/check-duplicate | 이름 충돌 방지 |

### 7. Long-term Forecast (장기 예측 결과)

> 학습 완료된 모델의 미래 예측값 조회.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `disk_capacity_7d_forecast_chart` | "디스크 용량 7일 장기 예측 차트 (소진 시점 시각화)" | long-term-forecasts/chart (cpu) | 용량 계획 핵심 시나리오 |
| `memory_forecast_3m_chart` | "메모리 사용률 3개월 장기 예측 차트" | long-term-forecasts/chart (mem) | 트렌드 예측 |
| `auto_period_forecast_chart` | "학습 기간 AUTO 설정으로 최적 예측 기간 자동 결정" | long-term-forecasts/chart (auto) | DataPeriod=AUTO |
| `forecast_summary_1m` | "리소스 장기 예측 요약 — 최근 1개월 데이터 기반" | long-term-forecasts/summary (1m) | 요약 카드 표시 |
| `forecast_rca_kpi_cards` | "RCA KPI 지표 장기 예측 카드 목록 조회" | long-term-forecasts/cards (rca) | MainIndicatorType=RCA_KPI |
| `forecast_metrics_running` | "학습 중인 장기 예측 지표 목록 조회 (ForecastState=RUNNING)" | forecast-metrics/list-filter (running) | 학습 상태 모니터링 |
| `forecast_metric_detail_disk` | "디스크 파일시스템 예측 지표 상세 — 잔여 용량·예측 기울기" | forecast-metrics/detail (with_period) | 용량 소진 예측 상세 |

### 8. Short-term Forecast (단기 예측)

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `cpu_short_term_today` | "오늘 CPU 사용률 단기 예측 차트 (향후 2시간 추이)" | forecasts/short-term/chart (cpu_today) | 피크 대비 시나리오 |
| `memory_short_term_1h` | "최근 1시간 메모리 단기 예측 — 누수 조기 경고" | forecasts/short-term/chart (mem_hour) | 메모리 누수 조기 탐지 |
| `live_forecast_realtime` | "실시간 단기 예측 차트 (현재 시각 기준 최신 추론)" | forecasts/short-term/chart (live) | 실시간 운영 모니터링 |
| `active_forecast_metrics_server` | "서버 타입 활성 예측 지표 조회 (사용자 분석 화면)" | forecasts/active-metrics (server) | UserAnalysis 화면용 |

### 9. Log Anomaly Model (로그 이상감지 모델 관리)

> NLP 기반으로 로그 패턴을 학습하고 이상·희귀 패턴을 탐지하는 모델.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `register_log_model_syslog` | "syslog 대상 로그 이상감지 모델 신규 등록" | log-anomaly-models/register (with_targets) | syslog 모니터링 |
| `register_log_model_applog` | "애플리케이션 에러 로그 이상감지 모델 전체 필드 등록" | log-anomaly-models/register (full) | 앱 에러 탐지 |
| `enable_log_model` | "비활성화된 로그 이상감지 모델 활성화 (서비스 재개 후)" | update-enable (on) | 모델 재가동 |
| `retrain_log_model_multi` | "로그 패턴 변화 후 복수 로그 모델 재학습" | log-anomaly-models/retrains (multi) | 배포 후 재학습 |
| `log_model_detail_with_history` | "로그 이상감지 모델 상세 — 학습 이력 포함 조회" | log-anomaly-models/{modelId} (with_history) | 모델 상태 점검 |
| `log_model_list_enabled` | "활성 로그 이상감지 모델 목록 조회" | log-anomaly-models/list-filter (enabled) | 운영 중 모델 파악 |
| `log_training_history_week` | "이번 주 로그 모델 학습 이력 조회 (학습 성공/실패)" | log-anomaly-models/{modelId}/history (week) | ForecastState 확인 |

### 10. Log Pattern & Anomaly Search (로그 패턴 및 이상로그 검색)

> 학습된 로그 패턴 조회 및 이상 로그 실시간 검색.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `search_error_anomaly_logs_today` | "오늘 ERROR 심각도 이상 로그 검색 (FaucetType=ANOMALY)" | anomaly-logs/search (today_error) | 장애 대응 첫 단계 |
| `search_rare_pattern_logs` | "희귀 패턴으로 분류된 로그 검색 (FaucetType=RARE)" | anomaly-logs/search (rare) | 신종 장애 패턴 탐지 |
| `anomaly_log_chart_week` | "이번 주 이상 로그 발생 추이 차트 (일 단위 집계)" | anomaly-logs/chart (week) | 주간 이상로그 트렌드 |
| `log_pattern_rare_list` | "모델의 희귀 패턴 목록 조회 (정상 로그에서 거의 미등장)" | patterns/list-filter (rare) | FaucetType=RARE 필터 |
| `log_pattern_anomaly_list` | "모델의 이상 패턴 목록 조회 (이상 판정 패턴들)" | patterns/list-filter (anomaly) | FaucetType=ANOMALY 필터 |
| `log_message_detail_context` | "이상 로그 메시지 주변 컨텍스트 포함 상세 조회" | log-messages/detail (context) | 원인 추적 |
| `schedule_test_log_model` | "로그 이상감지 모델 스케줄 테스트 실행 (탐지 윈도우 지정)" | anomaly-logs/schedule-test (with_window) | 탐지 정확도 검증 |

### 11. Static Threshold (정적 임계치)

> ML 없이 고정 수치 조건으로 알람 발생. AIOps 내 보조 기능.

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `static_threshold_cpu_80` | "CPU 사용률 80% 초과 정적 임계치 조건 생성" | static-threshold (cpu_80) | Direction=UPPER |
| `static_threshold_mem_90` | "메모리 사용률 90% 초과 정적 임계치 조건 생성" | static-threshold (mem_90) | 고임계 알람 |
| `static_threshold_enabled_check` | "알람 정의에 정적 임계치 기능 활성화 여부 확인" | static-threshold/enabled | 기능 가용성 확인 |
| `static_threshold_alarm_count` | "정적 임계치 알람 건수 기간 포함 조회" | static-threshold/alarm-count (with_time) | 알람 빈도 집계 |

### 12. Resource Level & Alarm (리소스 레벨 이상감지 현황)

| key | summary | intent | 비고 |
|-----|---------|--------|------|
| `resource_anomaly_status_all` | "전체 리소스 최신 이상감지 상태 일괄 조회 (대시보드 뷰)" | resources/anomaly-status-latest (all) | AlarmStatusType 분포 |
| `resource_anomaly_status_servers` | "서버 타입 리소스만 이상감지 최신 상태 조회" | resources/anomaly-status-latest (type) | 타입 필터 |
| `resource_anomaly_metrics` | "특정 리소스들의 이상감지 지표 목록 조회" | resources/anomaly-metrics (ids) | 지표 현황 파악 |
| `anomaly_alarm_summary_week` | "리소스 최근 1주 이상감지 알람 요약 조회" | anomaly-alarms/summary (week) | 주간 알람 리포트 |

---

## 사용법

### 목적

이 카탈로그는 `aiops.openapi.json` 각 endpoint의 `examples` 필드를 **ML/AIOps 도메인 어휘로 강화**할 때 참조한다.
현재 spec에는 "1페이지", "활성화", "비활성화" 같은 generic 레이블이 많으며 (audit 결함), 이 카탈로그의 시나리오로 교체해야 한다.

### 적용 원칙

1. **example key** — 카탈로그의 `key` 컬럼 값을 그대로 사용 (generic `default`/`enabled`/`on`/`off` 교체).
2. **summary** — 카탈로그 `summary` 컬럼의 한국어 자연어 그대로 사용. ML 어휘(급증·베이스라인·재학습·희귀패턴 등)를 포함해야 함.
3. **value** — 카탈로그 `비고` 컬럼에서 실제 필드값 힌트 참조. `OpaqueRequest` 기반이므로 schema 구조는 자유롭게 채움.
4. **우선순위** — 서브도메인별로 가장 대표적인 ML 시나리오(CPU 급증, 디스크 용량 예측, 로그 이상 탐지)를 먼저 작성.
5. **generic 금지** — "1페이지", "활성화", "비활성화" 단독 summary는 사용하지 않음. 항상 컨텍스트 포함 (예: "야간 배포 후 이상감지 정책 즉시 활성화").

### 매핑 예시

```
# 현재 spec (audit 결함)
examples:
  default:
    summary: "1페이지"
  enabled:
    summary: "활성화 정책만"

# 카탈로그 적용 후
examples:
  list_active_policies:
    summary: "현재 활성화된 이상감지 정책 목록 조회"
  cpu_spike_policy:
    summary: "프로덕션 서버 CPU·메모리 이상감지 정책 신규 생성"
```

### 카탈로그 커버리지

| 서브도메인 | 시나리오 수 | 대표 ML 시나리오 |
|-----------|------------|----------------|
| Anomaly Policy | 10 | CPU·메모리 정책 생성, 자동 모드, 수집 정책 주기 |
| Anomaly Model | 6 | CPU 급증 후 재학습, 전체 재학습, 지표 모델 ON/OFF |
| Anomaly Chart & Analysis | 11 | CPU 급증 차트, 메모리 누수, 지표 흐름, 히트맵 캘린더 |
| Anomaly Pattern | 3 | 유사패턴 저장, 히트맵 조회 |
| RCA | 7 | CPU 급증 RCA, java 프로세스 원인 분석, 랭크 Top10 |
| Forecast Policy | 8 | 디스크 용량 예측 정책 생성, 학습 기간 변경 |
| Long-term Forecast | 7 | 디스크 7일 예측, 메모리 3개월 예측, DataPeriod=AUTO |
| Short-term Forecast | 4 | CPU 2시간 추이, 메모리 누수 조기 경고, 실시간 |
| Log Anomaly Model | 7 | syslog 모델 등록, 배포 후 재학습, 학습 이력 |
| Log Pattern & Search | 7 | ERROR 이상로그, 희귀패턴, 주간 추이 차트 |
| Static Threshold | 4 | CPU 80% 임계치, 메모리 90%, 알람 건수 |
| Resource Level & Alarm | 4 | 전체 현황 대시보드, 서버 타입 필터, 주간 알람 요약 |
| **합계** | **78** | |

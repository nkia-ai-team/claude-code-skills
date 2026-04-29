# apm Examples 시나리오 카탈로그

## 도메인 정체성

APM(Application Performance Monitoring) 도메인. Java 애플리케이션의 트레이스(요청 흐름), 응답시간, 에러율, 엔트리포인트, DB SQL 호출을 실시간·기간별로 분석. 서비스/에이전트 단위 관리 및 JVM 메트릭 차트 포함.

---

## 도메인 어휘 (18개)

| 용어 | 의미 |
|------|------|
| 트레이스(Trace) | 단일 HTTP 요청의 전체 처리 흐름 (입구~출구) |
| 스팬(Span) | 트레이스 내 개별 처리 단위 (ENTRY/DB/EXIT) |
| 에이전트(Agent) | 애플리케이션 서버에 배포된 APM 수집기 (예: tomcat10) |
| 서비스(Service) | 에이전트 묶음 단위 (예: NkiaMarket) |
| 엔트리포인트(EntryPoint) | 트레이스 진입점 URL (예: `/api/order`) |
| 응답시간(ResponseTime) | 트레이스 처리에 걸린 시간 (ms 단위) |
| 에러율(ErrorRate) | 전체 요청 대비 에러 발생 비율 (%) |
| 스캐터(Scatter) | 응답시간 분포도 — X축 시간, Y축 응답시간, 점 = 트레이스 1건 |
| 백트레이스(BackTrace) | 특정 트레이스의 호출 스택 역추적 |
| TopN | 응답시간/처리건수/에러수 기준 상위 N개 엔트리포인트·SQL 순위 |
| DB 트레이스 | SQL 쿼리가 포함된 트레이스 (DB 호출 구간 포함) |
| From-To | 특정 출발 서비스 → 특정 도착 서비스 구간 트레이스 |
| 처리건수(ServicedCount) | 단위 시간 내 처리한 요청 수 |
| 백분위수(Percentile) | p50/p95/p99 응답시간 분포 지표 |
| JVM 메트릭 | 힙 메모리, GC 횟수, 스레드 수 등 JVM 내부 지표 |
| 서비스맵(ServiceMap) | 서비스 간 호출 의존 관계 시각화 |
| 등록 대기(Standby) | APM 에이전트가 발견됐으나 아직 서비스에 배정되지 않은 상태 |
| 카테고리(Category) | JVM 메트릭 분류 (memory / cpu / thread / gc 등) |

---

## 함정 회피 노트

### scatter vs chart 혼동 방지
- `trace_scatter`, `widget_traceScatter`, `topn_scatter`, `appAnalysis_getTopNScatter` — **scatter** endpoint 는 응답분포도(점 데이터). summary 는 "스캐터" 또는 "응답분포" 로만 표현. "차트" 금지.
- `summary_avgRespTime`, `summary_errorRate`, `topn_summaryChart`, `appAnalysis_getTopNSummaryChart` — **라인차트** endpoint. summary 는 "라인차트" 또는 "추이".
- `appAnalysis_getTopNScatter` summary 는 현재 "TopN 응답분포 차트" — "차트" 라는 단어가 섞여있어 혼동 유발. examples summary 에서는 반드시 "응답분포" 또는 "스캐터" 만 사용.

### ex1/ex2/ex3 메타라벨 금지
- 80개 endpoint 에 잔존하는 `ex1`/`ex2`/`ex3` 형태의 summary 는 **메타라벨**로 CI HARD #4 위반. 아래 카탈로그의 intent 컬럼을 기준으로 구체적 자연어로 교체.

### "다음 페이지" 중복 금지
- `trace_filterTraces`, `trace_filterFromToTraces`, `serviceGroup_listFilter`, `agent_filter`, `standby_filterStep1` 등 페이지네이션 endpoint 에서 "다음 페이지" summary 5회 중복 발견. endpoint 별로 "다음 페이지" 앞에 **도메인 컨텍스트** 명시 필수.
  - 예: "트레이스 목록 다음 50건" / "에이전트 목록 페이지 2" / "From-To 트레이스 2페이지"

---

## 시나리오 카탈로그

### Trace 분석 (트레이스 목록/상세/스팬)

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| trace_slow_top50 | "응답시간 100ms 초과 트레이스 50건 보여줘" | trace_filterTraces | list+filter(resTime) | minResTime 파라미터 |
| trace_error_1h | "최근 1시간 에러 발생 트레이스 목록" | trace_filterTraces | list+filter(error) | hasError=true |
| trace_agent_specific | "tomcat10 에이전트 트레이스 최근 5분" | trace_filterTraces | list+filter(agent) | agentId 지정 |
| trace_next_page | "트레이스 목록 다음 50건 (페이지 2)" | trace_filterTraces | list+paginate | nextPage 파라미터 |
| trace_single_detail | "특정 트레이스 ID의 전체 처리 정보 조회" | trace_getTraceInfo | detail | traceId 필수 |
| trace_span_all | "트레이스 내 모든 스팬 목록 보여줘" | trace_getTraceSpanList | list(span) | spanType 전체 |
| trace_span_db | "트레이스 중 DB 호출 스팬만 보기" | trace_getTraceSpan | detail(span) | spanType=DB |
| trace_span_entry | "ENTRY 스팬 요청/응답 헤더 포함 상세" | trace_getTraceSpan | detail(span) | spanType=ENTRY |
| trace_summary_p99 | "최근 1시간 트레이스 응답시간 p50/p95/p99" | trace_summary | aggregate(percentile) | |
| trace_entry_autocomplete | "/order 로 시작하는 엔트리포인트 이름 목록" | trace_entryPointNames | list(autocomplete) | prefix 검색 |
| trace_excel_error | "에러 발생 트레이스 엑셀 다운로드" | trace_excelTraces | export(excel) | binary response |

### Scatter (응답분포도)

> 주의: scatter endpoint 는 점 데이터 반환. "차트" 표현 금지, "응답분포" 또는 "스캐터" 로만.

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| scatter_trace_5m | "최근 5분 트레이스 응답분포 스캐터 데이터" | trace_scatter | chart(scatter) | 5분 기간 |
| scatter_trace_slow | "응답시간 100ms~5000ms 구간 스캐터 포인트" | trace_scatter | chart(scatter)+filter | minResTime/maxResTime |
| scatter_trace_1d | "하루치 트레이스 응답분포 스캐터" | trace_scatter | chart(scatter) | 1일 기간 |
| scatter_widget | "대시보드 위젯 트레이스 응답분포 스캐터" | widget_traceScatter | chart(scatter) | 위젯용 |
| scatter_widget_error | "에러 발생 트레이스만 위젯 스캐터" | widget_traceScatter | chart(scatter)+filter | hasError=true |
| scatter_topn_entry | "엔트리포인트별 TopN 응답분포 스캐터" | topn_scatter | chart(scatter) | topNType=entrypoint |
| scatter_topn_db | "DB 호출 TopN 응답분포 스캐터" | topn_scatter | chart(scatter) | topNType=database |
| scatter_appanalysis_entry | "AppAnalysis 엔트리포인트 응답분포 스캐터" | appAnalysis_getTopNScatter | chart(scatter) | topNType=entrypoint |

### TopN (서비스·메서드 순위)

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| topn_entry_response | "엔트리포인트 응답시간 순 TopN 목록" | appAnalysis_getTopNList | list+sort(resTime) | sortBy=responseTime |
| topn_entry_count | "엔트리포인트 처리건수 순 TopN" | appAnalysis_getTopNList | list+sort(count) | sortBy=servicedCount |
| topn_db_sql | "DB SQL 응답시간 순 TopN" | appAnalysis_getTopNList | list+sort(db) | topNType=database |
| topn_error_count | "에러 발생 건수 순 TopN 엔트리포인트" | appAnalysis_getTopNList | list+sort(error) | topNType=error |
| topn_entry_stat | "엔트리포인트 TopN 통계 정보 (호출수/응답시간)" | topn_entryPointSummary | aggregate(stat) | |
| topn_db_entry | "DB 호출 많은 엔트리포인트 TopN" | topn_databaseEntryPointTopn | list(db-entry) | |
| topn_error_entry | "에러 발생 빈도순 엔트리포인트 목록" | topn_errorEntrypointTopn | list(error-entry) | NPE / DataAccessException |
| topn_backtrace_entry | "엔트리포인트 TopN 백트레이스 역추적" | appAnalysis_getBackTrace | detail(backtrace) | topNType=entrypoint |
| topn_backtrace_db | "DB SQL TopN 백트레이스 1시간" | appAnalysis_getBackTrace | detail(backtrace) | topNType=database |
| topn_db_trace_list | "DB TopN 관련 트레이스 목록 (페이지네이션)" | topn_databaseTraces | list+paginate | |
| topn_error_latest | "TopN 에서 특정 에러 트레이스 상세 조회" | topn_errorLatest | detail(error) | traceId 필수 |

### Chart (시계열 라인차트)

> 주의: 이 섹션은 라인차트 시계열 데이터. scatter 와 혼동 금지.

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| chart_resp_5m | "NkiaMarket 서비스 최근 5분 평균 응답시간 라인차트" | summary_avgRespTime | chart(line) | serviceId 필수 |
| chart_resp_1h | "특정 서비스 1시간 응답시간 추이" | summary_avgRespTime | chart(line) | |
| chart_error_rate_5m | "서비스 에러율 5분 단위 라인차트" | summary_errorRate | chart(line) | |
| chart_serviced_1h | "서비스 처리건수 1시간 추이" | summary_servicedCnt | chart(line) | |
| chart_percentile_5m | "서비스 p50/p95/p99 응답시간 5분 라인차트" | summary_percentiles | chart(line+percentile) | |
| chart_histogram | "서비스 응답시간 히스토그램 (구간별 요청 분포)" | summary_respHistogram | chart(histogram) | |
| chart_topn_entry | "엔트리포인트별 응답시간 추이 TopN 라인차트" | appAnalysis_getTopNSummaryChart | chart(line+topN) | topNType=entrypoint |
| chart_topn_db | "DB SQL 응답시간 추이 라인차트" | appAnalysis_getTopNSummaryChart | chart(line+topN) | topNType=database |
| chart_error_latest | "최근 5분 에러 발생 추이 라인차트" | appAnalysis_getErrorLatestChart | chart(line+error) | |
| chart_jvm_heap | "tomcat10 힙 메모리 사용량 추이 차트" | jvm_singleChart | chart(jvm) | metricKey=heapUsed |
| chart_jvm_cpu | "tomcat10 CPU 사용률 추이 차트" | jvm_singleChart | chart(jvm) | metricKey=cpu |
| chart_jvm_multi_heap | "여러 에이전트 힙 메모리 비교 차트" | jvm_multiChart | chart(jvm+multi) | agentIds 배열 |
| chart_jvm_gc | "단일 JVM GC 횟수 상세 메트릭 차트" | jvm_singleMetricChart | chart(jvm+metric) | |
| chart_jvm_multi_gc | "여러 에이전트 GC 횟수 비교 차트 데이터" | jvm_multiMetricChart | chart(jvm+multi+metric) | |
| chart_func_detail | "heapMemoryUsed 메트릭 함수별 분포 상세" | metric_functionDetail | chart(func) | function=avg/max/min |
| chart_topn_metric | "응답시간 TopN 엔드포인트 메트릭 차트" | metric_chartTopn | chart(topN+metric) | |

### DB 트레이스

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| db_trace_list_filter | "최근 1시간 100ms 초과 DB 트레이스 목록" | trace_filterDatabaseTraces | list+filter(db) | minResTime 파라미터 |
| db_trace_agent | "특정 에이전트의 DB 트레이스 필터 조회" | trace_filterDatabaseTraces | list+filter(agent+db) | agentId 지정 |
| db_trace_detail | "특정 트레이스의 SQL 실행 내역 상세" | appAnalysis_getDatabaseTraceInfo | detail(db) | traceId 필수 |
| db_trace_topn | "DB 엔트리포인트 TopN 상위 5개 조회" | appAnalysis_getDatabaseEntryPointTopn | list(topN+db) | topN=5 |
| db_trace_excel | "최근 1일 DB 트레이스 엑셀 다운로드" | trace_excelDatabaseTraces | export(excel) | binary response |
| db_trace_error | "에러 발생 DB 트레이스 엑셀" | trace_excelDatabaseTraces | export(excel+error) | hasError=true |
| db_sql_top5 | "서비스 SQL 실행 횟수 기준 Top5" | summary_databaseTopn | list(topN+sql) | sortBy=callCount |

### Error 트레이스

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| error_trace_npe | "NullPointerException 발생 트레이스 목록" | trace_filterErrorTraces | list+filter(errClass) | exceptionClass=NPE |
| error_trace_1h | "최근 1시간 에러 트레이스 전체 목록" | trace_filterErrorTraces | list+filter(time) | |
| error_trace_dao | "DataAccessException 에러 트레이스 1일" | trace_filterErrorTraces | list+filter(errClass) | exceptionClass=DataAccessException |
| error_trace_detail | "에러 트레이스 상세 — NullPointerException 호출 스택" | appAnalysis_getErrorLatest | detail(error) | traceId 필수 |
| error_latest_5 | "서비스 최근 에러 5건 목록" | summary_errorLatest | list(error+latest) | |
| error_trace_excel | "에러 트레이스 1일치 엑셀 다운로드" | trace_excelErrorTraces | export(excel+error) | binary response |

### From-To 라인 트레이스

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| fromto_trace_1p | "특정 서비스 구간 From-To 트레이스 1페이지" | trace_filterFromToTraces | list+filter(fromTo) | fromService/toService 필수 |
| fromto_trace_next | "From-To 트레이스 목록 2페이지 50건" | trace_filterFromToTraces | list+paginate | nextPage 파라미터 |
| fromto_trace_excel | "From-To 구간 에러 발생 트레이스 엑셀" | trace_excelFromToTraces | export(excel+fromTo) | binary response |

### Service / Application 요약

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| svc_related_agents | "NkiaMarket 서비스 소속 에이전트 목록" | summary_relatedAgent | list(agent) | serviceId 필수 |
| svc_related_db | "NkiaMarket 서비스가 접속하는 DB 목록" | summary_relatedDatabase | list(db) | serviceId 필수 |
| svc_resource_count | "에이전트/DB 연관 리소스 수" | summary_relatedResourceCount | aggregate(count) | |
| svc_entry_top5 | "서비스 엔트리포인트 호출 횟수 기준 Top5" | summary_entrypointTopn | list(topN+entry) | sortBy=callCount |
| svc_basic_info | "NkiaMarket 서비스 기본 정보 조회" | configuration_serviceBasicInfo | detail(config) | serviceId 필수 |
| svc_list_filter | "전체 APM 서비스 목록 조회 (페이지네이션)" | serviceGroup_listFilter | list+paginate | |
| svc_list_name | "서비스명 'Market' 으로 서비스 목록 필터" | serviceGroup_listFilter | list+filter(name) | nameFilter 파라미터 |
| svc_find_by_name | "NkiaMarket 서비스명으로 서비스 그룹 조회" | serviceGroup_findByName | detail(byName) | exact match |
| svc_search_one | "serviceId 로 서비스 단건 조회" | serviceGroup_searchOne | detail(query) | serviceId 조건 |
| svc_permission | "현재 사용자의 서비스 접근 권한 확인" | serviceGroup_checkPermission | check(permission) | |
| svc_resource_type_count | "APM 서비스·에이전트 타입별 카운트" | serviceGroup_resourceTypeCount | aggregate(typeCount) | x-llm-examples 보유 |
| svc_excel | "서비스 목록 엑셀 다운로드" | serviceGroup_excelDownload | export(excel) | binary response |

### ServiceMap (서비스 의존 관계)

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| svcmap_by_trace | "특정 트레이스 기반 서비스 간 호출 관계 서비스맵" | servicemap_getByTraceID | graph(trace) | traceId 필수 |
| svcmap_by_service_5m | "NkiaMarket 서비스 최근 5분 서비스맵" | servicemap_getByService | graph(service) | serviceId + 5분 |
| svcmap_by_service_1d | "서비스 1일 의존 관계 서비스맵" | servicemap_getByService | graph(service) | 1일 기간 |

### Agent (에이전트 관리)

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| agent_conf_all | "전체 에이전트 conf 목록 조회" | agent_confList | list(conf) | |
| agent_conf_service | "특정 서비스 소속 에이전트 conf 목록" | agent_confList | list(conf+filter) | serviceId 지정 |
| agent_conf_count | "전체 에이전트 수 조회" | agent_confListCount | count | |
| agent_filter_page | "에이전트 목록 1페이지 조회 (등록 상태별 필터)" | agent_filter | list+filter+paginate | |
| agent_filter_error | "에러 상태 에이전트만 필터 조회" | agent_filter | list+filter(status) | status=ERROR |
| agent_filter_next | "에이전트 목록 페이지 2" | agent_filter | list+paginate | nextPage 파라미터 |
| agent_name_only | "에이전트 ID·이름만 경량 조회" | agent_listWithoutMetric | list(lightweight) | 자동완성용 |
| agent_grid_cols | "에이전트 목록 그리드 컬럼 정의 조회" | agent_gridColumns | config(grid) | gridType=agent |
| agent_excel | "전체 에이전트 목록 엑셀 다운로드" | agent_excelDownload | export(excel) | binary response |

### Standby (등록 대기 에이전트)

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| standby_new_count | "새로 발견된 등록 대기 에이전트 수" | standby_newCount | count | x-llm-examples 보유 |
| standby_ready_count | "READY 상태 에이전트 카운트" | standby_count | count(byStatus) | status=READY |
| standby_step1_list | "신규 에이전트 탐지 목록 STEP1 1페이지" | standby_filterStep1 | list+paginate(step1) | |
| standby_step1_next | "등록 대기 에이전트 목록 STEP1 2페이지" | standby_filterStep1 | list+paginate(step1) | nextPage 파라미터 |
| standby_step2_list | "서비스 배정 대기 에이전트 STEP2 목록" | standby_filterStep2 | list(step2) | agentIds 선택 후 |
| standby_register | "에이전트 서비스에 일괄 등록 처리" | standby_register | action(register) | agentIds 배열 |
| standby_delete_error | "에러 상태 등록 대기 에이전트 일괄 삭제" | standby_delete | action(delete) | status=ERROR |
| standby_step1_excel | "등록 대기 에이전트 STEP1 엑셀 다운로드" | standby_filterStep1Excel | export(excel) | binary response |

### Service Setting (서비스 설정)

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| setting_read | "NkiaMarket 서비스 현재 설정값 조회" | serviceSetting_read | detail(setting) | serviceId 필수 |
| setting_update_managed | "서비스 관리 상태를 MANAGED 로 변경" | serviceSetting_update | action(update) | manageStatus=MANAGED |
| setting_update_standby | "서비스 상태를 STANDBY 로 + 알람 정책 적용" | serviceSetting_update | action(update) | manageStatus=STANDBY |
| setting_monitor_agents | "서비스 상세 분석 에이전트 목록 조회" | serviceSetting_monitorAgents | list(monitorAgent) | serviceId 필수 |
| setting_update_policy | "특정 에이전트 상세 분석 정책 변경" | serviceSetting_updateMonitorAgents | action(update+policy) | agentId + policyType |

### Widget 대시보드

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| widget_topn_service | "대시보드 서비스 기준 APM TopN 카드 Top5" | widget_topnSummary | list(widget+topN) | topN=5 |
| widget_trace_list | "대시보드 최근 트레이스 목록 1페이지" | widget_traceList | list(widget) | |
| widget_trace_error | "대시보드 에러 트레이스만 위젯 목록" | widget_traceList | list(widget+filter) | hasError=true |
| widget_trace_slow | "응답시간 100ms~5000ms 위젯 트레이스" | widget_traceList | list(widget+filter) | resTime 범위 |
| widget_trace_excel | "위젯 트레이스 목록 엑셀 다운로드" | widget_traceListExcel | export(excel+widget) | binary response |

### JVM 메트릭

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| jvm_category_list | "NkiaMarket 서비스 JVM 메트릭 카테고리 목록" | jvm_singleCategory | list(jvm+category) | serviceId 필수 |
| jvm_category_metrics | "memory 카테고리 내 JVM 메트릭 항목 목록" | jvm_singleCategoryMetrics | list(jvm+metric) | category=memory |

### Collection / Setting

| key | summary | operationId | intent | 비고 |
|-----|---------|-------------|--------|------|
| collection_drop_30d | "30일 이전 MongoDB Collection 삭제" | collection_dropCollection | action(drop) | retentionDays=30 |
| cluster_setting | "APM 클러스터 전체 설정 정보 조회" | settings_getSettingInfo | detail(cluster) | resourceId 필수 |

---

## 사용법

이 카탈로그는 `apm.openapi.json` 각 endpoint 의 `examples` 작성 시 sampling base 로 사용.

**적용 절차**:
1. endpoint 의 operationId 로 해당 행을 찾는다.
2. `summary` 컬럼의 자연어 표현을 실제 examples 에 그대로 쓰거나 변형 적용.
3. `intent` 컬럼으로 example 의 다양성(list/detail/filter/sort/export/action) 을 확인 — 동일 intent 3건 연속은 금지.
4. `비고` 컬럼의 파라미터 힌트를 `value` 에 반영.

**scatter/chart 구분 체크리스트**:
- [ ] scatter endpoint (trace_scatter / widget_traceScatter / topn_scatter / appAnalysis_getTopNScatter) 의 summary 에 "차트" 단어 없는지 확인
- [ ] 라인차트 endpoint 의 summary 에 "스캐터" 단어 없는지 확인

**중복 방지 체크리스트**:
- [ ] 동일 operationId 내 3개 example 의 summary 가 모두 다른 의도를 표현하는지 확인
- [ ] "다음 페이지" 단독 summary 없음 — 반드시 도메인 컨텍스트 선행 (예: "트레이스 목록 다음 50건")
- [ ] ex1/ex2/ex3/case_N 형태의 메타라벨 없음

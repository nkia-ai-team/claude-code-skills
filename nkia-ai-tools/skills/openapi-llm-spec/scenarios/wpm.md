# WPM 시나리오 카탈로그

## 도메인 정체성
**Web Performance Monitoring (WPM)** — JVM 기반 웹 애플리케이션 서버(WAS)의 실시간 성능 관제. 액티브 서비스/스레드 모니터링, 에이전트 관리(등록·삭제·옵션), 힙덤프·서비스덤프·스레드덤프 진단, 엔트리포인트/SQL/HTTP/에러 통계, 트레이스 분석, 방문자수 차트, 서비스맵 시각화를 통합 제공한다.

---

## 도메인 어휘

| 용어 | 설명 |
|------|------|
| 에이전트(Agent) | WAS 프로세스에 주입된 WPM 수집 모듈; agentId / confId로 식별 |
| 액티브 서비스(Active Service) | 현재 처리 중인 HTTP 요청 단위; 응답시간·상태 실시간 노출 |
| 엔트리포인트(Entrypoint) | WAS가 수신한 HTTP 요청 URL 단위 통계 집계 기준 |
| 서비스 ID(serviceId/resourceId) | WPM 서비스 식별자; 태그 필터(`confType=wpm`)로 파생 |
| 트레이스(Trace) | 단일 HTTP 트랜잭션 전체 처리 흐름; traceId로 식별 |
| 스팬(Span) | 트레이스 내 개별 작업 단위 (SQL, HTTP 외부 호출 등) |
| 힙덤프(Heap Dump) | JVM 힙 메모리 스냅샷 파일; 메모리 누수 분석용 |
| 서비스덤프(Service Dump) | 특정 시점 서비스 상태 전체 스냅샷; 장애 원인 파악용 |
| 스레드 덤프(Thread Dump) | JVM 전체 스레드 스택 트레이스 일괄 수집 |
| 스레드(Thread) | WAS 내 실행 중인 Java 스레드; 응답 지연·행(hang) 감지 |
| TOP N | tagFilters + top(10/30/50) 기준 상위 서비스 정렬 조회 |
| TPS | Transactions Per Second — 초당 처리 건수 |
| 응답시간(Response Time) | HTTP 요청 처리에 소요된 시간(ms) |
| 에러율(Error Rate) | 전체 요청 대비 예외/에러 발생 비율 |
| 서비스맵(Service Map) | 에이전트 간 호출 관계 토폴로지 시각화 |
| 트리맵(Treemap) | 엔트리포인트 성능 지표를 면적 비례로 시각화 |
| 보관주기 정책(Retention Policy) | MongoDB 컬렉션별 데이터 보관 기간 설정 |
| WAS | Web Application Server (Tomcat, JBoss 등) |
| confId | 에이전트 구성 식별자 (`-1899035625_apm.Agent` 형식) |
| tagFilter | 에이전트 필터 표현식 (`confType = wpm`, `resourceId = -282579616`) |

---

## 시나리오 카탈로그

### Agent (에이전트 관리)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `agent_register_single` | 신규 WPM 에이전트 단건 등록 | action | `POST /api/wpm/v1/agents/standby-agent/register` |
| `agent_register_bulk` | 복수 에이전트 일괄 등록 | action | `POST /api/wpm/v1/agents/standby-agent/register` |
| `agent_auto_register_trigger` | READY 상태 에이전트 자동 등록 즉시 트리거 | action | `POST /api/wpm/v1/admin/trigger-agent-auto-registration` |
| `agent_unregister` | 에이전트 삭제 (단건 또는 일괄) | action | `POST /api/wpm/v1/agents/unregister` |
| `agent_env_info` | 에이전트 Java 환경 변수 조회 | detail | `GET /api/wpm/v1/agents/{agentId}/env` |
| `agent_was_info` | 에이전트 WAS 버전·구성 정보 조회 | detail | `GET /api/wpm/v1/agents/{agentId}/was-info` |
| `agent_options_get` | 에이전트 옵션 전체 또는 특정 키 조회 | detail | `POST /api/wpm/v1/agents/options/get` |
| `agent_options_set` | 에이전트 샘플링·임계값·SQL 수집 옵션 변경 | action | `POST /api/wpm/v1/agents/options/set` |
| `agent_loaded_classes` | 에이전트에 로드된 JVM 클래스 목록 페이징 조회 | list | `POST /api/wpm/v1/agents/classes/list` |
| `agent_loaded_classes_excel` | 로드된 클래스 목록 엑셀 다운로드 | export | `POST /api/wpm/v1/agents/classes/excel-download` |
| `agent_textcache_clear` | 에이전트 텍스트 캐시 강제 초기화 | action | `POST /api/wpm/v1/agents/textcache/clear` |
| `license_check` | WPM 라이센스 잔여 수량 및 에이전트 수 확인 | detail | `POST /api/wpm/settings/info` |

---

### Active Service (액티브 서비스 모니터링)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `active_service_top10` | 응답시간 기준 상위 10개 액티브 서비스 조회 | list+sort | `POST /api/wpm/v1/services/active/top` |
| `active_service_top30_tag_filter` | 특정 태그로 필터링한 상위 30개 액티브 서비스 조회 | list+filter | `POST /api/wpm/v1/services/active/top` |
| `active_service_top50_all_agents` | 전체 에이전트 대상 상위 50개 웹 서비스 현황 | list | `POST /api/wpm/v1/services/active/top` |
| `active_thread_detail` | 특정 에이전트 액티브 스레드 스택 트레이스 상세 조회 | detail | `POST /api/wpm/v1/services/active/thread/detail` |
| `agent_active_service_list` | 특정 에이전트에서 처리 중인 서비스 목록 조회 | list | `POST /api/wpm/v1/agents/activeservice/list` |
| `agent_thread_interrupt` | 과부하 배치 스레드에 인터럽트 신호 전송 | action | `POST /api/wpm/v1/agents/activeservice/thread/command` |
| `service_map` | 서비스의 에이전트 간 호출 관계 서비스맵 조회 | detail | `POST /api/wpm/v1/services/{serviceId}/service-map` |

---

### Heap Dump (힙덤프 관리)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `heapdump_list` | 에이전트 힙덤프 파일 목록 조회 | list | `POST /api/wpm/v1/agents/heapdump/list` |
| `heapdump_create` | 메모리 누수 분석을 위한 힙덤프 즉시 생성 | action | `POST /api/wpm/v1/agents/heapdump/create` |
| `heapdump_delete` | 분석 완료 후 힙덤프 파일 삭제 (디스크 확보) | action | `POST /api/wpm/v1/agents/heapdump/delete` |

---

### Service Dump (서비스덤프 관리)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `servicedump_list` | 에이전트 서비스덤프 파일 목록 조회 | list | `POST /api/wpm/v1/agents/servicedump/list` |
| `servicedump_create` | 장애 발생 시 서비스덤프 즉시 생성 | action | `POST /api/wpm/v1/agents/servicedump/create` |
| `servicedump_detail` | 서비스덤프 파일 상세 내용 조회 (스레드 상태 포함) | detail | `POST /api/wpm/v1/agents/servicedump/detail` |
| `servicedump_delete` | 분석 완료된 서비스덤프 파일 삭제 | action | `POST /api/wpm/v1/agents/servicedump/delete` |

---

### Thread / JVM (스레드·JVM 진단)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `thread_list` | 현재 실행 중인 JVM 스레드 목록 조회 | list | `POST /api/wpm/v1/agents/threads/list` |
| `thread_list_hang_check` | 행(hang) 상태 스레드 존재 여부 점검 | list+filter | `POST /api/wpm/v1/agents/threads/list` |
| `thread_dump_single` | 에이전트 스레드 덤프 단건 요청 | action | `POST /api/wpm/v1/agents/threads/dump` |
| `thread_dump_repeated` | 짧은 간격으로 반복 스레드 덤프 수집 (교착 상태 분석) | action | `POST /api/wpm/v1/agents/threads/dump` |
| `hourly_aggregation_trigger` | 특정 시간대 방문자 집계 수동 트리거 | action | `POST /api/wpm/v1/admin/trigger-hourly-aggregation` |

---

### Transaction / Trace (트레이스 분석)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `trace_list_by_time` | 시간 범위로 트레이스 목록 조회 | list+timeFilter | `POST /api/wpm/v1/services/{serviceId}/traces/list-filter` |
| `trace_list_slow` | 응답시간 긴 느린 트레이스 목록 필터 조회 | list+filter | `POST /api/wpm/v1/services/{serviceId}/traces/list-filter` |
| `trace_list_error` | 에러가 발생한 트레이스 목록만 조회 | list+filter | `POST /api/wpm/v1/services/{serviceId}/traces/list-filter` |
| `trace_timeline` | 특정 트레이스의 타임라인 뷰 조회 | detail | `GET /api/wpm/v1/services/{serviceId}/traces/{traceId}/timeline` |
| `trace_spans` | 트레이스에 포함된 스팬 목록 조회 (SQL·외부 API 포함) | detail | `GET /api/wpm/v1/services/{serviceId}/traces/{traceId}/spans` |
| `trace_response_distribution` | 서비스 응답 분포도 스캐터 차트 조회 | chart | `POST /api/wpm/v1/services/{serviceId}/traces/list-filter` |
| `trace_list_excel` | 트레이스 목록 엑셀 다운로드 | export | `POST /api/wpm/v1/services/{serviceId}/traces/list-filter` |
| `text_lookup_sql` | SQL 해시로 원문 SQL 텍스트 조회 | detail | `POST /api/wpm/v1/texts/view` |
| `text_lookup_url` | 엔드포인트 URL 해시로 원문 URL 조회 | detail | `POST /api/wpm/v1/texts/view` |

---

### Statistics (통계 — 엔트리포인트/SQL/HTTP/에러)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `stats_entrypoints_response_time` | 응답시간 기준 엔트리포인트 통계 조회 | list+sort | `POST /api/wpm/v1/statistics/entrypoints` |
| `stats_entrypoints_tps` | 처리량(TPS) 기준 엔트리포인트 통계 조회 | list+sort | `POST /api/wpm/v1/statistics/entrypoints` |
| `stats_entrypoints_error` | 에러 건수 기준 URL별 통계 조회 | list+sort | `POST /api/wpm/v1/statistics/entrypoints` |
| `stats_entrypoints_by_agent` | 특정 에이전트별 엔트리포인트 통계 조회 | list+filter | `POST /api/wpm/v1/statistics/entrypoints/{id}` |
| `stats_entrypoints_excel` | 엔트리포인트 통계 엑셀 다운로드 | export | `POST /api/wpm/v1/statistics/entrypoints/excel-download` |
| `stats_sql_slow` | 느린 SQL 쿼리 통계 (응답시간 기준 정렬) | list+sort | `POST /api/wpm/v1/statistics/sql` |
| `stats_sql_by_agent` | 특정 에이전트의 SQL 실행 통계 조회 | list+filter | `POST /api/wpm/v1/statistics/sql/{id}` |
| `stats_sql_detail` | 특정 SQL 집계 행 상세 실행 정보 조회 | detail | `POST /api/wpm/v1/statistics/sql/{id}/detail` |
| `stats_sql_excel` | SQL 통계 엑셀 다운로드 | export | `POST /api/wpm/v1/statistics/sql/excel-download` |
| `stats_http_slow` | 응답이 느린 외부 HTTP 호출 통계 조회 | list+sort | `POST /api/wpm/v1/statistics/http` |
| `stats_http_by_agent` | 특정 에이전트의 외부 HTTP 호출 통계 | list+filter | `POST /api/wpm/v1/statistics/http/{id}` |
| `stats_error_top` | 에러 발생 건수 기준 예외 통계 조회 | list+sort | `POST /api/wpm/v1/statistics/error` |
| `stats_error_by_agent` | 특정 에이전트의 에러 발생 통계 조회 | list+filter | `POST /api/wpm/v1/statistics/error/{id}` |
| `stats_error_detail` | 에러 통계 집계 행 상세 컨텍스트 조회 | detail | `POST /api/wpm/v1/statistics/error/{id}/detail` |

---

### Monitoring / Health (모니터링·설정·보관주기)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `entrypoint_treemap_response` | 응답시간 기준 엔트리포인트 트리맵 조회 | chart | `POST /api/wpm/v1/services/entrypoints/treemap` |
| `entrypoint_treemap_tps` | 처리량(TPS) 기준 엔트리포인트 트리맵 조회 | chart | `POST /api/wpm/v1/services/entrypoints/treemap` |
| `entrypoint_stats_chart` | 특정 엔트리포인트 시간별 성능 차트 조회 | chart+timeFilter | `POST /api/wpm/v1/services/entrypoints/statistics-chart` |
| `entrypoint_stats_latest` | 엔트리포인트 최신 성능 통계 1건 조회 | detail | `POST /api/wpm/v1/services/entrypoints/statistics/latest` |
| `hourly_visitors_chart` | 금일 시간별 방문자수 전일/전주 비교 차트 | chart+timeFilter | `POST /api/wpm/v1/services/{serviceId}/hourly-visitors` |
| `hourly_visitors_detail` | 특정 시간대 방문자수 상세 에이전트별 조회 | detail | `POST /api/wpm/v1/services/{serviceId}/hourly-visitors/detail` |
| `hourly_visitors_excel` | 시간별 방문자수 엑셀 다운로드 | export | `POST /api/wpm/v1/services/{serviceId}/hourly-visitors/excel-download` |
| `service_basic_info` | 리소스 ID로 서비스 기본 정보 조회 | detail | `GET /api/wpm/v1/configuration/{resourceId}/basic-info` |
| `service_setting_read` | 서비스 개별 임계값·샘플링 설정 조회 | detail | `GET /api/wpm/v1/setting/{serviceId}/read` |
| `service_setting_update` | 서비스 응답시간 임계값·샘플링 비율 설정 변경 | action | `PUT /api/wpm/v1/setting/{serviceId}/update` |
| `service_unregister` | 운영 종료 서비스 삭제 (단건 또는 일괄) | action | `POST /api/wpm/v1/services/unregister` |
| `retention_policy_list` | WPM 데이터 보관주기 정책 전체 목록 조회 | list | `GET /api/wpm/v1/retention-policies` |
| `retention_policy_update` | 트레이스·힙덤프·통계 데이터 보관주기 정책 저장/수정 | action | `PUT /api/wpm/v1/retention-policies/{policyName}` |
| `server_health_check` | WPM 서버 정상 동작 여부 헬스체크 | detail | `GET /api/wpm/v1/health` (또는 헬스체크 endpoint) |

---

## 사용법

이 카탈로그는 `openapi-llm-spec` 스킬의 **Phase 7 (examples 생성)** 단계에서 참조한다.

- 각 endpoint의 `examples` key는 위 시나리오 ID (`active_service_top10` 등) 영문 snake_case를 우선 사용
- summary는 한국어 자연어로 작성 (메타라벨·enum 코드값 노출 금지)
- tagFilter 조합 시나리오는 `confType = wpm` + `resourceId = <id>` 패턴 사용
- **WPM 시나리오 강제 적용 우선순위**: 느린 트레이스/트랜잭션 > 스레드 행(hang)/덤프 > 힙덤프 메모리 누수 > 엔트리포인트 성능 통계 > 방문자수 비교
- audit 결함 보완: response data sparse 3건 → trace_timeline / trace_spans / stats_error_detail 시나리오에서 data shape 인라인 정의 강화
- 6 endpoint underdoc → agent_env_info / agent_was_info / agent_options_get / text_lookup_sql / service_basic_info / retention_policy_update 우선 보완

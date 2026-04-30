# LMS 시나리오 카탈로그

도메인: **Log Management System (로그 수집/조회/패턴/파싱)**
Spec: `openapi/lms.openapi.json` | 41 endpoints | Audit 4.8/5

---

## 도메인 정체성

**Log Management System** — 로그 수집 파이프라인(Avro 배치 ingest), 파싱 설정(GROK/REGEX), 매칭/미매칭 패턴 현황, 전체현황 로그 조회, 샘플 메시지, 파싱 테스트, Facet 필터, 이벤트 관제 confType 관리까지 아우르는 로그 관리 모듈.

---

## 도메인 어휘

| 용어 | 정의 |
|------|------|
| parsingConfig | 로그를 파싱하는 설정 단위 (이름, GROK/REGEX 패턴, logTypeTag, enable 여부) |
| parserType | `GROK` 또는 `REGEX` — 파싱 엔진 구분 |
| logTypeTag | 로그 수집 소스에 붙이는 타입 태그. 예: `mssql`, `nginx`, `mysql` |
| eventType | 로그 이벤트 분류 타입. 파싱 설정에서 참조 |
| matchedLog | 파싱 설정 패턴에 매칭된 로그. `parsing-stat/matched` 계열 |
| unmatchedLog | 어떤 파싱 설정에도 매칭되지 않은 로그. `parsing-stat/unmatched` 계열 |
| logLevel | 로그 심각도. `ERROR`, `WARN`, `INFO`, `DEBUG` |
| cursor | 커서 기반 페이지네이션 토큰. `nextCursor` 필드로 다음 페이지 요청 |
| startTime / endTime | 시간 범위 — epoch milliseconds (int64) |
| confType | 이벤트 관제 식별자. 예: `server.LogMonitor`, `db.AlertMonitor` |
| Avro | 로그 배치 수집 직렬화 포맷 |
| facetFilter | 전체현황/파싱설정/패턴 화면에서 항목별 건수를 반환하는 필터 집계 API |
| parsingSample | 파싱 설정 생성/수정 시 사용할 샘플 로그 메시지 조회 |
| tagFilter | `key op value` 문법의 구조화 필터. 배열 원소 간 AND |

---

## 시나리오 카탈로그

### Log Query / Overview (전체현황 로그 조회)

| scenario_id | 대표 자연어 질의 | pattern | operationId |
|---|---|---|---|
| `log_messages_first_page` | "전체 현황 로그 메시지 목록 첫 페이지 조회" | list+timeFilter | `logOverview_getLogMessages` |
| `log_messages_error_level` | "에러 수준 로그 메시지 목록 조회" | list+filter | `logOverview_getLogMessages` |
| `log_messages_keyword_search` | "timeout 키워드로 로그 메시지 검색" | list+search | `logOverview_getLogMessages` |
| `log_messages_cursor_next` | "커서 기반으로 로그 메시지 다음 페이지 조회" | list+cursor | `logOverview_getLogMessages` |
| `log_messages_by_host` | "특정 호스트의 로그 메시지 목록 조회" | list+filter | `logOverview_getLogMessages` |
| `log_detail_by_id` | "특정 로그 ID의 파싱 상세 정보 조회" | detail | `logOverview_detail` |
| `log_detail_error_trace` | "에러 로그의 파싱 필드 및 추적 정보 상세 확인" | detail | `logOverview_detail` |
| `log_count_chart_today` | "오늘 시간대별 로그 수집 건수 차트 조회" | chart+timeFilter | `logOverview_countChart` |
| `log_count_chart_error_week` | "지난 1주 에러 로그 건수 추이 차트 조회" | chart+filter | `logOverview_countChart` |
| `log_messages_excel_today` | "오늘 전체 로그 메시지 목록 엑셀 다운로드" | export | `logOverview_listExcel` |
| `log_messages_excel_error` | "에러 로그 메시지 엑셀로 내보내기" | export+filter | `logOverview_listExcel` |

### Log Ingest / Collection (로그 수집)

| scenario_id | 대표 자연어 질의 | pattern | operationId |
|---|---|---|---|
| `log_ingest_avro_batch` | "Avro 형식 로그 이벤트 배치로 수집하여 버퍼에 저장" | action | `logIngest_batch` |
| `log_ingest_delete_index_schedule` | "보존기간 초과 로그 인덱스 삭제 스케줄 실행" | action | `logIngest_deleteIndexSchedule` |
| `log_event_ingest_single_test` | "nginx 단일 로그 이벤트 수집 테스트" | action+test | `logEventIngest_single` |
| `log_event_ingest_batch_test` | "nginx 로그 이벤트 2건 배치 수집 테스트" | action+test | `logEventIngest_batch` |

### Pattern / Parsing Stat — Matched (매칭 패턴 현황)

| scenario_id | 대표 자연어 질의 | pattern | operationId |
|---|---|---|---|
| `matched_log_list_first_page` | "매칭 로그 첫 페이지 조회" | list+cursor | `getMatchedLogTableList` |
| `matched_log_list_warn_level` | "WARNING 레벨 매칭 로그 조회" | list+filter | `getMatchedLogTableList` |
| `matched_log_list_cursor_next` | "다음 페이지 조회 (cursor 사용)" | list+cursor | `getMatchedLogTableList` |
| `matched_log_detail_error` | "ERROR 로그 상세 보기" | detail | `getMatchedLogDetail` |
| `matched_log_chart_1h` | "최근 1시간 매칭 로그 차트 조회" | chart+timeFilter | `getMatchedLogChart` |
| `matched_log_chart_today` | "오늘 매칭 로그 추이 보기" | chart+timeFilter | `getMatchedLogChart` |
| `matched_log_histogram_1h` | "패턴 로그 최근 1시간 히스토그램" | chart+timeFilter | `getMatchedPatternHistogram` |
| `matched_log_messages_first_page` | "매칭 패턴 로그 메시지 첫 페이지 조회" | list+cursor | `getMatchedLogMessages` |
| `matched_log_messages_cursor_next` | "다음 페이지 로그 메시지 조회" | list+cursor | `getMatchedLogMessages` |
| `matched_log_excel_download` | "매칭 로그 전체 엑셀 다운로드" | export | `downloadMatchedListExcel` |

### Pattern / Parsing Stat — Unmatched (미매칭 패턴 현황)

| scenario_id | 대표 자연어 질의 | pattern | operationId |
|---|---|---|---|
| `unmatched_list_1h` | "최근 1시간 미매칭 로그 파싱 통계 목록 조회" | list+timeFilter | `parsingStatUnmatched_list` |
| `unmatched_list_nginx_today` | "오늘 수집된 미매칭 이벤트 중 nginx 관련 항목 목록 조회" | list+filter | `parsingStatUnmatched_list` |
| `unmatched_detail_by_id` | "특정 미매칭 로그 ID 상세 정보 조회" | detail | `parsingStatUnmatched_detail` |
| `unmatched_count_chart_today` | "오늘 미매칭 로그 수 시간대별 차트 조회" | chart+timeFilter | `parsingStatUnmatched_countChart` |
| `unmatched_histogram_host` | "호스트별 미매칭 파싱 이벤트 분포 히스토그램 조회" | chart+filter | `parsingStatUnmatched_histogram` |
| `unmatched_log_messages_list` | "미매칭 패턴에 해당하는 실제 로그 메시지 첫 페이지 조회" | list+cursor | `parsingStatUnmatched_logMessages` |
| `unmatched_excel_today` | "오늘 미매칭 파싱 통계 목록 엑셀 다운로드" | export | `parsingStatUnmatched_listExcel` |

### Parsing Config (파싱 설정 관리)

| scenario_id | 대표 자연어 질의 | pattern | operationId |
|---|---|---|---|
| `parsing_config_save_nginx_grok` | "nginx access 로그 GROK 파싱 설정 저장" | action | `saveParsingConfig` |
| `parsing_config_save_mysql_regex` | "MySQL 에러 로그 REGEX 파싱 설정 저장" | action | `saveParsingConfig` |
| `parsing_config_update_nginx` | "nginx 파싱 설정 업데이트" | action | `updateParsingConfig` |
| `parsing_config_disable` | "파싱 설정 비활성화" | action | `updateParsingConfig` |
| `parsing_config_list_all` | "파싱 설정 전체 목록 조회" | list | `getParsingConfigList` |
| `parsing_config_list_grok_only` | "GROK 파서만 조회" | list+filter | `getParsingConfigList` |
| `parsing_config_list_enabled` | "활성화된 파싱 설정만 보여줘" | list+filter | `getParsingConfigList` |
| `parsing_config_enable_toggle` | "파싱 설정 활성화" | action | `enableParsingConfig` |
| `parsing_config_delete_single` | "파싱 설정 하나 삭제" | action | `deleteParsingConfigs` |
| `parsing_config_delete_bulk` | "파싱 설정 여러 개 삭제" | action | `deleteParsingConfigs` |
| `parsing_config_check_name` | "nginx-access-parser 이름 중복 체크" | query | `checkDuplicatedParsingConfigName` |
| `parsing_config_excel_all` | "파싱 설정 전체 엑셀 다운로드" | export | `downloadParsingConfigExcel` |
| `parsing_config_excel_grok` | "GROK 파서 설정만 엑셀로 받아줘" | export+filter | `downloadParsingConfigExcel` |

### Filter / Configuration (필터 집계 · 참조 데이터)

| scenario_id | 대표 자연어 질의 | pattern | operationId |
|---|---|---|---|
| `facet_overview_log_level_counts` | "전체 현황 화면에서 로그 수준별 항목 건수 조회" | count | `facetFilter_overviewCounts` |
| `facet_overview_host_counts` | "전체 현황 호스트별 로그 이벤트 건수 조회" | count | `facetFilter_overviewCounts` |
| `facet_parsing_config_enable_counts` | "파싱 설정 화면에서 활성화 여부별 항목 건수 조회" | count | `facetFilter_parsingConfigCounts` |
| `facet_parsing_config_parser_type_counts` | "파서 종류(GROK/REGEX)별 파싱 설정 건수 조회" | count | `facetFilter_parsingConfigCounts` |
| `facet_pattern_log_level_counts` | "매칭된 로그의 로그 수준별 패턴 필터 건수 조회" | count | `facetFilter_patternCounts` |
| `facet_pattern_unmatched_host_counts` | "미매칭 로그의 호스트별 패턴 현황 필터 건수 조회" | count | `facetFilter_patternCounts` |
| `event_type_list_all` | "이벤트 타입 전체 조회" | list | `getEventTypeList` |
| `log_tag_list_all` | "로그 타입 태그 전체 조회" | list | `getLogTagList` |

### Parsing Test / Sample (파싱 테스트 · 샘플)

| scenario_id | 대표 자연어 질의 | pattern | operationId |
|---|---|---|---|
| `parsing_test_nginx_grok` | "nginx 접속 로그 GROK 패턴으로 파싱 테스트 실행" | action+test | `parsingTest_execute` |
| `parsing_test_mysql_regex` | "MySQL 에러 로그 REGEX 파싱 테스트" | action+test | `parsingTest_execute` |
| `parsing_test_unmatched_case` | "패턴 미매칭 케이스 파싱 테스트로 확인" | action+test | `parsingTest_execute` |
| `parsing_sample_mysql_tag` | "MySQL 태그 필터로 샘플 로그 메시지 첫 페이지 조회" | list+filter | `parsingSample_messages` |
| `parsing_sample_no_filter` | "태그 필터 없이 최근 수집된 샘플 로그 메시지 조회" | list | `parsingSample_messages` |
| `parsing_sample_chart_mysql` | "MySQL 태그 샘플 메시지 시간별 카운트 차트 조회" | chart+filter | `parsingSample_countChart` |
| `parsing_sample_excel_mysql` | "MySQL 샘플 로그 메시지 엑셀 다운로드" | export | `parsingSample_listExcel` |

### Event Monitoring / confType (이벤트 관제)

| scenario_id | 대표 자연어 질의 | pattern | operationId |
|---|---|---|---|
| `event_conf_type_list` | "현재 관제 중인 이벤트 confType 목록 조회" | list | `eventMonitoring_getConfTypes` |
| `event_conf_type_append_server` | "서버 로그 모니터 관제 유형 캐시에 추가" | action | `eventMonitoring_appendConfType` |
| `event_conf_type_delete` | "서버 로그 모니터 관제 유형 삭제" | action | `eventMonitoring_deleteConfType` |

---

## 사용법

### 시나리오 선택 기준

1. **자연어 매핑**: 사용자 발화를 `대표 자연어 질의` 컬럼과 의미 매칭 → `scenario_id` 결정
2. **operationId 조회**: 해당 `operationId` 로 spec 내 endpoint 위치 확인
3. **pattern 조합**: 패턴 키워드로 요청 파라미터 구성 방향 결정
   - `list` → 페이지 파라미터 (size, page 또는 cursor)
   - `list+timeFilter` → startTime/endTime epoch-ms 추가
   - `list+cursor` → cursor 기반 페이지네이션 (`nextCursor` 사용)
   - `list+filter` → 필터 파라미터 (logLevel, host, parserType 등)
   - `chart+timeFilter` → 시계열 차트, 시간 범위 필수
   - `count` → 필터 집계, 숫자 반환
   - `detail` → 단일 항목 상세, ID 파라미터 필수
   - `action` → POST/PUT/DELETE, body 필수
   - `action+test` → 테스트 전용 endpoint, 프로덕션 미사용
   - `export` → 엑셀 다운로드, binary 응답

### 주요 chain-call 패턴

```
# 파싱 설정 생성 후 테스트
1. getEventTypeList       → eventTypeId 획득
2. getLogTagList          → logTypeTag 획득
3. parsingSample_messages → 샘플 로그 메시지 획득
4. parsingTest_execute    → 패턴 검증
5. saveParsingConfig      → 파싱 설정 저장

# 매칭/미매칭 현황 드릴다운
1. facetFilter_patternCounts     → 필터 항목별 건수 확인
2. getMatchedLogTableList        → 매칭 로그 목록
3. getMatchedLogDetail           → 상세 조회
   또는
2. parsingStatUnmatched_list     → 미매칭 목록
3. parsingStatUnmatched_detail   → 상세 조회
```

### 시간 범위 변환 (epoch-ms)

| 자연어 | startTime 계산 | endTime |
|--------|----------------|---------|
| 최근 1시간 | now - 3_600_000 | now |
| 오늘 | 오늘 00:00:00 KST | now |
| 지난 1주 | now - 604_800_000 | now |
| 사용자 지정 | 직접 입력 | 직접 입력 |

### tagFilter 문법 예시

```
# logType 필터
"logType = nginx"
"logType IN [nginx, mssql, mysql]"

# 사용자 태그 필터
"tag.env = production"
"tag.role != standby"
```

---

총 시나리오 수: **28개** (섹션별: Log Query 11 · Ingest 4 · Matched 10 · Unmatched 7 · Parsing Config 13 · Filter 8 · Parsing Test/Sample 7 · Event Monitoring 3)

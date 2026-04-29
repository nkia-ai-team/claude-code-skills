# DPM 시나리오 카탈로그

## 도메인 정체성
**Database Performance Management (DPM)** — Oracle / MySQL / MariaDB / PostgreSQL / SQL Server(MSSQL) / Tibero / CUBRID 7개 DBMS 인스턴스의 실시간 성능 관제. 느린 SQL 추적, 세션/락 분석, 실행계획 조회, 테이블스페이스/메모리 용량 관리, 이력 기반 성능 추이 분석을 통합 제공한다.

---

## 도메인 어휘

| 용어 | 설명 |
|------|------|
| 인스턴스(Instance) | 관제 대상 DB 서버 단위 (resourceId로 식별) |
| 세션(Session) | DB에 연결된 클라이언트 연결 단위 |
| SQL / SQL 텍스트 | 수집된 실행 SQL 원문; sqlId / digest로 식별 |
| 실행계획(Execution Plan) | SQL 처리 경로; planHashValue / planHash |
| Full Table Scan | 인덱스 미사용 전체 테이블 읽기 |
| 느린 SQL(Slow SQL) | 기준 시간 초과 장시간 실행 SQL |
| 락(Lock) | 동시성 제어로 다른 세션이 대기하는 상태 |
| 블로커(Blocker) | 락을 보유하여 다른 세션을 대기시키는 세션 |
| 데드락(Deadlock) | 두 세션이 서로 상대방 자원을 대기하는 교착 상태 |
| 대기 이벤트(Wait Event) | 세션이 CPU 외 자원 대기 시 기록되는 이벤트 |
| 테이블스페이스(Tablespace) | Oracle/Tibero 데이터 파일 논리 그룹; 용량/사용률 관리 |
| SGA / PGA | Oracle/Tibero 인스턴스 공유/프로세스 메모리 영역 |
| InnoDB Buffer Pool | MySQL/MariaDB 데이터 캐시 메모리 |
| Efficiency(Hit Ratio) | 버퍼 캐시 적중률 등 메모리 효율 지표 |
| Scatter 차트 | SQL 실행시간 × 실행횟수 분포 시각화 |
| Top SQL | 리소스 소모 상위 SQL 목록 |
| 이력(History) | 수집된 과거 성능 데이터 (시간 범위 지정) |
| 사전 등록(Pre-register) | 정책·태그 미확정 상태로 미리 등록하는 DB 항목 |
| Custom SQL | 사용자 정의 쿼리를 지표로 등록하는 기능 |
| Bloating | PostgreSQL 테이블/인덱스 부풀림(Dead Tuple 누적) |

---

## 시나리오 카탈로그

### Slow SQL / SQL Analysis

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `oracle_slow_sql_top10` | Oracle 인스턴스의 느린 SQL Top 10 | list+sort | `POST /api/dpm/oracle/history/sql/top-sql-summary` |
| `mysql_slow_sql_top10` | MySQL 느린 SQL Top 10 이력 | list+sort | `POST /api/dpm/mysql/history/sql/top-sql-summary` |
| `pg_slow_sql_top10` | PostgreSQL 느린 SQL Top 10 | list+sort | `POST /api/dpm/postgresql/history/sql/top-sql-summary` |
| `mssql_slow_sql_top10` | SQL Server 느린 SQL Top 10 | list+sort | `POST /api/dpm/sqlserver/history/sql/top-sql-summary` |
| `tibero_slow_sql_top10` | Tibero 느린 SQL Top 10 | list+sort | `POST /api/dpm/tibero/history/sql/top-sql-summary` |
| `oracle_sql_scatter` | Oracle SQL 실행시간 분포 Scatter 차트 | chart | `POST /api/dpm/oracle/sql/scatterchart` |
| `mysql_sql_scatter` | MySQL 현재 SQL Scatter (실행시간×횟수) | chart | `POST /api/dpm/mysql/sql/scatterchart` |
| `oracle_sql_full_text` | Oracle 특정 sqlId의 SQL 원문 조회 | detail | `GET /api/dpm/oracle/history/{resourceId}/sqltext/{sqlId}` |
| `oracle_sql_execution_plan` | Oracle SQL 실행계획 조회 (planHashValue) | detail | `GET /api/dpm/oracle/history/{resourceId}/sqlplan/{planHashValue}` |
| `mssql_sql_execution_plan` | SQL Server SQL 실행계획 XML 조회 | detail | `GET /api/dpm/sqlserver/history/{resourceId}/sqlplan/{planHash}` |
| `tibero_sql_execution_plan` | Tibero SQL 실행계획 조회 | detail | `GET /api/dpm/tibero/history/{resourceId}/sqlplan/{planHashValue}` |
| `oracle_sql_history_range` | Oracle SQL 이력 시간 범위 조회 (느린 SQL 구간 분석) | list+timeFilter | `POST /api/dpm/oracle/history/sql/sql-list-with-range` |
| `mssql_sql_history_list` | SQL Server SQL 이력 목록 (DB별 필터) | list+filter | `POST /api/dpm/sqlserver/history/sql/sql-list` |
| `pg_top_sql_history` | PostgreSQL Top SQL 시계열 이력 추이 | list+timeFilter | `POST /api/dpm/postgresql/sql/{resourceId}/top-sql-history` |
| `custom_sql_query_result` | 사용자 정의 SQL 즉시 실행 결과 조회 | action | `POST /api/dpm/custom/query-result` |

---

### Session / Lock

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `oracle_session_lock_status` | Oracle 세션 상태별 카운트 (active/inactive/lock) | detail | `GET /api/dpm/oracle/session/{resourceId}/status` |
| `oracle_blocking_sessions` | Oracle 락 보유 세션(블로커)과 대기 세션 목록 | list+filter | `POST /api/dpm/oracle/session/{resourceId}/current` |
| `mssql_blocking_sessions` | SQL Server 블로킹 세션과 블로커 현황 | list+filter | `POST /api/dpm/sqlserver/session/{resourceId}/current` |
| `pg_blocking_sessions` | PostgreSQL 락 대기 세션과 블로커 식별 | list+filter | `POST /api/dpm/postgresql/session/{resourceId}/current` |
| `mysql_lock_waiting_sessions` | MySQL 락 대기 중인 세션 목록 | list+filter | `POST /api/dpm/mysql/session/{resourceId}/current` |
| `tibero_blocking_sessions` | Tibero 블로킹 세션 현황 | list+filter | `POST /api/dpm/tibero/session/{resourceId}/current` |
| `oracle_session_kill` | Oracle 이상 세션 강제 종료 | action | `POST /api/dpm/oracle/session/kill` |
| `mssql_session_kill` | SQL Server 블로킹 세션 강제 종료 | action | `POST /api/dpm/sqlserver/session/kill` |
| `pg_session_kill` | PostgreSQL 세션 pg_terminate_backend 종료 | action | `POST /api/dpm/postgresql/session/kill` |
| `oracle_session_history_list` | Oracle 세션 이력 목록 (특정 시간대 이상 세션 소급) | list+timeFilter | `POST /api/dpm/oracle/history/session/list` |
| `mssql_session_history_list` | SQL Server 세션 이력 목록 (락 발생 구간 조회) | list+timeFilter | `POST /api/dpm/sqlserver/history/session/list` |
| `oracle_session_single_barchart` | 특정 Oracle 세션의 이력 리소스 막대 차트 | chart | `POST /api/dpm/oracle/history/session/single-session-barchart` |
| `oracle_session_top_objects` | Oracle 세션 이력에서 Top Object 목록 | list+sort | `POST /api/dpm/oracle/history/session/top-objects` |

---

### Wait Event

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `oracle_wait_event_sessions` | Oracle 대기 이벤트 발생 세션 현황 (current) | list+filter | `POST /api/dpm/oracle/session/{resourceId}/current` |
| `oracle_session_plan_list` | Oracle 세션의 실행계획 목록 (대기 원인 분석용) | list | `POST /api/dpm/oracle/history/session-planlist` |
| `mssql_session_plan_list` | SQL Server 세션 실행계획 목록 (대기 세션 분석) | list | `POST /api/dpm/sqlserver/history/session-planlist` |
| `tibero_wait_session_plan` | Tibero 대기 세션의 실행계획 목록 | list | `POST /api/dpm/tibero/history/session-planlist` |
| `oracle_single_session_sql_bar` | 특정 Oracle 세션의 단일 SQL 대기 시간 막대 차트 | chart | `POST /api/dpm/oracle/history/session/single-sql-barchart` |
| `oracle_history_interval` | Oracle 이력 수집 시간 간격 확인 (대기 분석 기준) | detail | `POST /api/dpm/oracle/history/interval` |

---

### Tablespace / I/O

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `oracle_tablespace_list` | Oracle Tablespace 목록 및 사용률 | list | `POST /api/dpm/oracle/sql/tablespace-list` |
| `oracle_top_tablespace` | Oracle 사용률 Top Tablespace | list+sort | `POST /api/dpm/oracle/sql/top-tablespace` |
| `tibero_tablespace_list` | Tibero Tablespace 목록 및 사용률 | list | `POST /api/dpm/tibero/sql/tablespace-list` |
| `tibero_top_tablespace` | Tibero 사용률 상위 Tablespace | list+sort | `POST /api/dpm/tibero/sql/top-tablespace` |
| `mssql_database_io` | SQL Server 데이터베이스 IO 통계 (읽기/쓰기) | list | `POST /api/dpm/sqlserver/config/{resourceId}/database-io` |
| `mssql_datafile_list` | SQL Server Datafile 목록 및 용량 현황 | list | `POST /api/dpm/sqlserver/config/{resourceId}/datafile` |
| `mssql_top_storage_database` | SQL Server Top Database 저장공간 사용량 | list+sort | `POST /api/dpm/sqlserver/storage/top-database` |
| `pg_bloating_tables` | PostgreSQL Bloating 테이블/인덱스 목록 (부풀림 감지) | list+filter | `POST /api/dpm/postgresql/config/{resourceId}/bloating` |
| `cubrid_volume_usage` | CUBRID Volume 사용량 현황 | detail | `POST /api/dpm/cubrid/volume/{resourceId}/usage/{type}` |

---

### Instance Health

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `oracle_instance_efficiency` | Oracle 인스턴스 Hit Ratio (Buffer Cache 효율) | detail | `GET /api/dpm/oracle/instance/{resourceId}/efficiency` |
| `mysql_instance_efficiency` | MySQL InnoDB Buffer Pool Hit Ratio | detail | `GET /api/dpm/mysql/instance/{resourceId}/efficiency` |
| `pg_instance_efficiency` | PostgreSQL 인스턴스 Hit Ratio 및 Efficiency | detail | `GET /api/dpm/postgresql/instance/{resourceId}/efficiency` |
| `mssql_instance_efficiency` | SQL Server Efficiency (Buffer Hit Ratio) | detail | `GET /api/dpm/sqlserver/instance/{resourceId}/efficiency` |
| `tibero_instance_status` | Tibero 인스턴스 상태 (open/mount/nomount) | detail | `GET /api/dpm/tibero/instance/{resourceId}/status` |
| `oracle_instance_status` | Oracle 인스턴스 가동 상태 확인 | detail | `GET /api/dpm/oracle/instance/{resourceId}/status` |
| `oracle_sga_memory` | Oracle SGA 메모리 구성 및 사용량 | detail | `GET /api/dpm/oracle/memory/{resourceId}/sga` |
| `oracle_pga_memory` | Oracle PGA 메모리 사용량 | detail | `GET /api/dpm/oracle/memory/{resourceId}/pga` |
| `mssql_top_memory_clerk` | SQL Server Top Memory Clerk (메모리 점유 컴포넌트) | list+sort | `GET /api/dpm/sqlserver/memory/{resourceId}/top-clerk` |
| `mysql_innodb_memory` | MySQL InnoDB Buffer Pool 메모리 현황 | detail | `GET /api/dpm/mysql/memory/{resourceId}/innodb-memory` |
| `pg_shared_memory` | PostgreSQL Shared Memory 사용 현황 | detail | `GET /api/dpm/postgresql/memory/{resourceId}/shared` |
| `oracle_instance_list` | 전체 Oracle 인스턴스 목록 및 상태 요약 | list | `POST /api/dpm/oracle/list` |
| `mysql_instance_list` | 전체 MySQL 인스턴스 목록 | list | `POST /api/dpm/mysql/list` |
| `mssql_instance_list` | 전체 SQL Server 인스턴스 목록 | list | `POST /api/dpm/sqlserver/list` |
| `db_connect_check` | 특정 DB 인스턴스 연결 가능 여부 확인 | detail | `GET /api/dpm/connect-check/{resourceId}` |
| `multi_resource_status` | 여러 DB 리소스 상태 일괄 조회 | list | `POST /api/dpm/resource/status` |

---

### Chart / History

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `oracle_sql_history_scatter` | Oracle SQL 이력 Scatter (느린 SQL 분포 시각화) | chart+timeFilter | `POST /api/dpm/oracle/history/sql/scatterchart` |
| `mssql_sql_history_scatter` | SQL Server SQL 이력 Scatter 차트 | chart+timeFilter | `POST /api/dpm/sqlserver/history/sql/scatterchart` |
| `oracle_single_sql_linechart` | Oracle 특정 SQL 실행시간 추이 라인 차트 | chart+timeFilter | `POST /api/dpm/oracle/history/sql/single-sql-linechart` |
| `mysql_single_sql_linechart` | MySQL 특정 SQL 성능 추이 라인 차트 | chart+timeFilter | `POST /api/dpm/mysql/history/sql/single-sql-linechart` |
| `pg_single_sql_summary` | PostgreSQL 특정 SQL 이력 요약 (평균/최대 실행시간) | detail | `POST /api/dpm/postgresql/history/sql/single-sql-summary` |
| `oracle_single_sql_barchart` | Oracle 특정 SQL 시간대별 실행 막대 차트 | chart | `POST /api/dpm/oracle/history/sql/single-sql-barchart` |
| `oracle_sql_history_targetnames` | Oracle SQL 이력 스키마/대상명 목록 | list | `POST /api/dpm/oracle/history/sql/targetnames` |
| `cubrid_sql_history_scatter` | CUBRID SQL 이력 Scatter 차트 | chart+timeFilter | `POST /api/dpm/cubrid/history/sql/scatterchart` |

---

## 사용법

이 카탈로그는 `openapi-llm-spec` 스킬의 **Phase 7 (examples 생성)** 단계에서 참조한다.

- 각 endpoint의 `examples` key는 위 시나리오 ID(`oracle_slow_sql_top10` 등) 영문 snake_case를 우선 사용
- 동일 DB 계열 endpoint (Oracle/MySQL/MariaDB/PostgreSQL/MSSQL/Tibero/CUBRID)는 DBMS 이름을 prefix로 구분
- summary는 한국어 자연어로 작성 (메타라벨·enum 코드값 노출 금지)
- **DB 시나리오 강제 적용 우선순위**: 느린 SQL > 락/블로킹 > 대기 이벤트 > 테이블스페이스 용량 > 인스턴스 효율
- audit 결함 보완: "운영계 태그 필터" 반복 대신 DB 엔진별 고유 시나리오 사용 (위 카탈로그 참조)

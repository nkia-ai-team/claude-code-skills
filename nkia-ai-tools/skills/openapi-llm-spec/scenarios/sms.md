# sms Examples 시나리오 카탈로그

## 도메인 정체성

SMS(Server Management System)는 서버(호스트) 등록·삭제·현황 조회, 에이전트 패치/설치 파일 관리, 구성정보(CPU/메모리/디스크/NIC/GPU/HBA/소프트웨어/핫픽스) 조회, 성능지표 상세 조회, 사용자 정의 모니터(로그/이벤트로그/프로세스/파일/Ping/TCP/Netstat/윈도우서비스/윈도우성능카운터) 관리, 모니터 템플릿·스크립트 관리, 네트워크 포트 인증정보, 사용자 성능 분석(UPM), 실시간 대시보드, 오퍼레이션(재시작/명령/Ping/Traceroute) API로 구성된 서버 관제 핵심 도메인이다.

---

## 도메인 어휘 (18개)

| 영문 | 한국어 | 설명/사용처 |
|---|---|---|
| host / hostName | 호스트 / 서버명 | 관제 대상 서버. tagFilter `hostName`, sort fieldName |
| resourceId | 리소스 ID | 에이전트가 부여한 서버 식별자. `MA_web-01_20240719` 형태 |
| osType | OS 유형 | `LINUX` / `WINDOWS` / `AIX`. tagFilter enum_ref `OsTypeEnum` |
| agentVersion | 에이전트 버전 | `10.2.5` 형태. gridFilter `agentVersion` |
| patchStatus | 패치 상태 | `COMPLETED` / `FAILED` / `PENDING` / `RUNNING` |
| availabilityStatus | 가용성 | `UP` / `DOWN`. 성능 조회·필터에 사용 |
| confType | 구성 유형 | `server`. agent list-filter 기본 tagFilter |
| monitorType | 커스텀 모니터 유형 | `LOG` / `EVENT_LOG` / `PROCESS` / `FILE` / `PING` / `CONNECT_TIME` / `NETSTAT` / `WIN_SERVICE` / `WIN_PERF_COUNTER` |
| collectionInterval | 수집 주기 | 커스텀 모니터 등록 시 초 단위 값 |
| threshold | 임계치 | 커스텀 모니터 경보 발생 기준값 |
| cpuUsage / memoryUsagePercent | CPU 사용률 / 메모리 사용률 | 성능 지표 응답 필드 |
| diskUsagePercent | 디스크 사용률 | 성능 지표 응답 필드 |
| protocol | 프로토콜 | `TCP` / `UDP`. 네트워크 포트 등록 시 사용 |
| tagFilters | 태그 필터 | list-filter 요청의 서버측 pre-filter (confType, osType, hostName, tag.*) |
| gridFilters | 그리드 필터 | list-filter 요청의 컬럼 레벨 후처리 필터 (field/value/operator) |
| sortFieldSets | 정렬 설정 | `{index, sortDirection(ASC/DESC), fieldName}` 배열 |
| standby | 등록대기 | 에이전트가 설치됐지만 아직 정식 등록 안 된 호스트 |
| UPM (user-performance-metric) | 사용자 성능 분석 | 관리자가 커스텀 정의한 성능 분석 뷰 |

---

## 시나리오 카탈로그 (서브도메인별, 47개)

### Host / Server

| key | summary | intent | 비고 |
|---|---|---|---|
| `cpu_over_80` | "CPU 사용률 80% 넘는 Linux 서버만 보여줘" | list+filter | tagFilter `osType=LINUX` + gridFilter `cpuUsage > 80` |
| `linux_only` | "Linux 계열 서버 목록 전체 불러와 줘" | list+filter | tagFilter `osType=LINUX` |
| `windows_only` | "Windows 서버만 골라서 보여줘" | list+filter | tagFilter `osType=WINDOWS` |
| `aix_only` | "AIX 서버 전체 목록 조회해 줘" | list+filter | tagFilter `osType=AIX` |
| `mem_heavy` | "메모리 사용률 90% 이상인 서버 목록 뽑아줘" | list+filter | gridFilter `memoryUsagePercent >= 90` |
| `disk_critical` | "디스크 사용률 95% 넘는 서버 알려줘" | list+filter | gridFilter `diskUsagePercent > 95` |
| `down_hosts` | "현재 가용성이 DOWN인 서버만 필터링해 줄래?" | list+filter | gridFilter `availabilityStatus=DOWN` |
| `ad_prefix` | "호스트명이 WEB으로 시작하는 서버만 조회해 줄래?" | list+filter | tagFilter `hostName LIKE 'WEB%'` |
| `count_windows` | "Windows 서버 총 몇 대야?" | count | tagFilter `osType=WINDOWS` |
| `prod_tag` | "운영 환경(tag.env=PROD) 서버 목록 알려줘" | list+filter | tagFilter `tag.env=PROD` |
| `db_role` | "DB 역할(tag.role=DB) 서버만 보여줘" | list+filter | tagFilter `tag.role=DB` |
| `sorted_by_name` | "서버 목록을 이름 오름차순으로 정렬해서 100건 불러와 줘" | list+filter | sortFieldSets `name ASC`, pagePerSize 100 |
| `host_basic_info` | "이 리소스 ID의 서버 기본 정보(OS·CPU·메모리 용량)를 알고 싶어" | detail | `GET /configuration/{resourceId}/basic-info` |
| `overall_config` | "서버 하나의 전체 구성정보를 한 번에 다 가져와 줄래?" | detail | `GET /configuration/{resourceId}/overall` |
| `standby_register` | "등록 대기 중인 서버를 정식 호스트로 등록해 줘" | create | `standby-hosts/register` |
| `host_delete_single` | "이 리소스 ID 하나를 호스트 목록에서 삭제해 줘" | delete | parameter 단건 |
| `host_delete_bulk` | "철거 완료된 서버 5대를 한꺼번에 삭제하고 싶어" | delete | parameter 5건 배열 |
| `manage_status_off` | "이 서버를 비관리 상태로 전환해 줄래?" | update | `hosts/manage-status` |

---

### Configuration (구성정보)

| key | summary | intent | 비고 |
|---|---|---|---|
| `disk_list` | "이 서버에 붙어 있는 디스크 파티션 목록 전부 알려줘" | detail | `GET /configuration/{resourceId}/disk` |
| `nic_list` | "서버의 네트워크 인터페이스(NIC) 목록 조회해 줄래?" | detail | `GET /configuration/{resourceId}/network-interface` |
| `software_list` | "이 서버에 설치된 소프트웨어 목록 보고 싶어" | detail | `GET /configuration/{resourceId}/software` |
| `hotfix_list` | "최근 패치 내역(핫픽스) 알려줘" | detail | `GET /configuration/{resourceId}/hotfix` |
| `gpu_list` | "이 서버의 GPU 카드 목록이 궁금해" | detail | `GET /configuration/{resourceId}/gpu-card` |
| `hba_port_list` | "서버의 HBA 포트 정보 조회해 줘" | detail | `GET /configuration/{resourceId}/hba-port` |
| `conf_refresh` | "이 서버의 구성 데이터를 지금 당장 강제 수집해 줄래?" | action | `settings/request/config-info` |

---

### Agent

| key | summary | intent | 비고 |
|---|---|---|---|
| `agent_active_only` | "현재 활성 상태인 에이전트만 조회해 줘" | list+filter | gridFilter `status=ACTIVE` |
| `agent_old_version` | "에이전트 버전이 10.2.3인 서버 목록 뽑아줘" | list+filter | gridFilter `agentVersion=10.2.3` |
| `agent_patch_completed` | "패치 완료된 에이전트 목록 보여줘" | list+filter | gridFilter `patchStatus=COMPLETED` |
| `agent_patch_failed` | "패치 실패한 에이전트만 골라줘" | list+filter | gridFilter `patchStatus=FAILED` |
| `agent_update_single` | "이 에이전트 한 대에 최신 패치 파일 적용해 줘" | action | `agent/update` parameter 단건 |
| `agent_update_bulk` | "패치 대상 서버 3대를 한꺼번에 업데이트해 줄래?" | action | `agent/update` parameter 3건 |
| `patch_file_list` | "업로드된 패치 파일 목록 중 가장 최근 수정된 것부터 보여줘" | list+filter | sortFieldSets `modifiedAt DESC` |
| `patch_file_download` | "특정 패치 파일을 파일 ID로 다운로드해 줘" | download | `agent/patch-file/download` |
| `agent_restart_single` | "응답이 없는 서버 에이전트 재시작해 줄래?" | action | `operation/agent-restart` 단건 |
| `agent_restart_bulk` | "점검 후 여러 에이전트를 동시에 재시작하고 싶어" | action | `operation/agent-restart` 다건 |

---

### Custom Monitor

| key | summary | intent | 비고 |
|---|---|---|---|
| `cm_log_register` | "Tomcat 오류 로그 패턴을 모니터링하도록 로그 모니터 등록해 줘" | create | `custom-monitor/register/log-monitor` |
| `cm_process_register` | "java 프로세스가 죽으면 알림 오도록 프로세스 모니터 등록해 줄래?" | create | `custom-monitor/register/process-monitor` |
| `cm_eventlog_register` | "Windows 이벤트로그 오류(레벨 2 이상)를 감시하는 모니터 만들어 줘" | create | `custom-monitor/register/event-log-monitor` |
| `cm_ping_register` | "외부 게이트웨이 192.168.1.1에 Ping 모니터 등록해 줄래?" | create | `custom-monitor/register/ping-monitor` |
| `cm_tcp_register` | "DB 서버 3306 포트 연결 시간 모니터 등록해 줘" | create | `custom-monitor/register/connect-time-monitor` |
| `cm_list_process_type` | "전체 커스텀 모니터 중 프로세스 유형만 조회해 줄래?" | list+filter | gridFilter `monitorType=PROCESS` |
| `cm_list_by_host` | "특정 서버에 등록된 커스텀 모니터 목록 전부 보여줘" | list+filter | `custom-monitor/list-filter/server` endpoint |
| `cm_count_by_type` | "커스텀 모니터 유형별 등록 건수 알려줘" | count | `custom-monitor/count/server/type-group` |
| `cm_deploy` | "이 템플릿으로 여러 서버에 커스텀 모니터를 일괄 배포해 줄래?" | action | `custom-monitor/deploy` |
| `cm_template_apply` | "모니터 템플릿을 선택한 서버에 적용해 줘" | action | `custom-monitor-templates/apply` |

---

### Netstat / Network Port

| key | summary | intent | 비고 |
|---|---|---|---|
| `nw_admin_port_list` | "관리자 포트 목록에 등록된 TCP 포트 전부 조회해 줄래?" | list+filter | gridFilter `protocol=TCP` |
| `nw_server_port_80` | "서버 포트 목록에서 80번 포트 인증 정보 찾아줘" | list+filter | gridFilter `port=80` |
| `nw_session_established` | "이 서버의 ESTABLISHED 상태 네트워크 세션만 보여줘" | list+filter | gridFilter `status=ESTABLISHED` |
| `nw_port_insert` | "서버 포트 인증 정보에 443/TCP 포트를 새로 추가해 줄래?" | create | `network/server/ports/insert` |
| `nw_port_delete` | "더 이상 사용 안 하는 포트 인증 정보 삭제해 줘" | delete | `network/admin/ports/delete` |

---

### Realtime Dashboard / UPM

| key | summary | intent | 비고 |
|---|---|---|---|
| `rd_create` | "운영 서버 CPU·메모리 현황 보는 실시간 대시보드 새로 만들어 줄래?" | create | `realtime-dashboard/register` |
| `rd_list_recent` | "최근에 수정된 대시보드부터 목록 조회해 줘" | list+filter | sortFieldSets `modifiedAt DESC` |
| `upm_register` | "특정 서버 그룹의 네트워크 트래픽을 분석하는 사용자 성능 분석 항목 등록해 줘" | create | `user-performance-metric/register` |
| `upm_list_sorted` | "사용자 성능 분석 항목을 이름 오름차순으로 정렬해서 보여줘" | list+filter | sortFieldSets `name ASC` |

---

### Operation

| key | summary | intent | 비고 |
|---|---|---|---|
| `op_command` | "이 서버에서 df -h 명령어 실행해 줘" | action | `operation/command` |
| `op_ping` | "이 서버에 Ping을 날려서 응답 시간 확인해 줄래?" | action | `operation/ping` |
| `op_traceroute` | "목적지 서버까지 네트워크 경로 추적해 줄래?" | action | `operation/traceroute` |
| `op_oid` | "SNMP OID 값을 직접 조회해서 검증해 줄래?" | action | `operation/oid` |
| `op_start_all` | "중지된 에이전트를 전체 일괄 시작해 줄래?" | action | `operation/start-all-agents` |

---

## 사용법 (5줄)

새 endpoint examples 작성 시:
1. **카테고리 매칭**: 위 서브도메인 표에서 endpoint 성격과 가장 가까운 카테고리를 찾는다.
2. **시나리오 3-5개 sampling**: 같은 카테고리의 시나리오 key를 골라 실제 필드명·enum 값을 endpoint schema에 맞춰 치환한다.
3. **필드명 근거**: `x-tag-vocabulary`, 응답 example, gridColumns example의 `field` 값을 반드시 사용한다 — 추측 금지.
4. **summary 원칙**: 위 표의 summary를 그대로 쓰거나 동의어로 변형한다. "조회해 줘" / "알려줘" / "뽑아줘" / "보여줘" 등 자연어 동사를 돌려 쓴다. **"조회", "확인" 단독 사용 절대 금지**.
5. **복붙 함정 회피**: list-filter 40개 endpoint에 `default_page/page_2/sort_asc/sort_desc/with_filter` 5-key를 그대로 복붙하지 말고, 해당 도메인 어휘를 활용한 **도메인 특화 필터 시나리오** 최소 2개(예: osType, monitorType, patchStatus 기반)를 반드시 포함한다.

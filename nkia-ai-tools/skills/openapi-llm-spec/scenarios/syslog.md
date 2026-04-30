# Syslog 도메인 시나리오 카탈로그

## 도메인 정체성

**Syslog — RFC 3164/5424 메시지 수신 포트 사전관리 + 정식관리 + Configuration**

- 시스템 로그(Syslog)를 수신하는 **포트**를 관리하는 도메인. 실제 syslog 메시지 데이터(host·severity·message body)를 직접 조회하는 API는 이 도메인에 없음 — 포트 설정(등록·수정·삭제)과 포트별 severity 매핑 규칙 관리가 핵심.
- 2단계 등록 흐름: **사전 관리대상(pre)** 먼저 등록 → **정식 관리대상(production)** 으로 승격.
- severity 매핑: RFC syslog 레벨(emergency/alert/critical/error/warn/notice/info/debug) → 내부 이벤트 등급(0=NO_RECEIVE·1=DEBUG·2=INFO·3=WARN·4=ERROR·5=FATAL).

**Endpoints (15):**

| # | Path | operationId | 태그 | 사이드이펙트 |
|---|------|-------------|------|-------------|
| 1 | POST /api/syslog/v1/pre/register | preRegisterSyslogPort | PreManaged | write |
| 2 | POST /api/syslog/v1/pre/list | getPreSyslogPortList | PreManaged | read |
| 3 | POST /api/syslog/v1/pre/error/count | getPreSyslogPortErrorCount | PreManaged | read |
| 4 | GET /api/syslog/v1/pre/detail/{resourceId} | getPreSyslogPortDetail | PreManaged | read |
| 5 | POST /api/syslog/v1/pre/update | preUpdateSyslogPort | PreManaged | write |
| 6 | POST /api/syslog/v1/pre/delete | preDeleteSyslogPort | PreManaged | delete |
| 7 | POST /api/syslog/v1/pre/list-excel | exportPreSyslogPortListToExcel | PreManaged | download |
| 8 | POST /api/syslog/v1/register | registerSyslogPort | Production | write |
| 9 | GET /api/syslog/v1/custom-monitor/count | countSyslogPort | Production | read |
| 10 | POST /api/syslog/v1/list | getSyslogPortList | Production | read |
| 11 | GET /api/syslog/v1/detail/{resourceId} | getSyslogPortDetail | Production | read |
| 12 | POST /api/syslog/v1/update | updateSyslogPort | Production | write |
| 13 | POST /api/syslog/v1/delete | deleteSyslogPort | Production | delete |
| 14 | POST /api/syslog/v1/list-excel | exportSyslogPortListToExcel | Production | download |
| 15 | GET /api/syslog/v1/configuration/{resourceId}/basic-info | getSyslogBasicInfo | Configuration | read |

---

## 도메인 어휘

| 용어 | 설명 |
|------|------|
| **resourceId** | MongoDB ObjectId 형식 포트 식별자 (예: `671ed85384e88114ed17221b`) |
| **port** | 수신 포트 번호 (1–65535). 표준: 514(UDP), 601(TCP) |
| **protocol** | UDP / TCP (대소문자 혼용 허용) |
| **encodingType** | UTF-8 / EUC-KR / UNICODE / CUSTOM |
| **customEncoding** | encodingType=CUSTOM 일 때 사용자 지정 charset (예: ISO-6824) |
| **enableUnregisteredReceive** | 미등록 장비 발신 syslog 수신 허용 여부 (boolean) |
| **syslogEventSeverity** | 8개 RFC 레벨(emergency·alert·critical·error·warn·notice·info·debug) → 내부 등급 매핑 객체 |
| **severity 등급** | 0=NO_RECEIVE, 1=DEBUG, 2=INFO, 3=WARN, 4=ERROR, 5=FATAL |
| **emergency** | RFC EMERG(0) — 시스템 사용 불가 수준 |
| **alert** | RFC ALERT(1) — 즉시 조치 필요 |
| **critical** | RFC CRIT(2) — 심각한 오류 조건 |
| **error** | RFC ERR(3) — 일반 오류 |
| **warn** | RFC WARNING(4) — 경고 |
| **notice** | RFC NOTICE(5) — 정상이나 주목 필요 |
| **facility** | RFC syslog facility 필드 (kern/user/mail/daemon/auth 등). 포트 설정 레벨에서는 직접 노출 안 됨 |
| **Pre(사전 관리대상)** | 정식 등록 전 사전 준비 단계 포트. `/api/syslog/v1/pre/*` |
| **Production(정식 관리대상)** | 실제 수신 활성화된 포트. `/api/syslog/v1/*` (pre 제외) |
| **licenseErrorCount** | 라이센스 초과로 수신 불가 상태인 포트 수 |
| **AP** | 수신 에이전트 프로세스 (Aggregation Point). 포트와 1:1 연결 |
| **Cisco syslog** | 독자 포맷 (priority value 포함). 포트 514 UDP, 종종 CUSTOM encoding 필요 |

---

## 시나리오 카탈로그

### Pre-Management (사전 관리대상 등록·조회·수정·삭제)

| scenario_id | 자연어 질의 예시 | 패턴 | 주요 endpoint |
|-------------|----------------|------|---------------|
| `pre_register_udp514` | "UDP 514 포트를 기본 설정으로 사전 등록해 줘" | create | preRegisterSyslogPort |
| `pre_register_tcp601` | "TCP 601 포트를 EUC-KR 인코딩으로 사전 등록해 줘" | create | preRegisterSyslogPort |
| `pre_register_cisco_custom` | "Cisco 장비용 포트 516번을 CUSTOM 인코딩(ISO-6824)으로 사전 등록해 줘" | create | preRegisterSyslogPort |
| `pre_register_no_unregistered` | "미등록 장비 수신 차단 설정으로 UDP 515 포트를 사전 등록해 줘" | create | preRegisterSyslogPort |
| `pre_list_all` | "사전 관리대상 Syslog 포트 목록 전체를 조회해 줘" | list | getPreSyslogPortList |
| `pre_list_page2` | "사전 관리 포트 목록 2페이지 10개씩 조회해 줘" | list+page | getPreSyslogPortList |
| `pre_list_sort_port_asc` | "사전 관리대상 포트를 포트 번호 오름차순으로 정렬해서 보여줘" | list+sort | getPreSyslogPortList |
| `pre_error_count` | "라이센스 초과로 에러 상태인 사전 관리 포트 수를 확인해 줘" | read | getPreSyslogPortErrorCount |
| `pre_detail` | "사전 관리대상 포트 671ed85384e88114ed17221b 의 상세 설정을 조회해 줘" | detail | getPreSyslogPortDetail |
| `pre_detail_severity_check` | "사전 등록 포트의 syslog 레벨별 이벤트 등급 설정을 확인하고 싶어" | detail | getPreSyslogPortDetail |
| `pre_update_protocol` | "사전 관리 포트 514의 프로토콜을 TCP로 변경해 줘" | update | preUpdateSyslogPort |
| `pre_update_debug_noreceive` | "특정 포트의 DEBUG 레벨 이벤트 등급을 NO_RECEIVE(0)로 변경해 줘" | update | preUpdateSyslogPort |
| `pre_update_encoding` | "사전 관리 포트의 인코딩을 EUC-KR로 바꿔줘" | update | preUpdateSyslogPort |
| `pre_delete_single` | "사전 관리대상 포트 1개를 삭제해 줘" | delete | preDeleteSyslogPort |
| `pre_delete_bulk` | "미사용 사전 관리 포트 여러 개를 한꺼번에 삭제해 줘" | delete(bulk) | preDeleteSyslogPort |
| `pre_excel_all` | "사전 관리대상 포트 목록 전체를 엑셀로 다운로드해 줘" | export | exportPreSyslogPortListToExcel |

---

### Production Port Management (정식 관리대상 등록·조회·수정·삭제)

| scenario_id | 자연어 질의 예시 | 패턴 | 주요 endpoint |
|-------------|----------------|------|---------------|
| `prod_register_from_pre` | "사전 등록된 UDP 514 포트를 정식 관리대상으로 승격해 줘" | create | registerSyslogPort |
| `prod_register_bulk` | "여러 사전 등록 포트를 한꺼번에 정식 등록해 줘" | create(bulk) | registerSyslogPort |
| `prod_count` | "현재 정식 등록된 Syslog 포트 전체 개수를 알려줘" | read | countSyslogPort |
| `prod_list_all` | "정식 관리대상 Syslog 포트 목록 전체를 조회해 줘" | list | getSyslogPortList |
| `prod_list_sort_ctime_desc` | "정식 관리 포트를 등록일 기준 내림차순으로 보여줘" | list+sort | getSyslogPortList |
| `prod_detail` | "정식 등록 포트 671ed85384e88114ed17221b 의 상세 설정을 조회해 줘" | detail | getSyslogPortDetail |
| `prod_detail_severity` | "정식 관리 포트의 syslog 레벨별 이벤트 심각도 매핑을 확인해 줘" | detail | getSyslogPortDetail |
| `prod_detail_unregistered` | "미등록 장비 수신 허용 상태인 포트의 상세 정보를 열람해 줘" | detail | getSyslogPortDetail |
| `prod_update_name_desc` | "정식 관리 포트의 이름과 설명을 변경해 줘" | update | updateSyslogPort |
| `prod_update_protocol_tcp` | "정식 관리 포트 프로토콜을 TCP로 변경해 줘 (Receiver 재시작 포함)" | update | updateSyslogPort |
| `prod_update_disable_unregistered` | "특정 포트의 미등록 장비 수신을 비활성화해 줘" | update | updateSyslogPort |
| `prod_delete_single` | "정식 관리대상 포트 1개를 삭제해 줘" | delete | deleteSyslogPort |
| `prod_delete_bulk` | "더 이상 사용하지 않는 정식 관리 포트 여러 개를 삭제해 줘" | delete(bulk) | deleteSyslogPort |
| `prod_excel_all` | "정식 관리대상 포트 목록 전체를 엑셀로 다운로드해 줘" | export | exportSyslogPortListToExcel |
| `prod_excel_columns` | "포트 번호와 가용성 상태만 포함하여 정식 관리 포트 목록을 엑셀로 다운로드해 줘" | export+columns | exportSyslogPortListToExcel |

---

### Configuration (기본 정보 조회)

| scenario_id | 자연어 질의 예시 | 패턴 | 주요 endpoint |
|-------------|----------------|------|---------------|
| `config_basic_info` | "Syslog 포트의 이름·포트번호·프로토콜 기본 설정 정보를 조회해 줘" | detail | getSyslogBasicInfo |
| `config_basic_info_ap` | "AP가 연결된 시스로그 포트의 Configuration 화면 기본 정보를 확인해 줘" | detail | getSyslogBasicInfo |

---

### Severity 매핑 중심 시나리오 (audit 결함 보완 — ERROR/CRITICAL 시나리오 강화)

> audit 지적: severity mapping 예시 30+ 중복(동일 5-key 복붙), ERROR query 시나리오 부재.
> 아래 시나리오는 severity 등급 설정의 의미적 변형을 커버하여 examples dedup sweep 시 활용.

| scenario_id | 자연어 질의 예시 | 패턴 | 비고 |
|-------------|----------------|------|------|
| `severity_error_only` | "ERROR 이상(error·critical·alert·emergency)만 이벤트로 받고 나머지는 수신 안 하도록 포트 등록해 줘" | create | emergency=5,alert=5,critical=5,error=4, 나머지=0 |
| `severity_all_fatal` | "모든 syslog 레벨을 FATAL(5)로 매핑해서 포트를 사전 등록해 줘" | create | 8개 필드 전부 5 |
| `severity_update_warn_up` | "현재 포트에서 WARN 레벨 이벤트 등급을 ERROR(4)로 올려줘" | update | warn: 3→4 |
| `severity_update_info_noreceive` | "INFO 이하(info·debug) 레벨을 NO_RECEIVE로 변경해 줘" | update | info=0, debug=0 |
| `severity_cisco_mapping` | "Cisco 장비 syslog를 수신하는 포트의 critical 이벤트 등급을 FATAL(5)로 설정해 줘" | update | Cisco 포트 + critical=5 |
| `severity_detail_verify` | "등록된 포트의 emergency·alert 레벨이 FATAL(5)로 설정되어 있는지 확인해 줘" | detail | syslogEventSeverity 검증 |

---

## 사용법

이 카탈로그는 `openapi-llm-spec` 스킬 Phase 0.5 (i18n+vocab 합성) 및 examples quality sweep 에서 활용됩니다.

- **examples dedup sweep**: 30+ 중복 severity 매핑 예시를 위 severity 시나리오 변형으로 교체할 때 scenario_id 를 참조.
- **LLM tool 테스트**: 각 행의 자연어 질의를 tool-calling 테스트 입력으로 직접 사용 가능.
- **chain-call 시나리오**: `prod_detail` / `prod_update_*` 는 `getSyslogPortList` → `getSyslogPortDetail` / `updateSyslogPort` 2-hop chain. `resourceId` 는 `x-semantic-types.syslog_resource_id` 로 연결.
- **audit 결함 대응**:
  - severity 중복 → severity 시나리오 6개로 변형 커버
  - ERROR query 부재 → `severity_error_only` / `severity_update_warn_up` 시나리오로 보완
  - 포트 설정 위주 → prod_detail / config_basic_info 로 Configuration 화면 시나리오 포함

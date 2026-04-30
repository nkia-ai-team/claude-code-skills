# NMS 시나리오 카탈로그

## 도메인 정체성
**Network Management System (NMS)** — Cisco / Juniper / HP / Huawei 등 이기종 네트워크 장비(스위치·라우터·방화벽·로드밸런서)의 등록·상태·성능·설정 통합 관제. SNMP 폴링 기반 인터페이스 트래픽·CPU·메모리 측정, ARP/MAC/라우팅/TCP 상태 테이블 수집, Trap 수신, MIB 관리, AutoMap 토폴로지, SLB 가상서버 현황, 커스텀 SNMP OID 및 스크립트 확장 수집을 제공한다.

---

## 도메인 어휘

| 용어 | 설명 |
|------|------|
| 장비(Resource) | 관제 대상 네트워크 노드; resourceId(예: `RES_NMS_0001`)로 식별 |
| 인터페이스(Interface) | 물리·논리 포트; interfaceKey(ifIndex 기반)로 식별 |
| ifDescr | 인터페이스 설명(예: `GigabitEthernet0/0`) |
| ifAdminStatus | 관리자가 설정한 포트 활성화 상태 (up/down) |
| ifOperStatus | 실제 운영 상태 (up/down) |
| VLAN | 논리 네트워크 분리 단위; 인터페이스별 VLAN ID 할당 |
| duplex | 포트 이중화 모드 (full/half/auto) |
| speed | 포트 전송 속도 (예: 1000 Mbps, 10G) |
| MTU | 최대 전송 단위 (바이트); 기본값 1500 |
| SNMP OID | SNMP 관리 정보 식별자(점으로 구분된 수열); 장비 모델·측정값 식별에 사용 |
| sysObjectId | SNMP sysObjectId — 장비 모델 고유 OID (예: `1.3.6.1.4.1.9.1.1745`) |
| sysName | SNMP sysName — 장비 호스트명 |
| Trap | 장비가 이벤트 발생 시 자발적으로 전송하는 SNMP 알림 |
| MIB | 관리 정보 베이스 — SNMP OID 정의 파일 (.my/.mib) |
| ARP 테이블 | IP-MAC 주소 매핑 테이블 |
| MAC 테이블 | 포트별 학습된 MAC 주소 포워딩 테이블 |
| 라우팅 테이블 | 목적지 네트워크별 넥스트홉 경로 정보 |
| TCP 연결 | 장비에서 수집한 현재 TCP 세션 목록 |
| SLB | Server Load Balancer — 가상 서버(VIP)·풀·멤버 3계층 구조 |
| AutoMap | LLDP/CDP 기반 자동 위상도(토폴로지) 생성 기능 |
| 임시 장비(Pre) | 정식 등록 전 검증 단계의 장비 항목 |
| availabilityStatus | 장비 가용성 상태 (UP/DOWN/UNKNOWN) |
| cpuUsage | CPU 사용률 (%) |
| memoryUsage | 메모리 사용률 (%) |

---

## 시나리오 카탈로그

### Interface / Port

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `down_interfaces` | DOWN 상태 인터페이스 목록 조회 (ifOperStatus=down 필터) | list+filter | `POST /api/nms/v1/interface/list` |
| `high_traffic_ports_top5` | 트래픽 가장 많은 포트 Top 5 (최근 1시간) | list+sort+timeFilter | `POST /api/nms/v1/interface/top5` |
| `vlan_specific_ports` | 특정 VLAN 소속 인터페이스 목록 조회 | list+filter | `POST /api/nms/v1/interface/list` |
| `duplex_half_ports` | half-duplex 설정 포트 조회 (성능 저하 원인 파악) | list+filter | `POST /api/nms/v1/interface/list` |
| `speed_mismatch_ports` | 1G 미만 저속 포트 목록 조회 | list+filter | `POST /api/nms/v1/interface/list` |
| `mtu_nonstandard_ports` | MTU 1500 이외 설정 포트 조회 | list+filter | `POST /api/nms/v1/interface/list` |
| `interface_detail` | 특정 장비의 특정 포트 상세 정보 조회 | detail | `POST /api/nms/v1/interface/detail/{resourceId}/{interfaceKey}` |
| `interface_count_by_device` | 장비별 인터페이스 개수 조회 | count | `POST /api/nms/v1/interface/count/{resourceId}` |
| `interface_status_list` | 전체 인터페이스 상태 현황 목록 (Status 탭) | list | `POST /api/nms/v1/status/interface/list` |
| `interface_configuration` | 특정 장비 인터페이스 설정 구성 조회 | detail | `POST /api/nms/v1/interface/interface/configuration/{resourceId}` |
| `interface_excel_export` | 특정 장비 인터페이스 목록 엑셀 다운로드 | export | `POST /api/nms/v1/interface/{resourceId}/list-excel` |

---

### Device (Switch / Router)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `device_list_all` | 전체 장비 목록 조회 (이름·IP·상태 포함) | list | `POST /api/nms/v1/list` |
| `device_down_status` | 현재 DOWN 상태 장비 목록 조회 | list+filter | `POST /api/nms/v1/status/list` |
| `device_system_info` | 특정 장비 시스템 정보 조회 (sysName·sysUptime) | detail | `POST /api/nms/v1/system/{resourceId}` |
| `device_status_summary` | 특정 장비 가용성·CPU·메모리 종합 상태 조회 | detail | `POST /api/nms/v1/system/status/{resourceId}` |
| `device_basic_info` | 특정 장비 기본 정보 조회 (IP·sysDescr·vendor) | detail | `POST /api/nms/v1/configuration/{resourceId}/basic-info` |
| `device_type_config` | 장비 유형별 설정 상세 조회 (router/switch/firewall) | detail | `POST /api/nms/v1/configuration/{resourceId}/{resourceType}` |
| `device_resource_types` | 등록 가능한 장비 유형 코드 목록 조회 | list | `POST /api/nms/v1/configuration/resource-types` |
| `device_config_history_diff` | 설정 변경 이력 두 건 비교 (변경 전후 diff) | detail+compare | `POST /api/nms/v1/configuration/histories/compare-two` |
| `device_config_history_count` | 특정 장비 설정 변경 이력 건수 조회 | count | `POST /api/nms/v1/configuration/histories/count` |
| `pre_device_list` | 임시 등록(Pre) 장비 목록 조회 | list | `POST /api/nms/v1/pre/list` |
| `pre_device_error_count` | 임시 장비 중 등록 검증 실패 건수 조회 | count | `POST /api/nms/v1/pre/error/count` |
| `device_add` | 신규 장비 등록 (IP·SNMP 커뮤니티·장비 유형 지정) | action | `POST /api/nms/v1/addResource` |
| `device_delete` | 장비 삭제 (resourceId 지정) | action | `POST /api/nms/v1/deleteResource/{resourceId}` |
| `device_csv_bulk_register` | CSV 파일로 장비 일괄 등록 결과 저장 | action | `POST /api/nms/v1/csv/register/save-csv-upload-result` |
| `device_csv_template_download` | 장비 일괄 등록용 CSV 템플릿 다운로드 | export | `POST /api/nms/v1/csv/register/download-csv-template` |

---

### SNMP Operation

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `snmp_reachability_check` | 특정 장비 SNMP 접속 가능 여부 확인 | detail | `POST /api/nms/v1/snmp/status` |
| `snmp_identifier_list` | 등록된 sysObjectId(장비 모델 식별 OID) 목록 조회 | list | `POST /api/nms/v1/identifier/list` |
| `snmp_identifier_detail` | 특정 sysObjectId 상세 정보 조회 | detail | `POST /api/nms/v1/identifier/{systemObjectId}` |
| `snmp_identifier_add` | 신규 장비 모델 OID 등록 | action | `POST /api/nms/v1/identifier/add` |
| `snmp_identifier_update` | 장비 모델 OID 정보 수정 | action | `POST /api/nms/v1/identifier/update` |
| `snmp_identifier_delete` | 장비 모델 OID 삭제 | action | `POST /api/nms/v1/identifier/delete/{systemObjectId}` |
| `mib_list` | 등록된 MIB 파일 목록 조회 | list | `POST /api/nms/v1/mib/list` |
| `mib_upload` | 신규 MIB 파일 업로드 | action | `POST /api/nms/v1/mib/save` |
| `mib_update` | 기존 MIB 파일 내용 업데이트 | action | `POST /api/nms/v1/mib/update` |
| `mib_delete` | MIB 파일 삭제 (id 지정) | action | `POST /api/nms/v1/mib/delete/{id}` |
| `custom_snmpoid_list` | 커스텀 SNMP OID 수집 장비 목록 조회 | list | `POST /api/nms/v1/custom/snmpoid/list` |
| `custom_snmpoid_template_list` | SNMP OID 수집 템플릿 목록 조회 | list | `POST /api/nms/v1/custom/snmpoid/template/list` |
| `custom_snmpoid_latest_value` | 커스텀 OID 수집 장비 최신 측정값 조회 | detail | `POST /api/nms/v1/custom/snmpoid/measurement/latest/{resourceId}` |

---

### Topology / Link (AutoMap)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `automap_link_interface_list` | AutoMap 링크 인터페이스 목록 조회 (토폴로지 연결 포트 전체) | list | `POST /api/nms/automap/link/interface-list` |
| `automap_node_interface_list` | 특정 장비(노드)의 AutoMap 인터페이스 목록 조회 | list | `POST /api/nms/automap/node/{resourceId}/interface-list` |
| `automap_link_src_dst` | 특정 장비 인터페이스의 AutoMap 소스-목적지 연결 조회 | detail | `POST /api/nms/automap/link/interface/{resourceId}/source-destination` |
| `automap_link_excel_export` | AutoMap 링크 인터페이스 목록 엑셀 다운로드 | export | `POST /api/nms/automap/link/interface-list/excel` |
| `autolink_avro_send` | AutoLink AVRO 이벤트 전송 (토폴로지 갱신 트리거) | action | `POST /api/nms/v1/autoLink/send/avro` |

---

### Trap / Alert

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `trap_device_list` | Trap 수신 장비 목록 조회 (버전·IP 포함) | list | `POST /api/nms/trap/v1/list` |
| `trap_device_detail` | 특정 장비 Trap 설정 상세 조회 | detail | `POST /api/nms/trap/v1/detail/{resourceId}` |
| `trap_device_register` | 신규 장비 Trap 수신 등록 | action | `POST /api/nms/trap/v1/register` |
| `trap_device_update` | Trap 수신 장비 설정 변경 | action | `POST /api/nms/trap/v1/update` |
| `trap_device_delete` | Trap 장비 삭제 | action | `POST /api/nms/trap/v1/delete` |
| `trap_pre_list` | 임시 Trap 장비 목록 조회 | list | `POST /api/nms/trap/v1/pre/list` |
| `trap_custom_monitor_count` | 커스텀 Trap 모니터 건수 조회 | count | `POST /api/nms/trap/v1/custom-monitor/count` |

---

### Measurement (CPU / Memory / Traffic / Metric)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `cpu_usage_list` | 전체 장비 CPU 사용률 이력 목록 (시간 범위 지정) | list+timeFilter | `POST /api/nms/v1/cpu/list` |
| `memory_usage_list` | 전체 장비 메모리 사용률 이력 목록 (시간 범위 지정) | list+timeFilter | `POST /api/nms/v1/memory/list` |
| `metric_timeseries_single` | 단일 메트릭(cpu/memory/traffic 등) 시계열 조회 | chart+timeFilter | `POST /api/nms/v1/metric/data/single/time-period` |
| `measurement_definitions_all` | 전체 측정 항목 정의 목록 조회 (수집 메트릭 종류 확인) | list | `POST /api/nms/v1/measurement/definitions/all` |
| `measurement_definition_by_id` | 특정 정의 ID 측정 항목 상세 조회 | detail | `POST /api/nms/v1/measurement/definitions/id/{definitionId}` |
| `measurement_definition_by_type` | 장비 유형·측정 유형별 측정 항목 목록 조회 | list+filter | `POST /api/nms/v1/measurement/definitions/resourcetype/{resourceType}/{measurementType}` |
| `slb_sankey_chart` | SLB VIP→풀→멤버 트래픽 흐름 Sankey 차트 (시간 범위) | chart+timeFilter | `POST /api/nms/v1/slb/top-chart/sankey` |
| `custom_script_latest_value` | 커스텀 스크립트 수집 장비 최신 측정값 조회 | detail | `POST /api/nms/v1/custom/script/measurement/latest/{resourceId}` |
| `custom_snmpoid_traits_history` | 커스텀 OID 수집 이력 추이 조회 | list+timeFilter | `POST /api/nms/v1/custom/snmpoid/traits-history` |
| `nms_collect_now` | NMS 폴링 즉시 실행 (스케줄 대기 없이 강제 수집) | action | `POST /api/nms/settings/execution-now` |

---

### SLB (Server Load Balancer)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `slb_support_check` | 특정 장비의 SLB 기능 지원 여부 확인 | detail | `POST /api/nms/v1/slb/support/{resourceId}` |
| `slb_list_by_type` | 장비별 SLB 항목 목록 조회 (virtualServer/pool/member) | list | `POST /api/nms/v1/slb/list/{serverType}/{resourceId}` |
| `slb_item_detail` | SLB 특정 항목 카드 상세 조회 | detail | `POST /api/nms/v1/slb/card/detail/{serverType}/{resourceId}` |
| `slb_mapping_list` | SLB VIP-풀-멤버 매핑 관계 목록 조회 | list | `POST /api/nms/v1/slb/list/mapping/{resourceId}` |
| `slb_top_chart_by_type` | SLB 유형별 트래픽 Top 차트 조회 | chart+timeFilter | `POST /api/nms/v1/slb/top-chart/{serverType}/{resourceId}` |

---

### Status Table (ARP / MAC / Route / TCP)

| 시나리오 ID | 한국어 설명 | 패턴 | 대표 endpoint |
|-------------|------------|------|---------------|
| `arp_table_list` | 전체 ARP 테이블 조회 (IP-MAC 매핑) | list | `POST /api/nms/v1/status/arp/list` |
| `mac_table_list` | MAC 포워딩 테이블 조회 (포트별 학습 MAC) | list | `POST /api/nms/v1/status/mac/list` |
| `routing_table_list` | 라우팅 테이블 조회 (목적지·넥스트홉·메트릭) | list | `POST /api/nms/v1/status/route/list` |
| `tcp_connection_list` | 현재 TCP 연결 목록 조회 (장비별 소켓 상태) | list | `POST /api/nms/v1/status/tcp/list` |
| `status_item_count` | 특정 장비·유형(arp/mac/route/tcp) 항목 건수 조회 | count | `POST /api/nms/v1/status/{type}/count/{resourceId}` |

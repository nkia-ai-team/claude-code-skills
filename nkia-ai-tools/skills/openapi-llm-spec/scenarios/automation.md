# Automation 도메인 시나리오 카탈로그

> 도메인: `automation` | API prefix: `/api/domain-automation` + `/api/domain-tcm`
> 총 endpoint: 216 | i18n module: `auto` (tcm 공용)
> 산출물: `openapi/automation.openapi.json`

---

## 도메인 정체성

**작업 자동화 플랫폼** — 스크립트·스케줄·플랜 기반으로 IT 인프라 작업(패치 배포, 소프트웨어 수집, 설정 관리 등)을 자동화한다. 크게 두 하위 도메인으로 구성된다.

- **Automation (`/api/domain-automation`)**: 소프트웨어 인벤토리·EOS 정책·OSS 라이선스·스크립트·스케줄·구성 사전·연동정보(Credential)를 관리한다.
- **TCM — Task Control Manager (`/api/domain-tcm`)**: 작업 계획(Plan)·폴더·그룹·스케줄·변수·호스트 그룹·실행 제어(즉시 실행·일시중지·강제 종료·재실행)·실행 상태 모니터링을 담당한다.

---

## 도메인 어휘

| 용어 | 설명 |
|------|------|
| Plan (작업 계획) | 실행 대상·순서·스케줄을 포함한 자동화 작업 단위 |
| Folder | Plan 내 작업 묶음 단위; 사용자 정의 이름 부여 가능 |
| Task | Folder 하위의 개별 실행 항목 (스크립트 1개 실행) |
| Execution Object | Plan/Folder/Task 를 통칭하는 추상 개념 (`executionObjectType` 파라미터로 구분) |
| Schedule (스케줄 관리) | TCM 내 반복·일회성 실행 일정; Plan 에 연결 |
| Host Group (호스트 그룹) | 작업 대상 서버들을 논리적으로 묶은 그룹 |
| Group Metadata (그룹 메타데이터) | TCM 내 Task 를 분류하는 그룹 계층 구조 |
| Concurrent Rule (동시 실행 규칙) | 같은 Task 의 동시 실행 허용 수를 제어하는 규칙 |
| Task Order Rule (이벤트 규칙) | Task 간 순서·의존 관계를 정의하는 규칙 |
| Variable (변수) | 스크립트·Plan 에서 참조하는 키-값; Global/Instance/System 3 계층 |
| Credential (연동정보) | AWS/Azure/GCP/SSH 등 외부 시스템 접속 정보 |
| Software (소프트웨어) | 수집·배포 대상 패키지 목록 |
| EOS Policy (EOS 정책) | 지원 종료(End of Support) 소프트웨어 관리 정책 |
| OSS License | 오픈소스 라이선스 관리 항목 |
| Script (스크립트) | 소프트웨어 수집·배포에 사용하는 실행 스크립트 |
| Config Dictionary (구성 사전) | 설정 파일 템플릿·사용자 정의 객체 사전 |
| Manual Execution (수동 실행) | 스케줄 없이 온디맨드로 실행하는 정의 |
| Quota Assignment (자원 할당) | 동시 실행 자원(슬롯) 할당 규칙 |
| Execution Control | run-now / pause / resume / re-run / force-terminate 등 실행 상태 전환 |
| Target | 작업 실행 대상 단일 서버/인스턴스 |
| Collect History | 소프트웨어 배포·실행 수집 이력 |

---

## 시나리오 카탈로그

### Plan / Workflow

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `plan_create_backup_nightly` | "매일 새벽 2시에 전체 서버 백업 스크립트를 실행하는 작업 계획을 만들어줘" | save → register |
| `plan_create_patch_deploy` | "이번 주 금요일 22시에 보안 패치를 전체 운영 서버에 배포하는 계획을 등록해줘" | save → register |
| `plan_create_disaster_recovery` | "장애 발생 시 자동 복구 플로우를 단계별로 구성하는 계획을 만들어줘" | save |
| `plan_list_registered` | "현재 등록된 작업 계획 목록을 최신순으로 보여줘" | list-page-filter |
| `plan_detail` | "특정 백업 작업 계획의 폴더·태스크 구성을 트리 구조로 조회해줘" | get |
| `plan_validate` | "저장하기 전에 이 작업 계획이 유효한지 검사해줘" | validate |
| `plan_copy_as_new` | "기존 정기 패치 계획을 복사해서 새 이름으로 만들어줘" | new-name → save |
| `plan_unregister` | "다음 달까지 실행하지 않을 계획을 등록 해제해줘" | unregister |
| `plan_delete` | "완료된 분기 점검 계획을 삭제해줘" | delete |
| `plan_export_xml` | "작업 계획들을 XML 파일로 내보내 백업해줘" | export |
| `plan_import_xml` | "다른 환경에서 가져온 XML 계획 파일을 현재 시스템에 임포트해줘" | import |
| `plan_import_excel` | "엑셀 템플릿으로 작성한 작업 계획을 시스템에 등록해줘" | import-excel |
| `plan_clear_resources` | "여러 계획의 대상 서버·호스트 그룹 정보를 일괄 초기화해줘" | clear-target-resources-and-host-group |

### Schedule (TCM 스케줄 관리)

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `schedule_create_weekly` | "매주 월요일 오전 6시 정기 점검 스케줄을 생성해줘" | create |
| `schedule_create_monthly` | "매월 마지막 날 자정 정기 보고 스케줄을 등록해줘" | create |
| `schedule_list` | "등록된 스케줄 전체 목록을 조회해줘" | all |
| `schedule_detail` | "특정 정기 백업 스케줄의 상세 정보와 연결된 작업을 확인해줘" | detail |
| `schedule_copy` | "기존 야간 배포 스케줄을 복사해서 테스트 환경용으로 수정해줘" | copy → update |
| `schedule_update` | "현재 매주 금요일로 설정된 패치 스케줄을 매주 수요일로 변경해줘" | update |
| `schedule_delete` | "더 이상 사용하지 않는 구형 스케줄을 삭제해줘" | delete |
| `schedule_convert_date` | "월간 스케줄 설정이 실제로 어떤 날짜들로 계산되는지 확인해줘" | convert-schedule-date |
| `software_schedule_immediate` | "스케줄 대기 없이 소프트웨어 배포 및 수집을 지금 당장 실행해줘" | immediatley-deploy-collect |
| `software_schedule_create` | "매일 오전 3시 서버 패키지 수집 스케줄을 등록해줘" | insert |

### Execution Control (실행 제어)

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `exec_run_now` | "스케줄 무시하고 긴급 패치 작업을 지금 즉시 실행해줘" | run-now |
| `exec_run_by_task` | "특정 태스크 하나만 즉시 실행해줘" | execute/immediately/by-task |
| `exec_run_by_folder` | "폴더 단위로 하위 태스크 전체를 즉시 실행해줘" | execute/immediately/by-folder |
| `exec_manual_run_now` | "수동 실행 정의를 사용해서 온디맨드 작업을 바로 시작해줘" | manual-run-now |
| `exec_pause` | "현재 실행 중인 대규모 배포 작업을 잠시 중단해줘" | pause |
| `exec_resume` | "일시중지된 패치 작업을 다시 재개해줘" | resume |
| `exec_force_terminate` | "응답 없이 멈춘 작업을 강제로 종료해줘" | force-terminate |
| `exec_re_run` | "실패한 배포 작업을 다시 실행해줘" | re-run |
| `exec_mark_completed` | "수동 확인 완료된 작업을 완료 상태로 표시해줘" | mark-completed |
| `exec_confirm_user` | "사용자 확인 대기 중인 승인 요청 작업을 확인 처리해줘" | confirm-user |
| `exec_decommission` | "실행 큐에서 불필요한 계획을 폐기해줘" | decommission |
| `exec_result_reset` | "최신 실행 결과를 초기화해줘" | execution-result/latest/reset |
| `exec_result_recovery` | "손상된 최신 실행 결과 컬렉션을 복구해줘" | execution-result/latest/recovery |

### Execution Status (실행 상태 모니터링)

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `status_overview_today` | "오늘 실행 중인 작업 계획들의 전체 현황을 보여줘" | status/overview/{date}/list-page-filter |
| `status_summary_top` | "실행 현황 대시보드 상단 요약 지표를 조회해줘" | status/summary/top |
| `status_summary_by_worktype` | "작업 유형별 실행 건수 통계를 보여줘" | status/summary/count-by-work-type |
| `status_task_execution` | "현재 태스크 실행 상태 요약을 조회해줘" | status/summary/task-execution |
| `status_by_folder` | "폴더 기준으로 오늘 실행 대상 트리 현황을 보여줘" | status/by-folders |
| `status_target_result` | "특정 대상 서버의 최신 실행 결과를 확인해줘" | status/target/execution-result/get/{date} |
| `status_target_history` | "특정 서버의 지난 30일 실행 이력을 페이지로 조회해줘" | status/target/execution-result/history/list-page-filter/{date} |
| `status_target_logs` | "특정 서버의 실행 로그를 필터 조건으로 조회해줘" | status/target/logs/list-page-filter/{date} |
| `status_target_waiting` | "실행 대기 중인 서버 목록을 확인해줘" | status/target/waiting-infos/list-page-filter/{date} |
| `status_script_content` | "실행 중인 태스크의 스크립트 파일 내용을 조회해줘" | status/task-script/fetch-file-content |
| `status_execution_object` | "특정 Plan/Folder/Task 의 상세 실행 상태를 조회해줘" | status/{executionObjectType}/get/{date} |
| `status_delete_objects` | "완료된 실행 객체들을 타입별로 일괄 삭제해줘" | status/execution-object/delete |

### Credential (연동정보 — AWS/Azure/GCP/SSH)

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `credential_create_aws` | "AWS IAM 키를 사용해 운영 계정 연동정보를 등록해줘" | insert |
| `credential_create_ssh` | "리눅스 서버 SSH 연동정보를 등록해줘" | insert |
| `credential_list` | "등록된 모든 연동정보 목록을 조회해줘" | list-page-filter |
| `credential_detail` | "특정 Azure 연동정보 상세를 확인해줘" | detail |
| `credential_update` | "만료된 GCP 서비스 계정 키를 새 키로 업데이트해줘" | update |
| `credential_delete` | "더 이상 사용하지 않는 구 AWS 계정 연동정보를 삭제해줘" | delete |
| `credential_aws_regions` | "AWS 에서 지원하는 리전 목록을 조회해줘" | regions/list |

### Variable Management (변수 관리)

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `variable_global_create` | "모든 플랜에서 공통으로 사용할 DB 접속 호스트 변수를 등록해줘" | variable-management/global/insert |
| `variable_global_list` | "등록된 공통 변수 전체 목록을 조회해줘" | variable-management/global/list-page-filter |
| `variable_global_update` | "공통 변수 값을 새로운 스테이징 서버 주소로 수정해줘" | variable-management/global/update |
| `variable_global_delete` | "사용하지 않는 공통 변수를 삭제해줘" | variable-management/global/delete |
| `variable_instance_create` | "특정 폴더 전용 배포 경로 변수를 개별 변수로 등록해줘" | variable-management/instance/insert |
| `variable_instance_list` | "특정 태스크에 연결된 개별 변수 목록을 조회해줘" | variable-management/instance/list-page-filter |
| `variable_system_list` | "시스템이 제공하는 내장 변수 목록을 카테고리별로 조회해줘" | variable-management/system/list-page-filter |
| `variable_validate_script` | "스크립트에서 사용 중인 변수들이 올바르게 정의되어 있는지 검사해줘" | variable-validation/text |
| `variable_validate_list` | "여러 변수를 한 번에 유효성 검사해줘" | variable-validation/variables |

### Host Group / Group Metadata

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `hostgroup_create_prod` | "운영 서버 30대를 묶어 운영계 호스트 그룹을 생성해줘" | host-group/insert |
| `hostgroup_list` | "등록된 호스트 그룹 전체 목록을 조회해줘" | host-group/list-page-filter |
| `hostgroup_update` | "호스트 그룹에 서버를 추가·제거하여 구성을 수정해줘" | host-group/update |
| `hostgroup_delete` | "더 이상 사용하지 않는 테스트 서버 그룹을 삭제해줘" | host-group/delete |
| `group_metadata_create` | "태스크 분류를 위한 새 그룹 메타데이터를 생성해줘" | group-metadata/create |
| `group_metadata_sync` | "그룹 메타데이터 동기화 상태를 확인하고 업데이트해줘" | group-metadata/sync → syncUpdate |
| `group_metadata_task_list` | "특정 그룹에 속한 태스크 목록을 필터 조건으로 조회해줘" | group-metadata/task/list-page-filter |

### Software / EOS / OSS

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `software_list` | "수집된 소프트웨어 인벤토리 목록을 조회해줘" | software/list-page-filter |
| `software_eos_register` | "지원이 종료된 구버전 JDK 8에 대한 EOS 정책을 등록해줘" | software/eos/insert |
| `software_eos_list` | "현재 등록된 EOS 정책 목록을 조회해줘" | software/eos/list-page-filter |
| `software_eos_update` | "EOS 정책의 적용 대상 소프트웨어를 수정해줘" | software/eos/update |
| `software_oss_register` | "오픈소스 컴포넌트의 라이선스 정보를 OSS 목록에 등록해줘" | software/oss/insert |
| `software_oss_list` | "등록된 OSS 라이선스 목록을 조회해줘" | software/oss/list-page-filter |
| `software_script_register` | "패치 배포에 사용할 새 배포 스크립트를 등록해줘" | software/script/insert |
| `software_script_toggle_prohibited` | "보안 이슈가 있는 스크립트의 실행을 금지 상태로 변경해줘" | software/script/update-executionProhibited |
| `software_collect_history` | "최근 소프트웨어 배포 수집 이력을 조회해줘" | software/collect-history/deploy/list-page-filter |

### Config Dictionary (구성 사전)

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `config_dict_list` | "등록된 구성 사전 항목 목록을 조회해줘" | config-dictionary/list-page-filter |
| `config_dict_create_file` | "서버 설정 파일 템플릿을 구성 파일 사전에 등록해줘" | config-dictionary/configuration-file/insert |
| `config_dict_create_custom` | "사용자 정의 구성 객체를 사전에 추가해줘" | config-dictionary/custom-object/insert |
| `config_dict_export` | "구성 사전 항목들을 파일로 내보내 백업해줘" | config-dictionary/export |
| `config_dict_import` | "다른 환경에서 내보낸 구성 사전 파일을 현재 시스템에 임포트해줘" | config-dictionary/import |

### Manual Execution / Quota / Concurrent Rule

| scenario_id | 자연어 질의 예시 | 주요 endpoint 패턴 |
|-------------|----------------|--------------------|
| `manual_exec_create` | "승인 없이 언제든지 실행할 수 있는 긴급 패치 수동 실행 정의를 만들어줘" | manual-executions/create |
| `manual_exec_list` | "등록된 수동 실행 정의 목록을 조회해줘" | manual-executions/all |
| `quota_create` | "동시 실행 자원 슬롯을 팀별로 할당하는 규칙을 생성해줘" | quota-assignments/create |
| `concurrent_rule_create` | "같은 태스크가 동시에 3개 이상 실행되지 않도록 동시 실행 규칙을 만들어줘" | concurrent-execution-rule/create |
| `concurrent_rule_list` | "등록된 동시 실행 규칙 목록을 조회해줘" | concurrent-execution-rule/rules |
| `task_order_rule_update` | "태스크 A 완료 후 태스크 B가 실행되도록 이벤트 규칙을 설정해줘" | task-order-execution-rule/update |

---

## 사용법

이 카탈로그는 `openapi-llm-spec` 스킬의 **Phase 0 (시나리오 파악)** 에서 참조한다.

- `scenario_id` → `x-scenarios` 루트 vocabulary 의 키로 사용
- 자연어 질의 예시 → 해당 endpoint 의 `examples[].summary` 작성 시 참고
- 주요 endpoint 패턴 → chain-call `x-source-endpoint` 연결 흐름 설계 시 참고

**audit 결함 개선 포인트** (현재 2/5점):
1. `PLAN-0001` 4회 반복 → 위 카탈로그의 `plan_*` 시나리오 13개로 다양화
2. `p1/p2/p3` 메타라벨 → 각 시나리오의 자연어 질의 예시로 대체
3. 자동화 시나리오 부재 → 백업(`plan_create_backup_nightly`), 배포(`plan_create_patch_deploy`), 복구(`plan_create_disaster_recovery`), 긴급 실행(`exec_run_now`), 스케줄링(`schedule_create_weekly`) 강제 포함

**총 시나리오 수**: 43개

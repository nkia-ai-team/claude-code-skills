# TCM 시나리오 카탈로그

생성일: 2026-04-29
소스 분석: openapi/tcm.openapi.json (152 endpoint), i18n module=tcm, audit 1/5점

---

## 도메인 정체성

**TCM = Task & Change Management** — 작업/변경 요청/승인/실행 계획 도메인.
인프라 자동화 운영 플랫폼에서 반복·스케줄·이벤트 기반 작업을 정의·등록·실행·모니터링하고, 변경 계획(Plan)을 수립·등록·폐기하는 전 생명주기를 관장한다.

---

## 도메인 어휘

| 한국어 용어 | 영문 키 | 설명 |
|---|---|---|
| 실행 객체 | ExecutionObject | PLAN / FOLDER_BASIC / TASK_COMMAND 등 계층 단위 |
| 잡 / 작업 | Job / Task | 스크립트·명령을 실행하는 최소 단위 (TASK_COMMAND) |
| 폴더 | Folder | Task 를 묶는 논리 그룹 (FOLDER_BASIC) |
| 변경 계획 | Plan | Folder + Task 트리 구조의 실행 계획 묶음 |
| 시퀀스 ID | sequenceId | 실행 인스턴스 식별자 (예: SEQ_2025_04_28_001) |
| 스케줄 | Schedule | 작업 실행 주기 정의 (일별·주별·월별·이벤트 등) |
| 크레덴셜 / 호스트 그룹 | HostGroup | STATIC / SMART 타입 대상 서버 집합 |
| 변수 | Variable | 시스템(System) / 공통(Global) / 개별(Instance) 3계층 |
| 동시 실행 규칙 | ConcurrentExecutionRule | 동일 작업 동시 수행 허용 여부·개수 제한 |
| 이벤트(순서) 실행 규칙 | TaskOrderExecutionRule | 선행 작업 완료 후 후속 작업 트리거 |
| 수동 실행 정의 | ManualExecution | 사용자가 파라미터를 직접 지정해 즉시 실행하는 정의 |
| 자원 할당 | QuotaAssignment | 작업 실행 자원(쿼터) 배분 규칙 |
| 그룹 메타데이터 | GroupMetadata | 상위/하위 그룹 분류 메타 정보 |
| 실행 결과 | ExecutionResult | Target 단건 실행의 성공·실패·로그 기록 |
| 실행 대기 | WaitingInfo | 스케줄·이벤트 대기 중인 실행 인스턴스 정보 |

---

## 시나리오 카탈로그

총 46개 시나리오 / 9개 섹션

---

### 1. Execution Control (긴급 실행·제어)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `run_now_task` | 스케줄 무시하고 특정 작업(Task) 즉시 실행 | action |
| `run_now_plan` | 변경 계획 전체를 지금 즉시 실행 | action |
| `run_now_folder` | 특정 폴더 하위 작업을 즉시 일괄 실행 | action |
| `manual_run_now` | 수동 실행 정의를 사용해 즉시 실행 (파라미터 지정 포함) | action |
| `pause_running_task` | 실행 중인 작업을 일시정지 | action |
| `pause_running_plan` | 실행 중인 계획 전체를 일시정지 | action |
| `resume_paused_task` | 일시정지된 작업 재개 | action |
| `force_terminate_task` | 응답 없는 작업 강제 종료 | action |
| `force_terminate_folder` | 폴더 단위 강제 종료 (긴급 롤백 선행) | action |
| `re_run_failed_task` | 실패한 작업 재실행 | action |
| `mark_completed_task` | 수동으로 작업을 완료 상태로 마킹 | action |
| `confirm_user_wait` | 사용자 확인 대기 상태의 작업 확인 처리 | action |
| `decommission_plan` | 실행 큐에서 계획을 폐기 | action |
| `execute_immediately_by_folder` | 폴더 단위 즉시 실행 (스케줄 무시) | action |
| `execute_immediately_by_task` | Task 단위 즉시 실행 (스케줄 무시) | action |

---

### 2. Execution Status (실행 현황 조회)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `today_summary_top` | 오늘 작업 현황 + Top5 요약 (대시보드) | list |
| `today_count_by_work_type` | 오늘 작업 유형별 건수 조회 | list |
| `today_status_overview` | 오늘 폴더별 상태 개요 페이지 조회 | list+filter |
| `status_overview_by_date` | 특정 날짜 폴더별 상태 개요 조회 | list+filter |
| `target_execution_result_today` | 특정 Target 의 오늘 실행 결과 단건 조회 | get |
| `target_execution_result_by_date` | 특정 날짜 기준 Target 실행 결과 조회 | get |
| `target_execution_history_30d` | Target 실행 이력 30일 페이지 조회 | list+filter |
| `target_waiting_infos` | 실행 대기 중인 Target 목록 조회 (날짜 지정) | list+filter |
| `execution_object_detail_today` | ExecutionObject(TASK/FOLDER/PLAN) 상세 조회 (오늘) | get |
| `execution_object_detail_by_date` | ExecutionObject 상세 조회 (특정 날짜) | get |
| `folders_status_tree_today` | FolderTask 기준 Target 트리 조회 (오늘) | list |
| `folders_status_tree_by_date` | FolderTask 기준 Target 트리 조회 (날짜) | list |
| `task_script_file_content` | 실행 중 Task 스크립트 파일 내용 조회 | get |

---

### 3. Planning / Plan (작업 계획 수립·등록)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `plan_list_filtered` | 작업 계획 목록을 이름·태그 조건으로 필터 조회 | list+filter |
| `plan_get_tree` | 특정 Plan 을 트리 구조로 단건 조회 | get |
| `plan_create_empty` | 새 빈 작업 계획 신규 생성 | action |
| `plan_update` | 기존 작업 계획 수정 (이름·설명·태그 변경) | action |
| `plan_register` | 작업 계획(들)을 실행 등록 (registered=true) | action |
| `plan_unregister` | 등록된 계획 해제 | action |
| `plan_delete` | 작업 계획 삭제 | action |
| `plan_validate` | 등록 전 계획 유효성 검사 | action |
| `plan_export_xml` | 계획들을 XML 파일로 내보내기 | action |
| `plan_import_xml` | XML 파일에서 복수 계획 가져오기 | action |
| `plan_auto_name` | 신규 Plan 이름 자동 생성 | get |

---

### 4. Execution Object (서버·DB·네트워크 대상)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `execution_object_summaries_all` | 최상위 ExecutionObject 요약 목록 조회 (전체 트리) | list |
| `execution_object_summaries_children` | 특정 부모 하위의 ExecutionObject 요약 조회 | list |
| `execution_object_summaries_page_filter` | ExecutionObject 요약 페이지 필터 조회 | list+filter |
| `execution_result_reset` | 최신 실행 결과 컬렉션 초기화 | action |
| `execution_result_recovery` | 최신 실행 결과 컬렉션 복구 | action |

---

### 5. Schedule Management (스케줄 관리)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `schedule_list_filtered` | 스케줄 목록 이름·조건 페이지 필터 조회 | list+filter |
| `schedule_detail_with_tasks` | 스케줄 상세 (소속 작업 목록 포함) 조회 | get |
| `schedule_create` | 신규 스케줄 생성 | action |
| `schedule_update` | 스케줄 수정 | action |
| `schedule_copy` | 스케줄 복사 (이름 변경) | action |
| `schedule_delete` | 스케줄 삭제 | action |
| `schedule_date_convert` | 스케줄 유형 → 실제 날짜 목록 변환 | get |

---

### 6. Variable Management (변수 관리)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `global_variable_list_filtered` | 공통 변수 페이지 필터 조회 | list+filter |
| `global_variable_create` | 공통 변수 신규 생성 | action |
| `global_variable_update` | 공통 변수 수정 | action |
| `instance_variable_list_by_folder` | 특정 폴더/Task 에 종속된 개별 변수 조회 | list+filter |
| `instance_variable_create` | 개별 변수 신규 생성 (폴더/Task 종속) | action |
| `system_variable_list_by_category` | 시스템 변수 카테고리별 건수 + 목록 조회 | list+filter |
| `variable_validate_script` | 스크립트 텍스트 내 변수 유효성 검사 | action |
| `variable_validate_list` | 변수 목록 일괄 유효성 검사 | action |

---

### 7. Host Group (호스트 그룹)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `host_group_list_static` | STATIC 타입 호스트 그룹 목록 조회 | list+filter |
| `host_group_list_smart` | SMART(동적) 타입 호스트 그룹 목록 조회 | list+filter |
| `host_group_get` | 호스트 그룹 단건 상세 조회 | get |
| `host_group_create` | 호스트 그룹 신규 생성 | action |
| `host_group_update` | 호스트 그룹 수정 | action |
| `host_group_delete` | 호스트 그룹 삭제 | action |

---

### 8. Concurrent / Order Execution Rules (실행 규칙)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `concurrent_rule_list_filtered` | 동시 실행 규칙 목록 페이지 필터 조회 | list+filter |
| `concurrent_rule_create` | 동시 실행 규칙 신규 생성 | action |
| `concurrent_rule_update` | 동시 실행 규칙 수정 | action |
| `concurrent_rule_delete` | 동시 실행 규칙 삭제 | action |
| `order_rule_list_filtered` | 이벤트(순서) 실행 규칙 목록 조회 | list+filter |
| `order_rule_upsert` | 이벤트 실행 규칙 수정 (업서트) | action |
| `order_rule_delete` | 이벤트 실행 규칙 삭제 | action |

---

### 9. Group Metadata / Quota / Common Setting (메타데이터·자원 할당·공통 설정)

| ID | 한국어 설명 | 패턴 |
|---|---|---|
| `group_metadata_top_list` | 최상위 그룹 메타데이터 페이지 필터 조회 | list+filter |
| `group_metadata_sub_list` | 서브 그룹 메타데이터 페이지 필터 조회 | list+filter |
| `group_metadata_detail_with_tasks` | 그룹 + 소속 작업 목록 상세 조회 | get |
| `group_metadata_create` | 그룹 메타데이터 신규 생성 | action |
| `group_metadata_sync_status` | 그룹 메타데이터 동기화 상태 조회 | get |
| `quota_assignment_list` | 자원 할당 목록 페이지 필터 조회 | list+filter |
| `quota_assignment_create` | 자원 할당 신규 생성 | action |
| `quota_assignment_update` | 자원 할당 수정 | action |
| `common_setting_get` | TCM 공통 설정 조회 | get |
| `common_setting_update` | TCM 공통 설정 수정 | action |

---

## 사용법

새 sweep 에서 위 시나리오 ID 를 examples key 로 직접 활용한다.

### 우선순위 (audit 결함 기준)

1. **Execution Control** (run_now / force_terminate / decommission) — `trigger` / `action` 긴급 운영
2. **Execution Status** (summary_top / status_overview / target_execution_result) — `list` / `get` 현황 모니터링
3. **Planning** (plan_register / plan_validate / plan_create_empty) — 배포·변경 관리 흐름
4. **Schedule + Variable** — 반복 작업·파라미터 관리
5. **Rules + HostGroup + GroupMetadata** — 메타 설정 CRUD

### 패턴 매핑

| 패턴 | examples 구조 힌트 |
|---|---|
| `action` | `{sequenceId, folderId, taskId, executionObjectType}` 또는 ID 배열 |
| `list+filter` | `{pageNumber, pagePerSize, sortFieldSets, tagFilters, gridFilters, arguments}` |
| `get` | `{parameter: <id or timestamp or null>}` 또는 ID 단건 |
| `trigger` | run-now / manual-run-now 와 동일 action 구조 |

### 커버리지 목표

- Execution Control 15개 × 3 examples = 45
- Execution Status 13개 × 3 examples = 39
- Planning 11개 × 3 examples = 33
- 나머지 섹션 × 2~3 examples

예상 추가 examples 수: **133 → 0** (22개 no-examples endpoint 포함 전체 커버)

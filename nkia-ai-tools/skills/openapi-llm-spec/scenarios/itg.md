# ITG 도메인 시나리오 카탈로그

> 도메인: Integration (itg) — 외부 시스템 통합 / 배치잡 / 프로세스 엔진 / 표준코드 / SLM 평가 / 공통파일
> 엔드포인트 수: 35 (GET 1 + POST 34)
> audit 점수: 2/5 → 결함: 75% robotic examples, 통합/배치 시나리오 26.6%, 단어 4개짜리 examples summary

---

## 도메인 정체성

**Integration (ITG)** 은 Lucida 플랫폼에서 외부 시스템 연동·배치 자동화·프로세스 워크플로우를 담당하는 미들웨어 허브 도메인이다.
핵심 역할은 네 가지: ① ITAM·PMS 등 내부 시스템과의 데이터 동기화, ② Kafka 기반 배치잡 스케줄링·실행, ③ BPMN 프로세스 엔진(Flowable 계열) 워크플로우 관리, ④ 외부 API 게이트웨이(`{if_id}/{job_id}`)를 통한 범용 통합 라우팅.
표준코드(Standard Collection) API는 MongoDB 도큐먼트 CRUD를 공통 인터페이스로 추상화하며, SLM(Service Level Management) 평가·스냅샷은 KPI 측정 자동화를 지원한다.

**감사 결함 요약**
- examples summary 가 "기본 호출 예시", "C001 코드 삭제해 줘" 등 4단어 이하 메타라벨 수준
- 통합/배치 고유 어휘(인터페이스 ID, 잡 ID, 프로세스 인스턴스, SLI 평가 주기) 없이 generic 질의만 존재
- 실제 사용자 의도("어제 실패한 동기화 확인", "이번 달 SLI 점수 조회") 반영 부재

---

## 도메인 어휘

| 용어 | 설명 |
|---|---|
| 배치잡 (Batch Job) | 주기적·일회성 데이터 처리 작업. `batchJobId`(예: `syncItamMaster`)로 식별 |
| 인터페이스 ID (`if_id`) | 외부 통합 게이트웨이 라우팅 식별자 (예: `ERP_SYNC`, `CMDB_PULL`) |
| 잡 ID (`job_id`) | 인터페이스 내 세부 작업 식별자 |
| 데이터 동기화 (Data Sync) | ITAM 자산 정보를 외부 시스템과 실시간 또는 배치로 일치시키는 작업 |
| 표준 컬렉션 (Standard Collection) | MongoDB 도큐먼트 CRUD를 공통 인터페이스로 감싼 ITG 고유 추상화 |
| 프로세스 인스턴스 (Process Instance) | BPMN 워크플로우 실행 단위. `processInstanceId`로 추적 |
| 프로세스 정의 (Process Definition) | BPMN XML로 설계된 워크플로우 템플릿. `processDefinitionId`로 식별 |
| BPMN XML | 프로세스 디자이너에서 저장하는 워크플로우 설계 파일 |
| SLI (Service Level Indicator) | 서비스 수준 측정 지표. `sliId`로 식별, 가용성·응답속도 등 측정 |
| SLM (Service Level Management) | SLI 목표치 설정·평가·리포팅 관리 체계 |
| 스냅샷 (SLI Snapshot) | 특정 시점의 SLI 측정값을 영구 보존하는 작업 |
| 월간 점수 (Monthly Score) | 월별 SLI 달성률 집계 결과 |
| Gantt 일정 동기화 | PMS WBS에서 작업 간 의존성 변경 시 시작·종료일을 자동 재계산 |
| 작업 해제 (Work Release) | ITAM 승인 완료 후 후속 처리 트리거 |
| 전역 사이트 코드 (Global Site Code) | 멀티 사이트 환경에서 현재 운영 대상 사이트 식별자 |
| ITG 프로퍼티 (ITG Property) | `application.properties` 또는 DB에 저장된 ITG 런타임 설정값 |
| 공통 파일 (Comm File) | ITG 도메인이 관리하는 첨부파일 저장소 (업로드/다운로드/삭제) |
| 중복 필드 확인 (Dup Field Check) | 표준 컬렉션에 새 도큐먼트 삽입 전 unique 필드 중복 여부 사전 검증 |
| 티켓 멱등성 (Idempotency Ticket) | 동일 요청 재처리 방지용 마지막 요청 토큰 확인 |
| ITG 메시지 | 운영자에게 전달되는 알림·팝업·공지. 미확인 신규 메시지 여부 폴링 |
| 데이터 초기화 (Data Initialize) | 컬렉션 구조 정의·뷰 생성 등 초기 적재 작업 |

---

## 시나리오 카탈로그 (28개)

### Batch Job / Data Sync

| 시나리오 ID | 대표 자연어 질의 | 패턴 | 엔드포인트 |
|---|---|---|---|
| `batch_run_itam_master` | "ITAM 마스터 데이터 동기화 배치잡 지금 실행해줘" | action | `POST /batchjob/executeBatchJob` |
| `batch_run_named_job` | "syncItamMaster 배치잡 수동으로 돌려줘" | action | `POST /batchjob/executeBatchJob` |
| `batch_kafka_sync` | "Kafka 배치잡 동기화 상태 맞춰줘" | action | `POST /batchjob/syncBatchJobForKafka` |
| `itam_data_sync_trigger` | "ITAM 자산 데이터 외부 시스템이랑 동기화 실행해" | action | `POST /itam/executeDataSync` |
| `itam_work_release` | "승인 완료된 ITAM 작업 해제 처리해줘" | action | `POST /itam/executeWorkRelease` |
| `pms_gantt_recalc` | "WBS 일정 바뀌었는데 Gantt 시작·종료일 자동 재계산해줘" | action | `POST /pms/updateGanttDateSync` |

### Process Engine (BPMN)

| 시나리오 ID | 대표 자연어 질의 | 패턴 | 엔드포인트 |
|---|---|---|---|
| `process_start` | "myApprovalFlow 프로세스 새로 시작해줘" | action | `POST /process/engine/processRequest` |
| `process_complete_task` | "프로세스 인스턴스 P-2024-001의 현재 태스크 완료 처리해" | action | `POST /process/engine/processRequest` |
| `process_validate_bpmn` | "신규 BPMN 정의 배포 전에 유효성 검증해줘" | action | `POST /process/validate/processValidate` |
| `process_copy_definition` | "결재흐름 프로세스 정의를 테스트 환경용으로 복사해줘" | action | `POST /process/validate/processCopy` |
| `process_wait_test` | "프로세스 엔진 대기 타임아웃 테스트 요청 보내줘" | action | `POST /process/validate/processRequest4WaitTest` |
| `process_bpmn_update` | "프로세스 디자이너 BPMN XML 연관 정보 갱신해줘" | action | `POST /process/designer/updateProcessDesignerBpmnXmlRelationInfo` |
| `process_bpmn_delete` | "더 이상 안 쓰는 BPMN 연관 정보 삭제해줘" | action | `POST /process/designer/deleteProcessDesignerBpmnXmlRelationInfo` |

### Standard Collection (표준코드 CRUD)

| 시나리오 ID | 대표 자연어 질의 | 패턴 | 엔드포인트 |
|---|---|---|---|
| `std_list_paged` | "ITG 표준코드 목록을 페이지별로 조회해줘 (총 개수 포함)" | list+page | `POST /standard/selectDefaultListWithCount` |
| `std_list_simple` | "운영 상태 코드 전체 목록 가져와줘 (페이징 없이)" | list | `POST /standard/selectDefaultList` |
| `std_insert` | "표준 컬렉션에 새 코드 도큐먼트 등록해줘" | action | `POST /standard/insertDefault` |
| `std_update` | "기존 표준코드 도큐먼트 내용 수정해줘" | action | `POST /standard/updateDefault` |
| `std_delete` | "더 이상 사용하지 않는 표준코드 도큐먼트 삭제해" | action | `POST /standard/deleteDefault` |
| `std_bulk_execute` | "표준 컬렉션 insert·update·delete 여러 건 한 번에 처리해줘" | action | `POST /standard/executeMultiple` |
| `std_excel_download` | "표준코드 목록 엑셀 파일로 내려받아줘" | action | `POST /standard/commExcelDownLoad` |
| `std_dup_check` | "새 코드 추가 전에 코드명 중복 여부 확인해줘" | lookup | `POST /common/base/chkDuplFld` |

### SLM Evaluation / SLI Snapshot

| 시나리오 ID | 대표 자연어 질의 | 패턴 | 엔드포인트 |
|---|---|---|---|
| `slm_eval_list_create` | "이번 분기 SLM 평가 목록 생성해줘" | action | `POST /slm/evaluation/createSlmEvaluationList` |
| `slm_sli_execute` | "SLI-001 평가 지금 당장 실행해줘" | action | `POST /slm/evaluation/executeSliEvaluation` |
| `slm_monthly_score` | "SLI-003의 이번 달 서비스 수준 점수 조회해줘" | lookup | `POST /slm/evaluation/selectMonthlyScore` |
| `slm_snapshot_run` | "현재 SLI 측정값 스냅샷 찍어서 저장해줘" | action | `POST /slm/snapshot/executeSliSnapshot` |

### External API Gateway

| 시나리오 ID | 대표 자연어 질의 | 패턴 | 엔드포인트 |
|---|---|---|---|
| `ext_api_post_route` | "ERP_SYNC 인터페이스의 DAILY_JOB 작업 POST로 호출해줘" | action | `POST /{if_id}/{job_id}` |
| `ext_api_get_route` | "CMDB_PULL 인터페이스 STATUS_CHECK 결과 조회해줘" | lookup | `GET /{if_id}/{job_id}` |
| `commonapi_call` | "외부 통합 라우터(commonapi)로 특정 시스템 API 호출해줘" | action | `POST /commonapi/goApi` |

### System / Config

| 시나리오 ID | 대표 자연어 질의 | 패턴 | 엔드포인트 |
|---|---|---|---|
| `itg_load_property` | "ITG 런타임 설정값 다시 불러와줘" | action | `POST /standard/itgLoadProperty` |
| `itg_set_site_code` | "운영 대상 사이트 코드 서울본사로 변경해줘" | action | `POST /standard/setGlobalSiteCode` |
| `itg_comm_file_upload` | "인터페이스 설정 파일 ITG 공통 파일함에 업로드해줘" | action | `POST /standard/uploadCommFile` |
| `itg_comm_file_download` | "공통 파일함에서 인터페이스 매핑 파일 다운로드해줘" | action | `POST /standard/downloadCommFile` |
| `itg_comm_file_delete` | "공통 파일함의 오래된 첨부파일 삭제해줘" | action | `POST /standard/deleteCommFile` |

---

## 사용법

### LLM Tool 호출 매핑

```
사용자: "ITAM 마스터 동기화 배치잡 실행해줘"
→ batch_run_itam_master
→ POST /api/domain-itg/batchjob/executeBatchJob
→ body: { "mapParams": { "batchJobId": "syncItamMaster" } }

사용자: "SLI-003 이번 달 점수 알려줘"
→ slm_monthly_score
→ POST /api/domain-itg/slm/evaluation/selectMonthlyScore
→ body: { "mapParams": { "sliId": "SLI-003", "month": "2026-04" } }

사용자: "ERP_SYNC / DAILY_JOB 외부 API 호출"
→ ext_api_post_route
→ POST /api/domain-itg/ERP_SYNC/DAILY_JOB
→ body: { "mapParams": { ... } }
```

### 체인 호출 패턴 예시

```
① slm_eval_list_create  → SLM 평가 목록 생성 (sliId 목록 확보)
② slm_sli_execute       → 특정 sliId 평가 즉시 실행
③ slm_monthly_score     → 실행 결과 월간 점수 확인
④ slm_snapshot_run      → 확정 측정값 스냅샷 저장

① std_dup_check         → 새 코드 도큐먼트 중복 사전 확인
② std_insert            → 중복 없으면 컬렉션에 등록
③ std_list_paged        → 등록 결과 목록 재조회

① process_validate_bpmn → 신규 프로세스 정의 유효성 검증
② process_bpmn_update   → 검증 통과 후 연관 정보 갱신
③ process_start         → 신규 프로세스 인스턴스 시작
```

### Audit 개선 포인트 (현 spec → 목표)

| 결함 | 현재 | 목표 |
|---|---|---|
| examples summary | "기본 호출 예시" (메타라벨) | "ITAM 마스터 동기화 배치잡 실행해줘" (자연어 의도) |
| 통합/배치 어휘 | generic mapParams 설명 | batchJobId / if_id / processDefinitionId 실사용 예시 |
| SLM 시나리오 커버리지 | 26.6% | 4개 SLM 엔드포인트 × 3~5 examples 각각 |
| 외부 게이트웨이 | if_id/job_id 설명 없음 | 실제 인터페이스 ID 예시 (`ERP_SYNC`, `CMDB_PULL`) 포함 |

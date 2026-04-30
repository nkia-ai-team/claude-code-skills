# KCM 시나리오 카탈로그

> 생성일: 2026-04-29 | 도메인 audit 점수: 2.5/5 | 총 endpoint: 269

---

## 도메인 정체성

**KCM = Kubernetes Container Management**
Polestar10 플랫폼의 K8s 클러스터 전체 생애주기를 관리하는 도메인.
Cluster / Node / Namespace / Pod / Container / Workload(Deployment · ReplicaSet · StatefulSet · DaemonSet · Job · CronJob) / Service / Ingress / ConfigMap / Storage(PV · PVC · StorageClass) / HPA 등 K8s 리소스 전 계층의 조회 · 운영 · 메트릭 · 이벤트 · YAML 이력 · 로그 · 운영 명령 API를 제공한다.

---

## 도메인 어휘

| 한국어 | 영어 / K8s 용어 | 비고 |
|--------|----------------|------|
| 클러스터 | Cluster | 최상위 K8s 인프라 단위 |
| 노드 | Node | 클러스터를 구성하는 물리/가상 서버 |
| 네임스페이스 | Namespace | 리소스 격리 논리 단위 |
| 파드 | Pod | 컨테이너 실행 최소 단위 |
| 컨테이너 | Container | Pod 내부 프로세스 단위 |
| 디플로이먼트 | Deployment | 무상태 워크로드 배포 리소스 |
| 레플리카셋 | ReplicaSet | Deployment가 관리하는 Pod 복제 단위 |
| 스테이트풀셋 | StatefulSet | 상태 유지형 워크로드 (DB 등) |
| 데몬셋 | DaemonSet | 모든 노드에 1개씩 배포되는 워크로드 |
| 잡 | Job | 일회성 배치 작업 |
| 크론잡 | CronJob | 주기적 배치 작업 |
| 쿠버네티스 서비스 | Service (K8s) | Pod 접근 추상화 레이어 |
| 인그레스 | Ingress | 외부 HTTP(S) 라우팅 규칙 |
| 컨피그맵 | ConfigMap | 설정 데이터 저장 리소스 |
| 퍼시스턴트 볼륨 | PersistentVolume (PV) | 클러스터 영구 스토리지 |
| 퍼시스턴트 볼륨 클레임 | PersistentVolumeClaim (PVC) | Pod의 PV 요청 |
| 스토리지 클래스 | StorageClass | 동적 PV 프로비저닝 정책 |
| 수평 파드 오토스케일러 | HorizontalPodAutoscaler (HPA) | CPU/메모리 기반 파드 자동 스케일링 |
| 파드 상태 | Pod Phase | Pending / Running / Succeeded / Failed / Unknown |
| CrashLoopBackOff | CrashLoopBackOff | 반복 재시작 오류 상태 |
| OOMKilled | OOMKilled | 메모리 초과로 컨테이너 강제 종료 |
| Evicted | Evicted | 노드 자원 부족으로 파드 퇴거 |

---

## 시나리오 카탈로그 (45개)

### Pod / Container

| 시나리오 ID | 자연어 쿼리 예시 | 패턴 | 관련 endpoint |
|-------------|----------------|------|---------------|
| `crashloop_pods_all` | "CrashLoopBackOff 상태인 파드 전체 조회" | list+filter | `POST /api/kcm/resource-explore/pods/list-filter` (filter: phase=CrashLoopBackOff) |
| `oomkilled_pods` | "OOMKilled로 종료된 파드 목록" | list+filter | `POST /api/kcm/resource-explore/pods/list-filter` (filter: containerState=OOMKilled) |
| `pending_pods_by_ns` | "default 네임스페이스에서 Pending 상태인 파드" | list+filter | `POST /api/kcm/resource-explore/namespace/{ID}/pods/list-filter` (filter: phase=Pending) |
| `running_pods_default_ns` | "default 네임스페이스 Running 파드 목록" | list | `POST /api/kcm/resource-explore/namespace/{ID}/pods/list-filter` |
| `high_cpu_pods_top10` | "CPU 사용률 높은 파드 Top 10" | list+sort | `POST /api/kcm/resource-explore/pods/list-filter` (sort: cpuUsage DESC, size=10) |
| `high_mem_pods` | "메모리 사용량 상위 파드 조회" | list+sort | `POST /api/kcm/resource-explore/pods/list-filter` (sort: memUsage DESC) |
| `pod_detail` | "특정 파드 상세 정보 확인" | detail | `POST /api/kcm/pods/{resourceId}/basic-info` |
| `pod_status` | "파드 현재 상태 조회" | detail | `POST /api/kcm/resource-explore/pods/{ID}/status` |
| `pod_events` | "파드 이벤트 목록 — 오류 원인 파악" | list | `POST /api/kcm/resource-explore/pod/{ID}/events-list-filter` |
| `pod_events_trend` | "파드 이벤트 발생 추이 차트 (최근 1시간)" | chart | `POST /api/kcm/resource-explore/pod/{ID}/events-count-chart` |
| `pod_yaml` | "파드 현재 YAML 확인" | detail | `POST /api/kcm/resource-explore/pod/{ID}/yaml` |
| `pod_yaml_history` | "파드 YAML 변경 이력 10건" | list | `POST /api/kcm/resource-explore/pod/{ID}/yaml-history` |
| `pod_containers` | "특정 파드 내 컨테이너 목록" | list | `POST /api/kcm/resource-explore/pod/{ID}/containers/list-filter` |
| `pod_linkable` | "파드와 연관된 리소스(Service, Deployment 등) 조회" | detail | `POST /api/kcm/resource-explore/pod/{ID}/linkable` |
| `pod_history_list` | "파드 이력(재기동·교체 이력) 목록" | list | `POST /api/kcm/resource-explore/pods/history/list-filter` |
| `pod_describe` | "파드 describe 결과로 이벤트·컨디션 확인" | operation | `POST /api/kcm/operation/command/pod/describe` |
| `container_log_stream` | "컨테이너 실시간 로그 스트림 (error 키워드 필터)" | stream | `POST /api/kcm/log/container/{ID}` |
| `container_cmd_env` | "파드 컨테이너 내 환경변수 조회 (env 명령)" | operation | `POST /api/kcm/operation/command/pod` |
| `container_detail` | "컨테이너 상세 정보 확인" | detail | `POST /api/kcm/containers/{resourceId}/basic-info` |
| `container_status` | "컨테이너 현재 상태 확인" | detail | `POST /api/kcm/resource-explore/container/{ID}/status` |
| `evicted_pods` | "Evicted 상태 파드 목록 조회" | list+filter | `POST /api/kcm/resource-explore/pods/list-filter` (filter: phase=Evicted) |
| `pod_map_ns` | "네임스페이스별 파드 상태 현황 맵" | map | `POST /api/kcm/podmap/resource-status` (groupBy=namespace) |
| `pod_groupby_cluster` | "클러스터별 파드 상태 집계" | aggregate | `POST /api/kcm/podmap/pod-status-filter/groupby` (groupBy=cluster) |
| `pod_perf_chart` | "파드 목록 최근 1시간 CPU 사용률 추이" | chart | `POST /api/kcm/measurement/multi-resource/time-period` (resourceType=pod) |

### Cluster / Node

| 시나리오 ID | 자연어 쿼리 예시 | 패턴 | 관련 endpoint |
|-------------|----------------|------|---------------|
| `cluster_list` | "전체 클러스터 목록 조회" | list | `POST /api/kcm/resource-explore/clusters/list-filter` |
| `cluster_running_only` | "Running 상태 클러스터만 필터링" | list+filter | `POST /api/kcm/resource-explore/clusters/list-filter` (filter: status=Running) |
| `cluster_detail` | "특정 클러스터 기본 정보(버전·노드 수 등) 조회" | detail | `POST /api/kcm/clusters/{resourceId}/basic-info` |
| `cluster_status` | "클러스터 현재 구동 상태 확인" | detail | `POST /api/kcm/resource-explore/cluster/{ID}/status` |
| `cluster_events` | "클러스터 최근 이벤트 목록" | list | `POST /api/kcm/resource-explore/cluster/{ID}/events-list-filter` |
| `cluster_event_trend` | "클러스터 이벤트 발생 건수 시간별 차트" | chart | `POST /api/kcm/resource-explore/cluster/{ID}/events-count-chart` |
| `cluster_resource_map` | "클러스터 리소스 맵 전체 현황" | map | `POST /api/kcm/resource-explore/cluster/{ID}/resource-map` |
| `cluster_pods` | "특정 클러스터의 전체 파드 목록" | list | `POST /api/kcm/resource-explore/cluster/{ID}/pods/list-filter` |
| `cluster_perf_multi` | "클러스터 CPU·메모리 멀티 메트릭 차트" | chart | `POST /api/kcm/measurement/multi/time-period` (resourceType=cluster) |
| `cluster_agent_list` | "클러스터 에이전트 목록 및 상태 확인" | list | `POST /api/kcm/clusters/{clusterId}/agents/list-filter` |
| `cluster_agent_restart` | "클러스터 에이전트 재시작 명령 실행" | operation | `POST /api/kcm/operation/agent-restart` |
| `cluster_kubectl_cmd` | "클러스터에서 kubectl 명령 실행 (get nodes 등)" | operation | `POST /api/kcm/operation/command` |
| `node_list` | "전체 노드 목록 조회" | list | `POST /api/kcm/resource-explore/nodes/list-filter` |
| `node_not_ready` | "NotReady 상태 노드 필터링" | list+filter | `POST /api/kcm/resource-explore/nodes/list-filter` (filter: status=NotReady) |
| `node_detail` | "노드 상세 정보(CPU·메모리·OS 등) 조회" | detail | `POST /api/kcm/nodes/{resourceId}/basic-info` |
| `node_pods` | "특정 노드에 배치된 파드 목록" | list | `POST /api/kcm/resource-explore/node/{ID}/pods/list-filter` |
| `node_events` | "노드 이벤트 목록 조회" | list | `POST /api/kcm/resource-explore/node/{ID}/events-list-filter` |
| `node_describe` | "노드 describe 결과로 조건·이벤트 확인" | operation | `POST /api/kcm/operation/command/node/describe` |
| `node_perf_chart` | "노드 오늘 CPU·메모리 성능 지표 차트" | chart | `POST /api/kcm/measurement/multi/time-period` (resourceType=node) |

### Namespace

| 시나리오 ID | 자연어 쿼리 예시 | 패턴 | 관련 endpoint |
|-------------|----------------|------|---------------|
| `ns_list` | "전체 네임스페이스 목록 조회" | list | `POST /api/kcm/resource-explore/namespaces/list-filter` |
| `ns_active_only` | "Active 상태 네임스페이스만 필터링" | list+filter | `POST /api/kcm/resource-explore/namespaces/list-filter` (filter: status=Active) |
| `ns_pods` | "특정 네임스페이스의 파드 전체 조회" | list | `POST /api/kcm/resource-explore/namespace/{ID}/pods/list-filter` |
| `ns_yaml_history` | "네임스페이스 YAML 설정 변경 이력" | list | `POST /api/kcm/resource-explore/namespace/{ID}/yaml-history` |
| `ns_events_trend` | "네임스페이스 이벤트 발생 추이" | chart | `POST /api/kcm/resource-explore/namespace/{ID}/events-count-chart` |

### Deployment / StatefulSet / DaemonSet

| 시나리오 ID | 자연어 쿼리 예시 | 패턴 | 관련 endpoint |
|-------------|----------------|------|---------------|
| `deploy_list` | "전체 디플로이먼트 목록 조회" | list | `POST /api/kcm/resource-explore/deployments/list-filter` |
| `deploy_pods` | "특정 디플로이먼트 하위 파드 목록" | list | `POST /api/kcm/resource-explore/deployment/{ID}/pods/list-filter` |
| `deploy_yaml_history` | "디플로이먼트 YAML 변경 이력으로 롤백 원인 추적" | list | `POST /api/kcm/resource-explore/deployment/{ID}/yaml-history` |
| `deploy_events` | "디플로이먼트 이벤트 목록 (배포 오류 원인 확인)" | list | `POST /api/kcm/resource-explore/deployment/{ID}/events-list-filter` |
| `sts_list` | "스테이트풀셋 목록 조회 (DB 워크로드 포함)" | list | `POST /api/kcm/resource-explore/statefulsets/list-filter` |
| `sts_pods` | "특정 스테이트풀셋 파드 목록 확인" | list | `POST /api/kcm/resource-explore/statefulset/{ID}/pods/list-filter` |
| `ds_list` | "데몬셋 목록 조회 (노드 에이전트 배포 현황)" | list | `POST /api/kcm/resource-explore/daemonsets/list-filter` |
| `rs_list` | "레플리카셋 목록 — desired/ready replica 불일치 확인" | list | `POST /api/kcm/resource-explore/replicasets/list-filter` |

### Resource Explore (HPA / Job / CronJob / Service / Ingress)

| 시나리오 ID | 자연어 쿼리 예시 | 패턴 | 관련 endpoint |
|-------------|----------------|------|---------------|
| `hpa_list` | "HPA 목록 조회 — 스케일링 정책 현황" | list | `POST /api/kcm/resource-explore/hpas/list-filter` |
| `hpa_scaling_events` | "HPA 스케일링 이벤트 발생 이력 확인" | list | `POST /api/kcm/resource-explore/hpa/{ID}/events-list-filter` |
| `hpa_yaml` | "HPA YAML 상세 — maxReplicas·minReplicas 확인" | detail | `POST /api/kcm/resource-explore/hpa/{ID}/yaml` |
| `job_list` | "잡 목록 조회 — 완료/실패 상태 확인" | list | `POST /api/kcm/resource-explore/jobs/list-filter` |
| `cronjob_list` | "크론잡 목록 조회 — 스케줄 주기 확인" | list | `POST /api/kcm/resource-explore/cronjobs/list-filter` |
| `svc_list` | "쿠버네티스 서비스 목록 조회" | list | `POST /api/kcm/resource-explore/services/list-filter` |
| `ingress_list` | "인그레스 목록 조회 — 외부 라우팅 규칙 확인" | list | `POST /api/kcm/resource-explore/ingresses/list-filter` |

### Storage

| 시나리오 ID | 자연어 쿼리 예시 | 패턴 | 관련 endpoint |
|-------------|----------------|------|---------------|
| `pvc_list` | "퍼시스턴트 볼륨 클레임 목록 — Pending/Bound 상태 확인" | list | `POST /api/kcm/resource-explore/pvcs/list-filter` |
| `pv_list` | "퍼시스턴트 볼륨 목록 조회" | list | `POST /api/kcm/resource-explore/pvs/list-filter` |
| `pvc_events` | "PVC 이벤트 목록 — 볼륨 마운트 오류 원인 파악" | list | `POST /api/kcm/resource-explore/pvc/{ID}/events-list-filter` |
| `sc_list` | "스토리지 클래스 목록 조회 — 동적 프로비저닝 정책 확인" | list | `POST /api/kcm/resource-explore/storageclasses/list-filter` |

### Measurement (K8s Metrics)

| 시나리오 ID | 자연어 쿼리 예시 | 패턴 | 관련 endpoint |
|-------------|----------------|------|---------------|
| `metric_defs_pod` | "파드에서 사용 가능한 측정 지표 정의 목록" | list | `POST /api/kcm/measurement/definitions/resourcetype/{resourceType}/metric` (resourceType=pod) |
| `metric_multi_resource` | "여러 파드의 주간 CPU·메모리 성능 현황 차트" | chart | `POST /api/kcm/measurement/multi-resource/time-period` (resourceType=pod) |
| `metric_multiline_chart` | "클러스터 CPU·메모리 멀티라인 차트 데이터" | chart | `POST /api/kcm/measurement/multi/time-period` (resourceType=cluster) |

---

## 사용법

### 시나리오 → endpoint 매핑 규칙

1. **path의 `resourceType` 파라미터와 요청 본문의 `resourceType` 값은 반드시 일치해야 한다.**
   - 예: `POST /api/kcm/measurement/definitions/resourcetype/pod/metric` → body `resourceType: "pod"`
   - 예: `POST /api/kcm/podmap/pod-status-filter/groupby` → body `groupBy: "namespace"` or `"cluster"`

2. **K8s 장애 시나리오 강제 포함 필드**
   - CrashLoopBackOff: `filter.phase = "CrashLoopBackOff"` (pods/list-filter)
   - OOMKilled: `filter.containerState = "OOMKilled"` (pods/list-filter)
   - Pending: `filter.phase = "Pending"` (pods/list-filter, namespace/{ID}/pods/list-filter)
   - HPA 스케일링: hpa/{ID}/events-list-filter → eventReason 필드로 ScalingReplicaSet 확인
   - Evicted: `filter.phase = "Evicted"` (pods/list-filter)

3. **chain-call 패턴 (ID 취득 → 상세 조회)**
   - 목록 조회로 `podId` 취득 → `basic-info` / `status` / `yaml` 로 드릴다운
   - 예: `pods/list-filter` → `pod/{ID}/yaml` → `pod/{ID}/yaml-history`

4. **audit 결함 및 수정 방향**

   | 결함 유형 | 발생 건수 | 수정 방향 |
   |-----------|----------|----------|
   | `"파드 파드"` 이중 표기 버그 (예: "파드 소속 파드 목록 조회") | 44건 | summary를 "클러스터 소속 파드 목록 조회" 등 부모 리소스 명칭으로 교체 |
   | `profile-options` 3 endpoint 동일 example | 3건 | reset/get/update 각 endpoint별 고유 example 작성 |
   | multi-slot dup example | 다수 | 각 slot에 실질적으로 다른 쿼리 조건 부여 |
   | k8s 장애 시나리오 부재 | — | 위 시나리오 카탈로그 `crashloop_pods_all`, `oomkilled_pods`, `pending_pods_by_ns`, `evicted_pods`, `hpa_scaling_events` 신규 추가 |

---

*총 시나리오: 45개 | 커버 섹션: Pod/Container(24) · Cluster/Node(19) · Namespace(5) · Deployment/StatefulSet/DaemonSet(8) · Resource Explore(7) · Storage(4) · Measurement(3)*

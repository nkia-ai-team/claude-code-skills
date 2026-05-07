# Services-Author Task Spec

testbed-build Phase 6 (services-author) 가 testbed-engineer agent 에 넘기는 task spec.

**조건**: interview.app.testbed_name 이 testbed-services 레포에 **없는 새 testbed** 일 때만 실행. 기존 testbed (plopvape-shop 등) 이면 skip 하고 바로 Phase 7 (inventory) 진행.

## Trigger 조건

```bash
TESTBED_DIR="${TESTBED_SVC_REPO}/${INTERVIEW_TESTBED_NAME}"
if [ -d "$TESTBED_DIR" ]; then
  echo "[phase 6] testbed-services 에 ${INTERVIEW_TESTBED_NAME} 이미 존재. services-author skip."
  update_manifest_phase "services_author" "completed"
  return 0
fi
echo "[phase 6] 신규 testbed → services-author dispatch"
```

## Task prompt (testbed-engineer 에게 전달)

```yaml
task: services-author

architecture:
  testbed_name: "{{INTERVIEW_TESTBED_NAME}}"        # interview.app.testbed_name
  domain: "{{INTERVIEW_DOMAIN}}"                     # interview.app.domain (자연어)
  language: java-spring
  java_version: 17

  services:                                          # interview.app.services[]
    {{#each SERVICES}}
    - name: "{{name}}"
      responsibilities: {{responsibilities}}
      endpoints: {{endpoints}}
      depends_on: {{depends_on}}
    {{/each}}

  db:
    kind: "{{INTERVIEW_DB_KIND}}"                    # interview.app.db_kind
    schemas: {{INTERVIEW_SCHEMAS}}                   # interview.app.db.schemas
    seed: true

  failure_surfaces: {{INTERVIEW_FAILURE_SURFACES}}  # interview.app.failure_surfaces

  # 배포 manifest 강제 요구사항 — Polestar10 APM 자원 자동 등록에 필수
  manifest_requirements:
    otlp_env_required: true        # 모든 service Deployment 의 env 에 5개 OTLP 변수 필수
    apm_jar_volume_required: true  # apm-agent jar hostPath mount 필수
    wpm_jvm_attach: true           # default ON. RCA 테스트베드는 6종 에이전트 풀 스택 모니터링이 목적.
                                   # WPM Scouter javaagent 가 OTel javaagent 와 dual-attach 됨:
                                   # → wpm-agent jar volume (/opt/polestar10/wpm → /opt/wpm) 추가
                                   # → JAVA_TOOL_OPTIONS 에 -javaagent:/opt/wpm/wpmagent.jar 추가
                                   # → WPM collector env (UDP 31002 / TCP 31005) 추가
                                   # 사용자가 명시적으로 OTel only 만 원하면 deep interview 에서 false 로 변경

context:
  testbed_services_repo: "{{TESTBED_SVC_REPO}}"     # bootstrap.paths.testbed_services_repo
  reference_subdir: "plopvape-shop"
  branch: "feat/{{TESTBED_NAME}}-scaffold"
  push_mode: "{{PUSH_MODE}}"                         # default: pr
  pat_available: {{PAT_PRESENT}}                     # ~/.git-credentials 존재 여부
```

## ⚠️ Deployment manifest 강제 요구사항 — OTLP env (Polestar10 APM 자원 등록 필수)

새 testbed 생성 시 **각 service Deployment 의 `env` 에 다음 5개 OTLP 변수를 반드시 포함**. 누락 시 OTel javaagent attach 후에도 데이터가 polestar10 OTLP receiver 로 도달 안 함 → standby 미감지 → APM 자원 자동 등록 실패 → fired alarm 0건.

```yaml
spec:
  template:
    spec:
      volumes:
        - name: apm-agent-jar
          hostPath:
            path: /opt/polestar10/apm
            type: Directory
      containers:
        - name: <service>
          volumeMounts:
            - name: apm-agent-jar
              mountPath: /opt/apm
              readOnly: true
          env:
            - name: JAVA_TOOL_OPTIONS
              value: "-javaagent:/opt/apm/opentelemetry-javaagent.jar"
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "${OTLP_ENDPOINT}"             # envsubst placeholder — deploy-time 치환. build-and-deploy.sh 가 OTLP_ENDPOINT env 받아 envsubst. ⚠️ jinja `{{ polestar10_collector_host }}` X, hardcoded IP X. 이유: build-and-deploy.sh 는 단순 kubectl apply — jinja 처리 안 함. 본 placeholder 만 envsubst 가 치환 가능.
            - name: OTEL_EXPORTER_OTLP_PROTOCOL
              value: "grpc"
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: "lucida.organizationId=__ORGANIZATION_ID__,lucida.groupId=__TESTBED_NAME__"   # services-author 가 generation 시점에 literal 치환 (organization_id 와 testbed_name 은 testbed identity — 정적 값). collector address 처럼 환경별로 변하지 않으므로 deploy-time envsubst 불필요.
            - name: OTEL_METRIC_EXPORT_INTERVAL
              value: "10000"
```

핵심 포인트 (round-7 사용자 진단으로 확정):

- **`OTEL_EXPORTER_OTLP_ENDPOINT` port 6565** — Polestar10 의 OTLP gRPC receiver. 표준 4317/4318 사용 X (refused).
- **`OTEL_RESOURCE_ATTRIBUTES.lucida.organizationId`** — bootstrap.yaml 의 24-hex `organization_id`. 누락 시 polestar10 가 어느 조직 데이터인지 판단 불가.
- **`OTEL_RESOURCE_ATTRIBUTES.lucida.groupId`** — testbed 이름 (= app_subdir / cluster_name). polestar10 web UI 에 service group 단위로 묶이기 위한 키.
- **`apm-agent-jar` hostPath** = `/opt/polestar10/apm` (ansible role agent-apm 이 호스트에 jar 배치한 경로). 컨테이너 mount 는 `/opt/apm`.

testbed-engineer agent 가 새 Deployment manifest 생성 시 위 5 env + volumes/volumeMounts 자동 포함. plopvape-shop 의 검증된 manifest 를 reference_subdir 로 사용 — 그 패턴 그대로 mimic.

검증: ansible-playbook 직후 SKILL.md Phase 8 의 8-c sanity check (APM standby agent count) 가 자동 검증 — fail 시 manifest 미반영 의심.

### 🚫 매니페스트 치환 패턴 — 강제 룰 (services-author 가 신규 testbed 만들 때 따를 것)

| 변수 | 변환 시점 | 매니페스트 표기 | 누가 치환 |
|---|---|---|---|
| OTEL_EXPORTER_OTLP_ENDPOINT | **deploy-time** (collector 주소가 환경마다 다름) | `${OTLP_ENDPOINT}` | build-and-deploy.sh 의 envsubst |
| OTEL_RESOURCE_ATTRIBUTES (organizationId / groupId) | **generation-time** (testbed identity 정적값) | `__ORGANIZATION_ID__` / `__TESTBED_NAME__` | services-author 가 generation 시점에 sed |
| 그 외 hardcoded IP / port | 사용 금지 | — | — |

**금지 패턴**:
- ❌ `value: "http://192.168.230.104:6565"` — 사내 IP leak + 환경별 변경 불가능
- ❌ `value: "http://{{ polestar10_collector_host }}:6565"` — Jinja 표현은 build-and-deploy.sh 가 처리 못함 (단순 kubectl apply). K8s 가 literal 문자열로 해석 → DNS 실패

**필수 — 신규 testbed 의 build-and-deploy.sh 표준 패턴**:

services-author 가 신규 testbed 의 `<testbed>/k8s/build-and-deploy.sh` 를 만들 때 마지막 phase (kubectl apply 영역) 가 다음 형식이어야 함:

```bash
# ${OTLP_ENDPOINT} 미설정이면 즉시 실패 — collector 주소 누락된 채 Pod 가 broken endpoint 로 뜨는 사고 차단
: "${OTLP_ENDPOINT:?OTLP_ENDPOINT 미설정 — ansible 또는 수동 export 필요 (예: http://<collector>:6565)}"

# 매니페스트 안 ${OTLP_ENDPOINT} 만 envsubst 로 치환. 그 외 ${...} 표현은 K8s downward API ($(POD_NAME) 등) 와 충돌 방지 위해 single-quote 로 envsubst 화이트리스트 명시.
for f in "${PROJECT_ROOT}/k8s/"*.yaml; do
  envsubst '${OTLP_ENDPOINT}' < "$f" | kubectl apply -f -
done
```

ansible service-k8s role 이 build-and-deploy.sh 호출 시 `OTLP_ENDPOINT="http://{{ polestar10_collector_host }}:6565"` env 주입. 사용자가 수동 실행 시엔 직접 export 필요.

이 패턴이 있어야:
- `polestar10_collector_host` 변경 시 ansible 재실행만으로 APM/WPM/KCM/SMS 모두 새 collector 로 갱신
- testbed-services 레포가 사내 IP leak 없는 placeholder 만 commit
- 수동 실행 시 OTLP_ENDPOINT 누락이 silent fail 대신 fail-fast

## ⚠️ WPM (Scouter) dual-attach — default ON (manifest_requirements.wpm_jvm_attach=true)

RCA 테스트베드는 Polestar10 의 6종 에이전트 (KCM / APM / WPM / SMS / DPM / NMS) 풀 스택 모니터링이 목적. WPM 은 default ON 으로 OTel javaagent 와 dual-attach. 새 testbed 생성 시 services-author 가 자동으로 다음 패턴 적용:

```yaml
spec:
  template:
    spec:
      volumes:
        - name: apm-agent-jar
          hostPath: { path: /opt/polestar10/apm, type: Directory }
        - name: wpm-agent-jar               # ← 추가
          hostPath: { path: /opt/polestar10/wpm, type: Directory }
      containers:
        - name: <service>
          volumeMounts:
            - { name: apm-agent-jar, mountPath: /opt/apm, readOnly: true }
            - { name: wpm-agent-jar, mountPath: /opt/wpm, readOnly: true }   # ← 추가
          env:
            # OTel + WPM dual-attach (한 JAVA_TOOL_OPTIONS 에 -javaagent 두 개)
            - name: JAVA_TOOL_OPTIONS
              value: "-javaagent:/opt/apm/opentelemetry-javaagent.jar -javaagent:/opt/wpm/wpmagent.jar -Dwpm.config=/opt/wpm/<service>/wpmagent.conf"
            # OTel env (위와 동일 — envsubst placeholder 형식)
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "${OTLP_ENDPOINT}"
            # ... 나머지 OTel env
            # WPM collector — UDP 31002 / TCP 31005 (Scouter 표준)
            - name: WPM_COLLECTOR_UDP_PORT
              value: "31002"
            - name: WPM_COLLECTOR_TCP_PORT
              value: "31005"
```

WPM 의 `<service>/wpmagent.conf` 는 ansible agent-wpm role 이 호스트에 service 별로 dir 생성 + 그 안에 conf render (msa_group_id={{app_subdir}}-{{item}}). 컨테이너 안에선 `/opt/wpm/<service>/wpmagent.conf` 로 mount 된 형태.

**default ON 인 이유**: RCA 테스트베드의 6종 에이전트 풀 스택 모니터링 목적. WPM 메트릭 (Scouter 고유 — TX queue / GC profiling / thread profiling) 이 OTel 메트릭 (response_time / error_rate / TPS) 과 함께 RCA 분석에 사용됨. dual-attach 의 JVM 부하 ↑ 는 트레이드오프이지만 6종 풀 스택이 우선. 사용자가 OTel only 원하면 deep interview 에서 'OTel only' 응답.

## 변환 (오케스트레이터가 task spec 채움)

```bash
TASK_PROMPT=$(cat <<EOF
task: services-author

architecture:
  testbed_name: "$INTERVIEW_TESTBED_NAME"
  domain: "$INTERVIEW_DOMAIN"
  language: java-spring
  java_version: 17
  services: $(yq '.app.services' "$INTERVIEW_YAML" -o=json)
  db:
    kind: "$INTERVIEW_DB_KIND"
    schemas: $(yq '.app.db.schemas' "$INTERVIEW_YAML" -o=json)
    seed: true
  failure_surfaces: $(yq '.app.failure_surfaces' "$INTERVIEW_YAML" -o=json)

context:
  testbed_services_repo: "$TESTBED_SVC_REPO"
  reference_subdir: "plopvape-shop"
  branch: "feat/${INTERVIEW_TESTBED_NAME}-scaffold"
  push_mode: "${PUSH_MODE:-pr}"
  pat_available: $([ -f ~/.git-credentials ] && echo true || echo false)
EOF
)

# Agent 호출
RESULT=$(claude_invoke_agent --type testbed-engineer --prompt "$TASK_PROMPT")
```

## 출력 처리

testbed-engineer 가 반환한 JSON:

```json
{
  "verdict": "ok",
  "testbed_name": "core-banking",
  "subdir_created": "<paths.testbed_services_repo>/core-banking",
  "services_created": ["account", "transfer", "ledger", "audit"],
  "files_count": 47,
  "build_passed": true,
  "build_warnings": 0,
  "branch": "feat/core-banking-scaffold",
  "pr_url": "https://github.com/nkia-ai-team/testbed-services/pull/12",
  "scenario_hints": {
    "lock_table": "accounts",
    "lock_endpoint": "/api/accounts/{id}",
    "external_endpoint": "/api/transfer",
    "external_container": "external-pg-mock",
    "primary_load_endpoint": "/api/transfer"
  }
}
```

오케스트레이터:
1. **verdict 확인**:
   - `ok` → manifest.phases.services_author = completed. scenario_hints 를 manifest 에 보존 (Phase 10 generate-scenarios 가 사용).
   - `conflict` → 사용자 prompt: "이름 충돌. 다른 이름?"
   - `build-failed` → testbed-engineer 가 자동 fix 3회 시도 후도 실패. 사용자에게 로그 + 디렉토리 보존 + manual fix 권고.
   - `auth-failed` → git push 인증 실패. PAT 점검 안내.
   - `unknown` → 사용자 prompt + 보존.

2. **PR 머지 대기 (push_mode=pr 시)** — AskUserQuestion:
   ```
   PR 생성됨: $PR_URL
   ```
   ```python
   AskUserQuestion(questions=[
     {
       "question": "PR 머지 후 Phase 7 (ansible deploy) 진행을 어떻게 하시겠어요?",
       "header": "PR 머지",
       "multiSelect": False,
       "options": [
         {"label": "머지 완료 — 진행 (Recommended)", "description": "사용자가 PR 직접 머지 후 클릭"},
         {"label": "자동 폴링 wait", "description": "60초마다 PR 머지 상태 polling, 머지되면 자동 진행"},
         {"label": "취소", "description": "phase 미완 상태로 종료, run 보존"}
       ]
     }
   ])
   ```

3. **scenario_hints 저장** (표준 verdict envelope 의 outputs 안에서 추출):
   ```bash
   yq -i ".scenario_hints = $(echo "$RESULT" | jq -c '.outputs.scenario_hints')" \
     "$HOME/.testbed-build/runs/$RUN_ID/manifest.yaml"
   ```

4. **architecture.md 갱신**:
   생성된 services_created + scenario_hints 를 architecture.md 에 추가 (Phase 12 finalize 가 보고서에 포함).

## Push mode 선택 가이드

| mode | 언제 |
|---|---|
| `pr` (default) | 안전. 사람이 review 후 머지. 첫 dogfooding 권장. |
| `direct-push` | 신뢰 환경. CI 없는 경우. main 으로 직접 머지. |
| `local-only` | 로컬 검증만. 사용자가 수동 push 시점 결정. |

오케스트레이터는 default `pr`. 사용자가 인터뷰에서 override 가능.

## services-author 미사용 (skip) 시나리오

다음 경우 phase 6 skip:
1. interview.app.testbed_name 이 testbed-services 레포에 이미 존재 (= 기존 plopvape-shop 등)
2. 사용자가 인터뷰에서 옵션 1 (plopvape-shop 레퍼런스) 또는 2 (다른 기존 testbed) 선택

→ manifest.phases.services_author = `skipped` 로 기록. Phase 7 진행.

## 실패 시 manifest 상태

| 상태 | 처리 |
|---|---|
| completed | scenario_hints 보존 + Phase 7 진행 |
| skipped | Phase 7 진행 |
| failed (build) | run dir 보존 + 사용자 manual fix 권고. resume 시 재시도 prompt. |
| failed (auth) | run dir 보존 + PAT 점검 안내. |
| failed (conflict) | run dir 보존 + 인터뷰 다시 prompt (이름 변경) |

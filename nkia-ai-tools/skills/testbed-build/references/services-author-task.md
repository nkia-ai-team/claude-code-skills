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
    otlp_env_required: true       # 모든 service Deployment 의 env 에 5개 OTLP 변수 필수
    apm_jar_volume_required: true  # apm-agent jar hostPath mount 필수

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
              value: "http://{{ polestar10_collector_host }}:{{ polestar10_apm_otlp_port | default('6565') }}"
            - name: OTEL_EXPORTER_OTLP_PROTOCOL
              value: "grpc"
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: "lucida.organizationId={{ polestar_organization_id }},lucida.groupId={{ testbed_name }}"
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

3. **scenario_hints 저장**:
   ```bash
   yq -i ".scenario_hints = $(echo "$RESULT" | jq -c '.scenario_hints')" \
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

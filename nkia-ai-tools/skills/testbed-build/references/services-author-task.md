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

context:
  testbed_services_repo: "{{TESTBED_SVC_REPO}}"     # bootstrap.paths.testbed_services_repo
  reference_subdir: "plopvape-shop"
  branch: "feat/{{TESTBED_NAME}}-scaffold"
  push_mode: "{{PUSH_MODE}}"                         # default: pr
  pat_available: {{PAT_PRESENT}}                     # ~/.git-credentials 존재 여부
```

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
  "subdir_created": "/home/sjbang/dev/testbed-services/core-banking",
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

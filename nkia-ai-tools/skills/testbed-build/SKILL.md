---
name: testbed-build
description: NKIA RCA 테스트베드 end-to-end 자동화 오케스트레이터 (Mode 1 = 새 테스트베드 처음부터 끝까지). 4단계 인터뷰 → 아키텍처 승인 → ansible-playbook 배포 → Polestar10 6종 자원 등록 → 시나리오 4종 생성 → LLM 알람 정책 → closed-loop 검증 → 보고서. 사용자가 "/testbed-build", "테스트베드 만들어줘", "RCA 환경 셋업", "새 testbed 구축" 같은 요청 시 트리거. 시나리오 추가만 원하면 testbed-generate-scenarios 단독 호출, 알람 재튜닝만 원하면 testbed-tune-alarms 단독 호출.
---

# testbed-build

## Overview

이 스킬은 **오케스트레이터**. 단계별로 sub-skill / agent 를 dispatch 하며 진행 상태를 `~/.testbed-build/runs/<ts>/manifest.yaml` 에 체크포인트.

### 책임 / 비책임

✅ 책임:
- 4단계 인터뷰 → 인벤토리/아키텍처 산출
- ansible-playbook 호출 + 실패 진단 위임 (testbed-engineer agent)
- testbed-polestar10-register / testbed-generate-scenarios / testbed-tune-alarms dispatch
- testbed-verifier agent → closed-loop 재시도 (오케스트레이터 레벨, max 3)
- 최종 보고서 작성 + 정리

❌ 비책임:
- 기존 테스트베드 cleanup (사용자 직접: `kubectl delete ns ...` + testbed-polestar10-register 시나리오 4)
- 시나리오만 추가 (testbed-generate-scenarios 단독 호출)
- 알람만 재튜닝 (testbed-tune-alarms 단독 호출)
- 새 testbed 생성 (옵션 3) 선택 시 testbed-engineer agent 가 testbed-services 레포에 코드 자동 생성 + git PR (Phase 6)

---

## ⚠️ 인터뷰는 AskUserQuestion 도구로

**모든 multi-choice 인터뷰 (인증 방식 / 옵션 선택 / yes-no 분기 / 사용자 승인) 은 텍스트 프롬프트가 아니라 `AskUserQuestion` 도구 호출.** 사용자에게 카드형 UI 가 떠서 클릭으로 선택. 자유 입력은 자동 추가되는 "Other" 또는 별도 텍스트 prompt.

여러 단계를 한 호출에 묶어서 (1~4 questions per call) UX 빠르게. 상세: [references/interview-flow.md](references/interview-flow.md) 의 추천 묶음 참조.

순수 자유 입력 슬롯 (target IP, namespace 이름, 자유 도메인 설명 등) 만 텍스트 프롬프트.

---

## CRITICAL: First Step — Bootstrap

매 호출 첫 단계 ([testbed-polestar10-register/SKILL.md](../testbed-polestar10-register/SKILL.md) 패턴 mimic):

### 1. `~/.testbed-build/` 디렉토리 init
```bash
mkdir -p ~/.testbed-build/{runs,reports,.locks}
chmod 700 ~/.testbed-build
```

### 2. `~/.testbed-build/bootstrap.yaml` 확인 + 인터뷰

상세: [references/bootstrap.md](references/bootstrap.md)

⚠️ **bootstrap.yaml 부재 시 AskUserQuestion 인터뷰 강제** — 다른 캐시 파일 (`~/.polestar10rc` / 레포 디렉토리 / `~/.git-credentials`) 존재 여부와 무관. 캐시된 파일은 인터뷰의 default value 제시용으로만 사용. "다 캐시돼 있으니 인터뷰 skip 하고 default 로 yaml 작성" 은 **금지**.

항상 물어야 하는 슬롯 (default 없음 — 매 호출 결정 필요):
- SSH 인증 방식 (password / ssh_key)
- 타겟 SSH user (default 표시: 기존 bootstrap.yaml 또는 `nkia`)
- Polestar10 base_url (default 표시: ~/.polestar10rc 의 값)
- Polestar10 user (default 표시: ~/.polestar10rc 의 값)
- 레포 경로 (default 표시: 기존 디렉토리 또는 `~/dev/...`)

캐시 파일 존재 시 skip 가능한 슬롯:
- ~/.polestar10rc → Polestar10 password 인터뷰 skip
- 레포 디렉토리 → clone 작업 skip
- ~/.git-credentials → git PAT 인터뷰 skip
- bootstrap.yaml 의 polestar10.organization_id 가 비어있지 않음 → organization_id 인터뷰 skip

⚠️ **organization_id 는 bootstrap.yaml 에 비어있으면 인터뷰 강제** — SMS install role 의 fail-fast 가드 + KCM helm chart 의 `kcm.orgId` (Secret `KCM_ORG_ID`) 가 모두 이 값을 참조. 빈값으로 진행하면 6종 자원 등록 시나리오에서 SMS/KCM standby 미감지 → PARTIAL verdict 로 끝남.

상세 슬롯 정책 표는 [references/bootstrap.md](references/bootstrap.md) 의 "인터뷰 슬롯 정책 표" 참조.

저장:
- chmod 600 으로 `~/.testbed-build/bootstrap.yaml` 영구 저장
- 다음 호출부터 인터뷰 X (값 변경 시 사용자가 직접 yaml 편집 또는 파일 삭제 후 재인터뷰)

### 3. 외부 레포 부재 시 git clone
```bash
TESTBED_SVC_REPO=$(grep '^testbed_services_repo:' ~/.testbed-build/bootstrap.yaml | awk '{print $2}')
RUNNER_REPO=$(grep '^scenario_runner_repo:' ~/.testbed-build/bootstrap.yaml | awk '{print $2}')

[ -d "$TESTBED_SVC_REPO/.git" ] || {
  echo "testbed-services 레포가 없습니다. clone 진행합니다."
  git clone https://github.com/nkia-ai-team/testbed-services.git "$TESTBED_SVC_REPO"
}
[ -d "$RUNNER_REPO/.git" ] || {
  echo "rca-scenario-runner 레포가 없습니다. clone 진행합니다."
  git clone https://github.com/nkia-ai-team/rca-scenario-runner.git "$RUNNER_REPO"
}
```

### 4. Resume 결정

[references/phase-checkpoint.md](references/phase-checkpoint.md) 참조.

```
~/.testbed-build/runs/ 스캔
  진행 중 (마지막 phase != "finalize") manifest 가 있으면:
    "run_id=<ts> 가 phase=<X> 에서 미완. 재개? [Y/n/new-run]"
  yes → 그 run_id 로 phase 부터 이어감
  new-run → 새 run_id (현재 timestamp)
```

새 run 시작 시:
```bash
RUN_ID=$(date +%Y%m%d-%H%M%S)
mkdir -p "$HOME/.testbed-build/runs/$RUN_ID"
```

### 5. Concurrency lock

[references/concurrency-lock.md](references/concurrency-lock.md) 참조.

인터뷰 단계까지 마친 후 (target_host 확정 후) lock 획득. 락 실패 시 안내 후 종료.

### 6. Polestar10 부트스트랩

`testbed-polestar10-register/references/bootstrap.md` 의 `~/.polestar10rc` 패턴 재사용. 같은 세션에 중복 부트스트랩 안 함.

---

## Phase Loop

진행 상태는 manifest.yaml 에 매 phase 후 즉시 저장 ([references/phase-checkpoint.md](references/phase-checkpoint.md)).

### [Phase 1] 인터뷰

[references/interview-flow.md](references/interview-flow.md) 의 4 단계 질문지 순차 진행:
- target server (IP/alias + SSH 자격증명 — bootstrap.yaml 에 캐시되면 재사용)
- 배포 앱 (plopvape-shop 레퍼런스 / 커스텀 git URL)
- NMS 모니터링 대상 (있음/없음)
- Polestar10 웹 조작 모드 (직접/자동)

답변 → `runs/<RUN_ID>/interview.yaml` 저장.

### [Phase 2] Polestar10 도달성 precheck

**Reachability 만 확인** — host 가 controller 에서 도달 가능한지. 실제 auth endpoint 동작은 testbed-polestar10-register 의 login.md (`POST /api/account/pre-login` → `POST /api/account/login`) 가 phase 9 시점에 검증. server 버전마다 auth path 다를 수 있어 본 단계에서 hardcode X.

```bash
HTTP_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" -m 10 "$POLESTAR10_BASE_URL/")
[ "$HTTP_CODE" = "000" ] && {
  echo "Polestar10 도달 불가 (network). bootstrap.yaml base_url + 네트워크 점검."
  exit 1
}
echo "[precheck] reachable (HTTP $HTTP_CODE)"
```

상세: [references/polestar10-error-handling.md](references/polestar10-error-handling.md). 실패 시 사용자 안내 후 phase 미완 상태로 종료 — ask-polestar10 호출은 actual auth 단계에서 (network 영역은 매뉴얼 무관).

### [Phase 3] Architecture-draft (인라인)

[references/architecture-template.md](references/architecture-template.md) 템플릿 변수 채우기:
- 인터뷰 답으로 mermaid 다이어그램 자동 생성
- 6종 에이전트 표 + 알람 정책 자리 (8단계 후 채워짐)
- 시나리오 자리 (7단계 후 채워짐)

산출: `runs/<RUN_ID>/architecture.md`. 사용자에게 표시.

### [Phase 4] 사용자 승인 ⛔

architecture.md 내용을 사용자에게 표시 후 `AskUserQuestion`:

```python
AskUserQuestion(questions=[
  {
    "question": "위 architecture v1 으로 진행할까요?",
    "header": "Arch 승인",
    "multiSelect": False,
    "options": [
      {"label": "진행 (Recommended)", "description": "Phase 5 lock 획득 → ansible 배포 시작"},
      {"label": "수정 (edit)", "description": "architecture.md 직접 편집 후 다시 prompt"},
      {"label": "취소", "description": "phase 미완 상태로 종료, run 보존"}
    ]
  }
])
```

### [Phase 4.5] 기존 testbed 감지 게이트 (cluster 단위)

타겟 서버에 같은 이름의 cluster 가 이미 떠있는지 사전 감지. 떠있으면 사용자 의도 카드 (장애 시나리오만 / 다른 testbed / 기존 삭제 / idempotent 재배포 / 중단).

**상세 절차**: [references/existing-testbed-detect.md](references/existing-testbed-detect.md) 를 read.
- Step 1: k3d cluster list (또는 k3s legacy 면 namespace) 검사
- Step 2: CLUSTER_EXISTS=1 일 때 AskUserQuestion 카드
- Step 3: 선택별 분기 (Phase 5/10 점프 / Phase 1 복귀 / 삭제 후 진행 / idempotent)
- Step 4: 다중 testbed 동시 운영 시 port 충돌 사전 점검

### [Phase 5] Lock 획득 (cluster 단위)

target_host + cluster_name 확정됐으니 [references/concurrency-lock.md](references/concurrency-lock.md) 의 flock 획득. lock key 는 `<target_host>_<cluster_name>` — 같은 호스트의 **다른** testbed 는 동시 빌드 가능 (k3d cluster 단위 격리), 같은 cluster 의 동시 빌드만 차단.

```bash
LOCK_KEY="${TARGET_HOST}_${CLUSTER_NAME}"
LOCK_FILE="$HOME/.testbed-build/.locks/${LOCK_KEY}.lock"
exec 200>"$LOCK_FILE"
flock -n 200 || { echo "FATAL: 이미 ${LOCK_KEY} 빌드 진행 중"; exit 1; }
```

### [Phase 6] Services-Author (조건부 — 새 testbed 생성 시만)

interview.app.is_new_variant=true (옵션 3 선택) 인 경우만 dispatch. 기존 testbed (plopvape-shop 등) 이면 skip.

상세: [references/services-author-task.md](references/services-author-task.md)

```bash
TESTBED_DIR="${TESTBED_SVC_REPO}/${INTERVIEW_TESTBED_NAME}"
if [ "$IS_NEW_VARIANT" = "true" ] && [ ! -d "$TESTBED_DIR" ]; then
  TASK_PROMPT=$(render_task_spec services-author-task.md)

  RESULT=$(claude_invoke_agent --type testbed-engineer --prompt "$TASK_PROMPT")

  VERDICT=$(jq -r '.verdict' <<< "$RESULT")
  case "$VERDICT" in
    ok)
      # scenario_hints 보존 → Phase 10 (generate-scenarios) 가 사용
      yq -i ".scenario_hints = $(jq -c '.scenario_hints' <<< "$RESULT")" \
        "$HOME/.testbed-build/runs/$RUN_ID/manifest.yaml"

      PR_URL=$(jq -r '.pr_url // empty' <<< "$RESULT")
      [ -n "$PR_URL" ] && {
        echo "PR 생성: $PR_URL"
        echo "PR 머지 후 Phase 7 진행. [Y/wait/n]"
        # wait 선택 시 60초마다 폴링
      }
      update_manifest_phase "services_author" "completed"
      ;;
    conflict|build-failed|auth-failed|unknown)
      echo "[services-author] verdict=$VERDICT"
      jq <<< "$RESULT"
      update_manifest_phase "services_author" "failed"
      exit 1
      ;;
  esac
else
  echo "[phase 6] services-author skip (기존 testbed 또는 디렉토리 이미 존재)"
  update_manifest_phase "services_author" "skipped"
fi
```

### [Phase 7] Dynamic inventory 생성

[references/dynamic-inventory-generator.md](references/dynamic-inventory-generator.md) 가이드 따라:
- 인터뷰 답 + bootstrap 자격증명 → `runs/<RUN_ID>/inventory.yml` 작성
- [arm64-sample.yml](../../infra/testbed/playbooks/inventory/arm64-sample.yml) 또는 [amd64-sample.yml] 형식 mimic
- [group_vars/all.yml](../../infra/testbed/playbooks/group_vars/all.yml) 의 변수 모두 채움 (collector hosts / org id / app subdir / namespace / agent flags / 등)
- 새 testbed 생성 (Phase 6 = completed) 인 경우 `app_subdir` 와 `app_branch` 가 새로 생성된 디렉토리/브랜치를 가리키도록 설정

### [Phase 8] ansible-playbook 실행 + 실패 진단

site.yml 의 7 roles 모두 자동 실행: common / agent-wpm / agent-apm / service-k8s / agent-kcm / agent-sms / **scenario-runner**. 마지막 scenario-runner role 이 rca-scenario-runner 를 타겟에 git clone + docker-compose 배포 — 사용자가 별도 ssh 들어갈 필요 X.

[references/ansible-failure-diagnosis.md](references/ansible-failure-diagnosis.md) 절차:

```bash
LOG_PATH="$HOME/.testbed-build/runs/$RUN_ID/deploy.log"
INVENTORY="$HOME/.testbed-build/runs/$RUN_ID/inventory.yml"
PLAYBOOK_DIR=$(<plugin_root>)/infra/testbed/playbooks
cd "$PLAYBOOK_DIR"
ansible-playbook -i "$INVENTORY" site.yml > "$LOG_PATH" 2>&1 &
ANSIBLE_PID=$!
```

`run_in_background` 으로 진행 (예상 15~25분). 사용자에게 progress 안내.

종료 후:
- exit 0 → phase complete
- exit != 0 → Agent: testbed-engineer 호출
  ```
  Agent({
    subagent_type: "testbed-engineer",
    prompt: "log_path: $LOG_PATH 진단. verdict + cause + fix + severity 4 필드 반환."
  })
  ```
  결과를 사용자에게 표시 + severity=blocking 이면 종료, recoverable 이면 재시도 prompt.

### [Phase 9] Polestar10 6종 자원 등록

agent install 직후의 standby polling delay (60초) + 자원별 dispatch + PARTIAL verdict 처리.

**상세 절차**: [references/polestar10-register-flow.md](references/polestar10-register-flow.md) 를 read.
- 9-a 사전 점검: organization_id 확인 + broker/collector 도달성 + 60초 grace period
- 9-b dispatch: testbed-polestar10-register 시나리오 1 (WPM/OTel/DPM/NMS 자동 분기)
- 9-c PARTIAL 처리: 자원별 등록 표 + 사용자 분기 (진행 / 재시도 / 중단)

### [Phase 10] 시나리오 생성

```
Skill: testbed-generate-scenarios
  testbed_name: <interview answer>
  count: 4 (default — 4종 패턴 mirror)
  push_mode: pr
  scenario_hints: <Phase 6 산출 — 새 testbed 생성 시 새 코드의 schema/endpoint 매핑>
```

scenario_hints 가 있으면 generate-scenarios 가 LLM 인터뷰 없이 직접 변수 채움 (lock_table, lock_endpoint, external_container 등).

산출: `runs/<RUN_ID>/scenarios.json` (생성된 파일 목록 + 각 expected_alarms).

### [Phase 11] 알람 정책

```
Skill: testbed-tune-alarms
  target_scope: <testbed_name>
  domain_filter: all
  mode: apply (사용자 승인 후 등록)
```

산출: `runs/<RUN_ID>/alarms.json` (등록된 정책 목록).

### [Phase 12] Closed-loop verify (오케스트레이터 레벨 재시도)

[references/verify-task.md](references/verify-task.md) 의 task spec 으로 testbed-verifier agent 호출.

**재시도 시 PASS 시나리오 skip** — 이전 attempt 에서 PASS 였던 시나리오는 재실행 X (시나리오당 5~8분 절약). missed/spurious 시나리오만 재검증. 시나리오 격리 가정 (cleanup 이 다른 시나리오에 영향 X) 에 의존.

```bash
ATTEMPT=1
MAX_ATTEMPTS=3
SCENARIOS_TO_VERIFY="all"   # 첫 attempt 는 전체

while [ "$ATTEMPT" -le "$MAX_ATTEMPTS" ]; do
  echo "[verify] attempt $ATTEMPT/$MAX_ATTEMPTS — scenarios=$SCENARIOS_TO_VERIFY"

  # Agent 호출 (verify-task.md 의 scenarios_to_verify 슬롯 사용)
  VERDICT=$(call testbed-verifier with task scenarios=$SCENARIOS_TO_VERIFY)
  jq -r '.overall' <<< "$VERDICT"

  if [ "$(jq -r '.overall' <<< "$VERDICT")" = "PASS" ]; then
    break
  fi
  if [ "$ATTEMPT" -eq "$MAX_ATTEMPTS" ]; then
    echo "[verify] max attempts 도달. PARTIAL/FAIL 결과로 finalize 진행."
    break
  fi

  # PARTIAL/FAIL → tune-alarms 재호출
  echo "[verify] FAIL/PARTIAL. testbed-tune-alarms 재호출 (recommendations 기반)"
  call testbed-tune-alarms with verdict.recommendations

  # 다음 attempt 는 PASS 가 아닌 시나리오만 재실행 (PASS 시나리오 skip — 시간 절약)
  SCENARIOS_TO_VERIFY=$(echo "$VERDICT" | jq -r '
    [ .scenarios[] | select(.verdict != "PASS") | .id ] | join(",")
  ')
  [ -z "$SCENARIOS_TO_VERIFY" ] && SCENARIOS_TO_VERIFY="all"   # safety fallback

  ATTEMPT=$((ATTEMPT+1))
done
```

각 attempt 의 verdict + 재튜닝 내역 → `runs/<RUN_ID>/verify.log`.

⚠️ **PASS skip 안전장치**: 한 시나리오의 cleanup 이 다른 시나리오에 부작용 (예: K3s pod 재기동으로 다른 시나리오의 메트릭 기준 변동) 이 있으면 skip 시 false-negative 가능. 다음 라운드에 의심 발생 시 `SCENARIOS_TO_VERIFY="all"` 강제 (전체 재실행) 옵션 사용.

### [Phase 13] Finalize (인라인)

[references/finalize-report-template.md](references/finalize-report-template.md) 템플릿:
- architecture.md 본문
- register.json 의 6종 자원 표
- alarms.json 의 정책 표
- verify.log 의 최종 verdict 요약
- learnings.md append (반복 이슈 hook — 본 세션은 placeholder)

산출: `~/.testbed-build/reports/<RUN_ID>-<testbed_name>.md`.

### [Phase 14] Cleanup — 시점 따라 사용자 prompt

run 종료 시점에 따라 산출물 / 외부 자원 정리 범위가 달라집니다. **finalize=completed (정상 종료)** 케이스는 [references/state-schema.md](references/state-schema.md) 의 자동 정리 룰 그대로 (run dir 삭제 + report 영구 보존). **사용자 cancel 또는 phase failed** 케이스는 다음 사용자 prompt 로 정리 범위를 사용자가 결정합니다.

진행된 phase 까지 추적하여 어디까지 cleanup 가능한지 표시:

```python
# 진행 시점 식별
last_phase = max([p for p, s in manifest.phases.items() if s == "completed"])

# 시점 별 cleanup 옵션
options = []
if last_phase >= "services_author":
    options.append({
        "label": "services-author 산출물 정리 (Recommended for cancel)",
        "description": "testbed-services 레포의 신규 branch close + (PR 머지된 경우) revert PR 자동 발행. main 의 새 디렉토리는 사용자 결정 후 별도 PR."
    })
if last_phase >= "ansible_deploy":
    options.append({
        "label": "ansible 배포 자원 정리",
        "description": "타겟 서버에 깔린 K3s namespace 삭제 + /opt/<namespace> 디렉토리 정리 + rca-scenario-runner 컨테이너 stop. K3s 자체는 유지 (다른 testbed 사용 가능)."
    })
if last_phase >= "polestar10_register":
    options.append({
        "label": "Polestar10 자원 정리",
        "description": "testbed-polestar10-register 의 시나리오 4 (자원 삭제 + 재출현 가드) 자동 호출. 6종 자원 모두 Polestar10 backend 에서 제거."
    })

options.append({
    "label": "정리 안 함 (run 디렉토리만 보존)",
    "description": "현재 상태 그대로 두고 run 디렉토리 (~/.testbed-build/runs/<ts>/) 만 보존. 사용자가 직접 분석 후 수동 정리. resume 시 이어서 진행 가능."
})

AskUserQuestion(questions=[
  {
    "question": "현재까지 phase 진행 상황을 보여드렸습니다. 어디까지 cleanup 을 진행할지 선택해 주세요. 진행한 phase 별로 정리 가능한 범위가 달라집니다. 보수적으로 가시려면 마지막 옵션 (정리 안 함) 을 고르시면 모든 자원이 그대로 보존되어 사용자가 직접 분석 후 결정할 수 있습니다.",
    "header": "Cleanup 범위",
    "multiSelect": True,
    "options": options
  }
])
```

선택된 옵션들 순차 실행. 각 단계 실행 결과 사용자에게 표시. 실패 시 해당 단계만 보존 + 다음 단계 진행.

```bash
flock -u "$LOCK_FD"
rm -f "$HOME/.testbed-build/.locks/$TARGET_HOST.lock"
mv "$HOME/.testbed-build/runs/$RUN_ID/manifest.yaml" \
   "$HOME/.testbed-build/runs/$RUN_ID/manifest-completed.yaml"
# (선택) zip archive
# rm -rf "$HOME/.testbed-build/runs/$RUN_ID"
```

manifest.phases.finalize=completed 이면 안전하게 runs 정리. 실패 케이스는 보존.

---

## Polestar10 에러 처리 표준 패턴

[references/polestar10-error-handling.md](references/polestar10-error-handling.md) 참조.

요지: API error 면 ask-polestar10 호출 → 매뉴얼 답변 → 자동 1회 재시도 → 그래도 실패 시 사용자 안내. Network error (connection refused / timeout) 는 ask-polestar10 우회하고 인프라 점검 안내.

---

## 단독 호출 권장

다음 작업은 testbed-build 통과시키지 말고 직접 호출 권장:
- 시나리오 추가: `/testbed-generate-scenarios`
- 알람 재튜닝: `/testbed-tune-alarms`
- Polestar10 자원 정리: `/testbed-polestar10-register` (시나리오 4: cleanup)
- 매뉴얼 검색: `/ask-polestar10`

---

## Resources

- [bootstrap.md](references/bootstrap.md) — 자격증명 + 레포 경로 부트스트랩 + clone
- [interview-flow.md](references/interview-flow.md) — 4단계 인터뷰 질문지
- [architecture-template.md](references/architecture-template.md) — 아키텍처 v1 markdown 템플릿
- [state-schema.md](references/state-schema.md) — `~/.testbed-build/` 디렉토리 레이아웃
- [phase-checkpoint.md](references/phase-checkpoint.md) — manifest.yaml + resume 룰
- [concurrency-lock.md](references/concurrency-lock.md) — flock 패턴
- [dynamic-inventory-generator.md](references/dynamic-inventory-generator.md) — inventory.yml 동적 생성
- [ansible-failure-diagnosis.md](references/ansible-failure-diagnosis.md) — testbed-engineer 위임 패턴
- [polestar10-error-handling.md](references/polestar10-error-handling.md) — 표준 에러 처리
- [verify-task.md](references/verify-task.md) — testbed-verifier task spec
- [services-author-task.md](references/services-author-task.md) — Phase 2 placeholder
- [finalize-report-template.md](references/finalize-report-template.md) — 보고서 템플릿

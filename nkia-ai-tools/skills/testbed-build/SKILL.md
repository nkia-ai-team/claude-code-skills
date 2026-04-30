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
- 신규 도메인 변형 (옵션 3) 선택 시 testbed-engineer agent 가 testbed-services 레포에 코드 자동 생성 + git PR (Phase 6)

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

핵심:
- 없으면 인터뷰 (SSH 자격증명 / Polestar10 자격증명 / git PAT / 레포 경로 default `~/dev/`)
- chmod 600 으로 영구 저장
- 다음 호출부터 묻지 X (값 변경 시 사용자가 직접 yaml 편집)

### 3. 외부 레포 부재 시 git clone
```bash
TESTBED_SVC_REPO=$(grep '^testbed_services_repo:' ~/.testbed-build/bootstrap.yaml | awk '{print $2}')
RUNNER_REPO=$(grep '^scenario_runner_repo:' ~/.testbed-build/bootstrap.yaml | awk '{print $2}')

[ -d "$TESTBED_SVC_REPO/.git" ] || {
  echo "testbed-services 레포가 없습니다. clone 진행합니다."
  git clone https://github.com/BangSungjoon/testbed-services.git "$TESTBED_SVC_REPO"
}
[ -d "$RUNNER_REPO/.git" ] || {
  echo "rca-scenario-runner 레포가 없습니다. clone 진행합니다."
  git clone https://github.com/BangSungjoon/rca-scenario-runner.git "$RUNNER_REPO"
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

### [Phase 2] Polestar10 연결 사전 체크

[references/polestar10-error-handling.md](references/polestar10-error-handling.md) 의 connectivity precheck 절차:

```bash
curl -sS -m 10 "$POLESTAR10_BASE_URL/api/sso/preLogin" >/dev/null \
  || { echo "Polestar10 연결 실패. 점검 후 재시도."; exit 1; }
```

실패 시 ask-polestar10 호출 + 사용자 안내 후 phase 미완 상태로 종료.

### [Phase 3] Architecture-draft (인라인)

[references/architecture-template.md](references/architecture-template.md) 템플릿 변수 채우기:
- 인터뷰 답으로 mermaid 다이어그램 자동 생성
- 6종 에이전트 표 + 알람 정책 자리 (8단계 후 채워짐)
- 시나리오 자리 (7단계 후 채워짐)

산출: `runs/<RUN_ID>/architecture.md`. 사용자에게 표시.

### [Phase 4] 사용자 승인 ⛔

```
=== 아키텍처 v1 ===
<architecture.md 내용>

이대로 진행? [Y/n/edit]
```

`edit` 시 사용자가 architecture.md 직접 편집 후 다시 prompt. `n` 시 phase 미완 상태로 종료.

### [Phase 5] Lock 획득

target_host 확정됐으니 [references/concurrency-lock.md](references/concurrency-lock.md) 의 flock 획득.

### [Phase 6] Services-Author (조건부 — 신규 변형 시만)

interview.app.is_new_variant=true (옵션 3 선택) 인 경우만 dispatch. 기존 변형 (plopvape-shop 등) 이면 skip.

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
  echo "[phase 6] services-author skip (기존 변형 또는 디렉토리 이미 존재)"
  update_manifest_phase "services_author" "skipped"
fi
```

### [Phase 7] Dynamic inventory 생성

[references/dynamic-inventory-generator.md](references/dynamic-inventory-generator.md) 가이드 따라:
- 인터뷰 답 + bootstrap 자격증명 → `runs/<RUN_ID>/inventory.yml` 작성
- [arm64-sample.yml](../../infra/testbed/playbooks/inventory/arm64-sample.yml) 또는 [amd64-sample.yml] 형식 mimic
- [group_vars/all.yml](../../infra/testbed/playbooks/group_vars/all.yml) 의 변수 모두 채움 (collector hosts / org id / app subdir / namespace / agent flags / 등)
- 신규 변형 (Phase 6 = completed) 인 경우 `app_subdir` 와 `app_branch` 가 새로 생성된 디렉토리/브랜치를 가리키도록 설정

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

```
Skill: testbed-polestar10-register
  scenario: 1 (full testbed)
  context: runs/<RUN_ID>/inventory.yml + interview.yaml
```

Polestar10 자원 등록 결과 → `runs/<RUN_ID>/register.json`. Polestar10 에러 시 표준 패턴.

### [Phase 10] 시나리오 생성

```
Skill: testbed-generate-scenarios
  testbed_name: <interview answer>
  count: 4 (default — 4종 패턴 mirror)
  push_mode: pr
  scenario_hints: <Phase 6 산출 — 신규 변형인 경우 새 코드의 schema/endpoint 매핑>
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

```bash
ATTEMPT=1
MAX_ATTEMPTS=3
while [ "$ATTEMPT" -le "$MAX_ATTEMPTS" ]; do
  echo "[verify] attempt $ATTEMPT/$MAX_ATTEMPTS"
  # Agent 호출
  VERDICT=$(call testbed-verifier with task)
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
  ATTEMPT=$((ATTEMPT+1))
done
```

각 attempt 의 verdict + 재튜닝 내역 → `runs/<RUN_ID>/verify.log`.

### [Phase 13] Finalize (인라인)

[references/finalize-report-template.md](references/finalize-report-template.md) 템플릿:
- architecture.md 본문
- register.json 의 6종 자원 표
- alarms.json 의 정책 표
- verify.log 의 최종 verdict 요약
- learnings.md append (반복 이슈 hook — 본 세션은 placeholder)

산출: `~/.testbed-build/reports/<RUN_ID>-<testbed_name>.md`.

### [Phase 14] Cleanup

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

# Ansible 배포 + 실패 진단 — testbed-deployer agent dispatch 패턴

`ansible_deploy` 의 dispatch 표준. orchestrator 는 ansible-playbook 을 직접 호출 X —
testbed-deployer agent 에게 위임. agent 가 단일 호출에서 run + 로그 캡처 + 진단까지
통합 처리.

이유: ansible 로그 (수만 줄, 수십 MB) 를 parent context 에 유입시키지 않음. agent 가 fork context 에서 처리 후 verdict JSON 만 리턴.

## Dispatch

⚠️ **`<plugin_root>` resolution**: orchestrator 가 dispatch 시 `$CLAUDE_PLUGIN_ROOT` (Claude Code env var) 또는 marketplace cache glob fallback 으로 실제 경로 결정. 사용자 dev clone 경로 직접 박기 금지. 자세한 패턴: [bootstrap.md § Plugin install 경로 발견](bootstrap.md).

```
Agent: testbed-deployer
input (yaml):
  task: ansible-deploy
  inventory_path: "$HOME/.testbed-build/runs/$RUN_ID/inventory.yml"
  playbook_path:  "${CLAUDE_PLUGIN_ROOT}/infra/testbed/playbooks/site.yml"   # bootstrap.md § Plugin install 경로 발견 패턴 따라 resolution
  run_id:         "$RUN_ID"
  log_dir:        "/tmp/testbed-build/$RUN_ID"
  timeout_sec:    1800   # 30분
  extra_vars:
    polestar10_collector_host: <bootstrap.polestar10.collector_host>
    polestar_organization_id:  <bootstrap.polestar10.organization_id>
    # ... 그 외 inventory override

  env:
    TESTBED_PASSWORD: "<ssh password, password auth 일 때만>"
    TESTBED_BECOME_PASSWORD: "<sudo password, 필요 시>"
    TESTBED_SSH_KEY: "<ssh key path, key auth 일 때만>"
```

`env` 값은 verdict JSON / deploy.log / diagnosis.log 에 출력하지 않는다. testbed-deployer 는
위 env 를 ansible-playbook process 에만 전달한다.

Agent 가 internally:
1. log_dir 준비
2. ansible-playbook 실행 (timeout 가드)
3. PLAY RECAP 파싱 (failed/unreachable/changed/ok 카운트)
4. 실패면 첫 fatal 위치 + 30줄 컨텍스트 + 패턴 라이브러리 매칭
5. 표준 verdict JSON 리턴

자세한 절차 + 패턴 라이브러리: [agents/testbed-deployer.md](../../../agents/testbed-deployer.md)

## Verdict 처리 (orchestrator 측)

```bash
VERDICT=$(jq -r '.verdict' <<< "$VERDICT_JSON")
NEXT_ACTION=$(jq -r '.next_action' <<< "$VERDICT_JSON")
SUMMARY=$(jq -r '.summary' <<< "$VERDICT_JSON")
```

| verdict | next_action | orchestrator 동작 |
|---|---|---|
| `ok` | `proceed` | manifest `ansible_deploy.status=completed` → `sanity_check` 진행 |
| `warn` | `proceed` | manifest `ansible_deploy.status=completed_with_warnings` → `sanity_check` 진행 |
| `fail` (severity=recoverable) | `retry` | 사용자 prompt: "fix 적용 후 재시도?" → yes 면 retry counter (max 2) |
| `fail` (severity=blocking) | `user-decision` | 사용자에게 cause + fix 표시 + run 보존하고 종료 (resume 가능) |
| `skipped` | `user-decision` | 사전 조건 미충족 안내 |

## 자동 retry 룰 (recoverable 만)

```bash
RETRY=0
while [ $RETRY -lt 2 ]; do
  VERDICT_JSON=$(invoke testbed-deployer ...)
  VERDICT=$(jq -r '.verdict' <<< "$VERDICT_JSON")
  [ "$VERDICT" = "ok" ] && break
  SEVERITY=$(jq -r '.errors[0].severity // "blocking"' <<< "$VERDICT_JSON")
  [ "$SEVERITY" = "blocking" ] && break

  read -r -p "$(jq -r '.errors[0].fix' <<< "$VERDICT_JSON") 적용 후 재시도? [Y/n] " ANS
  [ "$ANS" = "n" ] && break
  RETRY=$((RETRY+1))
done
```

blocking 은 자동 retry X — 사용자 결정 필수. recoverable 만 max 2회 retry.

## 🚫 자동 disable 금지 룰

testbed-deployer agent 의 verdict 에 KCM/WPM/APM/SMS 비활성 (`<agent>_enabled=false`) 권고가 와도 orchestrator 가 **자동으로 inventory 수정 X**. 반드시 AskUserQuestion 카드로 사용자 명시 승인 받기.

이유: 에이전트 비활성 = RCA 검증 자원 범위 축소. 사용자 의도와 무관하게 LLM 이 결정하면 ansible 은 통과해도 사용자가 의도한 RCA 검증을 못 함.

KCM ARM source-build 자격증명 누락 같은 케이스는 [kcm-arm64-setup.md](kcm-arm64-setup.md) 의 사용자 인터뷰 흐름으로.

## Polestar10 에이전트 설치 실패 분기

verdict 의 errors[].fix 가 `ask-polestar10` 호출 권고면 (예: SMS install 시 POLESTAR_ORG_ID 미설정, KCM source clone auth 실패):

```
agent 권고: ask-polestar10 호출 권장
자동 호출할까요? [Y/n]
```

yes → ask-polestar10 trigger → 매뉴얼 답변 + 사용자 안내. 그 후 사용자 선택에 따라 retry 또는 종료.

## 로그 archive

deploy.log 는 testbed-deployer agent 가 `/tmp/testbed-build/<run_id>/deploy.log` 에 저장. orchestrator 는 verdict.outputs.log_path 만 안고, 사용자가 필요 시 직접 read.

`finalize` 단계에서 gzip 또는 tail -1000 만 보존 (디스크 절약).

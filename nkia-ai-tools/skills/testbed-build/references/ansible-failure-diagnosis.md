# Ansible 실패 진단 — testbed-engineer 위임 패턴

Phase 7 (ansible-playbook) 실패 시 동작.

## 실행 + 로그 캡처

```bash
LOG_PATH="$HOME/.testbed-build/runs/$RUN_ID/deploy.log"
INVENTORY="$HOME/.testbed-build/runs/$RUN_ID/inventory.yml"
PLAYBOOK_DIR="<plugin_root>/infra/testbed/playbooks"

cd "$PLAYBOOK_DIR"

# stdout + stderr 한 파일로. ansible 자체는 -v 정도 권고 (지나친 verbosity 는 trace 폭증).
ansible-playbook -i "$INVENTORY" site.yml -v > "$LOG_PATH" 2>&1 &
ANSIBLE_PID=$!

# 주기적 진행 안내 (사용자가 25분 동안 무응답이면 불안)
echo "[ansible] PID=$ANSIBLE_PID 시작. 예상 15~25분."
echo "[ansible] log: $LOG_PATH"

# 60초마다 마지막 라인 표시
while kill -0 "$ANSIBLE_PID" 2>/dev/null; do
  sleep 60
  TAIL=$(tail -3 "$LOG_PATH" 2>/dev/null)
  echo "[ansible] (still running) ... $(date +%H:%M:%S)"
  echo "$TAIL" | sed 's/^/  | /'
done

wait "$ANSIBLE_PID"
EXIT_CODE=$?
echo "[ansible] exit=$EXIT_CODE"
```

## Exit code 처리

### exit=0 (성공)

```bash
update_manifest_phase "ansible_deploy" "completed"
# next phase
```

### exit != 0 (실패)

testbed-engineer agent 위임:

```bash
update_manifest_phase "ansible_deploy" "failed"

# Agent 호출
VERDICT_JSON=$(claude_invoke_agent \
  --type "testbed-engineer" \
  --prompt "$(cat <<EOF
task: ansible-failure-diagnosis
log_path: $LOG_PATH
inventory: $INVENTORY
target_arch: $TARGET_ARCH
expected_roles: [common, agent-wpm, agent-apm, service-k8s, agent-kcm, agent-sms]

위 로그를 분석하여 verdict / cause / fix / severity / log_excerpt / patterns_matched 5 필드 JSON 반환.
EOF
)")
```

> 실제 호출 메커니즘: Claude Code 의 Agent 도구 (Skill 컨텍스트에서 invoke 가능). 위 pseudo-code 는 의미만.

## Verdict 처리

```bash
VERDICT=$(jq -r '.verdict' <<< "$VERDICT_JSON")
SEVERITY=$(jq -r '.severity' <<< "$VERDICT_JSON")
CAUSE=$(jq -r '.cause' <<< "$VERDICT_JSON")
FIX=$(jq -r '.fix' <<< "$VERDICT_JSON")

# 사용자에게 표시
cat <<EOF
=== Ansible 실패 진단 ===
verdict:  $VERDICT
severity: $SEVERITY
cause:    $CAUSE
fix:      $FIX

상세 로그: $LOG_PATH
EOF
```

### severity=blocking

사용자 개입 필요 (sshpass 설치, 자격증명, 권한 등).
```
조치 후 testbed-build 재실행. resume 으로 phase 7 부터 이어집니다.
```
phase 종료 (run 보존). exit 1.

### severity=recoverable

transient 또는 자동 fix 가능. 사용자 prompt:
```
이 fix 를 자동 적용하고 ansible 재실행할까요? [Y/n]
```
yes → fix 명령 실행 → ansible-playbook 재호출 → 다시 verdict

> 🚫 **자동 disable 금지 룰**: testbed-engineer agent 가 KCM / WPM / APM / SMS 같은 에이전트를 자동으로 비활성 (`<agent>_enabled=false`) 으로 결정하는 fix 는 절대 금지. 에이전트 비활성은 RCA 검증 범위 축소 → 사용자 명시 승인 필수. 사용자가 인터뷰에서 직접 "비활성" 옵션을 선택하지 않았는데 LLM 이 fail-fast 후 알아서 disable 처리하면 ansible 은 통과하지만 사용자가 의도한 RCA 검증을 못 함.
>
> KCM 빌드 실패 케이스: 자격증명 누락 / GitLab 도달 X / 빌드 prereq 부족 등은 모두 사용자 인터뷰로 해결할 영역. testbed-engineer 가 verdict 에 fix 권고를 적되, 실제 inventory 수정 / kcm_enabled 변경은 **사용자에게 별 AskUserQuestion 카드로 묻고** 진행.

```bash
if [ "$SEVERITY" = "recoverable" ]; then
  read -r -p "fix 적용 후 재시도? [Y/n] " ANS
  if [ "$ANS" != "n" ]; then
    eval "$FIX" || echo "fix 실패. 수동 조치 권고."
    # 재시도 카운터 (max 2 — 무한 루프 방지)
    RETRY=$((RETRY+1))
    if [ "$RETRY" -le 2 ]; then
      goto ansible_retry
    else
      echo "max retry. 수동 조치 권고."
    fi
  fi
fi
```

## verdict=unknown 시

알려진 패턴 매칭 안 됨. agent 의 추론 답변 그대로 사용자에게 표시 + ask-polestar10 우회 (이건 ansible/SSH 영역, Polestar10 매뉴얼 무관).

```
verdict: unknown
cause: <agent 추론>
fix: <agent 권고>
log_excerpt: |
  TASK [common : install metrics-server] ******
  fatal: [arm64-target]: FAILED! => {"changed": false, "msg": "..."}

상세 로그 확인 후 수동 조치 권고:
  $LOG_PATH

도움이 필요하면 NKIAAI-540 의 README "Caveats — 알려진 한계" 섹션 참조.
```

## Polestar10 에이전트 설치 실패 분기

agent 의 verdict 가 Polestar10 자격증명 또는 매뉴얼 영역이면 (예: SMS install 시 POLESTAR_ORG_ID 미설정, KCM ARM 빌드 prereq 누락) — agent 가 자체적으로 ask-polestar10 권고 포함.

오케스트레이터는 그 권고를 보고 ask-polestar10 자동 호출 옵션 제공:
```
agent 권고: ask-polestar10 호출 권장
자동 호출할까요? [Y/n]
```
yes → ask-polestar10 trigger → 매뉴얼 답변 + 사용자 안내 후 phase 종료.

## 로그 archive

deploy.log 가 거대 (수만 줄) 일 수 있음. 정상 완료 시 gzip:
```bash
gzip "$LOG_PATH"   # phase 12 finalize 단계에서
# 또는 tail -1000 만 보존
```

## 디버깅 모드

사용자가 `TESTBED_BUILD_VERBOSE=1` env 로 호출하면 ansible -vvv (디테일 trace). 일반은 -v 만 (고급 디버깅용).

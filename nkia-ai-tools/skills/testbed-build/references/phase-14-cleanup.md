# Phase 14 — Cleanup (시점별 사용자 선택)

run 종료 시점에 따라 산출물 / 외부 자원 정리 범위가 달라짐.

## 두 가지 종료 케이스

### A. finalize=completed (정상 종료)

[state-schema.md](state-schema.md) 의 자동 정리 룰 그대로:
- run dir 정리: `manifest.yaml` → `manifest-completed.yaml` 로 rename
- report 영구 보존: `~/.testbed-build/reports/<RUN_ID>-<testbed_name>.md`
- (옵션) zip archive 후 run dir 삭제

```bash
flock -u "$LOCK_FD"
rm -f "$HOME/.testbed-build/.locks/${LOCK_KEY}.lock"
mv "$HOME/.testbed-build/runs/$RUN_ID/manifest.yaml" \
   "$HOME/.testbed-build/runs/$RUN_ID/manifest-completed.yaml"
# (선택) tar -czf archive ...
```

### B. 사용자 cancel 또는 phase failed

진행된 phase 까지 추적 → 사용자 prompt 로 cleanup 범위 결정.

## 진행 시점 식별

```bash
last_phase=$(yq '.phases | to_entries | map(select(.value == "completed")) | .[-1].key' \
  "$HOME/.testbed-build/runs/$RUN_ID/manifest.yaml")
```

## Cleanup 옵션 매트릭스

| last_phase 도달 | 옵션 | 영향 범위 |
|---|---|---|
| `services_author` 이상 | services-author 산출물 정리 | testbed-services 레포의 신규 branch close + (PR 머지된 경우) revert PR. main 의 새 디렉토리는 사용자 결정 후 별도 PR. |
| `ansible_deploy` 이상 | ansible 배포 자원 정리 | 타겟 서버에 깔린 K3s namespace 삭제 + /opt/<namespace> 디렉토리 정리 + rca-scenario-runner 컨테이너 stop. K3s 자체는 유지 (다른 testbed 사용 가능). |
| `polestar10_register` 이상 | Polestar10 자원 정리 | testbed-polestar10-register 의 시나리오 4 (자원 삭제 + 재출현 가드) 자동 호출. KCM/APM/WPM/SMS/DPM/NMS 모두 backend 에서 제거. |
| 항상 | 정리 안 함 | 현재 상태 그대로 + run dir 보존. resume 시 이어서 진행 가능. |

## AskUserQuestion 카드

```python
options = []
if last_phase >= "services_author":
    options.append({
        "label": "services-author 산출물 정리 (Recommended for cancel)",
        "description": "testbed-services 레포의 신규 branch close + (PR 머지된 경우) revert PR 자동 발행. main 의 새 디렉토리는 사용자 결정 후 별도 PR."
    })
if last_phase >= "ansible_deploy":
    options.append({
        "label": "ansible 배포 자원 정리",
        "description": "타겟 서버에 깔린 K3s namespace 삭제 + /opt/<namespace> 디렉토리 정리 + rca-scenario-runner 컨테이너 stop. K3s 자체는 유지."
    })
if last_phase >= "polestar10_register":
    options.append({
        "label": "Polestar10 자원 정리",
        "description": "testbed-polestar10-register 시나리오 4 자동 호출. 등록된 6종 관리대상 모두 제거."
    })
options.append({
    "label": "정리 안 함 (run 디렉토리만 보존)",
    "description": "현재 상태 그대로 두고 run 디렉토리만 보존. 사용자가 직접 분석 후 수동 정리. resume 가능."
})

AskUserQuestion(questions=[{
    "question": "cleanup 범위를 선택해 주세요. 진행한 phase 별로 정리 가능한 범위가 달라집니다. 보수적으로 가시려면 마지막 옵션 (정리 안 함) 을 고르시면 모든 자원이 그대로 보존되어 직접 분석 가능합니다.",
    "header": "Cleanup 범위",
    "multiSelect": True,
    "options": options
}])
```

## 실행

선택된 옵션들 순차 실행. 각 단계 결과 사용자에게 표시. 실패 시 해당 단계만 보존하고 다음 단계 진행 (전체 abort X).

### 🚫 destructive action chat 승인 룰 (강제)

cleanup 의 모든 destructive 명령 (`kubectl delete ns`, `helm uninstall`, `k3d cluster delete`, `gh pr close`, `git push --force`) 은 AskUserQuestion 카드 응답으로는 **권한 시스템이 승인 X**. 카드로 옵션 선택 받은 후, 실제 destructive bash 실행 직전에 한 번 더 자연어 chat prompt:

```
선택하신 cleanup 옵션을 실행합니다. 진행할까요?
  - services-author branch close (gh pr close 포함)
  - K3s namespace delete

응답해 주세요 (예: "응 진행", "확인", "취소").
```

사용자 자연어 응답 받은 후만 실행.

## 마무리

```bash
flock -u "$LOCK_FD" 2>/dev/null
rm -f "$HOME/.testbed-build/.locks/${LOCK_KEY}.lock"
```

manifest.phases.finalize=completed 이면 안전하게 runs 정리. 실패 케이스는 보존 (resume 가능).

---
name: testbed-generate-scenarios
description: RCA 테스트베드에 장애 시나리오를 추가/생성. `infra/testbed/scenario-patterns/` 카탈로그에서 패턴 선택 → bash 스크립트 인스턴스화 → service-spec.yaml 갱신 → rca-scenario-runner 레포 PR/push. 사용자가 "시나리오 추가해줘", "장애 시나리오 만들어줘", "/testbed-generate-scenarios", "<service> 에 N개 시나리오 추가" 같은 요청 시 트리거. testbed-build 의 7번 단계가 이를 dispatch.
---

# testbed-generate-scenarios

## Overview

이 스킬은 **dispatcher**. 직접 코드 작성 X — `infra/testbed/scenario-patterns/` 의 패턴 카드를 read → service-spec.yaml 의 메타와 결합 → bash 스크립트 + yaml entry 작성 → rca-scenario-runner 레포에 commit + push.

핵심 아이디어: 패턴 = 템플릿 (변수 치환 자리), 인스턴스화 = 특정 testbed 의 메타로 변수 채움.

`testbed-polestar10-register` 와 협업 X (이 스킬은 Polestar10 직접 호출 안 함). Polestar10 알람 매칭은 `testbed-verify` 단계 책임.

---

## 입력 슬롯

| 슬롯 | 자동 결정 | 사용자 인터뷰 |
|---|---|---|
| `testbed_name` | rca-scenario-runner 레포의 `scenarios/services/` 디렉토리 1개면 자동 | 여러 개면 prompt |
| `count` | default 1 (testbed-build 호출 시 4 — failure_surfaces 모두) | "몇 개?" 또는 "auto" (LLM 이 도메인 보고 권고) |
| `pattern` | 후보 카탈로그 prompt | 사용자 선택 또는 "자동" |
| `script_id_prefix` | 기존 service-spec.yaml 마지막 ID + 1 | 변경 가능 |
| `push_mode` | default `pr` | `pr` / `direct-push` / `local-only` |
| `scenario_hints` | testbed-build Phase 6 (services-author) 결과 — 신규 도메인 시 manifest.yaml 에 보존 | 단독 호출 시 X (룩업 표 / 코드 자동 분석 fallback) |

`scenario_hints` 가 있으면 [pattern-to-script.md §4-b](references/pattern-to-script.md) 의 신규 도메인 모드 활성화 — 룩업 표 / 사용자 인터뷰 X. 코드의 실제 schema/endpoint 기반.

---

## CRITICAL: First Step — 환경 탐지

매 호출 첫 단계:

1. **rca-scenario-runner 레포 위치 확인**
   ```bash
   if [ -d "$HOME/dev/rca-scenario-runner/.git" ]; then
     RUNNER_ROOT="$HOME/dev/rca-scenario-runner"
   elif [ -f "$HOME/.testbed-build/bootstrap.yaml" ]; then
     RUNNER_ROOT=$(grep '^scenario_runner_repo:' "$HOME/.testbed-build/bootstrap.yaml" | awk '{print $2}')
   else
     echo "rca-scenario-runner 레포 위치를 모릅니다. 사용자 인터뷰 필요."
   fi
   ```
2. **plugin install root 발견** (scenario-patterns 카탈로그 위치)
   ```
   Glob({pattern: "**/nkia-ai-tools/*/infra/testbed/scenario-patterns/README.md", path: "/"})
   ```
   매치된 첫 절대경로의 디렉토리가 `<patterns_root>`. dev clone 환경에서는 cwd 의 `nkia-ai-tools/infra/testbed/scenario-patterns/` fallback 허용.

3. **레포 부재 시 인터뷰 + git clone**:
   ```
   "rca-scenario-runner 레포가 없습니다. ~/dev/rca-scenario-runner 에 clone 할까요?"
   → yes: git clone https://github.com/BangSungjoon/rca-scenario-runner.git ~/dev/rca-scenario-runner
   ```

---

## Dispatch Flow

### 1. 대상 testbed 결정
```bash
ls "$RUNNER_ROOT/scenarios/services/"
```
1개면 자동, 여럿이면 사용자에게 선택 prompt.

### 2. 패턴 카탈로그 표시
[scenario-patterns/README.md](../../infra/testbed/scenario-patterns/README.md) 의 표 그대로 사용자에게 보여주고 선택 받기. (또는 "자동" → LLM 이 service-spec.yaml 도메인 메타 + 기존 시나리오 목록 보고 미커버 패턴 추천)

### 3. 패턴 카드 → 인스턴스 변환

선택된 패턴 카드 read (예: `<patterns_root>/db-lock-contention.md`). 카드의 `## 변형 포인트` 섹션 변수 들에 대해 사용자 인터뷰 또는 자동 추론:

- service-spec.yaml 의 service.namespace → `NAMESPACE`
- service.api_base → `SERVICE_API`
- 도메인 추론: e-commerce 면 `LOCK_TABLE=inventory` `LOAD_ENDPOINT=/api/orders`
- 인스턴스 시 치환할 placeholder 들 (`<table_name>`, `<row_key>` 등) 채움

**자세한 변환 룰**: [pattern-to-script.md](references/pattern-to-script.md)
**스크립트 골격 변환 가이드**: [script-template.md](references/script-template.md)

### 4. 스크립트 + yaml entry 작성

#### 4-a. bash 스크립트
- 경로: `$RUNNER_ROOT/scenarios/services/<testbed_name>/scripts/scenario-<NN>-<slug>.sh`
- 카드의 "bash 스크립트 골격" 을 변수 치환하여 작성
- `chmod +x`
- 멱등 cleanup + `trap cleanup EXIT` 보장

#### 4-b. service-spec.yaml entry
- 기존 yaml load → `scenarios:` 리스트에 새 항목 append
- 필드: id (`scenario-<NN>`), file, title, description, root_cause, propagation, estimated_duration_sec, expected_alarms (카드의 default), side_effects (있으면)
- yaml dump 시 들여쓰기 보존 — 가능하면 ruamel.yaml 또는 직접 string 추가

> **중요**: rca-scenario-runner 백엔드는 [scenarios.py](https://github.com/BangSungjoon/rca-scenario-runner/blob/develop/backend/app/scenarios.py) 가 service-spec.yaml glob 으로 시나리오 자동 발견. yaml 만 떨어뜨리면 컨테이너 재시작 후 자동 등록.

### 5. 사용자 미리보기 + 승인 ⛔

```
다음 시나리오 추가 예정:

[scripts/scenario-05-memory-leak.sh] (47 lines)
  trigger: java heap 강제 증가
  expected_alarms: APM 평균응답시간 / KCM Pod Memory / KCM Pod restart count
  estimated_duration_sec: 240
  cleanup: pod restart

[service-spec.yaml entry]
  id: scenario-05
  ...

이대로 진행? [Y/n/edit]
```

### 6. git commit + push (push_mode 에 따라)

```bash
cd "$RUNNER_ROOT"
git checkout -b "feat/scenario-<NN>-<slug>" 2>/dev/null || git checkout "feat/scenario-<NN>-<slug>"
git add scenarios/services/<testbed_name>/scripts/scenario-<NN>-*.sh
git add scenarios/services/<testbed_name>/service-spec.yaml
git commit -m "feat: add scenario-<NN> <slug> for <testbed_name>"
case "$PUSH_MODE" in
  pr)
    git push -u origin "feat/scenario-<NN>-<slug>"
    gh pr create --title "feat: scenario-<NN> <slug>" --body "..." 2>/dev/null \
      || echo "gh CLI 없음. PR 수동 생성 필요. push 는 완료."
    ;;
  direct-push)
    git checkout develop && git merge --no-ff "feat/scenario-<NN>-<slug>" && git push
    ;;
  local-only)
    echo "로컬에만 커밋. 사용자가 push 시점 결정."
    ;;
esac
```

### 7. 109 재배포 안내

> 새 시나리오는 컨테이너 재기동 후 활성화됩니다.
> ```
> ssh nkia@192.168.200.109
> cd ~/rca-scenario-runner
> git pull
> ./build-and-deploy.sh
> ```

오케스트레이터가 호출한 경우 자동으로 위 명령 실행 (사용자 승인 후).

---

## 단독 호출 예시

```
사용자: /testbed-generate-scenarios "plopvape-shop 에 memory leak 시나리오 추가"

스킬 응답:
  1. RUNNER_ROOT 확인 → ~/dev/rca-scenario-runner ✓
  2. 패턴 카탈로그 표시:
     [현재 plopvape-shop 시나리오: 4종 (lock / timeout / cpu-throttle / flood)]
     [추가 가능 패턴: template-generic (사용자 정의 필요)]
     [신규 패턴 메모리 누수 — 카탈로그에 없음. template-generic 으로 작성?]
  3. 사용자: "yes, template-generic 사용. java heap 누수 시나리오"
  4. LLM: heap 누수 시나리오 골격 작성 (template-generic 변형)
  5. 미리보기 + 승인
  6. commit + PR
```

---

## Resources

- [scenario-patterns/](../../infra/testbed/scenario-patterns/) — 패턴 카드 카탈로그
- [pattern-to-script.md](references/pattern-to-script.md) — 카드 → 스크립트 변환 룰
- [script-template.md](references/script-template.md) — bash 스크립트 표준 골격
- rca-scenario-runner 레포: `~/dev/rca-scenario-runner` (default)

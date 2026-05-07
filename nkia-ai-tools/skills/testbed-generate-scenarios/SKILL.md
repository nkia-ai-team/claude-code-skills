---
name: testbed-generate-scenarios
description: RCA 테스트베드에 장애 시나리오를 추가/생성. `infra/testbed/scenario-patterns/` 카탈로그에서 패턴 선택 → bash 스크립트 인스턴스화 → service-spec.yaml 갱신 → rca-scenario-runner 레포 PR/push. 사용자가 "시나리오 추가해줘", "장애 시나리오 만들어줘", "/testbed-generate-scenarios", "<service> 에 N개 시나리오 추가" 같은 요청 시 트리거. testbed-build 의 7번 단계가 이를 dispatch.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git:*), Bash(gh:*), Bash(jq:*), Bash(yq:*), Bash(curl:*), Bash(cat:*), Bash(grep:*), Bash(sed:*), Bash(awk:*), Bash(test:*), Bash(echo:*), Bash(mkdir:*), Bash(chmod:*), Bash(date:*)
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

3. **레포 부재 시 인터뷰 + git clone** — 사용자 환경마다 dev/projects/workspace 등 위치가 다름. testbed-build 의 [repo-discovery.md](../testbed-build/references/repo-discovery.md) 와 동일한 자동 발견 + 인터뷰 패턴 사용:
   ```
   1. cwd ($PWD) 우선 검사 → 발견되면 그대로 사용
   2. 부재 시 home 디렉토리 fallback (~/dev, ~/projects, ~/workspace, ~/)
   3. 둘 다 부재 시 AskUserQuestion 카드:
      - 옵션 (1) cwd 아래 ($PWD/rca-scenario-runner) — Recommended
      - 옵션 (2) $HOME/dev/rca-scenario-runner — 사용자가 dev 패턴 사용 시
      - Other (자동 추가) — 직접 경로 입력
   4. 결정된 경로에 git clone https://github.com/nkia-ai-team/rca-scenario-runner.git
   5. bootstrap.yaml 의 paths.scenario_runner_repo 에 영구 저장 (다음 호출부터 자동 사용)
   ```

   ⚠️ 사용자 환경 가정 금지 — 임의의 절대 경로 default 를 박지 말고 자동 발견 / 인터뷰 결과만 사용.

---

## Dispatch Flow

### 1. 대상 testbed 결정
```bash
ls "$RUNNER_ROOT/scenarios/services/"
```
1개면 자동, 여럿이면 사용자에게 선택 prompt.

### 2. 패턴 카탈로그 표시
[scenario-patterns/README.md](../../infra/testbed/scenario-patterns/README.md) 의 표 그대로 사용자에게 보여주고 선택 받기. (또는 "자동" → LLM 이 service-spec.yaml 도메인 메타 + 기존 시나리오 목록 보고 미커버 패턴 추천)

### 3. 패턴 카드 → 인스턴스 변환 (도메인-specific 합성 강제)

선택된 패턴 카드 read (예: `<patterns_root>/db-lock-contention.md`). 카드는 generic placeholder (`<table_name>` / `<row_key>` / `<endpoint>`) 만 — testbed 도메인에 맞는 실제 값으로 합성해야 함.

🚫 **절대 금지** — plopvape-shop 의 `scenarios/services/plopvape-shop/scripts/*.sh` 를 **read 후 sed 치환** 으로 변환 X. plopvape 시나리오는 e-commerce 도메인 전용 (orders 테이블 / pg-mock 컨테이너 / 30080 NodePort 가정). 다른 도메인 (food-delivery / banking / IoT 등) 에 sed 치환 시 비즈니스 의미 X + SQL error 가능. **패턴 카드 → 도메인-specific 합성** 만 정답.

#### 합성 우선순위 (위에서부터 — 첫 번째 만족 항목 사용)

1. **manifest.scenario_hints** (services-author Phase 6 산출 — 신규 testbed 자동 생성 시):
   - `lock_table` / `lock_endpoint` / `external_container` / `primary_load_endpoint` 등이 채워져있음
   - 그대로 사용. 별 분석 X.

2. **도메인 룩업 표** (e-commerce / banking / 예약 — pattern-to-script.md §4 표):
   - `interview.app.domain` 이 룩업 키 매치 → 표의 매핑 사용

3. **auto 모드 — 코드 분석 강제** (룩업 표에 없는 도메인 + scenario_hints 부재):
   - LLM 이 다음 read **필수**:
     - `<TESTBED_SVC_REPO>/<testbed_name>/*-service/src/main/java/.../*Controller.java` — endpoint + HTTP method + body schema
     - `<TESTBED_SVC_REPO>/<testbed_name>/db/init.sql` — 테이블 + 컬럼 + PK + seed
     - `<TESTBED_SVC_REPO>/<testbed_name>/k8s/*.yaml` — NodePort 실제 값, 외부 의존성 컨테이너
     - `<TESTBED_SVC_REPO>/<testbed_name>/docker-compose.dev.yml` (있다면) — mock 컨테이너 이름
   - 분석 결과로 도메인-specific 매핑 합성:
     - food-delivery 면 `LOCK_TABLE=orders` 또는 `restaurant_inventory` (init.sql 분석 결과 핫 row 후보)
     - 외부 의존성 컨테이너 = k8s manifest 에서 발견된 정확한 이름 (`pg-mock` 그대로 가정 X)
     - NodePort = manifest 의 실제 값 (30080 가정 X)

4. **사용자 인터뷰** (auto 결과 confidence 낮음 — 후보 여러 개):
   - 사용자에게 후보 표시 + 도메인 의도 묻기

5. **fail-fast** (위 모든 단계 결정 안 됨):
   - 시나리오 생성 abort. plopvape sed 치환으로 fallback **절대 금지**.

#### 합성 결과 검증 (사용자 confirm 필수)

LLM 이 합성한 시나리오 변수 (LOCK_TABLE / LOAD_ENDPOINT / EXTERNAL_CONTAINER 등) + 사용한 source (init.sql / Controller.java / k8s manifest) 를 사용자에게 명시:

```
=== food-delivery 도메인 합성 결과 ===

소스:
  - controllers: order-service/OrderController.java (POST /api/orders, /api/orders/cancel)
  - tables:      orders, order_items, restaurants, deliveries (init.sql)
  - k8s:         NodePort 30090 (food-delivery-nginx), mock 컨테이너: pg-mock-fd

scenario-01 (db-lock-contention):
  LOCK_TABLE=orders  ← 트랜잭션 핫 테이블 (orders.id PK)
  LOAD_ENDPOINT=POST /api/orders  ← 주문 생성 — order row 갱신
  LOAD_PAYLOAD={...}  ← OrderRequest schema 기반
  ...
```

사용자 confirm 후만 Step 4 (스크립트 + yaml entry 작성) 진입.

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

> **중요**: rca-scenario-runner 백엔드는 [scenarios.py](https://github.com/nkia-ai-team/rca-scenario-runner/blob/develop/backend/app/scenarios.py) 가 service-spec.yaml glob 으로 시나리오 자동 발견. yaml 만 떨어뜨리면 컨테이너 재시작 후 자동 등록.

### 5. 사용자 미리보기 + 승인 ⛔ (chat 응답 게이트 — 강제)

🚫 **강제 룰**: 본 step 의 사용자 chat 응답을 받기 전에는 **git commit / push / PR 생성 절대 X**. LLM 이 SKILL.md 따르며 "곧바로 git commit 해버리는" 패턴 금지. step 6 진입 조건 = 사용자가 자연어로 명시 승인 ("응" / "진행" / "PR" / "direct push" 등).

⚠️ **AskUserQuestion 카드 사용 X** — Claude Code 의 권한 정책상 destructive action (git push / gh pr create) 은 카드 응답이 의도 표현일 뿐 **별도 chat 승인을 요구**. 카드 → 자동 진행 패턴이 권한 시스템에 막혀 결국 chat 으로 다시 응답해야 함. 처음부터 chat 으로 받아 한 번에 처리.

#### 미리보기 — 의미 + 발화 조건까지 풀어서 설명

시나리오 파일 경로 / 라인 수만 표시하지 말고 **무엇을 시뮬레이션 하는지, 왜 이 testbed 에 적합한지, 어떤 알람이 어떤 조건에서 발화될지** 모두 자연어로 풀어서 출력:

```
=== 시나리오 추가 미리보기 ===

[scenario-05] Memory Leak (Heap exhaustion)

▶ 무엇을 시뮬레이션:
  Java heap 메모리를 강제로 증가시켜 OOM (OutOfMemoryError) 직전 상태를 재현.
  실제 production 의 메모리 누수 (캐시 무한 증식 / static collection 누적 /
  thread-local 미정리 등) 패턴을 모방.

▶ 왜 social-feed testbed 에 적합한가:
  feed-service 가 사용자별 피드 캐시를 in-memory 로 보관하는 구조라 메모리
  누수가 자연스럽게 발생할 가능성이 있음. 같은 testbed 에 이미 있는 lock /
  external-timeout / cpu / traffic-flood 와 카테고리 겹침 X — 메모리 도메인은
  현재 미커버.

▶ 트리거 메커니즘:
  bash 스크립트가 feed-service Pod 안에서 byte[] 배열을 list 에 무한 추가
  하는 작은 Java 프로그램을 실행. 60초 동안 heap 증가 → JVM 가 GC 압박 →
  Pod 메모리 limit 도달 → KCM 가 감지.

▶ 예상 발화 알람 (expected_alarms — Polestar10 web 의 알람 history 에서 매칭):
  1. APM 평균 응답시간 초과 (feed-service)
     조건: GC 압박으로 응답 latency 증가. p95 가 5s 이상 5분 지속 시 발화.
  2. KCM Pod Memory 사용률 (feed-service Pod)
     조건: Pod memory limit 의 90% 초과 5분 지속. KCM master 가 cgroup
     metric 받아 polestar10 push.
  3. KCM Pod restart count
     조건: Pod 가 OOMKilled 후 자동 restart. 재시작 1회 이상 시 발화.

▶ 메타:
  estimated_duration_sec: 240   # 4분 — 메모리 증가 + 알람 발화까지
  cleanup: pod restart           # kubectl rollout restart 로 메모리 reset
  side_effects:
    - feed-service Pod 가 잠시 unavailable. 다른 시나리오와 병렬 실행 X 권장.

▶ 변경 파일:
  + scripts/scenario-05-memory-leak.sh (신규, 47 lines)
  ~ service-spec.yaml (entry 추가, 12 lines)
```

#### chat prompt (위 미리보기 출력 직후)

미리보기 끝에 다음과 같이 묻고 사용자 자연어 응답 대기:

```
위 시나리오를 추가할까요? 다음 중 자연어로 답해 주세요:

  - "응" / "진행" / "PR" → git commit + push + gh pr create (default, Recommended)
  - "direct push" / "main 직접" → PR 없이 main 직접 push (신뢰 환경만)
  - "로컬만" / "local" → 로컬 commit 만, push 는 사용자 결정
  - "취소" / "no" → 변경사항 폐기

→ _
```

LLM 이 응답 자연어 파싱하여 push_mode 결정. 권한 prompt 가 한 번 더 뜰 수 있으나 chat 응답으로 한 번에 처리되는 형태 (카드 + 별도 권한 chat 의 이중 응답 회피).

⚠️ **chat 응답 받기 전 git 작업 X / Step 6 은 사용자 응답 후에만 진입**. 사용자가 "취소" 응답 시 임시 파일 정리 + 종료. testbed-build 오케스트레이터가 호출한 경우라도 반드시 본 게이트 통과 필수 — 자동 진행 모드에서도 이 게이트는 강제.

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

### 7. 타겟 호스트 재배포 안내

새 시나리오는 rca-scenario-runner 컨테이너 재기동 후 활성화됩니다. 명령은 testbed 가 떠있는 호스트에서 실행 — 109 / 다른 사내 서버 / 사용자 본인 머신 등 환경마다 다름.

호스트 결정 source (우선순위):
1. testbed-build 에서 호출된 경우 → `inventory.yml` 의 host vars (`ansible_host`, `ansible_user`)
2. 단독 호출의 경우 → bootstrap.yaml 의 SSH 자격증명 (`ssh.default_user` + 인터뷰에서 받은 host)

```bash
# inventory.yml / bootstrap.yaml 에서 추출한 변수 사용
TARGET_USER=<from inventory or bootstrap>
TARGET_HOST=<from inventory or bootstrap>
RUNNER_DIR=<scenario_runner_install_dir — group_vars/all.yml default 또는 사용자 override>

ssh "${TARGET_USER}@${TARGET_HOST}" "
  cd ${RUNNER_DIR} && \
  git pull && \
  ./build-and-deploy.sh
"
```

⚠️ 호스트 결정은 항상 inventory/bootstrap source 에서.

오케스트레이터가 호출한 경우 자동으로 위 명령 실행 (사용자 승인 후). 단독 호출의 경우 사용자에게 호스트 + 명령 표시 후 확인 받기.

---

## 단독 호출 예시

```
사용자: /testbed-generate-scenarios "plopvape-shop 에 memory leak 시나리오 추가"

스킬 응답:
  1. RUNNER_ROOT 확인 → bootstrap.yaml 의 paths.scenario_runner_repo 사용
     (예시: 사용자 환경마다 다름. cwd / $HOME/dev / $HOME/projects 등)
  2. 패턴 카탈로그 표시:
     [현재 plopvape-shop 시나리오: 4종 (lock / timeout / cpu-throttle / flood)]
     [추가 가능 패턴: template-generic (사용자 정의 필요)]
     [신규 패턴 메모리 누수 — 카탈로그에 없음. template-generic 으로 작성?]
  3. 사용자: "yes, template-generic 사용. java heap 누수 시나리오"
  4. LLM: heap 누수 시나리오 골격 작성 (template-generic 응용)
  5. 미리보기 + 승인
  6. commit + PR
```

---

## Resources

- [scenario-patterns/](../../infra/testbed/scenario-patterns/) — 패턴 카드 카탈로그
- [pattern-to-script.md](references/pattern-to-script.md) — 카드 → 스크립트 변환 룰
- [script-template.md](references/script-template.md) — bash 스크립트 표준 골격
- rca-scenario-runner 레포 path: `bootstrap.yaml` 의 `paths.scenario_runner_repo` (사용자별로 다름 — 자동 발견 결과 또는 인터뷰로 결정)

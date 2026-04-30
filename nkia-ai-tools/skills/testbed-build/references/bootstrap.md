# Bootstrap — 자격증명 + 레포 경로

매 testbed-build 호출 첫 단계.

## ~/.testbed-build/bootstrap.yaml 스키마

```yaml
# chmod 600. 사용자 home 에 영구 보존 (run 사이 공유).

ssh:
  default_user: nkia          # SSH 기본 user (인터뷰에서 override 가능)
  ssh_key_path: ""            # 비어있으면 password 사용

polestar10:
  base_url: "https://192.168.230.96"   # 기본 endpoint (인터뷰에서 변경 가능)
  user: ""                              # 비어있으면 매번 인터뷰
  # password 는 ~/.polestar10rc 에 별도 저장 (testbed-polestar10-register 호환)

git:
  pat_file: "~/.git-credentials"        # PAT 저장 위치 (default git credential.helper store)
  default_branch_strategy: "feature-pr" # feature-pr | direct-develop

paths:
  testbed_services_repo: "~/dev/testbed-services"
  scenario_runner_repo: "~/dev/rca-scenario-runner"
  ansible_playbook_root: ""             # 비우면 plugin install 디렉토리 발견
```

## ⚠️ 두 서버 개념 — 사용자에게 명확히 안내

인터뷰 시작 전 한 줄 안내 필수:

```
=== testbed-build 환영합니다 ===

테스트베드 구축을 위해서는 두 개의 서버가 필요합니다:

  1. 타겟 서버 (Target Host) — SSH 접근 필요
     테스트베드가 깔릴 곳. K3s + 5 services + Polestar10 에이전트
     4종 (KCM/APM/WPM/SMS) + rca-scenario-runner 가 설치됨.
     예: 109 DGX Spark (192.168.200.109)

  2. Polestar10 모니터링 서버 (Polestar10 instance) — HTTP(S) 접근 필요
     RCA 분석 백엔드. 자원 등록 / 알람 정책 / 메트릭 시계열 API
     가 여기로 호출됨. 사용자 ID/PW 도 함께 필요.
     예: NKIA 104 운영 (https://192.168.230.104)

  ※ 두 서버가 동일 호스트여도 OK (예: 같은 서버에 K3s + Polestar10).
    분리 운영이 더 일반적이지만 강제 X.

이번 단계에서는 양쪽 자격증명/주소를 한 번에 받아 ~/.testbed-build/
+ ~/.polestar10rc 에 캐시. 다음 호출부터 묻지 않음.

또한 NMS (네트워크 모니터링 시스템) 는 **자동 감지 + 자동 등록** 이
default. 타겟 서버가 속한 네트워크에서 SNMP 응답하는 장비
(라우터/스위치/방화벽/AP 등) 를 스캔하여 발견된 모든 장비를 NMS
자원으로 등록 (사용자에게 추가로 묻지 않음 — 가능하면 무조건 수집).
사용자에게는 결과 알림만 ("N 개 장비 자동 등록"). 스캔 실패 또는
0 장비 발견 시에만 skip + 안내.
```

이 안내를 인터뷰 첫 화면에 출력 후 AskUserQuestion 호출.

---

## 인터뷰 (없으면 수행) — AskUserQuestion 활용

**텍스트 prompt 가 아니라 `AskUserQuestion` 도구 사용** — 카드형 UI. ~/.polestar10rc 캐시 유무 따라 두 시나리오 분기.

### 캐시 (~/.polestar10rc) 가 이미 있을 때

캐시된 자격증명 사용이 default. 다른 서버 등록 케이스는 별 옵션:

```python
AskUserQuestion(questions=[
  {
    "question": "타겟 서버 (테스트베드 깔릴 곳) SSH 인증 방식?",
    "header": "타겟 SSH",
    "multiSelect": False,
    "options": [
      {"label": "Password (Recommended)", "description": "매 호출마다 password 입력. 가장 단순."},
      {"label": "SSH key", "description": "~/.ssh/id_rsa 또는 사용자 지정 경로 (key 기반 무인증 접속)"}
    ]
  },
  {
    "question": "Polestar10 서버는 어디로?",
    "header": "P10 서버",
    "multiSelect": False,
    "options": [
      {"label": "캐시된 서버 사용 (Recommended)", "description": "~/.polestar10rc 의 base_url + 자격증명 그대로 (예: 104 운영)"},
      {"label": "다른 서버에 등록", "description": "새 base_url + 사용자 ID/PW 직접 입력. 캐시는 보존, 이번 run 만 override"}
    ]
  }
  # 외부 레포 clone 은 자동 발견 후 분기 (아래 별 섹션 참조)
])
```

"다른 서버에 등록" 선택 시 자유 입력 prompt 로 base_url + ID + PW 받음. 이번 run 만 사용 (캐시 보존). 사용자가 영구 변경하려면 ~/.polestar10rc 직접 편집.

### 캐시 (~/.polestar10rc) 가 없을 때 — 첫 실행

```python
AskUserQuestion(questions=[
  {
    "question": "타겟 서버 (테스트베드 깔릴 곳) SSH 인증 방식은 무엇인가요?",
    "header": "타겟 SSH",
    "multiSelect": False,
    "options": [
      {"label": "Password (Recommended)", "description": "매 호출마다 password 입력. 가장 단순."},
      {"label": "SSH key", "description": "~/.ssh/id_rsa 또는 사용자 지정 경로"}
    ]
  },
  {
    "question": "Polestar10 모니터링 서버 (자원 등록·알람 API) 주소를 알려주세요",
    "header": "P10 서버",
    "multiSelect": False,
    "options": [
      {"label": "104 운영 (Recommended)", "description": "https://192.168.230.104 — NKIA 운영 환경 (기본)"},
    ]
  }
  # 외부 레포 clone 은 자동 발견 후 분기 (아래 별 섹션 참조)
])
```

`Other` 선택 시 자유 입력. 첫 실행이라 사용자 ID/PW 도 자유 입력 prompt 로 받음.

---

## 외부 레포 — 자동 발견 우선, 부재 시에만 인터뷰

`testbed-services` / `rca-scenario-runner` 두 레포는 **항상 묻기 전에 자동 발견** 시도. 발견되면 그대로 사용. 없을 때만 prompt.

### Step 1: cwd (Claude Code 작업 폴더) 우선 검사

```bash
# $PWD = Claude Code 가 켜져있는 작업 폴더
for repo in testbed-services rca-scenario-runner; do
  for candidate in "./$repo" "../$repo"; do
    [ -d "${candidate}/.git" ] && echo "FOUND_CWD $repo: $(realpath $candidate)" && break
  done
done
```

### Step 2: 부재 시 — 외부 영역 fallback

홈 디렉토리 일반적 위치 순회 (depth 1):
```bash
for repo in testbed-services rca-scenario-runner; do
  for path in ~/dev/$repo ~/projects/$repo ~/workspace/$repo ~/$repo; do
    [ -d "$path/.git" ] && echo "FOUND_HOME $repo: $path" && break
  done
done
```

### Step 3: 결과 따라 분기

#### Case A: 둘 다 발견 (cwd 또는 home)

**인터뷰 없이 자동 진행** — 발견된 경로 사용 + 알림만:
```
[레포 자동 발견 결과]
  ✓ testbed-services       → /home/sjbang/dev/claude-code-skills/testbed-services (cwd)
  ✓ rca-scenario-runner   → /home/sjbang/dev/rca-scenario-runner (home)

위 경로 그대로 사용합니다.
```

#### Case B: 둘 중 하나만 발견

발견된 건 자동 사용 + 미발견 건만 prompt:

```python
AskUserQuestion(questions=[
  {
    "question": "rca-scenario-runner 레포가 없습니다. 어디에 clone 할까요?",
    "header": "레포 clone",
    "multiSelect": False,
    "options": [
      {"label": "현재 작업 폴더 아래 (Recommended)", "description": "$PWD/rca-scenario-runner — Claude Code 작업 폴더 직속"},
      {"label": "$HOME/dev/", "description": "~/dev/rca-scenario-runner — 사용자 평소 작업 위치 패턴"}
    ]
  }
])
# Other 선택 시 직접 경로 입력
```

#### Case C: 둘 다 부재

같은 옵션으로 두 레포 묶음 prompt:

```python
AskUserQuestion(questions=[
  {
    "question": "두 외부 레포가 없습니다. 어디에 clone 할까요?",
    "header": "레포 clone",
    "multiSelect": False,
    "options": [
      {"label": "현재 작업 폴더 아래 (Recommended)", "description": "$PWD/{testbed-services,rca-scenario-runner} — Claude Code 작업 폴더 직속"},
      {"label": "$HOME/dev/", "description": "~/dev/ 두 레포 모두"}
    ]
  }
])
# Other 선택 시 각 레포 경로 따로 자유 입력
```

### Step 4: 결정된 경로로 진행

- 발견 케이스: 그대로 사용
- clone 케이스: `git clone https://github.com/nkia-ai-team/<repo>.git <chosen_path>` 실행
- bootstrap.yaml 의 `paths.testbed_services_repo` / `paths.scenario_runner_repo` 에 영구 저장 → **다음 호출부터 발견/clone 단계 자체 skip** (paths 가 가리키는 디렉토리에 .git 있는지만 확인)

자유 입력 슬롯 (텍스트 prompt — 위 카드와 별도로):
- 타겟 서버 IP 주소 (예: `192.168.200.109`)
- 타겟 서버 SSH user (default `nkia`) — *109/96/104 공통 user 가 nkia 라 default*
- 타겟 서버 SSH password 또는 key 경로 (선택한 인증 방식 따라)
- (Polestar10 Other 선택 시) Polestar10 base_url 직접 입력 (`https://...` 형식, self-signed cert 일반)
- **Polestar10 사용자 ID** (자원 등록·알람·메트릭 API 호출 권한 있는 계정. 보통 `admin`)
- **Polestar10 password**
- (레포 no 선택 시) testbed-services / rca-scenario-runner 경로 각각 직접 입력

> Polestar10 ID/PW 는 `~/.polestar10rc` (chmod 600) 에 저장돼 testbed-polestar10-register 와 공유됨. 이미 파일이 있으면 재사용 (재인터뷰 X).

### 자유 입력 흐름 (텍스트 prompt 순서)

```
1. "타겟 서버 IP/hostname?" → 192.168.200.109 (default 109)
2. "타겟 서버 SSH user?" → nkia (default)
3. (인증 방식이 password 면) "타겟 서버 SSH password?" → ****
4. (인증 방식이 ssh_key 면) "SSH key 경로?" → ~/.ssh/id_rsa (default)
5. (Polestar10 instance 가 Other 면) "Polestar10 base_url?" → https://...
6. ~/.polestar10rc 부재 시:
     "Polestar10 사용자 ID?" → admin (default)
     "Polestar10 password?" → ****
7. (레포 clone 이 no 면)
     "testbed-services 레포 경로?" → ~/dev/testbed-services (default)
     "rca-scenario-runner 레포 경로?" → ~/dev/rca-scenario-runner (default)
```

→ 모든 답변 종합 → `~/.testbed-build/bootstrap.yaml` (chmod 600) + `~/.polestar10rc` (chmod 600). 다음 호출부터 묻지 않음. 자격증명 변경 시 사용자가 직접 yaml 편집 또는 파일 삭제 후 재인터뷰.

→ 답변 종합 → `~/.testbed-build/bootstrap.yaml` 생성 + `chmod 600`. 다음 호출부터 묻지 않음.

## Polestar10 자격증명 — 2층 구조

testbed-build 의 bootstrap.yaml 은 base_url + user 만 캐시. **password 는 ~/.polestar10rc** 가 source of truth (testbed-polestar10-register 와 공유).

```bash
# ~/.polestar10rc (chmod 600, 기존 testbed-polestar10-register 가 관리)
export POLESTAR10_BASE_URL="https://192.168.230.96"
export POLESTAR10_USER="admin"
export POLESTAR10_PASS="..."
export POLESTAR10_CURL_OPTS="-k -sS"   # self-signed cert
```

testbed-build 진입 시:
1. bootstrap.yaml 의 polestar10.base_url + user 가 .polestar10rc 와 일치 확인
2. 불일치 시 사용자에게 "어느 쪽 따를까요?" prompt
3. .polestar10rc 부재 시 testbed-polestar10-register 의 부트스트랩 인터뷰 trigger

## 외부 레포 git clone

bootstrap.yaml.paths.* 가 가리키는 디렉토리 부재 시:

```bash
TESTBED_SVC_PATH=$(yq '.paths.testbed_services_repo' ~/.testbed-build/bootstrap.yaml | sed "s|~|$HOME|")
RUNNER_PATH=$(yq '.paths.scenario_runner_repo' ~/.testbed-build/bootstrap.yaml | sed "s|~|$HOME|")

if [ ! -d "$TESTBED_SVC_PATH/.git" ]; then
  echo "testbed-services 레포가 없습니다. clone 합니다."
  mkdir -p "$(dirname "$TESTBED_SVC_PATH")"
  git clone https://github.com/BangSungjoon/testbed-services.git "$TESTBED_SVC_PATH"
fi

if [ ! -d "$RUNNER_PATH/.git" ]; then
  echo "rca-scenario-runner 레포가 없습니다. clone 합니다."
  mkdir -p "$(dirname "$RUNNER_PATH")"
  git clone https://github.com/BangSungjoon/rca-scenario-runner.git "$RUNNER_PATH"
fi
```

git clone 실패 (PAT 만료 / private 권한 X) 시 ask-polestar10 가 아니라 직접 사용자 안내:
```
git clone 실패: <error>
  - PAT 가 ~/.git-credentials 에 있는지 확인
  - private 레포 권한 있는지 확인 (BangSungjoon org 멤버?)
  - 수동 clone 후 testbed-build 재호출 권장
```

## 부트스트랩 검증

매 호출 진입 시 sanity check.

⚠️ **bootstrap.yaml 부재 → 인터뷰 무조건 실행**. 다른 캐시 파일 (`~/.polestar10rc` / 레포 디렉토리 / `~/.git-credentials`) 이 모두 존재하더라도 skip 금지. 캐시는 인터뷰 옵션의 default value 자동 채우기에만 사용.

```bash
if [ ! -f ~/.testbed-build/bootstrap.yaml ]; then
  # 1. 캐시 파일 스캔 — default value 후보 확보 (인터뷰 skip 용이 아님)
  P10_DEFAULT_URL=$(grep -E '^export POLESTAR10_BASE_URL' ~/.polestar10rc 2>/dev/null | sed 's/.*="\(.*\)"/\1/')
  P10_DEFAULT_USER=$(grep -E '^export POLESTAR10_USER' ~/.polestar10rc 2>/dev/null | sed 's/.*="\(.*\)"/\1/')
  TESTBED_SVC_DEFAULT="$HOME/dev/testbed-services"
  RUNNER_DEFAULT="$HOME/dev/rca-scenario-runner"

  # 2. AskUserQuestion 인터뷰 — 캐시된 값을 첫 옵션 (Recommended) 으로 제시
  run_bootstrap_interview_with_defaults_from_cache \
    --p10-url-default "$P10_DEFAULT_URL" \
    --p10-user-default "$P10_DEFAULT_USER" \
    --testbed-svc-default "$TESTBED_SVC_DEFAULT" \
    --runner-default "$RUNNER_DEFAULT"
fi

# 추가 sanity check (bootstrap.yaml 이 있는 정상 케이스)
[ -f ~/.polestar10rc ] || trigger_polestar10_bootstrap
[ -d "$TESTBED_SVC_PATH/.git" ] || prompt_clone_testbed_services
[ -d "$RUNNER_PATH/.git" ] || prompt_clone_runner

# polestar10 connectivity 사전 체크 (Phase 2 에서)
```

## 인터뷰 슬롯 정책 표

bootstrap.yaml 부재 시 인터뷰에서 어떤 슬롯이 **always ask** / **default from cache** / **skip if cached** 인지 명시:

| 슬롯 | 정책 | 캐시 소스 | 비고 |
|---|---|---|---|
| SSH 인증 방식 | always ask | — | default 없음. password vs ssh_key 매 호출 결정 |
| 타겟 SSH default_user | always ask | bootstrap.yaml 또는 `nkia` | default 표시 후 confirm |
| Polestar10 base_url | always ask (default 표시) | ~/.polestar10rc | 캐시값을 (Recommended) 옵션으로 |
| Polestar10 user | always ask (default 표시) | ~/.polestar10rc | 캐시값을 (Recommended) 옵션으로 |
| Polestar10 password | **skip if cached** | ~/.polestar10rc | rc 파일 있으면 인터뷰 자체 생략 |
| 레포 clone yes/no | **skip if 디렉토리 존재** | filesystem | 둘 다 있으면 자동 yes |
| 레포 경로 | always ask (default 표시) | bootstrap.yaml 또는 `~/dev/...` | 디렉토리 존재 시 그 경로가 default |
| git PAT 입력 | **skip if cached** | ~/.git-credentials | 파일 있으면 PAT 인터뷰 skip |
| 분기 전략 | always ask (default 표시) | bootstrap.yaml 또는 `feature-pr` | feature-pr / direct-develop |

규칙:
- **always ask** = 캐시 파일이 있어도 AskUserQuestion 의 첫 옵션 (Recommended) 으로 표시한 후 사용자 confirm 필요. "확인 없이 캐시값 그대로 yaml 작성" 은 금지.
- **skip if cached** = 해당 캐시 파일이 있으면 인터뷰 자체를 생략. 부재 시에만 인터뷰 트리거.

위 규칙은 첫 호출 (bootstrap.yaml 부재) 에만 해당. bootstrap.yaml 이 있으면 모든 인터뷰 skip (값 변경은 사용자가 yaml 직접 편집 또는 파일 삭제 후 재인터뷰).

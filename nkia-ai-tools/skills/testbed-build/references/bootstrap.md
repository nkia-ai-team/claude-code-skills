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

testbed-build 는 **두 개의 서로 다른 서버** 를 다룸. 인터뷰 시작 전 한 줄 안내 필수:

```
=== testbed-build 환영합니다 ===

이 스킬은 두 개의 서버를 사용합니다:

  1. 타겟 서버 (Target Host)
     테스트베드가 깔릴 곳. K3s + 5 services + 폴스타10 에이전트
     4종이 설치됨. SSH 접근 가능해야 함.
     예: 109 DGX Spark (192.168.200.109)

  2. Polestar10 모니터링 서버 (Polestar10 instance)
     RCA 분석을 위한 모니터링 백엔드. 자원 등록 / 알람 정책 /
     메트릭 시계열 API 가 여기로 호출됨.
     예: NKIA 96 demo (https://192.168.230.96)

bootstrap 단계에서 둘 다의 자격증명/주소를 한 번에 캐시.
```

이 안내를 인터뷰 첫 화면에 출력 후 AskUserQuestion 호출.

---

## 인터뷰 (없으면 수행) — AskUserQuestion 활용

**텍스트 prompt 가 아니라 `AskUserQuestion` 도구 사용** — 카드형 UI. multi-choice 가 있는 슬롯들을 한 묶음에:

```python
AskUserQuestion(questions=[
  {
    "question": "타겟 서버 (테스트베드 깔릴 곳) SSH 인증 방식?",
    "header": "타겟 SSH",
    "multiSelect": False,
    "options": [
      {"label": "Password (Recommended)", "description": "매 호출마다 password 입력. 가장 단순. (예: nkia 사용자, NKIA1234)"},
      {"label": "SSH key", "description": "~/.ssh/id_rsa 또는 사용자 지정 경로 (key 기반 무인증 접속)"}
    ]
  },
  {
    "question": "Polestar10 모니터링 서버 (자원 등록·알람 API) 주소?",
    "header": "P10 서버",
    "multiSelect": False,
    "options": [
      {"label": "96 demo (Recommended)", "description": "https://192.168.230.96 — NKIA 외부 데모 환경"},
      {"label": "NKIA dev", "description": "사내 dev Polestar10 instance"}
    ]
  },
  {
    "question": "외부 레포 자동 clone 진행?",
    "header": "레포 clone",
    "multiSelect": False,
    "options": [
      {"label": "yes (Recommended)", "description": "testbed-services + rca-scenario-runner 둘 다 ~/dev/ 에 자동 clone"},
      {"label": "no — 직접 경로 입력", "description": "기존 다른 위치 사용"}
    ]
  }
])
```

자유 입력 슬롯 (텍스트 prompt — 위 카드와 별도로):
- 타겟 서버 SSH user (default `nkia`) — *109/96/104 공통 user 가 nkia 라 default*
- (SSH key 선택 시) SSH key 경로 (default `~/.ssh/id_rsa`)
- (Polestar10 Other 선택 시) Polestar10 base_url 직접 입력 (`https://...` 형식, self-signed cert 일반)
- (레포 no 선택 시) testbed-services / rca-scenario-runner 경로 각각 직접 입력

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

매 호출 진입 시 sanity check (인터뷰 unnecessarily 다시 안 하기 위해):

```bash
[ -f ~/.testbed-build/bootstrap.yaml ] || run_bootstrap_interview
[ -f ~/.polestar10rc ] || trigger_polestar10_bootstrap
[ -d "$TESTBED_SVC_PATH/.git" ] || prompt_clone_testbed_services
[ -d "$RUNNER_PATH/.git" ] || prompt_clone_runner

# polestar10 connectivity 사전 체크 (Phase 2 에서)
```

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
     예: NKIA 96 demo (https://192.168.230.96)

  ※ 두 서버가 동일 호스트여도 OK (예: 같은 서버에 K3s + Polestar10).
    분리 운영이 더 일반적이지만 강제 X.

이번 단계에서는 양쪽 자격증명/주소를 한 번에 받아 ~/.testbed-build/
+ ~/.polestar10rc 에 캐시. 다음 호출부터 묻지 않음.

또한 NMS (네트워크 모니터링 시스템) 는 **자동 감지** 시도 후 결과
따라 인터뷰. 타겟 서버가 속한 네트워크에서 SNMP 응답하는 장비
(라우터/스위치/방화벽/AP 등) 를 스캔하여 발견된 후보 리스트를
사용자에게 표시. 사용자가 confirm/edit 하여 NMS 자원으로 등록.
스캔 실패 또는 0 장비 발견 시에만 "직접 입력 또는 skip" 으로 fallback.
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

매 호출 진입 시 sanity check (인터뷰 unnecessarily 다시 안 하기 위해):

```bash
[ -f ~/.testbed-build/bootstrap.yaml ] || run_bootstrap_interview
[ -f ~/.polestar10rc ] || trigger_polestar10_bootstrap
[ -d "$TESTBED_SVC_PATH/.git" ] || prompt_clone_testbed_services
[ -d "$RUNNER_PATH/.git" ] || prompt_clone_runner

# polestar10 connectivity 사전 체크 (Phase 2 에서)
```

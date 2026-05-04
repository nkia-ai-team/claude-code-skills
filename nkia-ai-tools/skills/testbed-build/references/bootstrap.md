# Bootstrap — 자격증명 + 레포 경로

매 testbed-build 호출 첫 단계.

## ~/.testbed-build/bootstrap.yaml 스키마

```yaml
# chmod 600. 사용자 home 에 영구 보존 (run 사이 공유).

ssh:
  default_user: nkia          # SSH 기본 user (인터뷰에서 override 가능)
  ssh_key_path: ""            # 비어있으면 password 사용

polestar10:
  base_url: "https://192.168.230.104"   # 기본 endpoint (NKIA 운영. 인터뷰에서 변경 가능)
  user: ""                               # 비어있으면 매번 인터뷰
  organization_id: ""                    # SMS install 시 SAAS_TENANT_ID. Polestar10 web 우측 상단 [계정] > 조직명 마우스오버 24-hex
  # password 는 ~/.polestar10rc 에 별도 저장 (testbed-polestar10-register 호환)

git:
  pat_file: "~/.git-credentials"        # PAT 저장 위치 (default git credential.helper store)
  testbed_services_url: "https://github.com/nkia-ai-team/testbed-services.git"
  scenario_runner_url:  "https://github.com/nkia-ai-team/rca-scenario-runner.git"
  pr_merge_mode: "manual"               # manual (사용자가 PR 직접 머지 후 진행 버튼) | auto (gh CLI 로 자동 merge)
  default_branch_strategy: "feature-pr" # feature-pr | direct-develop

agents:
  kcm_source_repo: ""                   # ARM64 KCM source-build 시 사내 GitLab URL (예: https://cims2.nkia.net:8443/gitlab/lucida-kcmagent). 비우면 KCM 자동 skip
  kcm_source_credentials_help: ""       # 사용자 메모용 — clone 시 자격증명 어떻게 통과시키는지 (예: "git config credential.helper store 후 한 번 수동 clone")

paths:
  testbed_services_repo: ""             # 자동 발견 결과 또는 인터뷰. 비우면 cwd → ~/dev → ~/projects → ~ 순회
  scenario_runner_repo: ""              # 동일
  ansible_playbook_root: ""             # 비우면 plugin install 디렉토리 발견
```

## ⚠️ Step 0 — 컨트롤러 도구 사전 검증

본격 인터뷰 진입 전, 컨트롤러 (Claude Code 가 실행 중인 머신) 에 필요한 CLI 도구들이 깔려있는지 확인합니다. 부재 시 자동 설치 옵션을 제공해 사용자가 phase 7~8 시점에 cryptic 에러를 보지 않도록 사전 차단.

```bash
required=(ansible-playbook sshpass ssh git curl jq yq gh)
missing=()
for cmd in "${required[@]}"; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done

if [ ${#missing[@]} -gt 0 ]; then
  # AskUserQuestion 으로 자동 설치 여부 확인
  os=$(uname -s)
  pkg_mgr=$([ "$os" = "Darwin" ] && echo "brew" || echo "apt")
  install_cmds=$(generate_install_commands_for "$pkg_mgr" "${missing[@]}")
fi
```

부재 도구 발견 시 사용자에게 다음 카드:

```python
AskUserQuestion(questions=[
  {
    "question": "테스트베드 구축에 필요한 일부 CLI 도구가 컨트롤러에 깔려있지 않습니다. 자동으로 설치를 진행할까요? 부재 도구: {{MISSING_LIST}}. 설치 명령은 패키지 매니저 ({{PKG_MGR}}) 를 사용합니다.",
    "header": "도구 자동 설치",
    "multiSelect": False,
    "options": [
      {"label": "자동 설치 진행 (Recommended)", "description": "{{INSTALL_CMD_PREVIEW}} — sudo 권한 필요할 수 있어 password prompt 가 뜰 수 있습니다."},
      {"label": "직접 설치 후 재실행", "description": "사용자가 별 터미널에서 위 명령 실행 후 testbed-build 다시 호출"}
    ]
  }
])
```

도구 → 설치 명령 매핑:

| 도구 | macOS (brew) | Linux (apt) |
|---|---|---|
| ansible-playbook | `brew install ansible` | `sudo apt install ansible` |
| sshpass | `brew install hudochenkov/sshpass/sshpass` | `sudo apt install sshpass` |
| gh | `brew install gh` | `sudo apt install gh` |
| jq, yq, curl, git | `brew install <name>` | `sudo apt install <name>` |
| ssh | (시스템 기본) | (시스템 기본) |

설치 후 `command -v` 재검증 → 모두 통과해야 다음 단계 진입.

---

## ⚠️ 두 서버 개념 — 사용자에게 명확히 안내

인터뷰 시작 전 한 줄 안내 필수:

```
=== testbed-build 환영합니다 ===

테스트베드 구축을 위해서는 두 개의 서버가 필요합니다:

  1. 타겟 서버 (Target Host) — SSH 접근 필요
     테스트베드가 깔릴 곳. K3s 클러스터 + DB + 여러 microservices
     (testbed 마다 개수·구성 다름. plopvape-shop 은 5종, social-feed
     는 4종 등) + Polestar10 에이전트 4종 (KCM/APM/WPM/SMS) +
     rca-scenario-runner 가 설치됨.
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
    "question": "타겟 서버 (테스트베드 깔릴 곳) SSH 인증 방식은 무엇인가요?",
    "header": "타겟 SSH",
    "multiSelect": False,
    "options": [
      {"label": "Password (Recommended)", "description": "매 호출마다 password 입력. 가장 단순."},
      {"label": "SSH key", "description": "~/.ssh/id_rsa 또는 사용자 지정 경로 (key 기반 무인증 접속)"}
    ]
  },
  {
    "question": "Polestar10 서버는 어디로 사용하시겠어요?",
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
      {"label": "104 운영 (Recommended)", "description": "https://192.168.230.104 — NKIA 운영 환경 (기본)"}
    ]
  },
  {
    "question": "services-author agent 가 신규 testbed 코드를 testbed-services 레포에 생성한 후, GitHub 에 PR 을 어떤 방식으로 머지하시겠어요? 수동 머지는 사용자가 직접 PR 화면에서 review 후 merge 버튼을 누르는 방식이고, 자동 머지는 gh CLI 가 충분한 권한을 가지고 있다고 가정하고 즉시 squash 머지합니다.",
    "header": "PR 머지 모드",
    "multiSelect": False,
    "options": [
      {"label": "수동 머지 (Recommended)", "description": "안전한 default — services-author 가 PR 만 만든 뒤, 사용자가 직접 코드 review + merge 버튼 클릭. testbed-build 는 PR 머지 상태를 60초 주기로 폴링하다가 머지 감지되면 자동으로 다음 phase 진행."},
      {"label": "자동 머지", "description": "gh CLI 의 repo write 권한 가정 (`gh auth refresh -h github.com -s repo` 사전 실행 필요). PR 만든 직후 즉시 squash merge → 사용자 review 게이트 X. CI/dogfooding 빠른 환경에 적합."}
    ]
  }
  # 외부 레포 clone 은 자동 발견 후 분기 (아래 별 섹션 참조)
])
```

`Other` 선택 시 자유 입력. 첫 실행이라 사용자 ID/PW 도 자유 입력 prompt 로 받음.

---

## 외부 레포 — 자동 발견 우선, 부재 시에만 인터뷰

testbed-build 가 의존하는 두 외부 레포가 있습니다. 사용자가 처음 호출하는 경우에는 각 레포가 어떤 역할인지 안내한 후 자동 발견 결과를 보여드립니다:

```
[외부 레포 역할 안내]

  1. testbed-services — RCA 분석 대상이 될 microservices 코드 모음
     예: plopvape-shop (e-commerce, 5종 서비스), social-feed (소셜 피드, 4종)
     각 testbed 마다 서비스 개수·도메인이 다름 (MSA 구조만 공통).
     이 레포의 한 디렉토리가 K3s 에 배포돼 RCA 검증 시 부하·장애의
     무대가 됩니다. 신규 도메인은 services-author agent 가 자동 생성.
     URL: https://github.com/nkia-ai-team/testbed-services

  2. rca-scenario-runner — 장애 시나리오 실행 웹 도구
     플레이북 마지막 단계에서 109 같은 타겟 서버에 docker-compose 로
     배포됩니다. 사용자가 web UI (target:8091) 에서 시나리오를 실행
     하면 testbed-services 의 서비스에 장애를 주입하고 Polestar10 이
     RCA 분석.
     URL: https://github.com/nkia-ai-team/rca-scenario-runner

두 레포가 컨트롤러 (Claude Code 가 실행 중인 머신) 에 이미 clone 되어
있는지 확인 후, 없으면 어디에 clone 할지 묻습니다.
```

이 안내 출력 후 **자동 발견 시도**. 발견되면 그대로 사용 (인터뷰 X). 없을 때만 prompt.

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

### 추가 슬롯 — 가능한 한 카드형 (default-present), 비밀만 텍스트 prompt

> Polestar10 ID/PW 는 `~/.polestar10rc` (chmod 600) 에 저장돼 testbed-polestar10-register 와 공유됨. 이미 파일이 있으면 재사용 (재인터뷰 X).

#### 카드형 (default-present 슬롯) — 묶음 AskUserQuestion

타겟 서버 IP 와 SSH user 는 default 가 명확해서 카드형이 자연스럽습니다 (109 / nkia). Polestar10 사용자 계정은 환경마다 다양해서 (admin / nkia / 별도 운영 계정) 카드 옵션을 미리 정해두는 가치가 적으므로 다음 단계 비밀 입력 흐름에서 자유 입력으로 받습니다.

```python
AskUserQuestion(questions=[
  {
    "question": "타겟 서버 IP/hostname 은 어떤 걸 사용하시겠어요?",
    "header": "타겟 IP",
    "multiSelect": False,
    "options": [
      {"label": "192.168.200.109 (Recommended)", "description": "109 DGX Spark — 기존 RCA 테스트베드 위치"}
    ]
  },
  {
    "question": "타겟 서버 SSH user 는 누구로 사용하시겠어요?",
    "header": "SSH user",
    "multiSelect": False,
    "options": [
      {"label": "nkia (Recommended)", "description": "109/96/104 공통 user. 일반적으로 nkia."}
    ]
  }
])
# Other 가 자동 추가되어 자유 입력 가능 (예: 다른 IP, 다른 user)
```

> ⚠️ **Polestar10 base_url 의 Other 케이스**: 첫 인터뷰의 P10 서버 카드에서 Other 선택 시 위 묶음과 별 턴에 자유 입력 prompt: "Polestar10 base_url 을 직접 입력해 주세요 (`https://...` 형식)".

#### 자유 입력 — 단독 턴 텍스트 prompt (Polestar10 자격증명 + 비밀)

Polestar10 사용자 ID + password, 그리고 SSH 비밀은 카드형 default 가 의미 없거나 보안상 카드 표시 X. 단독 턴 텍스트 prompt 로 한 번에 묶어서 받습니다 (자유 입력끼리 묶음은 위 § 강제 규칙에서 허용).

**Polestar10 자격증명** (~/.polestar10rc 부재 시 한 번만):
```
Polestar10 사용자 ID 와 password 를 알려주세요. 자원 등록·알람·메트릭
API 호출 권한이 있는 계정이 필요합니다 (보통 admin 권한 계정). 입력은
~/.polestar10rc (chmod 600) 에 저장되어 testbed-polestar10-register
와 공유되며, 다음 호출부터 묻지 않습니다.

  - Polestar10 사용자 ID:
  - Polestar10 password:
```

**SSH 비밀** (인증 방식 따라 한 번만):
1. **타겟 서버 SSH password** (인증 방식이 password 일 때)
   ```
   타겟 서버 SSH password 를 입력해 주세요:
   ```
2. **SSH key 경로** (인증 방식이 ssh_key 일 때, default `~/.ssh/id_rsa`)
   ```
   SSH key 경로를 입력해 주세요 (default ~/.ssh/id_rsa, Enter 로 default 사용):
   ```

#### KCM (사내 GitLab) — 타겟 arch 가 ARM64 인 경우만, controller fetch + scp 패턴

타겟 서버 SSH 가 통한 직후 `uname -m` 으로 아키텍처를 자동 감지합니다. ARM64 (109 DGX Spark 같은) 인 경우 KCM 에이전트는 사내 GitLab (cims2.nkia.net) 의 lucida-kcmagent 소스를 빌드합니다. 타겟 서버에는 GitLab 자격증명이 없는 게 일반적이므로 **controller (사용자 머신) 에서 소스 확보 후 scp 로 타겟에 전달** 하는 흐름. AMD64 면 본 단계 skip.

##### Step 1: controller 의 cwd 에서 lucida-kcmagent 자동 검색

```bash
KCM_CWD_PATH="${PWD}/lucida-kcmagent"
[ -d "$KCM_CWD_PATH/.git" ] && KCM_LOCAL_PATH="$KCM_CWD_PATH"
```

cwd 아래에 이미 git 레포 있으면 그걸 사용. 다음 단계 skip.

##### Step 2: cwd 부재 시 사용자 path 입력 + fallback clone

```python
AskUserQuestion(questions=[
  {
    "question": "타겟 서버가 ARM64 입니다. KCM 에이전트는 ARM64 에서 사내 GitLab (cims2.nkia.net) 의 lucida-kcmagent 소스를 빌드합니다. 타겟에 자격증명이 없는 게 일반적이라 컨트롤러에서 소스를 확보한 뒤 scp 로 타겟에 전달하는 흐름입니다. lucida-kcmagent 가 컨트롤러 어딘가에 이미 clone 돼있는지 알려주세요.",
    "header": "ARM64 KCM",
    "multiSelect": False,
    "options": [
      {"label": "현재 작업 폴더에 자동 clone (Recommended)", "description": "${PWD}/lucida-kcmagent 에 git clone https://cims2.nkia.net:8443/gitlab/lucida-kcmagent develop 진행. controller 가 사내망 + GitLab 자격증명 (LDAP/PAT/SSH key) 가지고 있어야 합니다."},
      {"label": "다른 경로에 이미 있음 — 경로 직접 입력", "description": "기존 clone 위치를 자유 입력으로 받음. 그 디렉토리의 develop branch 를 fetch+pull 후 사용."},
      {"label": "KCM 만 비활성 (다른 5종 자원만 등록)", "description": "K8s 컨테이너 메트릭 수집 X. SMS/APM/WPM/DPM/NMS 5종으로 RCA 검증. 사용자 명시 결정만 OK."}
    ]
  }
])
```

##### Step 3: 결정된 경로로 develop branch 최신화 + scp

옵션별 처리:

- **자동 clone 선택**: `git clone https://cims2.nkia.net:8443/gitlab/lucida-kcmagent.git ${PWD}/lucida-kcmagent --branch develop` 실행. 자격증명 prompt 가 뜨면 사용자가 controller 의 일반 git 워크플로 (LDAP web 로그인 후 token / PAT / SSH key) 로 통과.
- **경로 직접 입력**: 자유 입력 prompt 으로 절대 경로 받음. 그 path 의 .git 확인. 없으면 다시 prompt 또는 자동 clone 옵션 제시.
- **KCM 비활성**: bootstrap.yaml 의 `agents.kcm_disabled = true` 저장. 사용자 명시 결정.

결정된 path 는 bootstrap.yaml 의 `paths.kcm_local_source` 에 저장. dynamic-inventory-generator 가 ansible-playbook 호출 시 `-e kcm_local_path=<path>` 로 전달. agent-kcm role 이 develop fetch + pull → ansible.posix.synchronize 로 타겟 staging 에 rsync → sudo cp 로 /opt/lucida-kcmagent 이동 → build → ctr import.

> 자동 disable 금지 룰 ([ansible-failure-diagnosis.md](ansible-failure-diagnosis.md)) — controller clone 실패 (사내망 X / 자격증명 X) 시 LLM 이 자동으로 `kcm_disabled=true` 처리 X. 사용자가 명시적으로 위 "KCM 비활성" 옵션을 선택해야만 disable.

> 🚫 **출력 가이드**: prompt 안에 "예시 답변 형식" / "다음과 같이 입력" 식으로 sample value (특히 자격증명) 절대 박지 말 것. LLM 이 메모리에서 본 자격증명을 sample 로 가져오면 화면 노출 사고 (PR #30 참조).

→ 모든 답변 종합 → `~/.testbed-build/bootstrap.yaml` (chmod 600) + `~/.polestar10rc` (chmod 600). 다음 호출부터 묻지 않음. 자격증명 변경 시 사용자가 직접 yaml 편집 또는 파일 삭제 후 재인터뷰.

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
  git clone https://github.com/nkia-ai-team/testbed-services.git "$TESTBED_SVC_PATH"
fi

if [ ! -d "$RUNNER_PATH/.git" ]; then
  echo "rca-scenario-runner 레포가 없습니다. clone 합니다."
  mkdir -p "$(dirname "$RUNNER_PATH")"
  git clone https://github.com/nkia-ai-team/rca-scenario-runner.git "$RUNNER_PATH"
fi
```

git clone 실패 (PAT 만료 / private 권한 X) 시 ask-polestar10 가 아니라 직접 사용자 안내:
```
git clone 실패: <error>
  - PAT 가 ~/.git-credentials 에 있는지 확인
  - private 레포 권한 있는지 확인 (nkia-ai-team org 멤버?)
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

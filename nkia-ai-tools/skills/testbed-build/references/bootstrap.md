# Bootstrap — 자격증명 + 레포 경로

매 testbed-build 호출 첫 단계.

## ~/.testbed-build/bootstrap.yaml 스키마

```yaml
# chmod 600. 사용자 home 에 영구 보존 (run 사이 공유).

ssh:
  default_user: nkia          # SSH 기본 user (인터뷰에서 override 가능)
  ssh_key_path: ""            # 비어있으면 password 사용

polestar10:
  base_url: "https://198.51.100.104"   # 기본 endpoint (NKIA 운영. 인터뷰에서 변경 가능)
  collector_host: ""                    # 비우면 base_url 의 hostname 자동 사용. ⚠️ 사내 NAT/방화벽 환경에서 base_url 이 public IP 면 collector_host 는 따로 사내 내부 IP 박을 것. 모든 WPM/APM/SMS/KCM 패킷이 이 host 로 흐르므로 outbound 차단되면 등록 silently 실패. ansible 의 polestar10_collector_host 변수로 흘러감.
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
  kcm_source_repo: "https://cims2.nkia.net:8443/gitlab/lucida-kcmagent.git"   # ARM64 KCM source-build 시 사내 GitLab URL. default 박혀있어 사용자 인터뷰 X. 다른 GitLab 인스턴스 사용 환경이면 케이스 B 캐시 confirm 카드의 "일부 변경" 으로 수정.
  kcm_source_branch: "develop"          # default branch. 변경 빈도 낮음 — 인터뷰 X.

paths:
  testbed_services_repo: ""             # 자동 발견 결과 또는 인터뷰. 비우면 cwd → ~/dev → ~/projects → ~ 순회
  scenario_runner_repo: ""              # 동일
  ansible_playbook_root: ""             # 비우면 plugin install 디렉토리 발견

cluster:
  # production 모사 — testbed 별 별 K8s cluster 격리 (default: k3d).
  # k3d (default) = Docker 컨테이너 안 K3s. 한 호스트에 N 개 testbed 동시 운영 가능.
  # k3s (legacy)  = native single-K3s + namespace 격리 (자원/노이즈 분리 X, 권장 X).
  kind: "k3d"
  # cluster_name 은 testbed 이름 (= app_subdir) 으로 자동 도출 — 본 yaml 에 박지 X.
  # 다중 testbed 동시 운영 시 각 testbed 별 별 host port 가 inventory host vars 에 박힘:
  #   k3d_api_port (default 6443) / k3d_node_http_port (8080) / k3d_node_https_port (8443)
  #   k3d_node_nodeport_offset (30000) / k3d_node_nodeport_max (30100)
  #   scenario_runner_port (8091)
  # default 는 single-testbed 가정. 사용자가 두 번째 testbed 만들 때 인터뷰에서 다른 port 받음.
```

## ⚠️ Step 0 — 컨트롤러 도구 사전 검증

본격 인터뷰 진입 전, 컨트롤러 (Claude Code 가 실행 중인 머신) 에 필요한 CLI 도구들이 깔려있는지 확인합니다. 부재 시 자동 설치 옵션을 제공해 사용자가 `inventory_generated` / `ansible_deploy` 시점에 cryptic 에러를 보지 않도록 사전 차단.

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

## Step 0.5 — Skill 사전 권한 (allowed-tools frontmatter)

testbed-build / testbed-polestar10-register / testbed-generate-scenarios / testbed-tune-alarms 4 SKILL.md 의 frontmatter `allowed-tools` 키가 **skill 호출 시점에 필요한 Bash 패턴 (ansible-playbook / sshpass / ssh / curl / jq / git / gh / kubectl / docker / k3d 등) 을 사전 선언**. 사용자가 plugin install 시 workspace trust 한 후엔 sandbox 가 listed tool 들을 자동 허용 — 매 호출 prompt X.

→ 사용자 측 settings.json 추가 작업 불필요. 다른 사용자도 install 만 하면 동일하게 작동.

⚠️ **여전히 ChatPrompt 필요한 케이스** — 다음은 allowed-tools 로도 사전 허용 안 됨:
- self-modification (settings.json 자체 수정) — 영구 차단
- 사용자 자격증명 leak 패턴 (e.g., gh auth token 출력) — 차단
- 명백한 destructive remote 작업이 첫 시도 거부되는 경우 — 같은 명령 재시도 또는 chat 승인 후 재시도

이런 케이스는 § Destructive action chat 승인 룰 섹션 따라 처리.

## Destructive action — chat 승인 룰 (강제)

`git push` / `gh pr create` / `git merge --no-ff main` / `kubectl delete ns` / `helm uninstall` 같은 **destructive action** (data 변경 / 외부 시스템 영향) 은 Claude Code 권한 정책상 별도 chat 승인 (사용자 자연어 응답) 을 요구. AskUserQuestion 카드 응답은 의도 표현일 뿐 — 권한 시스템은 카드 응답을 destructive action 승인으로 인정 X.

→ destructive action 직전에는 **반드시 chat 으로 한 번 더 묻고 사용자 자연어 응답 받기**. 카드 → 자동 진행 패턴 사용 X (권한 시스템에 막혀 결국 chat 으로 다시 응답해야 하는 이중 응답 발생).

예시:
```
이 시나리오를 추가하고 push 할까요? 자연어로 답해 주세요:
  "응 / 진행 / PR" → git commit + push + gh pr create
  "direct push" → main 직접 push
  "로컬만" → 로컬 commit 만
  "취소" → 변경 폐기
→ _
```

오케스트레이터가 자동 진행 모드여도 **destructive action 게이트는 chat 응답 필수** — 자동화 의도 vs 권한 정책 안전망의 합의점.

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
     예시: ARM64 K3s 호스트 (203.0.113.109)

  2. Polestar10 모니터링 서버 (Polestar10 instance) — HTTP(S) 접근 필요
     RCA 분석 백엔드. 자원 등록 / 알람 정책 / 메트릭 시계열 API
     가 여기로 호출됨. 사용자 ID/PW 도 함께 필요.
     예시: Polestar10 운영 인스턴스 (https://198.51.100.104)

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
      {"label": "104 운영 (Recommended)", "description": "https://198.51.100.104 — NKIA 운영 환경 (기본)"}
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

## 외부 레포 — 자동 발견 우선, 부재 시에만 인터뷰 (조건부)

testbed-build 가 의존하는 두 외부 레포 (testbed-services / rca-scenario-runner) 의 자동 발견 + clone 절차.

**상세 절차**: [repo-discovery.md](repo-discovery.md) 를 read.
- bootstrap.yaml 의 `paths.testbed_services_repo` / `paths.scenario_runner_repo` 가 비어있거나 그 경로에 `.git` 부재 시에만 read.
- 이미 path 박혀있고 디렉토리 정상이면 본 reference 자체 skip.
- 4 step (cwd 검색 → home fallback → 결과 분기 → 진행) + 발견/clone 결과를 bootstrap.yaml 에 영구 저장

### 추가 슬롯 — 가능한 한 카드형 (default-present), 비밀만 텍스트 prompt

> Polestar10 ID/PW 는 `~/.polestar10rc` (chmod 600) 에 저장돼 testbed-polestar10-register 와 공유됨. 이미 파일이 있으면 재사용 (재인터뷰 X).

#### 카드형 (default-present 슬롯) — bootstrap.yaml 캐시 있을 때만

타겟 서버 IP 와 SSH user 는 사용자 환경마다 다르므로 **임의의 default 사전 박지 말 것**. bootstrap.yaml 에 이전 호출의 값이 있으면 카드의 (Recommended) 옵션으로 제시 + Other 자유 입력. 캐시 없으면 (첫 호출) 카드 자체 부적합 — 자유 입력 텍스트 prompt 로.

```python
# 캐시 있는 케이스 — 이전 값 = bootstrap.yaml 의 ssh.default_user / 직전 run 의 target_host
AskUserQuestion(questions=[
  {
    "question": "타겟 서버 IP/hostname 은 어떤 걸 사용하시겠어요?",
    "header": "타겟 IP",
    "multiSelect": False,
    "options": [
      {"label": f"{cached_target_host} (이전 호출 값)", "description": "bootstrap.yaml 또는 직전 run 의 manifest 에서 가져옴"}
    ]
  },
  {
    "question": "타겟 서버 SSH user 는 누구로 사용하시겠어요?",
    "header": "SSH user",
    "multiSelect": False,
    "options": [
      {"label": f"{cached_ssh_user} (이전 호출 값)", "description": "bootstrap.yaml 의 ssh.default_user"}
    ]
  }
])
# Other 가 자동 추가되어 자유 입력 가능 (다른 IP / 다른 user)

# 캐시 없는 케이스 (첫 호출) — 카드 X. interview-flow.md 의 자유 입력 텍스트 prompt 패턴 사용:
#   "타겟 서버 IP 또는 hostname 을 입력해 주세요"
#   "SSH user 를 입력해 주세요"
```

> ⚠️ **Polestar10 base_url 의 Other 케이스**: 첫 인터뷰의 P10 서버 카드에서 Other 선택 시 위 묶음과 별 턴에 자유 입력 prompt: "Polestar10 base_url 을 직접 입력해 주세요 (`https://...` 형식)".

#### 자유 입력 — 단독 턴 텍스트 prompt (Polestar10 자격증명 + 비밀)

Polestar10 사용자 ID + password, 그리고 SSH 비밀은 카드형 default 가 의미 없거나 보안상 카드 표시 X. 단독 턴 텍스트 prompt 로 한 번에 묶어서 받습니다 (자유 입력끼리 묶음은 위 § 강제 규칙에서 허용).

**Polestar10 자격증명 + 조직 ID** (~/.polestar10rc / bootstrap.yaml 둘 다 부재 시 한 번만):
```
Polestar10 사용자 ID, password, 그리고 조직 (테넌트) ID 를 알려주세요.

  - 사용자 ID + password: 자원 등록·알람·메트릭 API 호출 권한 계정 (보통
    admin 권한). ~/.polestar10rc (chmod 600) 에 저장되어
    testbed-polestar10-register 와 공유.
  - 조직 ID (organization_id, 24자리 hex): SMS/KCM 에이전트가 broker 로
    publish 할 때 SAAS_TENANT_ID 로 사용. Polestar10 web 우측 상단
    [계정] > 조직명 마우스오버 시 표시되는 24자리 hex. ~/.testbed-build/
    bootstrap.yaml 에 저장되어 다음 호출부터 묻지 않음.

다음 호출부터 모두 묻지 않습니다.

  - Polestar10 사용자 ID:
  - Polestar10 password:
  - Polestar10 조직 ID (organization_id, 24자리 hex):
```

⚠️ **organization_id 가 빈값이면 안 됨** — SMS install role 의 `polestar_organization_id | length == 0` fail-fast 가드 + KCM DaemonSet 의 `KCM_TENANT_ID` env 도 동일 변수 참조. 사용자가 잘 모르겠다고 답하면 Polestar10 web UI 직접 안내:

```
Polestar10 web (https://<base_url>) 로그인 → 우측 상단 [계정] 아이콘 →
드롭다운의 조직명 위에 마우스 오버 → tooltip 으로 24자리 hex (예:
69731678b56620b247fb279a) 가 표시됨. 그 값 그대로 입력.
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

#### KCM ARM64 setup (조건부 — 타겟 arch == arm64 + KCM 사용 시만)

ARM64 타겟의 KCM 은 사내 GitLab 의 lucida-kcmagent 소스 빌드 패턴. controller 에서 소스 확보 후 scp 로 타겟에 전달.

⚠️ **bootstrap 단계에선 URL/자격증명 prompt X** — `kcm_source_repo` default 가 이미 박혀있어 첫 인터뷰는 흐름 끊지 X. 실제 처리는 phase loop 진입 후 ARM64 감지된 시점에 [kcm-arm64-setup.md](kcm-arm64-setup.md) 의 Step 1~3 (cwd 자동 검색 → 사용자 path 입력 → fallback clone) 만 발동. clone 실패 (사내망 X / 자격증명 만료) 시 그때 통과 방법 사용자 prompt — lazy.

**상세 절차**: [kcm-arm64-setup.md](kcm-arm64-setup.md) 를 read.
- target.arch == arm64 일 때만 read. AMD64 면 본 reference skip.
- 결정된 path 는 bootstrap.yaml 의 `paths.kcm_local_source` 저장

→ 모든 답변 종합 → `~/.testbed-build/bootstrap.yaml` (chmod 600) + `~/.polestar10rc` (chmod 600). 다음 호출부터 묻지 않음. 자격증명 변경 시 사용자가 직접 yaml 편집 또는 파일 삭제 후 재인터뷰.

## Polestar10 자격증명 — 2층 구조

testbed-build 의 bootstrap.yaml 은 base_url + user 만 캐시. **password 는 ~/.polestar10rc** 가 source of truth (testbed-polestar10-register 와 공유).

```bash
# ~/.polestar10rc (chmod 600, 기존 testbed-polestar10-register 가 관리)
export POLESTAR10_BASE_URL="https://198.51.100.96"
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

### 케이스 A — bootstrap.yaml 부재

**인터뷰 무조건 실행**. 다른 캐시 파일 (`~/.polestar10rc` / 레포 디렉토리 / `~/.git-credentials`) 이 모두 존재하더라도 skip 금지. 캐시는 인터뷰 옵션의 default value 자동 채우기에만 사용.

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
```

### 케이스 B — bootstrap.yaml 존재 (캐시 confirm 카드 강제) ⭐

**캐시값을 사용자에게 표시 + AskUserQuestion 카드로 확인 받기**. "yaml 있으니 인터뷰 전체 skip 하고 바로 다음 phase" 패턴 **금지**. 사용자는 매 세션 시작 시 캐시값 명시적으로 확인할 권리가 있음.

```bash
if [ -f ~/.testbed-build/bootstrap.yaml ]; then
  # 1. 캐시값 추출
  P10_URL=$(yq '.polestar10.base_url' ~/.testbed-build/bootstrap.yaml)
  P10_USER=$(yq '.polestar10.user' ~/.testbed-build/bootstrap.yaml)
  ORG_ID=$(yq '.polestar10.organization_id' ~/.testbed-build/bootstrap.yaml)
  SSH_USER=$(yq '.ssh.default_user' ~/.testbed-build/bootstrap.yaml)
  TESTBED_SVC=$(yq '.paths.testbed_services_repo' ~/.testbed-build/bootstrap.yaml)
  RUNNER=$(yq '.paths.scenario_runner_repo' ~/.testbed-build/bootstrap.yaml)

  # 2. 사용자에게 표시
  cat <<EOF
=== 캐시된 부트스트랩 설정 발견 ===

Polestar10:        ${P10_URL} (user: ${P10_USER})
조직 ID:            ${ORG_ID:-(빈값 — 인터뷰 필요)}
SSH default user:   ${SSH_USER}
testbed-services:   ${TESTBED_SVC}
scenario-runner:    ${RUNNER}
EOF

  # 3. AskUserQuestion 카드
  AskUserQuestion(questions=[
    {
      "question": "위 캐시된 설정으로 진행할까요? 환경이 바뀌었으면 재인터뷰 또는 일부 변경 가능합니다.",
      "header": "캐시 설정 확인",
      "multiSelect": False,
      "options": [
        {"label": "캐시 그대로 진행 (Recommended)", "description": "값 변경 X. 즉시 다음 phase 진행"},
        {"label": "일부 슬롯 변경", "description": "어느 슬롯 (P10 URL / SSH user / 레포 경로 등) 변경할지 추가 prompt"},
        {"label": "전체 재인터뷰", "description": "bootstrap.yaml 백업 후 처음부터 인터뷰 (다른 환경/머신 으로 이동 시)"}
      ]
    }
  ])
fi
```

선택 별 분기:
- **캐시 그대로 진행** → 다음 phase 로 즉시
- **일부 슬롯 변경** → 변경할 슬롯 multi-select → 해당 슬롯만 자유 입력으로 받아 yaml patch
- **전체 재인터뷰** → `mv ~/.testbed-build/bootstrap.yaml ~/.testbed-build/bootstrap.yaml.bak.<ts>` 후 케이스 A 루트로

### 케이스 A/B 공통 — 추가 sanity check

```bash
# 추가 sanity check (양쪽 케이스 모두)
[ -f ~/.polestar10rc ] || trigger_polestar10_bootstrap
[ -d "$TESTBED_SVC_PATH/.git" ] || prompt_clone_testbed_services
[ -d "$RUNNER_PATH/.git" ] || prompt_clone_runner

# polestar10 connectivity 사전 체크 (precheck phase 에서)
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
| Polestar10 organization_id | **skip if cached** | bootstrap.yaml | bootstrap.yaml 의 polestar10.organization_id 가 빈값/누락이면 인터뷰. SMS/KCM 의 SAAS_TENANT_ID 로 사용 — 빈값 진행 X (fail-fast) |
| 레포 clone yes/no | **skip if 디렉토리 존재** | filesystem | 둘 다 있으면 자동 yes |
| 레포 경로 | always ask (default 표시) | bootstrap.yaml 또는 `~/dev/...` | 디렉토리 존재 시 그 경로가 default |
| git PAT 입력 | **skip if cached** | ~/.git-credentials | 파일 있으면 PAT 인터뷰 skip |
| 분기 전략 | always ask (default 표시) | bootstrap.yaml 또는 `feature-pr` | feature-pr / direct-develop |

규칙:
- **always ask** = 캐시 파일이 있어도 AskUserQuestion 의 첫 옵션 (Recommended) 으로 표시한 후 사용자 confirm 필요. "확인 없이 캐시값 그대로 yaml 작성" 은 금지.
- **skip if cached** = 해당 캐시 파일이 있으면 인터뷰 자체를 생략. 부재 시에만 인터뷰 트리거.

위 규칙은 첫 호출 (bootstrap.yaml 부재 — 케이스 A) 에만 해당. bootstrap.yaml 이 있으면 (케이스 B) 위 § 부트스트랩 검증의 **캐시 confirm 카드** 가 진입점. 사용자가 "캐시 그대로 진행" 선택 시에만 인터뷰 skip — "일부 변경" / "전체 재인터뷰" 선택 시는 해당 슬롯들 다시 인터뷰.

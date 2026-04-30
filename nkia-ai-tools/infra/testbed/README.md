# RCA Testbed — Ansible 자동화

K3s + 서비스 (Spring boot + DB) + 에이전트 4종 (WPM/APM/KCM/SMS) 을 한 번에 깔아주는 Ansible playbook.
Claude Code 없이 `ansible-playbook` 직접 실행이 1차 인터페이스.

## 디렉토리 구조

```
infra/testbed/
├── README.md
├── docs/
│   └── runbooks/manual-e2e.md           # 수동 E2E 재현 가이드
└── playbooks/
    ├── site.yml                         # 호스트→롤 매핑
    ├── requirements.yml                 # Ansible collections
    ├── group_vars/all.yml               # 공통 변수 (collector hosts, K3s 옵션, 에이전트 URL)
    ├── inventory/
    │   ├── amd64-sample.yml
    │   └── arm64-sample.yml
    └── roles/
        ├── common/                      # Docker, K3s, metrics-server, firewall, Go(ARM)
        ├── service-k8s/                 # Spring boot 앱 + DB (PG 본 구현, MySQL/MariaDB/CUBRID/Tibero placeholder)
        ├── agent-wpm/                   # JVM agent jar 다운로드 → host /opt/polestar10/wpm
        ├── agent-apm/                   # JVM agent jar 다운로드 → host /opt/polestar10/apm
        ├── agent-kcm/                   # K3s DaemonSet (AMD: image pull / ARM: lucida-kcmagent 소스 빌드)
        └── agent-sms/                   # 호스트 systemd (사전 감지 → 이미 있으면 skip)
```

## 사전 요구사항

### 컨트롤러

```sh
python3 -m venv ~/.venv-ansible
~/.venv-ansible/bin/pip install ansible
~/.venv-ansible/bin/ansible-galaxy collection install -r playbooks/requirements.yml

# (선택) inventory 에 ansible_password 평문 쓰는 경우
brew install hudochenkov/sshpass/sshpass     # Mac
sudo apt install sshpass                     # Linux
```

### 타겟 호스트

- Linux + systemd (Ubuntu 22.04+/Debian 12+/RHEL/Rocky 9+ 권장)
- Python 3 (`/usr/bin/python3`)
- SSH 접근 + sudo 권한
- (ARM 타겟) gcc — 없으면 `apt install build-essential` 사전. Go 는 common 롤이 자동 설치

## 빠른 시작

### 1. 환경변수 export (자격증명 + 타겟 + 폴스타10 조직)

inventory sample 의 connection 값은 모두 환경변수에서 읽습니다 — git 에 평문 자격증명 commit 방지. testbed-build 스킬은 인터뷰로 받은 값으로 런타임 inventory 를 생성하므로 본 단계 자동화. 수동 ansible-playbook 실행 시:

```sh
# 필수
export TESTBED_HOST=<TARGET-HOST>               # 타겟 호스트 IP
export TESTBED_USER=nkia                          # SSH 사용자
export POLESTAR_ORG_ID=<24-hex tenant id>         # SMS install 시 SAAS_TENANT_ID 채움 (폴스타10 web [계정] > 조직명 마우스오버)

# SSH 인증 — 둘 중 하나
export TESTBED_SSH_KEY=~/.ssh/id_ed25519          # 권장: ssh key
# 또는
export TESTBED_PASSWORD=<password>                # 비추: 평문 password

# Sudo 인증 — 미설정 시 TESTBED_PASSWORD 재사용
export TESTBED_BECOME_PASSWORD=<sudo password>

# Private repo 자산 다운로드 — gh CLI 또는 PAT (다음 섹션 참조)
export GITHUB_PAT=<token>
```

`testbed_services` / `app_repo` / `app_subdir` / `app_namespace` 등 도메인 변수는 inventory `vars:` 또는 `-e` 로 override (다른 테스트베드 도메인 추가 시 [§ 다른 테스트베드 추가하기](#다른-테스트베드-추가하기-nkiaai-540-후속-작업자용) 참조).

### 2. GitHub 인증 (둘 중 하나)

WPM/APM/SMS 자산은 `nkia-ai-team/polestar-agents-binaries` (private repo) 에서 받습니다.

**옵션 A — gh CLI** (권장 — 이미 `gh` 쓰는 팀원은 추가 작업 없음):
```sh
gh auth login         # 한 번만. NKIA org 의 멤버이면 OK
gh auth status        # logged in 확인
```
ansible 이 자동으로 `gh auth token` 으로 token 추출.

**옵션 B — Personal Access Token**:
```sh
export GITHUB_PAT=ghp_xxx        # repo scope. NKIA org SAML SSO 면 별도 인가 필요
```

둘 다 미설정 시 WPM/APM/SMS 다운로드 task 는 skip + 안내 메시지 출력 — common + service-k8s 까지만 동작.

`group_vars/all.yml` 의 `wpm_release_tag` / `apm_release_tag` / `sms_release_tag` + `*_asset_name` 으로 어떤 release 를 쓸지 결정.

### 3. 실행

```sh
cd nkia-ai-tools/infra/testbed/playbooks

# 문법 검증
ansible-playbook --syntax-check -i inventory/arm64-sample.yml site.yml

# dry-run
ansible-playbook --check --diff -i inventory/arm64-sample.yml site.yml

# 실 실행 (1회차 — 5~25분, ARM+KCM 소스 빌드 시 추가)
ansible-playbook -i inventory/arm64-sample.yml site.yml

# 멱등성 검증 (2회차 — 모든 task changed=0)
ansible-playbook -i inventory/arm64-sample.yml site.yml
```

### 4. 결과 확인

```sh
ssh <target> 'sudo /usr/local/bin/k3s kubectl get pods -A'
curl http://<target>:30080/actuator/health
```

## 멱등성 보장

모든 task 는 두 번째 실행 시 `changed=0` 이 되도록 설계:

- **사전 감지**: `command -v docker`, `systemctl is-active k3s`, `pgrep sms-agent` 등으로 이미 있는 자원 skip
- **manifest 적용**: `kubectl apply` 자체가 idempotent
- **packages**: apt/dnf 모듈 idempotent
- **변경 추적**: `changed_when:` 명시
- **handler**: 변경 시에만 docker/systemd restart

SMS 만 호스트 systemd 라 다른 시스템에서 깔려 있을 가능성이 높음 → 사전 감지 후 skip 이 기본. 강제 재설치 시 `sms_force_reinstall=true`.

## 6 롤 책임 분담표

| 롤 | 책임 | ARM 분기 | 비고 |
|---|---|---|---|
| `common` | 방화벽 + Docker + K3s + metrics-server + Go(ARM) | Go 1.22 자동 설치 | metrics-server 는 `--kubelet-insecure-tls` 강제 (KCM 의존) |
| `service-k8s` | testbed-services monorepo deploy — git clone + `k8s/build-and-deploy.sh` 호출 (자체 5 service build + manifest apply) | image build 가 ARM native | namespace/secret/configmap/DB/5 service 모두 monorepo 의 `k8s/` 매니페스트가 정의 (NKIAAI-570) |
| `agent-wpm` | JVM jar 다운로드 → `/opt/polestar10/wpm/agent.jar` | 동일 (JVM 아키 무관) | service-k8s app deployment 가 hostPath mount |
| `agent-apm` | 동일 | 동일 | 동일 |
| `agent-kcm` | RBAC + DaemonSet apply | ARM = lucida-kcmagent 소스 scp → 타겟 빌드 (Go) → docker build → ctr import | metrics-server 미설치 시 KCM 메트릭 빈 값 |
| `agent-sms` | tarball install + systemd unit | ARM = qemu-user-static + binfmt-support → AMD 바이너리 동일 사용 | **사전 감지** (`pgrep sms-agent` / `systemctl is-active`) → 이미 있으면 skip. `sms_force_reinstall=true` 로 우회. report_interval 60s (qemu 부하 완화) |

## 다른 테스트베드 추가하기 (NKIAAI-540 후속 작업자용)

ansible playbook 본체는 **테스트베드 도메인을 모름** — 어떤 서비스/구조든 처리. testbed-services repo 가 빌드/배포 로직을 책임. 다른 도메인의 테스트베드 (예: 은행 시스템) 추가 시:

### 절차

1. **testbed-services repo 에 새 subdir 추가**
   ```
   testbed-services/  (NKIAAI-570)
   ├── plopvape-shop/         ← 기존
   └── core-banking/          ← 새 testbed
       ├── account-service/Dockerfile
       ├── transfer-service/Dockerfile
       ├── ledger-service/Dockerfile
       └── k8s/
           ├── build-and-deploy.sh   ← 표준 인터페이스 (필수)
           └── *.yaml                 ← namespace/secret/configmap/deploy/svc
   ```

2. **새 inventory 작성** (`inventory/banking-target.yml`):
   ```yaml
   all:
     children:
       testbed:
         hosts:
           banking-target:
             ansible_host: <target ip>
             ansible_user: <user>
             ...
         vars:
           app_namespace: "rca-banking"        # K8s namespace 격리
           app_repo: "https://github.com/nkia-ai-team/testbed-services"
           app_subdir: "core-banking"          # repo 내 subdir
           testbed_services: [account, transfer, ledger]
   ```

3. **단발 실행** (ansible playbook 본체 그대로):
   ```sh
   export GITHUB_PAT=<token>
   export POLESTAR_ORG_ID=<24-hex tenant id>   # SMS install 필수
   ansible-playbook -i inventory/banking-target.yml site.yml
   ```

### 변경 영역 매트릭스

| 변경 종류 | 어디서 변경? | 예시 |
|---|---|---|
| 서비스 개수 / 이름 | inventory + testbed-services repo | `testbed_services: [...]` + Dockerfile 추가 |
| 언어 (Java→Python/Node) | testbed-services repo | Dockerfile 의 base image 만 |
| DB 종류 (PG→MariaDB) | testbed-services repo | `k8s/10-mariadb.yaml` 로 매니페스트 교체 |
| 도메인 (e-commerce→banking) | testbed-services repo | 새 subdir |
| K8s namespace | inventory | `app_namespace: "rca-xxx"` |
| 사용 안 할 에이전트 | inventory | `wpm_enabled: false` (Python only 등) |
| 폴스타10 조직 | env | `POLESTAR_ORG_ID=...` |
| 타겟 호스트 | inventory | `ansible_host: ...` |

**ansible playbook 본체 (이 디렉토리) 변경 X**. 한 번 깔면 모든 테스트베드 처리.

### 같은 호스트/클러스터 다중 테스트베드 시 에이전트 공유

같은 109 + 같은 K3s 에 plopvape-shop + core-banking 두 테스트베드 운영:

| 에이전트 | 단위 | 동일 호스트/클러스터에 N testbed | 다른 호스트/클러스터 |
|---|---|---|---|
| **SMS** | 호스트 1대 | **공유 — 1개로 충분** | 호스트마다 별도 |
| **KCM** | K8s 클러스터 1개 | **공유 — DaemonSet 1개**가 모든 namespace 통합 | 다른 K3s 면 별도 |
| **WPM** | JVM 단위 | jar 1개 (`/opt/polestar10/wpm/wpmagent.jar`) 공유, conf 만 service 별 N개 | 호스트마다 별도 jar |
| **APM (OTel)** | JVM 단위 | jar 1개 (`opentelemetry-javaagent.jar`) 모든 service 공유 | 호스트마다 별도 |

→ N testbed 운영해도 SMS 1 + KCM 1 + WPM/APM jar 1개씩, conf 만 testbed_services 합본만큼.

### Caveats — 알려진 한계

1. **폴스타10 standby DB drift**: pod rolling update 로 옛 agent ID 의 K8s pod 이 죽어도 폴스타10 backend "관리대상 추가 → 애플리케이션" 큐에서 stale standby record 가 자동 cleanup 되지 않음. broker 연결도 끊긴 상태인데 web UI 에 계속 남음. **540 자동화 코드와 무관 — 폴스타10 자체 한계**. delete API 가 standby record 를 안 지우는 듯. 운영팀 확인 또는 backend DB 직접 청소가 진짜 해결.
2. **SMS agentId 재install 시 갱신 → 옛 ID 등록 시 DOWN**: SMS install 시 매번 `MA_<host>_<YYYYMMDDhhmmss>` 패턴의 새 agentId 가 생성됨. 이전 install 의 stale agentId 가 standby 큐에 남아있을 때 그걸 register 하면 hostname 은 일치해도 실제 daemon 의 publish agentId 와 안 맞아 backend 가 heartbeat 매칭 실패 → `availabilityStatus: DOWN`. **해결 절차** (testbed-polestar10-register 스킬에 흐름 박아야 함):
   1. `/api/sms/hosts/delete` 로 옛 agentId 등록 제거
   2. 109 SMS daemon 재시작 (`magentctl -stop` + `-start`)
   3. 30~60s 대기 후 standby 재조회 — 새 agentId 등장 확인
   4. 새 agentId 로 `/api/sms/standby-hosts/register`
   5. 30s 후 `availabilityStatus: UP` 확인
2. **`testbed_services` 배열 + repo 내 SERVICES 배열 이중 정의**: 어긋나면 WPM conf vs 실제 service 불일치. 향후 generator 로 단일 정의 통합 가능.
3. **KCM 사내 GitLab 의존 (ARM)**: `lucida-kcmagent` 소스 빌드 경로. 외부 환경에선 안 됨. polestar-agents-binaries 에 KCM ARM 빌드도 publish 필요 (NKIAAI-537 후속).
4. **DPM (DB) / NMS (네트워크 장비)**: SoT 6 종 스택 중 540 본체에 없음. testbed-build 스킬 후속 sub-skill 영역.


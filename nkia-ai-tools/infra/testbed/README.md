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

### 1. inventory 채우기

`inventory/amd64-sample.yml` 또는 `arm64-sample.yml` 복사 + 타겟 정보 채우기:

```yaml
all:
  children:
    testbed:
      hosts:
        my-target:
          ansible_host: 10.0.0.42
          ansible_user: ubuntu
          # ssh key 권장. 패스워드는 ansible-vault:
          # ansible-vault encrypt_string 'PASSWORD' --name 'ansible_password'
      vars:
        db_engine: postgres
        app_repo: "https://github.com/your-org/your-spring-boot-app"
        app_version: main
        app_nodeport: 30080
```

### 2. 에이전트 자산 URL 채우기

`group_vars/all.yml` 에 polestar-agents-binaries Releases URL 입력:

```yaml
wpm_agent_url: "https://.../wpm-agent.jar"
apm_agent_url: "https://.../apm-agent.jar"
kcm_image_url_amd64: "https://.../kcm-amd64.tar"
sms_agent_url: "https://.../sms-agent-linux-amd64.tar.gz"

wpm_agent_version: "1.0.0"
apm_agent_version: "1.0.0"
kcm_agent_version: "1.0.0"
sms_agent_version: "1.0.0"
```

URL 이 빈 값이면 해당 에이전트 task 는 안내 메시지 출력 후 skip — common + service-k8s 만 동작합니다.

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
| `service-k8s` | namespace + DB + Spring boot 앱 (host build → ctr import → K8s deploy) | image build 가 ARM native | postgres 본 구현. mysql/mariadb/cubrid/tibero placeholder — assert 가드 |
| `agent-wpm` | JVM jar 다운로드 → `/opt/polestar10/wpm/agent.jar` | 동일 (JVM 아키 무관) | service-k8s app deployment 가 hostPath mount |
| `agent-apm` | 동일 | 동일 | 동일 |
| `agent-kcm` | RBAC + DaemonSet apply | ARM = lucida-kcmagent 소스 scp → 타겟 빌드 (Go) → docker build → ctr import | metrics-server 미설치 시 KCM 메트릭 빈 값 |
| `agent-sms` | tarball install + systemd unit | ARM = qemu-user-static + binfmt-support → AMD 바이너리 동일 사용 | **사전 감지** (`pgrep sms-agent` / `systemctl is-active`) → 이미 있으면 skip. `sms_force_reinstall=true` 로 우회. report_interval 60s (qemu 부하 완화) |

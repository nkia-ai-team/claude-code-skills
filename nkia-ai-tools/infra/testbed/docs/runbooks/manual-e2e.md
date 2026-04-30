# Manual E2E Runbook

본 playbook 을 실제로 한 번 돌려보면서 마주치는 암묵 지식 + 환경별 절차 기록.
Claude Code 없이 `ansible-playbook` 만으로 동일 재현 가능.

---

## 0. 컨트롤러 준비

### Mac (Apple Silicon / Intel 공통)

```sh
python3 -m venv ~/.venv-ansible
source ~/.venv-ansible/bin/activate
pip install --upgrade pip
pip install ansible
ansible-galaxy collection install -r playbooks/requirements.yml
brew install hudochenkov/sshpass/sshpass        # 패스워드 inventory 사용 시
```

### Linux

```sh
python3 -m venv ~/.venv-ansible
source ~/.venv-ansible/bin/activate
pip install ansible
ansible-galaxy collection install -r playbooks/requirements.yml
sudo apt install -y sshpass
```

검증:

```sh
ansible --version | head -3
ansible-playbook --syntax-check -i playbooks/inventory/arm64-sample.yml playbooks/site.yml
```

---

## 1. 검증 타겟별 절차

### Path A — Mac multipass (격리 + cleanup 깔끔)

Mac host arch 가 그대로 VM arch:
- Apple Silicon Mac → ARM64 VM
- Intel Mac → AMD64 VM

```sh
brew install --cask multipass
multipass launch 24.04 --name testbed --cpus 2 --memory 8G --disk 30G

# ssh key 주입
multipass exec testbed -- bash -c "echo $(cat ~/.ssh/id_rsa.pub) >> ~/.ssh/authorized_keys"

# VM IP 확인
multipass info testbed | grep IPv4

# inventory 작성
cat > playbooks/inventory/multipass.yml <<'EOF'
all:
  children:
    testbed:
      hosts:
        multipass-target:
          ansible_host: 192.168.64.7    # multipass info 결과로 교체
          ansible_user: ubuntu
          ansible_ssh_private_key_file: ~/.ssh/id_rsa
          ansible_python_interpreter: /usr/bin/python3
      vars:
        db_engine: postgres
        app_repo: "https://github.com/your-org/your-spring-boot-app"
        app_version: main
        app_nodeport: 30080
EOF

ansible -i playbooks/inventory/multipass.yml all -m ping
```

cleanup:

```sh
multipass stop testbed && multipass delete testbed && multipass purge
```

### Path B — 일반 Linux 타겟

```sh
ssh-copy-id -i ~/.ssh/id_rsa.pub <user>@<target-ip>
# inventory/amd64-sample.yml 또는 arm64-sample.yml 복사 후 수정
ansible -i playbooks/inventory/<your>.yml all -m ping
```

### Path C — 기존 K3s 가 도는 호스트를 wipe 후 재구축

⚠️ 기존 cluster + workload 다 지움. 자동화 완성 후 재등록 가능 가정 하에만.

```sh
ssh <target>

# K3s uninstall
sudo /usr/local/bin/k3s-uninstall.sh

# Docker 운영 컨테이너 보존하려면 그대로. 정말 깨끗이 원하면:
sudo docker stop $(sudo docker ps -aq)
sudo docker rm $(sudo docker ps -aq)
sudo docker system prune -af --volumes

# iptables rule 정리 (K3s 가 만든 룰만 — 신중)
sudo iptables-save | grep -v KUBE | grep -v CNI | sudo iptables-restore

# 컨트롤러로 복귀 후 본 playbook
exit
ansible-playbook -i inventory/<your>.yml site.yml
```

---

## 2. 실행 시퀀스

### 2-1. dry-run

```sh
ansible-playbook --check --diff -i inventory/<your>.yml site.yml
```

`--check` 모드는 일부 모듈 (`command`, `shell`) 은 skip 처리됨. 실제 동작은 다음 단계에서.

### 2-2. 1회차 실행

```sh
time ansible-playbook -i inventory/<your>.yml site.yml
```

기대 시간:
- AMD + 자산 URL 미설정: 5~10분
- AMD + 자산 URL 다 설정: 10~15분
- ARM + KCM 소스 빌드: 15~25분 (Go 빌드 10~15분 + lucida-kcmagent clone 시간)

기대 결과:
- `failed=0`, `unreachable=0`
- common 처음이면 K3s/metrics-server/Go(ARM) changed=1
- service-k8s namespace/DB/app 모두 changed=1
- agent-* URL 설정에 따라 changed=1 또는 skip 메시지

### 2-3. 2회차 실행 (멱등성 검증)

```sh
time ansible-playbook -i inventory/<your>.yml site.yml
```

기대 결과:
- 모든 task `ok=N changed=0`
- 시간 30초~2분

changed != 0 이면 `--diff` 로 어떤 file/manifest 가 다시 변경되는지 확인.

### 2-4. 결과 검증

```sh
# K3s 클러스터
ssh <target> 'sudo /usr/local/bin/k3s kubectl get pods -A'

# 앱 헬스체크
curl -fsS http://<target>:30080/actuator/health

# 4 에이전트 UP (104 collector)
ssh sjbang@192.168.230.104 'docker logs polestar-app-wpm-1 2>&1 | tail -200 | grep -E "(WPM|APM|KCM|SMS).*managementStatus=UP"'

# metrics-server 정상
ssh <target> 'sudo /usr/local/bin/k3s kubectl top nodes'
```

`top nodes` 가 Empty/Error 면 `--kubelet-insecure-tls` flag 누락.

---

## 3. 자주 만나는 에러

| 단계 | 에러 | 원인 | 해결 |
|---|---|---|---|
| common/firewall | `community.general.ufw` not found | collection 미설치 | `ansible-galaxy collection install -r playbooks/requirements.yml` |
| common/docker | `Failed to fetch ...` | 사내망에서 docker.com 막힘 | inventory 에 `http_proxy`/`https_proxy` env 추가 또는 docker 사전 설치 |
| common/k3s | `wait_for: timeout` on 6443 | K3s 설치 후 server 기동 지연 | timeout 90→180초 또는 재실행 |
| common/metrics-server | `replace: regex no match` | upstream YAML args 형식 변경 | `metrics_server_version` 갱신 후 regex 검토 |
| common/go-toolchain | `go: command not found` | symlink 권한 또는 PATH | `ls -la /usr/local/bin/go` + `export PATH=/usr/local/go/bin:$PATH` |
| service-k8s/db | pod 대기 timeout | PVC 용량 또는 storage class | `kubectl get pvc -n testbed-app` + `kubectl describe pod` |
| service-k8s/app | `docker build` 실패 | Dockerfile 누락 또는 base image 접근 불가 | git repo 안 Dockerfile + base image registry 도달 |
| service-k8s/app | `Pod ImagePullBackOff` | 이미지가 K3s containerd 에 import 안 됨 | 수동: `docker save <image> \| sudo k3s ctr -n k8s.io images import -` |
| agent-kcm/ARM | `git: clone fail (auth)` | 사내 GitLab 인증 | git config + PAT 또는 ssh key 인증 |
| agent-kcm | `kubectl rollout status timeout` | metrics-server 누락 또는 RBAC 누락 | `kubectl logs -n kcm ds/kcm-agent` |
| agent-sms/ARM | `Exec format error` | binfmt_misc 미등록 | `sudo update-binfmts --enable qemu-x86_64` |
| agent-sms | "already running — skip" | 호스트에 이미 SMS 도는 중 (정상) | 강제 재설치 시 `--extra-vars sms_force_reinstall=true` |

---

## 4. 실행 로그 보관

```sh
ansible-playbook -i inventory/<your>.yml site.yml -v 2>&1 | tee logs/run1.log
ansible-playbook -i inventory/<your>.yml site.yml -v 2>&1 | tee logs/run2.log
ssh <target> 'sudo /usr/local/bin/k3s kubectl get pods -A -o wide' > logs/pods.txt
ssh sjbang@192.168.230.104 'docker logs polestar-app-wpm-1 2>&1 | tail -300' > logs/wpm-collector.log
```

`logs/` 는 `.gitignore` 처리 권장.

---

## 5. cleanup

### 본 playbook 으로 만든 리소스만 제거

```sh
ssh <target> 'sudo /usr/local/bin/k3s kubectl delete ns testbed-app kcm --ignore-not-found'
ssh <target> 'sudo systemctl disable --now sms-agent || true'
ssh <target> 'sudo rm -rf /opt/polestar10 /opt/lucida-kcmagent'
```

### multipass VM 제거

```sh
multipass stop testbed && multipass delete testbed && multipass purge
```

### K3s 자체 제거

```sh
ssh <target> 'sudo /usr/local/bin/k3s-uninstall.sh'
```

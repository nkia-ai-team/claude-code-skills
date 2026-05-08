# Dynamic Inventory Generator

`inventory_generated` — interview.yaml + bootstrap.yaml → `runs/<RUN_ID>/inventory.yml`.

## ⚠️ Ansible 변수 우선순위 함정 — host-level vars 강제

Ansible 의 변수 우선순위 룰:

```
playbook group_vars/all  >  inventory file group vars  >  inventory file host vars (낮음)

  ↑ 이게 제일 높은 게 아님!                          ↑ 이게 제일 높은 게 아님 ←—  ↑ 호스트 vars 가
                                                                               group_vars/all 보다 낮음
```

**실제로는** `host_vars` (host 단위) 가 `inventory file group vars` 보다 우선. 그리고 `playbook group_vars/all` 이 둘을 다 이김. 본 ansible playbook 의 `group_vars/all.yml` 에는 **plopvape-shop default 가 박혀있어서**, inventory 의 group vars (`testbed:vars:`) 에 다른 값을 써도 무시됨 (회고 P0 #3 의 root cause).

### 해결책: testbed 식별 변수는 모두 host-level 로 generate

```yaml
all:
  children:
    testbed:
      hosts:
        {{ALIAS}}:
          # === connection (이미 host-level) ===
          ansible_host: "{{TARGET_HOST}}"
          ansible_user: "{{TARGET_USER}}"
          ansible_password: "..."
          ansible_become_password: "..."
          ansible_python_interpreter: /usr/bin/python3

          # === testbed identity (host-level 로 강제 — group_vars/all 의 default 를 이김) ===
          app_repo: "{{APP_REPO}}"               # 예: https://github.com/nkia-ai-team/testbed-services
          app_version: "{{BRANCH}}"
          app_subdir: "{{APP_SUBDIR}}"           # 예: social-feed (신규) / plopvape-shop (기존)
          app_namespace: "{{NAMESPACE}}"
          testbed_services: {{TESTBED_SERVICES}} # 예: [post, feed, comment, notification]
          db_kind: "{{DB_KIND}}"

          # === KCM (ARM64 + enabled 시) — controller fetch + scp 패턴 ===
          # 타겟에는 GitLab 자격증명 없는 게 일반적이라 controller 에서
          # 소스 확보 후 scp/rsync 로 전달. agent-kcm role 이 사용.
          kcm_enabled: {{KCM_ENABLED}}           # 사용자 인터뷰 결정 (KCM 비활성 명시 선택 시만 false)
          kcm_local_path: "{{KCM_LOCAL_PATH}}"   # controller 의 lucida-kcmagent 절대 경로. bootstrap.paths.kcm_local_source.
          kcm_source_branch: "{{KCM_SOURCE_BRANCH}}"  # default `develop`

          # === Polestar10 broker / collector / 조직 (host-level 강제) ===
          # group_vars/all.yml 에 default 박혀있는 변수들. 인스턴스별로 다를 수 있어
          # host-level 로 override. 빈값/누락이면 SMS/KCM standby 미감지 → PARTIAL.
          polestar10_collector_host: "{{POLESTAR10_COLLECTOR_HOST}}"   # bootstrap.polestar10.base_url 의 hostname
          polestar_organization_id: "{{POLESTAR_ORGANIZATION_ID}}"     # bootstrap.polestar10.organization_id (24-hex SAAS_TENANT_ID)
          polestar10_kcm_collector_port: {{POLESTAR10_KCM_COLLECTOR_PORT}}   # default 7575 (KCM helm chart의 kcm.addr port)
          polestar10_sms_broker_port: {{POLESTAR10_SMS_BROKER_PORT}}        # default 1883

          # === Cluster 격리 (production 모사 — testbed 별 별 K8s cluster) ===
          # default cluster_kind=k3d. 한 호스트에 여러 testbed 동시 운영 시 cluster_name + 모든 k3d_*_port 가
          # testbed 마다 달라야 충돌 회피.
          cluster_kind: "{{CLUSTER_KIND}}"                    # k3d (default) | k3s (legacy)
          cluster_name: "{{CLUSTER_NAME}}"                    # 보통 testbed 이름 = app_subdir
          kubeconfig_path: "{{KUBECONFIG_PATH}}"              # /home/<user>/.kube/<cluster_name>.yaml
          k3d_api_port: {{K3D_API_PORT}}                      # cluster API server (default 6443; 다중 testbed 시 6444, 6445)
          k3d_node_http_port: {{K3D_NODE_HTTP_PORT}}          # default 8080
          k3d_node_https_port: {{K3D_NODE_HTTPS_PORT}}        # default 8443
          k3d_node_nodeport_offset: {{K3D_NODE_NODEPORT_OFFSET}}   # default 30000 (NodePort range 시작)
          k3d_node_nodeport_max: {{K3D_NODE_NODEPORT_MAX}}        # default 30100 (NodePort range 끝)

          # === scenario-runner (testbed 별 별 인스턴스) ===
          scenario_runner_port: {{SCENARIO_RUNNER_PORT}}           # default 8091 (다중 testbed 시 8092, 8093)
          # scenario_runner_install_dir 는 group_vars 의 default 가 cluster_name 기반이라 별도 override 불필요

          # === 신규 testbed 시 services-author 가 만든 정보 ===
          # is_new_variant=true 면 services_author 산출 (manifest.scenario_hints) 도 vars 로 흘려보내
          # 시나리오 생성 phase 가 host vars 로 직접 읽을 수 있게.
      # === 옵션 외 항목은 group vars 가능 (덜 민감) ===
      vars:
        # 서비스 + namespace 같이 testbed 를 식별하는 변수는 위 host vars 에 두고,
        # 여기는 진짜 group-wide 옵션만 (예: ansible 동작 옵션).
```

> **금기**: `app_subdir`, `testbed_services`, `app_namespace` 같이 testbed 를 식별하는 변수는 절대 group vars 에 두지 X. 항상 host-level 로 generate. 안 그러면 `group_vars/all.yml` 의 default 가 이김.

대안: ansible-playbook 호출 시 `--extra-vars` 로 전달. 모든 source 보다 우선순위 높음. 단 yaml 가독성 떨어져서 host-level vars 가 권장.

## 골격 — arm64-sample.yml 기반

[playbooks/inventory/arm64-sample.yml](../../../infra/testbed/playbooks/inventory/arm64-sample.yml) 형식 그대로 mimic.
아래 골격은 connection vars 뿐 아니라 testbed 식별 / Polestar10 / k3d 변수까지
host-level 에 포함해야 한다.

```yaml
all:
  children:
    testbed:
      hosts:
        {{ALIAS}}:
          ansible_host: "{{TARGET_HOST}}"
          ansible_user: "{{TARGET_USER}}"
          {% if AUTH_MODE == "password" %}
          ansible_password: "{{ lookup('env', 'TESTBED_PASSWORD') }}"
          ansible_become_password: "{{ lookup('env', 'TESTBED_BECOME_PASSWORD') | default(lookup('env', 'TESTBED_PASSWORD')) }}"
          {% else %}
          ansible_ssh_private_key_file: "{{SSH_KEY_PATH}}"
          ansible_become_password: "{{ lookup('env', 'TESTBED_BECOME_PASSWORD') }}"
          {% endif %}
          ansible_python_interpreter: /usr/bin/python3
          app_repo: "{{APP_REPO}}"
          app_version: "{{BRANCH}}"
          app_subdir: "{{APP_SUBDIR}}"
          app_namespace: "{{NAMESPACE}}"
          testbed_services: {{TESTBED_SERVICES}}
          db_kind: "{{DB_KIND}}"
          polestar10_collector_host: "{{POLESTAR10_COLLECTOR_HOST}}"
          polestar_organization_id: "{{POLESTAR_ORGANIZATION_ID}}"
          polestar10_kcm_collector_port: {{POLESTAR10_KCM_COLLECTOR_PORT}}
          polestar10_sms_broker_port: {{POLESTAR10_SMS_BROKER_PORT}}
          cluster_kind: "{{CLUSTER_KIND}}"
          cluster_name: "{{CLUSTER_NAME}}"
          kubeconfig_path: "{{KUBECONFIG_PATH}}"
          k3d_api_port: {{K3D_API_PORT}}
          k3d_node_http_port: {{K3D_NODE_HTTP_PORT}}
          k3d_node_https_port: {{K3D_NODE_HTTPS_PORT}}
          k3d_node_nodeport_offset: {{K3D_NODE_NODEPORT_OFFSET}}
          k3d_node_nodeport_max: {{K3D_NODE_NODEPORT_MAX}}
          scenario_runner_port: {{SCENARIO_RUNNER_PORT}}
      # ⚠️ testbed 식별 / Polestar10 broker 변수는 모두 host-level 에 있어야 함
      # (위 hosts: <ALIAS>: 영역). group vars 영역에 두면 group_vars/all.yml 의
      # default 가 이김 (회고 P0 #3 의 root cause). 본 vars: 영역에는 진짜 group-wide
      # ansible 동작 옵션만 (예: forks, gather_subset).
```

## 변수 매핑 표

| inventory 변수 | source | 변환 룰 |
|---|---|---|
| `ALIAS` | interview.target.host 의 마지막 octet 또는 `arm64-target` | 의미적 alias |
| `TARGET_HOST` | interview.target.host | 그대로 |
| `TARGET_USER` | interview.target.user | 그대로 |
| `AUTH_MODE` | interview.target.auth_mode | `password` / `ssh_key` |
| `SSH_KEY_PATH` | interview.target.ssh_key_path or bootstrap.ssh.ssh_key_path | 그대로 |
| `BRANCH` | interview.app.branch | default `main` |
| `APP_SUBDIR` | interview.app.app_subdir | 그대로 (예: `plopvape-shop`) |
| `NAMESPACE` | interview.app.namespace | 그대로 |
| `POLESTAR10_COLLECTOR_HOST` | bootstrap.polestar10.collector_host (있으면 그대로) → 없으면 base_url 의 hostname | URL parse → hostname only. ⚠️ base_url hostname 이 public IP (RFC1918 외 — 예: 221.x.x.x) 인데 사내 NAT/방화벽 환경이면 outbound 차단으로 모든 agent 패킷 silently fail. base_url 은 P10 web UI 도달용 public 그대로 두고 collector_host 만 사내 내부 IP (192.168.x.x 등 RFC1918) 로 분리 권장. 자동 추출 시 hostname 이 public 으로 보이면 사용자에게 "사내 내부 IP 가 따로 있나요?" prompt 권장 |
| `POLESTAR_ORGANIZATION_ID` | bootstrap.polestar10.organization_id | 24-hex. **빈값/누락 X** — Phase 1 인터뷰가 이미 받았어야 함. 빈값이면 SMS install role fail-fast |
| `POLESTAR10_KCM_COLLECTOR_PORT` | bootstrap.polestar10.kcm_collector_port (없으면 group_vars default `7575`) | KCM helm chart 의 `kcm.addr` (host:port) 의 port 부분. Polestar10 KCM backend 의 정석 port |
| `POLESTAR10_SMS_BROKER_PORT` | bootstrap.polestar10.sms_broker_port (없으면 group_vars default `1883`) | SMS AgentInstall.sh -m 의 broker port |
| `WPM_ENABLED` | true (default) | 사용자 인터뷰에서 disable 가능 |
| `APM_ENABLED` | true | 동일 |
| `KCM_ENABLED` | true (default) | ARM64 인터뷰에서 사용자가 "KCM 비활성" 명시 선택 시만 false |
| `SMS_ENABLED` | true | 동일 |
| `KCM_LOCAL_PATH` | bootstrap.paths.kcm_local_source | ARM64 + KCM enabled 인 경우만. controller 의 lucida-kcmagent 절대 경로 (인터뷰 / cwd 검색 / 자동 clone 결과). AMD64 면 빈값 OK. **role 의 fail-fast 는 본 변수만 검사 — `kcm_source_repo` 는 별 변수로 남아있으나 controller 자동 clone 시점에만 사용** |
| `KCM_SOURCE_BRANCH` | bootstrap.agents.kcm_source_branch | default `develop`. controller 에서 git checkout/pull 시 사용 |
| `CLUSTER_KIND` | bootstrap.cluster.kind | `k3d` (default — Docker 안 K3s) | `k3s` (legacy — native K3s) |
| `CLUSTER_NAME` | interview.app.app_subdir | testbed 이름 (예: `social-feed`). k3d cluster name + KCM helm release 의 clusterName. testbed 별로 unique |
| `KUBECONFIG_PATH` | derived from `/home/<user>/.kube/<cluster_name>.yaml` | cluster-manager role 이 export. 모든 K8s 관련 task 가 이 KUBECONFIG 사용 |
| `K3D_API_PORT` | interview / 6443 default | k3d API server host port. 다중 testbed 시 6444, 6445 등 |
| `K3D_NODE_HTTP_PORT` / `K3D_NODE_HTTPS_PORT` | 8080 / 8443 default | k3d ingress port. 다중 testbed 시 8081/8444 등 |
| `K3D_NODE_NODEPORT_OFFSET` / `K3D_NODE_NODEPORT_MAX` | 30000 / 30100 default | NodePort range. 다중 testbed 시 testbed 마다 다른 range (예: 30000-30100, 30200-30300) |
| `SCENARIO_RUNNER_PORT` | interview / 8091 default | rca-scenario-runner web port. 다중 testbed 시 8091, 8092, 8093 등 |

## 환경 변수 export (ansible-playbook 호출 직전)

비밀 값 (SSH password / become password) 만 env var 로 전달. organization_id / collector / broker port 등 비-비밀 변수는 inventory yaml 에 host-level 로 평문 박힘 (위 골격 참조).

```bash
# 비밀 — env var 로만
export TESTBED_HOST="${TARGET_HOST}"
export TESTBED_USER="${TARGET_USER}"
export TESTBED_PASSWORD="${interview.password}"          # AUTH_MODE=password 시
export TESTBED_BECOME_PASSWORD="${interview.become_password:-$TESTBED_PASSWORD}"
export TESTBED_SSH_KEY="${SSH_KEY_PATH}"                  # AUTH_MODE=ssh_key 시

# 비-비밀 — inventory host vars 에 박힌 형태 (위 골격) 가 우선. env fallback 은 group_vars/all.yml 에서.
# bootstrap.yaml 에서 읽어서 inventory 생성기가 직접 박음. 환경 변수 별도 export 불필요.
```

**주입 우선순위 정리** (회고 P0 #3 룰):
- `--extra-vars` (cli) > inventory **host vars** > playbook `vars:` > **inventory file group vars** > `group_vars/all.yml`
- 즉 `polestar_organization_id` / `polestar10_collector_host` 같이 인스턴스별로 다른 값은 **반드시 inventory host vars** 에 박을 것. group_vars 에 두면 default (`198.51.100.104` 등) 가 이김.

비밀 값은 inventory.yml 에 평문 X. env 만.

## DB / 추가 변수 (interview.app.db_kind)

testbed-services 의 `service-k8s` role 이 PostgreSQL/MySQL/MariaDB/CUBRID/Tibero 분기 가능하다면 group_vars 또는 host vars 에:

```yaml
vars:
  # ...
  db_kind: "{{DB_KIND}}"                  # postgresql / mysql / mariadb / cubrid / tibero
```

## NMS skip (interview.nms.enabled=false)

NMS 는 ansible role 이 없으니 inventory 변경 X. testbed-polestar10-register dispatch 시점에 nms.enabled 보고 skip.

## 검증

inventory.yml 작성 후 `ansible_deploy` 진입 전:

```bash
# 1. yaml 문법 검증
ansible-inventory -i "$INVENTORY" --list >/dev/null \
  || { echo "inventory yaml 문법 오류"; exit 1; }

# 2. 타겟 도달성 (이미 phase 1 에서 했지만 환경변수 적용 후 재확인)
ansible -i "$INVENTORY" testbed -m ping \
  || { echo "ping fail. SSH 자격증명 / 방화벽 점검."; exit 1; }
```

ping fail 시 manifest.phases.inventory_generated = "failed" + last_error 기록 + ask-polestar10 우회 (polestar10 아님 — SSH 인프라 영역).

## arm64 vs amd64 분기

interview.target.arch 따라 inventory 의 host vars 또는 group vars 에 `target_arch` 변수 설정. site.yml 의 pre_tasks 가 이미 자동 감지 (`ansible_architecture` 기반) 하므로 inventory 에 명시 X 도 OK.

## 동적 생성 vs 정적 sample 의 차이

infra/testbed/playbooks/inventory/{arm64,amd64}-sample.yml 은 **사람이 매뉴얼 실행할 때 편집**. testbed-build 는 인터뷰 → 동적으로 새 yaml 작성하여 runs/<RUN_ID>/inventory.yml 에 둠. site.yml 의 pre_tasks env vars 체크는 두 방식 모두 호환.

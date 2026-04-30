# Dynamic Inventory Generator

Phase 6 — interview.yaml + bootstrap.yaml → `runs/<RUN_ID>/inventory.yml`.

## 골격 — arm64-sample.yml 기반

[playbooks/inventory/arm64-sample.yml](../../../infra/testbed/playbooks/inventory/arm64-sample.yml) 형식 그대로 mimic.

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
      vars:
        # === testbed identity (interview.app 에서) ===
        app_repo: "https://github.com/BangSungjoon/testbed-services.git"
        app_version: "{{BRANCH}}"
        app_subdir: "{{APP_SUBDIR}}"
        app_namespace: "{{NAMESPACE}}"

        # === polestar10 collector (bootstrap.polestar10.base_url 또는 별도 endpoint) ===
        polestar10_collector_host: "{{POLESTAR10_COLLECTOR_HOST}}"
        polestar_organization_id: "{{ lookup('env', 'POLESTAR_ORG_ID') }}"

        # === agent enable flags ===
        wpm_enabled: "{{WPM_ENABLED}}"
        apm_enabled: "{{APM_ENABLED}}"
        kcm_enabled: "{{KCM_ENABLED}}"
        sms_enabled: "{{SMS_ENABLED}}"
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
| `POLESTAR10_COLLECTOR_HOST` | bootstrap.polestar10.base_url 의 hostname | URL parse → hostname only |
| `WPM_ENABLED` | true (default) | 사용자 인터뷰에서 disable 가능 |
| `APM_ENABLED` | true | 동일 |
| `KCM_ENABLED` | true | 동일 |
| `SMS_ENABLED` | true | 동일 |

## 환경 변수 export (ansible-playbook 호출 직전)

inventory 의 `lookup('env', ...)` 가 작동하려면:

```bash
export TESTBED_HOST="${TARGET_HOST}"
export TESTBED_USER="${TARGET_USER}"
export TESTBED_PASSWORD="${interview.password}"          # AUTH_MODE=password 시
export TESTBED_BECOME_PASSWORD="${interview.become_password:-$TESTBED_PASSWORD}"
export TESTBED_SSH_KEY="${SSH_KEY_PATH}"                  # AUTH_MODE=ssh_key 시
export POLESTAR_ORG_ID="${interview.polestar.org_id}"     # 또는 bootstrap 캐시
```

비밀 값은 environment 만 통해서. inventory.yml 에 평문 X.

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

inventory.yml 작성 후 phase 7 진입 전:

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

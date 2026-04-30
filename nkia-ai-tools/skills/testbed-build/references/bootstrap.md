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

## 인터뷰 (없으면 수행)

```
=== testbed-build 첫 사용 환영합니다. 자격증명 + 레포 경로를 한 번 설정합니다. ===

1. SSH 기본 user [nkia]: _
2. SSH key 사용? [Y/n] (n 이면 password 매번 입력): _
   yes → SSH key 경로 [~/.ssh/id_rsa]: _

3. Polestar10 instance:
   1) NKIA dev (https://...)
   2) 96 demo (https://192.168.230.96)
   3) 직접 입력
   선택 [1]: _

4. testbed-services 레포 경로 [~/dev/testbed-services]: _
   (없으면 자동 git clone — 진행할까요? [Y/n]): _

5. rca-scenario-runner 레포 경로 [~/dev/rca-scenario-runner]: _
   (없으면 자동 git clone — 진행할까요? [Y/n]): _

→ ~/.testbed-build/bootstrap.yaml 생성 + chmod 600. 다음 호출부터 묻지 않습니다.
```

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

# KCM ARM64 Setup — controller fetch + scp 패턴

**조건부 적용**: 타겟 서버 arch == arm64 + KCM 사용 시에만 read. AMD64 면 본 파일 skip.

## 배경

타겟 서버 SSH 가 통한 직후 `uname -m` 으로 아키텍처를 자동 감지합니다. ARM64 호스트인 경우 KCM 에이전트는 사내 GitLab (cims2.nkia.net) 의 lucida-kcmagent 소스를 빌드합니다. 타겟 서버에는 GitLab 자격증명이 없는 게 일반적이므로 **controller (사용자 머신) 에서 소스 확보 후 scp 로 타겟에 전달** 하는 흐름.

## Step 1: controller 의 cwd 에서 lucida-kcmagent 자동 검색

```bash
KCM_CWD_PATH="${PWD}/lucida-kcmagent"
[ -d "$KCM_CWD_PATH/.git" ] && KCM_LOCAL_PATH="$KCM_CWD_PATH"
```

cwd 아래에 이미 git 레포 있으면 그걸 사용. 다음 단계 skip.

## Step 2: cwd 부재 시 사용자 path 입력 + fallback clone

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

## Step 3: 결정된 경로로 develop branch 최신화 + scp

옵션별 처리:

- **자동 clone 선택**: `git clone https://cims2.nkia.net:8443/gitlab/lucida-kcmagent.git ${PWD}/lucida-kcmagent --branch develop` 실행. 자격증명 prompt 가 뜨면 사용자가 controller 의 일반 git 워크플로 (LDAP web 로그인 후 token / PAT / SSH key) 로 통과.
- **경로 직접 입력**: 자유 입력 prompt 으로 절대 경로 받음. 그 path 의 .git 확인. 없으면 다시 prompt 또는 자동 clone 옵션 제시.
- **KCM 비활성**: bootstrap.yaml 의 `agents.kcm_disabled = true` 저장. 사용자 명시 결정.

결정된 path 는 bootstrap.yaml 의 `paths.kcm_local_source` 에 저장. dynamic-inventory-generator 가 ansible-playbook 호출 시 `-e kcm_local_path=<path>` 로 전달. agent-kcm role 이 develop fetch + pull → ansible.posix.synchronize 로 타겟 staging 에 rsync → sudo cp 로 /opt/lucida-kcmagent 이동 → build → ctr import.

> 자동 disable 금지 룰 ([ansible-failure-diagnosis.md](ansible-failure-diagnosis.md)) — controller clone 실패 (사내망 X / 자격증명 X) 시 LLM 이 자동으로 `kcm_disabled=true` 처리 X. 사용자가 명시적으로 위 "KCM 비활성" 옵션을 선택해야만 disable.

> 🚫 **출력 가이드**: prompt 안에 "예시 답변 형식" / "다음과 같이 입력" 식으로 sample value (특히 자격증명) 절대 박지 말 것. LLM 이 메모리에서 본 자격증명을 sample 로 가져오면 화면 노출 사고 (PR #30 참조).

# 외부 레포 자동 발견 + clone 절차

**조건부 적용**: bootstrap.yaml 의 `paths.testbed_services_repo` / `paths.scenario_runner_repo` 가 비어있거나 그 경로의 `.git` 이 부재할 때만 read. 이미 path 가 박혀있고 디렉토리 정상이면 skip.

## 외부 레포 역할 안내

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

## Step 1: cwd (Claude Code 작업 폴더) 우선 검사

```bash
# $PWD = Claude Code 가 켜져있는 작업 폴더
for repo in testbed-services rca-scenario-runner; do
  for candidate in "./$repo" "../$repo"; do
    [ -d "${candidate}/.git" ] && echo "FOUND_CWD $repo: $(realpath $candidate)" && break
  done
done
```

## Step 2: 부재 시 — 외부 영역 fallback

홈 디렉토리 일반적 위치 순회 (depth 1):
```bash
for repo in testbed-services rca-scenario-runner; do
  for path in ~/dev/$repo ~/projects/$repo ~/workspace/$repo ~/$repo; do
    [ -d "$path/.git" ] && echo "FOUND_HOME $repo: $path" && break
  done
done
```

## Step 3: 결과 따라 분기

### Case A: 둘 다 발견 (cwd 또는 home)

**인터뷰 없이 자동 진행** — 발견된 경로 사용 + 알림만:
```
[레포 자동 발견 결과 — 예시 출력 형식]
  ✓ testbed-services       → <발견된 절대 경로> (cwd 또는 home)
  ✓ rca-scenario-runner   → <발견된 절대 경로> (cwd 또는 home)

위 경로 그대로 사용합니다.
```

(실제 경로는 사용자 환경마다 다름. cwd 의 위치 / 사용자가 평소 사용하는 dev 패턴에 따라 결정.)

### Case B: 둘 중 하나만 발견

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

### Case C: 둘 다 부재

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

## Step 4: 결정된 경로로 진행

- 발견 케이스: 그대로 사용
- clone 케이스: `git clone https://github.com/nkia-ai-team/<repo>.git <chosen_path>` 실행
- bootstrap.yaml 의 `paths.testbed_services_repo` / `paths.scenario_runner_repo` 에 영구 저장 → **다음 호출부터 발견/clone 단계 자체 skip** (paths 가 가리키는 디렉토리에 .git 있는지만 확인)

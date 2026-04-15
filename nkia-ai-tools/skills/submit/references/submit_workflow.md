# Submit Workflow — PR 생성 및 리뷰 루프 상세

## 1. PR/MR 제목 규칙

### 일반 레포

    {linear-issue} {이슈 제목}

예: `nkiaai-305 Chat AI: streaming 구조 리팩토링 (WriterEmitterAdapter 전환)`

Linear 이슈 번호는 브랜치명에서 추출합니다.

### UI 레포 (lucida-ui)

    #{PIMS} {Type} : {설명} {linear-issue}

예: `#117864 Feat : reasoning/answer 스트리밍 구현 nkiaai-306`

PIMS 번호와 Linear 이슈 번호는 Phase 1 Step 2에서 `/commit --format ui` 워크플로우가 사용자에게 확인합니다.
커밋 메시지와 MR 제목에 동일한 값을 사용하므로 한 번만 물어봅니다.

---

## 2. 타겟 브랜치 판별

### 우선순위

1. `/submit` 뒤에 브랜치명이 지정되면 → 해당 브랜치 (override)
2. 미지정 시 **git 히스토리로 자동 감지** (레포 이름 테이블은 사용하지 않음)
3. 자동 감지가 실패하면 `origin/develop` 또는 `main` fallback

### 2.1 자동 감지 알고리즘

HEAD가 실제로 어느 브랜치에서 뽑혔는지 찾습니다. 핵심 원리: **원격 후보 브랜치 중 `<cand>..HEAD`(HEAD에 있으나 후보에 없는 커밋 수)가 가장 작은 후보가 실제 base**입니다.

#### 왜 이 방법이 맞는가

kickoff가 `develop-10.2.4_3`에서 feature 브랜치를 뽑았다고 가정:

| 후보 | `<cand>..HEAD` | 의미 |
|------|----------------|------|
| `origin/develop-10.2.4_3` | N (feature 커밋 수) | **최솟값 — 실제 base** |
| `origin/develop-10.2.4_2` | N + (2→3 델타) | 이전 버전 브랜치 |
| `origin/develop` | N + (develop→10.2.4_3 누적) | 상위 base |
| `origin/main` | 훨씬 더 큼 | 최상위 |

레포 이름이 `lucida-ui`든 `lucida-chat-ai`든 상관 없이, HEAD의 **실제 조상**을 찾아내므로 하드코딩 테이블 없이도 정확합니다.

### 2.2 자동 감지 스크립트

    git fetch origin --quiet

    # 후보 base: 버전 브랜치 (-chat 변형 포함) + 전통 fallback
    candidates=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin/ \
      | grep -E '^origin/(develop-10\.[0-9]+\.[0-9]+_[0-9]+(-chat)?|develop|main|master)$')

    if [ -z "$candidates" ]; then
      echo "WARN: 후보 base 브랜치를 찾지 못했습니다. fallback으로 origin/develop 또는 main 사용." >&2
      TARGET_BRANCH=$(git ls-remote --heads origin develop main 2>/dev/null \
        | awk '{print $2}' | sed 's|refs/heads/||' | head -1)
    else
      # HEAD의 고유 커밋 수가 가장 적은 후보 = 실제 base
      best_base=""
      best_ahead=999999999
      for cand in $candidates; do
        ahead=$(git rev-list --count "$cand..HEAD" 2>/dev/null) || continue
        if [ "$ahead" -lt "$best_ahead" ]; then
          best_ahead=$ahead
          best_base=$cand
        fi
      done
      TARGET_BRANCH="${best_base#origin/}"
    fi

    echo "Auto-detected target: $TARGET_BRANCH (ahead: $best_ahead)"

### 2.3 엣지 케이스

| 케이스 | 동작 |
|--------|------|
| HEAD가 base와 동일 (fast-forward 가능) | `ahead=0`이 최솟값 → base를 정확히 반환. 단 이 경우 submit할 커밋이 없으므로 Step 1에서 이미 종료됨 |
| 여러 후보에서 ahead 동률 | 먼저 순회된 후보 선택 (`for-each-ref`는 사전식 정렬이므로 결정적) |
| `rev-list` 실패 (후보가 shallow clone에 없음) | 해당 후보 스킵 (`\|\| continue`) |
| 모든 후보가 실패 | `best_base`가 비어있어 `TARGET_BRANCH`가 빈 문자열 → 사용자에게 에러 안내 |
| kickoff가 `develop-10.x.y_z-chat-{function}` 하위 feature로 뽑은 경우 | `-chat` 접미사 브랜치가 후보에 포함되어 가장 가까운 ancestor로 선택됨 |
| 사용자가 `develop`에서 직접 뽑은 경우 | 버전 브랜치들은 `ahead`가 더 크므로 자연스럽게 `develop`이 선택됨 |

### 2.4 레포 이름 확인 (참고용, 자동 감지에는 불필요)

플랫폼 감지나 MR 제목 생성에만 사용:

    # git remote에서 레포 이름 추출
    git remote get-url origin
    # → https://github.com/org/lucida-chat-ai.git → lucida-chat-ai
    # → https://cims2.nkia.net:8443/gitlab/lucida-ui.git → lucida-ui

> **주의:** 레포 이름을 타겟 브랜치 판별에 사용하지 **않습니다**. 같은 레포에서도 kickoff가 매 사이클 다른 버전 브랜치에서 feature를 뽑으므로, 레포 이름 테이블은 구조적으로 잘못된 정보원입니다.

---

## 3. 플랫폼 감지

remote URL에서 플랫폼을 감지합니다.

| 패턴 | 플랫폼 |
|------|--------|
| `github.com` 포함 | GitHub |
| `gitlab` 포함 또는 self-hosted | GitLab |

---

## 4. PR/MR 생성 명령어

### GitHub

    gh pr create \
      --title "{pr-title}" \
      --body "$(cat <<'EOF'
    ## Summary
    - 변경 사항 요약

    ## Changes
    - 변경 단위별 불릿
    EOF
    )" \
      --base {target-branch} \
      --head {current-branch} \
      --assignee @me

### GitLab (self-hosted)

    # project ID 조회
    GITLAB_HOST={hostname} glab api "/projects/{group}%2F{project}"
    # → project_id 추출

    # 현재 사용자 ID 조회 (assignee용)
    GITLAB_HOST={hostname} glab api "/user"
    # → user_id 추출 (id 필드)

    # MR 생성 (assignee를 본인으로 설정)
    GITLAB_HOST={hostname} glab api --method POST \
      "/projects/{project_id}/merge_requests" \
      -f "source_branch={current-branch}" \
      -f "target_branch={target-branch}" \
      -f "title={mr-title}" \
      -f "description={mr-body}" \
      -f "assignee_id={user_id}"

GitLab self-hosted 인증은 [platform_operations.md Section 6](../../code-review/references/platform_operations.md) 참조

---

## 5. PR Body 생성 규칙

Summary와 Changes 섹션만 작성합니다. Test plan 섹션은 불필요.

### Summary

이슈 제목과 AC를 기반으로 1~3줄 요약:

    ## Summary
    - StreamEventEmitter를 WriterEmitterAdapter로 전환하여 스트리밍 구조 단순화

### Changes

`git log {target}..HEAD --oneline`과 `git diff {target}..HEAD --stat`을 기반으로 작성:

    ## Changes
    - StreamEventEmitter(Thread-safe Queue + 50ms 폴링) 완전 제거
    - WriterEmitterAdapter(get_stream_writer()) 신규 — emitter 인터페이스 래핑
    - 단위 테스트 5건 추가

---

## 6. 리뷰 루프 상세

### 리뷰 결과 파싱

code-review 스킬이 PR/MR에 게시한 코멘트에서 판정을 파싱합니다:

| 코멘트 내용 | 판정 |
|------------|------|
| `전체 판정: 승인` | 승인 |
| `전체 판정: 수정 후 승인 권장` | 수정 필요 |
| `전체 판정: 수정 필요` | 수정 필요 |

### 자동 수정 프로세스

1. 리뷰 코멘트에서 지적사항 목록 추출
2. 각 지적사항의 파일, 라인, 내용 파싱
3. 수정 가능 여부 판단 (SKILL.md의 자동 수정 범위 참조)
4. 수정 가능한 항목 자동 수정
5. 수정 불가 항목은 사용자에게 보고

### 자동 수정 불가 시 출력

    === 자동 수정 불가 항목 ===

    다음 항목은 직접 수정이 필요합니다:

    1. [Critical] src/api/auth.ts:42
       SQL injection 가능성 — 쿼리 파라미터 직접 삽입
       → 아키텍처 수준 변경 필요

    수정 후 /submit을 다시 실행하면 됩니다.

    ===========================

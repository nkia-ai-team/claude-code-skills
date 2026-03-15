---
name: submit
description: Submit completed work — commit, push, create PR/MR, run code review loop with auto-fix, and wait for user merge. Use this skill after development is complete and ready for review.
---

# Submit — 제출 (커밋 → PR → 리뷰 루프)

## CRITICAL: Merge 금지

**이 스킬은 절대로 PR/MR을 merge하지 않습니다.**
- `gh pr merge`, `glab mr merge` 등 merge 명령어 실행 금지
- merge는 반드시 사용자가 직접 수행

---

## Overview

개발 완료 후 커밋부터 코드 리뷰 통과까지의 과정을 자동화하는 오케스트레이터 스킬입니다.

**하는 일:**
- `/commit` 스킬 워크플로우로 커밋
- 원격에 푸시
- PR/MR 생성 (레포 유형에 맞는 제목, 타겟 브랜치)
- `/code-review` 스킬 워크플로우로 코드 리뷰
- 지적사항 자동 수정 → 재커밋 → 재리뷰 (최대 3회)

**하지 않는 일:**
- PR/MR merge (사용자가 직접)
- PR/MR approve

---

## Usage

    /submit                    # 기본: 타겟 브랜치 자동 판별
    /submit develop-ui-chat    # 타겟 브랜치 직접 지정

---

## Workflow

### Phase 1: 커밋 + 푸시

#### Step 1: Check Changes

    git status
    git diff --cached --stat
    git log origin/{current-branch}..HEAD --oneline 2>/dev/null

- staged 변경사항이 있으면 → Step 2 (커밋)
- unstaged 변경사항만 있으면 → 사용자에게 staging 안내
- 변경사항 없고 미푸시 커밋 있으면 → Step 3 (푸시만)
- 변경사항도 없고 미푸시 커밋도 없으면 → Phase 2 (기존 PR 확인)

#### Step 2: Commit (레포 유형에 따라 분기)

**A) 일반 레포** — `/commit` 스킬 워크플로우를 그대로 실행합니다:

1. 브랜치명에서 Linear 이슈 번호 추출
2. `git diff --cached`로 변경사항 분석
3. Type 키워드 결정
4. 커밋 메시지 생성 → 미리보기 → 사용자 확인 → 커밋

커밋 메시지 형식: `{linear-issue} {Type} : {설명}`

커밋 메시지 형식, Type 결정 규칙은 [commit SKILL.md](../commit/SKILL.md) 참조

**B) UI 레포 (lucida-ui)** — 커밋 메시지 형식이 다르므로 직접 생성합니다:

1. 사용자에게 PIMS 번호와 Linear 이슈 번호 확인
2. `git diff --cached`로 변경사항 분석
3. Type 키워드 결정
4. UI 레포 형식으로 메시지 생성 → 미리보기 → 사용자 확인 → 커밋

커밋 메시지 형식: `#{PIMS} {Type} : {설명} {linear-issue}`

예: `#117864 Feat : reasoning/answer 스트리밍 구현 nkiaai-306`

UI 레포 브랜치(`develop-ui-chat-*`)에는 Linear 이슈 번호가 없으므로, 최초 커밋 시 사용자에게 한 번 확인하고 이후 같은 세션에서는 재사용합니다.

#### Step 3: Push

    git push -u origin {current-branch}

- 푸시 성공 → Phase 2로
- 푸시 실패 (rejected — remote에 새 커밋) → `git pull --rebase` 후 재푸시
- 그 외 실패 → 에러 메시지 출력, 사용자에게 안내

---

### Phase 2: PR/MR 생성

#### Step 4: Check Existing PR

기존 PR/MR이 있는지 확인합니다.

**GitHub:**

    gh pr list --head {branch} --state open --json url

**GitLab:**

    GITLAB_HOST={hostname} glab api "/projects/{id}/merge_requests?source_branch={branch}&state=opened"

- 기존 PR 있으면 → URL 사용, 생성 스킵
- 없으면 → Step 5에서 생성

#### Step 5: Create PR/MR

PR/MR 제목, 타겟 브랜치 규칙은 [submit_workflow.md](references/submit_workflow.md) 참조

**PR Body 형식:**

    ## Summary
    - 변경 사항 요약 (1~3줄)

    ## Changes
    - 변경 단위별 불릿 리스트

---

### Phase 3: 코드 리뷰 루프 (최대 3회)

#### Step 6: Code Review (code-review 스킬 워크플로우)

`/code-review` 스킬의 워크플로우를 PR/MR URL로 실행합니다.

리뷰 체크리스트, 결과 템플릿은 [code-review SKILL.md](../code-review/SKILL.md) 참조

#### Step 7: Judge Review Result

리뷰 결과에 따라 분기합니다:

| 리뷰 결과 | 행동 |
|-----------|------|
| 승인 (Critical 0, Warning 0) | 루프 종료 → Phase 4 |
| 수정 후 승인 권장 (Warning/Info) | 자동 수정 시도 → 재리뷰 |
| 수정 필요 (Critical 있음) | 자동 수정 시도 → 재리뷰 |
| 승인 (Info만 남음) | 개선 가능하면 수정 → 재리뷰, 아니면 루프 종료 |
| 3회 초과 | 루프 중단, 사용자에게 인계 |

#### Step 8: Auto-Fix & Re-review

지적사항을 자동 수정합니다.

**자동 수정 범위:**

| 수정 가능 | 수정 불가 (사용자 개입 필요) |
|-----------|--------------------------|
| 코드 스타일/포맷 | 아키텍처 전면 재설계 |
| 네이밍 개선 | 비즈니스 요구사항 변경 |
| 매직넘버 상수화 | 외부 API 스펙 변경 |
| 불필요 import/코드 제거 | DB 스키마 변경 |
| 에러 핸들링 보강 | |
| 보안 취약점 수정 (Injection, XSS 등) | |
| 성능 개선 (N+1, 불필요 연산 제거) | |
| 테스트 추가/보강 | |
| 리팩토링 (메서드 추출, 중복 제거) | |
| 로깅/주석 개선 | |

수정 후:
1. `/commit` 워크플로우로 수정 내용 커밋
2. `git push`
3. Step 6으로 돌아가 재리뷰

**3회 초과 시:**

    === 코드 리뷰 자동 수정 한도 초과 ===

    3회 자동 수정을 시도했지만 아직 지적사항이 남아있습니다.

    남은 지적사항:
    - [Critical] src/api/auth.ts:42 — SQL injection 가능성
    - [Warning] src/utils/parser.ts:15 — 무한 루프 가능성

    직접 확인하고 수정해주세요.
    수정 후 /submit을 다시 실행하면 됩니다.

    ===========================

---

### Phase 4: 머지 대기

#### Step 9: Notify User

    === 코드 리뷰 통과 ===

    PR: https://github.com/org/repo/pull/42
    리뷰 결과: 승인

    PR을 확인하고 머지해주세요.
    머지 후 /wrap-up NKIAAI-305 로 마무리하실 수 있습니다.

    ===========================

---

## Resources

- [submit_workflow.md](references/submit_workflow.md) — PR 제목 규칙 (일반/UI), 타겟 브랜치 판별, 플랫폼별 PR 생성 명령어
- [commit SKILL.md](../commit/SKILL.md) — 커밋 메시지 형식, Type 결정 규칙
- [code-review SKILL.md](../code-review/SKILL.md) — 코드 리뷰 체크리스트, 결과 템플릿

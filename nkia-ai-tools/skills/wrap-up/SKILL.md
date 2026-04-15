---
name: wrap-up
description: Post-merge cleanup — switch to target branch, pull latest, prune remotes, delete merged branches, collect and register evidence, self-check evidence quality, handle manual uploads with auto-mapping, validate AC items, and transition issue to In Review. Use this skill after merging a PR/MR.
---

# Wrap-up — 마무리

## CRITICAL: First Step — Read the References

**증빙 수집 및 검증 시 반드시 참조:**
- [guideline-ref.md](../_shared/guideline-ref.md) — 이슈 상태, AC 항목 형식, AI-Verification Loop
- [wrapup_workflow.md](references/wrapup_workflow.md) — 브랜치 정리, 증빙 자가 점검, 검증 루프

## CRITICAL: 하위 스킬 반드시 사용

**오케스트레이터 스킬은 하위 스킬의 워크플로우를 직접 대체하지 않습니다.**
- 증빙 수집 시 반드시 `/linear-issue-evidence` 스킬 워크플로우를 실행할 것 (직접 증빙 수집·등록 금지)
- AC 검증 시 반드시 `/linear-issue-validator` 스킬 워크플로우를 실행할 것 (직접 검증 금지)

---

## Overview

PR/MR 머지 후 브랜치 정리부터 증빙 등록, AC 검증, 이슈 상태 전환까지의 마무리 과정을 자동화하는 오케스트레이터 스킬입니다.

**하는 일:**
- 머지 대상 브랜치로 전환 + 최신화 + prune + 로컬 브랜치 삭제
- `/linear-issue-evidence` 스킬 워크플로우로 증빙 수집·등록
- 증빙 자가 점검 → 미흡한 부분 자동 보강
- 수동 업로드 안내 + 업로드된 미디어 AC 자동 매핑
- `/linear-issue-validator` 스킬 워크플로우로 AC 검증
- 검증 실패 시 자동 보강 → 재검증 (최대 3회)
- 검증 통과 시 In Review 전환

**하지 않는 일:**
- 코드 수정 (코드 지적사항은 사용자에게 안내)

---

## Usage

    /wrap-up <issue-id>
    /wrap-up NKIAAI-305

---

## Workflow

### Phase 1: 브랜치 정리

#### Step 1: Switch & Update

**타겟 브랜치 판별** (git 히스토리로 자동 감지):

wrap-up 시점에는 HEAD가 방금 머지된 feature 브랜치이므로, HEAD가 **실제로 어느 base에서 분기됐는지**를 원격 후보 브랜치와의 커밋 거리로 찾습니다. 레포 이름 테이블에 의존하지 않으므로, kickoff가 매 사이클 새로 뽑는 `develop-10.x.y_z` / `develop-10.x.y_z-chat` 버전 브랜치에 자동 대응합니다.

    git fetch origin --quiet

    # 후보 base: 버전 브랜치 + 전통 fallback
    candidates=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin/ \
      | grep -E '^origin/(develop-10\.[0-9]+\.[0-9]+_[0-9]+(-chat)?|develop|main|master)$')

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

    git checkout "$TARGET_BRANCH"
    git pull origin "$TARGET_BRANCH"
    git remote prune origin

> 레포 이름 테이블(`lucida-ui→develop-ui-chat`, `lucida-chat-ai→develop-sandbox` 등)은 사용하지 않습니다. 같은 레포에서도 사이클마다 base가 바뀌므로 레포 이름만으로는 판별 불가능합니다. submit 스킬과 동일한 로직.

상세(fallback, 엣지 케이스)는 [wrapup_workflow.md Section 1](references/wrapup_workflow.md) 참조

#### Step 2: Delete Merged Local Branches

머지된 로컬 브랜치를 삭제합니다. 사용자 확인 없이 바로 삭제합니다.

    git branch --merged | grep -v '^\*' \
      | grep -v -x -E '  (main|master|develop|develop-ui|develop-ui-chat|develop-sandbox|release.*|develop-10\.[0-9]+\.[0-9]+_[0-9]+(-chat)?)' \
      | xargs -r git branch -d

- 현재 브랜치(`*`)는 제외
- 보호 브랜치는 정확한 이름 매칭으로 제외 (부분 매칭 아님)
- **버전 base 브랜치 보호**: `develop-10.x.y_z` / `develop-10.x.y_z-chat` 패턴을 명시적으로 제외하여 현재 사이클 base가 실수로 삭제되지 않도록 함
- UI feature 브랜치(`develop-10.2.4_3-chat-auditTrail` 등)는 `$`로 끝나지 않으므로 정상 삭제

---

### Phase 2: 증빙 수집 + 등록

**⚠️ CRITICAL: 현재 레포 범위만 증빙 수집**

하나의 이슈에 여러 레포(AI, AP, UI)의 변경사항이 포함될 수 있습니다.
**현재 작업 디렉토리의 레포에 해당하는 AC 항목만 증빙을 수집·업데이트합니다.**

범위 판별은 [wrapup_workflow.md Section 2](references/wrapup_workflow.md) 참조

#### Step 3: Collect Evidence (evidence 스킬 워크플로우)

`/linear-issue-evidence` 스킬의 워크플로우를 실행합니다. **현재 레포 범위의 AC만 대상.**

1. 이슈 AC 파싱
2. 현재 레포에 해당하는 AC 항목 필터링
3. 필터링된 항목만 완료 판단 + 증빙 수집
4. AC 체크박스 업데이트 + 증빙 텍스트 삽입

증빙 유형 식별, 수집 방법은 [evidence SKILL.md](../linear-issue-evidence/SKILL.md) 참조

#### Step 4: Self-Check Evidence

등록된 증빙을 다시 읽어서 미흡한 부분을 자동 보강합니다.

자가 점검 기준, 보강 방법은 [wrapup_workflow.md Section 3](references/wrapup_workflow.md) 참조

보강 가능한 항목은 자동으로 재수집하여 description을 업데이트합니다.

#### Step 5: Manual Upload Guide + Media Mapping

스크린샷/동영상 등 자동 수집 불가 항목이 있으면 사용자에게 안내합니다.

    === 수동 업로드 필요 ===

    다음 항목은 Linear 이슈에 직접 업로드해주세요:

    1. AC #3 "동작 확인 스크린샷" — 스크린샷 필요
       → 프롬프트 입력 → 감사 이력 기록 확인 화면

    업로드 완료 후 알려주세요.

    ===========================

**사용자가 업로드 완료를 알리면:**
1. `mcp__plugin_linear_linear__get_issue`로 이슈 재조회
2. `mcp__plugin_linear_linear__extract_images`로 업로드된 미디어 확인
3. 이미지 내용을 실제 열람하여 적절한 AC 항목에 자동 매핑
4. `mcp__plugin_linear_linear__save_issue`로 description 증빙 텍스트 업데이트

---

### Phase 3: 검증 루프 (최대 3회)

#### Step 6: Validate (validator 스킬 워크플로우)

`/linear-issue-validator` 스킬의 워크플로우를 실행합니다.

1. AC 항목 파싱
2. MR 스코프 커버리지 확인
3. 코드 리뷰 존재 확인 (Gate)
4. MR Diff 분석
5. 증빙 유형 분류 → 유형별 검증
6. 검증 결과 코멘트 게시
7. 체크박스 업데이트

검증 방법, 템플릿은 [validator SKILL.md](../linear-issue-validator/SKILL.md) 참조

#### Step 7: Judge Validation Result

| 결과 | 행동 |
|------|------|
| PASS | Step 8로 → In Review 전환 |
| PARTIAL/FAIL (증빙/문서 지적) | 자동 보강 → Step 6 재검증 |
| PARTIAL/FAIL (코드 지적) | 사용자에게 안내 → 스킬 종료 |
| 3회 초과 | 사용자에게 인계 |

검증 실패 분기 상세는 [wrapup_workflow.md Section 4](references/wrapup_workflow.md) 참조

**코드 지적사항 시 안내:**

    === 코드 수정 필요 ===

    검증에서 코드 관련 지적사항이 발견되었습니다:

    - AC #1: MR diff에서 StreamEventEmitter 참조가 남아있음

    새 브랜치를 생성하여 수정 후 /submit으로 다시 제출해주세요.
    수정 완료 후 /wrap-up을 다시 실행하면 됩니다.

    ===========================

#### Step 8: Transition to In Review

모든 AC 통과 시 `AskUserQuestion`으로 확인 후 In Review로 전환합니다.

    이슈를 'In Review' 상태로 이동하시겠습니까?

사용자 승인 시 `mcp__plugin_linear_linear__save_issue`로 상태 전환.

    === 마무리 완료 ===

    이슈: NKIAAI-305
    상태: In Progress → In Review
    AC: 3/3 통과
    증빙: 모두 첨부 완료

    ===========================

---

## Resources

- [wrapup_workflow.md](references/wrapup_workflow.md) — 타겟 브랜치 판별, 증빙 자가 점검 기준, 검증 실패 분기 상세
- [guideline-ref.md](../_shared/guideline-ref.md) — 이슈 상태, AC 항목 형식, AI-Verification Loop
- [evidence SKILL.md](../linear-issue-evidence/SKILL.md) — 증빙 유형 식별, 수집 방법
- [validator SKILL.md](../linear-issue-validator/SKILL.md) — 검증 방법, 결과 템플릿

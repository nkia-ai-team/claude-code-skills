---
name: linear-issue-validator
description: Validate and verify completed Linear issues by checking DoD (Definition of Done) and AC (Acceptance Criteria) items. Supports various evidence types including URLs, documents, images, PR links, API endpoints, and CI/CD logs. Posts validation results as comments and optionally moves issues to "In Review" status when all items pass.
---

# Linear Issue Validator

## CRITICAL: First Step — Read the References

**BEFORE generating any validation report, you MUST read:**
- [guideline-ref.md](../_shared/guideline-ref.md) — 이슈 상태 규칙, AI-Verification Loop, Estimate 규칙
- [validation_templates.md](references/validation_templates.md) — 검증 결과 코멘트 템플릿, 실패 유형별 메시지, Evidence Type 분류 규칙

**All validation comments MUST follow the exact templates from the references file.**

---

## Overview

완료된 Linear 이슈의 AC 항목을 검증하고 평가하는 스킬입니다. 작업자가 첨부한 결과물(링크, 이미지, 텍스트 등)을 실제로 확인하여 검증합니다.

이 스킬은 AI-Verification Loop의 **Step 3 (AC 검증)**에 해당합니다.

**주요 기능:**
1. AC 항목별 결과물 파싱 및 검증
2. 다양한 결과물 유형 지원 (URL, 이미지, PR, API, CI/CD 등)
3. 검증 결과를 이슈 코멘트로 작성
4. 전체 통과 시 "In Review" 상태로 이동 (선택)

---

## Status Rules

상태 규칙은 [guideline-ref.md "이슈 상태"](../_shared/guideline-ref.md) 참조.
검증 통과 시 상태 이동은 Step 12에서 처리합니다.

---

## Core Validation Principles

### Principle 1: 검증 실패를 만나도 끝까지 진행

**인증 실패, MCP 미연결, API 조회 불가 등으로 특정 항목을 검증하지 못하더라도 절대 멈추지 마세요!**
- 실패 항목을 `blocked_items`에 기록하고, **나머지 항목 검증을 끝까지 진행**
- 모든 항목 검증 완료 후, 마지막에 blocked_items를 한번에 사용자에게 보고

### Principle 2: 접속 확인 ≠ 검증 완료

**URL/문서 링크 검증 시 단순 "접속 가능 여부"만 확인하면 안 됩니다!**
- 결과물의 **내용이 AC 요건과 일치하는지** 확인해야 합니다
- 페이지 제목/주제가 요건과 관련 있는지, 핵심 키워드가 포함되어 있는지 확인

### Principle 3: 이미지/동영상은 실제 첨부 및 내용 확인 필수

**이미지나 동영상 증빙은 단순 URL 텍스트만으로 통과시키면 안 됩니다!**
- Linear 업로드 이미지(`uploads.linear.app/*`)는 **`mcp__plugin_linear_linear__extract_images` MCP 도구로 확인** (URL 서명 만료 방지)
- 외부 이미지는 Read tool의 vision 기능으로 **실제 이미지를 열어서 내용 확인** 필수
- URL만 텍스트로 적혀있고 실제 첨부가 아닌 경우 → `media_not_viewable`

### Principle 4: 문서 업데이트 AC는 내용 대조 필수

**AC가 문서 "업데이트/갱신"을 요구할 때, 문서 존재 여부나 수정일만 확인하면 안 됩니다!**
- 이슈의 변경 사항(MR diff, 다른 AC 항목)이 **문서 본문에 실제로 반영되었는지 대조 검증** 필수
- 상세 프로세스는 [evidence_validation_methods.md Section 5.2](references/evidence_validation_methods.md) 참조

---

## Usage

```
/linear-issue-validator <issue-id-or-url>
```

**Options:**

| 옵션 | 설명 |
|-----|------|
| `--strict` | 모든 항목 통과 필수 (부분 통과 불허) |
| `--skip-move` | 상태 변경 스킵 (검증만 수행) |
| `--ac-only` | AC 항목만 검증 |

---

## Workflow

### Step 1: Parse Issue Input

이슈 ID 또는 URL을 파싱합니다. (`NKIA-123`, Full URL, UUID 지원)

### Step 2: Fetch Issue Details

`mcp__linear__get_issue`로 이슈 정보를 가져옵니다. (title, description, state, assignee, attachments, comments)

### Step 3: Parse AC Items

이슈 description에서 AC 항목을 파싱합니다.

**현행 형식 (우선):**
- AC 섹션 찾기 (`## 3. 완료 조건 (Acceptance Criteria)`, `## 3. 완료 조건`)
- 각 체크박스 항목 파싱 (`- [ ]` 또는 `- [x]`)
- 결과물 추출 (`→ 결과물:` 이후 내용)

**레거시 형식 (호환):**
- DoD 섹션 찾기 (`## Definition of Done`, `## DoD` 등)
- AC 섹션 찾기 (`## Acceptance Criteria`, `## AC` 등)

### Step 4: Parse Scope & Validate MR Coverage

**⚠️ CRITICAL: 이슈의 스코프에 명시된 모든 시스템/레포에 대해 MR 링크가 첨부되어야 합니다.**

이슈 description의 "범위 (Scope)" 또는 "4. 범위 (Scope)" 섹션을 파싱하여 영향받는 시스템을 식별하고, 각 시스템에 대한 MR 링크 존재 여부를 확인합니다.

**PR/MR 링크 탐색 위치:**
- **이슈 `attachments`** (이슈 리소스로 첨부된 PR/MR 링크 — evidence 스킬이 `links` 필드로 추가)
- description 텍스트의 `→ 결과물:` 뒤에 있는 URL (레거시 호환)

스코프 파싱, 시스템-MR 매핑, 커버리지 검증은 [mr_scope_validation.md Section 1-3](references/mr_scope_validation.md) 참조

### Step 5: Check MR Code Review + Fetch Diffs (Gate, Parallel)

**⚠️ CRITICAL: MR에 코드 리뷰가 없으면 검증을 진행하지 않고 즉시 중단합니다.**

이 단계는 Gate입니다. 통과하지 못하면 이후 검증을 진행하지 않습니다.

**⚡ 병렬 실행:** Step 4에서 식별된 **모든 MR에 대해 리뷰 정보와 Diff를 동시에 조회**합니다. 각 MR별로 2개 명령을 병렬로 실행하고, MR 간에도 병렬로 실행합니다.

    예: MR이 3개인 경우 → 6개 명령을 한 번에 병렬 실행
    - MR1: gh pr view --json reviews,comments  |  gh pr diff
    - MR2: glab api .../notes                  |  glab api .../changes
    - MR3: glab api .../notes                  |  glab api .../changes

1. **모든 MR에 대해 병렬로 조회:**
   - **GitHub**: `gh pr view {url} --json reviews,comments` + `gh pr diff {number} --repo {owner/repo}`
     - **⚠️ 주의**: `gh api repos/.../pulls/{n}/reviews`는 공식 리뷰만, `gh api repos/.../pulls/{n}/comments`는 인라인 diff 코멘트만 반환합니다. PR 대화 탭의 일반 코멘트(코드 리뷰 결과 등)는 포함되지 않으므로 반드시 `gh pr view --json reviews,comments`를 사용하세요.
   - **GitLab**: `GITLAB_HOST={host} glab api "/projects/{id}/merge_requests/{number}/notes"` + `GITLAB_HOST={host} glab api "/projects/{path}/merge_requests/{number}/changes"`

2. **Gate 판정 — 리뷰 0건 AND 코멘트 0건인 MR이 있으면:**
   - **콘솔에 안내 메시지 출력** (Linear 코멘트가 아님):

         ⚠️ 코드 리뷰 미수행 — 검증을 중단합니다.

         다음 MR에 코드 리뷰 기록이 없습니다:
         - PR #1: https://github.com/org/repo/pull/1 (리뷰 0건, 코멘트 0건)

         `/code-review` 스킬로 코드 리뷰를 먼저 수행한 후 다시 검증을 요청해주세요.

   - **검증을 즉시 종료** (이후 Step으로 진행하지 않음, Linear 코멘트 작성 안 함)
3. **리뷰 또는 코멘트가 1건 이상이면:** 이미 조회된 Diff 데이터로 Step 6 진행

### Step 6: Analyze MR Diffs Against AC Items

**⚠️ CRITICAL: 각 MR의 코드 diff를 확인하여 AC 항목의 구현이 실제로 반영되었는지 검증합니다.**

Step 5에서 이미 병렬 조회한 Diff 데이터를 사용합니다. 추가 API 호출 없이 분석만 수행합니다.

단순히 MR이 merged 상태인지 확인하는 것을 넘어서, diff 내용이 AC 항목을 실제로 구현하고 있는지 검증합니다.

Diff 조회, 분석, AC 커버리지 확인은 [mr_scope_validation.md Section 4-7](references/mr_scope_validation.md) 참조

### Step 7: Classify Evidence Types

각 결과물의 유형을 분류합니다. (`pr_mr`, `ci_cd_log`, `monitoring`, `api_endpoint`, `document`, `frontend_url`, `data_path`, `image`, `video`, `metric_value`, `text`)

상세 분류 규칙과 URL 패턴은 [validation_templates.md Section 6](references/validation_templates.md) 참조

### Step 8: Validate Each Item (Parallel)

유형별로 검증을 수행합니다.

**⚡ 병렬 실행:** AC 항목 간에는 의존성이 없으므로 **모든 AC 항목을 동시에 병렬 검증**합니다.

    실행 방법:
    1. 각 AC 항목의 evidence type을 분류한 후, 검증에 필요한 도구 호출을 파악
    2. 독립적인 도구 호출(WebFetch, curl, gh, glab, Read 등)을 한 번에 병렬로 실행
    3. 인증이 필요한 항목은 blocked_items에 기록하고 나머지 항목은 병렬 진행 계속

    예: AC 5개인 경우
    - AC 1 (pr_mr): gh pr view ...
    - AC 2 (image): Read tool로 이미지 확인
    - AC 3 (frontend_url): WebFetch ...
    - AC 4 (document): WebFetch ...
    - AC 5 (ci_cd_log): gh run view ...
    → 5개 도구 호출을 한 번에 병렬 실행

**⚠️ CRITICAL: 인증 실패 시 바로 "수동 확인 필요"로 넘어가지 말 것!** 공개 접근 → CLI 인증 확인 → 사용자 인증 요청 → 최후 수단 순서로 시도합니다.

유형별 검증 방법과 인증 처리는 [evidence_validation_methods.md](references/evidence_validation_methods.md) 참조 — PR/MR, CI/CD, URL, 문서, API, 모니터링, 이미지/동영상, 텍스트, 데이터 경로

### Step 9: Handle Validation Failures

**⚠️ CRITICAL: Principle 1 — 실패해도 끝까지 진행!**

검증 도중 실패가 발생하면 `blocked_items`에 기록 (실패 유형 + 사유 + 필요 조치)하고 다음 항목으로 진행합니다.

실패 유형과 blocked_items 형식은 [evidence_validation_methods.md Section 11](references/evidence_validation_methods.md) 참조

### Step 10: Generate Validation Report

리포트 템플릿은 [validation_templates.md](references/validation_templates.md) 참조

- 전체 통과 (PASS): Section 1.1 템플릿 사용
- 부분 통과 (PARTIAL): Section 1.2 템플릿 사용
- 전체 실패 (FAIL): Section 1.3 템플릿 사용
- 실패 유형별 메시지: Section 2
- 검증 상세 메시지: Section 3
- 검증 히스토리: Section 4 — 검증 결과 코멘트 하단에 포함

### Step 11+12: Update Checkboxes + Post Comment (Parallel)

**⚡ 병렬 실행:** 체크박스 업데이트(description)와 코멘트 작성/수정은 서로 다른 리소스에 쓰므로 **동시에 실행**합니다.

    병렬 실행 구조:
    ┌─ (A) 체크박스 업데이트 → save_issue (description)
    └─ (B) 코멘트 작성/수정 → create_comment 또는 GraphQL update

**(A) 체크박스 업데이트:**

**IMPORTANT: 검증 통과한 항목은 반드시 체크박스를 업데이트해야 합니다!**

1. `mcp__linear__get_issue`로 현재 description 가져오기
2. 통과한 항목: `- [ ]` → `- [x]` / 실패한 항목: `- [x]` → `- [ ]`
3. `mcp__linear__save_issue`로 description 업데이트

**(B) 코멘트 작성/수정:**

**⚠️ CRITICAL: 재검증 시 새 코멘트를 추가하지 않고 기존 코멘트를 업데이트합니다!**

검증 결과와 히스토리를 하나의 코멘트로 관리합니다.

1. `mcp__linear__list_comments`로 기존 검증 코멘트 검색 (패턴: `# ✅ 검증 완료`, `# ⚠️ 검증 실패`, `# ❌ 검증 실패`)
2. **기존 코멘트 있음:**
   - 기존 코멘트의 히스토리 섹션을 파싱하여 시도 횟수 확인
   - 최신 검증 결과로 전체 교체 + 히스토리에 새 행 추가
   - GraphQL API로 업데이트:
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: ${LINEAR_API_KEY}" \
  -d '{"query": "mutation($id: String!, $body: String!) { commentUpdate(id: $id, input: { body: $body }) { success } }", "variables": {"id": "{comment_id}", "body": "{updated_body}"}}'
```
3. **기존 코멘트 없음 → `mcp__linear__create_comment`로 새로 생성** (히스토리 시도 #1)
4. `LINEAR_API_KEY` 미설정 시 새 코멘트를 생성하되, 사용자에게 이전 코멘트를 수동 삭제하도록 안내

**⚠️ 주의:** (A)의 `get_issue`와 (B)의 `list_comments`는 병렬 실행 가능하지만, 각각의 읽기→쓰기는 순차 유지

### Step 12: Move to "In Review" (Optional)

**규칙: 검증 통과 시 In Review로 이동. 사람의 최종 확인 후 Done으로 전환.**

**⚠️ CRITICAL: Done이 아닌 반드시 "In Review"로 전환해야 합니다!**

모든 항목 통과 시, `AskUserQuestion`으로 사용자에게 확인합니다:
- 질문: "이슈를 'In Review' 상태로 이동하시겠습니까?"
- 선택지: "예, In Review로 이동", "아니오, 현재 상태 유지"
- 사용자는 "Other"로 다른 지시사항을 입력할 수 있음

사용자가 승인하면 `mcp__linear__save_issue`로 "In Review" 상태로 이동합니다.

상태 변경 안내 메시지는 [validation_templates.md Section 5](references/validation_templates.md) 참조.

---

## Resources

- [guideline-ref.md](../_shared/guideline-ref.md) — 가이드라인 핵심 규칙 (이슈 상태, Estimate, AI-Verification Loop)
- [validation_templates.md](references/validation_templates.md) — 검증 결과 코멘트 템플릿, 실패 유형별 메시지, 검증 상세 메시지, 히스토리 템플릿, Evidence Type 분류 규칙, 에러 메시지
- [evidence_validation_methods.md](references/evidence_validation_methods.md) — 유형별 상세 검증 방법 (PR/MR, CI/CD, URL, 문서, API, 모니터링, 이미지/동영상, 텍스트, 데이터 경로), 인증 처리, 실패 유형 및 blocked_items 형식
- [mr_scope_validation.md](references/mr_scope_validation.md) — 스코프 파싱, 시스템-MR 매핑, MR 커버리지 검증, Diff 분석, AC 커버리지 확인

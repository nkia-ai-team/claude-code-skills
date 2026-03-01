---
name: linear-issue-validator
description: Validate and verify completed Linear issues by checking DoD (Definition of Done) and AC (Acceptance Criteria) items. Supports various evidence types including URLs, documents, images, PR links, API endpoints, and CI/CD logs. Posts validation results as comments and optionally moves issues to "In Review" status when all items pass.
---

# Linear Issue Validator

## CRITICAL: First Step - Read the Templates

**BEFORE generating any validation report, you MUST read:**
- [validation_templates.md](references/validation_templates.md) — 검증 결과 코멘트 템플릿, 실패 유형별 메시지, Evidence Type 분류 규칙

**All validation comments MUST follow the exact templates from the references file.**

---

## Overview

완료된 Linear 이슈의 DoD/AC 항목을 검증하고 평가하는 스킬입니다. 작업자가 첨부한 결과물(링크, 이미지, 텍스트 등)을 실제로 확인하여 검증합니다.

**주요 기능:**
1. DoD/AC 항목별 결과물 파싱 및 검증
2. 다양한 결과물 유형 지원 (URL, 이미지, PR, API, CI/CD 등)
3. 검증 결과를 이슈 코멘트로 작성
4. 전체 통과 시 "In Review" 상태로 이동 (선택)

---

## Core Validation Principles

### Principle 1: 검증 실패를 만나도 끝까지 진행

**인증 실패, MCP 미연결, API 조회 불가 등으로 특정 항목을 검증하지 못하더라도 절대 멈추지 마세요!**
- 실패 항목을 `blocked_items`에 기록하고, **나머지 항목 검증을 끝까지 진행**
- 모든 항목 검증 완료 후, 마지막에 blocked_items를 한번에 사용자에게 보고

### Principle 2: 접속 확인 ≠ 검증 완료

**URL/문서 링크 검증 시 단순 "접속 가능 여부"만 확인하면 안 됩니다!**
- 결과물의 **내용이 DoD/AC 요건과 일치하는지** 확인해야 합니다
- 페이지 제목/주제가 요건과 관련 있는지, 핵심 키워드가 포함되어 있는지 확인

### Principle 3: 이미지/동영상은 실제 첨부 및 내용 확인 필수

**이미지나 동영상 증빙은 단순 URL 텍스트만으로 통과시키면 안 됩니다!**
- Read tool의 vision 기능으로 **실제 이미지를 열어서 내용 확인** 필수
- URL만 텍스트로 적혀있고 실제 첨부가 아닌 경우 → `media_not_viewable`

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
| `--dod-only` | DoD 항목만 검증 |
| `--ac-only` | AC 항목만 검증 |

---

## Workflow

### Step 1: Parse Issue Input

이슈 ID 또는 URL을 파싱합니다. (`NKIA-123`, Full URL, UUID 지원)

### Step 2: Fetch Issue Details

`mcp__linear__get_issue`로 이슈 정보를 가져옵니다. (title, description, state, assignee, attachments, comments)

### Step 3: Parse DoD/AC Items

이슈 description에서 DoD/AC 항목을 파싱합니다.
- DoD 섹션 찾기 (`## Definition of Done`, `## DoD` 등)
- AC 섹션 찾기 (`## Acceptance Criteria`, `## AC` 등)
- 각 체크박스 항목 파싱 (`- [ ]` 또는 `- [x]`)
- 결과물 추출 (`→ 결과물:` 이후 내용)

### Step 4: Parse Scope & Validate MR Coverage

**⚠️ CRITICAL: 이슈의 스코프에 명시된 모든 시스템/레포에 대해 MR 링크가 첨부되어야 합니다.**

이슈 description의 "범위 (Scope)" 섹션을 파싱하여 영향받는 시스템을 식별하고, 각 시스템에 대한 MR 링크 존재 여부를 확인합니다.

스코프 파싱, 시스템-MR 매핑, 커버리지 검증은 [mr_scope_validation.md Section 1-3](references/mr_scope_validation.md) 참조

### Step 5: Review MR Diffs Against AC Items

**⚠️ CRITICAL: 각 MR의 코드 diff를 확인하여 AC 항목의 구현이 실제로 반영되었는지 검증합니다.**

단순히 MR이 merged 상태인지 확인하는 것을 넘어서, diff 내용이 AC 항목을 실제로 구현하고 있는지 검증합니다.

Diff 조회, 분석, AC 커버리지 확인은 [mr_scope_validation.md Section 4-7](references/mr_scope_validation.md) 참조

### Step 6: Classify Evidence Types

각 결과물의 유형을 분류합니다. (`pr_mr`, `ci_cd_log`, `monitoring`, `api_endpoint`, `document`, `frontend_url`, `data_path`, `image`, `video`, `metric_value`, `text`)

상세 분류 규칙과 URL 패턴은 [validation_templates.md Section 7](references/validation_templates.md) 참조

### Step 7: Validate Each Item

유형별로 검증을 수행합니다.

**⚠️ CRITICAL: 인증 실패 시 바로 "수동 확인 필요"로 넘어가지 말 것!** 공개 접근 → CLI 인증 확인 → 사용자 인증 요청 → 최후 수단 순서로 시도합니다.

유형별 검증 방법과 인증 처리는 [evidence_validation_methods.md](references/evidence_validation_methods.md) 참조 — PR/MR, CI/CD, URL, 문서, API, 모니터링, 이미지/동영상, 텍스트, 데이터 경로

### Step 8: Handle Validation Failures

**⚠️ CRITICAL: Principle 1 — 실패해도 끝까지 진행!**

검증 도중 실패가 발생하면 `blocked_items`에 기록 (실패 유형 + 사유 + 필요 조치)하고 다음 항목으로 진행합니다.

실패 유형과 blocked_items 형식은 [evidence_validation_methods.md Section 11](references/evidence_validation_methods.md) 참조

### Step 9: Generate Validation Report

리포트 템플릿은 [validation_templates.md](references/validation_templates.md) 참조
- 전체 통과 (PASS): Section 1.1 템플릿 사용
- 부분 통과 (PARTIAL): Section 1.2 템플릿 사용
- 전체 실패 (FAIL): Section 1.3 템플릿 사용
- 실패 유형별 메시지: Section 2
- 검증 상세 메시지: Section 3
- 히스토리: Section 4

### Step 10: Update Issue Checkboxes

**IMPORTANT: 검증 통과한 항목은 반드시 체크박스를 업데이트해야 합니다!**

1. `mcp__linear__get_issue`로 현재 description 가져오기
2. 통과한 항목: `- [ ]` → `- [x]` / 실패한 항목: `- [x]` → `- [ ]`
3. `mcp__linear__update_issue`로 description 업데이트

### Step 11: Post or Update Comment

**⚠️ CRITICAL: 기존 검증 코멘트가 있으면 새로 달지 않고 업데이트합니다!**

1. `mcp__linear__list_comments`로 기존 검증 코멘트 검색 (패턴: `# ✅ 검증 완료`, `# ⚠️ 검증 완료`, `# ❌ 검증 실패`)
2. **기존 코멘트 있음 → Linear GraphQL API로 업데이트:**
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: ${LINEAR_API_KEY}" \
  -d '{"query": "mutation($id: String!, $body: String!) { commentUpdate(id: $id, input: { body: $body }) { success } }", "variables": {"id": "{comment_id}", "body": "{report}"}}'
```
3. **기존 코멘트 없음 → `mcp__linear__create_comment`로 새로 생성**
4. `LINEAR_API_KEY` 미설정 시 새 코멘트를 생성하되, 사용자에게 안내

### Step 12: Move to "In Review" (Optional)

모든 항목 통과 시, 사용자에게 상태 변경 여부를 확인 후 `mcp__linear__update_issue`로 "In Review" 상태로 이동합니다.

---

## Resources

- [validation_templates.md](references/validation_templates.md) — 검증 결과 코멘트 템플릿, 실패 유형별 메시지, 검증 상세 메시지, 히스토리 템플릿, Evidence Type 분류 규칙, 에러 메시지
- [evidence_validation_methods.md](references/evidence_validation_methods.md) — 유형별 상세 검증 방법 (PR/MR, CI/CD, URL, 문서, API, 모니터링, 이미지/동영상, 텍스트, 데이터 경로), 인증 처리, 실패 유형 및 blocked_items 형식
- [mr_scope_validation.md](references/mr_scope_validation.md) — 스코프 파싱, 시스템-MR 매핑, MR 커버리지 검증, Diff 분석, AC 커버리지 확인

---
name: code-review
description: Perform automated code reviews on GitHub Pull Requests or GitLab Merge Requests. Input a PR/MR URL to analyze code changes, validate branch naming and commit messages, check for security vulnerabilities, performance issues, and code quality. Posts review results as comments directly on the PR/MR.
---

# Code Review Skill

## CRITICAL: First Step - Read the Ruleset

**BEFORE doing anything else, you MUST read:**
- [code_review_ruleset.md](references/code_review_ruleset.md) — 브랜치명/커밋 메시지 검증 규칙, 코드 리뷰 체크리스트, 리뷰 결과 템플릿, 심각도 레벨

**All review comments MUST be written in Korean (한국어) using the exact templates from the ruleset.**

## Overview

Perform comprehensive code reviews on GitHub Pull Requests or GitLab Merge Requests by analyzing code changes and posting detailed review comments.

**Supported Platforms:** GitHub (`gh` CLI), GitLab (`glab` CLI)

**Key Features:**
- Branch name validation
- Commit message validation (ALL commits, not just latest)
- Code quality analysis (Clean Code, SOLID principles)
- Security vulnerability detection (OWASP Top 10)
- Performance issue detection (N+1, pagination, etc.)
- Test code review
- Automatic comment posting to PR/MR

## Usage

```
/code-review <PR/MR URL>
```

**Options:**

| 옵션 | 설명 |
|-----|------|
| `--focus security` | 보안 취약점만 집중 리뷰 |
| `--focus performance` | 성능 이슈만 집중 리뷰 |
| `--focus quality` | 코드 품질만 집중 리뷰 |
| `--focus all` | 전체 리뷰 (기본값) |

---

## Workflow

### Step 1: Parse URL and Detect Platform

URL에서 플랫폼을 감지합니다.
- `github.com` 포함 → GitHub
- `gitlab` 포함 또는 `/-/merge_requests/` 경로 → GitLab
- 판별 불가 시 사용자에게 확인

### Step 2: Verify CLI Authentication

`gh auth status` 또는 `glab auth status`로 인증 상태를 확인합니다.

CLI 설치 및 인증은 [platform_operations.md Section 5](references/platform_operations.md) 참조

### Step 3: Fetch PR/MR Information

**CRITICAL: 페이지네이션으로 모든 커밋과 변경 파일을 빠짐없이 조회해야 합니다.**

- GitHub: `gh pr view` + `gh api --paginate`로 전체 커밋 조회 + `gh pr diff`로 전체 diff 조회
- GitLab: self-hosted URL 파싱 → project ID 조회 → `per_page=100`으로 커밋/변경사항 페이지네이션

상세 CLI 명령어, 페이지네이션, 대용량 파일 감지, URL 파싱은 [platform_operations.md Section 1-2](references/platform_operations.md) 참조

### Step 4+5+6: Validate Branch / Validate Commits / Code Review (병렬)

**Step 3 완료 후, 아래 3개 작업은 서로 의존성이 없으므로 병렬로 실행합니다.**

**4) Validate Branch Name**

브랜치명을 ruleset 기준으로 검증합니다.

**Pattern:** `^(feature|bugfix|hotfix|refactor|docs|test|config)/[a-z]+-[0-9]+-[a-z0-9-]+$`

**Check:** Type prefix, Linear 이슈 번호 형식, kebab-case, 브랜치-작업 타입 일치

**5) Validate Commit Messages**

**CRITICAL: 모든 커밋 메시지를 검증합니다 (최신 커밋만이 아님).**
- Step 3에서 페이지네이션으로 조회한 전체 커밋 목록 사용
- 총 커밋 수가 예상과 일치하는지 확인

**Pattern:** `^[a-z]+-[0-9]+ (Feat|Fix|Refactor|Cleanup|Wip|Revert|Style|Merge|Docs|Config|Dependency|Test) : .+$`

**Check:** Linear 이슈 번호, Type 키워드, 구분자 (` : `), 브랜치 이슈 번호 일치

**6) Perform Code Review**

**CRITICAL: 전체 MR diff (base → head)를 리뷰합니다. 개별 커밋 diff가 아닙니다.**

Diff 완전성 검증 후, ruleset의 코드 리뷰 체크리스트에 따라 분석합니다:

체크리스트 상세는 [code_review_ruleset.md Section 5](references/code_review_ruleset.md) 참조:
- 5.1 코드 품질 (Clean Code, Java/Spring 특화)
- 5.2 보안 검토 (OWASP Top 10)
- 5.3 성능 검토
- 5.4 테스트 코드 검토
- 5.5 에러 처리
- 5.6 API 문서화

### Step 7: Generate Review Results

템플릿 상세는 [code_review_ruleset.md Section 6](references/code_review_ruleset.md) 참조:
- 6.1 전체 요약 template
- 6.2 상세 코멘트 형식 template
- 6.3 심각도 레벨 (🔴 Critical, 🟡 Warning, 🔵 Info, 🟢 Praise)

### Step 8: Post Review Comment

플랫폼별 CLI로 리뷰 코멘트를 포스팅합니다.

포스팅 명령어는 [platform_operations.md Section 3](references/platform_operations.md) 참조 (GitHub gh / GitLab glab)

### Step 9: Display Completion Message

```
Code review completed and posted to {platform}!

PR/MR: {url}
Issues Found: {critical_count} critical, {warning_count} warnings, {info_count} info
Verdict: {verdict}
```

---

## Resources

- [code_review_ruleset.md](references/code_review_ruleset.md) — 브랜치명/커밋 메시지 검증 규칙, 코드 리뷰 체크리스트 (품질/보안/성능/테스트/에러/API), 리뷰 결과 작성 템플릿, 심각도 레벨
- [platform_operations.md](references/platform_operations.md) — GitHub/GitLab CLI 명령어, 페이지네이션 처리, 대용량 파일 감지, URL 파싱, 코멘트 포스팅, CLI 설치/인증, 에러 처리

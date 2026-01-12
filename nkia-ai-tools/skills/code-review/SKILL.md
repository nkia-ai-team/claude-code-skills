---
name: code-review
description: Perform automated code reviews on GitHub Pull Requests or GitLab Merge Requests. Input a PR/MR URL to analyze code changes, validate branch naming and commit messages, check for security vulnerabilities, performance issues, and code quality. Posts review results as comments directly on the PR/MR.
---

# Code Review Skill

## CRITICAL: First Step - Read the Ruleset

**BEFORE doing anything else, you MUST read the ruleset file:**

```
Read file: references/code_review_ruleset.md
```

This ruleset file contains:
- Branch name validation rules and regex patterns
- Commit message validation rules
- Code review checklist (quality, security, performance)
- **Review result templates in Korean** - MUST follow exactly
- Severity levels with emoji indicators (🔴 🟡 🔵 🟢 ✅ ❌ ⚠️)

**All review comments MUST be written in Korean (한국어) using the exact templates from the ruleset.**

## Overview

Perform comprehensive code reviews on GitHub Pull Requests or GitLab Merge Requests by analyzing code changes and posting detailed review comments.

**Supported Platforms:**
- GitHub (using `gh` CLI)
- GitLab (using `glab` CLI)

**Key Features:**
- Branch name validation
- Commit message validation
- Code quality analysis (Clean Code, SOLID principles)
- Security vulnerability detection (OWASP Top 10)
- Performance issue detection (N+1, pagination, etc.)
- Test code review
- Automatic comment posting to PR/MR

## Usage

```
/code-review <PR/MR URL>
```

**Examples:**
```
/code-review https://github.com/owner/repo/pull/123
/code-review https://gitlab.com/owner/repo/-/merge_requests/456
/code-review https://cims2.nkia.net:8443/gitlab/lucida-domain-wpm/-/merge_requests/78
```

---

## Workflow

### Step 1: Parse URL and Detect Platform

Parse the input URL to detect the platform:

**GitHub PR URL Patterns:**
- `https://github.com/{owner}/{repo}/pull/{number}`
- `https://github.com/{owner}/{repo}/pull/{number}/files`

**GitLab MR URL Patterns:**
- `https://gitlab.com/{owner}/{repo}/-/merge_requests/{number}`
- `https://{custom-domain}/{path}/-/merge_requests/{number}`

**Detection Logic:**
1. Extract host from URL
2. If contains `github.com` -> GitHub
3. If contains `gitlab` or path contains `/-/merge_requests/` -> GitLab
4. If unable to determine -> Ask user for platform confirmation

### Step 2: Verify CLI Authentication

**For GitHub:**
```bash
gh auth status
```

If authentication fails, display:
```
GitHub CLI authentication required.
Please authenticate with:
$ gh auth login
```

**For GitLab:**
```bash
glab auth status
```

If authentication fails, display:
```
GitLab CLI authentication required.
Please authenticate with:
$ glab auth login

For self-hosted GitLab instances:
$ glab auth login --hostname gitlab.your-company.com
```

### Step 3: Fetch PR/MR Information

**For GitHub PR:**
```bash
# PR metadata
gh pr view {url} --json title,body,author,state,additions,deletions,files,baseRefName,headRefName,commits

# PR diff
gh pr diff {url}
```

**For GitLab MR:**
```bash
# For gitlab.com
glab mr view {number} --repo {owner/repo}
glab mr diff {number} --repo {owner/repo}

# For self-hosted GitLab (e.g., cims2.nkia.net:8443)
# Step 3-1: Parse project path from URL
# URL: https://cims2.nkia.net:8443/gitlab/lucida-ai-develop/-/merge_requests/4
# Extract: hostname=cims2.nkia.net:8443, project_path=gitlab/lucida-ai-develop, mr_number=4

# Step 3-2: Get project ID using URL-encoded path OR search
# Method 1: URL-encoded path (replace / with %2F)
GITLAB_HOST={hostname} glab api "/projects/{group}%2F{project}"
# Example: GITLAB_HOST=cims2.nkia.net:8443 glab api "/projects/gitlab%2Flucida-ai-develop"

# Method 2: Search by project name (if path encoding fails)
GITLAB_HOST={hostname} glab api "/projects?search={project_name}"
# Example: GITLAB_HOST=cims2.nkia.net:8443 glab api "/projects?search=lucida-ai-develop"
# Extract "id" field from response (e.g., "id": 141)

# Step 3-3: Fetch MR information using project ID
GITLAB_HOST={hostname} glab api "/projects/{project_id}/merge_requests/{mr_number}"
GITLAB_HOST={hostname} glab api "/projects/{project_id}/merge_requests/{mr_number}/changes"
GITLAB_HOST={hostname} glab api "/projects/{project_id}/merge_requests/{mr_number}/commits"
```

**GitLab URL Parsing Example:**
```
URL: https://cims2.nkia.net:8443/gitlab/lucida-ai-develop/-/merge_requests/4
                 │                    │                        │
                 hostname             project_path             mr_number

project_path = "gitlab/lucida-ai-develop"
URL-encoded  = "gitlab%2Flucida-ai-develop"
```

### Step 4: Validate Branch Name

Validate the source branch name according to the ruleset in `references/code_review_ruleset.md`.

**Validation Pattern:**
```regex
^(feature|bugfix|hotfix|refactor|docs|test|config)/PIMS-[0-9]+-[a-z0-9-]+$
```

**Check Items:**
1. Type prefix (feature, bugfix, hotfix, refactor, docs, test, config)
2. PIMS number format (PIMS-XXXXX)
3. Description in kebab-case
4. Branch type matches work type

### Step 5: Validate Commit Messages

Validate all commit messages according to the ruleset.

**Validation Pattern:**
```regex
^#[0-9]+ (Feat|Fix|Refactor|Cleanup|Wip|Revert|Style|Merge|Docs|Config|Dependency|Test) : .+$
```

**Check Items:**
1. PIMS number present (#XXXXX)
2. Valid type keyword
3. Proper separator (` : `)
4. PIMS number matches branch PIMS number

### Step 6: Perform Code Review

Analyze the diff according to **Section 5 (코드 리뷰 체크리스트)** in `references/code_review_ruleset.md`:
- 5.1 코드 품질 (Clean Code, Java/Spring 특화)
- 5.2 보안 검토 (OWASP Top 10)
- 5.3 성능 검토
- 5.4 테스트 코드 검토
- 5.5 에러 처리
- 5.6 API 문서화

### Step 7: Generate Review Results

**IMPORTANT: Use the EXACT format from Section 6 (리뷰 결과 작성 형식) in `references/code_review_ruleset.md`.**

The ruleset contains:
- 6.1 전체 요약 template
- 6.2 상세 코멘트 형식 template
- 6.3 심각도 레벨 (🔴 Critical, 🟡 Warning, 🔵 Info, 🟢 Praise)

### Step 8: Post Review Comment

**For GitHub PR:**
```bash
gh pr comment {url} --body "{review_content}"
```

**For GitLab MR:**
```bash
# For gitlab.com
glab mr note {mr_number} --repo {owner/repo} --message "{review_content}"

# For self-hosted GitLab (use project_id obtained in Step 3-2)
GITLAB_HOST={hostname} glab api --method POST "/projects/{project_id}/merge_requests/{mr_number}/notes" -f body="{review_content}"

# Example:
# GITLAB_HOST=cims2.nkia.net:8443 glab api --method POST "/projects/141/merge_requests/4/notes" -f body="$(cat <<'EOF'
# Review content here...
# EOF
# )"
```

### Step 9: Display Completion Message

After posting the comment, display:
```
Code review completed and posted to {platform}!

PR/MR: {url}
Issues Found: {critical_count} critical, {warning_count} warnings, {info_count} info
Verdict: {verdict}

Review comment has been posted successfully.
```

---

## Prerequisites

### GitHub CLI (gh)
```bash
# Install (macOS)
brew install gh

# Authenticate
gh auth login
```

### GitLab CLI (glab)
```bash
# Install (macOS)
brew install glab

# Authenticate (gitlab.com)
glab auth login

# Authenticate (self-hosted GitLab)
glab auth login --hostname gitlab.your-company.com
```

---

## Error Handling

### CLI Not Installed
```
{platform} CLI is not installed.
Please install with:
$ brew install {gh/glab}
```

### Authentication Failed
```
{platform} CLI authentication required.
Please authenticate with:
$ {gh/glab} auth login
```

### PR/MR Access Denied
```
Unable to access PR/MR.
- Check repository access permissions
- For private repositories, ensure you have appropriate access rights
```

### URL Parse Error
```
Invalid PR/MR URL format.
Valid formats:
- GitHub: https://github.com/owner/repo/pull/123
- GitLab: https://gitlab.com/owner/repo/-/merge_requests/456
```

---

## Review Options

Users can request focused reviews:

```
/code-review {url} --focus security
/code-review {url} --focus performance
/code-review {url} --focus quality
/code-review {url} --focus all (default)
```

**Focus Options:**
- `security` - Focus on security vulnerabilities only
- `performance` - Focus on performance issues only
- `quality` - Focus on code quality only
- `all` - Review all areas (default)

---

## Large PR/MR Handling

For large changes (1000+ lines):

1. **Provide file-by-file summary first:**
```
This PR contains {n} files with +{additions} -{deletions} changes.

Major changed files:
1. src/api/auth.ts (+150, -30) - Authentication logic changes
2. src/utils/crypto.ts (+80, -0) - New utility added
...

Proceed with full review? Or select specific files to review?
```

2. **Allow file selection:**
```
Enter file numbers to review (e.g., 1,2,3 or all):
```

---

## Resources

### references/code_review_ruleset.md

Contains the comprehensive code review ruleset including:
- Branch name validation rules and patterns
- Commit message validation rules
- Code quality checklist (Clean Code, SOLID)
- Security review checklist (OWASP Top 10)
- Performance review checklist
- Test code review criteria
- Review result format templates
- Severity level definitions

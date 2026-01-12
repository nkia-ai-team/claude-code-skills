---
name: linear-issue-validator
description: Validate and verify completed Linear issues by checking DoD (Definition of Done) and AC (Acceptance Criteria) items. Supports various evidence types including URLs, documents, images, PR links, API endpoints, and CI/CD logs. Posts validation results as comments and optionally moves issues to "In Review" status when all items pass.
---

# Linear Issue Validator

## CRITICAL: First Step - Read the Templates

**BEFORE generating any validation report, you MUST read the templates file:**

```
Read file: references/validation_templates.md
```

This templates file contains:
- Validation result comment templates (PASS, PARTIAL, FAIL)
- Failure type specific messages
- Validation detail message formats
- Evidence type classification rules
- Error message templates

**All validation comments MUST follow the exact templates from the references file.**

---

## Overview

완료된 Linear 이슈의 DoD/AC 항목을 검증하고 평가하는 스킬입니다. 작업자가 첨부한 결과물(링크, 이미지, 텍스트 등)을 실제로 확인하여 검증합니다.

**주요 기능:**
1. DoD/AC 항목별 결과물 파싱 및 검증
2. 다양한 결과물 유형 지원 (URL, 이미지, PR, API, CI/CD 등)
3. 검증 결과를 이슈 코멘트로 작성
4. 전체 통과 시 "In Review" 상태로 이동 (선택)

## ⚠️ 핵심 검증 원칙: 접속 확인 ≠ 검증 완료

**URL/문서 링크 검증 시 단순 "접속 가능 여부"만 확인하면 안 됩니다!**

검증의 핵심은 **결과물의 내용이 DoD/AC 요건과 일치하는지** 확인하는 것입니다.

| 구분 | 잘못된 검증 | 올바른 검증 |
|-----|-----------|-----------|
| 문서 링크 | "페이지 접속됨 → 통과" | "문서 내용이 요건과 일치함 → 통과" |
| 공식문서 참조 | "HTTP 200 응답 → 통과" | "문서 주제가 조사 요건에 적합함 → 통과" |
| 프론트엔드 URL | "사이트 로드됨 → 통과" | "요구된 기능/UI가 구현됨 → 통과" |

**검증 시 확인해야 할 사항:**
1. 페이지/문서의 **제목과 주제**가 요건과 관련 있는가?
2. 요건에서 요구하는 **핵심 키워드/개념**이 내용에 포함되어 있는가?
3. 이 자료가 해당 DoD/AC 항목을 **실제로 증명/충족**하는가?

## Usage

```
/linear-issue-validator <issue-id-or-url>
```

**Examples:**
```
/linear-issue-validator NKIA-123
/linear-issue-validator https://linear.app/nkia-ai/issue/NKIA-123
```

---

## Supported Evidence Types

### 1. URL/Link Types

| 유형 | 패턴 | 검증 방법 |
|-----|------|----------|
| **일반 문서 링크** | Notion, Confluence, Google Docs 등 | WebFetch로 접속하여 내용 확인 |
| **프론트엔드 URL** | http(s)://... | 접속 가능 여부 + 페이지 내용 확인 |
| **PR/MR 링크** | github.com/.../pull/*, gitlab.com/.../merge_requests/* | gh/glab CLI로 상태 확인 (merged/approved) |
| **CI/CD 로그** | Jenkins, GitHub Actions, GitLab CI 등 | 빌드 성공 여부 확인 |
| **모니터링 링크** | Grafana, Datadog 등 | 접속하여 메트릭 확인 |
| **API 엔드포인트** | /api/*, /v1/* 등 | curl로 호출하여 응답 확인 |
| **테스트 리포트** | Coverage report, Test results | 목표 달성 여부 확인 |

### 2. Non-URL Types

| 유형 | 패턴 | 검증 방법 |
|-----|------|----------|
| **이미지** | 첨부된 스크린샷, 다이어그램 | 이미지 내용이 DoD/AC 요건과 일치하는지 확인 |
| **텍스트** | 직접 작성된 설명, 결과값 | 목적에 맞게 작성되었는지 확인 |
| **데이터 경로** | s3://, gs://, /data/* 등 | 경로 형식 유효성 검증 (접근권한 별도) |
| **메트릭 값** | 숫자, 퍼센트 등 | 목표 기준치 달성 여부 확인 |

---

## Workflow

### Step 1: Parse Issue Input

이슈 ID 또는 URL을 파싱합니다.

**Supported Formats:**
- Issue identifier: `NKIA-123`, `LIN-456`
- Full URL: `https://linear.app/team/issue/NKIA-123`
- Issue UUID

```
입력: NKIA-123
→ 파싱 결과: identifier = "NKIA-123"
```

### Step 2: Fetch Issue Details

`mcp__linear__get_issue`를 사용하여 이슈 정보를 가져옵니다.

**필요한 정보:**
- 이슈 제목 (title)
- 이슈 설명 (description) - DoD/AC 항목 포함
- 현재 상태 (state)
- 담당자 (assignee)
- 첨부 파일 (attachments)
- 기존 코멘트 (comments)

### Step 3: Parse DoD/AC Items

이슈 description에서 DoD/AC 항목을 파싱합니다.

**Expected Format in Description:**
```markdown
## Definition of Done (DoD)
- [x] CI 빌드 성공 및 이미지 배포 완료 → 결과물: https://jenkins.example.com/job/123
- [ ] 코드 리뷰 완료 → 결과물: https://github.com/org/repo/pull/456

## Acceptance Criteria (AC)
- [x] API 응답 시간 200ms 이하 → 결과물: 평균 150ms (테스트 결과 첨부)
- [ ] 에러율 0% 유지 → 결과물: https://grafana.example.com/dashboard/xyz
```

**Parsing Logic:**
1. DoD 섹션 찾기 (`## Definition of Done`, `## DoD` 등)
2. AC 섹션 찾기 (`## Acceptance Criteria`, `## AC` 등)
3. 각 체크박스 항목 파싱 (`- [ ]` 또는 `- [x]`)
4. 결과물 추출 (`→ 결과물:` 이후 내용)

**Parsed Item Structure:**
```json
{
  "type": "dod",
  "index": 1,
  "checked": true,
  "description": "CI 빌드 성공 및 이미지 배포 완료",
  "evidence": "https://jenkins.example.com/job/123",
  "evidence_type": "ci_cd_log"
}
```

### Step 4: Classify Evidence Types

각 결과물의 유형을 분류합니다.

**상세 분류 규칙은 `references/validation_templates.md` Section 7을 참조하세요.**

**지원 유형:**
| Type | 예시 |
|------|------|
| `pr_mr` | GitHub PR, GitLab MR |
| `ci_cd_log` | Jenkins, GitHub Actions |
| `monitoring` | Grafana, Datadog |
| `api_endpoint` | /api/*, /v1/* |
| `document` | Notion, Confluence |
| `frontend_url` | 일반 웹 URL |
| `data_path` | s3://, gs:// |
| `image` | *.png, *.jpg |
| `metric_value` | 숫자 + 단위 |
| `text` | 기타 텍스트 |

### Step 5: Validate Each Item

유형별로 검증을 수행합니다.

---

## ⚠️ CRITICAL: 인증 필요 시 처리 원칙

**절대로 첫 번째 접근 실패 후 바로 "수동 확인 필요"로 넘어가지 말 것!**

**인증 실패 시 처리 순서:**
1. **1차 시도**: 공개 접근 또는 기존 인증 정보로 접근
2. **2차 시도**: CLI 도구 인증 상태 확인 (gh, glab 등)
3. **3차 시도**: 사용자에게 인증 정보 입력 요청
4. **최후 수단**: 모든 방법 실패 시에만 수동 확인 요청

**사용자 인증 정보 요청 템플릿:**
```
🔐 인증이 필요한 리소스가 발견되었습니다.

리소스: {url}
유형: {resource_type}

다음 중 하나를 선택해주세요:

1. CLI 인증 진행 (권장)
   → {cli_auth_command}

2. API 토큰/인증 정보 직접 입력
   → 토큰을 입력하시면 이 세션에서 사용합니다

3. 쿠키/세션 정보 제공
   → 브라우저에서 복사한 인증 정보 사용

4. 스크린샷/텍스트로 대체
   → 자동 검증 건너뛰기

선택:
```

---

#### 5.1 PR/MR Link Validation

**GitHub PR:**
```bash
# 1차: gh CLI로 접근
gh pr view {url} --json state,merged,reviews,mergeable,statusCheckRollup

# 인증 실패 시:
# "GitHub CLI 인증이 필요합니다. `gh auth login` 실행하시겠습니까? (y/n)"
```

**GitLab MR (gitlab.com):**
```bash
# 1차: glab CLI로 접근
glab mr view {number} --repo {owner/repo}
```

**GitLab MR/파일 (self-hosted):**
```bash
# 1차: glab 인증 상태 확인
glab auth status --hostname {hostname}

# 인증 안 됨 → 사용자에게 선택지 제공:
# "GitLab {hostname} 인증이 필요합니다.
#  1. glab auth login --hostname {hostname} 실행
#  2. Personal Access Token 직접 입력
#  3. 스크린샷으로 대체
#  선택:"

# 2차: 인증 후 API 호출
# URL 파싱 예시:
# https://cims2.nkia.net:8443/gitlab/lucida-ai-develop/-/merge_requests/4
# → hostname: cims2.nkia.net:8443
# → project_path: gitlab/lucida-ai-develop (URL-encoded: gitlab%2Flucida-ai-develop)
# → mr_number: 4

# Project ID 조회
GITLAB_HOST={hostname} glab api "/projects/{group}%2F{project}"

# MR 정보 조회
GITLAB_HOST={hostname} glab api "/projects/{project_id}/merge_requests/{mr_number}"

# MR 노트/코멘트 조회 (리뷰 확인용)
GITLAB_HOST={hostname} glab api "/projects/{project_id}/merge_requests/{mr_number}/notes"

# 파일 내용 조회 (blob URL인 경우)
# URL: https://host/group/project/-/blob/branch/path/to/file.md
GITLAB_HOST={hostname} glab api "/projects/{project_id}/repository/files/{file_path_encoded}/raw?ref={branch}"
```

**검증 기준:**
- PR/MR이 merged 상태인가?
- 최소 1명 이상의 approve가 있는가?
- CI 체크가 통과했는가?
- (코드 리뷰의 경우) 리뷰 코멘트가 작성되어 있는가?

#### 5.2 CI/CD Log Validation

**Jenkins (인증 필요 시):**
```bash
# 1차: 공개 접근 시도
curl -s "{jenkins_url}/api/json"

# 인증 필요 시:
# "Jenkins 인증이 필요합니다.
#  1. API Token 입력 (username:token)
#  2. 빌드 결과 스크린샷으로 대체
#  선택:"

# 토큰 입력 시:
curl -s -u "{username}:{api_token}" "{jenkins_url}/api/json" | jq '.result'
```

**GitHub Actions:**
```bash
gh run view {run_id} --json status,conclusion
```

**GitLab CI (self-hosted):**
```bash
GITLAB_HOST={hostname} glab api "/projects/{project_id}/pipelines/{pipeline_id}"
GITLAB_HOST={hostname} glab api "/projects/{project_id}/pipelines/{pipeline_id}/jobs"
```

**검증 기준:**
- 빌드 결과가 SUCCESS인가?
- 모든 스텝이 통과했는가?

#### 5.3 Frontend URL Validation

```
1차: WebFetch로 접근 시도

인증 필요 시 (401/403 응답):
"이 URL은 로그인이 필요합니다.
 1. 세션 쿠키 입력 (브라우저 개발자 도구에서 복사)
 2. 로그인 후 접근 가능한 공개 URL로 교체
 3. 스크린샷으로 대체
 선택:"

쿠키 입력 시:
curl -H "Cookie: {session_cookie}" "{url}"
```

**검증 기준:**
- 페이지가 정상 로드되는가?
- 이슈에서 요구한 기능/UI가 표시되는가?
- 에러 메시지가 없는가?

⚠️ **CRITICAL: 접속 확인만으로는 검증 완료가 아닙니다!**

URL 접속 가능 여부만 확인하고 넘어가지 마세요. DoD/AC 항목의 **요건과 페이지 내용이 일치하는지** 반드시 확인해야 합니다.

**내용 일치 검증 체크리스트:**
1. **DoD/AC 항목의 요건 키워드 추출**: 해당 항목이 무엇을 요구하는지 파악
2. **페이지 제목/설명 확인**: 요건과 관련된 주제인지 확인
3. **핵심 키워드 포함 여부**: 요건에서 언급된 기술/개념이 페이지에 포함되어 있는지
4. **관련성 판단**: 단순히 "접속됨"이 아닌 "요건에 적합한 자료인지" 판단

**예시:**
```
DoD 항목: "플러그인 등록 방법 조사 완료 → [claude code plugin 공식문서](https://...)"

❌ 잘못된 검증:
   "페이지 접속 확인됨 → 통과"

✅ 올바른 검증:
   1. 페이지 내용 확인: "플러그인 만들기 - Claude Code Docs"
   2. 메타 설명: "슬래시 명령어, 에이전트, 훅, 스킬 및 MCP 서버를 사용하여 Claude Code를 확장..."
   3. 키워드 매칭: "플러그인", "등록", "만들기" 관련 내용 포함
   4. 결론: 요건("플러그인 등록 방법 조사")에 적합한 공식 문서임 → 통과
```

**인증 필요로 내용 확인 불가 시:**
- 수동 확인 요청 전에 사용자에게 페이지 내용이 요건과 일치하는지 질문
- "이 링크가 '{DoD/AC 요건}'에 대한 적절한 참조 자료입니까?"

#### 5.4 Document Link Validation

**Notion (공개 페이지):**
```
WebFetch로 접근
```

**Confluence (인증 필요 시):**
```bash
# Confluence MCP가 있으면 사용
# 없으면:
# "Confluence 인증이 필요합니다.
#  1. API Token 입력 (email:token)
#  2. 문서 내용 복사/붙여넣기
#  3. 스크린샷으로 대체
#  선택:"

curl -u "{email}:{api_token}" "{confluence_url}/rest/api/content/{page_id}?expand=body.storage"
```

**Google Docs (공유 설정에 따라):**
```
WebFetch로 접근 시도
접근 불가 시 → 공유 링크 또는 스크린샷 요청
```

**검증 기준:**
- 문서가 접근 가능한가?
- 요구된 내용이 포함되어 있는가?
- 형식이 올바른가?

⚠️ **CRITICAL: 문서 내용이 DoD/AC 요건과 일치하는지 반드시 확인!**

문서 링크 검증 시 단순 접속 확인이 아닌, **문서 내용이 해당 DoD/AC 항목의 요건을 충족하는지** 확인해야 합니다.

**문서 내용 검증 프로세스:**

1. **DoD/AC 요건 분석**
   - 해당 항목이 요구하는 것이 무엇인지 명확히 파악
   - 예: "플러그인 등록 방법 조사 완료" → "플러그인 등록 방법"에 대한 정보가 있어야 함

2. **문서 메타데이터 확인**
   - 문서 제목 (title)
   - 문서 설명 (description, meta)
   - 문서 태그/레이블

3. **문서 본문 내용 확인**
   - 요건과 관련된 핵심 키워드가 포함되어 있는지
   - 문서의 주제가 요건과 부합하는지
   - 단순히 관련 없는 문서가 아닌지

4. **적합성 판단**
   ```
   질문: "이 문서가 '{DoD/AC 요건}'을 충족하는 적절한 참조 자료인가?"

   ✅ 적합: 문서 내용이 요건에서 요구하는 정보를 포함
   ❌ 부적합: 문서 주제가 요건과 무관하거나 다른 내용
   ⚠️ 부분적: 관련은 있으나 요건을 완전히 충족하지 못함
   ```

**예시:**
```
DoD 항목: "플러그인 등록 방법 조사 완료 → [공식문서](https://code.claude.com/docs/ko/plugins)"

검증 과정:
1. WebFetch로 페이지 접근
2. 페이지 정보 확인:
   - title: "플러그인 만들기 - Claude Code Docs"
   - description: "슬래시 명령어, 에이전트, 훅, 스킬 및 MCP 서버를 사용하여 Claude Code를 확장하는 사용자 정의 플러그인을 만듭니다."
3. 요건 매칭:
   - 요건: "플러그인 등록 방법 조사"
   - 문서 주제: "플러그인 만들기" (등록/생성 방법 포함)
4. 결론: ✅ 적합한 참조 자료 → 검증 통과

부적합 예시:
DoD 항목: "성능 최적화 조사 완료 → [문서](https://example.com/intro)"
문서 내용: "회사 소개 페이지"
결론: ❌ 요건과 무관한 문서 → 검증 실패
```

**인증 필요로 내용 확인 불가 시:**
사용자에게 다음을 요청:
1. 문서 제목과 요약 제공
2. 요건과의 관련성 설명
3. 또는 스크린샷으로 내용 증명

#### 5.5 API Endpoint Validation

```bash
# 1차: 공개 API 접근
curl -s -o /dev/null -w "%{http_code}" "{api_url}"

# 인증 필요 시:
# "API 인증이 필요합니다.
#  1. Bearer Token 입력
#  2. API Key 입력
#  3. Basic Auth (username:password) 입력
#  선택:"

# 토큰 입력 시:
curl -H "Authorization: Bearer {token}" -s -o /dev/null -w "%{http_code}" "{api_url}"

# 응답 시간 측정
curl -H "Authorization: Bearer {token}" -s -o /dev/null -w "%{time_total}" "{api_url}"
```

**검증 기준:**
- 응답 코드가 2xx인가?
- 응답 시간이 기준 이내인가?
- 응답 형식이 올바른가?

#### 5.6 Monitoring Link Validation (Grafana, Datadog 등)

```
1차: WebFetch로 공개 대시보드 접근

인증 필요 시:
"모니터링 대시보드 인증이 필요합니다.
 1. API Key 입력
 2. 대시보드 스크린샷으로 대체 (메트릭 값 포함)
 선택:"

Grafana API (토큰 입력 시):
curl -H "Authorization: Bearer {api_key}" "{grafana_url}/api/dashboards/uid/{dashboard_uid}"
```

**검증 기준:**
- 대시보드가 접근 가능한가?
- 표시된 메트릭이 기준을 충족하는가?

#### 5.7 Image Validation

```
Read tool을 사용하여:
1. 이미지 내용 확인 (Claude의 vision 기능 활용)
2. DoD/AC 요건과 관련된 내용인지 판단
3. 스크린샷인 경우 예상 화면과 일치하는지 확인
```

**검증 기준:**
- 이미지가 DoD/AC 항목을 증명하는가?
- 필요한 정보가 이미지에 포함되어 있는가?

#### 5.8 Text/Metric Validation

**텍스트:**
- 목적에 맞는 내용이 작성되었는가?
- 필수 정보가 포함되어 있는가?

**메트릭:**
- 목표 수치를 달성했는가?
- 단위가 올바른가?

#### 5.9 Data Path Validation

```
경로 형식 검증:
- s3://bucket/path 형식 확인
- 경로가 의미있는 구조인지 확인

실제 접근 검증 (인증 정보 있을 시):
# AWS S3
aws s3 ls {s3_path}

# GCS
gsutil ls {gs_path}

인증 없으면 형식 검증만 수행
```

### Step 6: Handle Validation Failures

검증 실패 또는 불가능한 경우 처리:

**실패 유형:**

| 유형 | 원인 | 처리 방법 |
|-----|------|----------|
| `access_denied` | 인증 필요, 권한 없음 | 수동 확인 요청 |
| `not_found` | URL 404, 리소스 없음 | 결과물 재첨부 요청 |
| `timeout` | 응답 지연 | 재시도 후 수동 확인 |
| `invalid_format` | 잘못된 형식 | 올바른 형식으로 수정 요청 |
| `criteria_not_met` | 기준 미달성 | 구체적 부족분 명시 |
| `evidence_missing` | 결과물 미첨부 | 결과물 첨부 요청 |

**재시도 로직:**
```
최대 재시도: 2회
재시도 간격: 3초
재시도 후에도 실패 시 → manual_verification_required
```

### Step 7: Generate Validation Report

검증 결과를 정리합니다.

**IMPORTANT: `references/validation_templates.md` 파일의 템플릿을 사용하세요.**

```
Read file: references/validation_templates.md
```

**템플릿 선택:**
- 전체 통과 (PASS): Section 1.1 템플릿 사용
- 부분 통과 (PARTIAL): Section 1.2 템플릿 사용
- 전체 실패 (FAIL): Section 1.3 템플릿 사용

**실패 유형별 메시지:**
- Section 2의 실패 유형별 메시지 템플릿 참조
- `access_denied`, `not_found`, `criteria_not_met` 등

**검증 상세 메시지:**
- Section 3의 검증 성공 메시지 템플릿 참조
- PR/MR, CI/CD, URL, 메트릭, 이미지, 문서 등

### Step 8: Update Issue Checkboxes

**IMPORTANT: 검증 통과한 항목은 반드시 체크박스를 업데이트해야 합니다!**

검증 결과에 따라 이슈의 체크박스 상태를 업데이트합니다.

**Process:**
1. `mcp__linear__get_issue`로 현재 description 가져오기
2. 각 DoD/AC 항목의 검증 결과 확인
3. **통과한 항목**: `- [ ]`를 `- [x]`로 변경
4. **실패한 항목**: `- [x]`를 `- [ ]`로 변경 (이전에 체크되어 있었다면)
5. `mcp__linear__update_issue`로 description 업데이트

**체크박스 패턴 매칭:**
```regex
# 체크 안 됨 → 체크됨
- \[ \] (.+?) → 결과물:  →  - [x] $1 → 결과물:

# 체크됨 → 체크 안 됨 (실패 시)
- \[x\] (.+?) → 결과물:  →  - [ ] $1 → 결과물:
```

**Example:**
```markdown
# Before (검증 전)
## Definition of Done (DoD)
- [ ] CI 빌드 성공 → 결과물: https://jenkins.example.com/job/123
- [ ] 코드 리뷰 완료 → 결과물: https://github.com/org/repo/pull/456

## Acceptance Criteria (AC)
- [ ] API 응답 200ms 이하 → 결과물: 150ms 측정됨
- [ ] 에러율 0% → 결과물: (미첨부)

# After (검증 후) - DoD#1, DoD#2, AC#1 통과, AC#2 실패
## Definition of Done (DoD)
- [x] CI 빌드 성공 → 결과물: https://jenkins.example.com/job/123
- [x] 코드 리뷰 완료 → 결과물: https://github.com/org/repo/pull/456

## Acceptance Criteria (AC)
- [x] API 응답 200ms 이하 → 결과물: 150ms 측정됨
- [ ] 에러율 0% → 결과물: (미첨부)
```

**API 호출:**
```javascript
// 1. 이슈 정보 가져오기
const issue = await mcp__linear__get_issue({ id: "issue-id" });
const currentDescription = issue.description;

// 2. 체크박스 업데이트
let updatedDescription = currentDescription;

for (const item of validationResults) {
  if (item.status === "pass") {
    // 통과: 체크 안 됨 → 체크됨
    const pattern = `- [ ] ${escapeRegex(item.description)}`;
    const replacement = `- [x] ${item.description}`;
    updatedDescription = updatedDescription.replace(pattern, replacement);
  } else if (item.status === "fail") {
    // 실패: 체크됨 → 체크 안 됨
    const pattern = `- [x] ${escapeRegex(item.description)}`;
    const replacement = `- [ ] ${item.description}`;
    updatedDescription = updatedDescription.replace(pattern, replacement);
  }
}

// 3. 이슈 업데이트
await mcp__linear__update_issue({
  id: "issue-id",
  description: updatedDescription
});
```

**주의사항:**
- 체크박스 업데이트는 코멘트 작성 전에 수행
- 업데이트 성공 여부를 확인하고 로그 남기기
- 부분 매칭 주의: 항목 텍스트가 정확히 일치해야 함

### Step 9: Post Comment to Issue

검증 결과를 이슈 코멘트로 작성합니다.

```
mcp__linear__create_comment({
  issueId: "issue-uuid",
  body: "{validation_report_markdown}"
})
```

### Step 10: Move to "In Review" (Optional)

모든 항목이 통과한 경우, 사용자에게 상태 변경 여부를 확인합니다.

```
모든 DoD/AC 항목이 검증되었습니다! ✅

이슈를 "In Review" 상태로 이동하시겠습니까?
1. 예, 이동합니다
2. 아니오, 현재 상태 유지

선택:
```

**상태 변경:**
```
mcp__linear__update_issue({
  id: "issue-uuid",
  state: "In Review"
})
```

---

## Validation History Tracking

이전 검증 시도를 추적합니다.

**코멘트 파싱:**
- 기존 검증 코멘트 확인 (`🤖 Generated by Linear Issue Validator`)
- 이전 검증 결과와 현재 결과 비교
- 개선/악화된 항목 표시

**History Display:**
```markdown
## 검증 히스토리
| 시도 | 일시 | 결과 | 변화 |
|-----|------|------|------|
| 3 | 2025-01-09 14:30 | ✅ 8/8 | +2 (DoD#2, AC#1 통과) |
| 2 | 2025-01-08 16:00 | ⚠️ 6/8 | +1 (AC#3 통과) |
| 1 | 2025-01-07 10:00 | ⚠️ 5/8 | - |
```

---

## Re-validation Request

실패 항목에 대해 재검증을 요청합니다.

**자동 재검증 트리거:**
```
다음 항목들이 검증에 실패했습니다:

❌ DoD #2: 코드 리뷰 완료
   → PR #456이 아직 open 상태입니다.

❌ AC #1: API 응답 200ms 이하
   → 현재 평균 250ms (목표: 200ms)

수정 후 재검증하시겠습니까?
1. 예, 재검증 실행
2. 아니오, 나중에 재검증
3. 특정 항목만 재검증 (번호 입력)

선택:
```

---

## Error Handling

### Linear API Errors

```
Linear API 오류가 발생했습니다.
- 오류: {error_message}
- 이슈 ID: {issue_id}

해결 방법:
1. 이슈 ID가 올바른지 확인하세요
2. Linear 접근 권한을 확인하세요
3. 네트워크 연결을 확인하세요
```

### URL Access Errors

```
URL 접근에 실패했습니다.
- URL: {url}
- 오류: {status_code} {error}

이 URL은 수동 검증이 필요합니다.
스크린샷이나 텍스트로 결과를 첨부해주세요.
```

### Authentication Required

```
인증이 필요한 리소스입니다.
- 리소스: {url}
- 유형: {resource_type}

다음 중 하나를 선택해주세요:
1. 스크린샷 첨부
2. 텍스트로 결과 설명
3. 공개 접근 가능한 링크로 교체
```

---

## Configuration Options

사용자가 검증 옵션을 지정할 수 있습니다.

```
/linear-issue-validator NKIA-123 --strict
/linear-issue-validator NKIA-123 --skip-move
/linear-issue-validator NKIA-123 --dod-only
/linear-issue-validator NKIA-123 --ac-only
```

**Options:**
| 옵션 | 설명 |
|-----|------|
| `--strict` | 모든 항목 통과 필수 (부분 통과 불허) |
| `--skip-move` | 상태 변경 스킵 (검증만 수행) |
| `--dod-only` | DoD 항목만 검증 |
| `--ac-only` | AC 항목만 검증 |
| `--revalidate` | 이전에 통과한 항목도 재검증 |
| `--verbose` | 상세 검증 로그 출력 |

---

## Quick Reference

### Validation Status Icons

| 아이콘 | 의미 |
|-------|------|
| ✅ | 검증 통과 (Pass) |
| ❌ | 검증 실패 (Fail) |
| ⚠️ | 부분 통과 또는 수동 확인 필요 |
| 🔄 | 재검증 필요 |
| ⏳ | 검증 진행 중 |
| 🔒 | 접근 권한 필요 |

### Evidence Type Icons

| 아이콘 | 유형 |
|-------|------|
| 🔗 | URL/링크 |
| 📝 | 문서 |
| 🖼️ | 이미지 |
| 🔀 | PR/MR |
| ⚙️ | CI/CD |
| 📊 | 모니터링/메트릭 |
| 🌐 | API |
| 📁 | 데이터 경로 |
| 💬 | 텍스트 |

---

## Best Practices

### For Issue Creators (이슈 작성자)

1. **결과물을 구체적으로 명시**
   - ❌ `→ 결과물: 완료`
   - ✅ `→ 결과물: https://github.com/org/repo/pull/123`

2. **검증 가능한 형태로 제공**
   - 공개 접근 가능한 링크 우선
   - 내부 시스템은 스크린샷 함께 첨부

3. **메트릭은 수치와 함께**
   - ❌ `→ 결과물: 성능 개선됨`
   - ✅ `→ 결과물: 응답시간 150ms (이전 300ms → 개선율 50%)`

### For Validators (검증자)

1. **자동 검증 우선, 수동 검증 보조**
2. **실패 시 구체적인 원인과 해결책 제시**
3. **히스토리를 통해 진행상황 추적**

---

## Integration with Other Skills

### With `/linear-issue-creator`

이슈 생성 시 검증 가능한 DoD/AC 형식으로 자동 생성됩니다.

### With `/code-review`

PR 링크 검증 시 code-review 결과를 참조할 수 있습니다.

---

## Workflow Diagram

```
┌─────────────────┐
│  Issue Input    │
│  (ID or URL)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch Issue    │
│  Details        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parse DoD/AC   │
│  Items          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Classify       │
│  Evidence Types │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│         Validate Each Item          │
├─────────┬─────────┬─────────┬──────┤
│ PR/MR   │ CI/CD   │  URL    │ ...  │
│ Check   │ Check   │ Check   │      │
└────┬────┴────┬────┴────┬────┴──────┘
     │         │         │
     └─────────┴─────────┘
               │
               ▼
┌─────────────────┐
│  Generate       │
│  Report         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Update Issue   │
│  Checkboxes     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post Comment   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Move to        │
│  "In Review"?  │
└─────────────────┘
```

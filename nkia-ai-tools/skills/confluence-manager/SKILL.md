---
name: confluence-manager
description: NKIA-AI 스페이스 전용 Confluence 문서 관리 스킬. 문서 검색, 조회, 생성, 수정 기능을 제공합니다. 사용자가 Confluence 관련 작업을 요청할 때 이 스킬을 사용하세요.
---

# Confluence Manager

NKIA-AI Confluence 스페이스 전용 문서 관리 스킬입니다.

## Overview

이 스킬은 NKIA-AI 스페이스에서 Confluence 문서를 관리하는 모든 작업을 지원합니다:
- **검색**: 키워드로 문서 찾기
- **조회**: 문서 내용 보기
- **생성**: 새 문서 만들기
- **수정**: 기존 문서 수정, 댓글 추가

---

## 스페이스 정보 (하드코딩)

이 스킬은 NKIA-AI 스페이스 전용입니다. 모든 MCP 도구 호출 시 아래 값을 사용하세요:

```
cloudId: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
spaceId: 98313
spaceKey: NKIAAI
```

### 주요 폴더 구조 및 ID

| 폴더명 | ID | 용도 |
|--------|-----|------|
| Project | 65807 | 진행 중인 프로젝트 문서 |
| Area | 65808 | 업무 영역별 문서 (온보딩, 가이드 등) |
| Resource | 98638 | 참고 자료, 기술 문서 |
| Archive | 98639 | 완료/보관 문서 |

---

## 지원 기능

### 1. 문서 검색 (Search)

**사용자 요청 예시:**
- "RCA 관련 문서 찾아줘"
- "LLM 문서 검색해줘"
- "Resource 폴더에 있는 문서 목록 보여줘"

**MCP 도구:**
```
mcp__Atlassian__searchConfluenceUsingCql
```

**CQL 쿼리 패턴:**
```
# 키워드 검색
space = "NKIAAI" AND title ~ "{keyword}" AND type = page

# 특정 폴더 내 검색
space = "NKIAAI" AND ancestor = {folderId} AND type = page
```

**파라미터:**
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `cql`: CQL 쿼리 문자열

---

### 2. 문서 조회 (Read)

**사용자 요청 예시:**
- "MVP 기획문서 내용 보여줘"
- "페이지 ID 12345678 조회해줘"
- "이 문서의 하위 페이지 보여줘"

**MCP 도구:**

#### 페이지 내용 조회
```
mcp__Atlassian__getConfluencePage
```
**파라미터:**
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 페이지 ID

#### 하위 페이지 조회
```
mcp__Atlassian__getConfluencePageDescendants
```
**파라미터:**
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 상위 페이지 ID

#### 댓글 조회
```
mcp__Atlassian__getConfluencePageFooterComments
```
**파라미터:**
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 페이지 ID

---

### 3. 문서 생성 (Create)

**사용자 요청 예시:**
- "Resource 폴더에 새 문서 만들어줘"
- "Project > RCA Agent 하위에 문서 생성해줘"
- "설치 가이드 문서 작성해줘"

**MCP 도구:**
```
mcp__Atlassian__createConfluencePage
```

**파라미터:**
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `spaceId`: 98313
- `parentId`: 상위 폴더/페이지 ID (필수)
- `title`: 페이지 제목
- `body`: 페이지 내용 (Markdown 형식)

**폴더 ID 참조:**
- Project: 65807
- Area: 65808
- Resource: 98638
- Archive: 98639

---

### 4. 문서 수정 (Update)

**사용자 요청 예시:**
- "이 문서 내용 수정해줘"
- "페이지에 댓글 달아줘"
- "문서 업데이트해줘"

**MCP 도구:**

#### 페이지 수정
```
mcp__Atlassian__updateConfluencePage
```
**파라미터:**
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 수정할 페이지 ID
- `body`: 새 내용 (Markdown 형식)
- `title`: 새 제목 (선택)

#### 댓글 추가
```
mcp__Atlassian__createConfluenceFooterComment
```
**파라미터:**
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 페이지 ID
- `body`: 댓글 내용 (Markdown 형식)

---

## 워크플로우

### Step 1: 작업 유형 파악

사용자 요청에서 작업 유형을 파악합니다:

| 키워드 | 작업 유형 |
|--------|----------|
| 찾아줘, 검색, 목록 | 검색 |
| 보여줘, 내용, 읽어줘 | 조회 |
| 만들어줘, 작성, 생성 | 생성 |
| 수정, 업데이트, 댓글 | 수정 |

### Step 2: 작업 실행

#### 검색 흐름
1. 사용자로부터 검색 키워드 확인
2. CQL 쿼리 생성: `space = "NKIAAI" AND title ~ "{keyword}" AND type = page`
3. `mcp__Atlassian__searchConfluenceUsingCql` 실행
4. 결과를 테이블 형식으로 표시 (제목, URL, 최종수정일)

#### 조회 흐름
1. 페이지 ID 또는 제목으로 페이지 특정
2. `mcp__Atlassian__getConfluencePage` 실행
3. 내용을 Markdown 형식으로 표시
4. 필요시 하위 페이지/댓글 추가 조회

#### 생성 흐름
1. 상위 폴더 확인 (Project/Area/Resource/Archive)
2. 하위 폴더가 필요하면 `getConfluencePageDescendants`로 목록 조회
3. 제목과 내용 확인
4. `mcp__Atlassian__createConfluencePage` 실행
5. 생성된 페이지 URL 반환

#### 수정 흐름
1. 수정할 페이지 특정 (검색 또는 ID)
2. 현재 내용 조회하여 표시
3. 수정 내용 확인
4. `mcp__Atlassian__updateConfluencePage` 실행
5. 수정된 페이지 URL 반환

---

## 사용 예시

### 예시 1: 문서 검색
```
사용자: "RCA Agent 관련 문서 찾아줘"

실행:
mcp__Atlassian__searchConfluenceUsingCql(
  cloudId: "ed55cda3-43a9-4e60-ac24-d16a8f9aa88d",
  cql: "space = \"NKIAAI\" AND title ~ \"RCA Agent\" AND type = page"
)
```

### 예시 2: 문서 생성
```
사용자: "Resource 폴더에 'Claude Code 사용법' 문서 만들어줘"

실행:
mcp__Atlassian__createConfluencePage(
  cloudId: "ed55cda3-43a9-4e60-ac24-d16a8f9aa88d",
  spaceId: "98313",
  parentId: "98638",  # Resource 폴더
  title: "Claude Code 사용법",
  body: "# Claude Code 사용법\n\n..."
)
```

### 예시 3: 문서 조회
```
사용자: "MVP 기획문서 내용 보여줘"

1단계 - 검색:
mcp__Atlassian__searchConfluenceUsingCql(
  cloudId: "ed55cda3-43a9-4e60-ac24-d16a8f9aa88d",
  cql: "space = \"NKIAAI\" AND title ~ \"MVP 기획\" AND type = page"
)

2단계 - 조회:
mcp__Atlassian__getConfluencePage(
  cloudId: "ed55cda3-43a9-4e60-ac24-d16a8f9aa88d",
  pageId: "{검색된 페이지 ID}"
)
```

### 예시 4: 댓글 추가
```
사용자: "이 문서에 리뷰 완료 댓글 달아줘"

실행:
mcp__Atlassian__createConfluenceFooterComment(
  cloudId: "ed55cda3-43a9-4e60-ac24-d16a8f9aa88d",
  pageId: "{페이지 ID}",
  body: "리뷰 완료했습니다."
)
```

---

## 중요 가이드라인

1. **cloudId는 항상 고정**: `ed55cda3-43a9-4e60-ac24-d16a8f9aa88d`
2. **spaceId는 항상 고정**: `98313`
3. **문서 생성 시 parentId 필수**: 반드시 상위 폴더 ID를 지정해야 함
4. **내용은 Markdown 형식**: body 파라미터는 Markdown으로 작성
5. **검색 결과 표시**: 테이블 형식으로 제목, URL, 최종수정일 표시
6. **URL 항상 제공**: 생성/수정 후 결과 URL을 사용자에게 제공

# Confluence Operations

## 스페이스 정보 (하드코딩)

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

## 1. 문서 검색 (Search)

**MCP 도구:** `mcp__Atlassian__searchConfluenceUsingCql`

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

**예시:**
```
mcp__Atlassian__searchConfluenceUsingCql(
  cloudId: "ed55cda3-43a9-4e60-ac24-d16a8f9aa88d",
  cql: "space = \"NKIAAI\" AND title ~ \"RCA Agent\" AND type = page"
)
```

---

## 2. 문서 조회 (Read)

### 페이지 내용 조회
**MCP 도구:** `mcp__Atlassian__getConfluencePage`
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 페이지 ID

### 하위 페이지 조회
**MCP 도구:** `mcp__Atlassian__getConfluencePageDescendants`
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 상위 페이지 ID

### 댓글 조회
**MCP 도구:** `mcp__Atlassian__getConfluencePageFooterComments`
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 페이지 ID

---

## 3. 문서 생성 (Create)

**MCP 도구:** `mcp__Atlassian__createConfluencePage`

**파라미터:**
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `spaceId`: 98313
- `parentId`: 상위 폴더/페이지 ID (필수)
- `title`: 페이지 제목
- `body`: 페이지 내용 (Markdown 형식)

**예시:**
```
mcp__Atlassian__createConfluencePage(
  cloudId: "ed55cda3-43a9-4e60-ac24-d16a8f9aa88d",
  spaceId: "98313",
  parentId: "98638",  # Resource 폴더
  title: "Claude Code 사용법",
  body: "# Claude Code 사용법\n\n..."
)
```

---

## 4. 문서 수정 (Update)

### 페이지 수정
**MCP 도구:** `mcp__Atlassian__updateConfluencePage`
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 수정할 페이지 ID
- `body`: 새 내용 (Markdown 형식)
- `title`: 새 제목 (선택)

### 댓글 추가
**MCP 도구:** `mcp__Atlassian__createConfluenceFooterComment`
- `cloudId`: ed55cda3-43a9-4e60-ac24-d16a8f9aa88d
- `pageId`: 페이지 ID
- `body`: 댓글 내용 (Markdown 형식)

---

## 워크플로우 상세

### 검색 흐름
1. 사용자로부터 검색 키워드 확인
2. CQL 쿼리 생성
3. `mcp__Atlassian__searchConfluenceUsingCql` 실행
4. 결과를 테이블 형식으로 표시 (제목, URL, 최종수정일)

### 조회 흐름
1. 페이지 ID 또는 제목으로 페이지 특정
2. `mcp__Atlassian__getConfluencePage` 실행
3. 내용을 Markdown 형식으로 표시
4. 필요시 하위 페이지/댓글 추가 조회

### 생성 흐름
1. 상위 폴더 확인 (Project/Area/Resource/Archive)
2. 하위 폴더가 필요하면 `getConfluencePageDescendants`로 목록 조회
3. 제목과 내용 확인
4. `mcp__Atlassian__createConfluencePage` 실행
5. 생성된 페이지 URL 반환

### 수정 흐름
1. 수정할 페이지 특정 (검색 또는 ID)
2. 현재 내용 조회하여 표시
3. 수정 내용 확인
4. `mcp__Atlassian__updateConfluencePage` 실행
5. 수정된 페이지 URL 반환

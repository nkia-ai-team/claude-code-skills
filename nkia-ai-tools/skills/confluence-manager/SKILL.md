---
name: confluence-manager
description: NKIA-AI 스페이스 전용 Confluence 문서 관리 스킬. 문서 검색, 조회, 생성, 수정 기능을 제공합니다. 사용자가 Confluence 관련 작업을 요청할 때 이 스킬을 사용하세요.
---

# Confluence Manager

NKIA-AI Confluence 스페이스 전용 문서 관리 스킬입니다.

## Overview

- **검색**: 키워드로 문서 찾기
- **조회**: 문서 내용 보기
- **생성**: 새 문서 만들기
- **수정**: 기존 문서 수정, 댓글 추가

## Workflow

### Step 1: 작업 유형 파악

| 키워드 | 작업 유형 |
|--------|----------|
| 찾아줘, 검색, 목록 | 검색 |
| 보여줘, 내용, 읽어줘 | 조회 |
| 만들어줘, 작성, 생성 | 생성 |
| 수정, 업데이트, 댓글 | 수정 |

### Step 2: 작업 실행

작업 유형에 따라 적절한 MCP 도구를 호출합니다.

상세는 [confluence_operations.md](references/confluence_operations.md) 참조 — 스페이스 정보, 폴더 ID, MCP 도구 파라미터, CQL 쿼리 패턴, 작업 유형별 워크플로우

## Key Guidelines

1. **cloudId는 항상 고정**: `ed55cda3-43a9-4e60-ac24-d16a8f9aa88d`
2. **spaceId는 항상 고정**: `98313`
3. **문서 생성 시 parentId 필수**: 반드시 상위 폴더 ID를 지정
4. **내용은 Markdown 형식**: body 파라미터는 Markdown으로 작성
5. **검색 결과 표시**: 테이블 형식으로 제목, URL, 최종수정일 표시
6. **URL 항상 제공**: 생성/수정 후 결과 URL을 사용자에게 제공

---

## Resources

- [confluence_operations.md](references/confluence_operations.md) — 스페이스 정보, 폴더 구조/ID, 검색/조회/생성/수정 MCP 도구 파라미터, CQL 쿼리 패턴, 워크플로우 상세

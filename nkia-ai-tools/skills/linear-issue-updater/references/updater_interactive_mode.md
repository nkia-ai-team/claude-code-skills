# Interactive Mode Workflow

수동으로 DoD/AC 항목을 관리하는 기본 모드입니다.

---

## Step 1: Fetch Issue Details

`mcp__linear__get_issue`를 사용하여 현재 이슈 정보를 가져옵니다.

```
=== 이슈 정보 ===

제목: code-review 및 commit 스킬 Linear 이슈번호 형식 적용
상태: In Progress
담당자: 홍길동

--- 현재 Description ---
[현재 Description 전체 표시]
==================
```

## Step 2: Show Update Options

```
어떤 작업을 하시겠습니까?

1. DoD 항목 추가
2. DoD 항목 수정
3. DoD 항목 삭제
4. AC 항목 추가
5. AC 항목 수정
6. AC 항목 삭제
7. 배경/설명 수정
8. 전체 Description 직접 편집
9. 변경사항 확인 및 저장
0. 취소

선택:
```

---

## Operations

### Operation 1: DoD 항목 추가

```
=== DoD 항목 추가 ===

현재 DoD 항목:
1. [ ] code-review 스킬 브랜치명 검증 패턴 수정
2. [ ] commit 스킬 커밋 메시지 형식 수정

새로운 DoD 항목을 입력하세요:
(형식: [작업 내용] → 결과물: [증빙])

입력: 대용량 파일 처리 로직 추가 → 결과물: PR 링크 {{pr_link}}

우선순위 태그를 선택하세요:
1. 없음 (기본)
2. **[필수]**
3. **[공통]**
4. **[옵셔널]**

선택: 1

추가할 DoD 항목:
- [ ] 대용량 파일 처리 로직 추가 → 결과물: PR 링크 {{pr_link}}

추가하시겠습니까? (y/n)
```

**API 호출:**
```javascript
// 1. 현재 description 가져오기
const issue = await mcp__linear__get_issue({ id: "issue-id" });
let description = issue.description;

// 2. DoD 섹션 찾아서 항목 추가
const dodSection = "## Definition of Done (DoD)";
const newItem = "- [ ] 대용량 파일 처리 로직 추가 → 결과물: PR 링크 {{pr_link}}";

// DoD 섹션 끝에 항목 추가
description = insertAfterSection(description, dodSection, newItem);

// 3. 업데이트
await mcp__linear__update_issue({
  id: "issue-id",
  description: description
});
```

### Operation 2: DoD 항목 수정

```
=== DoD 항목 수정 ===

수정할 항목을 선택하세요:
1. [ ] code-review 스킬 브랜치명 검증 패턴 수정 → 결과물: PR 링크
2. [ ] commit 스킬 커밋 메시지 형식 수정 → 결과물: PR 링크

선택: 1

수정할 부분을 선택하세요:
1. 작업 내용 수정
2. 결과물 수정
3. 전체 수정
4. 체크 상태 변경 ([ ] ↔ [x])

선택:
```

### Operation 3: DoD 항목 삭제

```
=== DoD 항목 삭제 ===

삭제할 항목을 선택하세요:
[항목 목록]

⚠️ 다음 항목을 삭제합니다:
[선택된 항목]

삭제 사유를 입력하세요 (선택사항):
삭제하시겠습니까? (y/n)
```

### Operation 4-6: AC 항목 추가/수정/삭제

DoD와 동일한 방식으로 AC 섹션에 대해 수행합니다.

### Operation 7: 배경/설명 수정

```
=== 배경/설명 수정 ===

현재 배경:
[현재 내용]

수정할 내용을 입력하세요 (Markdown 지원):
```

### Operation 8: 전체 Description 직접 편집

```
=== 전체 Description 편집 ===

현재 Description이 표시됩니다.
수정된 Description을 입력하세요 (완료 시 빈 줄 2번 입력):
```

### Operation 9: 변경사항 확인 및 저장

```
=== 변경사항 미리보기 ===

📝 변경 내용:
[DoD/AC 변경 요약]

--- 변경 후 Description ---
[새로운 Description 전체 표시]
---

저장하시겠습니까?
1. 예, 저장하고 변경 코멘트 추가
2. 예, 저장만 (코멘트 없음)
3. 아니오, 계속 편집

선택:
```

# Evidence Parsing Logic

AC 항목 파싱, 체크 상태 변경, 증빙 첨부 로직을 정의합니다.

---

## 1. AC 항목 형식

### 기본 형식

    - [ ] [작업 내용] → 결과물: [증빙 자료]

### 우선순위 태그 (선택)

    - [ ] **[필수]** [작업 내용] → 결과물: [증빙]
    - [ ] **[공통]** [작업 내용] → 결과물: [증빙]
    - [ ] **[옵셔널]** [작업 내용] → 결과물: [증빙]

### 템플릿 변수 (미치환 상태)

    - [ ] 목표 데이터 {{record_count}}건 수집 → 결과물: {{data_path}}

증빙 첨부 시 `{{variable}}`을 실제 값으로 치환합니다.

---

## 2. Description Structure

### 현행 형식 (우선)

공통 템플릿 구조는 [guideline-ref.md "5.1 이슈 템플릿"](../../_shared/guideline-ref.md) 참조.

### Section Detection

| 섹션 | 현행 패턴 | 레거시 패턴 |
|-----|----------|-----------|
| AC | `## 3. 완료 조건`, `## 3.` | `## Acceptance Criteria`, `## AC`, `## 인수 조건` |
| DoD (레거시) | — | `## Definition of Done`, `## DoD`, `## 완료 정의` |

**파싱 우선순위:** 현행 번호 패턴(`## 3.`)을 먼저 탐색하고, 없으면 레거시 패턴으로 fallback.

### AC 섹션 탐색 순서

1. `## 3. 완료 조건 (Acceptance Criteria)` (현행)
2. `## 3. 완료 조건` (현행 축약)
3. `## Acceptance Criteria` (레거시)
4. `## AC` (레거시)
5. `## Definition of Done` (레거시 DoD — AC와 통합하여 파싱)

---

## 3. Parsing Logic

### AC 항목 파싱

    function parseChecklistItems(description, sectionHeader) {
      const sectionRegex = new RegExp(`${sectionHeader}[\\s\\S]*?(?=##|$)`, 'i');
      const sectionMatch = description.match(sectionRegex);
      if (!sectionMatch) return [];

      const itemRegex = /- \[([ x])\] (\*\*\[.+?\]\*\* )?(.+?)(?= → 결과물:| → |$)/g;
      const items = [];
      let match;
      while ((match = itemRegex.exec(sectionMatch[0])) !== null) {
        items.push({
          checked: match[1] === 'x',
          priority: match[2]?.replace(/\*\*/g, '').trim() || null,
          content: match[3].trim(),
          evidence: extractEvidence(match.input, match.index)
        });
      }
      return items;
    }

### 체크 상태 변경

    function checkItem(description, sectionHeader, itemIndex) {
      const items = parseChecklistItems(description, sectionHeader);
      if (itemIndex >= items.length) throw new Error('Invalid item index');

      const item = items[itemIndex];
      const oldPattern = `- [ ] ${formatItemContent(item)}`;
      const newPattern = `- [x] ${formatItemContent(item)}`;
      return description.replace(oldPattern, newPattern);
    }

### 증빙 첨부

    function attachEvidence(description, sectionHeader, itemIndex, evidence) {
      const items = parseChecklistItems(description, sectionHeader);
      if (itemIndex >= items.length) throw new Error('Invalid item index');

      const item = items[itemIndex];
      // 템플릿 변수({{var}})를 실제 증빙으로 치환
      // 또는 '결과물:' 뒤에 증빙 텍스트 삽입
      const oldEvidence = item.evidence || '{{placeholder}}';
      return description.replace(
        `→ 결과물: ${oldEvidence}`,
        `→ 결과물: ${evidence}`
      );
    }

---

## 4. Error Handling

### AC 섹션 없음

    ⚠️ AC 섹션을 찾을 수 없습니다.
    Description에 체크리스트 항목이 없습니다.

### 이미 체크된 항목

`AskUserQuestion`으로 확인:
- 질문: "항목 #2는 이미 완료 처리되어 있습니다. 어떻게 하시겠습니까?"
- 선택지: "증빙만 업데이트", "건너뛰기"
- 사용자는 "Other"로 다른 지시사항을 입력할 수 있음

### Conflict Detection

`AskUserQuestion`으로 확인:
- 질문: "이슈가 다른 곳에서 수정되었습니다. 어떻게 하시겠습니까?"
- 선택지: "최신 내용 다시 불러오기", "강제 저장 (다른 변경 덮어씀)"
- 사용자는 "Other"로 다른 지시사항을 입력할 수 있음

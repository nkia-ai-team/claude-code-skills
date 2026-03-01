# Updater Parsing Logic

Description 파싱, DoD/AC 항목 형식, 업데이트 로직을 정의합니다.

---

## 1. DoD/AC 항목 형식

### 기본 형식

```markdown
- [ ] [작업 내용] → 결과물: [증빙 자료]
```

### 우선순위 태그 (선택)

```markdown
- [ ] **[필수]** [작업 내용] → 결과물: [증빙]
- [ ] **[공통]** [작업 내용] → 결과물: [증빙]
- [ ] **[옵셔널]** [작업 내용] → 결과물: [증빙]
```

### 템플릿 변수 사용

```markdown
- [ ] 목표 데이터 {{record_count}}건 수집 → 결과물: {{data_path}}
- [ ] API 응답 시간 {{max_response_time}}ms 이하 → 결과물: {{perf_result}}
```

---

## 2. Description Structure

### Expected Format

```markdown
## 배경
[작업 배경 설명]

## 작업 설명
[상세 작업 내용]

## Definition of Done (DoD)
- [ ] **[필수]** [작업 내용 1] → 결과물: [증빙]
- [ ] **[공통]** [작업 내용 2] → 결과물: [증빙]
- [ ] [작업 내용 3] → 결과물: [증빙]

## Acceptance Criteria (AC)
- [ ] **[필수]** [품질 기준 1] → 결과물: [증빙]
- [ ] [품질 기준 2] → 결과물: [증빙]

## 참고사항
[추가 정보]
```

### Section Detection

| 섹션 | 인식 패턴 |
|-----|----------|
| 배경 | `## 배경`, `## Background` |
| 작업 설명 | `## 작업 설명`, `## Description`, `## 설명` |
| DoD | `## Definition of Done`, `## DoD`, `## 완료 정의` |
| AC | `## Acceptance Criteria`, `## AC`, `## 인수 조건` |
| 참고 | `## 참고사항`, `## Notes`, `## 참고` |

---

## 3. Parsing Logic

### DoD/AC 항목 파싱

```javascript
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
```

### 항목 업데이트

```javascript
function updateItem(description, sectionHeader, itemIndex, newContent) {
  const items = parseChecklistItems(description, sectionHeader);
  if (itemIndex >= items.length) throw new Error('Invalid item index');

  const oldItem = items[itemIndex];
  const newItemText = formatChecklistItem(newContent);
  return description.replace(formatChecklistItem(oldItem), newItemText);
}
```

---

## 4. Error Handling

### Parsing Errors

```
⚠️ Description 형식을 파싱할 수 없습니다.
DoD/AC 섹션이 없거나 형식이 다릅니다.
전체 편집 모드로 전환하시겠습니까? (y/n)
```

### Invalid Item Format

```
⚠️ 항목 형식이 올바르지 않습니다.
입력: 그냥 텍스트
권장 형식: [작업 내용] → 결과물: [증빙]
형식에 맞게 다시 입력해주세요:
```

### Conflict Detection

```
⚠️ 이슈가 다른 곳에서 수정되었습니다.

어떻게 하시겠습니까?
1. 최신 내용 다시 불러오기 (내 변경사항 유지)
2. 최신 내용으로 새로 시작
3. 강제 저장 (주의: 다른 변경 덮어씀)

선택:
```

---
name: linear-issue-creator
description: Create well-structured Linear issues with work-specific templates (Build/Deploy, Data, Evaluation, Feature Development, Feature Improvement, Refactoring, Research, Bug Fix). Supports both manual step-by-step input and automatic generation from meeting notes or natural language text with concrete DoD (Definition of Done) and AC (Acceptance Criteria). This skill should be used when users want to create a Linear issue for any type of work task.
---

# Linear Issue Creator

## Overview

Create well-structured Linear issues with appropriate work-specific templates, improved titles, automatic label application, and **concrete, measurable DoD/AC**.

**Two creation modes:**
1. **Manual Mode** — Step-by-step template-based input
2. **Auto Mode** — Automatic extraction from meeting notes or natural language text using LLM

## DoD vs AC

**Definition of Done (DoD):**
- Process completion evidence (프로세스 완료 증빙)
- Focus on "what was done"
- **Format**: `- [ ] **[필수/공통/옵셔널]** [작업 내용] → 결과물: [구체적 결과물]`

**Acceptance Criteria (AC):**
- Quality standards for deliverables (결과물 품질 기준)
- Focus on "how good it is"
- **Format**: `- [ ] **[필수/공통/옵셔널]** [품질 기준] → 결과물: [검증 가능한 결과물]`

**DoD/AC 생성 원칙:**
- **Keep it minimal**: DoD 2개 + AC 2개 = 총 4개 이내 권장
- **Be concrete and measurable**: 구체적 숫자, 메트릭, 링크 사용
- **Use template variables**: `{{variable_name}}` for context-specific values
- **Include evidence**: 검증에 필요한 증빙 명시 (링크, 리포트, 로그)

템플릿별 DoD/AC 예시는 [issue_templates.md "DoD/AC 생성 패턴"](references/issue_templates.md) 참조

---

## Work Templates and Issue Type Mapping

8 work templates are available, each automatically mapped to a Linear issue type:

| Work Template | Issue Type | Auto Labels |
|--------------|-----------|-------------|
| 1. 빌드/배포 | Task | "build" |
| 2. 데이터 작업 | Task | "task" |
| 3. 평가 | Task | "task" |
| 4. 새로운 기능 개발 | Feature | "feature" |
| 5. 기능 개선 | Feature | "improvement" |
| 6. 리팩토링 | Feature | "improvement" |
| 7. 리서치 | Research | "research" |
| 8. 버그 수정 | Bug | "bug" |

**Available Linear labels:** bug, build, feature, improvement, research, task

템플릿별 마크다운, 수집 정보, 제목 개선 가이드라인은 [issue_templates.md](references/issue_templates.md) 참조

---

## Workflow

### Auto Mode

```
/linear-issue-creator --auto
/linear-issue-creator --auto "회의록이나 자연어 텍스트"
```

Auto Mode 전체 워크플로우는 [creator_auto_mode.md](references/creator_auto_mode.md) 참조 — Steps 1-8: 자연어 추출, 구조화, 편집, 프로젝트/사이클 할당, 미리보기, 생성

### Manual Mode

```
/linear-issue-creator
```

Manual Mode 전체 워크플로우는 [creator_manual_mode.md](references/creator_manual_mode.md) 참조 — Steps 1-6: 기본 정보 수집, 제목 개선, 템플릿별 상세 + DoD/AC, 자동 할당, 미리보기, 생성

---

## Key Guidelines

### Title Improvement
Always suggest improved, clear titles:
- **Action-oriented** — Use verbs
- **Specific and concise** — Avoid vague terms
- **Clear scope and impact**

### Project Auto-Assignment
- Fetch active projects via `mcp__linear__list_projects`
- Match issue title/description keywords with project names
- Only assign on high confidence match — do not force assignment

### Cycle Auto-Assignment
- If `due_date` provided, match with `mcp__linear__list_cycles`
- Select cycle where `startsAt <= due_date < endsAt`

### Quick Process Principles
1. **Collect information in batches** — Present forms, not individual questions
2. **Mark optional fields clearly** — Use "(선택)" or "(선택사항)"
3. **Provide examples** — Show users how to respond with concrete DoD/AC examples
4. **Single final confirmation** — Confirm only once after collecting all information

---

## Resources

- [issue_templates.md](references/issue_templates.md) — 8개 작업 템플릿별 마크다운 템플릿, 수집 정보, DoD/AC 생성 패턴, 제목 개선 가이드라인, 이슈 타입/라벨 자동 매핑 규칙
- [creator_auto_mode.md](references/creator_auto_mode.md) — Auto Mode 전체 워크플로우 (자연어 추출, JSON 구조, 편집, 프로젝트/사이클 자동 할당, 미리보기, 생성), Pydantic 스키마 참조
- [creator_manual_mode.md](references/creator_manual_mode.md) — Manual Mode 전체 워크플로우 (기본 정보 수집, 제목 개선, 템플릿별 상세 정보 + DoD/AC, 자동 할당, 미리보기, 생성)

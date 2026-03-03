---
name: linear-issue-creator
description: Create well-structured Linear issues with work-specific templates (Build/Deploy, Data, Evaluation, Feature Development, Feature Improvement, Refactoring, Research, Bug Fix). Supports both manual step-by-step input and automatic generation from meeting notes or natural language text with concrete DoD (Definition of Done) and AC (Acceptance Criteria). This skill should be used when users want to create a Linear issue for any type of work task.
---

# Linear Issue Creator

## CRITICAL: First Step — Read the Guideline Reference

**BEFORE creating any issue, you MUST read:**
- [guideline-ref.md](../_shared/guideline-ref.md) — 이슈 상태, Estimate, 이슈 작성법, AC 검토 컨벤션, 이슈 템플릿, AI-Verification Loop

**이슈 생성 시 반드시 가이드라인의 규칙을 따라야 합니다.**

---

## Overview

Create well-structured Linear issues following the guideline's 6-section template, with improved titles, automatic label application, Estimate-based AC review workflow, and **concrete, measurable AC**.

**Two creation modes:**
1. **Manual Mode** — Step-by-step template-based input
2. **Auto Mode** — Automatic extraction from meeting notes or natural language text using LLM

---

## Issue Body Template

모든 이슈는 가이드라인의 6섹션 번호 구조를 따릅니다. 상세 템플릿은 [guideline-ref.md "이슈 템플릿"](../_shared/guideline-ref.md) 참조.

작업 유형별 섹션 내용 가이드와 AC 생성 패턴은 [issue_templates.md](references/issue_templates.md) 참조.

---

## Estimate & AC Review Workflow

Estimate 규칙과 AC 검토 컨벤션은 [guideline-ref.md "Estimate", "AC 검토"](../_shared/guideline-ref.md) 참조.

**스킬 동작:**
- Estimate 필드를 피보나치 스케일(1, 2, 3, 5, 8)로 입력받음 (13+ 시 하위 이슈 분해 권고)
- **Estimate 3+**: 이슈 생성 시 제목 끝에 `[AC 요청]` 자동 부착
- **Estimate 1~2**: 접미사 없이 생성

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

템플릿별 섹션 내용 가이드, AC 생성 패턴, 제목 개선 가이드라인은 [issue_templates.md](references/issue_templates.md) 참조

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

Manual Mode 전체 워크플로우는 [creator_manual_mode.md](references/creator_manual_mode.md) 참조 — Steps 1-6: 기본 정보 수집, 제목 개선, 템플릿별 상세 + AC, 자동 할당, 미리보기, 생성

---

## Key Guidelines

### Title Improvement
제목 공식: `[대상] + [행동] + [이유/효과]`
- **Bad**: 로그인 수정
- **Good**: 로그인: 비밀번호 재설정 메일 발송 실패 수정 (500 오류 해결)

### Acceptance Criteria
- DoD/AC를 분리하지 않고 **"완료 조건 (Acceptance Criteria)"** 단일 섹션으로 통합
- **Keep it minimal**: AC 3~5개 이내 권장
- **Be concrete and measurable**: 구체적 숫자, 메트릭, 링크 사용
- **Include evidence**: 검증에 필요한 증빙 명시
- **공통 AC**: 코드 변경 작업에는 `### 공통` 섹션에 코드 리뷰 항목 추가 (PR/MR은 이슈 리소스로 관리). 상세는 [issue_templates.md "공통 AC 항목"](references/issue_templates.md) 참조

### Project Auto-Assignment
- Fetch active projects via `mcp__linear__list_projects`
- Match issue title/description keywords with project names
- Only assign on high confidence match — do not force assignment

### Cycle Auto-Assignment & Mid-Cycle Guard
- If `due_date` provided, match with `mcp__linear__list_cycles`
- Select cycle where `startsAt <= due_date < endsAt`
- **사이클 중간 투입 경고**: 이미 시작된 사이클에 이슈를 할당하려는 경우, 사용자에게 다음을 안내:
  1. 사이클 중간 투입은 원칙적으로 금지 (기존 이슈 1개를 빼야 함 = Trade-off)
  2. Backlog 또는 다음 사이클에 배치를 권장
  3. 긴급한 경우에만 현재 사이클에 투입 (사유 기록 필요)

### Quick Process Principles
1. **Collect information in batches** — Present forms, not individual questions
2. **Mark optional fields clearly** — Use "(선택)" or "(선택사항)"
3. **Provide examples** — Show users how to respond with concrete AC examples
4. **Single final confirmation** — Confirm only once after collecting all information

---

## Resources

- [guideline-ref.md](../_shared/guideline-ref.md) — 가이드라인 핵심 규칙 (이슈 상태, Estimate, 이슈 작성법, AC 검토 컨벤션, 이슈 템플릿, AI-Verification Loop)
- [issue_templates.md](references/issue_templates.md) — 8개 작업 템플릿별 섹션 내용 가이드, AC 생성 패턴, 제목 개선 가이드라인, 이슈 타입/라벨 자동 매핑 규칙
- [creator_auto_mode.md](references/creator_auto_mode.md) — Auto Mode 전체 워크플로우 (자연어 추출, JSON 구조, 편집, 프로젝트/사이클 자동 할당, 미리보기, 생성), Pydantic 스키마 참조
- [creator_manual_mode.md](references/creator_manual_mode.md) — Manual Mode 전체 워크플로우 (기본 정보 수집, 제목 개선, 템플릿별 상세 정보 + AC, 자동 할당, 미리보기, 생성)

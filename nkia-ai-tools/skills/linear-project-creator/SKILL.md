---
name: linear-project-creator
description: Create comprehensive Linear projects with detailed documentation including project overview, goals, phases, tech stack, team composition, milestones, and success metrics. This skill should be used when users want to create a new Linear project or set up a major initiative in Linear.
---

# Linear Project Creator

## CRITICAL: First Step — Read the Guideline Reference

**BEFORE creating any project, you MUST read:**
- [guideline-ref.md](../_shared/guideline-ref.md) — **§0 운영 구조 (Project = 분기/일정 단위 실행 묶음, Feature > Task 를 담는 컨테이너)**, §5.2 프로젝트 템플릿, §9 Cycle 운영, 이슈 상태, Estimate

**프로젝트 생성 시 반드시 가이드라인의 규칙을 따라야 합니다.**

---

## Overview

가이드라인 v1.3 의 운영 구조에서 **Project 는 분기 또는 일정 단위의 실행 묶음**이며, Feature(=Linear Issue) 와 Task(=Sub-issue) 를 담는 최상위 컨테이너입니다. 이 스킬은 §5.2 프로젝트 템플릿에 맞춰 Linear Project 를 생성합니다:
- 목표 (Goal)
- 성공 기준 (Success Metrics)
- 주요 마일스톤 (Milestones)
- 리스크 및 대응 (Risks)

> 프로젝트 실행은 2주 단위 **Cycle** (§9) 로 운영됩니다. Cycle Planning 시 이 프로젝트의 Feature 중 일부가 해당 Cycle 대상으로 선택됩니다. 프로젝트 생성 단계에서는 Cycle 을 지정하지 않습니다 (Cycle 은 별도 운영).

## Workflow

### Step 1: Collect Basic Project Information

`mcp__linear__list_teams`로 팀 목록을 조회한 뒤, 기본 정보를 수집합니다:

1. **팀 이름** — Linear team selection
2. **프로젝트 이름**
3. **프로젝트 요약** — 한 줄 요약 (max 255 characters)
4. **프로젝트 설명** — 상세 설명
5. **프로젝트 목표** — 주요 목표
6. **우선순위** — No priority(0), Urgent(1), High(2), Medium(3), Low(4) (선택)
7. **프로젝트 리드** — 이름, 이메일, "me", 또는 비워두기 (선택)
8. **시작일** — YYYY-MM-DD (선택)
9. **목표일** — YYYY-MM-DD (선택)

### Step 2: Collect Detailed Project Information

수집 항목 구조는 [project_template.md "필수 수집 정보" / "선택 정보"](references/project_template.md) 참조

상세 정보 수집 항목: 목표, 성공 기준, 마일스톤, 리스크

### Step 3: Generate Project Description

프로젝트 description 마크다운 템플릿은 [guideline-ref.md "5.2 프로젝트 템플릿"](../_shared/guideline-ref.md) 참조
섹션별 가이드는 [project_template.md](references/project_template.md) 참조

수집된 정보로 프로젝트 템플릿에 맞춰 마크다운 description을 생성합니다.

### Step 4: Show Preview and Confirm

```
=== 생성될 프로젝트 미리보기 ===

프로젝트명: [프로젝트 이름]
팀: [팀]
요약: [프로젝트 요약]
우선순위: [우선순위]
프로젝트 리드: [리드]
시작일: [시작일]
목표일: [목표일]

--- 프로젝트 설명 ---
[생성될 마크다운 내용]
--------------

`AskUserQuestion`으로 확인:
- 질문: "이대로 생성하시겠습니까?"
- 선택지: "이대로 생성", "수정 후 생성"
- 사용자는 "Other"로 다른 지시사항을 입력할 수 있음
```

### Step 5: Create the Project

`mcp__linear__create_project` 호출:
- **name**, **team**, **summary**, **priority**, **lead** (선택), **startDate** (선택), **targetDate** (선택), **description**

### Step 6: Show Results and Suggest Next Steps

프로젝트 URL 표시 후 후속 작업 안내:

1. **Feature 등록** — `/linear-issue-creator` 로 Layer=Feature 이슈를 이 프로젝트에 등록 (마일스톤 단위로 Feature 백로그 구성)
2. **구글시트 백로그** — 각 Feature 의 간단 PRD 를 구글시트에 등록 (가이드라인 §0 작성 분리 원칙)
3. **Cycle Planning** — 등록된 Feature 중 첫 Cycle 대상을 스프린트 마스터가 선정 (§9.1)

---

## Date Handling

- YYYY-MM-DD 형식으로 입력받아 ISO 8601로 변환
- 시작일/목표일이 모두 있을 때 기간 자동 계산
- Phase별 마일스톤 날짜 제안

---

## Resources

- [guideline-ref.md](../_shared/guideline-ref.md) — 가이드라인 핵심 규칙 (프로젝트 템플릿, 이슈 상태, Estimate 등)
- [project_template.md](references/project_template.md) — 필수/선택 수집 정보, 우선순위 매핑, 섹션별 가이드

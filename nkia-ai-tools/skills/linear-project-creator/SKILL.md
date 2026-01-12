---
name: linear-project-creator
description: Create comprehensive Linear projects with detailed documentation including project overview, goals, phases, tech stack, team composition, milestones, and success metrics. This skill should be used when users want to create a new Linear project or set up a major initiative in Linear.
---

# Linear Project Creator

## Overview

Create comprehensive Linear projects with well-structured documentation that includes:
- Project overview and goals
- Phased implementation plans
- Tech stack details
- Team composition
- Timeline and milestones
- Success metrics
- Risk management

Efficiently collect project information and generate professional project documentation.

## Workflow Process

Follow this sequential process to create Linear projects:

### Step 1: Collect Basic Project Information

First, fetch available teams using `mcp__linear__list_teams`, then collect basic information sequentially:

Ask for the following in order:
1. **팀 이름** - Linear team selection (use `mcp__linear__list_teams`)
2. **프로젝트 이름** - Project name
3. **프로젝트 요약** - One-line summary (max 255 characters)
4. **프로젝트 설명** - Detailed project description
5. **프로젝트 목표** - Main goals to achieve
6. **우선순위** - No priority(0), Urgent(1), High(2), Medium(3), Low(4) (optional)
7. **프로젝트 리드** - Project leader name, email, "me", or leave empty (optional)
8. **시작일** - Project start date (YYYY-MM-DD format, optional)
9. **목표일** - Project target completion date (YYYY-MM-DD format, optional)

### Step 2: Collect Detailed Project Information

Request comprehensive project details in an organized format:

```
프로젝트 상세 정보를 입력해주세요:

1. 프로젝트 개요 (목적, 배경, 가치):

2. 프로젝트 목표 (구체적이고 측정 가능한 목표, 한 줄에 하나씩):
-
-
-

3. Phase 1 기능/작업 (초기 MVP, 한 줄에 하나씩):
-
-

4. Phase 2 기능/작업 (추가 기능, 한 줄에 하나씩):
-
-

5. Phase 3 기능/작업 (고급 기능, 한 줄에 하나씩, 선택):
-
-

6. 기술 스택:
   Backend:
   Frontend:
   Infrastructure:
   Tools:

7. 팀 구성 (선택):
   프로젝트 리드:
   개발자:
   디자이너:
   QA:

8. 성공 지표 (KPI/메트릭, 한 줄에 하나씩):
-
-
-

9. 위험 요소 및 대응 방안 (선택):
   위험 요소 | 영향도 | 대응 방안

10. 참고 자료 링크 (선택):
```

### Step 3: Generate Project Description

Using the template from `references/project_template.md`, generate a comprehensive markdown description following this structure:

```markdown
# {프로젝트 이름}

## 프로젝트 개요
{프로젝트 설명}

## 프로젝트 목표
1. 목표 1
2. 목표 2
3. 목표 3

## 주요 기능/범위

### Phase 1
- [ ] 기능/작업 1
- [ ] 기능/작업 2

### Phase 2
- [ ] 기능/작업 3
- [ ] 기능/작업 4

### Phase 3
- [ ] 기능/작업 5
- [ ] 기능/작업 6

## 기술 스택

**Backend:**
-

**Frontend:**
-

**Infrastructure:**
-

**Tools:**
-

## 팀 구성
- **프로젝트 리드**: {리드 이름}
- **개발자**:
- **디자이너**:
- **QA**:

## 일정
- **시작일**: {시작일}
- **목표 완료일**: {목표일}
- **예상 기간**: {기간 계산}

**마일스톤:**
- [ ] Phase 1 완료: {날짜}
- [ ] Phase 2 완료: {날짜}
- [ ] Phase 3 완료: {날짜}
- [ ] 최종 릴리즈: {날짜}

## 성공 지표
- 지표 1
- 지표 2
- 지표 3

## 위험 요소 및 대응 방안
| 위험 요소 | 영향도 | 대응 방안 |
|----------|--------|----------|
|          |        |          |

## 참고 자료
-
```

### Step 4: Show Preview and Confirm

Display the formatted project preview:

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

이대로 생성하시겠습니까? (y/n)
```

### Step 5: Create the Project

Use `mcp__linear__create_project` to create the project with the following parameters:

- **name**: 프로젝트 이름
- **team**: 팀 이름
- **summary**: 프로젝트 요약
- **priority**: 우선순위 숫자 (0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low)
- **lead**: 프로젝트 리드 (optional)
- **startDate**: 시작일 ISO 형식 (optional)
- **targetDate**: 목표일 ISO 형식 (optional)
- **description**: 생성된 마크다운 설명

### Step 6: Show Results and Suggest Next Steps

After successful project creation:

1. Display the project URL
2. Summarize project name and key information
3. Ask if user wants to create related issues

Example:
```
🎯 프로젝트가 생성되었습니다!
- 프로젝트명: 사용자 인증 시스템 개발
- 팀: Engineering
- 우선순위: High
- 목표일: 2025-12-31
- URL: https://linear.app/team/project/user-auth-system-abc123

다음으로 이 프로젝트에 필요한 이슈들을 생성하시겠어요?
```

## Project Creation Format

Use `mcp__linear__create_project` with the following parameters:

- **name**: 프로젝트 이름
- **team**: 팀 이름
- **summary**: 프로젝트 요약
- **priority**: 우선순위 숫자 (0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low)
- **lead**: 프로젝트 리드 (optional)
- **startDate**: 시작일 ISO 형식 (optional)
- **targetDate**: 목표일 ISO 형식 (optional)
- **description**: 생성된 마크다운 설명

## Priority Mapping

Map user-friendly priority names to Linear priority numbers:
- No priority → 0
- Urgent → 1
- High → 2
- Medium (or Normal) → 3
- Low → 4

## Date Handling

- Accept dates in YYYY-MM-DD format
- Convert to ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ) for the API
- Calculate project duration when both start and target dates are provided
- Suggest milestone dates based on phases and total duration

## Resources

### references/project_template.md

Contains the comprehensive project description template including:
- Full markdown structure for project documentation
- Required and optional information fields
- Guidance for each section (overview, goals, phases, tech stack, team, schedule, metrics, risks, references)
- Priority mapping reference
- Best practices for each template section

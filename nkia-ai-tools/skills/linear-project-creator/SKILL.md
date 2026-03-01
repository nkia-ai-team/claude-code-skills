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

상세 정보 수집 항목: 프로젝트 개요, 목표, Phase별 기능/작업, 기술 스택, 팀 구성, 성공 지표, 위험 요소, 참고 자료

### Step 3: Generate Project Description

마크다운 템플릿과 섹션별 가이드는 [project_template.md](references/project_template.md) 참조

수집된 정보로 마크다운 description을 생성합니다.

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

이대로 생성하시겠습니까? (y/n)
```

### Step 5: Create the Project

`mcp__linear__create_project` 호출:
- **name**, **team**, **summary**, **priority**, **lead** (선택), **startDate** (선택), **targetDate** (선택), **description**

### Step 6: Show Results and Suggest Next Steps

프로젝트 URL 표시 후 관련 이슈 생성 여부를 확인합니다.

---

## Date Handling

- YYYY-MM-DD 형식으로 입력받아 ISO 8601로 변환
- 시작일/목표일이 모두 있을 때 기간 자동 계산
- Phase별 마일스톤 날짜 제안

---

## Resources

- [project_template.md](references/project_template.md) — 프로젝트 설명 마크다운 템플릿, 필수/선택 수집 정보, 우선순위 매핑, 섹션별 가이드

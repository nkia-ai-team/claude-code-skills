---
name: linear-project-creator
description: Create comprehensive Linear projects with detailed documentation including project overview, goals, phases, tech stack, team composition, milestones, and success metrics. This skill should be used when users want to create a new Linear project or set up a major initiative in Linear.
---

# Linear Project Creator

## CRITICAL: First Step — Read the Guideline Reference

**BEFORE creating any project, you MUST read:**
- [guideline-ref.md](../_shared/guideline-ref.md) — **§0 제품·사업 Initiative > 기능·책임 범위 Project > 실행 Issue**, §5.2 프로젝트 템플릿, §9 Cycle 운영, 이슈 상태, 포인트 미사용

**프로젝트 생성 시 반드시 가이드라인의 규칙을 따라야 합니다.**

---

## Overview

프로젝트는 제품·사업 이니셔티브 안의 기능·책임 범위다. 분기·버전·목표 일정은 마일스톤으로 관리하고, 실제 실행 작업은 이슈로 관리한다. 동명 프로젝트를 이름·최근 수정일만으로 선택하지 않고 설명·이니셔티브·기존 자료를 확인한다. §5.2의 목표·성공 기준·마일스톤·리스크 양식을 사용한다.

Cycle은 실행 이슈의 2주 단위 계획이다. 프로젝트 생성 단계에서 Cycle을 임의 지정하지 않는다.

## Workflow

### Step 1: Collect Basic Project Information

`mcp__linear__list_teams`로 팀 목록을 조회한 뒤, 기본 정보를 수집합니다:

1. **팀 이름** — Linear team selection
2. **프로젝트 이름**
3. **프로젝트 요약** — 한 줄 요약 (max 255 characters)
4. **프로젝트 설명** — 상세 설명
5. **프로젝트 목표** — 주요 목표
6. **소속 이니셔티브** — 제품·사업 목적과 실제 ID 확인
7. **우선순위** — No priority(0), Urgent(1), High(2), Medium(3), Low(4) (선택)
8. **프로젝트 리드** — 이름, 이메일, "me", 또는 비워두기 (선택)
9. **시작일** — YYYY-MM-DD (선택)
10. **목표일** — YYYY-MM-DD (선택)

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

생성 후 현재 Linear 도구의 실제 이니셔티브 연결 기능으로 프로젝트를 연결한다. 재조회로 프로젝트 ID·소속·본문·리드를 확인한다. 연결 실패는 부분 완료로 보고하고 다른 프로젝트를 중복 생성하지 않는다.

### Step 6: Show Results and Suggest Next Steps

프로젝트 URL 표시 후 후속 작업 안내:

1. **실행 이슈 등록** — `/linear-issue-creator`로 4절 본문·Type 하나·프로젝트 하나를 지정하고 필요하면 부모·하위를 연결
2. **요약 공유** — 필요한 구글시트 요약은 `gws` CLI로 관리하고 상세 완료 조건·증빙은 Linear에 보존
3. **Cycle Planning** — 등록된 실행 이슈 중 첫 Cycle 대상을 스프린트 마스터가 선정 (§9.1)

---

## Date Handling

- YYYY-MM-DD 형식으로 입력받아 ISO 8601로 변환
- 시작일/목표일이 모두 있을 때 기간 자동 계산
- Phase별 마일스톤 날짜 제안

---

## Resources

- [guideline-ref.md](../_shared/guideline-ref.md) — 가이드라인 핵심 규칙 (프로젝트 템플릿, 이슈 상태, 포인트 미사용 등)
- [project_template.md](references/project_template.md) — 필수/선택 수집 정보, 우선순위 매핑, 섹션별 가이드

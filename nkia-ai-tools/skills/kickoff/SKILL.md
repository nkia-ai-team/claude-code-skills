---
name: kickoff
description: Start working on a Linear issue — read issue details, create a branch following repo conventions, transition to In Progress, and scaffold design docs if needed. Use this skill when starting development on a new issue.
---

# Kickoff — 작업 시작

## Overview

Linear 이슈를 읽어 브랜치를 생성하고, 개발 착수 준비를 자동화하는 스킬입니다.

**하는 일:**
- Linear 이슈 읽기 (title, description, labels, AC)
- 레포 유형에 따른 브랜치 자동 생성
- 이슈 상태 In Progress 전환
- 설계 AC 존재 시 설계 문서 scaffold 생성

**하지 않는 일:**
- 코드 구현 (사용자가 직접 또는 `/ralph-loop`으로)
- 커밋, PR 생성

---

## Usage

    /kickoff <issue-id>
    /kickoff NKIAAI-305

---

## Workflow

### Step 1: Parse & Fetch Issue

이슈 ID를 파싱하고 `mcp__plugin_linear_linear__get_issue`로 정보를 가져옵니다.

필요 필드: title, description, state, labels, estimate

### Step 2: Parse AC Items

Description에서 AC 항목을 파싱합니다.
- 설계 AC 존재 여부 확인 (키워드: "설계", "설계 문서", "design", "아키텍처")

### Step 3: Detect Repo Type & Create Branch

현재 작업 디렉토리의 레포 유형을 판별하여 적절한 브랜치를 생성합니다.

**사전 확인:** uncommitted 변경사항이 있으면 브랜치 생성 전에 사용자에게 안내합니다.

    git status --porcelain

변경사항이 있으면:

    현재 브랜치에 커밋되지 않은 변경사항이 있습니다.
    먼저 커밋하거나 stash한 후 다시 시도해주세요.

    $ git stash       # 임시 저장
    $ git add . && git commit  # 커밋

레포 판별, 브랜치 네이밍 규칙, label 매핑은 [kickoff_workflow.md](references/kickoff_workflow.md) 참조

### Step 4: Transition Issue Status

현재 상태가 Backlog/Todo이면 In Progress로 전환합니다.

    mcp__plugin_linear_linear__save_issue({ id: "issue-uuid", stateId: "in-progress-state-id" })

상태 ID 조회: `mcp__plugin_linear_linear__list_issue_statuses`로 팀의 상태 목록을 가져와서 "In Progress" 상태 ID를 확인합니다.

### Step 5: Design Scaffold (조건부)

AC에 설계 관련 항목이 있으면 설계 문서 초안을 생성합니다.

**트리거 키워드:** "설계", "설계 문서", "design", "아키텍처", "architecture"

**생성 위치:** 프로젝트의 문서 관례에 따름 (doc/, docs/ 등)

설계 문서가 생성되면 사용자에게 안내하고, 사용자와 대화하며 설계를 진행합니다.

### Step 6: Show Summary

    === NKIAAI-305 작업 시작 ===

    제목: Chat AI: streaming 구조 리팩토링 (WriterEmitterAdapter 전환)
    상태: Todo → In Progress
    브랜치: refactor/nkiaai-305-streaming-writer-emitter-adapter

    AC 항목 (3개):
    1. [ ] StreamEventEmitter 제거, WriterEmitterAdapter 전환 → 결과물: 코드 변경
    2. [ ] 기존 스트리밍 동작 유지 확인 → 결과물: 테스트 결과
    3. [ ] 코드 리뷰 완료 → 결과물: PR/MR 링크

    설계 AC 없음 → 바로 개발 진행 가능

    ===========================

---

## Resources

- [kickoff_workflow.md](references/kickoff_workflow.md) — 레포 유형 판별, 브랜치 생성 규칙 (일반/UI), label→prefix 매핑, function 추론 규칙

---
name: linear-issue-evidence
description: Update evidence on Linear issue AC items — check completed items and attach proof artifacts (PR links, screenshots, test results, etc.). Use this skill after completing development work, before running the validator.
---

# Linear Issue Evidence

## CRITICAL: First Step — Read the Guideline Reference

**BEFORE updating any evidence, you MUST read:**
- [guideline-ref.md](../_shared/guideline-ref.md) — 이슈 상태, AC 항목 형식, AI-Verification Loop

**증빙 업데이트 시 반드시 가이드라인의 AC 형식을 따라야 합니다.**

---

## Overview

완료된 작업에 대해 AC 항목의 체크박스를 체크하고 증빙 자료를 첨부하는 스킬입니다.

**하는 일:**
- AC 항목 체크 (`[ ]` → `[x]`)
- 증빙 자료 첨부 (`→ 결과물:` 뒤에 실제 링크/경로 삽입)

**하지 않는 일:**
- AC 항목 추가/삭제/수정 (내용 변경은 Claude가 직접 처리)
- 이슈 배경/설명/범위 수정

---

## Usage

    /linear-issue-evidence <issue-id>
    /linear-issue-evidence NKIAAI-137

---

## Workflow

### Step 1: Parse Issue Input

이슈 ID 또는 URL을 파싱합니다. (`NKIAAI-137`, Full URL, UUID 지원)

### Step 2: Fetch Issue Details

`mcp__linear__get_issue`로 이슈 정보를 가져옵니다. (title, description, state)

### Step 3: Parse AC Items

Description에서 AC 항목을 파싱합니다.

파싱 로직은 [evidence_parsing_logic.md](references/evidence_parsing_logic.md) 참조 — 현행 형식 + 레거시 형식 모두 지원

### Step 4: Show Current AC Status

현재 AC 항목의 체크 상태와 증빙 현황을 표시합니다.

    === NKIAAI-137 AC 현황 ===

    제목: code-review 스킬 브랜치명 검증 패턴 수정
    상태: In Progress

    AC 항목:
    1. [ ] 브랜치명 검증 패턴 수정 → 결과물: (미첨부)
    2. [ ] 테스트 작성 및 통과 → 결과물: (미첨부)
    3. [x] 코드 리뷰 완료 → 결과물: PR #42

    진행률: 1/3 (33%)

    ===========================

### Step 5: Collect Evidence

`AskUserQuestion` (multiSelect)으로 완료된 항목을 선택받습니다. 미완료 항목만 선택지로 표시합니다.

- 선택지: 미완료 AC 항목들 (예: "브랜치명 검증 패턴 수정", "테스트 작성 및 통과")
- 사용자는 "Other"로 다른 지시사항을 입력할 수 있음

항목 선택 후 각 항목에 대해 `AskUserQuestion`으로 증빙 자료를 입력받습니다.

- 선택지: 증빙 유형별 예시 (예: "PR 링크", "스크린샷 경로", "테스트 결과")
- 사용자는 "Other"로 직접 증빙 값을 입력할 수 있음

### Step 6: Preview and Confirm

변경 전/후를 비교하여 미리보기를 표시합니다.

    === 변경 미리보기 ===

    1. [x] 브랜치명 검증 패턴 수정 → 결과물: PR https://github.com/org/repo/pull/43  ← UPDATED
    2. [x] 테스트 작성 및 통과 → 결과물: CI 로그 https://ci.example.com/build/123  ← UPDATED
    3. [x] 코드 리뷰 완료 → 결과물: PR #42

    진행률: 3/3 (100%)

    ====================

`AskUserQuestion`으로 확인:
- 선택지: "적용", "수정 후 적용"
- 사용자는 "Other"로 다른 지시사항을 입력할 수 있음

### Step 7: Apply Changes

`mcp__linear__save_issue`로 description 업데이트

### Step 8: Manual Upload Guide

증빙 중 로컬 파일(스크린샷, 동영상 등)이 포함된 경우, 적용 완료 후 사용자에게 안내합니다.

    === 수동 업로드 필요 ===

    다음 파일은 Linear에 직접 업로드해주세요:

    1. 📷 스크린샷: temp/playwright-mcp/nkiaai-137/result.png
       → AC #2 "테스트 작성 및 통과" 증빙

    업로드 방법: Linear 이슈 → 코멘트 또는 첨부파일로 드래그 앤 드롭

    ===========================

**판단 기준:** 증빙 값이 URL(`http://`, `https://`)이 아닌 로컬 파일 경로이면 수동 업로드 대상으로 분류합니다.

---

## Evidence Types

증빙 유형별 가이드:

| 증빙 유형 | 형식 | 예시 | 수동 업로드 |
|----------|------|------|-----------|
| PR/MR 링크 | URL | `https://github.com/org/repo/pull/42` | - |
| CI/CD 로그 | URL | `https://ci.example.com/build/123` | - |
| 스크린샷 | 파일 경로 | `temp/playwright-mcp/nkiaai-137/result.png` | **필요** |
| 동영상 | 파일 경로 | `temp/playwright-mcp/nkiaai-137/demo.mp4` | **필요** |
| 테스트 결과 | 텍스트 또는 URL | `pytest 32/32 passed` | - |
| 문서 링크 | URL | `https://confluence.example.com/page/123` | - |
| 데이터 경로 | 파일 경로 | `/data/output/result.csv (1,024건)` | - |
| 메트릭 결과 | 텍스트 | `Accuracy: 95.2% (목표: 90%)` | - |

---

## Integration with Other Skills

| 스킬 | 연동 |
|-----|------|
| `/linear-issue-creator` | 이슈 생성 시 AC에 `→ 결과물:` 플레이스홀더 포함 |
| `/linear-issue-validator` | 증빙 첨부 후 별도 세션에서 객관적 검증 |

---

## Resources

- [guideline-ref.md](../_shared/guideline-ref.md) — 가이드라인 핵심 규칙 (AC 항목 형식, AI-Verification Loop)
- [evidence_parsing_logic.md](references/evidence_parsing_logic.md) — AC 파싱 로직, Section Detection, 체크/증빙 업데이트 로직

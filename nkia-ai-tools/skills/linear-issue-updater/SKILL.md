---
name: linear-issue-updater
description: Update Linear issue descriptions by adding, modifying, or removing DoD (Definition of Done) and AC (Acceptance Criteria) items. Use this skill when work scope changes during development, new requirements emerge, or existing criteria need modification.
---

# Linear Issue Updater

## Overview

진행 중인 Linear 이슈의 작업 내용과 DoD/AC를 업데이트하는 스킬입니다. 작업 범위 변경, 추가 요구사항, 기존 항목 수정 등을 지원합니다.

**주요 기능:**
1. DoD 항목 추가/수정/삭제
2. AC 항목 추가/수정/삭제
3. 작업 배경/설명 업데이트
4. 변경 이력 코멘트 자동 생성

## Usage

### Interactive Mode (기본)

```
/linear-issue-updater <issue-id>
```

### Quick Add Mode

```
/linear-issue-updater <issue-id> --add-dod "새로운 DoD 항목"
/linear-issue-updater <issue-id> --add-ac "새로운 AC 항목"
```

### Auto Mode (자연어 기반)

```
/linear-issue-updater <issue-id> --auto
/linear-issue-updater NKIAAI-137 --auto "GitLab MR에서 대용량 파일을 읽지 못하는 문제가 있어서 별도로 전체 파일을 조회하는 로직이 필요해"
```

**Options:**

| 옵션 | 설명 | 예시 |
|-----|------|------|
| `--add-dod` | DoD 항목 추가 | `--add-dod "작업 내용"` |
| `--add-ac` | AC 항목 추가 | `--add-ac "품질 기준"` |
| `--auto` | 자연어 기반 Auto Mode | `--auto "추가 작업 설명"` |
| `--apply` | Auto Mode에서 확인 없이 적용 | `--auto "..." --apply` |
| `--no-comment` | 변경 코멘트 생략 | `--no-comment` |
| `--reason` | 변경 사유 지정 | `--reason "요구사항 변경"` |

---

## Workflow

### Step 1: Parse Issue Input

이슈 ID 또는 URL을 파싱합니다. (`NKIAAI-137`, Full URL, UUID 지원)

### Step 2: Fetch Issue Details

`mcp__linear__get_issue`로 이슈 정보를 가져옵니다. (title, description, state, assignee)

### Step 3: Parse Current DoD/AC

Description에서 DoD/AC 항목을 파싱합니다.

DoD/AC 항목 형식, description 구조, 파싱 로직, 에러 처리는 [updater_parsing_logic.md](references/updater_parsing_logic.md) 참조

### Step 4: Execute Update (모드별 분기)

#### Interactive Mode

사용자에게 작업 옵션을 보여주고 수동으로 항목을 관리합니다. (추가/수정/삭제/배경 수정/전체 편집)

Interactive Mode 전체 워크플로우는 [updater_interactive_mode.md](references/updater_interactive_mode.md) 참조 — Steps 1-9, Operations 1-9

#### Auto Mode

자연어로 추가 작업을 설명하면 자동으로 DoD/AC 업데이트를 추천합니다.

Auto Mode 전체 워크플로우는 [updater_auto_mode.md](references/updater_auto_mode.md) 참조 — Steps 1-8, 분석 가이드라인, 변경 코멘트 템플릿

#### Quick Add Mode

`--add-dod` 또는 `--add-ac` 옵션으로 즉시 항목을 추가합니다.

1. 현재 description 가져오기
2. DoD/AC 섹션 끝에 새 항목 삽입
3. `mcp__linear__save_issue`로 업데이트
4. 변경 코멘트 생성 (`--no-comment` 미지정 시)

### Step 5: Preview and Confirm

변경 전/후 Description을 비교하여 미리보기를 표시하고 사용자 확인을 받습니다.

### Step 6: Apply Changes

1. `mcp__linear__save_issue`로 description 업데이트
2. 변경 코멘트 자동 생성 (`--no-comment` 미지정 시)

변경 코멘트 형식은 [updater_auto_mode.md "Change Comment Template"](references/updater_auto_mode.md) 참조

---

## Integration with Other Skills

| 스킬 | 연동 |
|-----|------|
| `/linear-issue-creator` | 이슈 생성 후 작업 중 변경사항 반영 |
| `/linear-issue-validator` | 검증 실패 항목 수정 후 재검증 |

---

## Resources

- [updater_auto_mode.md](references/updater_auto_mode.md) — Auto Mode 전체 워크플로우 (자연어 분석, 추천, 선택적 적용, 미리보기, 적용), 분석 가이드라인, 변경 코멘트 템플릿
- [updater_interactive_mode.md](references/updater_interactive_mode.md) — Interactive Mode 전체 워크플로우 (이슈 조회, 옵션 선택, Operations 1-9: DoD/AC 추가/수정/삭제, 배경 수정, 전체 편집, 저장)
- [updater_parsing_logic.md](references/updater_parsing_logic.md) — DoD/AC 항목 형식, Description 구조, Section Detection, 파싱 로직, 에러 처리 (파싱 오류, 형식 오류, 충돌 감지)

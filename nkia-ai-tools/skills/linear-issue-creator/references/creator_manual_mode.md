# Manual Mode Workflow

템플릿 기반으로 정보를 단계별로 수집하여 이슈를 생성합니다.

---

## Step 1: Collect Basic Information at Once

먼저 `mcp__linear__list_teams`로 팀 목록을 조회한 뒤, 모든 기본 정보를 한 번에 수집합니다.

```
Linear 이슈를 생성하겠습니다. 다음 정보를 입력해주세요:

1. Issue Layer (v1.3):
   1) Feature  — 사용자가 체감하는 기능 (Linear Issue, body = §5.1.a)
   2) Task     — Feature 하위 세부 작업 (Linear Sub-issue, body = §5.1.b, parent 필수)
   3) Standalone — 위계에 안 들어가는 단발성 이슈 (body = §5.1 공통 6섹션)

   (작업 템플릿이 "새로운 기능 개발/기능 개선/리팩토링" 이면 Feature 기본,
    parent Feature 지정 시 Task 로 전환됩니다.)

2. 작업 템플릿:
   1) 빌드/배포
   2) 데이터 작업
   3) 평가
   4) 새로운 기능 개발
   5) 기능 개선
   6) 리팩토링
   7) 리서치
   8) 버그 수정
   9) 문서 작업

3. 팀 이름: (사용 가능한 팀: [팀 목록])
4. 프로젝트 이름: (선택사항, 없으면 엔터)
5. 이슈 제목:
6. 우선순위: (Urgent/High/Normal/Low, 선택사항)
7. 담당자: (이름/이메일/'me', 선택사항)
8. 마감일: (YYYY-MM-DD, 선택사항)
9. Parent Feature 이슈 (Layer=Task 일 때 필수): NKIAAI-### 또는 이슈 URL
```

### Step 1.5: Validate Layer & Parent

- **Layer=Task** 인데 parent 미입력 → 사용자에게 parent Feature 를 묻거나, 적합한 Feature 가 없으면 Layer 를 Feature/Standalone 으로 재선택 안내.
- **Layer=Feature** 인데 parent 가 지정됨 → parent 가 Project (not Issue) 인지 확인. Issue 가 parent 라면 Task 로 재분류 제안.
- **Layer=Standalone** 에 parent 입력됨 → parent 무시하고 진행 (안내 메시지).

## Step 2: Suggest Improved Title

사용자 입력 제목을 분석하여 개선된 제목을 제안합니다.

**Good title characteristics:**
- **Action-oriented** (uses verbs)
- **Specific and concise** (avoid vague terms)
- **Clear scope and impact**

사용자에게 묻지 않고 개선된 제목을 바로 적용합니다.

## Step 3: Collect Template-Specific Details with DoD/AC

선택된 작업 템플릿에 맞는 상세 정보와 DoD/AC를 수집합니다.

**본문 구조는 Step 1 의 Layer 에 따라 분기합니다:**

| Layer | 수집 항목 |
|-------|---------|
| Feature | 목적, 주요 내용, 범위(포함/제외), **상세 완료 조건** (AC 3~5개), 하위 Task 목록(선택) |
| Task | 작업 내용, **간단 완료 조건** (한 줄씩, 보통 1~3개) |
| Standalone | 6섹션 (배경, 목표, AC, 범위, 검증, 참고) — 작업 템플릿별 가이드 적용 |

> Task 본문에는 Feature 의 상세 완료 조건 전체를 복사하지 않습니다. 해당 작업 자체의 완료 여부만 간단히 체크하세요 (guideline-ref.md §5.1.b).

**See `references/issue_templates.md` for template-specific markdown templates and collection fields.**

**수집 형식 예시 (데이터 작업):**
```
데이터 작업 상세 정보를 입력해주세요:

1. 배경 (왜 필요?):
2. 작업 설명 (어떤 데이터? 목표 품질은?):

3. 완료 조건 (AC) - 3~5개 권장:
   예시:
   - [ ] 데이터 파이프라인 실행 완료 → 결과물: 저장 경로 {{storage_path}}
   - [ ] 목표 데이터 {{record_count}}건 이상 수집 → 결과물: 데이터 경로 {{data_path}}
   - [ ] 품질 기준 충족 (Null < {{null_threshold}}%) → 결과물: 품질 리포트 {{quality_report}}

입력:
- [ ]
- [ ]
- [ ]

4. 범위 (선택, 포함/제외):
5. 검증 방법 (선택):
6. 참고사항 (선택, 데이터 소스/포맷/저장 위치):
```

## Step 4: Apply Issue Type and Labels Automatically

템플릿 기반 자동 매핑:
1. Linear 이슈 타입 결정 (Task/Feature/Research/Bug)
2. 템플릿별 라벨 적용 (Capitalize 정확히 일치 — Linear 라벨은 case-sensitive)
3. 내용 기반 추가 도메인 라벨

**⚠️ 라벨 검증 (필수):** `mcp__linear__list_issue_labels(team)` 로 워크스페이스 라벨을 먼저 조회하고, 매핑된 라벨이 실제로 존재하는지 확인. 없으면 폴백 적용 (`Refactor` → `Improvement`, `Document` → `Task`, `Data` → `Task`, `Infra` → 스킵). 모든 폴백도 부재 시 라벨 없이 생성 + 사용자 안내.

**See `references/issue_templates.md` Section "작업 템플릿 → 이슈 타입 자동 매핑", "라벨 체계", and "생성 직전 라벨 검증".**

## Step 4.5: Auto-assign Project Based on Content

1. `mcp__linear__list_projects`로 팀의 활성 프로젝트 조회
2. 이슈 제목/설명 키워드와 프로젝트 이름 매칭
3. 높은 신뢰도 매칭 시만 할당 (강제 할당 금지)

## Step 4.6: Auto-assign Cycle Based on Due Date

`due_date` 제공 시:
1. `mcp__linear__list_cycles`로 사이클 조회
2. `startsAt <= due_date < endsAt`인 사이클 선택

## Step 5: Show Preview and Confirm

```
=== 생성될 이슈 미리보기 ===

Layer: [Feature / Task / Standalone]
Parent: [Feature 이슈 ID + 제목] (Layer=Task 일 때만)
제목: [개선된 제목]
타입: [자동 매핑된 이슈 타입]
팀: [팀]
프로젝트: [프로젝트명] (자동 매칭됨) 또는 (없음)
우선순위: [우선순위]
담당자: [담당자]
마감일: [마감일]
사이클: [자동 배정된 사이클]
라벨: [자동 선택된 라벨들]

--- 설명 ---
[Layer 에 맞는 본문 마크다운]
--------------

미리보기 확인 없이 바로 생성합니다. 수정이 필요하면 Linear에서 직접 수정합니다.
```

## Step 6: Create the Issue

`mcp__linear__create_issue`로 이슈 생성:
- Auto-assigned project ID
- Auto-assigned cycle ID
- Template-based labels
- **Layer=Task 인 경우 `parentId` 필드에 Step 1 의 parent Feature 이슈 ID 지정 → Linear Sub-issue 로 생성됨**

결과 URL 표시. Layer=Feature 생성 후 하위 Task 목록이 본문에 있으면, 사용자에게 "하위 Task 들도 같은 흐름으로 이어서 생성할까요?" 안내.

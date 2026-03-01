# Project Update Rendering

수집된 데이터를 주간 프로젝트 업데이트 본문으로 렌더링하는 로직을 정의합니다.

---

## 1. 템플릿 참조

본문 구조는 [guideline-ref.md "5.3 주간 Project Update 템플릿"](../../_shared/guideline-ref.md) 참조.

---

## 2. "이번 주 성과" 렌더링

### 2.1 이전 계획 대비 (이전 업데이트가 있는 경우)

    ### 이번 주 성과

    **지난주 계획 대비:**
    - [x] {{matched_plan_item}} — {{matched_done_issue.identifier}} {{matched_done_issue.title}} (Done)
    - [ ] {{unmatched_plan_item}} — 미완료

    **추가 성과:**
    - {{unmatched_done_issue.identifier}} {{unmatched_done_issue.title}} (Done)
    - {{in_progress_issue.identifier}} {{in_progress_issue.title}} (In Progress — AC {{checked}}/{{total}})

    **이번 주 활동 요약:**
    - 완료: {{done_issues.length}}건
    - 진행 중: {{in_progress_issues.length}}건
    - 신규 등록: {{new_issues.length}}건
    - 기타 업데이트: {{updated_issues.length}}건

### 2.2 이전 업데이트 없는 경우 (첫 번째 업데이트)

    ### 이번 주 성과
    - {{done_issue.identifier}} {{done_issue.title}} (Done)
    - {{in_progress_issue.identifier}} {{in_progress_issue.title}} (In Progress — 착수)
    - 신규 이슈 {{new_issues.length}}건 등록

    **이번 주 활동 요약:**
    - 완료: {{done_issues.length}}건
    - 진행 중: {{in_progress_issues.length}}건
    - 신규 등록: {{new_issues.length}}건

---

## 3. "다음 주 계획" 렌더링

**자동 생성합니다 (사용자 입력 없음).**

현재 In Progress 이슈와 Todo 이슈를 기반으로 다음 주 계획을 자동 구성합니다:

    ### 다음 주 계획
    {{#each in_progress_issues}}
    - {{identifier}} {{title}} (계속 진행)
    {{/each}}
    {{#each todo_issues_top3}}
    - {{identifier}} {{title}} (착수 예정)
    {{/each}}

---

## 4. "리스크 & 지원 요청" 렌더링

**자동 생성합니다 (사용자 입력 없음).**

다음 소스에서 리스크를 자동 수집합니다:

### 4.1 In Progress 장기 체류 이슈

stale_in_progress 이슈가 있으면 자동으로 리스크에 포함:

    - **In Progress 장기 체류:** {{stale_issue.identifier}} {{stale_issue.title}} ({{days_stale}}일째 In Progress)

### 4.2 이슈 코멘트에서 문제 감지

각 In Progress 이슈의 최신 코멘트를 확인하여, 문제/블로커/장애 관련 내용이 있으면 리스크에 포함:

    - **{{issue.identifier}}:** {{코멘트 요약}}

코멘트에서 다음 키워드를 탐지합니다: 블로커, blocker, 장애, 지연, delay, 의존성, dependency, 리스크, risk

### 4.3 리스크 없는 경우

위 소스에서 리스크가 감지되지 않으면:

    ### 리스크 & 지원 요청
    - 없음

---

## 5. 최종 본문 조립

Health + "이번 주 성과" + "다음 주 계획" + "리스크 & 지원 요청"을 5.3 템플릿 형식으로 조립합니다.

    ## 상태: {{healthDisplay}}

    ### 이번 주 성과
    {{achievements_content}}

    ### 다음 주 계획
    {{next_week_content}}

    ### 리스크 & 지원 요청
    {{risks_content}}

**healthDisplay 매핑:**

| API 값 | 표시 |
|--------|------|
| onTrack | On Track |
| atRisk | At Risk |
| offTrack | Off Track |

---

## 6. 기존 업데이트 처리

같은 주에 이미 업데이트가 존재하는 경우를 감지합니다.

**감지 방법:**
`get_status_updates`로 가져온 최신 업데이트의 `createdAt`이 이번 주 범위 내인지 확인합니다.

**존재하는 경우:**

`AskUserQuestion`:
- 질문: "이번 주({{weekStart}} ~ {{weekEnd}}) 업데이트가 이미 존재합니다. 어떻게 하시겠습니까?"
- 선택지: "기존 업데이트 수정", "새 업데이트 생성", "취소"
- 사용자는 "Other"로 다른 지시사항을 입력할 수 있음

**기존 업데이트 수정 시:** `mcp__linear__save_status_update`에 `id: existingUpdateId`를 포함하여 업데이트

---

## 7. Error Handling

### 렌더링 실패

데이터가 비정상적인 경우 원시 데이터를 표시하고 사용자에게 직접 편집을 요청합니다.

### 저장 실패

자동으로 최대 2회 재시도합니다. 3회 실패 시 렌더링된 본문을 콘솔에 출력하고 사용자에게 수동 복사를 안내합니다.

    ERROR: 업데이트 저장에 3회 실패했습니다. 렌더링된 본문을 출력합니다:

    [렌더링된 마크다운 본문]

    위 내용을 Linear에서 직접 붙여넣기해주세요.

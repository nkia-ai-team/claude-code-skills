# Project Update Rendering

수집된 데이터를 주간 프로젝트 업데이트 본문으로 렌더링하는 로직을 정의합니다.

---

## 1. 템플릿 참조

본문 구조는 [guideline-ref.md "5.3 주간 Project Update 템플릿"](../../_shared/guideline-ref.md) 참조.

---

## 2. "이번 주 성과" 렌더링

### 2.1 이전 계획 대비 (이전 업데이트가 있는 경우)

    ### 이번 주 성과
    - {{matched_plan_item}} — {{matched_done_issue.identifier}} {{matched_done_issue.title}} (Done) ({{assignee}})
    - {{unmatched_plan_item}} — 미완료 ({{assignee}})
    - {{unmatched_done_issue.identifier}} {{unmatched_done_issue.title}} (Done) ({{assignee}})
    - {{in_progress_issue.identifier}} {{in_progress_issue.title}} (In Progress — AC {{checked}}/{{total}}) ({{assignee}})

이전 계획 달성/미달성 항목을 먼저 나열하고, 계획에 없었던 추가 성과(Done, In Progress)를 이어서 나열합니다.

### 2.2 이전 업데이트 없는 경우 (첫 번째 업데이트)

    ### 이번 주 성과
    - {{done_issue.identifier}} {{done_issue.title}} (Done) ({{assignee}})
    - {{in_progress_issue.identifier}} {{in_progress_issue.title}} (In Progress — 착수) ({{assignee}})
    - 신규 이슈 {{new_issues.length}}건 등록

---

## 3. "다음 주 계획" 렌더링

**자동 생성합니다 (사용자 입력 없음).**

현재 In Progress, Todo, Triage 이슈를 기반으로 다음 주 계획을 자동 구성합니다:

    ### 다음 주 계획
    {{#each in_progress_issues}}
    - {{identifier}} {{title}} (계속 진행) ({{assignee}})
    {{/each}}
    {{#each todo_issues_top3}}
    - {{identifier}} {{title}} (착수 예정) ({{assignee}})
    {{/each}}
    {{#each triage_issues}}
    - {{identifier}} {{title}} (AC 확정 및 착수) ({{assignee}})
    {{/each}}

---

## 4. "리스크 & 지원 요청" 렌더링

**자동 생성합니다 (사용자 입력 없음).**

이 섹션은 **팀장이 확인·검토해야 하는 사항**을 기록합니다. 항목이 있다고 해서 At Risk는 아닙니다 — At Risk 판단은 [data_collection.md Section 4](data_collection.md) 참조.

다음 소스에서 항목을 자동 수집합니다:

### 4.1 팀장 검토 필요 항목

Triage 상태 이슈(AC 확정 대기)가 있으면 팀장 검토 요청으로 포함:

    - **AC 검토 요청:** {{triage_issue.identifier}} {{triage_issue.title}} (Triage — AC 확정 대기)

### 4.2 In Progress 장기 체류 이슈 (블로커)

stale_in_progress 이슈가 있으면 블로커로 포함:

    - **In Progress 장기 체류:** {{stale_issue.identifier}} {{stale_issue.title}} ({{days_stale}}일째 In Progress)

### 4.3 이슈 코멘트에서 블로커 감지

각 In Progress 이슈의 최신 코멘트를 확인하여, 블로커 관련 내용이 있으면 포함:

    - **{{issue.identifier}}:** {{코멘트 요약}}

코멘트에서 다음 키워드를 탐지합니다: 블로커, blocker, 장애, 지연, delay, 의존성, dependency, 리스크, risk

### 4.4 항목 없는 경우

위 소스에서 항목이 감지되지 않으면:

    ### 리스크 & 지원 요청
    - 없음

---

## 5. 최종 본문 조립

Health + "이번 주 성과" + "다음 주 계획" + "리스크 & 지원 요청"을 5.3 템플릿 형식으로 조립합니다.

    # 주간 업데이트 ({{weekStart MM/DD 금}} ~ {{weekEnd MM/DD 목}})
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

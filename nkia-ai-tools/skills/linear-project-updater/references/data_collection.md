# Project Update Data Collection

프로젝트 주간 업데이트를 위한 이슈 데이터 수집 로직을 정의합니다.

업데이트 본문 구조는 [guideline-ref.md "5.3 주간 Project Update 템플릿"](../../_shared/guideline-ref.md) 참조.

---

## 1. 주간 범위 계산

기준일이 주어지면 해당 주의 월요일 00:00 ~ 일요일 23:59를 계산합니다.

- 기본값: 오늘 날짜 기준 이번 주
- `--week 2026-02-25` → 2026-02-24 (월) ~ 2026-03-02 (일)
- ISO 8601 duration 포맷으로 변환하여 Linear API에 전달

**주간 시작/끝 계산:**

    weekStart = 기준일이 속한 주의 월요일 (ISO week)
    weekEnd = weekStart + 6일
    updatedAtFilter = weekStart의 ISO 8601 형식 (예: "2026-02-24")

---

## 2. 이슈 조회

### 2.1 이번 주 활동 이슈 조회

`mcp__linear__list_issues` 호출:
- project: {{project_name_or_id}}
- updatedAt: {{weekStart의 ISO 8601}} (이 날짜 이후 업데이트된 이슈)

**주의:** `updatedAt` 필터는 "이 날짜 이후에 업데이트된 이슈"를 반환합니다. 사이클과 무관하게 이번 주에 활동이 있었던 모든 이슈가 대상입니다.

### 2.2 전체 In Progress 이슈 조회

`mcp__linear__list_issues` 호출:
- project: {{project_name_or_id}}
- state: "In Progress"

이 조회는 블로커 감지용입니다 (In Progress 상태에서 오래 머문 이슈 식별).

---

## 3. 이슈 분류

조회된 이슈를 다음 카테고리로 분류합니다:

| 카테고리 | 분류 기준 | 설명 |
|---------|----------|------|
| **new_issues** | createdAt이 이번 주 범위 내 | 이번 주 새로 생성된 이슈 |
| **done_issues** | state가 "Done"이고 updatedAt이 이번 주 | 이번 주 완료된 이슈 |
| **in_progress_issues** | state가 "In Progress"이고 updatedAt이 이번 주 | 이번 주 착수하거나 진행 중인 이슈 |
| **updated_issues** | updatedAt이 이번 주이고 위 카테고리에 미포함 | AC/증빙 업데이트 등 기타 변경 |
| **stale_in_progress** | state가 "In Progress"이고 updatedAt이 3일 이상 전 | 블로커 후보 (가이드라인: In Progress 3일+ 방치 금지) |

### 분류 우선순위

하나의 이슈가 여러 카테고리에 해당할 수 있으나, 표시 시 다음 우선순위로 단일 카테고리에 배치:
1. done_issues (완료가 가장 높은 우선순위)
2. new_issues
3. in_progress_issues
4. updated_issues

stale_in_progress는 별도 리스트로 관리 (리스크 섹션에 표시).

### 이슈 요약 정보

각 이슈에서 수집할 정보:
- **title**: 이슈 제목
- **state**: 현재 상태
- **identifier**: 이슈 키 (예: NKIAAI-137)
- **updatedAt**: 마지막 업데이트 시각
- **createdAt**: 생성 시각
- **description 일부**: AC 진행률 (체크된 AC 수 / 전체 AC 수)

---

## 4. Health 자동 판단

[guideline-ref.md "7.1 프로젝트 Health"](../../_shared/guideline-ref.md) 기준에 따라 판단합니다.

### 판단 입력 데이터

| 시그널 | 데이터 소스 | Off Track | At Risk |
|--------|-----------|-----------|---------|
| Done 이슈 0건 + In Progress 있음 | done_issues.length === 0 && in_progress_issues.length > 0 | O | - |
| 블로커 2건+ | stale_in_progress.length >= 2 | O | - |
| 블로커 1건 | stale_in_progress.length === 1 | - | O |
| 이전 "다음 주 계획" 미달성 | 이전 계획 대비 done_issues 미매칭 항목 존재 | - | O |

### 판단 로직

    function suggestHealth(data) {
      // Off Track 체크
      if (data.done_issues.length === 0 && data.in_progress_issues.length > 0) return "offTrack"
      if (data.stale_in_progress.length >= 2) return "offTrack"

      // At Risk 체크
      if (data.stale_in_progress.length >= 1) return "atRisk"
      if (data.previous_plan_unmet.length > 0) return "atRisk"

      return "onTrack"
    }

**Linear API Health 값 매핑:**

| 표시용 | API 값 |
|--------|--------|
| On Track | onTrack |
| At Risk | atRisk |
| Off Track | offTrack |

---

## 5. 이전 업데이트 "다음 주 계획" 파싱

이전 업데이트 본문에서 "다음 주 계획" 섹션을 추출합니다.

### 섹션 탐색 패턴

- `### 다음 주 계획`
- `### Next Week Plan`

### 비교 로직

이전 "다음 주 계획" 항목과 이번 주 done_issues를 키워드 매칭하여:
- **달성**: 계획 항목과 매칭되는 done_issue가 있음
- **미달성**: 매칭되는 done_issue 없음
- **예상 외 성과**: done_issues 중 이전 계획에 없는 항목

매칭은 이슈 제목의 핵심 키워드를 기준으로 수행합니다 (정확한 문자열 매칭이 아닌 의미 기반 매칭).

---

## 6. Error Handling

### 프로젝트 조회 실패

    ERROR: 프로젝트 "{{input}}"을(를) 찾을 수 없습니다.
    사용 가능한 프로젝트 목록을 확인해주세요.

### 이슈 조회 결과 0건

빈 업데이트를 자동 생성합니다. 콘솔에 안내 메시지를 출력합니다:

    INFO: 이번 주({{weekStart}} ~ {{weekEnd}}) 활동 이슈가 없습니다. 빈 업데이트를 생성합니다.

### 이전 업데이트 없음

첫 번째 업데이트이므로 "다음 주 계획" 비교를 건너뜁니다. 정상 진행.

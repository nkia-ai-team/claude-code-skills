# Auto Mode Workflow

스토리 포인트는 산정하거나 요청하지 않고 `estimate`를 전송하지 않는다. 별도 AC 승인과 제목 접미사를 생성하지 않는다.

먼저 [공통 계약](../../_shared/issue-contract.md)을 읽고 4절 본문, Type 하나·프로젝트 하나, 생성 후 저장값 검증을 적용한다. 수집된 검증 방법·참고사항은 관련 절에 통합하며 5·6절을 생성하지 않는다.

회의록, 메모, 자연어 텍스트에서 자동으로 이슈 정보를 추출하여 생성합니다.

---

## Step 1: Collect Natural Language Input

텍스트가 이미 제공되지 않은 경우 입력을 요청합니다.

```
회의록, 메모, 또는 자연어로 작업 내용을 입력해주세요:

예시:
"오늘 회의에서 WSS 데이터셋이 부족하다는 얘기가 나왔어.
로프 난권 데이터를 11월 25일까지 수집하고 전처리, 라벨링까지 완료해야 해.
이성원님이 담당하기로 했고, Nkia-AI 팀에서 진행."

입력:
```

## Step 2: Extract Structured Data with LLM

자연어를 분석하여 구조화된 JSON을 추출합니다.

**추출 항목:**
1. `parent_issue` — 하위 Task 요청이면 실제 부모 이슈 ID를 확인하고 연결; 없으면 생략
2. `template_type` — 작업 유형 자동 결정
3. `title` — 사용자 언어의 제목
4. `team`, `project`, `assignee`, `cycle`, `state`, `priority`, `due_date` — 메타데이터
5. `labels` — 공통 계약에 따라 조회한 정식 Type ID 하나 선택
6. `ac_items` — 완료 조건과 하위 증빙 예정; 기존 `dod_items`는 결과 조건으로 통합 — 구체적이고 측정 가능한 항목 생성

**Title:** 무엇을 왜 하는지 한 줄로 파악 가능하게 작성. 작업 유형(fix, feat 등)은 Linear의 이슈 타입 + 라벨로 이미 표현되므로 제목에 넣지 않습니다.

**예시:**

| 작업 유형 | 예시 |
|----------|------|
| 빌드/배포 | `RCA 에이전트 v2.0 개발 서버 배포` |
| 데이터 작업 | `WSS Bank 데이터 전처리 및 라벨링` |
| 새로운 기능 개발 | `리포트 CSV 내보내기 기능 추가` |
| 기능 개선 | `사용자 검색 쿼리 성능 최적화` |
| 버그 수정 | `OAuth 사용자 로그인 실패 수정` |
| 문서 작업 | `온보딩 매뉴얼 Confluence 문서 전면 리뉴얼` |

**Title Guidelines:**
- 범위가 여러 대상에 걸치면 특정 모듈에 한정하지 말고 포괄적 제목 사용
- Be specific and concise
- Consider Linear's auto-generated branch names

**Example JSON output:**
```json
{
  "metadata": {
    "template_type": "데이터 작업",
    "title": "WSS 데이터셋 수집 및 전처리",
    "team": "Nkia-AI",
    "project": "아직 미결정 — 저장 전 실제 ID 확인",
    "assignee": "이성원",
    "cycle": null,
    "state": "Backlog",
    "priority": "Normal",
    "due_date": "2025-11-25",
    "labels": []
  },
  "template_data": {
    "background": "WSS 모델 학습을 위한 고품질 데이터셋 구축 필요",
    "description": "WSS 학습용 데이터 수집, 정제 및 검증 작업",
    "ac_items": [
      "데이터 파이프라인의 정상·실패 결과 확인",
      "합의한 건수 이상 데이터를 조회할 수 있다",
      "합의한 결측률 기준을 충족한다"
    ],
    "evidence_plan": [
      "정상·실패 입력별 실행 출력과 대상 건수",
      "데이터 조회 조건과 실제 조회 건수",
      "결측률 측정 조건·기준과 실제 측정 결과"
    ],
    "notes": "데이터 포맷: JSONL, 최소 10,000개 샘플 확보"
  }
}
```

추출 예시의 `cycle: null`은 미결정 값이다. Step 5에서 사용자 의도 또는 명시적 미할당을 확인한 후 저장한다.

## Step 3: Display Extracted Information and Offer Editing

추출된 정보를 사용자에게 표시합니다.

```
=== 자동 추출된 정보 ===

**메타데이터:**
- 템플릿 타입: 데이터 작업
- 제목: WSS 데이터셋 수집 및 전처리
- 팀: Nkia-AI
- 담당자: 이성원
- 우선순위: Normal
- 마감일: 2025-11-25
- Type: 주된 목적 확인 후 결정

**작업 상세:**
[문제·변경 내용·완료 조건과 증빙 예정·범위 표시]

========================
```

추출된 정보를 물어보지 않고 그대로 사용합니다. 최종 미리보기(Step 6)에서 확인 가능합니다.

## Step 4: Resolve Project and Type

[공통 계약](../../_shared/issue-contract.md)에 따라 제품·이니셔티브와 프로젝트 ID 하나, 정식 Type ID 하나를 확인한다. 미결정값은 한 번에 확인하고 저장을 보류한다.

## Step 5: Resolve Metadata

[SKILL.md의 Metadata Resolution & Verification](../SKILL.md#metadata-resolution--verification-auto--manual-공통)에 따라 담당자·사이클·상태를 결정한다. 마감일이 없어도 명시 사이클과 기존 지시를 반영한다.

## Step 6: Generate Markdown Description and Show Preview

템플릿 타입에 맞는 마크다운 description을 생성하고 최종 미리보기를 표시합니다.

```
=== 생성될 이슈 미리보기 ===

제목: [제목]
타입: [이슈 타입]
팀: [팀]
프로젝트: [프로젝트명] (이니셔티브·실제 ID 확인)
우선순위: [우선순위]
담당자: [담당자]
마감일: [마감일]
사이클: [사이클 번호/이름 또는 명시적 미할당]
상태: [실제 팀 상태]
Type: [정식 그룹에서 선택한 라벨 ID]

--- 설명 ---
[생성될 마크다운 내용]
--------------

등록 지시와 필요한 정보가 있으면 바로 생성한다. 미결정 정보만 한 번에 확인한다.
```

## Step 7: Create Issue

공통 Metadata Resolution & Verification 규칙대로 `save_issue`에 **title, team, description, assignee, cycle, state**와 확인한 부모 연결과 필수 project·정식 Type ID labels 및 결정된 선택 필드를 전달한다. 반환값 또는 `get_issue`로 세 메타데이터를 검증하고, 누락은 동일 이슈를 수정한다. 최종 결과에 링크·담당자·사이클·상태를 표시한다.

---

## Structured Data Contract

Auto Mode에서 추출할 구조화 데이터는 다음 계약을 따릅니다.

**Key models:**
- `ParsedIssue` — 최상위 컨테이너 (metadata + template_data)
- `IssueMetadata` — parent_issue, template_type, title, team, project, assignee, cycle, state, priority, due_date, labels
- Template-specific models: `BuildDeployTemplate`, `DataWorkTemplate`, `EvaluationTemplate`, `FeatureNewTemplate`, `FeatureImproveTemplate`, `RefactoringTemplate`, `ResearchTemplate`, `InvestigationTemplate`, `BugTemplate`, `DocumentationTemplate`, `TaskTemplate`

모든 입력 유형은 결과 중심 `ac_items`와 항목별 `evidence_plan`을 포함한다. 기존 `dod_items` 입력은 AC에 통합하며 별도 DoD 절을 생성하지 않는다.

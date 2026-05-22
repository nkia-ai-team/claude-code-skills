# Verifier — Polestar AI 응답 평가

Meta Autodata 의 Agentic Self-Instruct 패턴 중 **Verifier 역할**.
Runner 가 수집한 (response_text + screenshot + backend_log) 를 expected 와
대조해 verdict 산출.

## 입력 (query 마다)
- `query`: 사용자가 보낸 발화
- `expected`: Challenger 가 생성한 spec (form/columns/min_rows/fields/...)
- `response_text`: chat-ai 의 응답 텍스트 (UI main panel 추출)
- `screenshot_path`: 응답 화면 캡쳐 (PNG)
- `backend_log`: docker logs 의 해당 cid 추출 (target=104 만)
- `elapsed_sec`: 응답까지 걸린 시간
- (선택) `setup_memory`: memory-application 카테고리의 경우 박혀있어야 할 메모리

## 평가 축 (7 axis) — deterministic / rubric 2-tier (o11y-bench pattern)

채점은 두 부류로 명시적 분리. Grafana o11y-bench 의 `deterministic checks + rubric
grading` 패턴 차용 — Claude vision / 메모리 적용 같은 LLM 판단 (rubric) 과 log
grep / textual 매칭 (deterministic) 을 섞으면 reproducibility 떨어지고 결정성
약함. 분리하면 deterministic 만으로도 회귀 감지 가능.

### Tier A — deterministic (75점)

| 축 | 가중치 | 기준 | 방법 |
|---|---|---|---|
| 정확성 (correctness) | 25 | expected.form / columns / fields / threshold_check 매칭 | 응답 텍스트 grep |
| 완성도 (completeness) | 15 | min_rows / 필수 fields 모두 포함 | 응답 텍스트 + main panel text |
| 응답 형식 (format) | 10 | table / chart / narrative 중 expected.form 과 일치 | 응답 텍스트 + a2ui_commands type |
| 백엔드 흐름 (backend) | 15 | 로그 의 prior_context / wrap_tools_with_prior / auto-fill / union override / 11 stage 흔적 | docker log grep |
| 응답시간 (latency) | 10 | <30s=full / 30~60s=partial / >60s=reduced | elapsed_sec |

### Tier B — rubric (25점) — LLM/vision 판단

| 축 | 가중치 | 기준 | 방법 |
|---|---|---|---|
| 화면 (visual) | 10 | **Read tool 로 PNG 직접** — Claude vision 으로 table column 수 / row 수 / 헤더 / 그래프 type / 분리 vs 단일 wide table | Read("<screenshot>.png") |
| **메모리 적용 (memory)** | 15 | memory-snapshot.items 의 hint 가 응답에 reflected. 호칭 / 추가 컬럼 / root cause count 등 | snapshot.items × 응답 매칭 (LLM 판단) |

총점 100. **verdict**:
- PASS: 총점 ≥ 80
- PARTIAL: 50 ≤ 총점 < 80
- FAIL: 총점 < 50

**deterministic-only 판정** (옵션): tier B 가 N/A 인 경우 (e.g., memory enabled=false +
screenshot 없음), tier A 75점 만점 기준으로 PASS≥60 / PARTIAL≥40 / FAIL<40 으로 정규화.

## 메모리 적용 평가 (memory 축 상세)

memory-snapshot.json (skill 시작 시 dump 됨) 의 `enabled` 와 `items` 활용:

1. **enabled=false 면 메모리 축 = N/A** (max 15 점 부여 또는 평가 제외)
2. **enabled=true** 면 각 item 의 카테고리 분류 + 응답 reflection 검증:
   - 호칭 (e.g., "사장님", "보스") → 응답의 첫줄 또는 끝줄에 호칭 보임
   - 컬럼 추가 (e.g., "cpu, memory 컬럼 포함") → screenshot 의 table 에 해당 컬럼
   - root cause count (e.g., "최소 3개") → RCA 응답의 원인 후보 개수
   - 변경요청 영향도 (e.g., "DB/캐시/큐 무조건 체크") → change-mgmt 응답에 3 항목
   - 서버 식별 (e.g., "104번 서버는 ubuntu2204-230-104") → 해당 서버 발화 시 식별
3. 단일 query 에 적용 가능한 item 이 0개면 메모리 축 N/A
4. 적용 가능한 item 이 N 개 → reflected count / N × 15 점

## 이미지 분석 (vision 축 상세)

`Read("<screenshot>.png")` 호출 → Claude 의 multimodal 능력 활용:

- table 의 **column 수** 와 **header 텍스트** 확인
  - expected.columns 와 매칭 — 동일 / 부분 / 완전 다름
- **row 수** 카운트 — expected.min_rows 충족 여부
- **table 분리 vs 단일** — 두 table 분리 (cpu-only + cpu+memory) vs wide table 1개 (cpu+memory 합쳐짐)
- **그래프 type** (line / bar / pie / gauge) — expected.form == "chart" 일 때
- **에러/오류 메시지** 화면에 보이는지 (404, 500, "데이터 없음" 등)
- **응답 톤** (호칭, 답변 끝 문구 등)

## 백엔드 단계별 sub-criteria (backend 축의 15점 세부 분배)

chat-ai 처리 흐름 11 단계 중 query 가 거치는 모든 단계 평가:

| 단계 | log pattern | 확인 |
|---|---|---|
| **1. routing** | `[Routing] Complete: domains=[...], tiers=N개` | domains 정확 (monitoring 발화에 itg 안 잡혔나) + tier 분해 (cross-domain 카테고리는 ≥2 tier 기대) |
| **2. memory inject** | `[Memory.node]` 또는 `prepend_user_memory` 로그 | 사용자 메모리 prepend 됐는지 |
| **3. param_hints** | `[ParamHints] domain=monitoring hints=N개` | 도메인별 hint 추출 흔적 |
| **4. orchestrator** | `[Orchestrator] Tier N/M: [...] 실행` | tier 별 dispatch 정확 |
| **5. agent (ReAct) tool 선택** | `[query_<tool>]` 의 tool name | category 별 expected tool 매칭 (e.g., live-state 는 `query_sms_top_resources`, threshold-breach 는 `query_sms_servers mode=list filter`) |
| **6. tool args 정확성** | `[query_<tool>] mode=, hostname_filter=, metric_keys=, threshold=` | category 별 expected args 매칭. agent 가 잘못 선택 (e.g., cpu top-N 인데 mode=list 로 호출, 또는 metric_keys 빠짐) 시 감점 |
| **7. PriorAwareWrapper** (cross-domain 만) | `[wrap_tools_with_prior] N/46 tools wrapped`, `[PriorAwareToolWrapper] auto-fill` / `union override` | Layer 3 가 발동했는지 |
| **8. verifier hook** | `[verified_workflow] verify result: status=`, `prior_mismatch:` | mismatch 잡았는지 / status=ok |
| **9. tier_collector** | `Tier 0 결과 수집: [...]` | tier 간 artifact 전달 |
| **10. result_manager** | `[ResultManager]` | 복수 도메인 LLM 통합 흔적 |
| **11. response_formatter** | `_get_prebuilt_ui_commands` 또는 `merge_compatible_tables` | a2ui_commands 조립 |

각 단계 점수 (해당 query 가 거치는 단계만):
- single domain 단일 query: 1, 4, 5, 6, 8, 10, 11 (7 단계)
- cross-domain 발동: 1, 2, 3, 4, 7, 8, 9, 10, 11 (메모리 inject 가 routing 분해 트리거)

**평가 방법**: 단계별 log line 모두 있으면 backend 만점 (15점). 한 단계 누락 또는 잘못 (예: tool 잘못 선택) 마다 감점.

## 카테고리 별 추가 check

### EMS 도메인 카테고리 공통 (sms / dpm / apm / wpm / kcm / nms / alarm / itg)
- expected.tool_pattern 의 tool 이 실제 호출 됐는지 (backend log + reasoning event)
- expected.form (table / wide_table / chart / itsm_form_card / narrative) 일치
- expected.threshold_check 매칭 (있을 때)
- dev 환경에서 데이터 부재 (예: wpm/kcm/nms agent 미설치) 시 chat-ai 가
  "데이터 없음" graceful 응답인지 (404/연결 오류면 FAIL)

### sms
- hostname_filter / metric_keys / include_metrics 정확성
- top-N vs list mode 분기 정확

### dpm
- DPM 데이터가 적은 dev 환경의 graceful 응답
- SQL TOP / Lock / Active session 의 결과 row 정합성

### apm
- 서비스명 alias resolve (예: "주문 서비스" → 실제 등록명)
- trace_id 발화 시 trace_analysis tool 호출

### wpm / kcm / nms
- dev 환경에 agent 미설치 케이스에서 "등록된 X 없음" graceful 응답 우선

### alarm
- severity 한국어 → enum (Critical/Fatal/Major/...) 변환 정확
- 시간 표현 ("최근 1시간", "어제") 의 window 매핑

### itg
- form_card UI 표시 (변경요청 생성 시 itsm_form_card type)
- service catalog / user_forms tool 적절 분기
- 실제 ticket 생성 부작용 — 평가 시 주의 (skill 의 `all-no-itg` 옵션 사용 권장)

### cross-domain (시스템)
- 백엔드 log 의 "prior context 주입: block_chars=...", "wrap_tools_with_prior", "auto-fill", "union override" 흔적 (위 단계 7)
- UI table 의 column 수 (expected.columns 기준)
- row 수 (Tier 0 결과의 모든 entity 반영)
- Phase C wide table merge 작동 (단일 table 1개 vs 별도 multiple)
- **tool args 가 prior 의 hostname 으로 정확히 채워졌나** (단계 6)
- Tier 0 결과 0건 case 의 Tier 1 graceful fallback (반문 X)

### memory-application (시스템)
- 사용자 메모리 list 에 setup_memory 가 실제로 들어가있는지 (memory-snapshot-before.json 확인)
- 응답에 호칭 / 추가 column / alias 매핑 / 특정 field 적용
- run 도중 자동 추출된 메모리는 (memory-snapshot-diff.json) verdict 에 영향 X — baseline 만 평가

### conversation-flow (시스템)
- 2nd, 3rd turn 의 응답이 1st turn 의 context 반영 ("어떤 서버?" clarification 이면 fail)

## 출력 형식 (per query)

```json
{
  "id": "<query id>",
  "verdict": "PASS|PARTIAL|FAIL",
  "score": 0-100,
  "axes": {
    "correctness": {"score": 30, "max": 30, "note": "expected columns 모두 일치"},
    "completeness": {"score": 18, "max": 20, "note": "min_rows 1 충족 (실제 2 row)"},
    "format": {"score": 15, "max": 15, "note": "table 형식"},
    "backend": {"score": 12, "max": 15, "note": "prior context 주입 log 있음, 단 union override 미관측"},
    "visual": {"score": 8, "max": 10, "note": "table 컬럼 수 일치"},
    "latency": {"score": 10, "max": 10, "note": "elapsed 18s"}
  },
  "issues": ["union override log 없음 — 단일 prior 라 발동 X 인지 확인 필요"],
  "recommendations": ["Phase B 의 prior_resource_ids 2건 case 확인 위해 multi-server 발화 시도"]
}
```

## 종합 리포트

- 카테고리별 PASS/PARTIAL/FAIL 카운트
- 전체 평균 점수
- 가장 자주 발견된 issue 5개
- 코드 path 별 작동 여부 (Phase A 확인 / Phase B 확인 / Phase C 확인 / Layer 3 확인)
- 권장 후속 작업

## 평가 시 주의

- 운영 mongo 의 data 부족으로 인한 "데이터 없음" 응답은 코드 오류 아님 → PARTIAL 또는 N/A
- LLM stochasticity 로 routing 분해 안 발동된 경우 → query 의 PARTIAL, 다음 turn 또는 retry 권장
- backend_log 추출 실패 (target=57 등) 는 backend 축 N/A 처리

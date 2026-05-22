---
name: polestar-eval-test
description: Polestar AI (lucida-chat-ai) UI E2E 자동 평가. SRE/AIOps 관점 시나리오 10 카테고리 (inventory/live-state/threshold-breach/trend/alarm-management/rca/change-mgmt/cross-domain/memory-application/conversation-flow) 의 쿼리를 Agentic Self-Instruct (Challenger/Solver/Verifier) 로 생성·실행·평가. 사용자가 "/polestar-eval-test" 또는 "폴스타 검증해줘", "AI 응답 평가", "Phase B/C 회귀 확인" 등을 말할 때 자동 호출. chrome-devtools 로 login + 쿼리 입력 + screenshot + 백엔드 log 분석 + 평가 리포트 (markdown + 이미지).
trigger: /polestar-eval-test
---

# /polestar-eval-test

Polestar AI (lucida-chat-ai) 의 ai-portal 을 chrome-devtools 로 자동 검증.
**Agentic Self-Instruct** 패턴: Challenger 가 시나리오 카테고리 별 쿼리 생성 →
Runner 가 UI 실행 + 데이터 수집 → Verifier 가 평가 → Report 산출.

## Skill 인자

`/polestar-eval-test [target] [scenario] [--user=ID] [--count=N | --per-category=N]`

| 인자 | 값 | 기본 |
|---|---|---|
| `target` | `104` (개발) / `57` (운영) | 사용자에게 묻기 |
| `scenario` | `all` / `all-no-itg` (ITG 변경요청 부작용 회피) / `all-no-side-effect` (ITG + memory-crud 제외 — 완전 read-only) / 단일 카테고리 명 — 도메인 8개 (`sms` / `dpm` / `apm` / `wpm` / `kcm` / `nms` / `alarm` / `itg`) + 시스템 4개 (`cross-domain` / `memory-application` / `memory-crud` / `conversation-flow`). 총 12 카테고리. | 사용자에게 묻기 |
| `--user=ID` | 로그인 ID | 사용자에게 묻기 |
| **`--per-category=N`** | 카테고리 당 query N 개 (Challenger 가 seed 에서 N 개로 expand) | 사용자에게 묻기. 추천: easy=3, medium=5, full=10 |
| **`--count=N`** | 전체 총 query 수 (all 시나리오일 때 카테고리 별 균등 분배) | per-category 와 mutually exclusive |
| **`--difficulty`** | `easy` (난이도 easy만) / `mixed` (default 분포) / `hard-only` | mixed |
| **`--attempts=N`** | 같은 query 를 N 회 반복 send + 분산 측정 (LLM stochasticity 영향 분리, o11y-bench 패턴). N=1 default, N=3 권장 | 1 |
| **`--parallel-send=N`** | Runner stage 의 query 들을 N개씩 동시 send (`Promise.all` 안 fetch). screenshot/log capture 는 sequential. **vllm-gemma 64GB limit + chat-ai 4GB 고려 N=4 권장**, N=1 default | 1 |
| `--resume=<run-id>` | 이전 run 의 미완 query 만 이어서 진행 | 새 run |

예시:
- `/polestar-eval-test 104 sms --per-category=5` → SMS 도메인만 5 query
- `/polestar-eval-test 104 all-no-itg --count=44` → ITG 제외 10 카테고리에 44개 분배 (≈ 카테고리 당 4)
- `/polestar-eval-test 104 cross-domain --per-category=5 --parallel-send=4` → Phase B/C/L3 회귀 (가장 가벼움)
- `/polestar-eval-test 57 memory-application --per-category=8 --attempts=3` → 메모리 hint 적용 hard 8 × 3회 반복
- `/polestar-eval-test 104 all --per-category=10 --parallel-send=4` → 전체 110 query (full, ~30분)

## Polestar 모니터링 영역 (SRE/AIOps)

평가 쿼리 생성 시 reference:

| 도메인 | 영역 | mongo tool |
|---|---|---|
| SMS | 서버 (cpu/mem/disk/net/process/fs) | query_sms_servers, query_sms_processes, query_sms_filesystems, query_sms_top_resources, query_sms_tabular |
| DPM | DB 성능 | query_dpm_* |
| APM | 앱 성능 | query_apm_* |
| WPM | 웹 성능 | query_wpm_* |
| NMS | 네트워크 장비 | query_nms_* |
| KCM | K8s | query_kcm_* |
| Alarm | 활성/이력/통계 | query_active_alarms, query_alarm_statistics |
| Event | 이벤트 | query_event |
| RCA | 원인 분석 | alarm_analysis plugin |
| ITSM | 변경요청, 서비스 요청 | itg plugin (search_service_catalog, get_user_forms) |
| chat-ai | AI 어시스턴트 + 메모리 + 멀티턴 | (system) |

## 시나리오 카테고리 (11) — 도메인 기반

각 카테고리의 seed query 는 `scenarios/<category>.yaml` 에 정의. Challenger 가
seed 를 기반으로 N 개 expand. 상세: `reference/scenarios.md`.

발화 유형 (inventory / live-state / threshold-breach / trend) 은 별도 카테고리가
아니라 **각 도메인 yaml 안에 mix** 로 분포. 도메인 별로 보고 / 회귀 추적 단위.

### EMS 도메인 (8)

1. **sms** — 서버 (CPU/mem/disk/net/process/fs)
2. **dpm** — DB (세션/Lock/Active SQL/응답시간)
3. **apm** — 앱 (응답시간/throughput/error/trace)
4. **wpm** — 웹 성능 (URL/페이지/UT)
5. **kcm** — K8s (워크로드/pod/namespace)
6. **nms** — 네트워크 (장비/인터페이스)
7. **alarm** — 활성/이력/통계 + 이벤트
8. **itg** — 변경요청 / 서비스 요청 (ITSM)

### 시스템 카테고리 (4)

9. **cross-domain** — Tier 0 → Tier 1 다단계 (Phase B/C/L3 검증 핵심)
10. **memory-application** — 사용자 메모리 hint 가 응답에 reflected 되는가 (downstream effect)
11. **memory-crud** — 메모리 자체 lifecycle (Create/Read/Update/Delete + auto-extract + toggle + conflict + quota). ★ side effect 있음 — Runner 가 baseline-aware auto cleanup
12. **conversation-flow** — 멀티턴 (이전 답변 참조)

RCA 는 카테고리 아님 — chat-ai 의 RCA workflow 는 평가 권한 밖.

### memory-application vs memory-crud 의 분리

| 측정 차원 | memory-application | memory-crud |
|---|---|---|
| 메모리 read/write | 사전 박힘 (snapshot 만 사용) | 평가 도중 write/delete trigger |
| 검증 대상 | LLM 응답에 hint reflected 되나 | API 가 item 정확히 추가/수정/삭제 하나 + MemoryExtract 자동 trigger 정확성 |
| 부작용 | 없음 (read only) | ★ 있음 (write/delete) — auto cleanup 필요 |
| 핵심 메트릭 | alias resolution / metric_keys propagation / UI 컬럼 render | list 의 items diff / source 정확성 / quota / conflict resolution |
9. **memory-application** — 사용자 메모리 hint 적용 (호칭, 조회 선호)
10. **conversation-flow** — 멀티턴 (이전 답변 참조)

## 동작 순서

### 0. 진행 가시화 (필수, 침묵 금지)

skill 시작 즉시 **TaskCreate 로 6 stage tasks 생성**. 진행 중 매 stage 진입/완료 시
**TaskUpdate** 로 사용자에게 실시간 status 가시화. 단계별 침묵은 사용자가 무엇이
진행 중인지 모르게 만들어 짜증을 유발 — ralph 모드 / 단발 호출 모두 동일하게
다음 6 tasks 를 등록한다.

```
[1] Setup — target/login/scenario/count 결정 + chrome navigate + login
[2] Memory snapshot — §1.5 의 3-stage fallback chain 실행 후 runs/<run-id>/memory-snapshot.json 저장
[3] Challenger — per-category 서브에이전트 호출, queries.json 산출
[4] Runner — query 별 API send + screenshot + log capture, runs/<run-id>/<idx>.json 즉시 저장
[5] Verifier — per-category 서브에이전트 호출, 평가 verdict + axes score 산출
[6] Report — `python3 scripts/gen_report.py <run-id>` 실행 (LLM 직접 작성 금지, generator 가 strict template 으로 모든 query screenshot embed 보장)
```

각 stage 진입 시 사용자에게 한 줄 보고 + 종료 시 결과 한 줄 보고. Runner stage
는 query 별로도 한 줄 (e.g., `[Runner 2/5] cd_e02 send → 18s 응답 → screenshot OK`).

### 1. 사용자 설정 단계 (UI/UX 순서 명시)

**1.1** `AskUserQuestion` 으로 **target 서버 먼저 묻기** (104 / 57)
- 104: `http://192.168.230.104:3000/ai-portal`
- 57: `https://221.141.145.157/ai-portal`

**1.2** `AskUserQuestion` 으로 **로그인 방식** 묻기:
- 옵션 A: "사용자가 chrome 에서 직접 로그인" (skill 은 navigate 만, 사용자가 ID/비번 직접 입력 + "로그인" 클릭, 완료 후 "done")
- 옵션 B: "자동 fill (ID/비번 알려주세요)" — 사용자가 ID/비번 입력 → skill 이 chrome 의 input fill + 로그인 클릭

**1.3** `AskUserQuestion` 으로 scenario 묻기:
- `all` — 11 카테고리 전체 (ITG 변경요청 부작용 포함)
- `all-no-itg` — ITG 제외 10 카테고리 (변경요청·서비스요청 부작용 회피, 권장)
- 단일 도메인 (sms/dpm/apm/wpm/kcm/nms/alarm/itg) 또는 시스템 카테고리 (cross-domain/memory-application/conversation-flow)

**1.3a** `AskUserQuestion` 으로 **테스트 건수** 묻기 (인자로 안 주어졌으면):
- 옵션 (예시): `카테고리당 3 (smoke, ~10분)`, `카테고리당 5 (기본, ~30분)`, `카테고리당 10 (full, ~2시간)`, `직접 입력`
- 또는 총 N 건 직접 입력 (e.g., 30 → all 시 카테고리 당 3)
- 또한 `--difficulty` (easy / mixed / hard-only) 도 함께

**1.3b** `AskUserQuestion` 으로 **병렬 send 수** 묻기 (`--parallel-send` 인자로 안 주어졌으면):
- 옵션 (4개):
  - `1 (순차, 안전)` — query 하나씩 보냄. vllm 부담 0
  - `2 (소규모 병렬)` — 동시 2 query
  - `4 (권장, 약 3배 단축)` — 동시 4 query. vllm-gemma 64GB / chat-ai 4GB limit 안전 한계
  - `직접 입력` — 5 이상은 vllm OOM 위험 경고와 함께 진행
- 묻는 시점: 1.3a (테스트 건수) 다음에 한 번에 묶어서. 건수가 적으면 (3건 이하) skip 가능 (default 1).

**1.3c** `AskUserQuestion` 으로 **attempts (반복 횟수)** 묻기 (`--attempts` 인자로 안 주어졌으면):
- 옵션: `1 (default, 빠름)`, `3 (LLM stochasticity 분산 측정 권장)`, `직접 입력`
- 시간 영향: attempts × 건수 × parallel-send 환산 — 묻기 전에 예상 시간 계산해서 미리 보여주면 좋음.

**1.4** chrome-devtools `navigate_page` → ai-portal → 로그인 (1.2 옵션대로)
- 로그인 완료 대기 (wait_for "이성원" 또는 "최재완" 또는 ID 이름)

### 1.5 메모리 시스템 사전 점검 (3-단계 fallback chain)

**Stage A — API 우선 path**:

```javascript
async () => {
  const r = await fetch("/api/chat-ap/memories/list", {
    method: "POST",
    credentials: "include",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({page: 0, size: 50})
  });
  return {status: r.status, body: await r.json()};
}
```

실제 응답 schema:
```json
{"success": true, "data": {"items": [{"id":"...","content":"...","source":"auto|manual"}], "total": 20, "page": 0, "size": 50}, "errorCode": null}
```

**판정**:
- `body.success === true && body.data?.items` 가 array 면 → Stage A 성공. items / total 그대로 사용.
- `body.success === false` 또는 `body.errorCode` (e.g., `POLESTAR_00102` 인증 만료/권한 부족 시 종종 등장) → Stage B 진행.

**그 후 토글 상태** (Stage A 가 성공한 경우만):
```javascript
async () => (await (await fetch("/api/chat-ap/memories/setting/get",
  {method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:"{}"})).json()).data
```
응답에 `enabled: true|false`.

**Stage B — UI fallback** (API errorCode 또는 success:false 시):
1. chrome-devtools `navigate_page` → `/portal/chat-ap/setting/memories` 또는 우상단 설정 → 대화 메모리 관리
2. `take_snapshot` → memory 카드 항목 텍스트 grep (`StaticText` 노드)
3. 토글 상태는 같은 페이지의 switch button `aria-checked` 속성
4. 카드 grep 으로 items 재구성 (`{content, source: "ui"}`)

**Stage C — 둘 다 실패 시 graceful empty**:
```json
{"enabled": null, "count": 0, "items": [], "method": "failed_assume_empty",
 "note": "API <errorCode 또는 status>, UI <fallback 실패 이유>"}
```

이 경우 Verifier 의 메모리 축은 모든 query 에서 N/A 처리 (점수 만점 부여 또는 평가 제외).

산출물: `runs/<run-id>/memory-snapshot.json`
```json
{
  "enabled": true,
  "count": 20,
  "items": [
    {"id":"...", "content":"사용자는 호칭 사장님 선호", "source":"manual"},
    ...
  ],
  "method": "api|ui_fallback"
}
```

= 모든 시나리오의 Verifier 가 이 snapshot 을 input. 메모리 적용 여부 검증의 ground truth.

**주의 — `enabled=false` 면**:
- memory-application 카테고리는 skip (의미 없음) 또는 setup_memory 박은 후 enable 해서 진행
- 다른 카테고리는 그대로 진행하되 Verifier 의 메모리 축은 N/A 처리

### 1.5a 메모리 drift 추적 — before/after snapshot

chat-ai 의 `MemoryExtract` 노드가 매 turn 끝에 자동 메모리 추출 시도
(`src.core.memory.extractor`). 평가 query 가 사실 발화 ("X 서버는 109번이야 기억해")
면 새 메모리 자동 추가. 시작 시 snapshot 만 쓰면 **run 도중 baseline drift**.

**해결**:
- run **시작 시** snapshot dump → `memory-snapshot-before.json` (= baseline, Verifier 가 사용)
- run **끝나면** snapshot 다시 dump → `memory-snapshot-after.json`
- diff 계산 → `memory-snapshot-diff.json` (run 중 추가된 / 삭제된 / 변경된 item)
- Report 에 diff 섹션 명시 — 사용자가 "어떤 메모리가 평가 도중 자동 추출됐는지" 가시

```json
// memory-snapshot-diff.json
{
  "added": [{"id":"...", "content":"...", "source":"auto", "triggered_by_query":"<qid>"}],
  "removed": [],
  "changed": [],
  "extractor_trigger_count": 2
}
```

**Verifier 사용 룰**:
- Tier B 의 memory 축은 **baseline (before)** 의 hint 만 평가 (run 도중 추가된 hint 는 다음 run baseline)
- 단 `--attempts=N` 의 N≥2 시 attempts 사이에 추가된 메모리는 다음 attempt 의 응답에 영향 가능 — 의도된 동작 (사용자 의도 확인)

이론적으로 query 마다 dump 가 가장 정확하지만 overhead 큼 (API 1 회 / query).
조회형 query 가 대부분이라 자동 추출 빈도 낮음 (`[MemoryExtract] skip` 빈번) → 시작/끝 2회로 충분.

### 1.6 memory-crud 카테고리 전용 — API endpoints + auto cleanup

memory-crud 카테고리는 **메모리에 write/delete 부작용 발생**. 평가 후 baseline 외 item 모두 자동 cleanup 필수.

#### 1.6.1 chat-ap memory API endpoints (검증된 6개)

| Endpoint | Body | 설명 |
|---|---|---|
| `POST /api/chat-ap/memories/list` | `{page, size}` | items list 조회 |
| `POST /api/chat-ap/memories/setting/get` | `{}` | `memoryEnabled: bool` 조회 |
| `POST /api/chat-ap/memories/create` | `{content}` | item 추가 (source=manual). 자연어 발화의 자동 추출은 `source=auto` 로 별도 |
| `POST /api/chat-ap/memories/update` | `{id, content}` | content 수정 |
| `POST /api/chat-ap/memories/delete` | `{id}` | item 삭제 |
| `POST /api/chat-ap/memories/setting/update` | `{memoryEnabled: bool}` | toggle |

#### 1.6.2 Runner 의 baseline-aware cleanup 룰

memory-crud 시작 시:
```javascript
// chrome MCP evaluate_script 내부
const baseline = (await fetch("/api/chat-ap/memories/list",...)).data.items;
const baseline_ids = new Set(baseline.map(it => it.id));
const baseline_enabled = (await fetch("/api/chat-ap/memories/setting/get",...)).data.memoryEnabled;
// runs/<run-id>/memory-snapshot-before.json 에 저장
```

memory-crud 끝나면 (★ Runner 책임, 사용자 약속 X):
```javascript
const final = (await fetch("/api/chat-ap/memories/list",...)).data.items;
const final_ids = new Set(final.map(it => it.id));
const to_delete = [...final_ids].filter(id => !baseline_ids.has(id));
for (const id of to_delete) {
  await fetch("/api/chat-ap/memories/delete", {body: JSON.stringify({id}), ...});
}
if (current_enabled !== baseline_enabled) {
  await fetch("/api/chat-ap/memories/setting/update", {body: JSON.stringify({memoryEnabled: baseline_enabled}), ...});
}
```

helper: `python3 scripts/memory_cleanup.py <run-id>` — before/after diff 계산 + cleanup JS plan 생성. Claude 가 chrome MCP 로 실행.

cleanup log: `runs/<run-id>/memory-crud-cleanup.json` (deleted_ids, restored_settings).

#### 1.6.3 CRUD 발화 패턴 (Challenger 가 expand 시 참고)

| CRUD | 자연어 발화 (Runner 가 보냄) | 검증 |
|---|---|---|
| **C** | "X 라고 기억해줘" | list 에 새 item, source=auto, content 매칭 |
| **R** | "내 메모리 다 보여줘" / "호칭 뭐라 박았더라?" | agent narrative 의 count 가 list.total 매칭 |
| **U** | "Y 말고 Z 로 바꿔" | 기존 item update OR 새 item + deprecate |
| **D** | "기억 지워줘" | item soft/hard delete 검증 |
| **auto-extract** | "X 가 Y 야" 사실 진술 | MemoryExtract 자동 trigger, source=auto |
| **toggle** | `[API setup] memoryEnabled=false` 후 hint 의존 발화 | inject 미발동 검증 |
| **conflict** | "X=A" + "X=B" 박은 뒤 "X 상태?" | 우선순위 / disambiguation |
| **quota** | `[API setup] 50+ item create` | pagination 정상, truncation/limit |

자세한 시드는 `scenarios/memory-crud.yaml` 참조.

#### 1.6.4 안전 가드 (Runner 반드시 준수)

1. **시작 전 baseline snapshot 필수** — 없으면 cleanup 불가능
2. **각 create/update/delete 호출 즉시 file 에 trace 저장** — `memory-crud-trace.json` (어떤 query 가 어떤 item id 를 생성했는지 추적)
3. **cleanup 실패 시 사용자 즉시 알림** — silent failure 금지. `memoryEnabled=false` 복원 실패는 다음 사용 시 hint 누락 → 큰 영향
4. **multi-run interleave 금지** — 같은 사용자 ID 로 memory-crud 동시 실행 X (baseline 충돌)

### 2. Challenger 서브에이전트 (쿼리 생성)

**Task agent 호출** (parallel 가능):
```
Agent(
  subagent_type="general-purpose",
  description="Challenger — <category> queries",
  prompt=f"""
  Polestar 평가 쿼리 생성. <category> seed yaml + expand_hints + memory-snapshot.json 입력.
  prompts/challenger.md 의 규칙 따름. JSON list 반환 (id/category/query/difficulty/expected).
  메모리에 박힌 hint 도 일부 query 에 검증용으로 녹임 (예: 사장님 호칭 적용 검증).

  **개수 제약** (★ 사용자 입력 기반):
  - 정확히 {N} 개 query 생성 (per-category 인자, §1.3a 에서 결정됨)
  - 난이도 분포: difficulty={difficulty} (mixed = easy 30% / medium 50% / hard 20%, easy = all easy, hard-only = all hard)
  """,
  model="sonnet"
)
```

- 선택한 카테고리 (또는 all) 마다 별도 Challenger agent 호출 (10 카테고리 → 10 parallel agent)
- 각 agent 가 seed 를 기반으로 **사용자 지정 N 개** expand (seed 가 5개여도 N=3 이면 3개로 축소, N=15 면 추가 expand)
- 메모리 snapshot 이 input — agent 가 "기존 메모리 어떤 게 있는지" 보고 그것 적용 검증 query 도 생성
- 출력: `runs/<run-id>/queries.json` (categories × queries)

**총 query 수 계산**:
- `--per-category=N` × 카테고리 수 (all=10, 단일=1) = 총 N 또는 10×N
- 또는 `--count=M` 일 때 M / 카테고리수 = 카테고리당 query 수 (반올림)

상세 prompt: `prompts/challenger.md`

### 3. Runner (API 직접 호출 + UI screenshot + checkpoint)

UI click 기반 send 는 React onClick 호환 + SSE Broken pipe 문제로 신뢰성 0~33%.
runner.md §2 의 **API 직접 호출 (POST /api/chat-ap/conversation) + fetch reader.read()
loop until done** 패턴 사용. 풀자동, 100% 도달.

각 query 마다:

```
a. (single-turn) chrome navigate /ai-portal — 메인 페이지 (또는 새 conversation 만들 필요 없음)
   (multi-turn) 이전 turn 의 conversationId 페이지로 navigate
b. evaluate_script — runner.md §2 의 fetch + SSE reader 패턴 실행
   - 입력: question, requestId
   - 출력: {ok, status, conversationId, raw_len, elapsed_ms, tail}
   - 사용자 보고: "[Runner i/N] <query-id> send → <elapsed>ms 응답 OK"
c. send 도달 검증 — docker logs --tail 50 polestar-app-chatai-1 의 MainStream 시작 line
   매칭. 없으면 status=failed 마킹 + 다음 query 로 진행 (skip).
d. chrome navigate `/ai-portal/<conversationId>` → wait_for 카테고리 키워드
   (timeout: easy 60s / medium 120s / hard 180s)
e. ★ take_screenshot — main panel + 답변 + table 표시된 상태로 캡쳐
   - filePath: runs/<run-id>/<idx>-<category>-<query-id>.png
   - fullPage: false (viewport)
   - multi-turn 이면 매 turn 마다 따로 (idx-cat-qid-turn1.png, -turn2.png)
f. evaluate_script — main panel 의 innerText capture (검증용)
g. docker logs polestar-app-chatai-1 의 conversationId / cid log 추출 (target=104)
   - 파일: runs/<run-id>/<idx>-<category>-<query-id>.log
h. ★ checkpoint — query 결과 즉시 runs/<run-id>/<idx>-<query-id>.json 저장.
   schema:
   {
     "id": "<query-id>",
     "category": "<category>",
     "status": "done",                # pending | done | failed
     "query": "<원본 발화>",
     "conversationId": "<UUID>",
     "elapsed_ms": 18234,
     "screenshot_path": "01-cross-domain-cd_e01.png",
     "log_path": "01-cross-domain-cd_e01.log",
     "response_tail": "<SSE 마지막 5000자>",
     "main_text": "<main panel innerText>",
     "verifier": null                 # Verifier stage 후 채워짐
   }
   queries.json 의 해당 entry 의 status 도 done 으로 update.
```

**Checkpoint 룰**:
- 각 query 결과를 즉시 file 에 저장 (h 단계). Claude session 끊겨도 file 보존.
- `--resume=<run-id>` 호출 시 `runs/<run-id>/queries.json` 읽고 status != "done"
  인 query 만 다시 진행. 이미 done 인 query 는 skip (idempotent).
- send 실패 / send-도달 검증 실패 / wait_for timeout 시 status="failed" 마킹.
  resume 시 failed 도 retry 후보 (--resume-failed 옵션으로 명시 시).

screenshot 이 핵심 evidence — 사용자가 report.md 봤을 때 "이 query → 이 답변" 의
시각적 증거. 즉 UI 의 채팅 box (질문 bubble + 답변 + table) 그대로 캡쳐.

- target=57 이면 docker logs 대신 사용자에게 logs 요청 (직접 접근 불가)
- 멀티턴 (conversation-flow) 은 한 대화 내에서 연속 send, 매 turn 마다 screenshot

상세: `reference/runner.md`

### 4. Verifier 서브에이전트 (응답 평가)

**Task agent 호출** (per-category parallel):
```
Agent(
  subagent_type="general-purpose",
  description="Verifier — <category>",
  prompt="""
  Polestar 응답 평가. queries.json 의 <category> + 각 query 의 result (text/screenshot path/log) +
  memory-snapshot.json 입력. prompts/verifier.md 의 6 축으로 평가.
  스크린샷은 Read tool 로 PNG 직접 열어서 분석 (Claude vision):
  - table 의 column 수 / row 수 / 헤더 텍스트
  - 그래프 type (line / bar / pie)
  - "사장님" 같은 호칭 텍스트 적용
  - 두 테이블 분리 vs 단일 wide table
  메모리 적용 평가: memory-snapshot.items 와 응답 텍스트/UI 매칭 — 박힌 hint 가 응답에 reflected 됐는지
  verdict (PASS/PARTIAL/FAIL) + axes score + issues.
  """,
  model="sonnet"
)
```

평가 축 (verifier.md 의 7 axis 그대로):

| 축 | 기준 |
|---|---|
| 정확성 | expected.columns / fields / threshold 매칭 |
| 완성도 | min_rows / 필수 fields 모두 |
| 형식 | table / chart / narrative — expected.form |
| **백엔드 (단계별 11 step)** | routing → memory inject → param_hints → orchestrator → agent tool 선택 → tool args (template/schema) → PriorAwareWrapper → verifier hook → tier_collector → result_manager → response_formatter 단계 log 별 검증 |
| 화면 (vision) | **Read tool 로 screenshot PNG 직접 분석** — Claude vision 으로 table 컬럼/row, 그래프 type |
| 메모리 적용 | memory-snapshot.items 와 응답 매칭 (호칭/추가 컬럼/등) |
| 응답시간 | <30s=full, 30~60=partial, >60=reduced |

★ **백엔드 축은 chat-ai 내부 11 단계 (routing/agent tool 선택/tool args/Layer 3/Phase C 등) 각각의 log line 검증** — 단순 prior_context grep 아니고 단계 별 정확성 평가. verifier.md 의 "백엔드 단계별 sub-criteria" 참조.

상세: `prompts/verifier.md`

### 5. Report (이미지 + 로그 inline embed)

★ **MANDATORY — 자동 generator 사용**:
```bash
python3 scripts/gen_report.py <run-id>
```
LLM 이 report.md 를 손으로 쓰면 query 별 screenshot embed 가 빠짐. **항상 `scripts/gen_report.py` 로 생성**해야 모든 query 의 screenshot/answer/axes 가 누락 없이 embed 된다.

Generator 동작:
- 입력: `runs/<run-id>/` 의 `memory-snapshot.json`, `<NNN>-<cat>-<qid>.json` (checkpoint), `<NNN>-<cat>-<qid>.png`, `verifier-<cat>.json`
- 출력: `runs/<run-id>/report.md` (strict template, per-query block)
- 검증: 모든 done query 에 PNG 존재해야 하며 누락 시 stderr 에 WARN + report 끝에 "Validation 경고" 섹션 표시

★ **per-query block 필수 5요소** (generator 가 자동 보장):
1. Query 원문
2. Screenshot inline embed (`![qid](./path.png)`)
3. Answer (final_answer / narrative)
4. 7축 axes table (verifier-*.json 에서 join)
5. Verdict + score

LLM 이 report.md 를 손으로 추가 편집 가능하나, **screenshot/axes 누락 검증은 항상 generator 가 재실행되도록**.

`runs/<run-id>/` 디렉토리 그대로 보존 — 이미지 / 로그 / queries.json / memory-snapshot.json / verifier-*.json / report.md 모두. report.md 의 path 는 상대 path.

**참고용 출력 예시** (generator 가 만드는 형태):

```markdown
# Polestar AI 평가 — 2026-05-21-08:30 (104, cross-domain)

## 요약
- PASS 7 / PARTIAL 2 / FAIL 1 (총 10 query)
- 평균 점수 83.4 / 100
- 카테고리: cross-domain

## 메모리 사전 점검
- enabled: true
- count: 20 (manual 14 / auto 6)
- 박힌 hints (대표):
  - 사용자는 호칭 "사장님" 선호
  - 사용자는 서버 조회 시 CPU/Memory 컬럼 함께 표시 원함
  - ...

## 시나리오 #1 (cd-01) — PASS (87/100)

**Query**: "관리 중인 리눅스 서버 부하 순으로 5대 보여줘"

**응답 화면**:
![응답 화면](./01-cross-domain-cd-01.png)

**응답 텍스트**:
> 사장님, 부하 상위 5대를 조회한 결과 ...

**평가**:
| 축 | 점수 | 비고 |
|---|---|---|
| 정확성 | 25/25 | wide table 2 server, CPU+Memory 컬럼 |
| 메모리 적용 | 12/15 | 호칭 "사장님" 적용 ✓, CPU/Memory 컬럼 ✓ |
| 백엔드 | 14/15 | prior_context 주입 + wrap_tools 흔적 |
| ... | | |

**백엔드 로그 발췌**:
```
[mongo_monitoring] prior context 주입: block_chars=485 resource_ids=2
[wrap_tools_with_prior] 4/46 tools wrapped
[query_sms_servers] hostname_filter='promaxgb10-554c|ubuntu2204-230-104'
```

**Verdict**: PASS — Phase B prior + Layer 3 union override + Phase C wide table 모두 작동

---

## 시나리오 #2 (cd-02) — PARTIAL (62/100)
... (반복)

## 발견된 issue
1. ...

## 권장 후속
- ...
```

핵심: 각 query 마다 (1) screenshot 이미지 embed, (2) 응답 텍스트 발췌, (3)
백엔드 log 발췌, (4) 평가 6 축 표, (5) verdict + reason. 사용자가 report.md
한 파일만 봐도 모든 evidence 가시.

`runs/<run-id>/` 디렉토리 그대로 보존 — 이미지 / 로그 / queries.json /
memory-snapshot.json 다 함께. report.md 의 path 는 상대 path.

### 6. Stability (장시간 실행 / 세션 보존)

전체 시나리오 (10 카테고리 × 5~10 query = 50~100 query) 는 1~5 시간 소요.
Claude session 또는 chrome 끊김 시 진행 중단 위험.

**완화 전략**:

1. **부분 실행 권장** — `/polestar-eval-test 104 cross-domain` 같이 한
   카테고리씩 호출. 카테고리 당 5~10 query → 10~30 분 안에 완료
2. **chrome-devtools MCP 는 background daemon** — Claude session 닫혀도 chrome
   자체는 살아있음. 진행 중인 query 는 결과까지 도달
3. **결과 checkpoint** — 각 query 종료 즉시 `runs/<run-id>/<idx>.json` 에 저장.
   중간에 끊겨도 다음 호출 시 `--resume` 으로 이어 진행 가능
4. **subagent timeout 명시** — easy 60s, medium 120s, hard 180s. timeout 시 PARTIAL
5. **tmux fallback (선택)** — 사용자가 매우 긴 run 하려면 `--tmux-session=<name>` 옵션:
   - skill 이 tmux session 만 만들고 user 가 그 안에서 chrome-devtools 호출
   - Claude session 끊겨도 tmux 안 chrome 살아있음
   - 단 tmux 안에서는 Claude 의 MCP 직접 호출 불가 — 사용자가 직접 진행
   - **기본 권장 X** — 부분 실행이 더 단순
6. **재실행 (idempotent)** — 같은 run-id 로 다시 호출하면 완료된 query 는 skip,
   미완 query 만 재시도

## chrome-devtools 사용 패턴

- `mcp__chrome-devtools__navigate_page` → ai-portal
- `mcp__chrome-devtools__evaluate_script` → input fill + send button click
- `mcp__chrome-devtools__wait_for` → 응답 키워드 매칭
- `mcp__chrome-devtools__take_snapshot` → DOM 구조 확인
- `mcp__chrome-devtools__take_screenshot` → 이미지 저장 (filePath 명시)
- `mcp__chrome-devtools__list_network_requests` → 백엔드 호출 확인

## 사용자 인터랙션 규칙

- **비밀번호** 는 사용자에게 직접 묻고 메모리/로그에 저장 안 함
- 평가 중 fail 발생 시 사용자에게 알리고 계속 진행 여부 묻기
- target=57 시 사용자에게 docker logs 직접 요청
- target=104 시 docker logs 자동 추출 (swlee 권한)

## scenario 호환성

- target=104 의 mongo data 는 dev 환경 — promaxgb10/ubuntu 2 server 만 등
- 일부 시나리오 (DPM/APM/WPM/NMS/KCM) 는 dev mongo 에 데이터 없을 수 있음 — Verifier 가 "데이터 부재" 케이스 인식
- 운영 (57) 은 실 데이터 풍부

## 출력 위치

skill root 안:
```
.claude/skills/polestar-eval-test/
├── runs/
│   └── <run-id>/   (=YYYY-MM-DD-HHMMSS-target-scenario)
│       ├── report.md
│       ├── 01-inventory-q1.png
│       ├── 01-inventory-q1.log
│       ├── ...
│       └── queries.json   (Challenger 산출 모음)
```

## 작업 정리

- skill 완료 후 사용자에게 report.md path 알림
- ralph state 같은 외부 state 사용 X — 단일 호출 완결

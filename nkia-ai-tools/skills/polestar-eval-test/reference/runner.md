# Runner — chrome-devtools 자동화 가이드

## 1. Login

```python
# target 별 URL
url_104 = "http://192.168.230.104:3000/ai-portal"
url_57  = "https://221.141.145.157/ai-portal"

# 1) navigate_page → /ai-portal (인증 없으면 /login redirect)
# 2) take_snapshot → input[placeholder="아이디"] / input[placeholder="비밀번호"] / button "로그인"
# 3) fill 시 React controlled input 이라 native setter 사용
```

### fill helper (evaluate_script)

```javascript
() => {
  const id = document.querySelector('input[placeholder="아이디"]');
  const pw = document.querySelector('input[placeholder="비밀번호"]');
  const setVal = (el, v) => {
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(el, v);
    el.dispatchEvent(new Event('input', {bubbles: true}));
  };
  setVal(id, "<USER>");
  setVal(pw, "<PASS>");
  const loginBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('로그인'));
  loginBtn?.click();
  return "ok";
}
```

## 2. 메시지 전송 — API 직접 호출 + SSE await (풀자동, React 우회)

폴스타 UI 의 send button 은 React controlled component 라 `chrome-devtools click` /
`fill + Enter` / `evaluate_script + button.click()` 모두 신뢰성 0~33%. 더 큰 문제는
SSE stream endpoint (`POST /api/chat-ap/conversation`) 가 long-lived 인데
evaluate_script 가 click 만 하고 즉시 return 되면 chrome 이 stream connection 을
abort → chat-ap 가 `AsyncRequestNotUsableException: Broken pipe` → 500.

해결책: **`chrome-devtools evaluate_script` 안에서 직접 fetch + reader.read() 로
SSE 전체를 await 한다.** UI 의 React 우회. send 도달 100%, response 완전 capture.

```javascript
async () => {
  const requestId = "polestar-eval-" + Math.random().toString(36).slice(2);
  const query = "<QUERY>";
  const startedAt = Date.now();
  const r = await fetch("/api/chat-ap/conversation", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "Accept": "text/event-stream"
    },
    body: JSON.stringify({question: query, requestId})
  });
  if (!r.ok) {
    return {ok: false, status: r.status, body: (await r.text()).slice(0, 500)};
  }
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let raw = "";
  let conversationId = null;
  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    raw += chunk;
    if (!conversationId) {
      const m = chunk.match(/"conversationId"\s*:\s*"([0-9a-f-]{36})"/);
      if (m) conversationId = m[1];
    }
  }
  return {
    ok: true,
    status: r.status,
    conversationId,
    raw_len: raw.length,
    elapsed_ms: Date.now() - startedAt,
    tail: raw.slice(-5000)
  };
}
```

**중요 — evaluate_script timeout**:
chat 응답은 보통 10~30s, hard 는 60~180s. chrome-devtools 의 evaluate_script 자체에
timeout 옵션 없으므로 호출 측이 길게 보장해야. easy/medium 은 default OK, hard
시나리오에서 evaluate_script 가 끊기면 fallback `wait_for` 로 텍스트 매칭.

**send 도달 검증** (필수):
fetch return 후 즉시 docker log 확인:
```bash
docker logs --tail 50 polestar-app-chatai-1 2>&1 | grep "MainStream\] 시작.*query=<query 일부>" | tail -1
```
없으면 PARTIAL/FAIL 마킹 + 다음 query 진행.

## 2a. 병렬 send — `--parallel-send=N` 옵션 (옵션 A)

§2 의 단일 send 패턴 외에, N 개 query 를 **하나의 evaluate_script 안에서 `Promise.all`
로 동시 fetch** 하는 패턴. Runner stage 의 query × duration 직렬 합계가 bottleneck
일 때 사용. screenshot/log capture 는 어차피 chrome 의 single page 라 sequential.

### 왜 옵션 A (subagent 분리 X)

- **chrome MCP 는 단일 browser 인스턴스** — 여러 subagent 가 동시 호출 시 navigate/
  take_screenshot 의 race condition 위험. 단일 page 안 fetch 동시는 정상 동작.
- evaluate_script Promise.all 이 가장 단순 + chrome 호환 명확.
- subagent 분리 (옵션 C) 는 결국 navigate/screenshot 단계에서 main 으로 모아 sequential
  처리해야 하므로 옵션 A 와 거의 동치 + spawn overhead 추가.

### 병렬 안전 한계

- **vllm-gemma container 64GB limit** — 동시 4~5 inference 까지 안전 (이전 audit)
- **chat-ai container 4GB limit** — 4 동시 SSE stream OK
- 권장 N=4. N>5 는 vllm OOM 위험.

### 코드 패턴 (evaluate_script)

```javascript
async () => {
  // queries: [{id, query}, ...]  ← Runner 가 N 개씩 chunk 로 잘라서 호출
  const queries = [/* N 개 query */];
  const startedAt = Date.now();

  const results = await Promise.all(queries.map(async ({id, query}) => {
    const requestId = `polestar-eval-${id}-${Math.random().toString(36).slice(2)}`;
    const t0 = Date.now();
    const r = await fetch("/api/chat-ap/conversation", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "locale": "ko_kr"
      },
      body: JSON.stringify({question: query, requestId})
    });
    if (!r.ok) {
      return {id, ok: false, status: r.status, elapsed_ms: Date.now() - t0};
    }
    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    let raw = "", conversationId = null;
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      raw += chunk;
      if (!conversationId) {
        const m = chunk.match(/"conversationId"\s*:\s*"([0-9a-f-]{36})"/);
        if (m) conversationId = m[1];
      }
    }
    // context bloat 방지: tail 은 window 에 저장, return 은 metadata 만
    window.__polestar_eval_tails = window.__polestar_eval_tails || {};
    window.__polestar_eval_tails[id] = raw.slice(-5000);
    return {id, ok: true, conversationId, raw_len: raw.length, elapsed_ms: Date.now() - t0};
  }));

  return {total_elapsed_ms: Date.now() - startedAt, results};
}
```

### tail 가져오기 (필요 시 별도 evaluate_script)

```javascript
(id) => window.__polestar_eval_tails?.[id] || null
```

main context bloat 방지 — N 개 raw_tail (5KB × N) 을 한 번에 return 안 받음.
필요한 query 만 별도 호출.

### screenshot/log capture — sequential

병렬 send 끝난 후, 결과의 conversationId 들을 순회하며:
1. `navigate_page(/ai-portal/<conversationId>)` → wait_for 키워드 → `take_screenshot`
2. docker log 의 conversationId / cid 추출 → file 저장
3. checkpoint file 저장 (status="done")

응답이 이미 stored conversation 에 있어서 navigate 후 빠르게 표시 (보통 1~2초).

### 진행 가이드

- query N 개 전체를 한 chunk 로: `Promise.all(N queries)` — N≤4 일 때
- query 가 더 많으면: chunks of 4 → chunk 별 sequential, chunk 안 parallel
- 동시 5개 이상 시도 시 vllm container memory 모니터링 필수 (`docker stats vllm-gemma4-cyankiwi-llm-v021`)

### 시간 단축 추정

| 시나리오 | 직렬 | parallel-send=4 |
|---|---|---|
| 3 query (easy/med/hard 15+16+77s) | 108s | max(15,16,77) = 77s |
| 10 query × 30s 평균 = 300s | 300s | 75s (4 chunks × 30s) |
| 50 query × 30s = 1500s | 25분 | 6.3분 (13 chunks × 30s) |

## 3. 응답 capture — fetch return + UI screenshot

§2 의 fetch 가 SSE 전체를 raw 로 받아옴. 거기서:
- **응답 텍스트**: `raw.tail` 의 SSE event 들 parse → `event: answer_chunk` / `data: {...}` 의 content concat
- **conversationId**: 응답에서 capture (다음 navigate 용)
- **elapsed_ms**: client-side 측정

**Screenshot — UI 에 응답 표시 후 캡쳐**:
fetch 가 끝나도 chrome 의 UI 는 그 conversation 을 안 봤음. 따라서 capture 위해서:
```
mcp__chrome-devtools__navigate_page(url=f"http://192.168.230.104:3000/ai-portal/{conversationId}")
mcp__chrome-devtools__wait_for(text=["총 ", "사용률", "조회"])  # 응답 키워드
mcp__chrome-devtools__take_screenshot(filePath=f"runs/<run-id>/<idx>-<category>-<query-id>.png")
```

navigate → chat-ap 의 history endpoint 가 stored conversation 로딩 → UI 가 표시 →
screenshot 가능. conversationId 가 fetch return 에 있으므로 deterministic.

### 카테고리 별 응답 키워드 (wait_for 용 — UI 표시 확인)

```python
keywords_per_category = {
    "inventory": ["서버명", "총 ", "건"],
    "live-state": ["%", "상위", "TOP"],
    "threshold-breach": ["%", "초과", "미초과"],
    "trend": ["시간", "그래프", "차트"],
    "alarm-management": ["Critical", "심각도", "활성", "알람"],
    "rca": ["원인", "후보", "분석"],
    "change-mgmt": ["변경요청", "ITG", "등록"],
    "cross-domain": ["서버명", "CPU", "메모리", "총 "],
    "memory-application": ["사장님", "보스", "님", "안녕"],
    "conversation-flow": ["서버", "결과"]
}
```

### 응답 텍스트 추출 (보강 — main panel DOM 에서 한 번 더)

```javascript
() => document.querySelector('main')?.innerText.slice(0, 5000) || ""
```

UI navigate 후 위 script 로 DOM 텍스트 capture → §2 의 raw tail 과 비교 / merge.

## 4. Backend log 추출 (target=104 만)

```bash
# cid 추출 — chat-ai 의 첫 응답 후 log
docker logs --since "<start_time>" --until "<end_time>" polestar-app-chatai-1 2>&1 \
  | grep -E "cid=<UUID>" \
  > runs/<run-id>/<idx>-<category>.log
```

cid 는 응답 직후 docker logs 에서 마지막 "cid=" 패턴으로 추출.

## 5. 멀티턴 (conversation-flow)

- 같은 대화 (새 대화 시작 안 함)
- 각 turn 마다 fill + send + wait_for
- 2nd turn 의 응답이 1st turn 의 context 반영하는지 확인

## 6. 실패 처리

- wait_for timeout 시 PARTIAL 또는 FAIL 로 마킹 + 다음 query 진행
- chrome-devtools error 시 한 번 재시도 + 그래도 실패 시 skip + 사용자 알림
- 모든 query 끝나면 누락 / fail list 사용자에게 보고

## 7. 데이터 보존

각 query 의 결과:
```
runs/<run-id>/
├── queries.json              # Challenger 산출 + Runner 결과 + Verifier 평가 통합
├── 01-inventory-e01.png
├── 01-inventory-e01.log
├── 01-inventory-e01.txt      # 응답 텍스트
├── ...
└── report.md                 # 최종 평가 리포트
```

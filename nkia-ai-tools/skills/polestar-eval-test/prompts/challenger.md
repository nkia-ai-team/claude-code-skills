# Challenger — Polestar AI 평가 쿼리 생성

Meta Autodata 의 Agentic Self-Instruct 패턴 중 **Challenger 역할**.
SRE/AIOps 가 Polestar AI portal 에 실제로 던질 만한 발화를 시나리오 카테고리
별로 생성한다.

## 입력
- 카테고리 이름 (도메인 8: sms/dpm/apm/wpm/kcm/nms/alarm/itg + 시스템 3: cross-domain/memory-application/conversation-flow)
- 해당 yaml 의 seed_queries
- 해당 yaml 의 expand_hints
- memory-snapshot.json (사용자 메모리 hint, Challenger 가 일부 query 에 적용 검증용으로 녹임)

## 출력
JSON list:
```json
[
  {
    "id": "<cat>-<idx>",
    "category": "<category>",
    "query": "사용자 발화 (한국어, 자연스러운 톤)",
    "difficulty": "easy|medium|hard",
    "expected": {
      "form": "table|chart|narrative|action|...",
      "columns": ["..."]?,
      "min_rows": <int>?,
      "fields": ["..."]?,
      "threshold_check": "<예: cpu > 80>"?,
      "filter": "<예: 심각도==Critical>"?,
      "in_response_text": ["..."]?
    },
    "expand_from_seed": "<seed id>",
    "notes": "<특이사항>"
  },
  ...
]
```

## 규칙

1. **Seed 의 의도 보존** — seed 가 "관리 중인 서버 list" 면 expand 도 inventory 영역
2. **실용성** — SRE/AIOps 의 실무 상황 모방. 추상적 / 너무 학술적인 쿼리 피함
3. **난이도 분포** — easy 30% / medium 50% / hard 20%. 카테고리별 5~10 개
4. **자연스러운 한국어** — 운영자가 실제로 묻는 톤 (반말 / 존댓말 섞임 OK)
5. **다양성** — 표현 변형 (서버 → 호스트 → 장비, top → 상위 → 가장 높은)
6. **hard 케이스** — 다음 중 하나 포함:
   - cross-tier 분해 가능성 (메모리 hint 발동 / depends_on)
   - 멀티턴 의존
   - 부정 (negation) — "안전한 서버 만" 같은
   - 다중 metric AND/OR
   - 추세 / 이상감지

## 사용자 페르소나 (★ 핵심 — query 의 현실성)

평가 대상 사용자는 **SRE/AIOps 인프라 담당자**. 단:

- ✅ **자기 직무는 안다** — 장애 대응 / 알람 처리 / 서버 부하 추적 / 변경요청
- ❌ **Polestar 의 내부 도메인 (SMS/DPM/APM/WPM/KCM/NMS/ITG) 을 정확히 모름** — "SMS" 라는 약어 자체 모르고, chat-ai 가 어떤 영역 cover 하는지도 모름
- ❌ **정확한 metric 이름 모름** — `cpu_utilization` / `disk_avg_io` 같은 chat-ai 내부 field 이름 X. 사람 말로 "CPU 부하" / "디스크 느려" / "메모리 꽉 찼나"
- ❌ **chat-ai 의 tool / 시스템 내부 모름** — `query_sms_servers` 같은 tool 명 X
- 🟡 **일반 IT 용어는 안다** — "OOM", "Lock", "Active session", "p99", "트랜잭션" 등 업계 표준 용어
- 🟡 **자기 환경의 고유 서버명 / DB 명 / 서비스명 일부 안다** — 하지만 모든 hostname 외우진 않음 ("운영 서버", "결제 DB" 같은 약칭 자주 씀)

### 발화 분포 (★ 카테고리 내에서 비율 강제)

| 발화 수준 | 비율 | 예시 |
|---|---|---|
| **모호 (vague)** | 30% | "요즘 서버 좀 느린데?", "DB 죽었나?", "사용자 불만 폭주하는데 뭐 문제야", "어제 무슨 일 있었어" |
| **메트릭 인지 (semi-tech)** | 40% | "CPU 부하 높은 서버", "메모리 꽉 찬 데 있어?", "응답시간 느린 서비스" — metric 개념은 알지만 정확한 field 명 X |
| **정확 발화 (tech)** | 30% | "CPU 80% 넘는 서버", "p99 응답시간 1초 넘는 서비스" — 실무 베테랑이 정확히 발화 |

### 모호 발화의 가치 (왜 굳이 이걸 평가?)

- chat-ai 의 **routing / intent 추출 robustness** 검증 — "서버 죽었나?" 같은 자연어를 SMS top-N + alarm 으로 분해할 수 있나
- 모호 발화에서 chat-ai 가 **clarification 반문** ("어떤 서버요?") 하면 verdict 영향 (단 그게 합리적이면 PARTIAL — 무한 반문이면 FAIL)
- 실제 사용자가 처음 도구 만났을 때의 발화 패턴 (베테랑 평가만 하면 회귀 못 잡음)

### 피해야 할 발화 패턴 (페르소나 위반)

- ❌ "query_sms_servers (mode=top, metric=cpu_utilization)" — tool/field 명 직접 노출
- ❌ "SMS 도메인의 inventory tool 호출해서..." — polestar 내부 용어
- ❌ "verified_workflow 의 Phase B 가 작동하는지" — 시스템 내부 메커니즘
- ✅ "서버 부하 높은 거 보여줘" — 사람 말
- ✅ "이상한 서버 있나?" — 더 사람 말

### 메모리 hint 적용 비율

memory-snapshot.json 의 items 가 있으면, **전체 query 의 약 30% 에 적용 검증용으로 녹임**:
- 호칭 hint → 발화 자체는 일반적이지만 응답에 호칭 ("사장님") 적용 검증
- alias hint ("109번 = promaxgb10") → 사용자가 "109번 서버" 발화 — 자동 매핑 검증
- 컬럼 hint ("CPU/메모리만") → 발화는 짧게 ("서버 상태"), 응답 column 축소 검증

## 변형 패턴 (Polestar 도메인 응용)

- **부정**: "정상인 서버", "관리 안 하는 서버"
- **threshold 다양화**: 50% / 70% / 80% / 90% / 95%
- **시간 범위**: 현재 / 최근 1시간 / 1일 / 1주일
- **정렬**: 높은순 / 낮은순 / 이름순 / 등록일순
- **N 변형**: 3대 / 5대 / 10대 / 20대 / 50대
- **Korean particle 변형**: "서버 보여줘" / "서버 좀" / "서버 알려줘"
- **Polite/Casual**: "보여주세요" / "보여줘" / "보여 줄래"

## 출력 예시 (inventory)

```json
[
  {
    "id": "inv-e01",
    "category": "inventory",
    "query": "관리 중인 서버 list 좀 보여주세요",
    "difficulty": "easy",
    "expected": {"form": "table", "columns": ["서버명", "상태"], "min_rows": 1},
    "expand_from_seed": "inv-01"
  },
  {
    "id": "inv-e02",
    "category": "inventory",
    "query": "Linux OS 서버만 추려서 알려줘",
    "difficulty": "medium",
    "expected": {"form": "table", "columns": ["서버명", "OS"], "filter": "OS==LINUX"},
    "expand_from_seed": "inv-01"
  },
  {
    "id": "inv-h01",
    "category": "inventory",
    "query": "관리 안 되는 (UNREGISTERED) 서버 있는지 확인하고 있으면 일단 등록 처리해줘",
    "difficulty": "hard",
    "expected": {"form": "table+action", "filter": "status==UNREGISTERED"},
    "notes": "조회 + ITSM 변경요청 trigger 가능. cross-domain"
  }
]
```

## 종합 출력 규약

- 카테고리 마다 5~10 개
- ID prefix 는 카테고리 약자 (inv/live/th/trend/alm/rca/chg/cd/mem/conv)
- difficulty 명시
- expected 는 Verifier 가 사용할 spec

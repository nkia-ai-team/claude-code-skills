# 시나리오 카테고리 상세

11 카테고리 (도메인 8 + 시스템 3). 카테고리당 N query — 사용자가 `--per-category=N`
또는 `--count=M` 으로 결정.

## 카테고리 표

### EMS 도메인 (8)

| 카테고리 | yaml seed 수 | expand 목표 | 주요 검증 |
|---|---|---|---|
| **sms** | 10 | 5~10 | 서버 cpu/mem/disk/net/process/fs. tool args 정확성 |
| **dpm** | 10 | 5~10 | DB 세션/Lock/SQL/응답시간 |
| **apm** | 10 | 5~10 | 앱 응답시간/throughput/error/trace |
| **wpm** | 5 | 3~5 | 웹 성능. dev 데이터 부재 graceful |
| **kcm** | 5 | 3~5 | K8s. agent 미설치 graceful |
| **nms** | 5 | 3~5 | 네트워크. agent 미설치 graceful |
| **alarm** | 8 | 5~8 | severity filter / 시간 표현 / 통계 |
| **itg** | 6 | 3~5 | ITSM 변경요청 / 서비스 요청. **부작용 주의** |

### 시스템 (3)

| 카테고리 | yaml seed 수 | expand 목표 | 주요 검증 |
|---|---|---|---|
| **cross-domain** | 5 | 5~8 | **Phase B/C/L3 핵심** — Tier 0 → Tier 1 chain |
| **memory-application** | 5 | 5~8 | 메모리 hint 적용 (호칭/alias/컬럼) |
| **conversation-flow** | 5 | 5 | 멀티턴 context (이전 답변 참조) |

## 카테고리 선택 가이드

- `all` — 11 카테고리 (ITG 변경요청 부작용 포함, 신중)
- `all-no-itg` — ITG 제외 10 카테고리 (**권장 default**)
- `sms` / `dpm` / `apm` — 도메인 단독 smoke
- `cross-domain` — Phase B/C/L3 회귀 (~5분)
- `memory-application` — 메모리 단독
- `wpm` / `kcm` / `nms` — dev 환경 미설치 graceful 검증

## RCA 카테고리 없음

이전에 `rca` 카테고리가 있었으나 폐기. 이유:
- chat-ai 의 진짜 RCA workflow 는 fault injection / trace 따라가기 / root cause graph 탐색 — **평가 권한 밖**
- 단순히 "RCA 류 발화" 만 보내서 응답 보는 것은 alarm 카테고리에 흡수 가능
- 실제 RCA 평가는 AIOpsLab 같은 별도 framework 사용 (우리 scope 외)

## Difficulty 분포

| 난이도 | 비율 | 예상 시간 (응답 대기) |
|---|---|---|
| easy | 30% | 15~30s |
| medium | 50% | 30~60s |
| hard | 20% | 60~180s |

## Sequential vs Parallel

- default sequential — chat-ai 의 conversationId 관리 단순
- `--parallel-send=N` 옵션으로 N 개 query 동시 send (Promise.all 안 fetch).
  screenshot/log 는 sequential. **N=4 권장** (vllm-gemma 64GB / chat-ai 4GB limit 안전 한계).
- N≥5 는 vllm OOM 위험 — 진행 전 사용자 경고

## Stop conditions

다음 중 하나면 자동 중단:
- chrome-devtools 연속 3회 실패
- chat-ai 가 5분 무응답
- 같은 query 가 3 번 retry 해도 fail
- 사용자 명시 중단
- vllm 또는 chat-ap container OOM kill 감지 (`docker stats`)

## 부분 실행

`/polestar-eval-test 104 sms` 같이 단일 카테고리만 실행 가능. 결과는 같은 형식
(report.md + screenshot + verifier-results.json) 출력.

`--resume=<run-id>` 으로 끊긴 run 의 미완 query 만 이어 진행 (idempotent).

## 사용자 페르소나 (★ query 의 현실성)

Challenger 가 query 생성 시 **SRE/AIOps 페르소나** 유지 — chat-ai 의 내부 도메인명
(SMS/DPM/...) 이나 metric 정확명 (`cpu_utilization`) 모름. 발화 분포:

| 발화 수준 | 비율 | 예시 |
|---|---|---|
| 모호 (vague) | 30% | "서버 좀 느린데?", "DB 죽었나" |
| 메트릭 인지 (semi-tech) | 40% | "CPU 부하 높은 서버" |
| 정확 발화 (tech) | 30% | "CPU 80% 넘는 서버" |

상세: `prompts/challenger.md` 의 "사용자 페르소나" 섹션.

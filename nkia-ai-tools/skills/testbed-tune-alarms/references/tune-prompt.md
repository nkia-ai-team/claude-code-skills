# 임계치 결정 LLM Prompt 템플릿

`testbed-tune-alarms` 가 메트릭 분포 + sre-baseline + 도메인 → 권고 임계치 추론 시 사용.

---

## 인라인 호출 (default)

오케스트레이터/스킬 자체 컨텍스트에서 추론. 무거운 케이스 (자원 50+ × 메트릭 10+) 만 testbed-engineer agent 위임 검토.

---

## Prompt 템플릿

다음 형식으로 LLM 에 보냄 (단순 문자열 substitution):

```
당신은 SRE 엔지니어입니다. Polestar10 알람 임계치를 결정합니다.

## 컨텍스트

서비스: <service_name>
도메인: <domain>  (예: 결제·정산 / 주문·재고 / 검색·조회 / ...)
testbed_name: <testbed_name>

## 흐르는 메트릭 분포 (지난 <window_min> 분)

<for each (resource, measurement)>
| resource | measurement | unit | p50 | p95 | p99 | max | std |
| <r> | <m> | <unit> | <p50> | <p95> | <p99> | <max> | <std> |
</for>

## 현재 적용된 임계치

<for each existing policy>
- <resource>.<measurement>: LEVEL1=<v1> LEVEL2=<v2> LEVEL3=<v3> LEVEL4=<v4>
</for>

## SRE Baseline (참고)

<infra/testbed/alert-policies/sre-baseline.md 의 해당 도메인 섹션 인용>

## 요구

각 (resource, measurement) 에 대해:
1. 권고 임계치 LEVEL1~4
2. 근거 (한 줄, 100자 이내)
3. 우선순위: high (즉시 변경 권고) / medium (검토 후 변경) / low (현재 OK)

출력 형식:

```yaml
recommendations:
  - resource: <r>
    measurement: <m>
    units: <unit>
    levels:
      level1: <v1>
      level2: <v2>
      level3: <v3>
      level4: <v4>
    rationale: "<한 줄 근거>"
    priority: high|medium|low
    change: "<현재 → 권고 요약>"
```

## 결정 룰

- 평소 분포 + 도메인 SLA + sre-baseline 3가지 가중. baseline 만 따르지 X.
- p95 ≤ LEVEL2, p99 ≤ LEVEL3 권고 (보수적). 도메인이 외부 의존 큰 경우 (결제 외 PG 등) 권고 임계치를 baseline 보다 관대하게.
- 메트릭이 스파이크 큰 경우 (max >> p99) → max 무시하고 p99 기준. 알람 노이즈 줄임.
- 신규 정책 (현재 임계치 X) → priority=high, baseline 그대로 시작 + 도메인 보정.
- 현재 임계치가 baseline 의 2배 이상 관대하면 → priority=high, 보수적 권고.
- 현재 임계치가 baseline 의 50% 이하 보수적이면 → priority=medium, 노이즈 분석 권고 (변경 신중).
- max_alarms_per_min default 5. 자주 spike 하는 메트릭은 3 으로 줄임.

## 금지

- p99 < LEVEL2 으로 설정 (즉시 알람 폭주)
- LEVEL1 > LEVEL2 식의 monotonic 위반
- units 변경 (메트릭 catalog 의 단위 그대로 사용)
- 근거 없이 baseline 의 50% 이상 변경
```

---

## 출력 파싱

LLM 응답의 yaml 블록을 파싱하여 `policy-yaml-schema.md` 의 `individual_alarms` / `common_policies` 형식으로 매핑:

```python
import yaml

response_yaml = yaml.safe_load(llm_response_block)
for rec in response_yaml["recommendations"]:
    individual_alarms.append({
        "resource_name": rec["resource"],
        "measurement_type": rec["measurement"],
        "measurement_alias": rec.get("alias", rec["measurement"]),
        "units": rec["units"],
        "levels": rec["levels"],
        "max_alarms_per_min": rec.get("max_alarms_per_min", 5),
        "enable": True,
        "comment": rec["rationale"],
    })
```

---

## 사용자 승인 prompt 시 표시 우선순위

권고들 중 priority=high 가 가장 위. medium → low. 같은 priority 안에서는 도메인 (APM > DPM > KCM > SMS) → 자원 이름 알파벳.

---

## testbed-engineer agent 위임 시기

다음 조건 모두 만족 시 위임 고려:
- 자원 수 × 메트릭 수 > 50 (인라인 컨텍스트 부담)
- 도메인 특성 추론이 모호 (사용자가 "도메인은 자유 입력 / 신규" 답변)
- 메트릭 분포가 high variance (p99/p95 비율 > 5)

위임 prompt:
```
task: alarm-threshold-tuning
input:
  metrics_snapshot: <path>
  current_policies: <inline yaml>
  sre_baseline_excerpt: <inline>
  domain_meta: <from service-spec.yaml>
output: 위 prompt 의 yaml 형식 그대로
```

testbed-engineer 가 reading + reasoning 격리 → 결과만 부모 컨텍스트로.

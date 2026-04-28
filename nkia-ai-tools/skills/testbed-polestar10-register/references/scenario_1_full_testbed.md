# Scenario 1 — 신규 테스트베드 구축

> "테스트베드 자원 한 번에 다 등록해줘"
> "RCA 테스트베드 셋업해줘"

여러 자원을 **하나의 서비스 그룹** 으로 묶어 일괄 등록. 가장 흔한 첫 사용 흐름.

---

## Trigger 키워드

`테스트베드`, `한 번에`, `일괄`, `다`, `구축`, `셋업`, `setup`

---

## Pre-conditions

- Bootstrap 완료 ([bootstrap.md](bootstrap.md))
- 등록 대상이 agent-based 면 에이전트가 polestar10-itg collector 로 heartbeat 보내고 있어야 함 (`hostStatus:"READY"` 가 standby 에 떠야 등록 가능)

---

## Dispatch flow

```
1. 인터뷰 — 테스트베드 메타
   - 테스트베드 이름 (= 서비스 그룹 값. 기본: "RCA-Testbed")
   - 시스템 그룹 (기본: 1=Default. recipes/list-groups.md 응답에서 선택)
   - 이상감지 정책 (기본: "성능 이상감지 기본 정책")
   - 등록할 리소스 목록 (멀티 입력)

2. 서비스 그룹 사전 생성 (선택)
   recipes/service-group-tag.md  ← /api/cm/tag/value/insert
   ※ 등록 단계에서 자동 생성도 가능. 사전 insert 는 UI dropdown 노출용.

3. 리소스별 등록 — 위 메타 슬롯을 공통으로 사용
   각 리소스에 대해:
     [agent-based]
       a. recipes/list-targets.md "Standby 조회" → hostStatus:"READY" 인 agentId 추출
       b. 안 보이면 사용자에게 "에이전트 heartbeat 대기 (5~10분)" 안내 후 retry/skip
       c. recipes/add-target.md "서버 등록" Step 2  ← /api/sms/standby-hosts/register
          payload 의 serviceGroupTagValue / groupId / anomalyPolicyTagValue 에 인터뷰 슬롯 주입
     [config-only — Web URL]
       a. recipes/add-target.md "Web URL 등록" Step 1  ← /api/weburl/save
       b. 응답의 data.id 추출
       c. Step 2  ← /api/weburl/register
     [config-only — SLO]
       a. recipes/slo.md  ← register/standby → list-filter (registered:false) → register
     [TBD 타입 — DB/APM/KCM/NMS/Syslog/SQL/SNMP OID]
       UI fallback 안내 (recipes/add-target.md "UI Fallback") + 등록 후 수동 standby 조회로 검증

4. 일괄 검증
   recipes/list-targets.md 의 type 별 list-filter 로 새 자원 모두 보이는지 확인
   /api/cm/portal/configuration/count 전체 수 증가 확인

5. 보고
   - 등록 성공/실패 자원 목록
   - 사용한 서비스 그룹 / 시스템 그룹 / 이상감지 정책
   - 다음 단계 안내 (개별 알람 = 시나리오 2, 삭제 = 시나리오 4)
```

---

## 멱등성

같은 이름으로 두 번째 호출 시:

| 자원 종류 | 사전 체크 | 충돌 시 처리 |
|---|---|---|
| Web URL | `weburl/list-filter` 에서 `resourceName` 매칭 | skip / 사용자에게 prompt |
| 서버 | `sms/hosts-filter` 에서 `hostname` 매칭 | 이미 MANAGED 이면 skip |
| SLO | `cm/slo/list-filter` 에서 `name` 매칭 (registered:true/false 둘 다) | skip 또는 staging 정리 후 재등록 |
| 서비스 그룹 | `cm/tag/value/insert` 자체가 멱등 | 별도 처리 불필요 |

---

## 실패 시 부분 롤백

리소스 5개 중 3개 등록 후 4번째에서 실패한 경우:
- 자동 롤백은 하지 않음 (의도치 않은 삭제 위험)
- 사용자에게 "이미 등록된 N개 + 실패 1개 + 미시도 M개" 상태 표 보여주고:
  - 시나리오 4 (resource cleanup) 으로 부분 정리하시겠습니까?
  - 또는 4번째만 retry?
  - 또는 그대로 두고 UI 에서 마저 진행?

---

## 사용자에게 보여줄 최종 요약 예

```
✅ RCA 테스트베드 등록 완료
   서비스 그룹: RCA-Testbed (자동 생성)
   시스템 그룹: Default (id=1)
   이상감지 정책: 성능 이상감지 기본 정책

   서버 (3): plopvape-app, plopvape-db, dgx-spark
   Web URL (1): plopvape-shop probe (https://...)
   SLO (1): testbed-availability-weekly

   다음 단계 추천:
     • 개별 알람 추가:    시나리오 2 — "<자원>에 알람 걸어줘"
     • 자원 정리:          시나리오 4 — "<자원> 삭제"
```

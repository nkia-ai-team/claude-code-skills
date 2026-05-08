# `polestar10_register` — Polestar10 관리대상 등록 (KCM / APM / WPM / SMS / DPM / NMS — 사전 점검 + dispatch + PARTIAL 처리)

**조건부 적용**: `ansible_deploy` + `sanity_check` 완료 직후 read. agent install 끝난 시점.

## 9-a. 사전 점검 (testbed-polestar10-register dispatch 전)

### 1. bootstrap.yaml + .polestar10rc 일치 확인

```bash
ORG_ID=$(yq '.polestar10.organization_id' ~/.testbed-build/bootstrap.yaml)
[ -z "$ORG_ID" ] || [ "$ORG_ID" = "null" ] && {
  echo "FATAL: organization_id 가 비어있습니다. Phase 1 인터뷰가 누락한 것."
  echo "재인터뷰: ~/.testbed-build/bootstrap.yaml 의 polestar10.organization_id 채우거나 파일 삭제 후 재호출."
  exit 1
}
```

### 2. broker / collector 도달성 (Polestar10 backend → target 의 NodePort 들)

- DPM (mysql/postgres NodePort) 도달성 — `nc -zv $TARGET_HOST 30432` 또는 `30306`
- SMS broker (1883) — `nc -zv $POLESTAR10_HOST $POLESTAR10_SMS_BROKER_PORT`
- KCM backend (7575) — `nc -zv $POLESTAR10_HOST $POLESTAR10_KCM_COLLECTOR_PORT` (master Pod 가 Polestar10 KCM backend 로 push)
- 실패 시 사용자에게 표 표시 + dispatch 진행 (각 자원 register 시점에 fail 하면 자동 skip 분기)

### 3. agent install 후 standby polling delay

```bash
echo "[polestar10_register] Polestar10 backend 가 SMS/KCM/APM heartbeat 받아 standby 에 등록할 시간 확보 (60초)..."
sleep 60
```

ansible 마지막 task (agent install) 직후 즉시 register 시도하면 standby 미등록 → register API 가 빈 응답. 60초 base grace 가 필수.

⚠️ **WPM 은 더 오래 걸림** — 새 pod 의 JVM startup + `-javaagent:wpmagent.jar` 로딩 + UDP 31002 heartbeat + collector sync = 60~120초 추가. WPM 등록 분기는 60초 단발 wait 대신 **10초 간격 × 최대 30회 (5분) polling** 패턴 사용 ([scenario_1_full_testbed.md § WPM (Scouter) path](../../testbed-polestar10-register/references/scenario_1_full_testbed.md)).

## 9-b. dispatch

```
Skill: testbed-polestar10-register
  scenario: 1 (full testbed)
  context: runs/<RUN_ID>/inventory.yml + interview.yaml
```

testbed-polestar10-register 의 시나리오 1 가 [scenario_1_full_testbed.md](../../testbed-polestar10-register/references/scenario_1_full_testbed.md) 의 **WPM (Scouter) vs OTel APM 분기**, **DPM 도달성 분기**, **NMS SNMP probe 분기** 모두 포함하여 자동 진행. 결과 → `runs/<RUN_ID>/register.json`.

## 9-c. PARTIAL verdict 처리

testbed-polestar10-register 가 일부 자원 등록 실패 시 PARTIAL 반환. SKILL 은:

1. register.json 의 자원별 등록 표 사용자에게 표시 (성공 / 실패 / 미시도)
2. 실패 자원에 대해 가능한 fix 제안:
   - SMS standby 미감지 → broker connectivity 재확인 + agent restart
   - KCM standby 미감지 → `helm get values kcm-agent -n kcm-monitoring` 으로 orgId / addr 확인 + master/node Pod logs (`kubectl logs -n kcm-monitoring deploy/kcm-master-agent`) 확인 + helm rollback / upgrade
   - APM (OTel) 자동 등록 안 됨 → Polestar10 web UI 직접 안내
   - DPM mysql 도달성 X → NodePort 방화벽 / network policy 확인
3. 사용자 선택:
   - (1) 그대로 진행 (`generate_scenarios` 로) — 부분 등록 자원만으로 verify
   - (2) 등록 재시도 (특정 자원만)
   - (3) `polestar10_register` 전체 retry (60초 추가 sleep + dispatch)
   - (4) 중단 (run 보존, 사용자가 web UI 에서 보강 후 재호출)

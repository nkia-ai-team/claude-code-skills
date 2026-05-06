# Phase 4.5 — 기존 testbed 감지 게이트 (cluster 단위)

**조건부 적용**: Phase 4 (architecture 승인) 직후, Phase 5 (lock 획득) 직전에 read. 사용자 승인된 이후만 실행.

타겟 서버에 **같은 이름의 cluster** (cluster_kind=k3d 면 k3d cluster, k3s legacy 면 같은 namespace) 가 이미 떠있는지 사전 감지. 떠있으면 사용자 의도 확인.

## Step 1: cluster 존재 여부 검사

```bash
source ~/.testbed-build/runs/$RUN_ID/secrets.env
CLUSTER_NAME="${APP_SUBDIR}"   # = bootstrap.cluster.name 도출 (testbed 이름)

# k3d cluster 단위 검사 (default cluster_kind=k3d)
EXISTING_CLUSTER=$(sshpass -e ssh -o ConnectTimeout=5 \
  "${TARGET_USER}@${TARGET_HOST}" \
  "k3d cluster list -o json 2>/dev/null | jq -r '.[].name' | grep -Fx '${CLUSTER_NAME}' || true")

CLUSTER_EXISTS=$([ -n "$EXISTING_CLUSTER" ] && echo 1 || echo 0)

# (k3s legacy 케이스) — cluster_kind=k3s 면 namespace 검사 (이전 패턴 유지)
if [ "$CLUSTER_KIND" = "k3s" ]; then
  EXISTING_NS=$(sshpass -e ssh -o ConnectTimeout=5 \
    "${TARGET_USER}@${TARGET_HOST}" \
    "echo '${TESTBED_BECOME_PASSWORD}' | sudo -S /usr/local/bin/k3s kubectl get ns ${APP_NAMESPACE} -o name 2>/dev/null")
  CLUSTER_EXISTS=$([ -n "$EXISTING_NS" ] && echo 1 || echo 0)
fi
```

## Step 2: 사용자 카드 (CLUSTER_EXISTS=1 일 때만)

```python
AskUserQuestion(questions=[
  {
    "question": f"{TARGET_HOST} 에 이미 cluster '{CLUSTER_NAME}' 이 존재합니다. 어떻게 진행할까요?",
    "header": "기존 testbed 감지",
    "multiSelect": False,
    "options": [
      {"label": "장애 시나리오만 추가", "description": "deploy/agent install 모두 skip — testbed-generate-scenarios 단독 호출로 분기"},
      {"label": "다른 testbed 만들기", "description": "Phase 1 인터뷰 다시 (다른 cluster_name = 다른 testbed 이름)"},
      {"label": "기존 cluster 삭제 후 새로", "description": "k3d cluster delete <name> (또는 k3s 면 kubectl delete ns) 후 정상 진행 — 데이터 / DB 모두 사라짐 ⚠️"},
      {"label": "그대로 재배포 (idempotent)", "description": "현재 cluster 위에 ansible apply — helm upgrade --install 이 변경분만 적용"}
    ]
  }
])
```

## Step 3: 선택별 분기

- (1) → Phase 5~9 skip, Phase 10 (generate-scenarios) 로 점프
- (2) → Phase 1 으로 복귀
- (3) → k3d: `sshpass -e ssh ${TARGET_USER}@${TARGET_HOST} "k3d cluster delete ${CLUSTER_NAME}"` 후 Phase 5 / k3s: `kubectl delete ns ${APP_NAMESPACE} --wait=true`
- (4) → 그대로 Phase 5 진행 (helm upgrade --install 이 idempotent)

`CLUSTER_EXISTS=0` (깨끗) 이면 카드 자체 skip → Phase 5 직행.

## Step 4: port 충돌 사전 점검 (다중 testbed 동시 운영 시)

같은 호스트에 다른 testbed 가 떠있는데 cluster_name 만 다르면 — k3d_api_port (6443) / scenario_runner_port (8091) 등이 충돌 가능. 인터뷰가 다른 port 받지 않았다면 사용자에게 안내:

```bash
PORTS_IN_USE=$(sshpass -e ssh ${TARGET_USER}@${TARGET_HOST} "ss -tlnp 2>/dev/null | grep -E ':6443|:8091' | wc -l")
[ "$PORTS_IN_USE" -gt 0 ] && warn "host port 충돌 가능 — 다른 cluster 가 같은 port 사용 중. 인터뷰 다시 + 다른 port 입력 필요"
```

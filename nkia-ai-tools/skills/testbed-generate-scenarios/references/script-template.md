# Bash 스크립트 표준 골격

`testbed-generate-scenarios` 가 시나리오 스크립트를 작성할 때 따르는 표준 구조. 인스턴스화된 모든 시나리오 스크립트는 본 골격을 만족해야 함 (rca-scenario-runner 와의 인터페이스 보장).

---

## 필수 요소

```bash
#!/bin/bash
# scenario-<NN>-<slug>.sh
#
# 패턴: <카탈로그 카드 이름>
# 도메인: <e-commerce / banking / ...>
# 생성: testbed-generate-scenarios v1
#
set -euo pipefail
trap cleanup EXIT

# === 환경 변수 (env override 가능) ===
NAMESPACE="${NAMESPACE:-<from service-spec.yaml>}"
SERVICE_API="${SERVICE_API:-<from service-spec.yaml>}"
# ... 패턴 카드의 치환 슬롯 변수들

cleanup() {
  echo "[INFO] cleanup: <원상복구 절차 한 줄>"

  # 1) 시나리오가 직접 만든 seed/mock state 정리 (기존 패턴)
  # psql_exec -c "DELETE FROM <table> WHERE <seed-id-filter>;"

  # 2) ⚠️ (CAPACITY-GATED 도메인 전용) lifecycle terminal 일괄 전이.
  #    scenario_hints 의 capacity_table / lifecycle_active_state / lifecycle_terminal_state 가
  #    채워진 testbed 만 합성. 시나리오 도중 들어온 real traffic 이 만든 row 도 회수.
  #    capacity-gated 가 아닌 도메인 (단순 이벤트 적재) 은 본 라인 제외.
  # psql_exec -c "UPDATE <capacity_table> SET status='<lifecycle_terminal_state>' WHERE status='<lifecycle_active_state>';"

  # 3) 임시 파일 정리
  # rm -f /tmp/<scenario>-*.log

  # 멱등하게: 이미 정리된 상태에서도 에러 없이 종료
  echo "[OK] cleanup complete"
}

# Cleanup 모드 분기
if [ "${1:-}" = "cleanup" ]; then
  cleanup
  exit 0
fi

echo "[INFO] starting $0"

# === 트리거 ===
# 1. <장애 유발>

# 2. <부하 또는 측정 윈도우>

echo "[OK] done"
```

---

## 강제 규약 (rca-scenario-runner 호환)

1. **`trap cleanup EXIT`** 첫 줄에 가까이. SIGKILL 은 못 잡지만 SIGTERM/정상 종료 cleanup 보장.
2. **`set -euo pipefail`** — 실패 즉시 중단. unset 변수 에러.
3. **두 모드 지원**:
   - `./script.sh` (no arg) → 시나리오 실행
   - `./script.sh cleanup` → cleanup 만 실행
4. **종료 메시지**:
   - 정상 완료 시 `[OK] done` 라인 (rca-scenario-runner 의 test_api.py 가 검증)
   - cleanup 완료 시 `[OK] cleanup complete` 라인 (`test_cleanup_mode` 가 검증)
5. **stdout 가 사용자에게 streaming**: 진행 상황은 `[INFO] ...` 형식으로. 디버깅 정보는 stderr.
6. **chmod +x** — rca-scenario-runner 가 직접 실행하므로 실행권한 필수.

---

## NAMESPACE / SERVICE_API 결정

service-spec.yaml 의 `target` 섹션에서 가져옴:
```yaml
target:
  namespace: rca-testbed
  api_base: "http://127.0.0.1:30080"
```

→ 스크립트에서:
```bash
NAMESPACE="${NAMESPACE:-rca-testbed}"
SERVICE_API="${SERVICE_API:-http://127.0.0.1:30080}"
```

다른 testbed (다른 namespace) 에 같은 시나리오 스크립트를 공유하려면 env 로 override:
```bash
NAMESPACE=rca-testbed-v2 ./scenario-01.sh
```

---

## kubectl 호출

호스트 kubeconfig 마운트 가정:
```bash
# rca-scenario-runner 의 docker-compose.yml 이 마운트한 kubeconfig.
# KUBECONFIG env 가 이미 set 돼있으면 그대로, 아니면 ssh user 의 default 경로로 fallback.
# 사용자 환경마다 username 다르므로 hardcoded /home/<user> X — env 우선 + $HOME/.kube/config fallback.
export KUBECONFIG="${KUBECONFIG:-${HOME}/.kube/config}"

kubectl -n "$NAMESPACE" exec "$POD" -- ...
```

(rca-scenario-runner CLAUDE.md `# Volume Mounts` 의 KUBECONFIG_HOST_PATH 참조)

---

## docker 호출 (호스트 컨테이너 조작)

scenario-runner 의 `/var/run/docker.sock` 마운트로 호스트 daemon 직접 호출 가능:
```bash
docker stop pg-mock
docker start pg-mock
```

**주의**: 보안상 신뢰 환경 한정. CLAUDE.md `Known Gotchas` #3 참조.

---

## 부하 도구

기본은 `curl`. 정밀한 RPS 가 필요하면:

| 도구 | 설치 | 사용 |
|---|---|---|
| curl | 기본 | `for i in $(seq 1 N); do (curl ... &) ; done; wait` |
| hey | `go install github.com/rakyll/hey@latest` | `hey -n 1000 -c 50 -m POST -d '...' <url>` |
| wrk | `apt install wrk` | `wrk -t4 -c200 -d60s -s post.lua <url>` |
| vegeta | `go install github.com/tsenart/vegeta@latest` | RPS pacing 정밀 |

스크립트 안에 도구 prereq 명시 (없으면 fail-fast):
```bash
command -v hey >/dev/null || { echo "hey not installed"; exit 2; }
```

---

## 멱등 cleanup 작성 룰

cleanup 은 **여러 번 호출되어도 같은 결과**:
- `kubectl patch` 으로 변경한 리소스 → 원래 값으로 다시 patch (`|| true` 로 이미 그 값이면 무시)
- `docker stop` 한 컨테이너 → `docker start` (`|| true` 로 이미 running 이면 무시)
- 백그라운드 프로세스 → `pkill -P $$` 또는 PID 파일 사용
- 임시 파일 → `rm -f` (`-f` 로 없는 파일 OK)

cleanup 안에 `kubectl rollout status --timeout=60s` 같이 wait 넣으면 사용자 체감 길어짐. 60초 안에 끝나는 작업만.

---

## 안티패턴 (피하기)

- `kubectl delete deployment` — 삭제는 cleanup 으로 복구 어려움. patch / restart 사용.
- `iptables` 으로 호스트 방화벽 영구 변경 — flush 안 하면 다음 시나리오 영향.
- `sleep` 으로 시나리오 길이 늘리기 — estimated_duration_sec 와 일치하지 않음. 측정 윈도우는 부하 자체로 채움.
- 사용자 자격증명 (DB password 등) 을 스크립트에 hardcode — env var 또는 K8s secret 으로.
- DB 데이터 영구 변경 (DROP TABLE 등) — 변경하더라도 cleanup 에서 원복 가능해야.

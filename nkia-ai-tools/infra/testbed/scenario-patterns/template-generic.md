# Pattern: <패턴 이름>

> 신규 패턴 작성 시 본 파일을 복사하여 사용. 모든 섹션을 채워야 `testbed-generate-scenarios` 가 인스턴스화 가능.

## Summary
한 줄. 트리거 + 결과를 짧게.

## 트리거 메커니즘
- 어떤 조작으로 장애를 유발하는지 (process kill / docker stop / kubectl patch / iptables / SQL injection 등)
- 단계별 동작 명시

## propagation (root → user-visible)
1. (root cause) 어디서 시작
2. 어떤 컴포넌트로 전파
3. 어떤 메트릭이 첫 번째로 이상치
4. 캐스케이드 경로
5. 사용자 체감 증상

## 적합한 도메인
- 어떤 비즈니스 도메인에 의미 있는지 (e-commerce / banking / IoT / messaging / ...)
- 환경 prereq (K8s 필요? Docker 권한 필요? metrics-server 필요? 외부 mock 필요?)

## bash 스크립트 골격
```bash
#!/bin/bash
# scenario-XX-<name>.sh
set -euo pipefail
trap cleanup EXIT

# === 인스턴스 시 치환할 변수 (환경/도메인별) ===
NAMESPACE="${NAMESPACE:-rca-testbed}"
TARGET_<X>="${TARGET_X:-<value>}"
LOAD_DURATION_SEC="${LOAD_DURATION_SEC:-120}"
# ...

cleanup() {
  echo "[INFO] cleanup: <원상복구 절차>"
  # 멱등 cleanup. 이미 정리된 상태에서도 에러 없이 끝나야 함.
  echo "[OK] cleanup complete"
}

if [ "${1:-}" = "cleanup" ]; then
  cleanup
  exit 0
fi

echo "[INFO] starting $0"

# 1. <장애 트리거>

# 2. <부하 또는 측정 윈도우>

echo "[OK] done"
```

## expected_alarms (기본값)
- 어떤 카테고리 알람이 발화해야 하는지
- 임계치 권고 단위 (LEVEL1 ~ LEVEL4)
- 어떤 자원에서 측정되어야 하는지

## cleanup 안전성 + 부작용
- 안전: cleanup 이 멱등하게 동작하는 근거
- 부작용 1: 데이터/구성 영향 (있다면)
- 부작용 2: Polestar10 에이전트/알람 영향 (있다면 — 예: KCM 알람 disable, WPM 재등록)
- SIGKILL 안전망: trap 미동작 시 수동 정리 명령

## 변형 포인트
- 어떤 변수를 도메인별로 치환할지
- 어떤 매개변수로 강도를 조정할지
- 사용 가능한 부하 도구 옵션

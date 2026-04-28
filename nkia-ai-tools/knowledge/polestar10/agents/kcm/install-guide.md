# KCM Agent 설치 가이드

## 개요

KCM(Kubernetes Cluster Monitor) 에이전트는 대상 K8s 클러스터에 DaemonSet 으로 배포되어 노드/파드/메트릭서버 지표를 수집기로 송신합니다. 네이티브 Go 바이너리라 CPU 아키별 이미지가 필요합니다.

## 설치 개요 (AMD64)

1. `install-spec.yaml` 의 `detection_command` 로 클러스터에 이미 KCM DaemonSet 이 있는지 확인합니다.
2. 배포 서버(104) 의 이미지 레지스트리에서 `polestar10-kcm:<ver>-amd64` 이미지를 가져옵니다.
3. 매니페스트 `kcm-daemonset.yaml` 의 `image:` 를 해당 태그로 설정한 뒤 `kubectl apply -f` 합니다.
4. `kubectl get ds -A | grep kcm` 에서 DESIRED/AVAILABLE 이 일치하면 정상입니다.

## 설치 개요 (ARM64) — cross-build 필수

ARM 전용 베어메탈/엣지 클러스터(예: Raspberry Pi, Ampere, AWS Graviton) 에는 **qemu-user-static 기반 에뮬레이션 빌드가 실패**하는 케이스가 반복적으로 나타납니다. 실제 운영에서는 **AMD64 빌드 머신에서 cross-build** 로 이미지를 만든 뒤 ARM 클러스터에 `scp` 나 레지스트리 push 로 전달하는 방식을 사용합니다.

### 소스 및 빌드 절차

- 소스 URL: `https://github.com/polestar/kcm-agent`  *(내부 GitLab 미러에서 관리)*
- 빌드 도구: Go 1.22+, `docker buildx`, (옵션) `docker-buildx-cross` 이미지
- 빌드 명령 (AMD64 머신에서 실행):
  ```sh
  docker buildx create --use --name kcm-cross || true
  docker buildx build \
    --platform linux/arm64 \
    --tag polestar10-kcm:<ver>-arm64 \
    --output type=docker \
    .
  ```
- 생성된 이미지를 tar 로 내보냅니다.
  ```sh
  docker save polestar10-kcm:<ver>-arm64 -o kcm-arm64.tar
  scp kcm-arm64.tar <arm-cluster-node>:/tmp/
  ssh <arm-cluster-node> 'sudo ctr -n k8s.io images import /tmp/kcm-arm64.tar'
  ```
- `kcm-daemonset.yaml` 의 `image:` 를 `polestar10-kcm:<ver>-arm64` 로 세팅하고 `kubectl apply` 합니다.

## 보강 (메뉴얼 바깥의 실전 지식)

- **qemu-user-static 에뮬레이션은 KCM 에 충분하지 않다**: 일부 syscall 과 cgroup v2 접근에서 SEGV 가 발생합니다. 따라서 KCM ARM 은 반드시 native cross-build 로 빌드합니다.
- **metrics-server 의존**: K3s 기본 설치에는 metrics-server 가 없어 KCM 의 Pod CPU/MEM 수집이 빈 값으로 돌아옵니다. 설치 전에 metrics-server 를 `--kubelet-insecure-tls` 플래그와 함께 배포하세요. 이 조건이 빠지면 HPA + KCM 알람이 모두 막힙니다.
- **RBAC**: `nodes/proxy`, `pods`, `services` 에 대한 `get/list/watch` 가 필요합니다. 제공된 `kcm-rbac.yaml` 을 함께 `apply` 합니다.

## 문제 해결

- 수집 누락은 대개 `metrics-server` 미설치, `qemu` 에뮬, RBAC 누락 중 하나입니다.
- `kubectl -n kcm logs -l app=kcm-agent --tail=200 | grep -iE "error|denied"` 로 1차 원인을 좁힙니다.

# KCM Agent 설치 가이드

## 개요

KCM(Kubernetes Cluster Monitor) 에이전트는 대상 K8s 클러스터에 DaemonSet 으로 배포되어 노드/파드/메트릭서버 지표를 수집기로 송신합니다. 네이티브 Go 바이너리라 CPU 아키별 이미지가 필요합니다.

## 설치 개요 (AMD64) — native 바이너리

1. `install-spec.yaml` 의 `detection_command` 로 클러스터에 이미 KCM DaemonSet 이 있는지 확인합니다.
2. 배포 서버(104) 의 이미지 레지스트리에서 `polestar10-kcm:<ver>-amd64` 이미지를 가져옵니다.
3. 매니페스트 `kcm-daemonset.yaml` 의 `image:` 를 해당 태그로 설정한 뒤 `kubectl apply -f` 합니다.
4. `kubectl get ds -A | grep kcm` 에서 DESIRED/AVAILABLE 이 일치하면 정상입니다.

## 설치 개요 (ARM64) — 타겟 호스트에서 직접 소스 빌드

ARM 전용 클러스터(예: Ampere, AWS Graviton, NVIDIA Grace) 에서는 **타겟 호스트에서 직접 소스 빌드** 방식을 채택합니다. 별도의 AMD64 빌드 머신이나 cross-build 파이프라인을 운영하지 않습니다 (운영 단순화 + qemu-user-static 으로는 KCM 의 일부 syscall/cgroup v2 접근이 SEGV 로 실패하는 케이스가 반복).

### 사전 요구사항 (ARM 타겟 호스트)

- gcc (`apt install -y build-essential` 또는 `dnf groupinstall -y "Development Tools"`)
- Go 1.22+ (`apt install -y golang-1.22-go` 또는 [Go 공식 tarball](https://go.dev/dl/))
- 타겟에서 직접 docker build 할 거면 docker daemon 이 떠 있어야 함 (K3s 의 내장 containerd 만 쓰는 환경이면 `nerdctl build` 로 대체)
- 타겟 디스크 여유 약 1.5GB (소스 + Go 모듈 캐시 + 이미지 레이어)

### 소스 및 빌드 절차

소스 URL: 사내 GitLab의 `lucida-kcmagent` 저장소 *(외부 미러 없음, 사내망 only)*. 정확한 URL은 운영팀 또는 사내 위키 참조 (보안상 본 문서엔 미기재). ansible 사용 시 env `KCM_SOURCE_REPO` 또는 inventory `kcm_source_repo` 로 주입.

```sh
# 1) 운영 PC 에서 git clone (사내 GitLab 인증 필요)
export KCM_SOURCE_REPO=<internal gitlab url>
git clone "${KCM_SOURCE_REPO}.git"
scp -r lucida-kcmagent <arm-target>:/tmp/

# 2) ARM 타겟에서 빌드 (10~15분)
ssh <arm-target>
cd /tmp/lucida-kcmagent
go build -o build/kcm-agent ./cmd/agent

# 3) 컨테이너 이미지 빌드 (타겟이 ARM 이므로 결과물은 자동으로 linux/arm64)
docker build -t polestar10-kcm:<ver>-arm64 .

# 4) K3s 의 containerd 가 docker 데몬과 분리돼 있으면 import 단계 필요
docker save polestar10-kcm:<ver>-arm64 -o /tmp/kcm-arm64.tar
sudo ctr -n k8s.io images import /tmp/kcm-arm64.tar

# 5) 매니페스트 image 태그 세팅 후 apply
sed -i "s|<KCM_IMAGE>|polestar10-kcm:<ver>-arm64|" kcm-daemonset.yaml
kubectl apply -f kcm-daemonset.yaml -f kcm-rbac.yaml
```

### 빌드 자동화 (Ansible 롤)

`infra/testbed/playbooks/roles/agent-kcm/` 에서 위 절차를 자동화합니다 (gcc/Go 사전 설치 → git clone → scp → 타겟 빌드 → image import → manifest apply). `target_arch=arm64` 일 때만 분기.

## 보강 (메뉴얼 바깥의 실전 지식)

- **qemu-user-static 으로 KCM 을 돌리지 마세요**: 일부 syscall 과 cgroup v2 접근에서 SEGV 가 반복적으로 발생합니다. 타겟 빌드 채택의 1차 사유.
- **별도 AMD64 빌드 머신을 두지 않은 이유**: 빌드 머신 운영 비용 + cross-build 산출물 신뢰성 검증 비용이 타겟 빌드 10~15분 비용보다 큽니다. 빌드 1회당 한 번만 발생하니 trade-off 유리.
- **metrics-server 의존**: K3s 기본 설치에는 metrics-server 가 없어 KCM 의 Pod CPU/MEM 수집이 빈 값으로 돌아옵니다. 설치 전에 metrics-server 를 `--kubelet-insecure-tls` 플래그와 함께 배포하세요. 이 조건이 빠지면 HPA + KCM 알람이 모두 막힙니다.
- **RBAC**: `nodes/proxy`, `pods`, `services` 에 대한 `get/list/watch` 가 필요합니다. 제공된 `kcm-rbac.yaml` 을 함께 `apply` 합니다.

## 문제 해결

- 수집 누락은 대개 `metrics-server` 미설치, RBAC 누락, ARM 의 경우 빌드 산출물 arch 불일치 중 하나입니다.
- `kubectl -n kcm logs -l app=kcm-agent --tail=200 | grep -iE "error|denied"` 로 1차 원인을 좁힙니다.
- ARM 빌드 실패 시: `go env GOARCH` 가 `arm64` 인지, `gcc -v` 가 ARM target 인지 확인. 타겟 머신에서 빌드하므로 cross 옵션은 불필요.

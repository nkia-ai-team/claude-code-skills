# SMS Agent 설치 가이드

## 개요

SMS(System Management Sensor) 에이전트는 대상 OS 에 native 프로세스로 설치되어 CPU, 메모리, 디스크, 네트워크, 프로세스 감시 지표를 수집기로 송신합니다. 네이티브 바이너리라 아키별 산출물이 필요합니다.

## 설치 개요 (AMD64)

1. `install-spec.yaml` 의 `detection_command` 로 `sms-agent` 프로세스가 이미 떠 있는지 확인합니다.
2. 배포 서버(104) 산출물 저장소에서 `sms-agent-<ver>-linux-amd64.tar.gz` 를 내려받습니다.
3. `/opt/polestar10/sms/` 에 해제하고 systemd unit 을 설치합니다.
4. `systemctl enable --now sms-agent` 로 기동합니다.
5. 수집기 UI 의 "서버 에이전트 관리" 에 UP 으로 올라오면 정상입니다.

## 설치 개요 (ARM64) — qemu-user-static 경유

SMS 의 ARM64 산출물이 아직 정식으로는 배포되지 않는 구간에서는 AMD64 바이너리를 **qemu-user-static** 으로 구동합니다. KCM 과 달리 syscall 폭이 좁아 `qemu-user-static` 에뮬레이션이 실측상 안정적으로 동작합니다.

### 준비 (ARM 호스트에서 1회)

```sh
sudo apt update
sudo apt install -y qemu-user-static binfmt-support
# binfmt 등록 확인
ls /proc/sys/fs/binfmt_misc/ | grep -E "qemu-x86_64|qemu-amd64"
```

### 설치

```sh
tar xzf sms-agent-<ver>-linux-amd64.tar.gz -C /opt/polestar10/sms/
# binfmt 가 등록돼 있으면 ELF 헤더로 자동 qemu 로 분기됨
/opt/polestar10/sms/sms-agent --version
systemctl enable --now sms-agent
```

### 성능 주의

- qemu 에뮬이므로 native 대비 CPU 사용량이 2~3배 상승합니다. 고밀도 ARM 노드에서는 수집기 리포팅 주기를 늘려(`report_interval=60s`) 부하를 줄입니다.
- 장기적으로는 SMS ARM64 native 빌드 산출물이 제공되는 즉시 교체하세요.

## 보강 (메뉴얼 바깥의 실전 지식)

- **SMS 는 KCM/WPM 과 달리 OS 프로세스 계측**이라 컨테이너가 아니라 호스트에 systemd 로 올라갑니다. K8s 노드에도 DaemonSet 이 아니라 호스트 쪽 systemd 로 설치하는 편이 지표 일관성이 좋습니다.
- **Windows**: Windows 호스트에서는 서비스로 등록되며, 아키 이슈가 없습니다(동일 x86_64 바이너리). ARM Windows 는 현재 대상에서 제외.
- **네트워크**: 수집기 → 에이전트 방향은 필요 없고, 에이전트 → 수집기 방향 단방향 TCP 만 열면 됩니다.

## 문제 해결

- 기동 직후 실패하면 `journalctl -u sms-agent -n 200` 으로 로그를 확인합니다.
- ARM 에서 `Exec format error` 가 나오면 `binfmt_misc` 가 제대로 등록되지 않은 것입니다. `update-binfmts --enable qemu-x86_64` 후 재시도합니다.

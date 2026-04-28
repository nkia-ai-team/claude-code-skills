# APM Java Agent 설치 가이드

## 개요

APM(Application Performance Monitor) Java 에이전트는 JVM 에 `-javaagent` 로 부착되어 애플리케이션 메서드 호출, JDBC 쿼리, 외부 HTTP 호출 등 성능 지표를 수집합니다. JVM 바이트코드 레벨 계측이므로 CPU 아키텍처(x86_64/ARM64)는 JVM 구현에서 흡수되어 에이전트 자체는 아키 독립입니다.

## 설치 개요

1. `install-spec.yaml` 의 `detection_command` 로 대상 JVM 프로세스에 이미 APM 에이전트가 붙어 있는지 확인합니다.
2. 배포 서버(104) 산출물 저장소에서 `polestar10-apm-agent-<ver>.tar.gz` 를 내려받아 `/opt/polestar10/apm/` 에 해제합니다.
3. 애플리케이션 기동 스크립트 또는 systemd unit 의 JVM 인자에 다음을 추가합니다.
   ```
   -javaagent:/opt/polestar10/apm/apm-agent.jar
   -Dapm.collector.host=<수집기 호스트>
   -Dapm.app.id=<앱 식별자>
   ```
4. 애플리케이션 기동 후 수집기 UI 의 "애플리케이션 에이전트 목록" 에 UP 으로 올라오면 정상입니다.

## 보강 (메뉴얼 바깥의 실전 지식)

- **JVM 아키텍처 독립**: APM 에이전트는 순수 Java 바이트코드이므로, AMD64/ARM64 모두 동일 산출물로 설치됩니다. 베이스 이미지만 각 아키의 JRE/JDK 를 쓰면 됩니다. 별도 cross-build 나 qemu 에뮬레이션이 필요 없습니다.
- **JVM 버전 매트릭스**: 현재 빌드는 Java 8/11/17 까지만 공식 지원합니다. Java 21 은 레코드/패턴매칭/virtual threads 조합에서 계측 실패가 보고되었으므로 Java 21 애플리케이션은 제외합니다.
- **수집기 네트워크 조건**: 에이전트 → 수집기 방향 TCP 포트가 사내 방화벽에서 열려 있어야 합니다. 설치 전에 `telnet <수집기> <포트>` 로 연결성을 확인하세요.
- **샘플링/오버헤드**: 기본 설정은 전량 수집(trace 100%) 입니다. 고부하 서비스에서는 `apm.sampling.rate=0.1` 같은 JVM 옵션으로 조정하세요.

## 제거

1. JVM 인자에서 `-javaagent:...apm-agent.jar` 라인을 제거합니다.
2. 애플리케이션을 재기동합니다.
3. 수집기 UI 의 해당 엔트리를 수동 삭제합니다.

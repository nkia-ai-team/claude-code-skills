# WPM Agent 설치 가이드

## 개요

WPM(Web Performance Monitor) 에이전트는 Tomcat/Spring 기반 웹 애플리케이션에 JVM 레벨로 부착되어 요청 경로, 응답 시간, 예외를 수집합니다. 아키텍처(x86_64/ARM64)는 JVM 로더가 흡수하므로 에이전트 자체는 아키 독립입니다.

## 설치 개요

1. `install-spec.yaml` 의 `detection_command` 를 먼저 돌려 타겟에 이미 WPM 에이전트가 있는지 확인.
2. 없으면 배포 서버(104) 의 patch share 또는 nkia 산출물 저장소에서 `wpm-agent-<ver>.tar.gz` 를 받습니다.
3. `APP_ROOT/wpm/` 혹은 고객이 지정한 경로에 해제합니다.
4. Tomcat `JAVA_OPTS` 에 에이전트 jar 를 `-javaagent:/path/to/wpm-agent.jar` 로 주입합니다.
5. WAS 를 재기동하고 `polestar-app-wpm-1` 수집 파드/컨테이너 로그에서 `agent save` 이벤트가 들어오는지 확인합니다.

## 보강 (메뉴얼 바깥의 실전 지식)

폴스타10 K8s 설치 환경에서 WPM 을 써보면 메뉴얼에 없는 제약이 반복적으로 걸립니다.

- **Pod 이름 기반 에이전트 식별**: WPM 수집기는 `managementStatus` 를 Pod 이름으로 해시합니다. K8s ReplicaSet rolling 에서 Pod 이름이 바뀌면 이전 에이전트가 DOWN 으로 잡힌 채 새 에이전트가 UP 으로 등록되는 흔적이 `polestar-app-wpm-1` docker logs 에서 관찰됩니다. 이는 정상 동작이지만 알람/리포트를 Pod 이름으로 묶으면 오탐이 생기므로 쿠버네티스 환경에서는 deployment 레벨로 그룹핑해야 합니다.
- **RestClient 미지원** (조건부 — 실제 0건 케이스 확인 필요): Spring 6.1 이후 표준이 된 `RestClient` 인터페이스에 대한 계측이 없어 호출이 집계에서 누락된다고 알려져 있습니다. 단, round-12 dogfooding 결과 `served=0` 의 직접 원인이 아닌 경우가 다수 — application 자체가 5xx fast-fail (validation/외부 의존성 등) 로 정상 요청을 거의 못 받는 케이스가 먼저 의심됩니다. **WPM 데이터 누락 시 진단 순서는 §4 진단 가이드 (phase-12-verify-loop.md) 참조** — application HTTP status 분포 확인이 1순위. `WebClient` / `RestTemplate` 로 대체하거나, 커스텀 계측 추가는 application 정상 확인 후 검토.
- **`@XxxMapping` value 필수** (조건부): `@GetMapping`, `@PostMapping` 등 요청 매핑 애노테이션의 `value` (또는 `path`) 속성이 비어 있으면 WPM 이 엔드포인트를 인식하지 못해 metric 이 생성되지 않는다고 알려져 있습니다. 단 round-12 사례에서는 매핑 정상 + application 5xx 가 원인이었습니다. 이 가설로 시간 허비하지 말고 5xx 점검 우선.
- **Java 21 미지원**: 현재 빌드는 Java 17 까지만 지원합니다. Java 21 ZGC / virtual threads 조합에서는 에이전트가 부팅 단계에서 NPE 로 죽으므로, Java 21 애플리케이션은 WPM 대상에서 제외하거나 차기 빌드를 기다려야 합니다.

## 문제 해결

- 수집이 안 보이면 104 서버에서
  `docker logs polestar-app-wpm-1 --since 10m | grep -i "agent save\|managementStatus"`
  로 UP/DOWN/agent-save 이벤트를 확인합니다.
- Pod 이름이 갱신되었는데 DOWN 으로 남아 있으면 WPM UI 의 "애플리케이션 에이전트 관리" 에서 이전 엔트리를 수동 삭제합니다.

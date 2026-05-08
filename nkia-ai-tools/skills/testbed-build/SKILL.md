---
name: testbed-build
description: NKIA RCA 테스트베드 end-to-end 자동화 오케스트레이터. 4단계 인터뷰 → 아키텍처 승인 → ansible 배포 → Polestar10 6종 자원 등록 (KCM/APM/WPM/SMS/DPM/NMS) → 시나리오 4종 생성 → LLM 알람 정책 → closed-loop 검증 → 보고서. 무거운 phase (코드 합성 / ansible 15~25분 / 메트릭 시계열 / 시나리오 검증) 는 4 sub-agent (testbed-engineer / testbed-deployer / testbed-tuner / testbed-verifier) 에게 fork-context dispatch — parent 에는 표준 verdict JSON 만 유입. 사용자가 "/testbed-build", "테스트베드 만들어줘", "RCA 환경 셋업" 같은 요청 시 트리거. 시나리오 추가만 원하면 testbed-generate-scenarios 단독 호출, 알람 재튜닝만 원하면 testbed-tune-alarms 단독 호출.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(ansible-playbook:*), Bash(ansible:*), Bash(ansible-galaxy:*), Bash(sshpass:*), Bash(ssh:*), Bash(scp:*), Bash(rsync:*), Bash(curl:*), Bash(jq:*), Bash(yq:*), Bash(gh:*), Bash(git:*), Bash(kubectl:*), Bash(docker:*), Bash(k3d:*), Bash(helm:*), Bash(flock:*), Bash(mkdir:*), Bash(chmod:*), Bash(chown:*), Bash(rm:*), Bash(cp:*), Bash(mv:*), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(awk:*), Bash(sed:*), Bash(date:*), Bash(test:*), Bash(echo:*), Bash(printf:*), Bash(tee:*), Bash(python3:*), Bash(envsubst:*), Bash(nc:*), Bash(timeout:*), Bash(tar:*), Bash(gzip:*), Bash(unzip:*), Bash(find:*), Bash(xargs:*), Bash(head:*), Bash(tail:*), Bash(wc:*), Bash(tr:*), Bash(sort:*), Bash(uniq:*), Bash(stat:*), Bash(uname:*), Bash(which:*), Bash(command:*)
---

# testbed-build

## Overview

**얇은 오케스트레이터**. canonical phase contract 를 기준으로 sub-agent /
sub-skill dispatch + manifest checkpoint 를 수행한다. 각 phase 의 raw 데이터는
sub-agent fork context 에 격리, parent 에는 verdict JSON 만 흐름.

✅ 책임: 인터뷰 → 인벤토리/아키텍처 → phase loop dispatch → closed-loop 재시도 → 보고서
❌ 비책임: cleanup 단독 실행, 시나리오만 추가 (`/testbed-generate-scenarios`), 알람만 재튜닝 (`/testbed-tune-alarms`)

## Canonical Contract

모든 phase id / 순서 / manifest 상태 / resume 판단은
[phase-contract.md](references/phase-contract.md) 를 단일 source of truth 로 따른다.
다른 reference 에 남아있는 숫자 phase 표기는 사용자 설명용으로만 보고,
분기 판단에는 `phase_id` 를 사용한다.

## 인터뷰 도구

multi-choice 인터뷰 (인증 / 옵션 / yes-no / 승인) 는 **AskUserQuestion** 도구. 자유 입력 슬롯 (target IP, namespace 이름, 자유 도메인 설명) 만 텍스트 prompt. 묶음 룰 + 추천 카드: [interview-flow.md](references/interview-flow.md).

## Bootstrap (매 호출 첫 단계)

상세: [bootstrap.md](references/bootstrap.md).

1. `~/.testbed-build/{runs,reports,.locks}` 디렉토리 init (chmod 700)
2. `~/.testbed-build/bootstrap.yaml` 부재 시 인터뷰 강제 (캐시 파일 존재해도 default value 제시용으로만 사용 — skip 금지)
3. 외부 레포 (testbed-services / rca-scenario-runner) 부재 시 git clone
4. Resume 결정 — 진행 중 manifest 있으면 사용자 prompt
5. Concurrency lock (`<target_host>_<cluster_name>` 키)
6. Polestar10 부트스트랩 (`~/.polestar10rc` 재사용)

⚠️ `polestar10.organization_id` 빈값으로 진행 X — `polestar10_register` 전에 fail-fast.

## Sub-agent / Sub-skill 매트릭스

| phase_id | Dispatcher | Type | Verdict 핵심 outputs |
|---|---|---|---|
| `services_author` | testbed-engineer | agent (services-author) | branch / pr_url / scenario_hints |
| `ansible_deploy` | testbed-deployer | agent | play_recap / log_path / errors |
| `polestar10_register` | testbed-polestar10-register | skill | resource_ids per agent type |
| `generate_scenarios` | testbed-generate-scenarios | skill | scenario_ids / yaml_path |
| `tune_alarms` | testbed-tune-alarms | skill (→ testbed-tuner agent) | policy_yaml / policies_recommended |
| `verify` | testbed-verifier | agent | overall verdict / recommendations |

표준 verdict JSON 스키마: [verdict-schema.md](references/verdict-schema.md).

## Phase Loop

진행 상태는 매 phase 후 `runs/<RUN_ID>/manifest.yaml` 즉시 저장 ([phase-checkpoint.md](references/phase-checkpoint.md)).

### `interview` — 인터뷰
[interview-flow.md](references/interview-flow.md) 의 4 단계 질문지 (target / 배포 앱 / NMS / Polestar10 모드). 답변 → `runs/<RUN_ID>/interview.yaml`.

### `precheck` — Polestar10 reachability precheck
HTTP 도달성만 (auth 동작은 `polestar10_register` 의 login.md 가 검증). 실패 시 사용자 안내 + 종료. 상세: [polestar10-error-handling.md](references/polestar10-error-handling.md).

### `architecture` — Architecture-draft
[architecture-template.md](references/architecture-template.md) 변수 채움 (mermaid + 6 agent 표 + 알람/시나리오 자리). 산출: `architecture.md`.

### `user_approval` — 사용자 승인 ⛔
AskUserQuestion: 진행 / 수정 / 취소.

### `existing_testbed_detect` — 기존 testbed 감지 게이트
[existing-testbed-detect.md](references/existing-testbed-detect.md). cluster 동명 발견 시 사용자 의도 카드 (장애 시나리오만 / 다른 testbed / 삭제 후 / idempotent / 중단).

### `lock_acquired` — Lock 획득
[concurrency-lock.md](references/concurrency-lock.md). lock key = `<target_host>_<cluster_name>`. 같은 host 다른 cluster 동시 빌드 가능 (k3d 격리).

### `services_author` — Services-Author (조건부)
`interview.app.is_new_variant=true` 일 때만. testbed-engineer agent dispatch — 신규 testbed 코드 생성 + mvnw 빌드 + git push (PR / direct / local). 상세: [services-author-task.md](references/services-author-task.md). verdict.outputs.scenario_hints 보존 → `generate_scenarios` 입력.

### `inventory_generated` — Dynamic inventory 생성
[dynamic-inventory-generator.md](references/dynamic-inventory-generator.md). 인터뷰 답 + bootstrap → `runs/<RUN_ID>/inventory.yml`. group_vars/all.yml 변수 모두 채움 (collector hosts / org id / app subdir / 등).

### `ansible_deploy` — Ansible 배포 + 진단
testbed-deployer agent dispatch (run + 캡처 + 진단 단일 호출 통합). 상세: [ansible-failure-diagnosis.md](references/ansible-failure-diagnosis.md). raw 로그 (수만 줄) 는 agent fork context 에 격리, parent 에는 PLAY RECAP 카운트 + errors 만.

verdict=ok 면 8-c sanity check ([phase-8-sanity-check.md](references/phase-8-sanity-check.md)) → APM standby heartbeat 검증 (round-7 silent failure 차단). 실패 시 manifest OTLP env / collector_host 점검 안내.

### `polestar10_register` — Polestar10 관리대상 등록
[polestar10-register-flow.md](references/polestar10-register-flow.md). agent install 후 60초 grace → testbed-polestar10-register 시나리오 1 dispatch (KCM/APM/WPM/SMS/DPM/NMS 6종 자동 분기). PARTIAL 처리 사용자 prompt.

### `generate_scenarios` — 시나리오 생성
testbed-generate-scenarios dispatch. `services_author` 의 scenario_hints 가 있으면 LLM 인터뷰 없이 직접 변수 채움. 산출: `runs/<RUN_ID>/scenarios.json`.

### `tune_alarms` — 알람 정책
testbed-tune-alarms dispatch (skill 내부에서 testbed-tuner agent 가 메트릭 + 추론 + yaml 합성). mode=apply 시 사용자 승인 후 testbed-polestar10-register 시나리오 2 dispatch. 산출: `runs/<RUN_ID>/alarms.json`.

⚠️ 시스템 default 정책 존재해도 testbed 전용 always add ([scenario_2_alarm_policy.md § 강제 룰](../testbed-polestar10-register/references/scenario_2_alarm_policy.md)).

### `verify` — Closed-loop verify (orchestrator 재시도 max 3)
[phase-12-verify-loop.md](references/phase-12-verify-loop.md). testbed-verifier agent dispatch (단발 verdict). PARTIAL/FAIL → tune-alarms recommendations 적용 → 재시도. PASS 시나리오 skip 으로 시간 절약.

### `finalize` — Finalize
[finalize-report-template.md](references/finalize-report-template.md). architecture + register 표 + alarms 표 + verify 결과 요약 → `~/.testbed-build/reports/<RUN_ID>-<testbed_name>.md`.

### `cleanup` — Cleanup
[phase-14-cleanup.md](references/phase-14-cleanup.md). 정상 종료는 자동 정리, 사용자 cancel / phase failed 케이스는 진행된 phase 별 cleanup 옵션 prompt (services-author 산출물 / ansible 자원 / Polestar10 자원 / 정리 안 함).

destructive action (kubectl delete / helm uninstall / k3d cluster delete / gh pr close) 은 카드 응답 후 자연어 chat 재승인.

## Polestar10 에러 처리 표준

[polestar10-error-handling.md](references/polestar10-error-handling.md). API error → ask-polestar10 호출 → 매뉴얼 답변 → 자동 1회 재시도 → 실패 시 사용자 안내. Network error 는 ask-polestar10 우회하고 인프라 점검 안내.

## 자립 원칙의 한계

오케스트레이터는 사용자에게 작업을 떠넘기지 않고 가능한 모든 자동화 경로를 시도. 단 다음은 manual fallback 정상:
- Polestar10 API endpoint 미정 (PATCH 등 — 매뉴얼 X 영역)
- 사용자 자격증명 누락 (사내 GitLab PAT 등 — agent 가 만들 수 없음)
- destructive action 권한 시스템 chat 재승인 (의도 표현이 아닌 실제 승인)

회피 패턴 (절대 금지):
- "context 한도 가까움" 핑계로 finalize escape
- "endpoint 없으니 사용자 수동" 으로 도망 (모든 길 시도 후만 manual fallback)
- "기본 정책 있으니 skip" (`tune_alarms` 강제 룰 위반)

context 한도 도달 시 사용자에게 `/compact` 권고. 사용자가 "그냥 끝내자" 명시 응답 시에만 finalize 허용.

## 단독 호출 권장

- 시나리오 추가: `/testbed-generate-scenarios`
- 알람 재튜닝: `/testbed-tune-alarms`
- Polestar10 자원 정리: `/testbed-polestar10-register` (시나리오 4)
- 매뉴얼 검색: `/ask-polestar10`

## Resources

### Phase 가이드
- [bootstrap.md](references/bootstrap.md) — 자격증명 + 레포 부트스트랩
- [phase-contract.md](references/phase-contract.md) — canonical phase id + manifest contract
- [interview-flow.md](references/interview-flow.md) — 4단계 인터뷰 + AskUserQuestion 묶음
- [architecture-template.md](references/architecture-template.md) — `architecture` 마크다운 템플릿
- [existing-testbed-detect.md](references/existing-testbed-detect.md) — `existing_testbed_detect` cluster 감지
- [concurrency-lock.md](references/concurrency-lock.md) — `lock_acquired` flock
- [services-author-task.md](references/services-author-task.md) — `services_author` testbed-engineer 입력 spec
- [dynamic-inventory-generator.md](references/dynamic-inventory-generator.md) — `inventory_generated` inventory.yml 생성
- [ansible-failure-diagnosis.md](references/ansible-failure-diagnosis.md) — `ansible_deploy` testbed-deployer dispatch
- [phase-8-sanity-check.md](references/phase-8-sanity-check.md) — `sanity_check` APM standby heartbeat
- [polestar10-register-flow.md](references/polestar10-register-flow.md) — `polestar10_register` 6종 등록 분기
- [verify-task.md](references/verify-task.md) — `verify` testbed-verifier task spec
- [phase-12-verify-loop.md](references/phase-12-verify-loop.md) — `verify` 재시도 루프
- [finalize-report-template.md](references/finalize-report-template.md) — `finalize` 보고서
- [phase-14-cleanup.md](references/phase-14-cleanup.md) — `cleanup` 사용자 prompt + 옵션

### 표준 / 공통
- [phase-checkpoint.md](references/phase-checkpoint.md) — manifest.yaml + resume
- [state-schema.md](references/state-schema.md) — `~/.testbed-build/` 디렉토리 레이아웃
- [verdict-schema.md](references/verdict-schema.md) — sub-agent verdict JSON 표준
- [polestar10-error-handling.md](references/polestar10-error-handling.md) — API/network 에러 분기
- [repo-discovery.md](references/repo-discovery.md) — bootstrap 의 외부 레포 자동 발견
- [kcm-arm64-setup.md](references/kcm-arm64-setup.md) — ARM64 KCM source-build 자격증명

### Sub-agents
- `testbed-engineer` — services-author 모드 (코드 합성 + 빌드 + git push)
- `testbed-deployer` — ansible run + 로그 캡처 + 진단
- `testbed-tuner` — 메트릭 + 임계치 추론 + yaml 합성
- `testbed-verifier` — 시나리오 trigger + 알람 매칭 verdict

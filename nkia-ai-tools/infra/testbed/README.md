# RCA 테스트베드 구축 자동화

이 디렉토리는 **RCA 테스트베드 자동화 시스템의 SoT (Single Source of Truth)**.
팀원이 `/testbed-build` 한 번으로 RCA 테스트베드 (서비스 + 6종 에이전트 + polestar10 등록 + 알람 + 시나리오 검증) 를 완성할 수 있게 하는 게 목표.

**Linear**: NKIAAI-542 (오케스트레이터 메인 이슈)

---

## 워크플로우 (10단계)

```
1. 사용자: /testbed-build 호출
2. 인터뷰 4단계:
   a. 타겟 서버 IP/alias + SSH·polestar10 자격증명
   b. 배포 앱 (plopvape-shop 레퍼런스 / 커스텀 git URL)
   c. NMS 모니터링 대상 네트워크 장비 있음 (IP+SNMP 정보) / 없음
   d. polestar10 웹 조작 모드 (직접 / 자동)
3. 아키텍처 문서 v1 생성 → 사용자에게 표시 → 승인
4. 서비스 배포 (Spring boot + K3s + DB)
   - K3s 단일 노드 또는 클러스터
   - Spring boot 앱 + PostgreSQL/MySQL/MariaDB/CUBRID/Tibero 중 1
   - scp 로 타겟 서버 (예: 109) 에 전송
5. 에이전트 6종 설치 + heartbeat
   - polestar-agents-binaries 레포에서 download
   - scp + systemd/docker 설치
   - ARM+SMS: 호환층 라이브러리 (이름 미확정)
   - ARM+KCM: lucida-kcmagent 소스 scp → 타겟에서 빌드
6. polestar10 등록  ← 현재 testbed-polestar10-register sub-skill 로 자동화됨
   - 시나리오 1 (full testbed) dispatch
   - 6종 모두 등록 (NMS 는 인터뷰 'no' 면 skip)
7. 시나리오 + 스크립트 생성
   - scenario-patterns 카탈로그 + 배포 서비스 메타 → 4종 시나리오
   - rca-scenario-runner 의 scenarios/services/<name>/scripts/ 에 추가
   - 첫 실행 시 rca-scenario-runner 부재면 git clone
8. LLM 자동 알람 정책 등록
   - 입력 3종: ① 흐르는 메트릭 (/api/measurement/metric/*) ② sre-baseline.md ③ 서비스 도메인 특성
   - 공통 정책 + 개별 정의 모두 자동 생성
9. 시나리오 실행 + 알람 발생 검증 (closed-loop)
   - 발화 안 하면 LLM 임계치 재조정 → 8번 재실행
   - max retry = 3
10. 최종 보고서 + 정리
    - 아키텍처 문서 + 알람 정책 표 + 검증 결과
    - 더미 파일 정리 + 종료
```

---

## 고정 에이전트 스택

| 에이전트 | 사유 | 강제 환경 |
|---|---|---|
| KCM | RCA K8s 메트릭 검증 필수 | K3s/K8s |
| APM + WPM | RCA JVM 트레이스 검증 필수 | Spring boot |
| SMS | 호스트 모니터링 (공통) | — |
| DPM | RCA DB 메트릭 검증 필수 | DB 설치 (PG/MySQL/MariaDB/CUBRID/Tibero 중 1) |
| NMS | 네트워크 장비 있을 때만 — 인터뷰 yes/no | (선택) |

**아키텍처 분기 없음** — 매트릭스 (Spring? K8s?) 폐기. 단순 SMS-only 환경 원하더라도 풀 스택 강제. 이유: 테스트베드 목적은 6종 RCA 검증.

**ARM 처리**:
- SMS: 호환층 라이브러리 (이름 미확정 — Phase 1 검증 필요)
- KCM: lucida-kcmagent (`https://cims2.nkia.net:8443/gitlab/lucida-kcmagent`) 소스 scp → 타겟에서 직접 빌드. Toolchain (gcc/Go) prereq 로 install-spec 에 명시.

---

## 컴포넌트 맵

### 스킬 (`claude-code-skills/nkia-ai-tools/skills/`)

| 스킬 | 책임 | 상태 |
|---|---|---|
| `testbed-build` | 10단계 오케스트레이터 | ❌ 미구현 |
| `testbed-polestar10-register` | 6번 polestar10 등록 | ✅ 구현됨 |
| `testbed-deploy-service` (가제) | 4번 서비스 배포 | ❌ 미구현 |
| `testbed-install-agents` (가제) | 5번 에이전트 6종 설치 | ❌ 미구현 |
| `testbed-generate-scenarios` (가제) | 7번 시나리오 생성 | ❌ 미구현 |
| `testbed-tune-alarms` (가제) | 8번 LLM 알람 정책 결정 | ❌ 미구현 |
| `testbed-verify` (가제) | 9번 closed-loop 검증 | ❌ 미구현 |
| `testbed-finalize` (가제) | 10번 보고서 + 정리 | ❌ 미구현 |

### 지식 자산 (`claude-code-skills/nkia-ai-tools/knowledge/`)

| 자산 | 책임 | 상태 |
|---|---|---|
| `polestar10/api/recipes/` | polestar10 web API recipe (login/list/add/delete/...) | ✅ 12 recipes |
| `polestar10/api/endpoints.md` | 전체 endpoint 명세 | ✅ |
| `polestar10/api/README.md` | recipe 운영 매뉴얼 | ✅ |

### 자동화 본체 (`claude-code-skills/nkia-ai-tools/infra/testbed/`)

| 자산 | 책임 | 상태 |
|---|---|---|
| `README.md` | 본 문서 (SoT) | ✅ |
| `playbooks/` | Ansible (서비스 배포 + 에이전트 설치) | ❌ |
| `scenario-patterns/` | 장애 유형 카드 카탈로그 | ❌ |
| `alert-policies/sre-baseline.md` | LLM prior knowledge | ❌ |
| `manuals/` | docx → md 변환 결과 (SMS/APM/KCM 매뉴얼) | ❌ |
| `install-spec.yaml` | 에이전트별 설치 명세 + arch_support | ❌ |

### 외부 레포

| 레포 | 책임 | 상태 |
|---|---|---|
| `polestar-agents-binaries` (NKIA org) | Linux 최신 바이너리, GitHub Releases | 🟡 README + verify.sh 만 |
| `rca-scenario-runner` (NKIA org) | 시나리오 실행 웹 서비스 + 스크립트 저장소 | ✅ plopvape-shop 시나리오 1종 |
| `lucida-kcmagent` (사내 GitLab) | KCM ARM 빌드용 소스 | 외부 자산 (참조만) |

---

## 핵심 설계 결정 (날짜 역순)

### 2026-04-28 — 매트릭스 폐기 + 알람 LLM 자동 결정
- **Before**: 인터뷰 5단계, 매트릭스 (Spring? K8s?) 분기 → 4종 조합 (A/B/C/D), 알람은 SRE 추천만 사용자가 복붙
- **After**: 인터뷰 4단계, 6종 고정 스택, 알람은 LLM 이 메트릭+baseline+서비스 특성 보고 자동 결정 + closed-loop 검증
- **Why**: (1) 테스트베드 목적이 6종 RCA 검증이라 매트릭스 분기 가치 낮음 (2) LLM 이 실시간 메트릭 + baseline 으로 임계치 결정 가능, 9번 closed-loop 검증이 안전망 역할

### (날짜 미상) — 스킬 얇게 / 플레이북 두껍게
- 스킬 = 인터뷰 + dispatch 만. 실제 설치는 Ansible
- Claude Code 없어도 `ansible-playbook` 직접 실행 가능 (폴백)

### (날짜 미상) — polestar10 웹 자동화 = 하이브리드
- Playwright 로 API 녹화 → HAR 분석 → HTTP 직호출
- 사용자 "직접 vs 자동" 선택권. 런타임 에러 시 가이드 fallback

### (날짜 미상) — 아키텍처 중립
- AMD64/ARM64 대등. 기본/특수 개념 없음
- `install-spec.yaml` 의 `arch_support.{amd64,arm64}` 각 first-class

### (날짜 미상) — 바이너리 git 금지
- polestar-agents-binaries 레포의 GitHub Releases 전용
- Linux 최신만 (AIX/HP/Solaris/구버전 제외)
- KCM 은 바이너리 없이 소스 URL 만

### (날짜 미상) — 사전 에이전트 감지 → skip
- 멱등성. 이미 설치된 에이전트 재설치 안 함

---

## Phase 별 진행 상태

| Phase | 무엇 | 상태 | 비고 |
|---|---|---|---|
| 0 | 온보딩 README | 🟡 | 본 문서가 진입점 역할 시작 |
| 1 | polestar-agents-binaries 레포 + 바이너리 | 🟡 | 레포 ✅, 바이너리 ❌ |
| 2 | polestar10 지식베이스 (메뉴얼 변환 + TOC + install-spec) | 🟡 | recipes 12개 ✅, install-spec ❌, 매뉴얼 변환 ❌ |
| 4 | ask-polestar10 스킬 | ❌ | |
| 5 | 자동화 본체 | 🟡 | infra/testbed/ 디렉토리 신설 (이 문서) — 내용물 미충 |
| 6 | testbed-build 오케스트레이터 + sub-skill | 🟡 | testbed-polestar10-register 1개만 |

추정 진행률: **~10%**

---

## 사용 (현재 가능한 것)

### 단독 호출 가능 (부분 자동화)
- **`testbed-polestar10-register`** — 6번 단계만. 자원이 이미 등록된 polestar10 인스턴스에서 추가/삭제/알람 정책 등록 가능. 사용 예시는 [skills/testbed-polestar10-register/SKILL.md](../../skills/testbed-polestar10-register/SKILL.md) 참조.

### 미구현 영역 (현재는 수동)
- 1~5번 (서비스 배포 + 에이전트 설치): Ansible playbook 미작성. 현재는 `/home/sjbang/dev/admin/docx/` 의 매뉴얼 보고 수동 진행.
- 7번 (시나리오 생성): rca-scenario-runner 에 직접 추가
- 8번 (알람 정책): polestar10 UI 또는 testbed-polestar10-register 시나리오 2 단독 호출 (LLM 자동 결정 안 됨)
- 9~10번 (검증 + 보고서): 수동

---

## 다음 작업 (우선순위순)

### A. 사용자 dogfooding 가능하게
1. **`testbed-build` 오케스트레이터 스킬** — 10단계 분기 결정자. 미구현 sub-skill 자리는 "TBD — 수동 안내" 로 채움
2. **에이전트 설치 sub-skill** — 5번 자동화. polestar-agents-binaries 다운로드 + scp + systemd 설치

### B. Phase 1 자산 채우기
3. **polestar-agents-binaries** 레포에 실제 바이너리 + install-spec.yaml 업로드

### C. 시나리오 통합
4. **scenario-runner 통합 sub-skill** — 7번 자동화. scenario-patterns 카탈로그 + 첫 실행 시 clone

### D. 알람 자동화
5. **알람 정책 LLM 결정 sub-skill** — 8번 자동화. closed-loop 검증 hook 포함

### E. 검증 + 보고서
6. **검증 sub-skill** — 9번 closed-loop 자동화
7. **보고서 sub-skill** — 10번 최종 정리

---

## 운영 매뉴얼

### polestar10 업그레이드 시
1. `/home/sjbang/dev/polestar10-api-explore/.venv/bin/python scripts/01_login.py` 로 재녹화
2. HAR 에서 URL/payload 변동 확인
3. 변동된 `knowledge/polestar10/api/recipes/` 갱신 + PR

### 새 type 캡처 시 (Syslog/SQL/SNMP OID 등)
1. 크롬 DevTools 로 UI 의 해당 조작 캡처
2. `recipes/<op>.md` 의 TBD 섹션 → 실제 curl 블록으로 교체
3. 관련 스킬의 SKILL.md Resource Type Catalog 갱신

### 새 시나리오 패턴 추가 시
- `infra/testbed/scenario-patterns/` 에 마크다운 카드 추가
- scenario-generator 가 자동 발견 (구현 후)

### 설계 결정 변경 시
1. 본 README 의 "핵심 설계 결정" 섹션에 날짜 + Before/After 추가
2. 메모리 hook (`project_testbed_automation_plan.md`) 짧은 갱신
3. (선택) NKIAAI-542 Linear 댓글에 변경 사실 + 본 README 링크

---

## 참고 문서

- [Linear NKIAAI-542](https://linear.app/nkia/issue/NKIAAI-542) — 오케스트레이터 메인 이슈
- [Linear NKIAAI-477~480](https://linear.app/nkia/issue/NKIAAI-477) — 수동 구축 단계 (선행 이슈)
- [knowledge/polestar10/api/README.md](../../knowledge/polestar10/api/README.md) — recipe 사용 정책 + 핸드오프 노트
- [knowledge/polestar10/api/endpoints.md](../../knowledge/polestar10/api/endpoints.md) — 전체 endpoint 명세
- [skills/testbed-polestar10-register/SKILL.md](../../skills/testbed-polestar10-register/SKILL.md) — 등록 sub-skill (현재 유일하게 구현된 sub-skill)
- (외부) `/home/sjbang/dev/polestar10-api-explore/` — recipe 캡처 도구. 플러그인 외부 영역

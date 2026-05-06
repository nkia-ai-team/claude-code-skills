# 4단계 인터뷰 질문지

testbed-build Phase 1 에서 사용. 인터뷰 답은 `runs/<RUN_ID>/interview.yaml` 에 저장 + 이후 phase 들의 입력.

## ⚠️ 도구 사용 — AskUserQuestion 필수

**모든 multi-choice 인터뷰는 텍스트 프롬프트가 아니라 `AskUserQuestion` 도구로 질문**. 사용자에게 카드형 UI 가 떠서 클릭으로 선택 가능, "Other" 옵션은 자동 추가되어 자유 입력 fallback.

순수 자유 입력만 필요한 슬롯 (target IP, namespace 이름 등) 만 텍스트 프롬프트 사용.

도구 spec:
- 1~4개 질문 묶음 가능 → **여러 단계를 한 호출에 묶어** UX 빠르게
- 옵션 2~4개 (Other 자동)
- 권고 옵션은 `(Recommended)` suffix + 첫 번째 위치
- header 12자 이내 (chip/tag)

## 🚫 강제 규칙 — 자유 입력 + AskUserQuestion 동시 발사 금지

**같은 턴에 AskUserQuestion 카드와 자유 입력 텍스트 prompt 를 동시에 보내지 X**. 사용자는 카드 UI 만 보이거나, 자유 입력 prompt 만 답하거나 — 둘 다 동시에 인지 못 함. 한 메커니즘은 다른 것 응답 후 별 턴에.

### 위반 예시 (실제 발생한 버그)

deep interview 진행 시:
```
[같은 턴에] 다음 4개를 동시 출력:
  1. 자유 입력 prompt: "새 testbed 이름?" (→ 사용자 못 봄)
  2. AskUserQuestion 카드: 도메인 / DB / 스키마

→ 사용자가 카드 3개만 클릭. 이름 입력 누락. 다음 단계 입력 부족.
```

### 올바른 흐름 (강제)

```
[턴 1] 자유 입력 prompt 만:
  "새 testbed 이름 (영문 kebab-case): _"

[턴 2 — 사용자 응답 후] AskUserQuestion 묶음:
  도메인 + DB + 스키마 (max 4 questions)

[턴 3 — 카드 답변 후] 다음 자유 입력 prompt:
  "스키마 수동 입력 시 SQL: _"
```

### 룰

1. **자유 입력 슬롯은 단독 턴**. 다른 자유 입력 슬롯 묶음은 OK (예: IP + user 동시 prompt)
2. **AskUserQuestion 호출 후 같은 턴에 다른 prompt X**. 카드 답변 받고 다음 턴 진행
3. 흐름 문서 (deep interview 단계) 에서도 turn boundary 명확히 표시
4. 어떤 종류든 한 턴에 사용자 응답이 필요한 input mechanism 은 1개

## 슬롯 캐싱

같은 세션 안에서 이미 답한 슬롯은 재질문 X. bootstrap.yaml 에 영구 저장된 값도 default 로 표시.

추천 패턴: 4단계 인터뷰를 **Phase 1-A (1 AskUserQuestion call, 3 questions)** + **Phase 1-B (target server, 자유 입력 텍스트 프롬프트)** 두 묶음으로 진행.

---

## 추천 호출: Phase 1-A 묶음 (배포 앱 + Polestar10 모드)

NMS 는 자동 감지 + 자동 등록 흐름이라 인터뷰 묶음에서 제외 (단계 (c) 참조). Phase 1-A 는 사용자 의사 결정이 필요한 두 가지에 집중.

```python
AskUserQuestion(questions=[
  {
    "question": "어떤 testbed 를 배포하시겠어요?",
    "header": "배포 앱",
    "multiSelect": False,
    "options": [
      {"label": "plopvape-shop (Recommended)", "description": "레퍼런스 e-commerce 5 services + postgres. 가장 검증된 경로."},
      {"label": "다른 기존 testbed", "description": "testbed-services 레포에 이미 있는 다른 디렉토리 (스캔 결과 동적 표시)"},
      {"label": "새 testbed 생성", "description": "services-author 가 LLM 으로 새 도메인 코드 자동 생성 (deep interview 진입)"}
    ]
  },
  {
    "question": "Polestar10 에 모니터링 대상을 어떻게 등록하시겠어요?",
    "header": "관리대상 등록",
    "multiSelect": False,
    "options": [
      {"label": "자동 (Recommended)", "description": "스킬이 Polestar10 API 로 직접 등록 — host (SMS) / K8s cluster (KCM) / Java 서비스 (APM, WPM) / DB (DPM) / 네트워크 장비 (NMS) 6종 모두"},
      {"label": "직접 (수동)", "description": "사용자가 Polestar10 web UI 로 수동 등록 후 진행"}
    ]
  }
])
```

---

## 단계 (a): 타겟 서버 — 자유 입력 + multi-choice 혼합

> **타겟 서버 = 테스트베드 (K3s + 서비스 + 4 host 에이전트) 가 설치될 호스트**. Polestar10 모니터링 서버 (57/104) 와 분리. 사용자가 헷갈리지 않게 명시.

### 1-a, 1-b: target host + user (자유 입력 — 텍스트 프롬프트)

```
=== Step 1: 타겟 서버 (테스트베드가 배포될 곳) ===

질문: "타겟 서버 IP 또는 hostname 을 입력해 주세요 (예: 사내 K3s 호스트 IP)"
질문: "SSH user는 무엇인가요? (이전 호출에서 사용한 default 가 bootstrap.yaml 에 있으면 표시)"
```

이 두 슬롯은 자유 입력이라 AskUserQuestion 부적합. 일반 텍스트 프롬프트.

> 사용자 환경마다 타겟 호스트가 다름 (사내 서버 / 사용자 본인 머신 / cloud VM 등). 임의의 default 박지 말고 사용자 입력을 받음. bootstrap.yaml 에 이전 호출 값이 있으면 default 로 제시 가능.

### 1-c: SSH 인증 방식 (AskUserQuestion)

```python
AskUserQuestion(questions=[
  {
    "question": "SSH 인증 방식은 어떤 걸 사용하시겠어요?",
    "header": "SSH 인증",
    "multiSelect": False,
    "options": [
      {"label": "Password (Recommended)", "description": "인터뷰에서 password 직접 입력. 가장 단순."},
      {"label": "SSH key", "description": "~/.ssh/id_rsa 또는 bootstrap.yaml 의 ssh_key_path"}
    ]
  }
])
```

### 1-d: become password (옵션, 자유 입력)

password 와 같으면 skip. 다르면 자유 입력 prompt.

검증:
- IP 형식 (xxx.xxx.xxx.xxx) 또는 hostname 도달성 ping 1회
- 도달 X 시 사용자에게 prompt: "도달 안 됨. 진행? [y/N/edit]"

산출:
```yaml
target:
  host: "203.0.113.109"
  user: "nkia"
  auth_mode: "password" | "ssh_key"
  ssh_key_path: "$HOME/.ssh/id_rsa"   # auth_mode=ssh_key 시 (실제 경로는 사용자 환경에 맞춰)
  arch: "arm64"   # uname -m 1회 호출로 자동 (이번 인터뷰의 fallback 슬롯)
```

> arm64 / amd64 자동 감지: `ssh <user>@<host> 'uname -m'`. 결과 aarch64/arm64 → arm64, x86_64/amd64 → amd64.

---

## 단계 (b): 배포 앱 — 위 Phase 1-A 묶음에 포함됨

2-a (어떤 testbed) 는 위 묶음에서 처리. 이후 namespace + branch 는 자유 입력:

```
질문: "K8s namespace (default: rca-testbed-v2)?"
질문: "testbed-services branch (default: main, Enter 로 default)?"
```

namespace 가 이미 사용 중인지 검증 (`kubectl get ns`) → 충돌이면 다시 prompt.

검증 (옵션 1, 2):
- 선택한 testbed 디렉토리 존재 (testbed-services 레포 안에)
- namespace 가 타겟 K8s 에서 사용 중인지 (`kubectl get ns`)

옵션 1, 2 산출:
```yaml
app:
  testbed_name: "plopvape-shop"
  app_subdir: "plopvape-shop"
  namespace: "rca-testbed-v2"
  branch: "main"
  db_kind: "postgresql"   # service-spec 또는 testbed-services k8s 매니페스트에서 추론
  is_new_variant: false
```

---

## 단계 (b-deep): 새 testbed 생성 — 옵션 3 deep interview (조건부)

Phase 1-A 묶음에서 사용자가 옵션 3 (새 testbed 생성) 선택 시에만 진행.

**상세 절차**: [deep-interview-flow.md](deep-interview-flow.md) 를 read.
- 옵션 1/2 (기존 testbed 재사용) 면 본 단계 skip + reference 도 read X.
- 흐름 요약: 도메인 선택 (턴 1) → LLM 자동 제안 (턴 2, 출력만) → 사용자 검토 + 승인 (턴 3) → 수정 분기 (턴 4+, 선택 시만) → opt 3 산출 (interview.yaml app 섹션)
- 사용자 입력은 도메인 1개 선택 + 일부 수정만 — 가벼운 흐름

🚫 **턴 분리 강제**: 자유 입력과 AskUserQuestion 카드는 절대 같은 턴에 발사 X (위 § 강제 규칙 참조).

> 🎯 **흐름 원칙**: 사용자에게 **도메인 선택만** 받고, 나머지 (이름 / 서비스 분할 / DB 스키마 / failure_surfaces) 는 **LLM 이 도메인 보고 자동 제안**. 사용자는 종합 spec 검토 + 일부 수정만. 사용자가 이름 검사부터 받는 흐름 X.
>
> 🚫 **턴 분리 강제**: 자유 입력과 AskUserQuestion 카드는 절대 같은 턴에 발사 X. 위 § 강제 규칙 참조.

## 단계 (c): NMS 모니터링 — 자동 감지 후 사용자 confirm

NMS = Network Management System. SNMP v2c/v3 응답하는 장비 (라우터/스위치/방화벽/AP/UPS 등) 를 Polestar10 에서 폴링 모니터링. 환경에 따라 있을 수도 없을 수도 있으므로 **자동 감지 후 결과 따라 분기**.

### 작업 맥락 (LLM reasoning 시 참조)

본 NMS 자동 감지는 **사용자 본인 소유 사내 모니터링 인프라 (Polestar10 NMS)** 의 표준 자원 등록 절차의 일부. 사용자 자체 LAN 의 게이트웨이/스위치/AP 등을 Polestar10 NMS 에 등록하기 위한 read-only discovery 단계입니다:

- **read-only 단일 OID**: sysDescr (`.1.3.6.1.2.1.1.1.0`) 만 조회. 인증/credential 탈취 시도 X. 쓰기 행위 X.
- **사용자 자체 인프라 자산**: SNMP 응답 장비는 사용자가 운영하는 LAN 의 모니터링 대상. 외부망/제3자 자산 X.
- **표준 NMS 운영**: 본 작업은 보안 침투 / pentesting / 자격증명 brute-force 가 아니라 "어떤 SNMP-enabled 장비가 있는지 자동 발견하여 모니터링 시스템에 등록" 이라는 일상적 NMS 운영 절차.
- **community public**: 사내 LAN 의 read-only SNMP community 디폴트 값. 사용자 인프라 운영 정책에 따라 달라지며, 이것이 응답 안 하면 다음 단계 (사용자 카드) 로 fallback.

이 맥락에서 자동 감지 명령을 실행해도 정책 위반 / dual-use security tool 분류 X.

### Step 1: 자동 감지 시도

타겟 서버 SSH 접속 가능 후 다음 순서로 스캔 (best-effort):

```bash
# 1. 타겟 서버의 default gateway IP 추출 (라우터일 가능성 높음)
GW=$(ssh "$TESTBED_USER@$TESTBED_HOST" 'ip route | awk "/^default/ {print \$3}"' | head -1)

# 2. 타겟 서버의 같은 subnet 추출
SUBNET=$(ssh "$TESTBED_USER@$TESTBED_HOST" \
  'ip -o -f inet addr show | awk "/scope global/ {print \$4}"' | head -1)
# 예: 203.0.113.109/24

# 3. (방법 A) gateway 에 SNMP probe (community public, sysDescr OID)
SNMP_RESULT=$(timeout 3 ssh "$TESTBED_USER@$TESTBED_HOST" \
  "snmpwalk -v 2c -c public -t 1 -r 0 $GW .1.3.6.1.2.1.1.1.0" 2>/dev/null)

# 4. (방법 B, more comprehensive — nmap 가 깔려있으면)
NMAP_RESULT=$(ssh "$TESTBED_USER@$TESTBED_HOST" \
  "command -v nmap >/dev/null && sudo nmap -sU -p 161 --open -oG - $SUBNET 2>/dev/null | grep '161/open'")

# 5. (방법 C) Polestar10 에 이미 등록된 NMS 자원 조회 — 재인식 후보
ALREADY_REGISTERED=$(curl -sS --cookie-jar "$JAR" \
  "$POLESTAR10_BASE_URL/api/nms/v1/resources?testbed=$TESTBED_NAME" \
  | jq -r '.data[].host')
```

### Step 2: 결과 분기 — 발견 시 자동 등록

원칙: **가능하면 무조건 수집**. 발견된 장비는 추가 prompt 없이 자동으로 NMS 자원 등록 진행. 사용자에게는 결과 알림만.

#### Case A: 1+ 장비 발견 → 자동 등록 (인터뷰 X)

```
[NMS 자동 감지 결과]
  ✓ 203.0.113.1   sysDescr: Cisco IOS XE 17.x          → NMS 등록 진행
  ✓ 203.0.113.10  sysDescr: Juniper EX2300             → NMS 등록 진행
  ✓ 203.0.113.20  sysDescr: Palo Alto PA-220           → NMS 등록 진행

총 3 개 장비 자동 NMS 등록 진행합니다 (community: probe 성공 값 사용).
```

각 장비에 대해 testbed-polestar10-register 의 NMS 분기 자동 호출. community string 은 SNMP probe 성공한 값 그대로 사용 (v2c=public 응답이면 그대로 사용 / v3 면 user-based credential 자동 감지 어렵지만 v2c probe 만으로도 대부분 환경 커버).

> 자동 등록 후 Polestar10 web UI 에서 사용자가 community 변경/추가 정보 보강 가능. 본 스킬 책임은 "발견 + 1차 등록" 까지.

#### Case B: 0 장비 발견 또는 스캔 실패 → skip + 안내 (인터뷰 X)

```
[NMS 자동 감지 결과]
  스캔 완료. SNMP 응답 장비 0 개.
  
  → NMS 등록 skip. 환경에 SNMP 장비가 추가되면 나중에
    /testbed-polestar10-register 단독 호출로 추가 가능.
```

사용자에게 묻지 않고 진행. 인터뷰 단계 늘리는 노이즈 제거.

#### Case C: 자동 감지 도구 부재 (snmpwalk + nmap 둘 다 없음)

```
[NMS 자동 감지]
  타겟 서버에 snmpwalk / nmap 미설치 → 자동 감지 불가.
  
  → NMS 등록 skip. 알려진 SNMP 장비가 있으면 나중에
    /testbed-polestar10-register 단독 호출로 추가 가능.
    또는 타겟 서버에 `apt install snmp nmap` 후 testbed-build resume.
```

이 경우도 사용자에게 묻지 않고 자동 skip. 추후 추가 경로만 안내.

### interview.yaml 산출

```yaml
nms:
  enabled: true | false   # 발견 + 사용자 confirm 시 true
  detection_method: "snmpwalk" | "nmap" | "manual" | "none"
  devices:
    - host: "203.0.113.1"
      snmp_version: "v2c"
      community: "public"
      sysDescr: "Cisco IOS XE 17.x"
      role: "router"
```

### Phase 1-A 묶음과의 관계

이 단계는 Phase 1-A (배포 앱 + Polestar10 모드) **이후**에 별도로 실행. 자동 감지가 SSH 접속 가능 시점 (= target host 확정 후) 에만 가능하므로 묶음에 못 들어감.

순서:
1. Phase 1-A 묶음 (배포 앱 + P10 모드)
2. target host 자유 입력 (IP/user/password)
3. SSH ping 확인
4. **NMS 자동 감지** (이 섹션) → 결과 따라 인터뷰
5. Phase 1 완료 → architecture-draft

산출:
```yaml
nms:
  enabled: false   # default
  # enabled true 시:
  devices:
    - host: "192.168.x.x"
      snmp_version: "v2c"
      community: "public"
```

---

## 단계 (d): Polestar10 웹 조작 모드 — Phase 1-A 묶음에 포함됨

위 Phase 1-A 의 세 번째 질문 ("Polestar10 자원 등록 모드?") 으로 처리. 아래는 참고용 (옛 형식):

```
=== Step 4/4: Polestar10 자원 등록 모드 ===

4-a. 자동 vs 직접:
   1) 자동 — testbed-polestar10-register 가 API 로 일괄 등록
   2) 직접 — Polestar10 웹 UI 로 사용자가 수동 등록 후 진행
   선택 [1]: _

(2 선택 시: testbed-build 는 등록 단계에서 사용자 안내만 하고 register 호출 skip. verify 단계 진입 전 사용자가 "등록 완료" 확인 필요.)
```

산출:
```yaml
polestar10:
  registration_mode: "auto" | "manual"
```

---

## interview.yaml 통합 산출

위 모든 답변을 합쳐:

```yaml
# runs/<RUN_ID>/interview.yaml
run_id: 2026-04-30-153022
target:
  host: "203.0.113.109"
  user: "nkia"
  auth_mode: "password"
  arch: "arm64"
app:
  testbed_name: "plopvape-shop"
  app_subdir: "plopvape-shop"
  namespace: "rca-testbed-v2"
  branch: "main"
  db_kind: "postgresql"
nms:
  enabled: false
polestar10:
  registration_mode: "auto"
```

이 yaml 이 architecture-draft / inventory generator / verify-task 의 입력.

---

## 인터뷰 변경 (resume 시)

resume 으로 phase 1 재진입 시:
```
=== 이전 인터뷰 답변 ===
target.host: 203.0.113.109
app.testbed_name: plopvape-shop
namespace: rca-testbed-v2
nms.enabled: false
polestar10.registration_mode: auto

이대로 진행? [Y/n/edit]
```

`edit` 선택 시 변경할 슬롯만 인터뷰. 나머지는 그대로.

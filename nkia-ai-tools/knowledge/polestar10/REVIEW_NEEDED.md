# polestar10 지식베이스 — 사람 검토 필요 항목

Playwright 기반 메뉴 검색 자동 검증 (2026-04-28) 결과를 정리합니다.
검증 절차는 `scripts/validate-menu-paths.md` 참조.

## 1. 요약

| 분류 | 건수 | 비율 |
|---|---:|---:|
| 자동 검증 통과 (`menu_path_verified: true`) | 96 | 51.6% |
| 부분 매치 (사람 검토 후보) | 47 | 25.3% |
| 메뉴 검색 미존재 | 43 | 23.1% |
| **합계** | **186** |  |

> 자동 검증: 매뉴얼 frontmatter `feature` 값 → polestar10 통합 검색창 입력 → `.portal-auto-complete-dropdown` 결과 추출. `keyword` 가 `feature` 와 정확 일치하면 EXACT (자동 verified).

## 2. 카테고리별 분포

| 역할/카테고리 | exact | partial | none | total |
|---|---:|---:|---:|---:|
| user/account | 24 | 9 | 10 | 43 |
| user/agent-install | 4 | 3 | 1 | 8 |
| user/alert | 13 | 7 | 9 | 29 |
| user/db | 2 | 0 | 0 | 2 |
| user/k8s | 18 | 0 | 2 | 20 |
| user/network | 8 | 1 | 0 | 9 |
| user/perf | 19 | 7 | 3 | 29 |
| user/system | 7 | 5 | 7 | 19 |
| admin/agent-install | 0 | 13 | 10 | 23 |
| admin/db | 0 | 2 | 0 | 2 |
| admin/k8s | 1 | 0 | 0 | 1 |
| admin/system | 0 | 0 | 1 | 1 |

## 3. 부분 매치 (사람 확인 필요)

`feature` 검색 시 결과는 있었으나 정확 매치가 아닌 경우. 가장 가까운 후보 메뉴 경로를 같이 적었습니다. 사람 확인 후 `menu_path_verified: true` 토글 + `menu_path_full` 추가 또는 `feature` 값 수정.

### user/account (9 건)

| slug | feature | 검색 쿼리 | 후보 |
|---|---|---|---|
| account-003 | 권한 | `권한` | ITSM 요청권한 관리 (운영관리 > ITG > ITSM 요청권한 관리) |
| account-005 | 기본 사용자 정의 항목 관리 | `기본 사용자` | 기본 사용자 정의 항목 (운영관리 > EMS > 기본 사용자 정의 항목) |
| account-014 | 사용자 정의 SQL 템플릿 | `사용자 정의` | 로그 (전체구성 > 사용자 정의 항목 > 로그)<br>윈도우 이벤트 로그 (전체구성 > 사용자 정의 항목 > 윈도우 이벤트 로그)<br>프로세스 (전체구성 > 사용자 정의 항목 > 프로세스) |
| account-015 | 사용자 정의 스크립트 템플릿 | `사용자 정의` | 로그 (전체구성 > 사용자 정의 항목 > 로그)<br>윈도우 이벤트 로그 (전체구성 > 사용자 정의 항목 > 윈도우 이벤트 로그)<br>프로세스 (전체구성 > 사용자 정의 항목 > 프로세스) |
| account-017 | 사용자 정의 SQL 목록 | `사용자 정의` | 로그 (전체구성 > 사용자 정의 항목 > 로그)<br>윈도우 이벤트 로그 (전체구성 > 사용자 정의 항목 > 윈도우 이벤트 로그)<br>프로세스 (전체구성 > 사용자 정의 항목 > 프로세스) |
| account-021 | 사용자 정의 스크립트 목록 | `사용자 정의` | 로그 (전체구성 > 사용자 정의 항목 > 로그)<br>윈도우 이벤트 로그 (전체구성 > 사용자 정의 항목 > 윈도우 이벤트 로그)<br>프로세스 (전체구성 > 사용자 정의 항목 > 프로세스) |
| account-023 | 상면 목록 | `상면` | 상면 관리 (상면 관리) |
| account-035 | 요청 담당자그룹 목록 | `요청` | 요청현황 (요청현황)<br>ITSM 요청데이터 관리 (운영관리 > ITG > ITSM 요청데이터 관리)<br>ITSM 요청권한 관리 (운영관리 > ITG > ITSM 요청권한 관리) |
| account-036 | 공통코드(일반) | `공통코드` | 공통코드 관리 (운영관리 > ITG > 공통코드 관리) |

### user/agent-install (3 건)

| slug | feature | 검색 쿼리 | 후보 |
|---|---|---|---|
| agent-install-002 | WPM Agent 삭제 | `WPM` | domain-wpm-0 (polestar) |
| agent-install-003 | WPM Java Agent 설치 | `WPM` | domain-wpm-0 (polestar) |
| agent-install-004 | 사용자 매뉴얼 | `사용자` | 로그 (전체구성 > 사용자 정의 항목 > 로그)<br>윈도우 이벤트 로그 (전체구성 > 사용자 정의 항목 > 윈도우 이벤트 로그)<br>프로세스 (전체구성 > 사용자 정의 항목 > 프로세스) |

### user/alert (7 건)

| slug | feature | 검색 쿼리 | 후보 |
|---|---|---|---|
| alert-008 | 관리 대상 추가 | `관리` | 관리대상 추가 (전체구성 > 관리대상 > 관리대상 추가)<br>전체 (전체구성 > 관리대상 > 전체)<br>서버 (전체구성 > 관리대상 > 서버) |
| alert-014 | 알람 상세 내용 | `알람` | 알람 현황 (알람 & 이벤트 > 알람 & 이벤트 현황 > 알람 현황)<br>이벤트 현황 (알람 & 이벤트 > 알람 & 이벤트 현황 > 이벤트 현황)<br>공통 알람 정책 (알람 & 이벤트 > 알람 정책 > 공통 알람 정책) |
| alert-015 | 알람 설정 | `알람` | 알람 현황 (알람 & 이벤트 > 알람 & 이벤트 현황 > 알람 현황)<br>이벤트 현황 (알람 & 이벤트 > 알람 & 이벤트 현황 > 이벤트 현황)<br>공통 알람 정책 (알람 & 이벤트 > 알람 정책 > 공통 알람 정책) |
| alert-016 | 알람 컨디션 로그 표현식 | `알람` | 알람 현황 (알람 & 이벤트 > 알람 & 이벤트 현황 > 알람 현황)<br>이벤트 현황 (알람 & 이벤트 > 알람 & 이벤트 현황 > 이벤트 현황)<br>공통 알람 정책 (알람 & 이벤트 > 알람 정책 > 공통 알람 정책) |
| alert-017 | 알람 패턴 통보 설정 | `알람 패턴` | 알람 패턴 통보설정 (운영관리 > EMS > 알람 패턴 통보설정) |
| alert-020 | 전체구성 (요약 대시보드) | `전체구성` | 관리대상 추가 (전체구성 > 관리대상 > 관리대상 추가)<br>전체 (전체구성 > 관리대상 > 전체)<br>서버 (전체구성 > 관리대상 > 서버) |
| alert-021 | 윈도우 이벤트 로그 감시 | `윈도우 이벤트` | 윈도우 이벤트 로그 (전체구성 > 사용자 정의 항목 > 윈도우 이벤트 로그) |

### user/network (1 건)

| slug | feature | 검색 쿼리 | 후보 |
|---|---|---|---|
| network-009 | 전체구성 | `전체구성` | 관리대상 추가 (전체구성 > 관리대상 > 관리대상 추가)<br>전체 (전체구성 > 관리대상 > 전체)<br>서버 (전체구성 > 관리대상 > 서버) |

### user/perf (7 건)

| slug | feature | 검색 쿼리 | 후보 |
|---|---|---|---|
| perf-002 | Ping 감시 | `Ping` | PING (전체구성 > 사용자 정의 항목 > PING) |
| perf-006 | 공유 노트 목록 | `공유` | 공유노트 (공유노트 > 공유노트 > 공유노트)<br>휴지통 (공유노트 > 공유노트 > 휴지통) |
| perf-007 | 공유 노트 추가 | `공유` | 공유노트 (공유노트 > 공유노트 > 공유노트)<br>휴지통 (공유노트 > 공유노트 > 휴지통) |
| perf-009 | 대시보드 생성 및 편집 | `대시보드` | 위젯 대시보드 (대시보드 > 대시보드 > 위젯 대시보드)<br>빌더 (대시보드 > 대시보드 > 빌더) |
| perf-012 | 성능 예측 | `성능` | 윈도우 성능카운터 (전체구성 > 사용자 정의 항목 > 윈도우 성능카운터)<br>성능 조회 (성능 조회)<br>성능 이상감지 정책 (알람 & 이벤트 > AIOps Lucida 정책 > 성능 이상감지 정책) |
| perf-014 | 이상감지 시각화 | `이상감지` | 성능 이상감지 정책 (알람 & 이벤트 > AIOps Lucida 정책 > 성능 이상감지 정책)<br>성능 이상감지 개별 현황 (알람 & 이벤트 > AIOps Lucida 정책 > 성능 이상감지 개별 현황) |
| perf-022 | 성능 이상감지 분석 | `성능 이상감지` | 성능 이상감지 정책 (알람 & 이벤트 > AIOps Lucida 정책 > 성능 이상감지 정책)<br>성능 이상감지 개별 현황 (알람 & 이벤트 > AIOps Lucida 정책 > 성능 이상감지 개별 현황) |

### user/system (5 건)

| slug | feature | 검색 쿼리 | 후보 |
|---|---|---|---|
| system-002 | 대시보드 불러오기 | `대시보드` | 위젯 대시보드 (대시보드 > 대시보드 > 위젯 대시보드)<br>빌더 (대시보드 > 대시보드 > 빌더) |
| system-003 | 데이터 수집 설정 | `데이터` | 데이터수집 설정 (운영관리 > EMS > 데이터수집 설정)<br>ITSM 요청데이터 관리 (운영관리 > ITG > ITSM 요청데이터 관리) |
| system-005 | 보고서 관리 | `보고서 관리` | 보고서 현황 (보고서 > 보고서 관리 > 보고서 현황)<br>보고서 템플릿 현황 (보고서 > 보고서 관리 > 보고서 템플릿 현황) |
| system-011 | 시스템 트리 관리 | `시스템` | 연계 시스템 (전체구성 > 관리대상 > 연계 시스템)<br>연계 시스템 (연계 시스템)<br>시스템 그룹 관리 (운영관리 > 기본 설정 > 시스템 그룹 관리) |
| system-012 | 업무 시간 및 휴일 설정 | `업무` | 업무시간 및 휴일 설정 (운영관리 > EMS > 업무시간 및 휴일 설정) |

### admin/agent-install (13 건)

| slug | feature | 검색 쿼리 | 후보 |
|---|---|---|---|
| agent-install-002 | APM Java Agent 삭제 | `APM` | domain-apm-0 (polestar) |
| agent-install-003 | APM Java Agent 설치 | `APM` | domain-apm-0 (polestar) |
| agent-install-007 | KCM Agent 기동 | `KCM` | domain-kcm-0 (polestar) |
| agent-install-009 | KCM Agent 삭제 | `KCM` | domain-kcm-0 (polestar) |
| agent-install-010 | KCM Agent 설치 | `KCM` | domain-kcm-0 (polestar) |
| agent-install-011 | KCM Agent 중지 | `KCM` | domain-kcm-0 (polestar) |
| agent-install-012 | Polestar 10 기동 | `Polestar` | 서비스 (Polestar 관리 > Polestar > 서비스)<br>작업 스케줄 (Polestar 관리 > Polestar > 작업 스케줄) |
| agent-install-013 | Polestar 10 설치 | `Polestar` | 서비스 (Polestar 관리 > Polestar > 서비스)<br>작업 스케줄 (Polestar 관리 > Polestar > 작업 스케줄) |
| agent-install-014 | Polestar 10 중지 | `Polestar` | 서비스 (Polestar 관리 > Polestar > 서비스)<br>작업 스케줄 (Polestar 관리 > Polestar > 작업 스케줄) |
| agent-install-015 | SMS Agent 기동 | `SMS` | domain-sms-0 (polestar) |
| agent-install-017 | SMS Agent 설치 | `SMS` | domain-sms-0 (polestar) |
| agent-install-018 | SMS Agent 제거 | `SMS` | domain-sms-0 (polestar) |
| agent-install-019 | SMS Agent 중지 | `SMS` | domain-sms-0 (polestar) |

### admin/db (2 건)

| slug | feature | 검색 쿼리 | 후보 |
|---|---|---|---|
| db-001 | Polestar 10 DB 백업 | `Polestar` | 서비스 (Polestar 관리 > Polestar > 서비스)<br>작업 스케줄 (Polestar 관리 > Polestar > 작업 스케줄) |
| db-002 | Polestar 10 DB 복구 | `Polestar` | 서비스 (Polestar 관리 > Polestar > 서비스)<br>작업 스케줄 (Polestar 관리 > Polestar > 작업 스케줄) |

## 4. 메뉴 검색 미존재

polestar10 통합 검색에서 결과가 0건. 사유 후보:
- **메뉴가 아닌 동적 라우팅 화면** (예: 목록 행 클릭 시 진입하는 "상세" 화면)
- **메뉴가 아닌 사이드바 탭/단축버튼** (예: "즐겨찾기", "Ask Lucida")
- **매뉴얼 메타 챕터** ("서문", "부록", "간편가이드", "사용자 매뉴얼")
- **데모 환경(192.168.230.104)에 미설치 모듈**
- **운영 가이드(설치/기동/중지) 매뉴얼** — admin/agent-install 카테고리는 polestar10 메뉴와 별개

### user/account (10 건)

| slug | feature | menu_path |
|---|---|---|
| account-002 | 계정 | 계정 |
| account-007 | 로그인 | 로그인 |
| account-009 | 메시지 파싱 규칙 매뉴얼 | 메시지파싱규칙 |
| account-011 | 비밀번호찾기 | 비밀번호찾기 |
| account-022 | 상면관리(뷰) | 상면관리(뷰) |
| account-025 | 포탈 서비스 종합 현황 | 서비스종합현황 |
| account-031 | 2차 인증 | 시스템설정2차인증-(1) |
| account-032 | 연계정보관리 | 연계정보관리 |
| account-041 | 자산정보관리 | 자산정보관리 |
| account-043 | 조직 관리 | 조직관리 |

### user/agent-install (1 건)

| slug | feature | menu_path |
|---|---|---|
| agent-install-001 | 사전 설치 환경 조사 | WPMAgent사전설치환경조사 |

### user/alert (9 건)

| slug | feature | menu_path |
|---|---|---|
| alert-001 | Ask Lucida | AskLucida |
| alert-006 | 개인정보 프로필 | 개인정보프로필 |
| alert-009 | 레이아웃 | 레이아웃 |
| alert-022 | 장기 예측 정책 | 장기예측정책 |
| alert-023 | 정적 임계치 추천 | 정적임계치 |
| alert-024 | 태그맵 | 태그맵 |
| alert-025 | 태그트리 | 태그트리 |
| alert-028 | 포털 서비스 종합 현황 | 포털서비스종합현황 |
| alert-029 | 포털 서비스 통합 검색 | 포털서비스통합검색 |

### user/k8s (2 건)

| slug | feature | menu_path |
|---|---|---|
| k8s-009 | 스토리지클래스 목록 | 쿠버네티스스토리지클래스목록 |
| k8s-011 | 잡 목록 | 쿠버네티스잡목록 |

### user/perf (3 건)

| slug | feature | menu_path |
|---|---|---|
| perf-017 | 시점 분석 | 성능조회시점분석 |
| perf-023 | 장기 예측 개별 현황 | 장기예측개별현황 |
| perf-024 | 즐겨찾기 | 즐겨찾기 |

### user/system (7 건)

| slug | feature | menu_path |
|---|---|---|
| system-007 | 분류관리 | 분류관리 |
| system-009 | 시스템그룹 트리 | 시스템그룹트리 |
| system-010 | 보안 설정 | 시스템설정보안설정 |
| system-013 | 연계시스템 현황 | 연계시스템 |
| system-014 | 연계시스템 목록 | 연계시스템목록 |
| system-015 | 연계시스템 상세 | 연계시스템상세 |
| system-017 | 접근제어 일괄설정 | 접근제어일괄설정 |

### admin/agent-install (10 건)

| slug | feature | menu_path |
|---|---|---|
| agent-install-001 | 사전 설치 환경 조사 | APMJavaAgent사전설치환경조사 |
| agent-install-004 | lucida-for-docker<br /> | ls<br /> |
| agent-install-005 | 간편가이드 | AP원복가이드 |
| agent-install-006 | 간편가이드 | AP패치가이드 |
| agent-install-008 | 사전 설치 환경 조사 | KCMAgent사전설치환경조사 |
| agent-install-016 | 사전 설치 환경 조사 | SMSAgent사전설치환경조사 |
| agent-install-020 | 부록 | 부록 |
| agent-install-021 | 사전 설치 | 사전설치 |
| agent-install-022 | 사전 설치 환경 조사 | 사전설치환경조사 |
| agent-install-023 | 관리자 매뉴얼 | 서문 |

### admin/system (1 건)

| slug | feature | menu_path |
|---|---|---|
| system-001 | 룰체인 툴 설정 | 룰체인툴설정 |

## 5. 자동 검증 통과 (참고용 전체 표)

`menu_path_verified: true` 로 토글 + `menu_path_full` 추가된 매뉴얼 96 개.

### user/account (24 건)

| slug | feature | menu_path_full |
|---|---|---|
| account-001 | MyPage | MyPage |
| account-004 | 기능 관리 | 운영관리 > 기본 설정 > 기능 관리 |
| account-006 | 담당자 구분 | 운영관리 > EMS > 담당자 구분 |
| account-008 | 메뉴 관리 | 운영관리 > 기본 설정 > 메뉴 관리 |
| account-010 | 부서 관리 | 운영관리 > 기본 설정 > 부서 관리 |
| account-012 | 빌더 대시보드 목록 | 대시보드 > 대시보드 > 빌더 |
| account-013 | 사용자 관리 | 운영관리 > 기본 설정 > 사용자 관리 |
| account-016 | SNMP OID | 전체구성 > 사용자 정의 항목 > SNMP OID |
| account-018 | Syslog 목록 | 전체구성 > 사용자 정의 항목 > Syslog |
| account-019 | Trap 목록 | 전체구성 > 사용자 정의 항목 > Trap |
| account-020 | 네트워크 스크립트 | 전체구성 > 사용자 정의 항목 > 네트워크 스크립트 |
| account-024 | 서비스수준관리 – 서비스수준목표 | 서비스수준관리 |
| account-026 | 서비스카탈로그 | 서비스카탈로그 |
| account-027 | 서비스포트폴리오 – 서비스도메인 관리 | 서비스포트폴리오 |
| account-028 | 소프트웨어 EOS 관리 | 운영자동화 > 소프트웨어 관리 > 소프트웨어 EOS 관리 |
| account-029 | 소프트웨어 스크립트 관리 | 운영자동화 > 소프트웨어 관리 > 소프트웨어 스크립트 관리 |
| account-030 | 소프트웨어 현황 | 운영자동화 > 소프트웨어 관리 > 소프트웨어 현황 |
| account-033 | 요청현황 | 요청현황 |
| account-034 | ITAM 기준정보 관리 – 자산분류체계 | 운영관리 > ITG > ITAM 기준정보 관리 |
| account-037 | 위젯 대시보드 목록 | 대시보드 > 대시보드 > 위젯 대시보드 |
| account-038 | 위젯 대시보드 편집 | 대시보드 > 대시보드 > 위젯 대시보드 |
| account-039 | 자산구성작업 – 자산구성작업 목록 | 자산구성작업 |
| account-040 | 자산구성조회 – 자산정보 | 자산구성조회 |
| account-042 | KMS(공지사항) 목록 | 정보관리 |

### user/agent-install (4 건)

| slug | feature | menu_path_full |
|---|---|---|
| agent-install-005 | 서버 에이전트 관리 | 운영관리 > EMS > 서버 에이전트 관리 |
| agent-install-006 | 서비스 목록 | 애플리케이션 > 관리대상 > 서비스 |
| agent-install-007 | 에이전트 목록 | 애플리케이션 > 관리대상 > 에이전트 |
| agent-install-008 | 에이전트 상세 | 애플리케이션 > 관리대상 > 에이전트 |

### user/alert (13 건)

| slug | feature | menu_path_full |
|---|---|---|
| alert-002 | SLO 목록 | 전체구성 > 사용자 정의 항목 > SLO |
| alert-003 | SQL Server 목록 | 전체구성 > 관리대상 > SQL Server |
| alert-004 | 웹 URL 상세 | 전체구성 > 관리대상 > 웹 URL |
| alert-005 | 개별 알람 정책 | 알람 & 이벤트 > 알람 정책 > 개별 알람 정책 |
| alert-007 | 공통 알람 정책 | 알람 & 이벤트 > 알람 정책 > 공통 알람 정책 |
| alert-010 | 로그 감시 | 전체구성 > 사용자 정의 항목 > 로그 |
| alert-011 | 복합 알람 정책 | 알람 & 이벤트 > 알람 정책 > 복합 알람 정책 |
| alert-012 | 서버 상세 | 전체구성 > 관리대상 > 서버 |
| alert-013 | Syslog 목록 | 전체구성 > 사용자 정의 항목 > Syslog |
| alert-018 | 오라클 목록 | 전체구성 > 관리대상 > 오라클 |
| alert-019 | 오라클 상세 | 전체구성 > 관리대상 > 오라클 |
| alert-026 | 통합 로그 | 통합 로그 |
| alert-027 | Trap 목록 | 전체구성 > 사용자 정의 항목 > Trap |

### user/db (2 건)

| slug | feature | menu_path_full |
|---|---|---|
| db-001 | CUBRID 목록 | 전체구성 > 관리대상 > CUBRID |
| db-002 | CUBRID 상세 | 전체구성 > 관리대상 > CUBRID |

### user/k8s (18 건)

| slug | feature | menu_path_full |
|---|---|---|
| k8s-001 | HPA 목록 | 쿠버네티스 > 오토스케일러 > HPA |
| k8s-002 | 네임스페이스 목록 | 쿠버네티스 > 네임스페이스 |
| k8s-003 | 노드 목록 | 쿠버네티스 > 노드 |
| k8s-004 | 데몬셋 목록 | 쿠버네티스 > 워크로드 > 데몬셋 |
| k8s-005 | 디플로이먼트 목록 | 쿠버네티스 > 워크로드 > 디플로이먼트 |
| k8s-006 | 리플리카셋 목록 | 쿠버네티스 > 워크로드 > 리플리카셋 |
| k8s-007 | 서비스 목록 | 애플리케이션 > 관리대상 > 서비스 |
| k8s-008 | 스테이트풀셋 목록 | 쿠버네티스 > 워크로드 > 스테이트풀셋 |
| k8s-010 | 인그레스 목록 | 쿠버네티스 > 네트워크 > 인그레스 |
| k8s-012 | 쿠버네티스 목록 | 전체구성 > 관리대상 > 쿠버네티스 |
| k8s-013 | 컨테이너 목록 | 쿠버네티스 > 워크로드 > 컨테이너 |
| k8s-014 | 컨피그맵 목록 | 쿠버네티스 > 컨피그맵 |
| k8s-015 | 크론잡 목록 | 쿠버네티스 > 워크로드 > 크론잡 |
| k8s-016 | 클러스터 목록 | 쿠버네티스 > 클러스터 |
| k8s-017 | 클러스터 상세 | 쿠버네티스 > 클러스터 |
| k8s-018 | 파드 목록 | 쿠버네티스 > 워크로드 > 파드 |
| k8s-019 | 퍼시스턴트 볼륨 목록 | 쿠버네티스 > 스토리지 > 퍼시스턴트 볼륨 |
| k8s-020 | 퍼시스턴트 볼륨 클레임 목록 | 쿠버네티스 > 스토리지 > 퍼시스턴트 볼륨 |

### user/network (8 건)

| slug | feature | menu_path_full |
|---|---|---|
| network-001 | 네트워크 관리 | 전체구성 > 관리대상 > 네트워크 |
| network-002 | 네트워크 목록 | 전체구성 > 관리대상 > 네트워크 |
| network-003 | 네트워크 상세 | 전체구성 > 관리대상 > 네트워크 |
| network-004 | 네트워크 세션 감시 | 전체구성 > 사용자 정의 항목 > 네트워크 세션 |
| network-005 | 네트워크 스크립트 템플릿 | 전체구성 > 사용자 정의 항목 > 네트워크 스크립트 |
| network-006 | 네트워크 자동맵 | 전체구성 > 관리대상 > 네트워크 |
| network-007 | 소프트웨어 수집 이력 | 운영자동화 > 소프트웨어 관리 > 소프트웨어 수집 이력 |
| network-008 | 네트워크 관리 | 전체구성 > 관리대상 > 네트워크 |

### user/perf (19 건)

| slug | feature | menu_path_full |
|---|---|---|
| perf-001 | PMS – 사업관리 | PMS |
| perf-003 | SNMP OID 템플릿 | 전체구성 > 사용자 정의 항목 > SNMP OID |
| perf-004 | SQL Server 상세 | 전체구성 > 관리대상 > SQL Server |
| perf-005 | TCP 포트 감시 | 전체구성 > 사용자 정의 항목 > TCP 포트 |
| perf-008 | 기본 포트 인증 관리 | 운영관리 > EMS > 기본 포트 인증 관리 |
| perf-010 | 로그 이상감지 현황 | 전체구성 > 사용자 정의 항목 > 로그 |
| perf-011 | 서버목록 | 전체구성 > 관리대상 > 서버 |
| perf-013 | 성능 이상감지 개별 현황 | 알람 & 이벤트 > AIOps Lucida 정책 > 성능 이상감지 개별 현황 |
| perf-015 | 성능 이상감지 정책 | 알람 & 이벤트 > AIOps Lucida 정책 > 성능 이상감지 정책 |
| perf-016 | 성능 조회 | 성능 조회 |
| perf-018 | <span id=\"_Hlk169177776\" class=\"anchor\"></span>애플리케이션 상세 | 전체구성 > 관리대상 > 애플리케이션 |
| perf-019 | 애플리케이션 전체 | 전체구성 > 관리대상 > 애플리케이션 |
| perf-020 | 윈도우 서비스 감시 | 전체구성 > 사용자 정의 항목 > 윈도우 서비스 |
| perf-021 | 윈도우 성능카운터 감시 | 전체구성 > 사용자 정의 항목 > 윈도우 성능카운터 |
| perf-025 | 토폴로지 맵 목록 | 토폴로지 맵 |
| perf-026 | 토폴로지 맵 뷰어 | 토폴로지 맵 |
| perf-027 | 토폴로지 맵 편집 | 토폴로지 맵 |
| perf-028 | 파일 감시 | 전체구성 > 사용자 정의 항목 > 파일 |
| perf-029 | 프로세스 감시 | 전체구성 > 사용자 정의 항목 > 프로세스 |

### user/system (7 건)

| slug | feature | menu_path_full |
|---|---|---|
| system-001 | 웹 URL 목록 | 전체구성 > 관리대상 > 웹 URL |
| system-004 | 라이선스 관리 | 운영관리 > 기본 설정 > 라이선스 관리 |
| system-006 | 보고서 템플릿 관리 | 운영관리 > EMS > 보고서 템플릿 관리 |
| system-008 | 소프트웨어 수집 | 운영자동화 > 소프트웨어 관리 > 소프트웨어 수집 |
| system-016 | 위젯 대시보드 뷰어 | 대시보드 > 대시보드 > 위젯 대시보드 |
| system-018 | 태그 설정 | 운영관리 > 기본 설정 > 태그 설정 |
| system-019 | 통보 설정 | 운영관리 > 기본 설정 > 통보 설정 |

### admin/k8s (1 건)

| slug | feature | menu_path_full |
|---|---|---|
| k8s-001 | 클러스터 구성 | 쿠버네티스 > 클러스터 |

## 6. 기타 자동 감지 이슈 (이전 ralph 작업에서 옮겨온 항목)

- **pandoc flag 호환성 분기 (ralph rule #2 default-apply)**: 이 환경의 pandoc 은 2.9.2.1 로
  PRD 에 적힌 `--markdown-headings=atx` 옵션이 아직 없습니다. `convert-docx.sh` 는 런타임에
  `--help` 를 점검해서 2.11+ 에서는 PRD 그대로, 2.9.x 에서는 deprecated alias 인 `--atx-headers`
  를 사용합니다. 결과 마크다운은 동일(ATX 스타일 `#` 헤딩)이며 수동 액션 필요 없음.
- **plugin.json `agents` 키 수동 추가 (ralph rule #2 default-apply)**: Story 16 은 Claude Code
  `/agents` 목록에 `polestar10-expert` 가 자동 등록되는지 확인 후 필요 시에만
  `"agents": "./agents"` 키를 추가하라고 지시합니다. ralph 는 플러그인 런타임에서 `/agents` 호출을
  할 수 없으므로, 안전한 기본값(명시적 키 추가) 을 적용했습니다. 로컬에서 `polestar10-expert` 가
  이미 자동 감지되면 `nkia-ai-tools/.claude-plugin/plugin.json` 의 `"agents": "./agents"` 라인은
  제거해도 무방합니다.

# Recipe: NMS 네트워크 등록 (TBD)

polestar10 에 NMS 네트워크(라우터/스위치 SNMP 모니터링 대상) 등록.

- **엔드포인트**: **TBD** (추정 prefix: `/api/nms/*` 또는 `/api/nms/v1/*`)
- **인증 필요**: `recipes/login.md` 먼저 실행
- **부작용**: 모니터링 대상 추가

## ⚠️ 현재 상태: 미확정

## 힌트 — 로그인 HAR 에서 관찰된 관련 엔드포인트

```
POST /api/nms/v1/custom/snmpoid/count
POST /api/nms/v1/custom/script/count
POST /api/nms/trap/v1/custom-monitor/count
```

→ NMS 서비스는 `/api/nms/v1/` prefix 사용. 등록은 `/api/nms/v1/<resource>/<save|create|register>` 패턴일 가능성.

## 확정 절차

1. 좌측 사이드바: **NMS (또는 네트워크 관리) > 네트워크 등록** 메뉴 진입
2. **+ 등록** 버튼 → 필드 입력 (네트워크명 · CIDR · SNMP community · SNMP 버전 등)
3. **저장** → DevTools Network 에서 POST 요청 식별
4. URL + payload 캡처

## 레시피 (확정 후 작성)

```bash
# TODO: DevTools 캡처 후 작성
```

## UI Fallback

> **NMS > 네트워크 관리** 메뉴에서 수동 등록. 필요 정보: CIDR, SNMP community string, SNMP v2c/v3 여부.

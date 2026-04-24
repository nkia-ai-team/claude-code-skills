# Recipe: DPM 등록 (TBD)

polestar10 에 DPM(DB Performance Monitoring) 대상 등록.

- **엔드포인트**: **TBD** (추정 prefix: `/api/dpm/*`)
- **인증 필요**: `recipes/login.md` 먼저 실행
- **부작용**: 모니터링 대상 추가

## ⚠️ 현재 상태: 미확정

## 힌트 — 로그인 HAR 에서 관찰된 관련 엔드포인트

```
POST /api/dpm/custom/sql/count
```

→ DPM 서비스는 `/api/dpm/` prefix. 등록 엔드포인트는 별도 확인 필요.

## 확정 절차

1. **DPM (또는 DB 성능 관리) > 대상 관리** 메뉴 진입
2. **+ 등록** → DB 접속 정보 입력 (호스트·포트·DB명·계정·비밀번호·DB 종류)
3. **저장** → DevTools Network 에서 POST 요청 식별

## 레시피 (확정 후 작성)

```bash
# TODO: DevTools 캡처 후 작성
```

## UI Fallback

> **DPM > 관리대상** 에서 수동 등록. 접속 테스트가 성공해야 저장 가능.

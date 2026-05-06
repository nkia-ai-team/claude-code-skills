# weekly-report references

NKIA AI 팀 주간보고 자동화에 필요한 참고 자료.

## client_secret.json — 의도적 공유 (진짜 secret 아님)

이 디렉토리의 `client_secret.json` 은 NKIA AI 팀 주간보고 docs (Google Sheets / Calendar / Drive) 접근용 OAuth client.

**왜 public 레포에 있나** — Google OAuth 의 [installed application pattern](https://developers.google.com/identity/protocols/oauth2/native-app) 에 해당. Google 공식 문서:

> "The process [of installed apps] results in a client ID and, in some cases, a client secret, which you embed in the source code of your application. **In this context, the client secret is obviously not treated as a secret.**"

진짜 권한은 client_secret 이 아니라 **사용자별 OAuth consent + access/refresh token** 이 결정. 노출돼도:

- 다른 사용자 Google 데이터 접근 X (consent 한 사용자 본인 데이터만)
- API quota 가 client 단위라 누가 abusively 쓰면 우리 quota 소비 가능 정도
- scopes (sheets / calendar 일부) 한정이라 큰 손해 X

## False positive 알람 — 무시 OK

이 파일이 GitHub Secret Scanning / TruffleHog / 사내 보안 도구의 알람을 발생시킬 수 있으나 위 이유로 **dismiss / accepted risk 처리** 권장.

## 실제 권한 변경 시점

NKIA AI 팀 주간보고용 Google API 권한 (스코프 / 사용자 consent) 자체를 변경하려면 [Google Cloud Console — project nkia-492808](https://console.cloud.google.com/apis/credentials) 에서 진행.

이 client 가 실제로 abusive 사용 흔적이 발견되면 (Google Cloud Audit Log 모니터링) rotate 가능. 단 일상적 노출만으로는 rotate 불필요.

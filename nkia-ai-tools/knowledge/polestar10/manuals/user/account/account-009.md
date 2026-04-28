---
menu_path: "메시지파싱규칙"
feature: "메시지 파싱 규칙 매뉴얼"
admin_required: false
original_title: "메시지파싱규칙"
category: account
menu_path_verified: false
---
메시지 파싱 규칙 매뉴얼

수집된 로그 메시지를 Grok패턴을 이용해 분석 및 필드 추출을 하기 위한 파싱 규칙을 정의하는 방법을 안내합니다. 파싱 규칙은 java-grok 오픈소스 프로젝트에 존재하는 Grok 패턴 정의를 기반으로 작성됩니다.

메시지 파싱 규칙 매뉴얼

수집된 로그 메시지를 Grok패턴을 이용해 분석 및 필드 추출을 하기 위한 파싱 규칙을 정의하는 방법을 안내합니다. 파싱 규칙은 java-grok 오픈소스 프로젝트에 존재하는 Grok 패턴 정의를 기반으로 작성됩니다.

Grok 패턴이란?

Grok은 정규표현식을 사람이 읽기 쉬운 이름으로 추상화한 것으로, 텍스트에서 구조화된 데이터를 추출하는 데 사용됩니다. 각 패턴은 이름과 정규식으로 구성되며, 다양한 시스템 로그 메시지를 패턴화할 수 있습니다.

**기본 Grok 패턴 목록**

Grok은 정규표현식을 사람이 읽기 쉬운 이름으로 추상화한 것으로, 텍스트에서 구조화된 데이터를 추출하는 데 사용됩니다. 각 패턴은 이름과 정규식으로 구성되며, 다양한 시스템 로그 메시지를 패턴화할 수 있습니다.

| 패턴 이름      | 설명              | 예시 값           |
| ---------- | --------------- | -------------- |
| IP         | IPv4 혹은 IPv6 주소 | 127.0.0.1      |
| HOSTNAME   | 호스트명            | myserver.local |
| PATH       | 파일 경로           | /usr/local/bin |
| URIPATH    | URI 경로          | /api/logs      |
| URIPARAM   | URI 파라미터        | ?id=123        |
| DATE       | 날짜 (정해진 포맷)     | 2025-08-01     |
| TIME       | 시간 (HH:mm:ss)   | 12:34:56       |
| INT        | 정수              | 42             |
| NUMBER     | 숫자              | 3.14           |
| WORD       | 알파벳 문자열         | GET, POST      |
| GREEDYDATA | 가능한 한 많은 문자열    | 전체 로그 메시지 등    |

| 패턴 이름      | 설명              | 예시 값           |
| ---------- | --------------- | -------------- |
| IP         | IPv4 혹은 IPv6 주소 | 127.0.0.1      |
| HOSTNAME   | 호스트명            | myserver.local |
| PATH       | 파일 경로           | /usr/local/bin |
| URIPATH    | URI 경로          | /api/logs      |
| URIPARAM   | URI 파라미터        | ?id=123        |
| DATE       | 날짜 (정해진 포맷)     | 2025-08-01     |
| TIME       | 시간 (HH:mm:ss)   | 12:34:56       |
| INT        | 정수              | 42             |
| NUMBER     | 숫자              | 3.14           |
| WORD       | 알파벳 문자열         | GET, POST      |
| GREEDYDATA | 가능한 한 많은 문자열    | 전체 로그 메시지 등    |

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/account-009/media/image1.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>Java-grok 오픈소스 프로젝트 경로 https://github.com/thekrakken/java-grok</p></td>
</tr>
</tbody>
</table>

**사용자 정의 예시 패턴**

Grok은 정규표현식을 사람이 읽기 쉬운 이름으로 추상화한 것으로, 텍스트에서 구조화된 데이터를 추출하는 데 사용됩니다. 각 패턴은 이름과 정규식으로 구성되며, 다양한 시스템 로그 메시지를 패턴화할 수 있습니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/account-009/media/image1.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>샘플 로그 : $ wget http://POLSETAR_AP_IP/NNPAgend_SMS_Linux64_3.4.8.4.7_5.tar.gz<br />
Grok 패턴: $ wget %{URIPROTO:protocol}://%{URIHOST:host}/%{GREEDYDATA:file_name}</p>
<p>추출 결과</p>
<p>protocol : http</p>
<p>host : POLSETAR_AP_IP</p>
<p>file_name : NNPAgend_SMS_Linux64_3.4.8.4.7_5.tar.gz</p></td>
</tr>
</tbody>
</table>

**파싱 규칙 작성 가이드**

파싱 규칙 입력창에는 하나의 메시지 패턴에 대응하는 Grok 표현식을 입력합니다.  
여러 로그 포맷이 있을 경우 각각에 대해 규칙을 따로 정의합니다.  
불필요한 공백 또는 $ 등의 특수문자는 이스케이프 처리(\\$)해야 합니다.


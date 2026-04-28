---
menu_path: "알람컨디션로그표현식"
feature: "알람 컨디션 로그 표현식"
admin_required: false
original_title: "알람컨디션로그표현식"
category: alert
menu_path_verified: false
---
알람 컨디션 로그 표현식

알람 컨디션 로그 표현식을 통해 알람 내용을 사용의 목적에 맞게 조합할 수 있습니다.

또한 문자열 처리를 위한 함수를 내장하고 있어서 이를 활용할 수 있습니다.

알람 컨디션 로그의 표현식 사용법은 아래 표를 참고하시기 바랍니다.

알람 컨디션 로그 표현식

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/alert-016/media/image3.png" style="width:0.21667in;height:0.21667in" />복합알람에서 제외되는 표현식</p>
<p>${resourceId}, ${resourceName}, ${ipAddress}, ${resourceTypeName}, ${resourceDescription}, ${hostname}, ${resourceType}, ${os}, ${vendor}, ${ifAlias}, ${ifName}, ${ifIpAddress}, ${lbVirtualServerName}, ${lbVirtualServerIp}, ${lbVirtualServerPort}, ${lbPhysicalServerName}, ${lbPhysicalServerIp}, ${lbPhysicalServerPort}</p></td>
</tr>
</tbody>
</table>

| 표현식                                       | 설명                                             | 예                                                                               |
| ----------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------- |
| ${defaultConditionLog}                    | 내부적으로 설정되어 있는 컨디션 로그 기본값                       | 사용률 \[82 % (\> 80 %)\]                                                          |
| ${sourceValue}                            | 측정값                                            | 90 %                                                                            |
| ${threshold}                              | 알람 정의 시 설정한 임계값                                | 90%                                                                             |
| ${threshold2}                             | 알람 정의 시 수치 임계값을 두개 설정한 경우(범위 안, 범위 밖) 두 번째 임계값 | 90%                                                                             |
| ${alarmName}                              | 사용자가 입력한 알람 이름                                 | CPU 사용률 High                                                                    |
| ${alarmDescription}                       | 사용자가 입력한 알람 설명                                 | CPU 사용률 높은 상태. 프로세스 점검 필요함.                                                     |
| ${alarmDate}                              | 알람 발생일자                                        | Tue Oct 07 14:50:35 KST 2014                                                    |
| ${alarmDetailLink}                        | 알람 상세보기 페이지 링크 URL                             | https://221.141.xxx.xxx/new-page/viewer?referrer=...                            |
| ${formatAlarmDate('yyyy-MM-dd HH:mm:ss')} | 패턴으로 포맷팅된 알람 발생일자. 날짜 패턴은 아래 날짜 패턴 표를 참고       | 2014-09-18 14:45:23                                                             |
| ${formatAlarmDate(HH:mm')}                | 패턴으로 포맷팅된 알람 발생일자. 날짜 패턴은 아래 날짜 패턴 표를 참고       | 14:45                                                                           |
| ${severity}                               | 알람 심각도                                         | 심각                                                                              |
| ${conditions}                             | 설정된 알람 컨디션 정보                                  | 사용률 Threshold \[TROUBLE (\> 90.0 %), ATTENTION (\> 80.0 %), CLEAR (\< 70.0 %)\] |
| ${resourceId}                             | 알람 발생한 리소스 ID                                  | 3892                                                                            |
| ${resourceName}                           | 리소스 이름                                         | WIN-ED8VVQVE3QE                                                                 |
| ${resourceDescription}                    | 리소스 설명                                         | WIN-ED8VVQVE3QE(model:RHEV Hypervisor, vendor: Red Hat) server information.     |
| ${resourceType}                           | 리소스 타입                                         | 서버                                                                              |
| ${hostname}                               | 플랫폼 리소스 호스트명 가상머신 리소스는 구성 정보의 물리 서버 호스트명이 표시   | WIN-ED8VVQVE3QE                                                                 |
| ${ipAddress}                              | 플랫폼 리소스 IP                                     | 127.0.0.1                                                                       |
| ${availability}                           | 리소스의 현재 가용성 상태                                 | UP                                                                              |
| ${os}                                     | 서버플랫폼 리소스의 OS종류                                | WINDOWS                                                                         |
| ${vendor}                                 | 서버, 네트워크장비, ICMP노드 플랫폼 리소스의 제조사                | CiscoSystems                                                                    |
| ${ifAlias}                                | 네트워크장비 포트에 설정된 별칭                              | Ethernet                                                                        |
| ${ifName}                                 | 네트워크 Interface 이름                              | Ethernet                                                                        |
| ${ifIpAddress}                            | 네트워크 Interface IP 주소                           | 127.0.0.1                                                                       |
| ${lbVirtualServerName}                    | LB Virtual Server 이름                           | net\_179\_11                                                                    |
| ${lbVirtualServerIp}                      | LB Virtual Server IP                           | 127.0.0.1                                                                       |
| ${lbVirtualServerPort}                    | LB Virtual Server 포트                           | 80                                                                              |
| ${lbPhysicalServerName}                   | LB Physical Server 이름                          | svr2\_2                                                                         |
| ${lbPhysicalServerIp}                     | LB Physical Server IP                          | 127.0.0.1                                                                       |
| ${lbPhysicalServerPort}                   | LB Physical Server 포트                          | 80                                                                              |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |
|                                           |                                                |                                                                                 |

알람 컨디션 로그 표현식 함수

<table>
<thead>
<tr class="header">
<th>함수</th>
<th>설명</th>
<th>예</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>formatDate(Date date, String pattern)</td>
<td>주어진 날짜를 pattern으로 포맷팅 처리<br />
날짜 패턴은 아래 날짜 패턴 표를 참고</td>
<td></td>
</tr>
<tr class="even">
<td>substring(String str, int start)</td>
<td>주어진 문자열을 시작지점 이후로 잘라냄.</td>
<td>substring(null, *) = null, substring('', *) = '',<br />
substring('abc', 0) = 'abc',substring('abc', 2) = 'c',<br />
substring('abc', 4) = '', substring('abc', -2) = 'bc',<br />
substring('abc', -4) = 'abc'</td>
</tr>
<tr class="odd">
<td>substring(String str, int start, int end)</td>
<td>주어진 문자열을 시작지점부터 완료지점까지 잘라냄.</td>
<td>substring(null, *, *) = null, substring('', *, *) = '',<br />
substring('abc', 0, 2) = 'ab', substring('abc', 2, 0) = '',<br />
substring('abc', 2, 4) = 'c', substring('abc', 4, 6) = '',<br />
substring('abc', 2, 2) = '', substring('abc', -2, -1) = 'b'<br />
substring('abc', -4, 2) = 'ab'</td>
</tr>
<tr class="even">
<td>substringBefore(String str, String separator)</td>
<td>주어진 문자열을 처음 발견되는 구분자까지 잘라냄.<br />
구분자는 결과에 포함되지 않음</td>
<td>substringBefore(null, *) = null, substringBefore('', *) = '',<br />
substringBefore('abc', 'a') = '',substringBefore('abcba', 'b') = 'a',<br />
substringBefore('abc', 'c') = 'ab', substringBefore('abc', 'd') = 'abc',<br />
substringBefore('abc', '') = '', substringBefore('abc', null) = 'abc'</td>
</tr>
<tr class="odd">
<td>substringBeforeLast(String str, String separator)</td>
<td>주어진 문자열을 마지막 발견되는 구분자까지 잘라냄.<br />
구분자는 결과에 포함되지 않음</td>
<td>substringBeforeLast(null, *) = null, substringBeforeLast("", *) = "",<br />
substringBeforeLast("abcba", "b") = "abc",substringBeforeLast("abc", "c") = "ab",<br />
substringBeforeLast("a", "a") = "", substringBeforeLast("a", "z") = "a",<br />
substringBeforeLast("a", null) = "a", substringBeforeLast("a", "") = "a"</td>
</tr>
<tr class="even">
<td>substringAfter(String str, String separator)</td>
<td>주어진 문자열을 처음 발견되는 구분자부터 마지막까지 잘라냄.<br />
구분자는 결과에 포함되지 않음</td>
<td>substringAfter(null, *) = null, substringAfter('', *) = '',<br />
substringAfter(*, null) = '', substringAfter('abc', 'a') = 'bc',<br />
substringAfter('abcba', 'b') = 'cba', substringAfter('abc', 'c') = ''<br />
substringAfter('abc', 'd') = '', substringAfter('abc', '') = 'abc'</td>
</tr>
<tr class="odd">
<td>substringAfterLast(String str, String separator)</td>
<td>주어진 문자열을 마지막 발견되는 구분자부터 마지막까지 잘라냄.<br />
구분자는 결과에 포함되지 않음</td>
<td>substringAfterLast(null, *) = null, substringAfterLast('', *) = '',<br />
substringAfterLast(*, '') = '', substringAfterLast(*, null) = '',<br />
substringAfterLast('abc', 'a') = 'bc', substringAfterLast('abcba', 'b') = 'a',<br />
substringAfterLast('abc', 'c') = '', substringAfterLast('a', 'a') = '',<br />
substringAfterLast('a', 'z') = ''</td>
</tr>
<tr class="even">
<td>substringBetween<br />
(String str, String open, String close)</td>
<td>주어진 문자열에서 두 개의 문자열 사이에 포함된 결과를 반환.<br />
첫번째 매칭되는 결과만 반환됨</td>
<td>substringBetween('wx[b]yz', '[', ']') = 'b', substringBetween(null, *, *) = null,<br />
substringBetween(*, null, *) = null, substringBetween(*, *, null) = null,<br />
substringBetween('', '', '') = '', substringBetween('', '', ']') = null,<br />
substringBetween('', '[', ']') = null, substringBetween('yabcz', '', '') = '',<br />
substringBetween('yabcz', 'y', 'z') = 'abc',substringBetween('yabczyabcz', 'y', 'z') = 'abc'</td>
</tr>
<tr class="odd">
<td>substringBetweenIfMatch<br />
(String str, String open, String close)</td>
<td>substringBetween과 동일함.<br />
단,매칭 결과가 존재하지 않는 경우 기존 문자열을 그대로 반환함.</td>
<td>substringBetweenIfMatch('yabcz', 'f', 'i') = ' yabcz'</td>
</tr>
<tr class="even">
<td>replaceAll(String str, String searchText, String replacement)</td>
<td>주어진 문자열에서 특정 문자열을 모두 치환함.</td>
<td>replaceAll(null, *, *) = null, replaceAll('', *, *) = '',<br />
replaceAll('any', null, *) = 'any', replaceAll('any', *, null)= 'any',<br />
replaceAll('any', '', *) = 'any', replaceAll('aba', 'a', null) = 'aba',<br />
replaceAll('aba', 'a', '') = 'b', replaceAll('aba', 'a', 'z') = 'zbz’</td>
</tr>
</tbody>
</table>

날짜 패턴

| 문자 | 설명                | 예                       |
| -- | ----------------- | ----------------------- |
| G  | 연대                | AD                      |
| y  | 연도                | 2014; 14                |
| M  | 월                 | July; Jul; 07           |
| w  | 연내의 주             | 27                      |
| W  | 월내의 주             | 2                       |
| D  | 연내의 일             | 189                     |
| d  | 월내의 일             | 10                      |
| E  | 요일                | Tuesday; Tue            |
| a  | AM/PM             | PM                      |
| H  | 일내의 시간(0-23)      | 0                       |
| k  | 일내의 시간(1-24)      | 24                      |
| K  | 오전/오후에서의 시간(0-11) | 0                       |
| h  | 오전/오후에서의 시간(1-12) | 12                      |
| m  | 분                 | 30                      |
| s  | 초                 | 55                      |
| S  | 밀리초               | 978                     |
| z  | 타임존               | 한국 표준시; KST; GMT +09:00 |
| Z  | 타임존               | \+0900                  |


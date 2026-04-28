---
menu_path: "KCMAgent사전설치환경조사"
feature: "사전 설치 환경 조사"
admin_required: true
original_title: "KCMAgent사전설치환경조사"
category: agent-install
menu_path_verified: false
---
사전 설치 환경 조사

KCM Agent 설치 전 사전에 필요한 환경정보 입니다.

KCMAgent 지원버전에 따라 Agent 설치가능여부를 확인하시면 됩니다.

에이전트 지원 쿠버네티스 버전

| 쿠버네티스 버전 | 1.25+ |
| -------- | ----- |
| Helm     | v3    |

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-008/media/image5.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>쿠버네티스 설치 및 Helm, 쿠버네티스 운영을 위한 kubectl 설치 과정은 생략합니다. 에이전트가 지원하는 버전의 쿠버네티스와 Helm이 설치되어 있는 환경에서 에이전트 설치가 가능합니다.</p>
<p>[version 확인방법]</p>
<p>#kubectl version</p>
<p>#helm version</p></td>
</tr>
</tbody>
</table>

설치 전 방화벽 확인

방화벽 확인

KCM Agent는 KCM 수집서버와 통신하기 위해 TCP 7575 포트를 사용하며, 해당포트가 사용될 수 있도록 방화벽 설정을 확인합니다. 포트 번호는 변경될 수 있으니 설치 전 수집서버의 KCM 설정 정보를 확인하세요

<table>
<thead>
<tr class="header">
<th>사용포트</th>
<th>SOURCE</th>
<th>방향</th>
<th>DESTINATION</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>7575</p>
<p>(TCP)</p></td>
<td>Agent</td>
<td>-&gt;</td>
<td>Back-End</td>
<td>구성/성능 수집</td>
</tr>
</tbody>
</table>


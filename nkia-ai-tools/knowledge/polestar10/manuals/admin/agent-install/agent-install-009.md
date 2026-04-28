---
menu_path: "KCMAgent삭제"
feature: "KCM Agent 삭제"
admin_required: true
original_title: "KCMAgent삭제"
category: agent-install
menu_path_verified: false
---
KCM Agent 삭제

KCM agent 삭제

<table>
<thead>
<tr class="header">
<th>1. Agent 삭제 명령 실행: --uninstall</th>
<th></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td></td>
<td><p>Agent 설치 디렉토리(예: /usr/nkia/kcmagent) 디렉토리로 이동합니다.</p>
<p>“--uninstall” 옵션을 이용하여 Agent를 삭제합니다.</p>
<p>[삭제 예시]</p>
<p>#&gt;cd /usr/nkia/kcmagent/</p>
<p>#&gt;./kcm-aio-install-online.sh –uninstall</p></td>
</tr>
<tr class="even">
<td>2. 삭제확인: ls -al /usr/nkia/kcmagent/</td>
<td></td>
</tr>
<tr class="odd">
<td></td>
<td><p>삭제확인 방법은 아래와 같습니다.</p>
<p>1) #&gt;cd /usr/nkia/kcmagent/</p>
<p>2) #&gt;ls -al 실행합니다.</p>
<p>2) 하위 디렉토리인 ./log 디렉토리 와 설치 file 만 존재하는지 확인 합니다.</p></td>
</tr>
</tbody>
</table>


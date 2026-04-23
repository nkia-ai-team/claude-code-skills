---
menu_path: "ls<br />"
feature: "lucida-for-docker<br />"
admin_required: true
original_title: "AP설치가이드"
category: agent-install
menu_path_verified: false
---
간편가이드

AP 설치를 위한 간편가이드입니다.

아래 절차대로 진행하시고 각 절차별 상세 내용은 하위 메뉴에서 확인하시기 바랍니다.

<table>
<thead>
<tr class="header">
<th>1. 설치 파일 준비</th>
<th></th>
<th></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>설치파일 다운로드</td>
<td><p>Polestar 10 공식 파일서버에서 최신파일을 다운로드<br />
설치파일(예시) :</p>
<p>polestar10.x.x_yyyymmddhhmmss.tar.gz</p></td>
<td></td>
</tr>
<tr class="even">
<td>설치파일 압축해제</td>
<td># tar xvzf polestar10*.tar.gz<br />
# ls<br />
lucida-for-docker<br />
pre-installer</td>
<td></td>
</tr>
<tr class="odd">
<td>2. 사전 설치 환경 조사</td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td><p># ./pre-install-check.sh</p>
<p>[파일위치]<br />
pre-installer/</p></td>
<td><p>[사전 설치 환경 조사]</p>
<p>세부 가이드 참조</p></td>
</tr>
<tr class="odd">
<td>3. 사전 설치</td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td><p># ./pre-install.sh</p>
<p>[파일위치]<br />
pre-installer/</p></td>
<td><p>[사전 설치]</p>
<p>세부 가이드 참조</p></td>
</tr>
<tr class="odd">
<td>4. Polestar 10 설치</td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td><p>#./lucida-install.sh</p>
<p>[파일위치]<br />
lucida-for-docker/installer/</p></td>
<td><p>[Polestar 10 설치]</p>
<p>세부 가이드 참조</p></td>
</tr>
<tr class="odd">
<td>5. Polestar 10 기동</td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td><p># ./start.sh</p>
<p>[파일위치]<br />
lucida-for-docker/polestar/bin/</p></td>
<td><p>[Polestar 10 기동]</p>
<p>세부 가이드 참조</p></td>
</tr>
<tr class="odd">
<td>6. Polestar 10 중지</td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td><p>#./stop.sh</p>
<p>[파일위치]<br />
lucida-for-docker/polestar/bin/</p></td>
<td><p>[Polestar 10 중지]</p>
<p>세부 가이드 참조</p></td>
</tr>
</tbody>
</table>


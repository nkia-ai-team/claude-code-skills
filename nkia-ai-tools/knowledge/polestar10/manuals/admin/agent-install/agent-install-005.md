---
menu_path: "AP원복가이드"
feature: "간편가이드"
admin_required: true
original_title: "AP원복가이드"
category: agent-install
menu_path_verified: false
is_menu: false
---
간편가이드

AP 설치후 원복이 필요한 경우 아래 절차에 따라 진행하시기 바랍니다.

아래 절차중 세부내용은 AP 설치 가이드를 참조하시면 됩니다.

<table>
<thead>
<tr class="header">
<th>1. Polestar 10 원복</th>
<th></th>
<th></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>중지</td>
<td><p>#./stop.sh</p>
<p>[파일위치]<br />
lucida-for-docker/polestar/bin/</p></td>
<td><p>[Polestar 10 중지]</p>
<p>세부 가이드 참조</p></td>
</tr>
<tr class="even">
<td><p>설치파일</p>
<p>복구</p></td>
<td><p>설치 디렉토리로 이동 (예시 : /app)</p>
<p># cd /app</p>
<p># mv lucida-for-docker ./backup/20240604</p>
<p>복구할 백업디렉토리 선택</p>
<p># mv ./backup/20240516/lucida-for-docker /app</p></td>
<td></td>
</tr>
<tr class="odd">
<td><p>컨테이너</p>
<p>이미지</p>
<p>복구</p></td>
<td><p>현재버전 이미지를 로컬 리포지토리에서 삭제</p>
<p># docker rmi -f $(docker images -aq)</p>
<p>복구 버전 이미지를 로컬 리포지토리에 로딩</p>
<p># cd lucida-for-docker/installer</p>
<p># ./lucida-images-load.sh</p></td>
<td></td>
</tr>
<tr class="even">
<td>DB 복구</td>
<td># ./mongodb.sh -restore</td>
<td><p>[Polestar 10 DB 복구]</p>
<p>세부 가이드 참조</p></td>
</tr>
<tr class="odd">
<td>2. Polestar 10 기동</td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td># ./start.sh</td>
<td><p>[Polestar 10 기동]</p>
<p>세부 가이드 참조</p></td>
</tr>
</tbody>
</table>


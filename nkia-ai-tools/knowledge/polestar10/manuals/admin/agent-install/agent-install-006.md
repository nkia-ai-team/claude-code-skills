---
menu_path: "AP패치가이드"
feature: "간편가이드"
admin_required: true
original_title: "AP패치가이드"
category: agent-install
menu_path_verified: false
---
간편가이드

AP 설치후 업데이트 버전의 패치가 필요한 경우 아래 절차에 따라 진행하시기 바랍니다.

아래 절차중 세부내용은 AP 설치 가이드를 참조하시면 됩니다.

<table>
<thead>
<tr class="header">
<th>1. Polestar 10 백업</th>
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
<td><p>DB 백업</p>
<p>(옵션)</p></td>
<td># ./mongodb.sh -backup</td>
<td><p>[Polestar 10 DB 백업]</p>
<p>세부 가이드 참조</p></td>
</tr>
<tr class="odd">
<td><p>설치파일</p>
<p>백업</p></td>
<td><p>설치디렉토리 이동(예&gt; cd /app)</p>
<p># ls</p>
<p>lucida-for-docker</p>
<p>pre-installer</p>
<p>polestar10.1.0_20240516085509.tar.gz</p>
<p># mkdir -p ./backup/20240516</p>
<p># mv lucida-for-docker pre-installer polestar10*.tar.gz ./backup/20240516/</p></td>
<td></td>
</tr>
<tr class="even">
<td><p>패치파일</p>
<p>압축해제</p></td>
<td><p># ls (예&gt; /app)</p>
<p>기존설치 디렉토리 및 파일이 없어야 함.</p>
<p>신규 패치파일 다운로드</p>
<p># tar xvzf polestar101.0*.tar.gz (패치파일)</p>
<p># ls</p>
<p>lucida-for-docker</p>
<p>pre-installer</p>
<p>polestar10.1.0_20240518143311.tar.gz</p></td>
<td></td>
</tr>
<tr class="odd">
<td>2. Polestar 10 설치</td>
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
<td>3. Polestar 10 환경 동기화(옵션)</td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td><p>#./lucida-setting-updater.sh</p>
<p>[파일위치]<br />
lucida-for-docker/installer/</p>
<p># manager.sh</p>
<p>[파일위치]<br />
lucida-for-docker/polestar/bin</p></td>
<td><p>[기존설정 가져오기]<br />
대상 : .env, application.env</p>
<p>설치후 별도 설정을 한 경우</p>
<p>해당 키값을 마이그레이션 제공</p>
<p>[도커 볼륨 초기화]</p>
<p>휘발성 볼륨이므로 모두 삭제 또는 kafka, kafka-streams, schema-registry, zookeeper 삭제 권장</p></td>
</tr>
<tr class="odd">
<td>4. Polestar 10 기동</td>
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
</tbody>
</table>


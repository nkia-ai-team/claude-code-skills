---
menu_path: "POLESTAR10중지"
feature: "Polestar 10 중지"
admin_required: true
original_title: "POLESTAR10중지"
category: agent-install
menu_path_verified: false
---
Polestar 10 중지

Polestar 10 어플리케이션을 중지할 때 필요한 가이드를 설명합니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-014/media/image3.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>Polestar 10 서비스 이름과 해당 컨테이너를 아래와 같이 정의합니다.</p>
<p>아래표와 같이 플랫폼 서비스와 도메인 서비스로 크게 2개로 분류합니다.</p>
<table>
<thead>
<tr class="header">
<th>1. 플랫폼 서비스</th>
<th>mongodb, traefik, kafka, zookeeper, schema-registry, yorkie, akhq, emqx, envoy, aiserver, redis, redis-access-control, redis-aiops, elasticsearch-aiops, …</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>2. 도메인 서비스</td>
<td><strong>(공통) aiops, alarm, audit, automap, builder, event, loader, management-service, measurement, notification, performance, topology, widget, mfa-account, mfa-alarm, mfa-automap, mfa-dashboard, mfa-host, mfa-notification, mfa-performance, mfa-topology, mfa-widget, …</strong></td>
</tr>
<tr class="even">
<td></td>
<td><strong>(모듈) sms, apm, automation, dpm, kcm, nms, mfa-apm, mfa-automation, mfa-dpm, mfa-kcm, mfa-nms, mfa-sms,…</strong></td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

아래 스크립트를 실행하여 기동합니다.

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>[예시] 단일모드로 중지시</p>
<p># ./stop.sh</p>
<p>[+] Running 1/1</p>
<p>√ Container lucida-emqx Removed 0.0s</p>
<p>[+] Running 4/4</p>
<p>√ Container lucida-zookeeper-1 Removed 0.0s</p>
<p>--- 중략 ---</p>
<p>[+] Running 2/2</p>
<p>√ Container lucida-mongodb-1 Removed 0.0s</p>
<p>√ Container lucida-mongodb-initializer Removed 0.7s</p>
<p>Polestar 10 is loading … [/]</p>
<p>[+] Running 26/26</p>
<p>--- 중략 ---</p>
<p>√ Container polestar-apm Removed 0.5s</p>
<p>√ Container polestar-alarm Removed 0.3s</p>
<p>√ Container polestar-event Removed 0.5s</p>
<p>√ Container polestar-measurement Removed 0.2s</p>
<p>[+] Polestar 10 has been stoped. [ok]</p>
<p>[예시] 클러스터 모드 중지시</p>
<p># ./stop.sh</p>
<p>[+] Detected cluster mode with 3 nodes.</p>
<p>[+] Executing stack-remove.sh for cluster mode.</p>
<p>Loading environment variables...</p>
<p>Loading environment variables from .env ...</p>
<p>Resolving variable references...</p>
<p>Environment variables loaded successfully.</p>
<p>…</p>
<p>[+] Polestar 10 has been stoped. [ok]</p></td>
<td><p>[파일 위치]</p>
<p>lucida-for-docker/polestar/bin</p>
<p>[실행 절차]</p>
<p>기동순서와 반대로 진행됩니다.</p>
<p>단일모드일 경우</p>
<p>1. 도메인 서비스 중지</p>
<p>2. 플랫폼 서비스 중지</p>
<p>클러스터 모드일 경우</p>
<p>1. 클러스터 모드 판단기준 : .env파일에 아래 항목에 IP가 2개이상 설정된 경우</p>
<p>ACCESS_DOMAIN_RULES</p>
<p>2. ./stack-remove.sh 실행됨</p></td>
</tr>
</tbody>
</table>

중지 옵션

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./stop.sh -help</p>
<p>Usage: ./stop.sh [-platform] [-domain]</p>
<p>-platform : Stop only the platform services within ap</p>
<p>-domain : Stop only the domain services within ap</p></td>
<td>사용법 도움말</td>
</tr>
<tr class="even">
<td># ./stop.sh</td>
<td><p>모든 서비스 중지</p>
<p>플랫폼 서비스와 도메인서비스 모두 중지</p></td>
</tr>
<tr class="odd">
<td># ./stop.sh -platform</td>
<td><p>플랫폼 서비스만 중지</p>
<p>(클러스터모드에서는 미지원)</p></td>
</tr>
<tr class="even">
<td># ./stop.sh -domain</td>
<td><p>도메인 서비스만 중지</p>
<p>(클러스터모드에서는 미지원)</p></td>
</tr>
</tbody>
</table>


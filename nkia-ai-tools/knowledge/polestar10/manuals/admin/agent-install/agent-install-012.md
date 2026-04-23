---
menu_path: "POLESTAR10기동"
feature: "Polestar 10 기동"
admin_required: true
original_title: "POLESTAR10기동"
category: agent-install
menu_path_verified: false
---
Polestar 10 기동

Polestar 10 어플리케이션을 기동하고 중지할 때 필요한 가이드를 설명합니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-012/media/image3.png" style="width:0.21667in;height:0.21667in" />노트</p>
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
<td>(공통) aiops, alarm, audit, automap, builder, event, loader, management-service, measurement, notification, performance, topology, widget, mfa-account, mfa-alarm, mfa-automap, mfa-dashboard, mfa-host, mfa-notification, mfa-performance, mfa-topology, mfa-widget, …</td>
</tr>
<tr class="even">
<td></td>
<td>(모듈) sms, apm, automation, dpm, kcm, nms, mfa-apm, mfa-automation, mfa-dpm, mfa-kcm, mfa-nms, mfa-sms,…</td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-012/media/image4.png" style="width:0.21667in;height:0.21667in" />주의</p>
<p><strong>클러스터 모드일 경우에는 모든 노드에서 Polestar 10 설치가 진행후 기동해야 합니다.</strong></p>
<p><strong>Polestar 10 기동 및 중지는 클러스터 노드중 한 노드에서 진행하면 됩니다.</strong></p>
<p><strong>접속 URL은 클러스터 노드 모든 IP로 동일하게 접속이 가능합니다.</strong></p>
<p><strong>예&gt; 클러스터 노드가 192.168.213.1, 192.168.213.2, 192.168.213.3 일 경우</strong></p>
<p><strong>https:// 192.168.213.1, https:// 192.168.213.2, https:// 192.168.213.3 으로 동일한 화면으로 접속이 됩니다.</strong></p></td>
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
<td><p>[예시] 단일모드로 기동시</p>
<p># ./start.sh</p>
<p>[+] Running 2/2</p>
<p>√ Container lucida-mongodb-1 Started 0.0s</p>
<p>√ Container lucida-mongodb-initializer Started 0.7s</p>
<p>[+] Running 1/1</p>
<p>√ Container lucida-emqx Started 0.0s</p>
<p>[+] Running 4/4</p>
<p>√ Container lucida-zookeeper-1 Started 0.0s</p>
<p>--- 중략 ---</p>
<p>Polestar 10 is loading … [/]</p>
<p>[+] Running 26/26</p>
<p>--- 중략 ---</p>
<p>√ Container polestar-apm Started 0.5s</p>
<p>√ Container polestar-alarm Started 0.3s</p>
<p>√ Container polestar-event Started 0.5s</p>
<p>√ Container polestar-measurement Started 0.2s</p>
<p>[+] Polestar 10 has been started. [ok]</p>
<p>[+] Access it at https://192.168.213.172 [ok]</p>
<p>[예시] 클러스터 모드 기동시</p>
<p># ./start.sh</p>
<p>[+] Detected cluster mode with 3 nodes.</p>
<p>[1/3] All nodes have valid [node-alias] labels.</p>
<p>[2/3] Manager node count is sufficient (3).</p>
<p>[3/3] All nodes are in a healthy state.</p>
<p>Start in cluster mode? (Y/n): y</p>
<p>Starting Docker Swarm mode...</p>
<p>…</p>
<p>[+] Polestar 10 has been started. [ok]</p></td>
<td><p>[파일 위치]</p>
<p>lucida-for-docker/polestar/bin/</p>
<p>[실행 절차]</p>
<p>1. 단일모드일 경우</p>
<p>1-1 플랫폼 서비스 기동</p>
<p>1-2 도메인 서비스 기동</p>
<p>2. 클러스터 모드일 경우</p>
<p>2-1 클러스터 모드 판단기준 : .env파일에 아래 항목에 IP가 2개이상 설정된 경우</p>
<p>ACCESS_DOMAIN_RULES</p>
<p>2-2 기동전에 클러스터 조건을 확인함</p>
<p>조건1: 필수 노드 레이블(node-alias)이 설정되어 있는지 확인</p>
<p>조건2: 매니저 노드 수 확인(최소 3개이상)</p>
<p>조건3: 노드 상태 확인</p>
<p>위 3가지 조건을 확인후 사용자에게 실행할지 확인후 진행함.</p>
<p>조건1은 필수이므로 기동이 안됨</p>
<p>조건2, 조건3은 사용자에게 문의후 진행</p>
<p>2-3 ./stack-depols.sh로 기동됨</p></td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-012/media/image3.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>Polestar 10 기동시 도커가 기동되어 있어야 합니다.</p>
<p>도커는 초기설치후 서버 재기동시 자동으로 재기동이 되도록 설정이 됩니다.</p>
<p>[참조] pre-installer/docker/docker-install-bin.sh</p>
<p>1. /etc/systemd/system/docker.service 파일 생성</p>
<p>2. systemctl daemon-reload</p>
<p>3. systemctl enable docker</p>
<p>4. systemctl start docker</p>
<p>하지만, 도커가 정상적으로 기동되어 있지 않을 경우나 도커가 중지된 상태에서 Polestar 10기동시 아래와 같은 에러가 출력되므로 도커를 기동하고 스크립트를 다시 실행해야 합니다.</p>
<p>&lt;예시&gt;</p>
<p>ERROR: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?</p>
<p>errors pretty printing info</p>
<p>[-] Cannot connect to the docker daemon. [fail]</p>
<p>Please check the docker status and start docker using the following commands:</p>
<p># systemctl status docker (check docker status)</p>
<p># systemctl start docker (start docker)</p></td>
</tr>
</tbody>
</table>

기동 옵션

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./start.sh --help</p>
<p>Usage: ./start.sh [OPTIONS]</p>
<p>Options:</p>
<p>platform : Start the platform services</p>
<p>domain : Start the domain services</p>
<p>--help : Display this help message</p></td>
<td>사용법 도움말</td>
</tr>
<tr class="even">
<td># ./start.sh</td>
<td><p>모든 서비스 기동</p>
<p>플랫폼 서비스와 도메인 서비스 기동</p>
<p>(단일 모드와 클러스터 모드 모두 사용)</p></td>
</tr>
<tr class="odd">
<td># ./start.sh platform</td>
<td><p>플랫폼 서비스 모두 기동</p>
<p>(클러스터모드에서는 미지원)</p></td>
</tr>
<tr class="even">
<td># ./start.sh domain</td>
<td><p>도메인 서비스 모두 기동</p>
<p>(클러스터모드에서는 미지원)</p></td>
</tr>
</tbody>
</table>

서비스 기동 상태 점검

Polestar 10이 정상적으로 기동이 되었는지 각 서비스별로 확인할 수 있습니다.

\[fail\] 서비스가 있는 경우 해당 서비스 컨테이너의 정상 기동여부를 확인하고 컨테이너별 로그를 확인하여 조치해야 합니다.

클러스터 모드일 경우 현재 지원되지 않습니다.(스웜 비주얼라이저로 서비스 상태 모니터링 가능함)

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>Usage: ./service.sh [COMMAND]</p>
<p>Command:</p>
<p>status Show status of all services</p>
<p>list List all services</p>
<p>Examples:</p>
<p>./service.sh status</p>
<p>./service.sh list</p>
<p>./service.sh --help</p></td>
<td>사용법 도움말</td>
</tr>
<tr class="even">
<td><p>[예시]</p>
<p>#./service.sh status</p>
<p>SERVICE NAME STATE</p>
<p>akhq polestar-akhq-1 running</p>
<p>app-aiops polestar-app-aiops-1 running</p>
<p>app-alarm polestar-app-alarm-1 running</p>
<p>app-apm polestar-app-apm-1 running</p>
<p>app-audit polestar-app-audit-1 running</p>
<p>app-automap polestar-app-automap-1 running</p>
<p>…</p></td>
<td><p>[파일위치]</p>
<p>lucida-for-docker/polestar/bin/</p>
<p>[항목 설명]</p>
<p>SERVICE : 서비스 이름</p>
<p>NAME : 컨테이너 이름</p>
<p>STATE : 서비스 상태(running, not running)</p>
<p>CREATED AT : 서비스 기동시간</p>
<p>IMAGE : 서비스 이미지 이름</p></td>
</tr>
</tbody>
</table>


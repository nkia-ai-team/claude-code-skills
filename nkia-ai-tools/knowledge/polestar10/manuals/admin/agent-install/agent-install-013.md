---
menu_path: "POLESTAR10설치"
feature: "Polestar 10 설치"
admin_required: true
original_title: "POLESTAR10설치"
category: agent-install
menu_path_verified: false
---
Polestar 10 설치

사전 설치 환경에 필요한 모든 설치가 완료된 이후에 Polestar 10 어플리케이션을 설치하는 가이드입니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-013/media/image3.png" style="width:0.21667in;height:0.21667in" />주의</p>
<p>1. 사전 설치 환경조사에서 모든 설치가 완료된 상태에서 진행해야 합니다.</p>
<p><strong>2. 클러스터 모드일 경우에는 모든 노드에서 동일한 과정으로 설치를 진행해야 합니다.</strong></p>
<p><strong>- 설치후 기동 및 중지는 노드중 아무 곳이나 한 노드에서 진행하면 됩니다.</strong></p>
<p><strong>- 접속은 클러스터 노드 모든 IP로 동일하게 접속이 가능합니다.</strong></p></td>
</tr>
</tbody>
</table>

아래 스크립트를 실행하여 자동으로 설치를 진행합니다.

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./lucida-install.sh</p>
<p>----------------------------------------------</p>
<p>POLESTR 10 Installation</p>
<p>----------------------------------------------</p>
<p>[1/5] Checking pre-installation...</p>
<p>[2/5] Removing all existing docker images...</p>
<p>To update docker images, all images must be removed.</p>
<p>[+] Remove all docker images? (Y/n) y</p>
<p>[100% 56/56] tchiotludo/akhq:0.24.0 is deleted.</p>
<p>[3/5] Loading docker images...</p>
<p>[100% 57/57] elasticsearch_7.17.14.tar is loading.</p>
<p>[4/5] Configuring the .env file...</p>
<p>This server ip addresses:</p>
<p>1 : 192.168.200.97</p>
<p>2 : 172.26.0.1</p>
<p>3 : 172.17.0.1</p>
<p>4 : 172.18.0.1</p>
<p>5 : input manually</p>
<p>[+] Select the service IP: 1</p>
<p>[+] Is this a cluster mode(swarm mode)? (Y/n) n</p>
<p>[5/5] Signing SSL certificate...</p>
<p>[+] Polestar 10 installation completed. [ok]</p></td>
<td><p>[파일 위치]</p>
<p>lucida-for-docker/installer/lucida-install.sh</p>
<p>[실행 절차]</p>
<p>1. 사전 설치 완료여부 추가 확인</p>
<p>2. 기존 도커 이미지 삭제</p>
<p>3. 신규 도커 이미지 로딩</p>
<p>4. 환경변수(.env) 셋팅</p>
<p>5. SSL 인증서 생성 및 적용</p></td>
</tr>
</tbody>
</table>

절차별 상세 내용

<table>
<thead>
<tr class="header">
<th>절차</th>
<th>진행항목</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td>사전 설치 완료 상태 확인</td>
<td><p>[1/5] Checking pre-installation...</p>
<p>[fail] 항목이 없을 경우 다음 절차로 계속 진행합니다.</p>
<p>[fail] 항목이 있을 경우 해당항목 표시후 중지됩니다.</p>
<p>[-] pre-installation checking... [fail]</p>
<p>[-] java [fail]</p></td>
</tr>
<tr class="even">
<td>2</td>
<td>기존 도커 이미지 삭제</td>
<td><p>[2/5] Removing all existing docker images..</p>
<p>초기설치시에는 해당되지 않으며, 패치나 재설치시 해당됩니다.</p>
<p>기동중인 컨테이너가 있을 경우 이미지 업데이트가 안되므로 컨테이너 모두 중지된 상태에서 실행해야 합니다.</p>
<p>기동중인 컨테이너가 있을 경우 아래와 같이 출력후 중지합니다.</p>
<p>Please remove all running containers before installation.</p>
<p>Use 'docker rm $(docker ps -q)' to remove all containers.</p>
<p>[-] There are currently 2 containers running. [fail]</p>
<p>기동중인 컨테이너가 없을 경우 도커 이미지 삭제를 사용자에게 입력받은후 진행합니다. (y : 삭제, n : 중지)</p>
<p>To update docker images, all images must be removed.</p>
<p>[+] Remove all docker images? (Y/n) y</p>
<p>[100% 56/56] tchiotludo/akhq:0.24.0 is deleted.</p></td>
</tr>
<tr class="odd">
<td>3</td>
<td>신규 도커 이미지 로딩</td>
<td><p>[3/5] Loading docker images...</p>
<p>초기설치 이후 기존에 로딩된 이미지가 있을 경우 이미지 업데이트를 위해서 아래와 같이 삭제를 하고 진행합니다.</p>
<p>Do you wish to proceed with deleting all docker images? (Y/n)</p>
<p>- y : 모두 삭제후 진행</p>
<p>- n : 설치 중단</p>
<p>[출력 예시]</p>
<p>[84% 51/57] elasticsearch_7.17.14.tar is loading.</p>
<p>도커 이미지를 로컬 리포지토리에 모두 로딩이 되어야 서버스별 컨테이너를 실행할 수 있습니다.</p>
<p>./images 폴더에 있는 이미지 파일들을 로컬 리포지토리에 모두 로딩합니다.</p>
<p>[참고]</p>
<p>컨테이너가 자신의 이미지를 찾는 순서는 로컬 리포지토리에서 먼저 검색하고 없을 경우 원격 리포지토리를 찾습니다.</p>
<p>온라인 상태에서는 원격 리포지토리에서 직접 연결해서 이미지를 받아 올수 있지만 오프라인 환경에서는 해당서버 로컬 레포지토리만 접근이 가능하기 때문에 로컬 리포지토리에 이미지를 로딩해야 합니다.</p>
<p>이미지 로딩이 된 목록은 아래와 같이 확인할 수 있습니다.</p>
<p># docker images</p>
<table>
<thead>
<tr class="header">
<th>REPOSITORY</th>
<th>TAG</th>
<th>IMAGE ID</th>
<th>CREATED</th>
<th>SIZE</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>polestar.io/sms</td>
<td>10.1.0</td>
<td>1a157798fea6</td>
<td>2 weeks ago</td>
<td>266MB</td>
</tr>
<tr class="even">
<td>polestar.io/mfa-sms</td>
<td>10.1.0</td>
<td>613b685b8bc8</td>
<td>2 weeks ago</td>
<td>63.4MB</td>
</tr>
<tr class="odd">
<td>confluentinc/cp-kafka</td>
<td>7.6.1</td>
<td>5b4c63590c11</td>
<td>2 months ago</td>
<td>802MB</td>
</tr>
<tr class="even">
<td>mongo</td>
<td>7.0.9</td>
<td>ff65a94ec485</td>
<td>5 weeks ago</td>
<td>795MB</td>
</tr>
<tr class="odd">
<td>--- 중략 ---</td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
</tbody>
</table>
<p>REPOSITORY는 &lt;registry-url&gt;/&lt;namespace&gt;/&lt;repository&gt; 형식으로 표시되며, Polestar &lt;registry-url&gt;은 polestar.io를 사용하고 &lt;namespace&gt;는 사용하지 않습니다.</p>
<p>외부 라이브러리(kafka, mongo, redis 등)는 원본 REPOSITORY를 그대로 표시합니다.</p>
<p>&lt;registry-url&gt;이 없을 경우 기본적으로 docker.io 입니다.</p>
<p>TAG는 Polestar 10 버전을 명시하고 외부 라이브러리는 원본 버전을 그대로 표시합니다.</p></td>
</tr>
<tr class="even">
<td>4</td>
<td>환경변수(.env) 셋팅</td>
<td><p>현재 서버 IP목록 출력후 사용자가 선택하도록 제공합니다.</p>
<p>&lt;출력예시&gt;</p>
<p>[4/5] Configuring the .env file...</p>
<p>This server ip addresses:</p>
<p>1 : 192.168.200.97</p>
<p>2 : 172.26.0.1</p>
<p>3 : 172.17.0.1</p>
<p>4 : 172.18.0.1</p>
<p>5 : input manually</p>
<p>[+] Select the service IP: 1</p>
<p>[+] Is this a cluster mode(swarm mode)? (Y/n)</p>
<p>[4-1] N/n 입력시</p>
<p>[+] Is this a cluster mode(swarm mode)? (Y/n) n</p>
<p>선택된 IP로 Polestar 10이 기동됩니다. (예시 : https:// 192.168.200.97)</p>
<p>[4-2] Y/y 입력시</p>
<p>클러스터 구성일 경우 추가로 클러스터 구성 노드 IP를 입력해야 합니다.</p>
<p>위에서 선택한 현재 서버 IP를 포함하여 같이 입력하고, 예시처럼 콤마로 구분하여 입력해야 합니다.</p>
<p>IP는 최소 2개이상으로 입력되어야 하며, 기본 3개 클러스터 IP 입력이 필요합니다.</p>
<p>[+] Is this a cluster mode(swarm mode)? (Y/n) y</p>
<p>Enter the IPs of all nodes in the cluster.</p>
<p>ex (if 3 nodes) : 192.168.100.1,192.168.100.2,192.168.100.3</p>
<p>Cluster IPs (comma-separated) : 192.168.100.136,192.168.100.137,192.168.100.138</p>
<p>입력된 클러스터 IP 모두 접속이 가능합니다. (예시 : https:// 192.168.100.137)</p>
<p>입력된 IP는 Polestar 10 환경파일(.env)의 아래 항목을 변경합니다.</p>
<p>&lt;lucida-for-docker/polestar/bin/.env 파일&gt;</p>
<p>--- 중략 ---</p>
<p>APPLICATION_DOMAIN=192.168.213.172</p>
<p>ACCESS_DOMAIN_RULES="(Host(`192.168.213.172`))”</p>
<p>클러스터 모드일 경우는 아래 4가지 항목을 업데이트함</p>
<p>1) ACCESS_DOMAIN_RULES="(Host(`192.168.213.172`) || Host(`192.168.213.173`) || Host(`192.168.213.174`))"</p>
<p>2) ZOOKEEPER_HOST=${HOSTNAME_PREFIX}zookeeper-1:2181,${HOSTNAME_PREFIX}zookeeper-2:2181,${HOSTNAME_PREFIX}zookeeper-3:2181</p>
<p>3) KAFKA_CLUSTER_BOOTSTRAP=${HOSTNAME_PREFIX}kafka-1:9092,${HOSTNAME_PREFIX}kafka-2:9092,${HOSTNAME_PREFIX}kafka-3:9092</p>
<p>4) MONGODB_URI=mongodb://${HOSTNAME_PREFIX}mongodb-1:27017,${HOSTNAME_PREFIX}mongodb-2:27017,${HOSTNAME_PREFIX}mongodb-3:27017/?w=1&amp;replicaSet=lucida</p>
<p>5) MQTT_URI=tcp://${HOSTNAME_PREFIX}emqx-1:1883,tcp://${HOSTNAME_PREFIX}emqx-2:1883,tcp://${HOSTNAME_PREFIX}emqx-3:1883</p>
<p>--- 중략 ---</p></td>
</tr>
<tr class="odd">
<td>5</td>
<td>SSL 인증서 생성 및 적용</td>
<td><p>[5/5] Signing SSL certificate...</p>
<p>사전설치한 keytool, openssl 패키지를 사용하여 ssl 인증서 생성 및 등록하는 절차를 자동으로 실행합니다.</p>
<p>lucida-for-docker/polestar/self-signed-certificate/ssl_run.sh 가 내부적으로 실행됩니다.</p>
<p>IP는 4번에서 입력된 IP들이 모두 인증서에 적용됩니다.</p>
<p>클러스터 모드일 경우 입력한 노드 IP에 대해서 모두 인증서에 포함됩니다.</p></td>
</tr>
</tbody>
</table>


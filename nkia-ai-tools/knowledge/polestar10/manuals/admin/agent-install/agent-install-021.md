---
menu_path: "사전설치"
feature: "사전 설치"
admin_required: true
original_title: "사전설치"
category: agent-install
menu_path_verified: false
---
사전 설치

Polestar 10 설치전에 사전에 필요한 항목들 설치 가이드입니다.

사전 설치 환경조사에서 확인된 설치항목을 아래 가이드에 따라 설치 진행합니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-021/media/image3.png" style="width:0.21667in;height:0.21667in" />주의</p>
<p>사전 설치가 완료되고 나면 사전 설치 환경조사에서 자동점검스크립트를 재실행하여 최종적으로 다시 확인을 해 주시기 바랍니다. (# ./pre-install-check.sh)</p></td>
</tr>
</tbody>
</table>

사전설치 스크립트를 실행하고 필요한 항목을 선택하여 자동으로 설치를 진행합니다.

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./pre-install.sh</p>
<p>----------------------------------------------</p>
<p>1 : Install docker</p>
<p>2 : Install java</p>
<p>3 : Install utility</p>
<p>4 : Set os parameter</p>
<p>5 : Change docker root directory</p>
<p>6 : Exit</p>
<p>----------------------------------------------</p>
<p>Select an option (1-6): ■</p></td>
<td><p>[파일 위치]</p>
<p>pre-installer/pre-install.sh</p>
<p>[항목 설명]</p>
<p>1. 도커 및 도커컴포즈 설치</p>
<p>- 아래 [fail] 항목의 경우 설치 진행</p>
<p>[-] docker [fail]</p>
<p>[-] docker compose [fail]</p>
<p>2. 자바 설치(keytool 포함)</p>
<p>- 아래 [fail] 항목의 경우 설치 진행</p>
<p>[-] java [fail]</p>
<p>3. 유틸리티 설치(pv 등)</p>
<p>- 아래 [recmomended]시 선택후 설치 진행</p>
<p>[-] utility [recommended]</p>
<p>4. OS 파라미터 설정</p>
<p>- 아래 [fail] 항목의 경우 설치 진행</p>
<p>[-] os parameter [fail]</p>
<p>5. 도커 루트 디렉토리 변경</p>
<p>- 기본 디렉토리 : /var/lib/docker</p>
<p>- 데이터는 도커 루트디렉토리에 저장되므로 용량이 부족할 경우 또는 데이터 디스크를 추가할 경우 디렉토리 변경이 필요할 때 진행</p>
<p>- 예&gt; /data/lib/docker</p>
<p>6. 종료</p></td>
</tr>
</tbody>
</table>

도커 설치

도커와 도커컴포즈 최신버전을 자동으로 설치합니다.

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./pre-install.sh</p>
<p>----------------------------------------------</p>
<p>1 : Install docker</p>
<p>2 : Install java</p>
<p>3 : Install utility</p>
<p>4 : Set os parameter</p>
<p>5 : Change docker root directory</p>
<p>6 : Exit</p>
<p>----------------------------------------------</p>
<p>Select an option (1-6): 1</p>
<p>[+] Starting Docker installation...</p>
<p>Copying Docker binaries to /usr/bin...</p>
<p>Copying docker-compose to /usr/local/lib/docker/cli-plugins...</p>
<p>Enabling docker to start on boot...</p>
<p>Starting docker service via systemd...</p>
<p>Checking docker service status...</p>
<p>….</p>
<p>[+] Docker installation completed successfully. [ok]</p>
<p>[참고 : 도커 설치버전이 존재할 경우]</p>
<p>기존 설치 버전 삭제여부 확인(삭제후 진행 필요)</p>
<p>- y : 이전 설치버전 삭제</p>
<p>- n : 설치 중단</p>
<p>Docker is already installed. (version: 23.0.0)</p>
<p>Do you want to uninstall the current version and install the latest version 26.0.0 ? (Y/n) : y</p>
<p>[+] Starting Docker uninstallation...</p>
<p>Stopping Docker daemon...</p>
<p>Removing Docker binaries and docker-compose...</p>
<p>[+] Docker removal complete.</p>
<p>[+] Docker uninstallation completed successfully. [ok]</p></td>
<td><p>[실행 절차]</p>
<p>1. 도커설치가 되어 있을 경우 기존 설치 버전 삭제 여부 확인</p>
<p>- n : 기존 도커버전 유지(설치중지)</p>
<p>- y : 현재 설치버전 삭제</p>
<p>2. 도커 바이너리 파일로 설치 진행</p>
<p>- 위치 : ./docker/binaries</p>
<p>4. 도커 기동 및 재기동시 자동기동 설장</p>
<p>- docker.service 복사(etc/system/system)</p>
<p>- systemctl daemon-reload</p>
<p>- systemctl enable docker</p>
<p>- systemctl start docker</p>
<p>5. 설치 정상 종료시 아래 메시지 출력됨</p>
<p>[+] Docker installation completed successfully. [ok]</p>
<p>[참고]</p>
<p>1. 도커 상태확인</p>
<p># systemctl status docker</p>
<p>2. 도커 기동</p>
<p># systemctl start docker</p>
<p>2. 도커 중지</p>
<p># systemctl stop docker</p></td>
</tr>
</tbody>
</table>

자바 설치(keytool 포함)

Polestar 10 접속을 위한 SSL인증서를 생성하기 위해서 keytool 패키지가 필요합니다.

keytool 패키지를 설치하는 과정이며, 자바 JDK 패키지(JRE 버전에는 미포함)에 포함되어 있어서 자바를 설치합니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-021/media/image4.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>여기서 설치되는 자바는 SSL인증서 생성시에만 사용되고 Polestar 10 운영시 사용되지 않으며, Polestar 10 운영시 사용되는 자바는 각 서비스 컨테이너(MSA)안에 자바 17 JRE 버전이 설치되어 있습니다.</p></td>
</tr>
</tbody>
</table>

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./pre-install.sh</p>
<p>----------------------------------------------</p>
<p>1 : Install docker</p>
<p>2 : Install java</p>
<p>3 : Install utility</p>
<p>4 : Set os parameter</p>
<p>5 : Change docker root directory</p>
<p>6 : Exit</p>
<p>----------------------------------------------</p>
<p>Select an option (1-6): 2</p>
<p>[+] Starting Java installation...</p>
<p>[+] Installing JDK from ./java/openjdk-17.0.2_linux-x64_bin.tar.gz...</p>
<p>Creating installation directory at /usr/local/java...</p>
<p>--- 중략 ---</p>
<p>OpenJDK Runtime Environment (build 17.0.2-86)</p>
<p>OpenJDK 64-Bit Server VM (build 17.0.2+8-86, mixed mode, sharing)</p>
<p>[+] Java installation completed successfully. [ok]</p>
<p>[+] run the command [# source /etc/profile.d/jdk.sh]</p>
<p># source /etc/profile.d/jdk.sh</p>
<p># keytool</p>
<p>Key and Certificate Management Tool</p></td>
<td><p>[실행 절차]</p>
<p>1. /usr/local/java 디렉토리에서 자바 설치(openjdk-17.0.2 설치)</p>
<p>2. 설치 정상종료시 아래 메시지 출력됨</p>
<p>[+] Java installation completed successfully. [ok]</p>
<p>[+] run the command [# source /etc/profile.d/jdk.sh]</p>
<p>3. 자동설치스크립트 종료후 반드시 아래 실행해야 현재 쉘에서 확인가능(jdk path 추가)</p>
<p># source /etc/profile.d/jdk.sh</p>
<p>4. 최종적으로 keytool 실행시 정상적으로 인식되는지 확인 필요</p>
<p># keytool</p>
<p>Key and Certificate Management Tool</p></td>
</tr>
</tbody>
</table>

유틸리티 설치

Polestar 10 운영시 유용한 유틸리티를 설치합니다.

필수 선택은 아니지만 설치를 권장하며, 현재는 PV만 설치하고 추후 계속 추가될 예정입니다.

PV(PipeViewer)는 몽고디비 백업 및 복원 등 시간이 오래 걸리는 작업에서 진행상태를 표시해 주는 툴입니다.

참고 : PV가 설치되어 있지 않을 경우 몽고디비 백업 및 복원시 진행상태만 표시하지 않고 작업은 진행됩니다.

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./pre-install.sh</p>
<p>----------------------------------------------</p>
<p>1 : Install docker</p>
<p>2 : Install java</p>
<p>3 : Install utility</p>
<p>4 : Set os parameter</p>
<p>5 : Change docker root directory</p>
<p>6 : Exit</p>
<p>----------------------------------------------</p>
<p>Select an option (1-6): 3</p>
<p>[+] Starting utility installation...</p>
<p>Current OS: rocky</p>
<p>Version ID: 9.3</p>
<p>Major Version: 9</p>
<p>[+] Installing all RPM packages in ./utility/linux/centos</p>
<p>-- 중략 ---</p>
<p>All RPM packages installed successfully.</p>
<p>[+] Utility installation completed successfully. [ok]</p></td>
<td><p>[실행 절차]</p>
<p>1. 리눅스 정보 수집</p>
<p>- O/S, 버전 검사</p>
<p>2. 해당 O/S에 맞는 PV리눅스 패키지(yum, apt)로 설치함</p>
<p>- ./utility/packages/linux</p>
<p>3. 설치 정상 종료시 아래 메시지 출력됨</p>
<p>[+] Utility installation completed successfully. [ok]</p></td>
</tr>
</tbody>
</table>

O/S파라미터 설정

Polestar 10 운영시 몽고디비에서 권장하는 설정이며, /etc/sysctl.conf 파일에서 설정합니다.

vm.swappiness=1 : 몽고디비에서 스왑사용을 권장하지 않지만 OOM(Out of Memory)을 피하고 최소한으로 사용하기 위해서 \[swappiness = 1\]로 설정합니다.

vm.max\_map\_count = 262144 : 단일 프로세스가 가질 수 있는 메모리 매핑의 최대 수를 지정합니다. 이 매핑은 메모리 매핑 파일, 메모리 매핑 장치, 익명 메모리 매핑 등을 포함합니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-021/media/image4.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>O/S 설정값은 실제로 컨테이너에 모두 적용이 되어야 합니다.</p>
<p>1. 아래 설정값은 도커가 기동되는 O/S에 설정하면 기동되는 컨테이너는 동일한 설정으로 적용됩니다.</p>
<p>설치 스크립트로 실행시(Set os parameter) 자동으로 적용합니다.</p>
<p>[/etc/sysctl.conf]</p>
<p>vm.swappiness=1</p>
<p>vm.max_map_count = 262144</p>
<p>2. 아래 설정값은 컨테이너 내부에 직접 설정을 해야 합니다.</p>
<p>각 서비스의 docker-compose.yml 파일에서 설정합니다.</p>
<p>참고 : 현재 몽고디비만 적용되어 있는데 모든 서비스에 적용이 필요합니다.</p>
<p>일괄 적용을 위해서 도커설정파일(/etc/docker/daemon.json)에 설정하는 방법도 있습니다.</p>
<p>[/etc/security/limits.conf]</p>
<p>ulimit hard nofile = 65536</p>
<p>ulimit soft nofile = 65536</p>
<p>ulimit hard nproc = 65536</p>
<p>ulimit soft nproc = 65536</p>
<p>ulimit soft memlock = unlimited</p>
<p>ulimit hard memlock = unlimited</p></td>
</tr>
</tbody>
</table>

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./pre-install.sh</p>
<p>----------------------------------------------</p>
<p>1 : Install docker</p>
<p>2 : Install java</p>
<p>3 : Install utility</p>
<p>4 : Set os parameter</p>
<p>5 : Change docker root directory</p>
<p>6 : Exit</p>
<p>----------------------------------------------</p>
<p>Select an option (1-6): 4</p>
<p>[+] Updating os parameter setting...</p>
<p>[+] Swappiness added with value 1.</p>
<p>vm.max_map_count = 262144</p>
<p>[+] vm.max_map_count set to 262144.</p>
<p>vm.max_map_count = 262144</p>
<p>[+] vm.max_map_count added with value 262144.</p>
<p>[+] Sysctl settings applied successfully.</p>
<p>[+] OS parameter settings successfully. [ok]</p></td>
<td><p>[실행 절차]</p>
<p>1. /etc/sysctl.conf 에서 swappiness, vm.max_map_count 값 권장값 설정 여부 확인</p>
<p>2. 기존에 설정값이 없을 경우 아래 추가하고 있을 경우 업데이트</p>
<p>vm.swappiness=1</p>
<p>vm.max_map_count = 262144</p>
<p>3. 시스템 적용</p>
<p># sysctl -p</p>
<p>[설정 확인]</p>
<p># cat /etc/sysctl.conf</p></td>
</tr>
</tbody>
</table>

도커 루트디렉토리 변경

일반적으로 O/S 디스크와 데이터 디스크를 분리하고 고객사별로 적절한 용량산정에 따라 데이터 디스크를 추가합니다.

Polestar 10 저장되는 데이터 저장 디스크를 변경하기 위한 과정입니다.

몽고디비 컨테이너를 포함한 모든 컨테이너 데이터는 도커 루트 디렉토리에 저장됩니다.

실제 저장되는 디렉토리는 다음과 같습니다.

\- 도커 루트 디렉토리(Default) : /var/lib/docker

\- 도커 저장 볼륨(Default) : /var/lib/docker/volumes

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-021/media/image3.png" style="width:0.21667in;height:0.21667in" />주의</p>
<p>운영중에 도커 루트 디렉토리를 변경하면 기존에 모든 데이터는 삭제되므로 초기에 셋팅해야 합니다.</p>
<p>운영중에 도커 루트디렉토리를 변경할려면 모든 데이터(몽고디비, 설정 등)를 백업하고 복원과정을 진행해야 합니다. (Polestar 10 원복 가이드 참조)</p></td>
</tr>
</tbody>
</table>

<table>
<thead>
<tr class="header">
<th>스크립트 실행</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p># ./pre-install.sh</p>
<p>----------------------------------------------</p>
<p>1 : Install docker</p>
<p>2 : Install java</p>
<p>3 : Install utility</p>
<p>4 : Set os parameter</p>
<p>5 : Change docker root directory</p>
<p>6 : Exit</p>
<p>----------------------------------------------</p>
<p>Select an option (1-6): 5</p>
<p>[+] Changing docker root directory...</p>
<p>Current Docker root directory : /var/lib/docker</p>
<p>WARNING: Changing the Docker root directory will delete all existing Docker data, including volumes and images!</p>
<p>Do you want to change the Docker root directory? (Y/n): y</p>
<p>Enter the new Docker root directory: /data/lib/docker</p>
<p>/etc/docker/daemon.json:</p>
<p>{</p>
<p>"data-root": "/data/lib/docker"</p>
<p>}</p>
<p>Do you want to restart the Docker daemon to apply changes? (Y/n): y</p>
<p>Stopping Docker daemon...</p>
<p>Starting Docker daemon...</p>
<p>[+] Docker root directory changing successfully. [ok]</p></td>
<td><p>[실행 절차]</p>
<p>1. 현재 루트 디렉토리 출력</p>
<p>- 예&gt; 기본값 : /var/lib/docker</p>
<p>2. 루트 디렉토리 변경시 데이터 삭제된다는 경고 메시지 출력 및 변경 여부 사용자 입력</p>
<p>- y : 변경 작업 진행</p>
<p>- n : 설치 중단</p>
<p>3. /etc/docker/daemon.json 파일 존재여부 확인</p>
<p>- 없으면 파일 생성후 (“data-root”) 값 추가</p>
<p>- 존재할 경우 해당 옵션 값만 추가</p>
<p>4. 변경할 디렉토리 사용자 입력</p>
<p>용량이 충분한 데이터 디스크 선택 필요</p>
<p>- 예&gt; /data/lib/docker</p>
<p>5. 설정값 출력</p>
<p># cat /etc/docker/daemon.json</p>
<p>{</p>
<p>"data-root": "/data/lib/docker"</p>
<p>}</p>
<p>6. 도커 재기동후 적용되므로 재기동 여부 사용자 확인후 진행</p>
<p>- 도커 중지 : # pkill dockerd</p>
<p>- 도커 실행 : # /usr/bin/dockerd &amp;</p>
<p>7. 변경 정상 종료시 아래 메시지 출력</p>
<p>[+] Docker root directory changing successfully. [ok]</p></td>
</tr>
</tbody>
</table>


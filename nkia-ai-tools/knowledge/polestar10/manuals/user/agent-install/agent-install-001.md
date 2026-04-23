---
menu_path: "WPMAgent사전설치환경조사"
feature: "사전 설치 환경 조사"
admin_required: false
original_title: "WPMAgent사전설치환경조사"
category: agent-install
menu_path_verified: false
---
사전 설치 환경 조사

WPM Agent 설치 전 사전에 필요한 환경정보 입니다.

WPM 지원버전에 따라 Agent 설치가능여부를 확인하시면 됩니다.

에이전트 지원 JVM/OS, WAS, Library 버전

WPM 에이전트 지원 버전

| JVM Versions  | OS                                         |
| ------------- | ------------------------------------------ |
| JDK6 \~ JDK20 | Linux, Unix 계열 OS, Windows, Windows Server |

WPM 지원 애플리케이션 서버 정보

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-001/media/image3.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>WPM 에이전트는 Java 언어로 개발된 애플리케이션은 성능 모니터링이 가능합니다. 아래의 애플리케이션 서버에 대해서는 WAS 버전과 같은 특정 WAS에 국한된 구성정보도 수집할 수 있는 버전입니다. 따라서 아래 목록에 없더라도 성능 모니터링을 원한다면 해당 애플리케이션의 JDK 버전만 확인하시면 됩니다.</p></td>
</tr>
</tbody>
</table>

<table>
<thead>
<tr class="header">
<th>애플리케이션 서버</th>
<th>Versions</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Jeus</td>
<td>7.x, 8.x</td>
</tr>
<tr class="even">
<td><a href="https://www.payara.fish/">Jboss</a></td>
<td><p>6.x, 7.x</p>
<p>EAP 6.x, EAP 7.x<br />
Wildfly</p></td>
</tr>
<tr class="odd">
<td><a href="http://tomcat.apache.org/">Tomcat</a></td>
<td>7.0.x, 8.5.x, 9.0.x, 10.0.x</td>
</tr>
</tbody>
</table>

사전 설치 정보 목록

WPM Agent를 설치할 애플리케이션 대상에 대한 필요 정보를 사전에 준비합니다.

다음의 표시는 사전 설치 시 필요한 정보의 예시입니다.

<table>
<thead>
<tr class="header">
<th>정보</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>IP 주소</td>
<td>애플리케이션 수행되고 있는 서버의 IP 주소</td>
</tr>
<tr class="even">
<td>모니터링 대상 정보</td>
<td><p>모니터링 대상의 정보.</p>
<p>필수 정보는 JDK버전입니다.</p>
<p>예) JDK 버전, Tomcat 8, JEUS 7, SpringBoot</p></td>
</tr>
<tr class="odd">
<td>모니터링 대상 기동 스크립트 또는 기동 방법</td>
<td><p>WPM 옵션을 설정한 후 Java 애플리케이션을 재기동하기 위해 모니터링 대상 기동 스크립트 파일명 또는 기동 방법을 명시합니다.</p>
<p>예) /was/tomcat8/startup.sh</p></td>
</tr>
<tr class="even">
<td>모니터링 대상 중지 스크립트 또는 중지 방법</td>
<td><p>WPM 옵션을 설정하기위해 Java 애플리케이션을 중지하기 위해 모니터링 대상 중지 스크립트 파일명 또는 중지 방법을 명시합니다.</p>
<p>예) /was/tomcat8/stop.sh</p></td>
</tr>
<tr class="odd">
<td>모니터링 대상 Java 옵션 설정 파일</td>
<td><p>Java 애플리케이션에 WPM을 설치하기 위해서는 Java 옵션에 WPM 옵션을 추가하여야 합니다. 애플리케이션에 Java 옵션을 설정하는 스크립트 또는 설정 파일명을 명시합니다.</p>
<p>예) /was/tomcat8/setenv.sh</p></td>
</tr>
<tr class="even">
<td>접속정보</td>
<td><p>애플리케이션에 JAVA 옵션 설정,에이전트 파일 설치 등을 위해 root계정 및 애플리케이션 기동 계정에 대한 접속 정보가 필요합니다.</p>
<p>예) root/passwd, oper/passwd1</p></td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-001/media/image3.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>시스템에 telnet/ftp 기본 접속 방식을 지원하지 않는 경우 또는 SSH나 접근 제어가 설치되어 있는 경우에는 별도 접근 방법을 통하여 설치해야 합니다.</p></td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-001/media/image3.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>가장 많이 사용되고 있는 WAS의 일반적인 자바옵션 설정 파일은 아래의 표를 참고합니다. 설치 환경에 따라 기동 스크립트는 아래의 일반적인 자바옵션 설정파일이 아닐 수 있습니다. 해당 프로젝트의 Java 애플리케이션 담당자에게 문의하여 확인하는 것이 가장 정확합니다.</p>
<p>Java 애플리케이션 관리자의 관리 패턴에 따라 다양한 형태의 자바 옵션 설정 파일이 존재할 수 있습니다. 사전 작업 조사서를 통해 자바 옵션 설정 파일 경로를 미리 조사해 두면 설치 시간을 줄일 수 있습니다.</p>
<table>
<thead>
<tr class="header">
<th>WAS 종류</th>
<th>자바옵션 설정 파일</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Tomcat</td>
<td>$TomcatHome$/bin/catalina.sh</td>
</tr>
<tr class="even">
<td>JBoss</td>
<td><p>AS 4,5,6 버전: $JbossHome$/bin/run.sh 또는</p>
<p>$JbossHome$/server/서버명/run.conf</p>
<p>AS 7 버전: $JbossHome$/bin/standalone.sh 또는</p>
<p>$JbossHome$/bin/standalone.conf</p></td>
</tr>
<tr class="odd">
<td>Weblogic</td>
<td><p>도메인의 start script</p>
<p>도메인 이름의 디렉토리내에 존재</p>
<p>예) /bea/basedomain/startManaged.sh 등</p>
<p>startManaged.sh를 도메인명으로 변경한 스크립트</p></td>
</tr>
<tr class="even">
<td>JEUS</td>
<td><p>5,6 버전: $JEUS_HOME/config/호스트명/JEUSMain.xml</p>
<p>7,8 버전: $JEUS_HOME/domains/도메인명/config/domain.xml</p>
<p>또는 admin 콘솔(http://호스트ip:9736/webadmin)</p>
<p>* 콘솔 포트는 환경에 따라 다를 수 있습니다.</p>
<p>* admin 콘솔 로그인 정보 필요</p></td>
</tr>
<tr class="odd">
<td>WebSphere</td>
<td><p>admin 콘솔 사용(http://호스트ip:9090/admin)</p>
<p>* 콘솔 포트는 환경에 따라 다를 수 있습니다.</p>
<p>* admin 콘솔 로그인 정보 필요</p></td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

설치 전 권한 및 방화벽 확인

권한 확인

WPM Java Agent 설치는 Java 애플리케이션 기동 계정이 접근할 수 있는 권한이 있는 디렉토리라면 어느 디렉토리든 가능합니다. 시스템 관리자에게 문의하여 WPM 에이전트 설치 디렉토리 경로를 확인합니다.

방화벽 확인

WPM Java Agent는 WPM 수집서버와 통신하기 위해 다음의 포트 정보가 기본적으로 사용되며, 설치 환경에 따라 포트 번호가 변경될 수 있습니다. 확인된 포트가 사용될 수 있도록 방화벽 설정을 확인합니다.

<table>
<thead>
<tr class="header">
<th>프로토콜</th>
<th>포트 번호</th>
<th>사용 용도</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>TCP</td>
<td><strong>31005</strong></td>
<td>사용자가 화면의 기능을 통해 에이전트에게 특정 액션을 요청할 때 사용<br />
예 : 쓰레드 목록, 쓰레드 덤프 명령</td>
</tr>
<tr class="even">
<td>UDP</td>
<td>31002</td>
<td>성능정보, 트레이스 정보 등 주요 성능 관련 데이터 수집 포트</td>
</tr>
</tbody>
</table>


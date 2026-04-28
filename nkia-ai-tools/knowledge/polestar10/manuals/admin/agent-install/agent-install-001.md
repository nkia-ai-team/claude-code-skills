---
menu_path: "APMJavaAgent사전설치환경조사"
feature: "사전 설치 환경 조사"
admin_required: true
original_title: "APMJavaAgent사전설치환경조사"
category: agent-install
menu_path_verified: false
---
사전 설치 환경 조사

APM Agent 설치 전 사전에 필요한 환경정보 입니다.

APM Agent는 Opentelemetry 에이전트를 사용하여 설치합니다.

APM Java Agent 지원버전에 따라 Agent 설치가능여부를 확인하시면 됩니다.

에이전트 지원 JVM/OS, WAS, Library 버전

Opentelemetry 공식 테스트 완료 JVM, OS 버전

| JVM                          | JVM Versions | OS 버전                          |
| ---------------------------- | ------------ | ------------------------------ |
| OpenJDK (Eclipse Temurin)    | 8, 11, 17    | Ubuntu 18, Windows Server 2019 |
| OpenJ9 (IBM Semeru Runtimes) | 8, 11, 17    | Ubuntu 18, Windows Server 2019 |

Opentelemetry 공식 테스트 완료 애플리케이션 서버 정보

| 애플리케이션 서버                                                                       | Versions                    | JVM               |
| ------------------------------------------------------------------------------- | --------------------------- | ----------------- |
| Jetty                                                                           | 9.4.x, 10.0.x, 11.0.x       | OpenJDK 8, 11, 17 |
| [Payara](https://www.payara.fish/)                                              | 5.0.x, 5.1.x                | OpenJDK 8, 11     |
| [Tomcat](http://tomcat.apache.org/)                                             | 7.0.x, 8.5.x, 9.0.x, 10.0.x | OpenJDK 8, 11, 17 |
| [TomEE](https://tomee.apache.org/)                                              | 7.x, 8.x                    | OpenJDK 8, 11, 17 |
| [Websphere Liberty Profile](https://www.ibm.com/cloud/websphere-liberty)        | 20.x, 21.x                  | OpenJDK 8         |
| [Websphere Traditional](https://www.ibm.com/cloud/websphere-application-server) | 8.5.5.x, 9.0.x              | IBM JDK 8         |
| [WildFly](https://www.wildfly.org/)                                             | 13.x                        | OpenJDK 8         |
| [WildFly](https://www.wildfly.org/)                                             | 17.x, 21.x, 25.x            | OpenJDK 8, 11, 17 |

사전 설치 정보 목록

APM Agent를 설치할 애플리케이션 대상에 대한 필요 정보를 사전에 준비합니다.

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
<td><p>모니터링 대상의 정보</p>
<p>예) Tomcat 8, JEUS 7, SpringBoot</p></td>
</tr>
<tr class="odd">
<td>모니터링 대상 기동 스크립트 또는 기동 방법</td>
<td><p>APM 옵션을 설정한 후 Java 애플리케이션을 재기동하기 위해 모니터링 대상 기동 스크립트 파일명 또는 기동 방법을 명시합니다.</p>
<p>예) /was/tomcat8/startup.sh</p></td>
</tr>
<tr class="even">
<td>모니터링 대상 중지 스크립트 또는 중지 방법</td>
<td><p>APM 옵션을 설정하기위해 Java 애플리케이션을 중지하기 위해 모니터링 대상 중지 스크립트 파일명 또는 중지 방법을 명시합니다.</p>
<p>예) /was/tomcat8/stop.sh</p></td>
</tr>
<tr class="odd">
<td>모니터링 대상 Java 옵션 설정 파일</td>
<td><p>Java 애플리케이션에 APM을 설치하기 위해서는 Java 옵션에 APM 옵션을 추가하여야 합니다. 애플리케이션에 Java 옵션을 설정하는 스크립트 또는 설정 파일명을 명시합니다.</p>
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

APM Java Agent 설치는 Java 애플리케이션 기동 계정이 접근할 수 있는 권한이 있는 디렉토리라면 어느 디렉토리든 가능합니다. 시스템 관리자에게 문의하여 APM 에이전트 설치 디렉토리 경로를 확인합니다.

방화벽 확인

APM Java Agent는 APM 수집서버와 통신하기 위해 TCP 기본 포트인 6565 포트를 사용하며, 해당포트가 사용될 수 있도록 방화벽 설정을 확인합니다.


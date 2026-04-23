---
menu_path: "APMJavaAgent설치"
feature: "APM Java Agent 설치"
admin_required: true
original_title: "APMJavaAgent설치"
category: agent-install
menu_path_verified: false
---
APM Java Agent 설치

Java 애플리케이션 관제를 위해서는 APM Java Agent를 다운 받고 관제 대상인 Java 애플리케이션의 설정 파일에 옵션을 설정하여 설치합니다.

설치 전 사전 준비 사항 확인 및 준비하여 설치 절차로 수행하면 APM Java Agent를 설치 할 수 있습니다.

사전 준비 사항

APM java Agent를 설치 전에 미리 준비 할 내용을 확인하고 준비를 해야 합니다.

> 사전 준비 항목

| 전송주소  | APM Java Agent가 데이터 수신할 Polestar10에 전송할 URL 주소      |
| ----- | --------------------------------------------------- |
| 조직아이디 | APM Java Agent의 추가할 조직의 아이디                         |
| 접근권한  | APM Java Agent가 설치할 디렉토리에 대한 애플리케이션에서 읽기 권한이 있는지 확인 |

> 조직 아이디 확인 절차

1.  Polestar10 로그인 한다.

2.  \[계정\]\>조직명 마우스 호버 한다.

3.  툴팁에 표시되는 조직 아이디를 복사

![](./images/agent-install-003/media/image3.png)

APM Java Agent 설치

사전 준비 사항을 확인 하셨다면 아래의 절차대로 수행하여 APM java Agent를 설치 할 수 있습니다.

> 설치 디렉토리 생성 및 업로드

1.  APM Java Agent 설치 할 디렉토리 생성합니다.

2.  APM 에이전트 설차 파일을 생성한 디렉토리에 업로드합니다.

> Java Agent 구성 설정

1.  APM 에이전트 설정 파일(agentsetting.conf)의 아래 내용을 수정합니다.

2.  에이전트 설정 파일의 “Connect & Config” 옵션 부분을 찾아 otel.exporter.otlp.endpoint에 Polestar EMS 수집주소를 추가합니다.

3.  otel.service.name에 \<에이전트 이름\>을 설정합니다.

4.  otel.resource.attributes의 lucida.organizationId에는 \<조직ID\>를 설정하고 lucida.groupId에는 \<서비스명\>(애플리케이션 서비스 그룹명)을 설정합니다.

5.  “Defaut export”항목과 “Metric Setting”은 특별한 설치 가이드가 없을 경우 수정하지 않고 초기값을 사용합니다.

6.  “Enable manual instrumentation” 항목들은 애플리케이션이 사용하고 있는 프레임웍 또는 라이브러리에 따라 수집 설정을 변경할 수 있습니다.

7.  OTEL\_JAVAAGENT\_CONFIGURATION\_FILE 환경변수에 APM 에이전트 환경 설정파일(agentsetting.conf)파일의 절대경로를 입력합니다.

8.  javaagent 옵션에 APM 에이전트 파일의 절대 경로를 입력 합니다.

9.  생성한 디렉토리에 애플리케이션이 접근 할 수 있도록 읽기 권한 부여 합니다.

> APM 에이전트 수집 환경 설정 파일

APM 에이전트 수집 환경 설정파일은 OS와 상관없이 동일합니다.

<table>
<tbody>
<tr class="odd">
<td><p># Connect &amp; Config</p>
<p>otel.exporter.otlp.endpoint=&lt;Polestar EMSAP수집주소&gt;</p>
<p>otel.service.name=&lt;에이전트 이름&gt;</p>
<p>otel.resource.attributes=lucida.organizationId=&lt;조직아이디&gt;,lucida.groupId=&lt;서비스 이름&gt;</p>
<p># Default export</p>
<p>otel.exporter.otlp.protocol=grpc</p>
<p>otel.traces.exporter=otlp</p>
<p>otel.metrics.exporter=otlp</p>
<p>otel.logs.exporter=otlp</p>
<p># Metric Setting</p>
<p>otel.instrumentation.runtime.metrics.enabled=true</p>
<p>otel.metric.export.interval=10000</p>
<p># Enable manual instrumentation</p>
<p>otel.instrumentation.common.default-enabled=false</p>
<p>otel.instrumentation.methods.enabled=true</p>
<p>otel.instrumentation.external-annotations.enabled=true</p>
<p>otel.instrumentation.activej-http.enabled=true</p>
<p>otel.instrumentation.avaje-jex.enabled=true</p>
<p>otel.instrumentation.akka-actor.enabled=true</p>
<p>otel.instrumentation.akka-http.enabled=true</p>
<p>otel.instrumentation.alibaba-druid.enabled=true</p>
<p>otel.instrumentation.axis2.enabled=true</p>
<p>otel.instrumentation.camel.enabled=true</p>
<p>otel.instrumentation.cassandra.enabled=true</p>
<p>otel.instrumentation.cxf.enabled=true</p>
<p>otel.instrumentation.apache-dbcp.enabled=true</p>
<p>otel.instrumentation.apache-dubbo.enabled=true</p>
<p>otel.instrumentation.geode.enabled=true</p>
<p>otel.instrumentation.apache-httpasyncclient.enabled=true</p>
<p>otel.instrumentation.apache-httpclient.enabled=true</p>
<p>otel.instrumentation.kafka.enabled=true</p>
<p>otel.instrumentation.jsf-myfaces.enabled=true</p>
<p>otel.instrumentation.pekko-actor.enabled=true</p>
<p>otel.instrumentation.pekko-http.enabled=true</p>
<p>otel.instrumentation.pulsar.enabled=true</p>
<p>otel.instrumentation.rocketmq-client.enabled=true</p>
<p>otel.instrumentation.apache-shenyu.enabled=true</p>
<p>otel.instrumentation.struts.enabled=true</p>
<p>otel.instrumentation.tapestry.enabled=true</p>
<p>otel.instrumentation.tomcat.enabled=true</p>
<p>otel.instrumentation.wicket.enabled=true</p>
<p>otel.instrumentation.armeria.enabled=true</p>
<p>otel.instrumentation.async-http-client.enabled=true</p>
<p>otel.instrumentation.aws-lambda.enabled=true</p>
<p>otel.instrumentation.aws-sdk.enabled=true</p>
<p>otel.instrumentation.azure-core.enabled=true</p>
<p>otel.instrumentation.clickhouse.enabled=true</p>
<p>otel.instrumentation.couchbase.enabled=true</p>
<p>otel.instrumentation.c3p0.enabled=true</p>
<p>otel.instrumentation.dropwizard-views.enabled=true</p>
<p>otel.instrumentation.dropwizard-metrics.enabled=true</p>
<p>otel.instrumentation.grizzly.enabled=true</p>
<p>otel.instrumentation.jersey.enabled=true</p>
<p>otel.instrumentation.jetty.enabled=true</p>
<p>otel.instrumentation.jetty-httpclient.enabled=true</p>
<p>otel.instrumentation.metro.enabled=true</p>
<p>otel.instrumentation.jsf-mojarra.enabled=true</p>
<p>otel.instrumentation.vertx-http-client.enabled=true</p>
<p>otel.instrumentation.vertx-kafka-client.enabled=true</p>
<p>otel.instrumentation.vertx-redis-client.enabled=true</p>
<p>otel.instrumentation.vertx-rx-java.enabled=true</p>
<p>otel.instrumentation.vertx-sql-client.enabled=true</p>
<p>otel.instrumentation.vertx-web.enabled=true</p>
<p>otel.instrumentation.elasticsearch-api-client.enabled=true</p>
<p>otel.instrumentation.elasticsearch-transport.enabled=true</p>
<p>otel.instrumentation.elasticsearch-rest.enabled=true</p>
<p>otel.instrumentation.finagle-http.enabled=true</p>
<p>otel.instrumentation.guava.enabled=true</p>
<p>otel.instrumentation.google-http-client.enabled=true</p>
<p>otel.instrumentation.gwt.enabled=true</p>
<p>otel.instrumentation.grails.enabled=true</p>
<p>otel.instrumentation.graphql-java.enabled=true</p>
<p>otel.instrumentation.grpc.enabled=true</p>
<p>#otel.instrumentation.hibernate.enabled=true</p>
<p>#otel.instrumentation.hibernate-reactive.enabled=true</p>
<p>otel.instrumentation.hikaricp.enabled=true</p>
<p>otel.instrumentation.influxdb.enabled=true</p>
<p>otel.instrumentation.java-http-client.enabled=true</p>
<p>otel.instrumentation.java-http-server.enabled=true</p>
<p>otel.instrumentation.http-url-connection.enabled=true</p>
<p>otel.instrumentation.jdbc.enabled=true</p>
<p>otel.instrumentation.jdbc-datasource.enabled=true</p>
<p>otel.instrumentation.rmi.enabled=true</p>
<p>otel.instrumentation.runtime-telemetry.enabled=true</p>
<p>otel.instrumentation.servlet.enabled=true</p>
<p>otel.instrumentation.executors.enabled=true</p>
<p>otel.instrumentation.java-util-logging.enabled=true</p>
<p>otel.instrumentation.javalin.enabled=true</p>
<p>otel.instrumentation.jaxrs-client.enabled=true</p>
<p>otel.instrumentation.jaxrs.enabled=true</p>
<p>otel.instrumentation.jaxws.enabled=true</p>
<p>otel.instrumentation.jboss-logmanager-appender.enabled=true</p>
<p>otel.instrumentation.jboss-logmanager-mdc.enabled=true</p>
<p>otel.instrumentation.jms.enabled=true</p>
<p>otel.instrumentation.jodd-http.enabled=true</p>
<p>otel.instrumentation.jsp.enabled=true</p>
<p>otel.instrumentation.kubernetes-client.enabled=true</p>
<p>otel.instrumentation.ktor.enabled=true</p>
<p>otel.instrumentation.kotlinx-coroutines.enabled=true</p>
<p>otel.instrumentation.log4j-appender.enabled=true</p>
<p>otel.instrumentation.log4j-mdc.enabled=true</p>
<p>otel.instrumentation.log4j-context-data.enabled=true</p>
<p>otel.instrumentation.logback-appender.enabled=true</p>
<p>otel.instrumentation.logback-mdc.enabled=true</p>
<p>otel.instrumentation.micrometer.enabled=true</p>
<p>otel.instrumentation.mongo.enabled=true</p>
<p>otel.instrumentation.mybatis.enabled=true</p>
<p>otel.instrumentation.hystrix.enabled=true</p>
<p>otel.instrumentation.netty.enabled=true</p>
<p>otel.instrumentation.okhttp.enabled=true</p>
<p>otel.instrumentation.liberty.enabled=true</p>
<p>otel.instrumentation.openai.enabled=true</p>
<p>otel.instrumentation.opensearch-rest.enabled=true</p>
<p>otel.instrumentation.opentelemetry-extension-annotations.enabled=true</p>
<p>otel.instrumentation.opentelemetry-instrumentation-annotations.enabled=true</p>
<p>otel.instrumentation.opentelemetry-api.enabled=true</p>
<p>otel.instrumentation.oracle-ucp.enabled=true</p>
<p>otel.instrumentation.oshi.enabled=true</p>
<p>otel.instrumentation.payara.enabled=true</p>
<p>otel.instrumentation.play.enabled=true</p>
<p>otel.instrumentation.play-ws.enabled=true</p>
<p>otel.instrumentation.powerjob.enabled=true</p>
<p>otel.instrumentation.quarkus.enabled=true</p>
<p>otel.instrumentation.quartz.enabled=true</p>
<p>otel.instrumentation.r2dbc.enabled=true</p>
<p>otel.instrumentation.rabbitmq.enabled=true</p>
<p>otel.instrumentation.ratpack.enabled=true</p>
<p>otel.instrumentation.rxjava.enabled=true</p>
<p>otel.instrumentation.reactor.enabled=true</p>
<p>otel.instrumentation.reactor-kafka.enabled=true</p>
<p>otel.instrumentation.reactor-netty.enabled=true</p>
<p>otel.instrumentation.jedis.enabled=true</p>
<p>otel.instrumentation.lettuce.enabled=true</p>
<p>otel.instrumentation.rediscala.enabled=true</p>
<p>otel.instrumentation.redisson.enabled=true</p>
<p>otel.instrumentation.restlet.enabled=true</p>
<p>otel.instrumentation.scala-fork-join.enabled=true</p>
<p>otel.instrumentation.spark.enabled=true</p>
<p>otel.instrumentation.spring-batch.enabled=true</p>
<p>otel.instrumentation.spring-boot-actuator-autoconfigure.enabled=true</p>
<p>otel.instrumentation.spring-cloud-aws.enabled=true</p>
<p>otel.instrumentation.spring-cloud-gateway.enabled=true</p>
<p>otel.instrumentation.spring-core.enabled=true</p>
<p>otel.instrumentation.spring-data.enabled=true</p>
<p>otel.instrumentation.spring-jms.enabled=true</p>
<p>otel.instrumentation.spring-integration.enabled=true</p>
<p>otel.instrumentation.spring-kafka.enabled=true</p>
<p>otel.instrumentation.spring-pulsar.enabled=true</p>
<p>otel.instrumentation.spring-rabbit.enabled=true</p>
<p>otel.instrumentation.spring-rmi.enabled=true</p>
<p>otel.instrumentation.spring-scheduling.enabled=true</p>
<p>otel.instrumentation.spring-security-config.enabled=true</p>
<p>otel.instrumentation.spring-web.enabled=true</p>
<p>otel.instrumentation.spring-webflux.enabled=true</p>
<p>otel.instrumentation.spring-webmvc.enabled=true</p>
<p>otel.instrumentation.spring-ws.enabled=true</p>
<p>otel.instrumentation.spymemcached.enabled=true</p>
<p>otel.instrumentation.tomcat-jdbc.enabled=true</p>
<p>otel.instrumentation.twilio.enabled=true</p>
<p>otel.instrumentation.finatra.enabled=true</p>
<p>otel.instrumentation.undertow.enabled=true</p>
<p>otel.instrumentation.vaadin.enabled=true</p>
<p>otel.instrumentation.vibur-dbcp.enabled=true</p>
<p>otel.instrumentation.xxl-job.enabled=true</p>
<p>otel.instrumentation.zio.enabled=true</p></td>
</tr>
</tbody>
</table>

> Java Agent 실행 및 적용 확인

1.  Java 애플리케이션 재시작을 한다.

2.  애플리케이션 로그에 io.opentelemetry.javaagent.tooling.VersionLogger - opentelemetry-javaagent - version: 내용이 표시 된다.

ㄱ

OS별 Java Agent 구성 설정 템플릿

Java Agent 설치 시 OS별 구성 템플릿을 복사 후 환경에 맞게 변경하여 사용 할 수 있습니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-003/media/image4.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>APM 에이전트 수집 환경 설정파일에 대한 자세한 내용은 Java Agent수집 설정 항목을 참고 하세요.</p></td>
</tr>
</tbody>
</table>

> Linux 환경

<table>
<tbody>
<tr class="odd">
<td><p>export OTEL_JAVAAGENT_CONFIGURATION_FILE=&lt;에이전트 환경 설정 파일&gt;</p>
<p>JAVA_OPTS="$JAVA_OPTS$ -javaagent:&lt;에이전트 설치 파일&gt;"</p></td>
</tr>
</tbody>
</table>

> Window 환경

<table>
<tbody>
<tr class="odd">
<td><p>set OTEL_JAVAAGENT_CONFIGURATION_FILE=&lt;에이전트 환경 설정 파일&gt;</p>
<p>set JAVA_OPTS=%JAVA_OPTS% -javaagent:&lt;에이전트 설치 파일&gt;</p></td>
</tr>
</tbody>
</table>

설치 예 : Tomcat (on Linux)

1.  에이전트 수집 환경 설정 파일에 수집서버IP(Polestar EMS IP와 포트)와 APM 수집포트 조직ID, 에이전트 이름, 서비스 이름은 설치환경에 맞게 수정해주세요.

2.  파일명 : $(TOMCAT\_HOME)/bin/catalina.sh

> Tomcat디렉토리/bin의 catalina.sh 파일을 vi와 같은 편집기로 열어 옵션을 설정합니다.

3.  샘플 예시

<!-- end list -->

  - 에이전트 파일 위치 : /app/apmagent/

  - 조직ID : 675bf43e20dee972e1b6417b

  - 에이전트 이름 : tomat8\_test

  - 서비스 이름 : nkia\_groupware

<!-- end list -->

4.  환경 설정 파일 예시

<table>
<tbody>
<tr class="odd">
<td><p># Connect &amp; Config</p>
<p>otel.exporter.otlp.endpoint=http://192.168.10.123:6565</p>
<p>otel.service.name=tomat8_test</p>
<p>otel.resource.attributes=lucida.organizationId=675bf43e20dee972e1b6417b,lucida.groupId= nkia_groupware</p>
<p># Default export</p>
<p>otel.exporter.otlp.protocol=grpc</p>
<p>otel.traces.exporter=otlp</p>
<p>otel.metrics.exporter=otlp</p>
<p>otel.logs.exporter=otlp</p>
<p># Metric Setting</p>
<p>otel.instrumentation.runtime.metrics.enabled=true</p>
<p>otel.metric.export.interval=10000</p>
<p># Enable manual instrumentation</p>
<p>otel.instrumentation.common.default-enabled=false</p>
<p>otel.instrumentation.methods.enabled=true</p>
<p>otel.instrumentation.external-annotations.enabled=true</p>
<p>otel.instrumentation.activej-http.enabled=true</p>
<p>otel.instrumentation.avaje-jex.enabled=true</p>
<p>otel.instrumentation.akka-actor.enabled=true</p>
<p>otel.instrumentation.akka-http.enabled=true</p>
<p>… 중략 …</p></td>
</tr>
</tbody>
</table>

5.  Tomcat의 catalina.sh 파일 예시

<table>
<tbody>
<tr class="odd">
<td><p>#!/bin/sh</p>
<p># Licensed to the Apache Software Foundation (ASF) under one or more</p>
<p># contributor license agreements. See the NOTICE file distributed with</p>
<p># this work for additional information regarding copyright ownership.</p>
<p>…. 중략 ….</p>
<p># use nohup so that the Tomcat process will ignore any hangup</p>
<p># signals. Default is "false" unless running on HP-UX in which</p>
<p># case the default is "true"</p>
<p># -----------------------------------------------------------------------------</p>
<p># OS specific support. $var _must_ be set to either true or false.</p>
<p># Polestar 10 APM Configuration</p>
<p># ------------------------------------------------------------------------</p>
<p>export OTEL_JAVAAGENT_CONFIGURATION_FILE=/app/apmagent/agentsetting.conf</p>
<p>JAVA_OPTS="$JAVA_OPTS$ -javaagent:/app/apmagent/opentelemetry-agent.jar"</p>
<p># ------------------------------------------------------------------------</p></td>
</tr>
</tbody>
</table>

Java Agent 수집 설정 항목

Java Agent에 구성 항목에 대한 상세 내용을 확인 할 수 있습니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-003/media/image4.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>otel.resource.attribute 설정은 key=value 문법으로 정의 합니다. 여러 개의 설정은 “,”로 설정하여 key1=value,key2=value2 문법으로 입력 하면 됩니다 내부적으로 정의된 key 값으로 정의 할 경우고 덮어쓰기 형태가 되고 새로운 key 와 값을 정의 할 수 있고 이 정의 된 값은 수신부에서 사용 할 수 있습니다.</p>
<p>예) otel.resource.attribute=lucida.organizationId=661f6ff6c3352163887be149<br />
예) otel.resource.attribute=lucida.organizationId=661f6ff6c3352163887be149, lucida. groupId=groupware</p></td>
</tr>
</tbody>
</table>

<table>
<thead>
<tr class="header">
<th>Polestar EMS AP 주소</th>
<th><p>에이전트에서 수집한 데이터를 수신 받을 폴스타URL 주소를 입력 합니다.</p>
<p>기본 포맷 : http://URL:port</p></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>에이전트 이름</td>
<td><p>애플리케이션에 등록할 에이전트 이름을 입력 합니다.</p>
<p>otel.service.name=&lt;에이전트 이름&gt;</p></td>
</tr>
<tr class="even">
<td>조직 ID</td>
<td><p>등록할 조직 아이디 입력합니다.</p>
<p>otel.resource.attribute=lucida.organizationId=&lt;조직아이디&gt;</p></td>
</tr>
<tr class="odd">
<td>서비스 이름</td>
<td><p>에이전트가 속해있는 서비스 이름을 입력합니다.</p>
<p>otel.resource.attribute=lucida.organizationId=&lt;조직아이디&gt;,</p>
<p>lucida.groupId=&lt;서비스 이름&gt;</p></td>
</tr>
<tr class="even">
<td>전송 프로토콜</td>
<td><p>데이터 전송 시 사용하는 프로토콜 유형<br />
기본 값 : grpc</p>
<p>otel.exporter.otlp.endpoint=grpc</p></td>
</tr>
<tr class="odd">
<td><p>항목별</p>
<p>전송 프로토콜</p></td>
<td><p>트레이스와 성능, 로그 수집 시 사용하는 프로토콜을 설정</p>
<p>형식 : otel.&lt;항목&gt;.exporter</p>
<p>기본 값 : otlp</p>
<p>otel.traces.exporter=otlp</p>
<p>otel.metrics.exporter=otlp</p>
<p>otel.logs.exporter=otlp</p></td>
</tr>
<tr class="even">
<td><p>런타임</p>
<p>성능 수집여부</p></td>
<td><p>Cpu, 메모리등과 같은 런타임 메트릭 성능 데이터 수집 여부를 설정할 수 있습니다.</p>
<p>기본 값 : true</p>
<p>otel.instrumentation.runtime.metrics.enabled=true</p></td>
</tr>
<tr class="odd">
<td>성능수집주기</td>
<td><p>성능 데이터 수집 주기를 설정한다 기본 값은 10초마다 수집한다.</p>
<p>성능 값이 수집되지 않으면 애플리케션에 관제 대상으로 등록 되지 않는다.</p>
<p>기본값 : 10000</p>
<p>설정 단위 : miliseconds</p>
<p>otel.metric.export.interval=10000</p></td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-003/media/image4.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>otel.instrumentation.common.default-enable 옵션을 false로 설정한 경우에는 아래에 라이브러리/프레임워크에 대해 true로 설정된 항목에 대해서만 수집이 됩니다. otel.instrumentation.common.default-enable 옵션을 false로 설정한 경우 아래의 각 라이브러리/프레임워크에 대해 수집 여부를 설정해주어야합니다. 수집 옵션은 otel.instrumentation.[name].enabled에 true에 설정을 통해 사용합니다. 예를 들어 otel.instrumentation.common.default-enable=false로 설정되어 있는 상태에서 Servlet 수행 내역을 수집하려면 otel.instrumentation.servlet.enabled=true로 설정합니다.</p></td>
</tr>
</tbody>
</table>

> 라이브러리/프레임워크 별 수집 설정을 위한 name목록

| 라이브러리/프레임워크                                      | 라이브러리/프레임워크 설정 시 name                     |
| ------------------------------------------------ | ----------------------------------------- |
| Additional methods tracing                       | methods                                   |
| Additional tracing annotations                   | external-annotations                      |
| Activej HTTP                                     | activej-http                              |
| Avaje Jex                                        | avaje-jex                                 |
| Akka Actor                                       | akka-actor                                |
| Akka HTTP                                        | akka-http                                 |
| Alibaba Druid                                    | alibaba-druid                             |
| Apache Axis2                                     | axis2                                     |
| Apache Camel                                     | camel                                     |
| Apache Cassandra                                 | cassandra                                 |
| Apache CXF                                       | cxf                                       |
| Apache DBCP                                      | apache-dbcp                               |
| Apache Dubbo                                     | apache-dubbo                              |
| Apache Geode                                     | geode                                     |
| Apache HttpAsyncClient                           | apache-httpasyncclient                    |
| Apache HttpClient                                | apache-httpclient                         |
| Apache Kafka                                     | kafka                                     |
| Apache MyFaces                                   | jsf-myfaces                               |
| Apache Pekko Actor                               | pekko-actor                               |
| Apache Pekko HTTP                                | pekko-http                                |
| Apache Pulsar                                    | pulsar                                    |
| Apache RocketMQ                                  | rocketmq-client                           |
| Apache Shenyu                                    | apache-shenyu                             |
| Apache Struts 2                                  | struts                                    |
| Apache Tapestry                                  | tapestry                                  |
| Apache Tomcat                                    | tomcat                                    |
| Apache Wicket                                    | wicket                                    |
| Armeria                                          | armeria                                   |
| AsyncHttpClient (AHC)                            | async-http-client                         |
| AWS Lambda                                       | aws-lambda                                |
| AWS SDK                                          | aws-sdk                                   |
| Azure SDK                                        | azure-core                                |
| Clickhouse Client                                | clickhouse                                |
| Couchbase                                        | couchbase                                 |
| C3P0                                             | c3p0                                      |
| Dropwizard Views                                 | dropwizard-views                          |
| Dropwizard Metrics                               | dropwizard-metrics                        |
| Eclipse Grizzly                                  | grizzly                                   |
| Eclipse Jersey                                   | jersey                                    |
| Eclipse Jetty                                    | jetty                                     |
| Eclipse Jetty HTTP Client                        | jetty-httpclient                          |
| Eclipse Metro                                    | metro                                     |
| Eclipse Mojarra                                  | jsf-mojarra                               |
| Eclipse Vert.x HttpClient                        | vertx-http-client                         |
| Eclipse Vert.x Kafka Client                      | vertx-kafka-client                        |
| Eclipse Vert.x Redis Client                      | vertx-redis-client                        |
| Eclipse Vert.x RxJava                            | vertx-rx-java                             |
| Eclipse Vert.x SQL Client                        | vertx-sql-client                          |
| Eclipse Vert.x Web                               | vertx-web                                 |
| Elasticsearch API client                         | elasticsearch-api-client                  |
| Elasticsearch client                             | elasticsearch-transport                   |
| Elasticsearch REST client                        | elasticsearch-rest                        |
| Finagle                                          | finagle-http                              |
| Google Guava                                     | guava                                     |
| Google HTTP client                               | google-http-client                        |
| Google Web Toolkit                               | gwt                                       |
| Grails                                           | grails                                    |
| GraphQL Java                                     | graphql-java                              |
| GRPC                                             | grpc                                      |
| Hibernate                                        | hibernate                                 |
| Hibernate Reactive                               | hibernate-reactive                        |
| HikariCP                                         | hikaricp                                  |
| InfluxDB                                         | influxdb                                  |
| Java HTTP Client                                 | java-http-client                          |
| Java HTTP Server                                 | java-http-server                          |
| Java HttpURLConnection                           | http-url-connection                       |
| Java JDBC                                        | jdbc                                      |
| Java JDBC DataSource                             | jdbc-datasource                           |
| Java RMI                                         | rmi                                       |
| Java Runtime                                     | runtime-telemetry                         |
| Java Servlet                                     | servlet                                   |
| java.util.concurrent                             | executors                                 |
| java.util.logging                                | java-util-logging                         |
| Javalin                                          | javalin                                   |
| JAX-RS (Client)                                  | jaxrs-client                              |
| JAX-RS (Server)                                  | jaxrs                                     |
| JAX-WS                                           | jaxws                                     |
| JBoss Logging Appender                           | jboss-logmanager-appender                 |
| JBoss Logging MDC                                | jboss-logmanager-mdc                      |
| JMS                                              | jms                                       |
| Jodd HTTP                                        | jodd-http                                 |
| JSP                                              | jsp                                       |
| K8s Client                                       | kubernetes-client                         |
| Ktor                                             | ktor                                      |
| kotlinx.coroutines                               | kotlinx-coroutines                        |
| Log4j Appender                                   | log4j-appender                            |
| Log4j MDC (1.x)                                  | log4j-mdc                                 |
| Log4j Context Data (2.x)                         | log4j-context-data                        |
| Logback Appender                                 | logback-appender                          |
| Logback MDC                                      | logback-mdc                               |
| Micrometer                                       | micrometer                                |
| MongoDB                                          | mongo                                     |
| MyBatis                                          | mybatis                                   |
| Netflix Hystrix                                  | hystrix                                   |
| Netty                                            | netty                                     |
| OkHttp                                           | okhttp                                    |
| OpenLiberty                                      | liberty                                   |
| OpenAI                                           | openai                                    |
| OpenSearch REST                                  | opensearch-rest                           |
| OpenTelemetry Extension Annotations              | opentelemetry-extension-annotations       |
| OpenTelemetry Instrumentation Annotations        | opentelemetry-instrumentation-annotations |
| OpenTelemetry API                                | opentelemetry-api                         |
| Oracle UCP                                       | oracle-ucp                                |
| OSHI (Operating System and Hardware Information) | oshi                                      |
| Payara                                           | payara                                    |
| Play Framework                                   | play                                      |
| Play WS HTTP Client                              | play-ws                                   |
| Powerjob                                         | powerjob                                  |
| Quarkus                                          | quarkus                                   |
| Quartz                                           | quartz                                    |
| R2DBC                                            | r2dbc                                     |
| RabbitMQ Client                                  | rabbitmq                                  |
| Ratpack                                          | ratpack                                   |
| ReactiveX RxJava                                 | rxjava                                    |
| Reactor                                          | reactor                                   |
| Reactor Kafka                                    | reactor-kafka                             |
| Reactor Netty                                    | reactor-netty                             |
| Redis Jedis                                      | jedis                                     |
| Redis Lettuce                                    | lettuce                                   |
| Rediscala                                        | rediscala                                 |
| Redisson                                         | redisson                                  |
| Restlet                                          | restlet                                   |
| Scala ForkJoinPool                               | scala-fork-join                           |
| Spark Web Framework                              | spark                                     |
| Spring Batch                                     | spring-batch                              |
| Spring Boot Actuator Autoconfigure               | spring-boot-actuator-autoconfigure        |
| Spring Cloud AWS                                 | spring-cloud-aws                          |
| Spring Cloud Gateway                             | spring-cloud-gateway                      |
| Spring Core                                      | spring-core                               |
| Spring Data                                      | spring-data                               |
| Spring JMS                                       | spring-jms                                |
| Spring Integration                               | spring-integration                        |
| Spring Kafka                                     | spring-kafka                              |
| Spring Pulsar                                    | spring-pulsar                             |
| Spring RabbitMQ                                  | spring-rabbit                             |
| Spring RMI                                       | spring-rmi                                |
| Spring Scheduling                                | spring-scheduling                         |
| Spring Security Config                           | spring-security-config                    |
| Spring Web                                       | spring-web                                |
| Spring WebFlux                                   | spring-webflux                            |
| Spring Web MVC                                   | spring-webmvc                             |
| Spring Web Services                              | spring-ws                                 |
| Spymemcached                                     | spymemcached                              |
| Tomcat JDBC                                      | tomcat-jdbc                               |
| Twilio SDK                                       | twilio                                    |
| Twitter Finatra                                  | finatra                                   |
| Undertow                                         | undertow                                  |
| Vaadin                                           | vaadin                                    |
| Vibur DBCP                                       | vibur-dbcp                                |
| XXL-JOB                                          | xxl-job                                   |
| ZIO                                              | zio                                       |


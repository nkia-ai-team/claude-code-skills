---
menu_path: "룰체인툴설정"
feature: "룰체인 툴 설정"
admin_required: true
original_title: "룰체인툴설정"
category: system
menu_path_verified: false
---
룰체인 툴 설정

연계시스템의 룰체인 툴인 Node-RED의 API를 사용하기 위해서는 토큰 인증을 해야 합니다.

토큰 인증을 하려면 토큰을 이용한 로그인 인증 기능을 활성화하는 작업을 해야 하며 최초 1회 설정만 진행하면 됩니다.

아래와 같은 작업 순서로 진행합니다.

1.  password 해시 생성

2.  Node-RED 설정 파일 수정

3.  Node-RED 재기동

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/system-001/media/image3.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>계정 및 비밀번호는 admin/admin을 기준으로 설정합니다.</p>
<p>계정 및 비밀번호 변경하고자 하는 경우 하위에 굵게 표시된 “admin” 대신 변경하고자 하는 계정명 및 비밀번호로 설정, 비밀번호로 해시 생성하여 설정해야 합니다.</p></td>
</tr>
</tbody>
</table>

Password 설정

Node-RED의 설정파일(settings.js)의 adminAuth \> password항목은 bcrypt 해시로 입력을 해야 하며 해시는 이미 생성된 password로 설정하거나 node가 설치된 서버 또는 PC에서 생성하여 설정할 수 있습니다.

해시를 생성하는 방법은 다음과 같습니다.

1.  node 설치 (node가 설치되지 않은 서버 또는 PC의 경우)

> <https://nodejs.org/ko> 접속
> 
> LTS (Long Term Support) 버전 다운로드
> 
> 설치 마법사 실행 후 “Add to PATH” 옵션 체크 이후 단계는 기본값 그대로 설치
> 
> 설치 확인 방법으로 node -v, npm -v 명령어 실행 후 버전이 출력되면 정상 설치

2.  bcryptjs 설치

> npm install bcryptjs
> 
> added 1 package in 5s

3.  해시 생성

> 콘솔 또는 터미널 창에서 node -e "console.log(require('bcryptjs').hashSync('**admin**', 8)); 실행
> 
> 예)
> 
> C:\\Users\\NKIA\>node -e "console.log(require('bcryptjs').hashSync('admin', 8));"
> 
> $2b$08$xy4NQpEtrBKSL/q7YyadW.def4nHpXHhgAV7NWj7.c46PXDukZq8y
> 
> Node-RED 설정 파일 수정

Node-RED 설정 파일 (settings.js)에서 adminAuth 항목 설정의 주석을 해제하고 (구축 후 최초 기동 시 주석처리되어 있음) 신규 생성한 해시를 password 항목의 값으로 설정합니다.

<table>
<tbody>
<tr class="odd">
<td><p>…</p>
<p>adminAuth: {</p>
<p>type: "credentials",</p>
<p>users: [{</p>
<p>username: "admin",</p>
<p>password: "$2b$08$xy4NQpEtrBKSL/q7YyadW.def4nHpXHhgAV7NWj7.c46PXDukZq8y",</p>
<p>permissions: "*"</p>
<p>}]</p>
<p>},</p>
<p>…</p></td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/system-001/media/image3.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>settings.js 기본 파일 위치는 “/app/lib/docker/volumes/polestar_node-red-data/_data/” 입니다.</p></td>
</tr>
</tbody>
</table>

RuleChain 서비스 설정 확인

RuleChain 설정 파일(application.yml)에서 Node-RED 접속 정보 설정을 확인합니다.

<table>
<tbody>
<tr class="odd">
<td><p>…</p>
<p>node-red:</p>
<p>webclient:</p>
<p>base-url: http://${APPLICATION_DOMAIN}:1880/</p>
<p>callback-url: http://${APPLICATION_DOMAIN}:8888</p>
<p>timeout-seconds: 10</p>
<p>username: admin</p>
<p>password: admin</p>
<p>callback-timeout: 10</p>
<p>url: http://${APPLICATION_DOMAIN}:1880</p>
<p>…</p></td>
</tr>
</tbody>
</table>


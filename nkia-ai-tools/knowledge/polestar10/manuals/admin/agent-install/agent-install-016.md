---
menu_path: "SMSAgent사전설치환경조사"
feature: "사전 설치 환경 조사"
admin_required: true
original_title: "SMSAgent사전설치환경조사"
category: agent-install
menu_path_verified: false
---
사전 설치 환경 조사

SMS Agent 설치 전 사전에 필요한 환경정보입니다.

O/S 지원버전

Agent O/S 지원버전에 따라 Agent 설치가능여부를 확인하시면 됩니다.

<table>
<thead>
<tr class="header">
<th>OS 종류</th>
<th>OS 버전</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>AIX</td>
<td>AIX 5.3 이상</td>
</tr>
<tr class="even">
<td>SunOS(Solaris)</td>
<td>SunOS 5.10 이상</td>
</tr>
<tr class="odd">
<td>HPUX</td>
<td>HPUX 11.23 이상</td>
</tr>
<tr class="even">
<td>LINUX</td>
<td><p>SUSE 계열, CentOS 계열, Red Hat 계열, Ubuntu 계열, Fedora계열</p>
<p>(Kernel 2.4이상)</p></td>
</tr>
<tr class="odd">
<td>Windows</td>
<td><p>Windows 2008, Windows 2012, Windows 2016, Windows 2019, Windows 2022</p>
<p>(Microsoft Visual C++ 2008 SP1 이상 런타임 패키지 설치)</p></td>
</tr>
</tbody>
</table>

에이전트 설치바이너리 정보

O/S 종류/지원 버전에 따라 Agent 설치바이너리를 선택하여 설치하시면 됩니다.

<table>
<thead>
<tr class="header">
<th>OS 종류</th>
<th>설치 바이너리명</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>AIX</td>
<td>polestar10_SMS_AIX_5.3_[Agent버전].tar.gz</td>
<td>AIX 5.3 버전 이상</td>
</tr>
<tr class="even">
<td><p>SunOS</p>
<p>(Solaris)</p></td>
<td>polestar10_SMS_Solaris_sparc_10_[Agent버전].tar.gz</td>
<td><p>Solaris 5.10 이상</p>
<p>(sparc 계열)</p></td>
</tr>
<tr class="odd">
<td></td>
<td>polestar10_SMS_Solaris_x86_10_[Agent버전].tar.gz</td>
<td><p>Solaris 5.10 이상</p>
<p>(intel 계열)</p></td>
</tr>
<tr class="even">
<td>HPUX</td>
<td>polestar10_SMS_HP_11.23_[Agent버전].tar.gz</td>
<td>HPUX 11.23</td>
</tr>
<tr class="odd">
<td></td>
<td>polestar10_SMS_HP_11.31_[Agent버전].tar.gz</td>
<td>HPUX 11.31</td>
</tr>
<tr class="even">
<td>LINUX</td>
<td>polestar10_SMS_Linux64_3.4_[Agent버전].tar.gz</td>
<td><p>uname -i 결과 x86_64 ,</p>
<p>gcc -v 결과 3.4 이상</p></td>
</tr>
<tr class="odd">
<td></td>
<td>polestar10_SMS_Linux_ppc64_4.1_[Agent버전].tar.gz</td>
<td><p>uname -i 결과 ppc64 ,</p>
<p>gcc -v 결과 4.1 이상</p></td>
</tr>
<tr class="even">
<td></td>
<td>polestar10_SMS_Linux_ppc64le_4.8_[Agent버전].tar.gz</td>
<td><p>uname -i 결과 ppc64le ,</p>
<p>gcc -v 결과 4.8 이상</p></td>
</tr>
<tr class="odd">
<td></td>
<td>polestar10_SMS_Linux64GPU_4.4_[Agent버전].tar.gz</td>
<td>GPU 모니터링 필요 시 설치, gcc -v 결과 4.4 이상</td>
</tr>
<tr class="even">
<td></td>
<td>polestar10_SMS_Linux_3.2_[Agent버전].tar.gz</td>
<td><p>32bit 전용,</p>
<p>gcc -v 결과 3.2</p></td>
</tr>
<tr class="odd">
<td></td>
<td>polestar10_SMS_Linux_3.4_[Agent버전].tar.gz</td>
<td><p>32bit 전용,</p>
<p>gcc -v 결과 3.4 이상</p></td>
</tr>
<tr class="even">
<td>Windows</td>
<td>polestar10_SMS_x64_Agent_Win_[Agent버전].exe</td>
<td>Windows 64bit 전용</td>
</tr>
</tbody>
</table>

O/S 환경 설정

Agent가 설치되는 O/S 환경에서 디스크 여유량 정보입니다.

<table>
<thead>
<tr class="header">
<th>설정항목</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>디스크 여유량</td>
<td><p>최소용량 : 500MB 이상</p>
<p>사용자모니터 등록 건 수, Agent 로깅레벨 등 Agent 로그에 쌓이는 양에 따라 달라짐</p></td>
</tr>
</tbody>
</table>

포트 사용 현황

사전에 사용포트 및 방향에 따른 방화벽 오픈이 이루어져야 합니다.

<table>
<thead>
<tr class="header">
<th>사용포트</th>
<th>SOURCE</th>
<th>방향</th>
<th>DESTINATION</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p>1883</p>
<p>(TCP)</p></td>
<td>Agent</td>
<td>-&gt;</td>
<td>AP</td>
<td><p>1.구성/성능 publish</p>
<p>2.사용자모니터/오퍼레이션 subscription</p></td>
</tr>
<tr class="even">
<td><p>443</p>
<p>(TCP)</p></td>
<td>Agent</td>
<td>-&gt;</td>
<td>AP</td>
<td><p>에이전트 자동업데이트 포트</p>
<p>(https)</p></td>
</tr>
<tr class="odd">
<td><p>80,443</p>
<p>(TCP)</p></td>
<td>Agent</td>
<td>-&gt;</td>
<td>*.microsoft.com / *.windowsupdate.com / *.windows.com</td>
<td>윈도우 업데이트 및 분석</td>
</tr>
<tr class="even">
<td><p>42005</p>
<p>(TCP)</p></td>
<td>Agent</td>
<td>-&gt;</td>
<td>AP</td>
<td>파일배포(바이너리/스크립트) 용도</td>
</tr>
<tr class="odd">
<td><p>41003</p>
<p>(TCP)</p></td>
<td>SMSAgentL</td>
<td>-&gt;</td>
<td>MAgentL</td>
<td>Agent서버 내 SMSAgentL에서 MAgentL방향으로 로컬통신</td>
</tr>
<tr class="even">
<td></td>
<td>DCAAgentL</td>
<td>-&gt;</td>
<td>MAgentL</td>
<td>Agent서버 내 DCAAgentL에서 MAgentL방향으로 로컬통신</td>
</tr>
</tbody>
</table>


---
menu_path: "트랩목록"
feature: "Trap 목록"
admin_required: false
original_title: "트랩목록"
category: alert
menu_path_verified: false
---
Trap 목록

전체 구성에서 \[Trap\]을 선택하면 등록되어 있는 전체 Trap 포트 목록을 확인할 수 있습니다. Trap 포트는 대상 네트워크 장비로부터 SNMP Trap 이벤트를 수신하기 위해 사용되는 포트입니다. SNMP Trap은 요청과 응답 방식을 사용하는 대신 대상 리소스로 등록된 네트워크 장비에 특정한 이벤트가 발생할 경우 지정된 Trap 포트를 통해 수신 시스템으로 바로 전달해주는 방식입니다.

Trap 목록을 통해 Trap 이벤트 수신을 위한 포트 번호, 상태, 이름, 프로토콜, SNMP 버전, 대상 리소스, 등록 일시를 확인할 수 있습니다. 또한 해당 화면에서 등록된 Trap 포트를 삭제할 수 있습니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/alert-027/media/image2.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>전체 구성에서 관리되는 Trap은 [전체구성] 메뉴의 [관리 대상 추가]에서 Trap [관리 대상 등록]을 통해 등록되어야 합니다. 그리고 Trap 목록의 대상 리소스는 로그인 사용자에게 읽기 권한이 할당된 계정 내 네트워크 장비만 표시됩니다.</p></td>
</tr>
</tbody>
</table>

![](./images/alert-027/media/image3.png)

> ▶ \[그림1\] Trap 목록
> 
> Trap 목록

<table>
<thead>
<tr class="header">
<th>상태</th>
<th><p>포트 상태 가용성을 색상 아이콘으로 표시합니다.</p>
<table>
<thead>
<tr class="header">
<th><img src="./images/alert-027/media/image4.png" style="width:0.18403in;height:0.20027in" /><strong>: Trap 포트 정상 상태 표시(Up)</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p><img src="./images/alert-027/media/image1.png" /><strong>: Trap 포트 다운 상태 표시(Down)</strong></p>
<p><img src="./images/alert-027/media/image5.png" style="width:0.18819in;height:0.20074in" /><strong>: Trap 포트 알 수 없음 상태 표시(Unknown)</strong></p></td>
</tr>
</tbody>
</table></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>포트 번호</td>
<td>Trap 포트 등록 시 입력했던 포트 번호가 표시됩니다. (Trap은 기본적으로 162 번을 사용합니다.)</td>
</tr>
<tr class="even">
<td>이름</td>
<td>Trap 포트 등록 시 입력했던 이름이 표시됩니다. 등록 시 입력하지 않은 경우 프로토콜과 포트 번호를 조합한 이름이 자동으로 설정됩니다. 예를 들어, 162 포트 번호에 UDP 프로토콜을 사용하면서 이름을 설정하지 않은 경우 자동으로 udp_162라는 이름이 설정됩니다.</td>
</tr>
<tr class="odd">
<td>프로토콜</td>
<td>Trap 포트 등록 시 입력했던 프로토콜 정보(ex. TCP 또는 UDP)가 표시됩니다. 대부분 UDP 프로토콜을 사용합니다.</td>
</tr>
<tr class="even">
<td>SNMP 버전</td>
<td>Trap 포트 등록 시 입력했던 SNMP Trap 이벤트에 사용할 SNMP 버전 정보가 표시됩니다.</td>
</tr>
<tr class="odd">
<td>대상 리소스</td>
<td>Trap 포트 등록 시 선택했던 대상 리소스가 표시됩니다. 계정 내의 네트워크 장비 중에서 로그인한 사용자에게 읽기 권한이 할당된 장비만 목록에 표시됩니다.</td>
</tr>
<tr class="even">
<td>등록 일시</td>
<td>Trap 포트 등록 일시가 표시됩니다.</td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/alert-027/media/image2.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>SNMP Trap은 네트워크 장비에서 이벤트 발생 시, AP 서버를 향해 Trap 이벤트를 전송하도록 설정되어 있어야 합니다. 수신된 모든 Trap 이벤트는 대메뉴의 [알람 &amp; 이벤트]의 [이벤트 현황]에서 확인할 수 있습니다.</p></td>
</tr>
</tbody>
</table>

Trap 삭제

삭제할 Trap 포트를 선택하고 우측 상단의 \[삭제\] 버튼을 선택하여 등록된 Trap 포트를 삭제할 수 있습니다. Trap 포트 삭제 시 해당 포트를 사용한 Trap 이벤트 수신 뿐 아니라 해당 Trap 포트를 사용하는 다른 계정의Trap 이벤트 수신 또한 중지됩니다.

![](./images/alert-027/media/image6.png)

▶ \[그림2\] Trap 삭제

> Trap 삭제 절차

1.  삭제하고자 하는 Trap 선택 (다중 선택 가능)

2.  테이블 우측 상단의 삭제 아이콘 클릭

3.  메시지창에서 확인 클릭

컬럼 수정

Trap 목록의 우측 상단 \[컬럼 수정\] 버튼을 통해 Trap 목록에 원하는 컬럼만을 표시하거나 제외할 수 있습니다. 엑셀 저장시에도 컬럼 수정을 통해 표시된 컬럼만 저장됩니다. 컬럼 수정 팝업창에서는 컬럼 검색 기능을 제공하며 선택된 항목을 하단에 표시하고 표시된 컬럼을 제외할 수 있는 기능을 제공합니다.

![](./images/alert-027/media/image7.png)

▶ \[그림3\] Trap 목록 컬럼 수정

> Trap컬럼 수정 절차

1.  Trap목록에서 우측 상단 컬럼 수정 아이콘 클릭

2.  컬럼 수정 팝업창에서 화면에 표시하고자 하는 컬럼을 체크박스에서 선택

3.  저장 버튼 클릭

엑셀 저장

Trap 목록의 우측 상단 \[엑셀 저장\] 버튼을 통해 Trap목록을 엑셀로 저장할 수 있습니다. 컬럼 수정 기능, 상단 태그 검색 기능, 그리드 컬럼 검색 기능 등을 통해 엑셀에 보여줄 컬럼과 내용을 원하는 조건에 맞게 필터링하여 저장할 수 있습니다.

![](./images/alert-027/media/image8.png)

▶ \[그림4\] Trap목록 엑셀 저장

> Trap목록 엑셀 저장 및 조회 절차

1.  Trap목록에서 우측 상단 엑셀 저장 아이콘 클릭

2.  브라우저 우측 상단 창에 저장된 엑셀 파일명이 표시됨

3.  해당 파일명을 클릭하여 엑셀 파일 확인


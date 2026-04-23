---
menu_path: "TCP포트감시"
feature: "TCP 포트 감시"
admin_required: false
original_title: "TCP포트감시"
category: perf
menu_path_verified: false
---
TCP 포트 감시

서버 관점에서 특정 서비스 포트 상태(가용성, 응답시간, 응답여부)를 감시할 수 있는 기능입니다.

![](./images/perf-005/media/image2.png)

▶ \[그림1\] TCP 포트 감시 목록

화면 지표

<table>
<thead>
<tr class="header">
<th>상태</th>
<th><p>TCP 포트 감시 항목의 가용성 상태를 색상으로 표현합니다.</p>
<p><img src="./images/perf-005/media/image3.png" style="width:0.225in;height:0.19167in" /> : TCP 포트 응답 있음</p>
<p><img src="./images/perf-005/media/image4.png" style="width:0.21667in;height:0.20833in" /> : TCP 포트 응답 없음</p>
<p><img src="./images/perf-005/media/image5.png" style="width:0.22502in;height:0.21669in" /> : TCP 포트 응답 여부 수집 불가</p></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>이름</td>
<td>TCP 포트 감시 항목의 이름을 표시합니다.</td>
</tr>
<tr class="even">
<td>시스템 이름</td>
<td>TCP 포트 감시 항목이 등록된 서버의 시스템 이름을 표시합니다.</td>
</tr>
<tr class="odd">
<td>호스트 이름</td>
<td>TCP 포트 감시 항목이 등록된 서버의 호스트 이름을 표시합니다.</td>
</tr>
<tr class="even">
<td>IP 주소</td>
<td>TCP 포트 감시 항목이 등록된 서버의 IP 주소를 표시합니다.</td>
</tr>
<tr class="odd">
<td>감시 IP 주소</td>
<td>TCP 포트 감시 중인 IP 주소를 표시합니다.</td>
</tr>
<tr class="even">
<td>감시 포트</td>
<td>TCP 포트 감시 중인 포트 번호를 표시합니다.</td>
</tr>
<tr class="odd">
<td>등록 일시</td>
<td>TCP 포트 감시 항목이 등록된 일시를 표시합니다.</td>
</tr>
<tr class="even">
<td>설정</td>
<td>TCP 포트 감시 설정을 변경할 수 있는 TCP 포트 상세 화면을 호출합니다.</td>
</tr>
</tbody>
</table>

TCP 포트 감시 추가

모니터링할 TCP 포트 정보를 설정합니다. 모든 필수 항목을 입력해야 \[저장\] 버튼이 활성화됩니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/perf-005/media/image6.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>사용자가 ‘쓰기’ 이상의 권한을 가지고 있는 서버에만 TCP 포트 감시를 등록할 수 있습니다.</p>
<p>TCP 포트 감시 추가 시, 서버 장비에 설정된 권한이 자동으로 적용됩니다. TCP 포트 감시 수정 기능을 통해 권한 정보를 변경할 수 있습니다.</p></td>
</tr>
</tbody>
</table>

![](./images/perf-005/media/image7.png)

▶ \[그림2\] TCP 포트 감시 추가

기본 정보

| 대상 리소스 | 감시 항목의 타입을 표시합니다. ‘TCP 포트 모니터’ 타입이 자동으로 설정되어 있습니다.                  |
| ------ | ------------------------------------------------------------------- |
| 이름     | TCP 포트 감시 항목의 이름을 입력합니다. 미입력시 감시할 IP와 포트 정보로 설정됩니다. (포맷: ‘IP주소:포트’) |
| 설명     | TCP 포트 감시 항목의 설명을 입력합니다.                                            |

장비 정보

TCP 포트 감시 항목을 등록할 장비를 1대 이상 선택합니다. 장비 목록에는 사용자가 ‘쓰기’ 이상의 권한을 가지고 있는 서버만 표시되며, 태그 필터를 사용해 원하는 대상 장비를 상세 검색할 수 있습니다.

설정 정보

| IP 주소 | 원격지 서버의 IP 주소를 입력합니다.     |
| ----- | ------------------------- |
| 포트    | 원격지 서버의 TCP 포트 번호를 입력합니다. |

TCP 포트 감시 추가 절차

1.  TCP 포트 감시 목록 우측 상단의 \[추가\] 버튼 클릭

2.  기본 정보, 장비 정보, 설정 정보를 입력하고 \[저장\] 버튼 클릭

TCP 포트 성능 정보 조회

TCP 포트 감시 목록에서 ‘이름’ 필드를 클릭하여 등록한 TCP 포트 감시의 성능 정보를 조회합니다. TCP 포트 감시 설정 정보에 따라 특정 TCP 포트의 응답 정보를 확인할 수 있습니다.

![](./images/perf-005/media/image8.png)

▶ \[그림3\] TCP 포트 성능 정보

TCP 포트 감시 수정

TCP 포트 감시 목록에서 ‘설정’ 필드를 클릭하여 등록한 TCP 포트 감시의 설정 정보를 수정할 수 있습니다. TCP 포트 감시의 기본 권한은 서버 장비의 권한을 따르므로 ‘상속’ 옵션이 활성화되어 있습니다. ‘상속’ 옵션을 비활성화하면 TCP 포트 감시에만 적용되는 전용 권한을 설정할 수 있습니다. 모든 필수 항목을 입력해야 \[저장\] 버튼이 활성화됩니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/perf-005/media/image6.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>사용자가 ‘쓰기’ 이상의 권한을 가지고 있는 TCP 포트 감시만 수정할 수 있습니다.</p></td>
</tr>
</tbody>
</table>

![](./images/perf-005/media/image9.png)

▶ \[그림4\] TCP 포트 상세

TCP 포트 감시 수정 절차

1.  TCP 포트 감시 목록에서 수정할 항목의 ‘설정’ 필드 클릭

2.  기본 정보, 설정 정보, 역할 및 권한 설정 중 수정할 항목을 변경하고 \[저장\] 버튼 클릭

TCP 포트 감시 삭제

TCP 포트 감시 목록에서 특정 TCP 포트 항목을 삭제할 수 있습니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/perf-005/media/image6.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>TCP 포트 감시의 역할 및 권한 상속 여부에 따라 TCP 포트 감시를 삭제할 수 있는 최소 권한이 달라집니다. 역할 및 권한 상속 여부는 TCP 포트 상세 화면에서 확인할 수 있습니다.</p>
<ul>
<li><p>상속 ON: ‘쓰기’ 이상의 권한 필요</p></li>
<li><p>상속 OFF: ‘삭제’ 권한 필요</p></li>
</ul></td>
</tr>
</tbody>
</table>

![](./images/perf-005/media/image10.png)

▶ \[그림5\] TCP 포트 감시 삭제

TCP 포트 감시 삭제 절차

1.  TCP 포트 감시 목록에서 삭제할 TCP 포트 선택 (다수 선택 가능)

2.  TCP 포트 감시 목록 우측 상단의 \[삭제\] 버튼 클릭

TCP 포트 감시 일괄 추가

TCP 포트 감시 설정 정보를 CSV 형식으로 입력하여 다수의 TCP 포트 감시를 일괄 등록할 수 있습니다.

\[등록된 설정 다운로드\]를 통해 등록되어 있는 TCP 포트 감시 설정 정보를 CSV 파일로 다운로드하고, 이 CSV 파일을 활용하여 기존 TCP 포트 감시 설정을 일괄 업데이트 할 수 있습니다.

TCP 포트 감시 설정 정보를 저장한 CSV 파일을 업로드하고 \[검증\] 버튼을 클릭하면 CSV 파일 데이터의 유효성을 검사하여 등록 진행 가능 여부를 판별합니다. 하나라도 잘못된 설정이 포함되어 있는 경우 일괄 등록을 진행할 수 없습니다. 이 경우, ‘검증 결과’ 필드를 참고하여 설정 오류를 수정하고 다시 검증을 진행하시기 바랍니다.

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/perf-005/media/image6.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>CSV 파일에서 일괄 추가 대상 장비를 태그로 설정한 경우, 사용자의 장비 권한에 따라 TCP 포트 감시가 적용되는 장비가 달라질 수 있습니다.</p>
<ul>
<li><p>등록: 사용자가 ‘쓰기’ 이상의 권한을 가지고 있는 서버</p></li>
<li><p>수정: 사용자가 ‘쓰기’ 이상의 권한을 가지고 있는 TCP 포트 감시</p></li>
</ul></td>
</tr>
</tbody>
</table>

![](./images/perf-005/media/image11.png)

▶ \[그림6\] TCP 포트 감시 일괄 추가

![](./images/perf-005/media/image12.png)

▶ \[그림7\] TCP 포트 감시 일괄 추가 – 검증 및 업로드 설정 목록

TCP 포트 감시 일괄 추가 절차

1.  TCP 포트 감시 목록 우측 상단의 \[일괄 추가\] 버튼 클릭

2.  \[등록된 설정 다운로드\] 버튼 클릭

3.  다운로드 받은 CSV 파일을 열고, 기존 등록되어 있는 TCP 포트 감시 설정을 참고해서 신규 TCP 포트 감시 설정 추가

4.  CSV 파일에 있던 기존 TCP 포트 감시 설정 삭제

5.  일괄 추가 드로어에서 CSV 파일 업로드하고 \[검증\] 버튼 클릭

6.  ‘업로드 설정 목록’에서 결함 유무 확인하고, 결함이 없는 경우 \[저장\] 버튼 클릭


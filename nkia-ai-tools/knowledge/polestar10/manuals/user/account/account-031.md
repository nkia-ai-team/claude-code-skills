---
menu_path: "시스템설정2차인증-(1)"
feature: "2차 인증"
admin_required: false
original_title: "시스템설정2차인증-(1)"
category: account
menu_path_verified: false
---
2차 인증

운영관리를 선택하면 시스템 설정 메뉴를 선택 합니다.

시스템 설정은 보안, 메일 서버, SMS 통보, 2차 인증 탭으로 구성되어 있습니다..

2차 인증설정

![](/home/sjbang/dev/claude-code-skills/nkia-ai-tools/knowledge/polestar10/_staging/user/images/시스템설정2차인증-\(1\)/media/image1.png)

▶ \[그림1\] 2차 인증설정 화면

인증 등록 절차

1\. 운영관리 \> 시스템 설정 \> 2차 인증 탭 클릭

2\. 순서대로 값 입력

3\. 오퍼레이션 / 로그인 2차인증 여부 활성화

4\. 인증 메세지 ${authCode}를 포함하여 입력

5\. 인증 방식(다중 선택 가능)

\- SMS -\> SMS 통보 탭 \> 사용 여부 YES 후 저장해야 방식에서 선택 가능

\- EMAIL -\> 메일 서버 탭 \> 사용 여부 YES 후 저장해야 방식에서 선택 가능

6\. 필수 값 모두 입력 후 저장

7\. 활성화한 서비스 이동 후 2차 인증 서비스 확인

화면 지표

| 대기시간 설정     | 사용자가 인증 제한 시간을 설정합니다. (1이상의 정수만 입력 가능)                |
| ----------- | ----------------------------------------------------- |
| 인증 설정 여부    | 사용자가 활성화활 인증을 설정합니다.                                  |
| 주요 기능 인증 설정 | 사용자가 인증 메시지와 인증 방식을 입력, 선택합니다.                        |
| 인증 메시지      | 사용자가 ${authCode}라는 문구를 반드시 포함하여 인증 메시지를 입력합니다.        |
| 인증 방식       | 사용자가 메일 서버, SMS 통보 탭에서 사용여부를 YES로 저장한 후 인증 방식을 선택합니다. |

2차인증 로그인

![](/home/sjbang/dev/claude-code-skills/nkia-ai-tools/knowledge/polestar10/_staging/user/images/시스템설정2차인증-\(1\)/media/image2.png)

![](/home/sjbang/dev/claude-code-skills/nkia-ai-tools/knowledge/polestar10/_staging/user/images/시스템설정2차인증-\(1\)/media/image3.png)

▶ \[그림2\] 2차인증 로그인 인증 화면

로그인 2차 인증 절차

1\. 로그인

2\. 2차 인증에서 설정한 인증 방식으로 인증

3\. 사용자가 등록한 이메일 주소로 인증 받기 클릭

4\. 설정한 인증 시간내로 인증 번호 입력

5\. 인증 성공 후 조직 선택

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/account-031/media/image4.png" style="width:0.21667in;height:0.21667in" />주의</p>
<p>1. OTP 기능 제공 X</p>
<p>2. 해당 사용자 계정에서 등록한 이메일 계정으로만 확인 가능</p>
<p>3. SMS는 SMS 통보 설정에서 등록한 DB URL로 접속 후 메시지 확인</p>
<p>4. 인증 시간이 지나면 다시 인증 번호 받아야 인증 성공 가능</p>
<p>5. 조직이 1개인 계정은 바로 포털 화면으로 이동</p></td>
</tr>
</tbody>
</table>

화면 지표

| SMS 인증 / Email 인증 | 사용자가 인증 받을 방식을 선택합니다.                       |
| ----------------- | ------------------------------------------- |
| 인증번호 받기           | 사용자가 입력한 값으로 인증번호를 받습니다.                    |
| 인증번호 입력           | 제한시간 내에 사용자는 인증번호를 입력합니다.                   |
| 다음                | 인증번호를 입력 전까지는 비활성화, 인증번호를 입력 후 인증 확인을 받습니다. |

오퍼레이션 2차인증 화면

![](/home/sjbang/dev/claude-code-skills/nkia-ai-tools/knowledge/polestar10/_staging/user/images/시스템설정2차인증-\(1\)/media/image5.png)

![](/home/sjbang/dev/claude-code-skills/nkia-ai-tools/knowledge/polestar10/_staging/user/images/시스템설정2차인증-\(1\)/media/image6.png)

![](/home/sjbang/dev/claude-code-skills/nkia-ai-tools/knowledge/polestar10/_staging/user/images/시스템설정2차인증-\(1\)/media/image7.png)

▶ \[그림3\] 2차인증 오퍼레이션 화면

오퍼레이션 2차 인증 절차

1\. 로그인

2\. 전체 구성 \> 서버 \> 서버 클릭 \> 상세 이동

3\. 서버 오퍼레이션 버튼 클릭

4\. 항목 실행

5\. 2차 인증에서 설정한 인증 방식으로 인증

6\. 사용자가 등록한 이메일 주소로 인증 받기 클릭

7\. 설정한 인증 시간내로 인증 번호 입력

8\. 인증 성공 후 오퍼레이션 실행

화면 지표

| SMS 인증 / Email 인증 | 사용자가 인증 받을 방식을 선택합니다.                       |
| ----------------- | ------------------------------------------- |
| 인증번호 받기           | 사용자가 입력한 값으로 인증번호를 받습니다.                    |
| 인증번호 입력           | 제한시간 내에 사용자는 인증번호를 입력합니다.                   |
| 다음                | 인증번호를 입력 전까지는 비활성화, 인증번호를 입력 후 인증 확인을 받습니다. |


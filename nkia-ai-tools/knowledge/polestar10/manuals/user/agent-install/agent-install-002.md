---
menu_path: "WPMAgent삭제"
feature: "WPM Agent 삭제"
admin_required: false
original_title: "WPMAgent삭제"
category: agent-install
menu_path_verified: false
---
WPM Agent 삭제

확인 사항

WPM Agent를 삭제하기 위해서는 애플리케이션 기동 스크립트 등을 수정해야 하며 WPM에이전트 옵션 제거 후 애플리케이션을 재기동해야 WPM 애플리케이션 화면에서 에이전트를 삭제할 수 있습니다. 작업 전 애플리케이션 재기동 가능 여부를 확인하세요.

**WPM Agent 삭제**

1.  **Java 애플리케이션에 WPM Agent 옵션 제거**

> WPM Java Agent을 제거하기 위해서는 자바 애플리케이션 혹은 WAS 서버의 자바 옵션에 추가한 WPM Agent 옵션을 모두 제거해야 합니다.
> 
> 예시) 아래 밑줄로 표시된 옵션을 모두 제거합니다.

<table>
<tbody>
<tr class="odd">
<td><blockquote>
<p><span class="underline">JAVA_OPTS="$JAVA_OPTS -javaagent:&lt;애플리케이션별 에이전트 설치경로&gt;/wpmagent.jar" -Dwpmagent.conf=&lt;애플리케이션별 에이전트 설치경로&gt;/wpmagent.conf"</span></p>
</blockquote></td>
</tr>
</tbody>
</table>

2.  **Java 애플리케이션 재기동**

<table>
<tbody>
<tr class="odd">
<td><p><img src="./images/agent-install-002/media/image1.png" style="width:0.21667in;height:0.21667in" />노트</p>
<p>자바 애플리케이션 개발 환경, WAS 종류에 따라 또는 관리자에 따라 애플리케이션 기동은 다를 가능성이 높습니다. 애플리케이션 재기동 방법을 사전 환경 조사서 작성 시 모두 전달받거나 또는 애플리케이션 관리자와 함께 작업하도록 합니다</p></td>
</tr>
</tbody>
</table>

3.  **완전 삭제를 위해서 에이전트 디렉토리를 삭제합니다.**


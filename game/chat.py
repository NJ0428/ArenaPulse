from direct.gui.DirectGui import DirectEntry, DirectLabel, DGG
from panda3d.core import TextNode, Vec4
import time


class ChatSystem:
    def __init__(self, game):
        self.game = game
        self.messages = []  # 채팅 메시지 저장
        self.max_messages = 8  # 표시할 최대 메시지 수
        self.is_chat_open = False  # 채팅창 열림 상태

        # 채팅 UI 생성
        self._create_chat_ui()

        print("[Chat] 채팅 시스템 초기화 완료")

    def _create_chat_ui(self):
        """채팅 UI 생성"""
        # 채팅 메시지 표시 영역 (화면 왼쪽 하단) - 초기에는 숨김
        self.chat_display = DirectLabel(
            pos=(-0.83, 0, -0.35),
            frameSize=(-0.01, 0.5, -0.01, 0.45),
            frameColor=(0, 0, 0, 0.5),
            text="",
            text_scale=0.04,
            text_align=TextNode.ALeft,
            text_pos=(0.02, 0.42),
            text_fg=(1, 1, 1, 1),
            text_wordwrap=16,
            state=DGG.NORMAL
        )
        self.chat_display.hide()  # 평소에는 숨김

        # 채팅 입력창 (초기에는 숨김)
        self.chat_entry = DirectEntry(
            pos=(-0.83, 0, -0.85),
            scale=0.05,
            frameColor=(0.2, 0.2, 0.2, 0.8),
            text_fg=(1, 1, 1, 1),
            initialText="",
            numLines=1,
            width=35,
            focus=0,
            command=self._send_message
        )
        self.chat_entry.hide()

        # 안내 메시지 표시
        self._add_system_message("Press T to open chat")

    def _send_message(self, text):
        """메시지 전송 (영어만 허용)"""
        # 빈 메시지 무시
        if not text or text.strip() == "":
            self.close_chat()
            return

        # 영어와 공백, 기본 문장부호만 허용 (한글 등 제거)
        filtered_text = ''.join(char for char in text if char.isascii() or char.isspace())

        # 필터링 후 빈 메시지 확인
        if not filtered_text.strip():
            self._add_system_message("영어만 입력 가능합니다.")
            self.close_chat()
            return

        # 메시지 추가
        self._add_message("Player", filtered_text)

        # 입력창 초기화 및 닫기
        self.chat_entry.enterText('')
        self.close_chat()

    def _add_message(self, sender, message):
        """일반 메시지 추가"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {sender}: {message}"
        self.messages.append(formatted_message)

        # 메시지 수 제한 (최근 N개만 표시)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        # UI 업데이트
        self._update_chat_display()

    def _add_system_message(self, message):
        """시스템 메시지 추가"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [SYSTEM] {message}"
        self.messages.append(formatted_message)

        # 메시지 수 제한
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        # UI 업데이트
        self._update_chat_display()

    def _update_chat_display(self):
        """채팅 표시 업데이트"""
        # 최근 N개 메시지만 표시 (줄바꿈으로 구분)
        display_messages = self.messages[-self.max_messages:]
        full_text = "\n".join(display_messages)
        self.chat_display['text'] = full_text

    def open_chat(self):
        """채팅 열기"""
        self.is_chat_open = True
        self.chat_display.show()  # 메시지 표시 영역도 표시
        self.chat_entry.show()
        self.chat_entry['focus'] = 1  # 입력창에 포커스

        # 마우스 커서 표시
        from panda3d.core import WindowProperties
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.game.win.requestProperties(props)

    def close_chat(self):
        """채팅 닫기"""
        self.is_chat_open = False
        self.chat_entry['focus'] = 0
        self.chat_entry.hide()
        self.chat_display.hide()  # 메시지 표시 영역도 숨김

        # 마우스 다시 숨기고 중앙으로
        from panda3d.core import WindowProperties
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)
        self.game.win.requestProperties(props)

        # 마우스 중앙으로 리셋
        center_x = self.game.win.getXSize() // 2
        center_y = self.game.win.getYSize() // 2
        self.game.win.movePointer(0, center_x, center_y)

    def toggle_chat(self):
        """채팅 토글"""
        if self.is_chat_open:
            self.close_chat()
        else:
            self.open_chat()

    def is_open(self):
        """채팅 열림 상태 반환"""
        return self.is_chat_open

    def cleanup(self):
        """정리"""
        if self.chat_display:
            self.chat_display.destroy()
        if self.chat_entry:
            self.chat_entry.destroy()

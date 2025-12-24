from direct.gui.DirectGui import (
    DirectFrame,
    DirectButton,
    DGG
)
from panda3d.core import TextNode, Vec4


class PauseMenu:
    def __init__(self, game, resume_callback, quit_callback):
        self.game = game
        self.resume_callback = resume_callback
        self.quit_callback = quit_callback
        self.menu_frame = None

        self._create_menu()

    def _create_menu(self):
        """일시정지 메뉴 UI 생성"""
        # 메뉴 배경 프레임
        self.menu_frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.4, 0.4, -0.4, 0.4),
            pos=(0, 0, 0)
        )
        self.menu_frame.hide()

        # 제목 텍스트
        self.title = DirectButton(
            parent=self.menu_frame,
            text="PAUSED",
            text_scale=0.15,
            text_pos=(0, 0.2),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            state=DGG.DISABLED
        )

        # 계속하기 버튼
        self.resume_btn = DirectButton(
            parent=self.menu_frame,
            text="RESUME",
            text_scale=0.08,
            text_pos=(0, 0),
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.5, 0.2, 1),
            frameSize=(-0.25, 0.25, -0.06, 0.06),
            pos=(0, 0, 0.1),
            command=self.resume_callback
        )

        # 게임 종료 버튼
        self.quit_btn = DirectButton(
            parent=self.menu_frame,
            text="QUIT",
            text_scale=0.08,
            text_pos=(0, 0),
            text_fg=(1, 1, 1, 1),
            frameColor=(0.7, 0.2, 0.2, 1),
            frameSize=(-0.25, 0.25, -0.06, 0.06),
            pos=(0, 0, -0.05),
            command=self.quit_callback
        )

        print("[PauseMenu] Pause menu created")

    def show(self):
        """메뉴 표시"""
        self.menu_frame.show()

    def hide(self):
        """메뉴 숨김"""
        self.menu_frame.hide()

    def is_visible(self):
        """메뉴 표시 상태 반환"""
        return self.menu_frame.isHidden() == False

    def cleanup(self):
        """메뉴 정리"""
        if self.menu_frame:
            self.menu_frame.destroy()

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import (
    WindowProperties,
    AmbientLight,
    DirectionalLight,
    Point3,
    Vec4,
    TransparencyAttrib,
    CardMaker,
    TextNode
)
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE
from game.database import Database
from game.player import Player
from game.controls import Controls


class ArenaPulseGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # 창 설정 (Full HD 1920x1080)
        self._setup_window()

        # 데이터베이스 초기화
        self.db = Database()

        # 조명 설정
        self._setup_lights()

        # 기본 씬 생성
        self._create_scene()

        # 플레이어 생성
        self.player = Player(self)

        # 카메라를 플레이어에 연결 (FPS)
        self._setup_fps_camera()

        # 컨트롤 설정
        self.controls = Controls(self, self.player)

        # 조준점 UI 생성
        self._create_crosshair()

        # 메인 업데이트 태스크
        self.taskMgr.add(self._update_task, "UpdateTask")

        print("[Game] ArenaPulse 게임 시작! (DOOM 스타일 FPS)")
        print("[Game] WASD: 이동 | 마우스: 조준 | 좌클릭: 원거리 | 우클릭/Space: 근접 | ESC: 일시정지")

    def _setup_window(self):
        """창 설정"""
        props = WindowProperties()
        props.setTitle(WINDOW_TITLE)
        props.setSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.win.requestProperties(props)

        # 배경색 하늘색으로 설정
        self.setBackgroundColor(0.5, 0.7, 0.9, 1.0)

        print(f"[Game] 해상도: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

    def _setup_lights(self):
        """조명 설정"""
        # 주변광 (Ambient Light) - 더 밝게
        ambient_light = AmbientLight("ambient_light")
        ambient_light.setColor(Vec4(0.5, 0.5, 0.5, 1))
        ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_light_np)

        # 방향광 (Directional Light)
        directional_light = DirectionalLight("directional_light")
        directional_light.setColor(Vec4(0.8, 0.8, 0.8, 1))
        directional_light_np = self.render.attachNewNode(directional_light)
        directional_light_np.setHpr(45, -45, 0)
        self.render.setLight(directional_light_np)

        print("[Game] 조명 설정 완료")

    def _create_scene(self):
        """기본 씬 생성 - 회색 타일 바닥"""
        # 회색 타일 바닥 생성
        self.floor = self.loader.loadModel("models/box")
        self.floor.reparentTo(self.render)
        self.floor.setScale(100, 100, 0.1)
        self.floor.setPos(0, 0, -0.1)
        self.floor.setColor(0.5, 0.5, 0.5, 1.0)  # 회색

        print("[Game] 씬 생성 완료 (회색 바닥)")

    def _setup_fps_camera(self):
        """FPS 카메라 설정"""
        self.disableMouse()
        # 카메라를 플레이어에 연결
        self.player.setup_camera(self.camera)
        print("[Game] FPS 카메라 설정 완료")

    def _create_crosshair(self):
        """Create crosshair UI"""
        # Crosshair (+)
        self.crosshair = OnscreenText(
            text="+",
            pos=(0, 0),
            scale=0.15,
            fg=(0, 1, 0, 1),
            align=TextNode.ACenter,
            mayChange=False
        )

        print("[Game] Crosshair UI created")

    def _update_task(self, task):
        """메인 게임 루프"""
        dt = globalClock.getDt()

        if not self.controls.is_paused():
            self.player.update(dt)
            self.controls.update()

        return Task.cont

    def _exit_game(self):
        """게임 종료"""
        print("[Game] 게임 종료 중...")
        self.player.cleanup()
        self.controls.cleanup()
        self.db.close()
        sys.exit()


def main():
    game = ArenaPulseGame()
    game.run()


if __name__ == "__main__":
    main()

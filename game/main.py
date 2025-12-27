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
    TextNode,
    Texture,
    TextureStage,
    ColorAttrib
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

        # 구름 생성
        self._create_clouds()

        # 플레이어 생성
        self.player = Player(self)

        # 카메라를 플레이어에 연결 (FPS)
        self._setup_fps_camera()

        # 컨트롤 설정
        self.controls = Controls(self, self.player)

        # 조준점 UI 생성
        self._create_crosshair()

        # 총알 UI 생성
        self._create_ammo_ui()

        # 메인 업데이트 태스크
        self.taskMgr.add(self._update_task, "UpdateTask")

        print("[Game] ArenaPulse game started! (DOOM style FPS)")
        print("[Game] WASD: Move | Mouse: Aim | L-Click: Shoot | R-Click/Space: Melee | R: Reload | ESC: Pause")

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
        """기본 씬 생성 - 흰색 돌 질감 바닥"""
        # CardMaker로 바닥 평면 생성 (정점 색상 문제 해결)
        cm = CardMaker('floor')
        cm.setFrame(-100, 100, -100, 100)  # 200x200 크기
        self.floor = self.render.attachNewNode(cm.generate())

        # 바닥을 수평으로 회전
        self.floor.setP(-90)
        self.floor.setPos(0, 0, -0.1)

        # 돌 질감 텍스처 로드
        stone_texture = self.loader.loadTexture("textures/stone.png")
        if stone_texture:
            # 텍스처 반복 설정
            stone_texture.setWrapU(Texture.WMRepeat)
            stone_texture.setWrapV(Texture.WMRepeat)

            # 텍스처 적용
            self.floor.setTexture(stone_texture)
            self.floor.setTexScale(TextureStage.getDefault(), 20, 20)

            print("[Game] 돌 질감 텍스처 적용 완료 (20x20 타일링)")
        else:
            print("[Game] 텍스처 로드 실패 (textures/stone.png)")

        print("[Game] 씬 생성 완료 (돌 질감 바닥)")

    def _create_clouds(self):
        """하늘에 구름 생성"""
        self.clouds = []

        # 구름 텍스처 로드
        cloud_texture = self.loader.loadTexture("textures/cloud.png")

        if cloud_texture:
            # 여러 개의 구름 생성
            cloud_positions = [
                (-50, -80, 40, 15),
                (30, -90, 50, 18),
                (70, -70, 35, 12),
                (-30, -60, 45, 20),
                (60, -85, 55, 16),
                (0, -100, 38, 14),
                (-70, -75, 48, 17),
                (40, -65, 42, 13),
            ]

            for x, y, z, scale in cloud_positions:
                # CardMaker로 구름 평면 생성
                cm = CardMaker(f'cloud_{len(self.clouds)}')
                cm.setFrame(-scale, scale, -scale * 0.6, scale * 0.6)
                cloud = self.render.attachNewNode(cm.generate())

                # 위치 설정
                cloud.setPos(x, y, z)

                # 항상 카메라를 향하도록 (Billboarding)
                cloud.setBillboardPointEye()

                # 투명도 설정
                cloud.setTransparency(TransparencyAttrib.MAlpha)

                # 텍스처 적용
                cloud.setTexture(cloud_texture)

                self.clouds.append({
                    'node': cloud,
                    'speed': 0.5 + (len(self.clouds) * 0.1),  # 각기 다른 속도
                    'original_y': y
                })

            print(f"[Game] 구름 {len(self.clouds)}개 생성 완료")
        else:
            print("[Game] 구름 텍스처 로드 실패 (textures/cloud.png)")

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

    def _create_ammo_ui(self):
        """총알 UI 생성"""
        self.ammo_text = OnscreenText(
            text="",
            pos=(0, -0.85),
            scale=0.1,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )

        print("[Game] Ammo UI created")

    def _update_task(self, task):
        """메인 게임 루프"""
        dt = globalClock.getDt()

        if not self.controls.is_paused():
            self.player.update(dt)
            self.controls.update()
            self._update_clouds(dt)

        # 총알 UI 업데이트
        self._update_ammo_ui()

        return Task.cont

    def _update_clouds(self, dt):
        """구름 움직임 업데이트"""
        for cloud in self.clouds:
            # 구름을 천천히 이동
            cloud['node'].setY(cloud['node'].getY() + cloud['speed'] * dt)

            # 너무 멀어지면 반대편으로 이동
            if cloud['node'].getY() > 50:
                cloud['node'].setY(cloud['original_y'])

    def _update_ammo_ui(self):
        """총알 UI 업데이트"""
        current_ammo = self.player.gun_current_ammo
        magazine_size = self.player.gun_magazine_size
        total_ammo = self.player.gun_total_ammo

        self.ammo_text.setText(f"{current_ammo} / {magazine_size}  ({total_ammo})")

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

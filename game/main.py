from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import DirectFrame, DGG
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
from game.chat import ChatSystem
from game.target import TargetSystem
from game.sound import SoundManager
from game.obstacle import ObstacleSystem
from game.daynight import DayNightCycle
from game.enemy import EnemySystem
from game.resources import ResourceSystem


class ArenaPulseGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # 창 설정 (Full HD 1920x1080)
        self._setup_window()

        # 데이터베이스 초기화
        self.db = Database()

        # 사운드 매니저 초기화
        self.sound = SoundManager(self)

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

        # 총기 이미지 UI 생성
        self._create_gun_ui()

        # 채팅 시스템 생성
        self.chat = ChatSystem(self)

        # 표적 시스템 생성
        self.targets = TargetSystem(self)

        # 장애물 시스템 생성
        self.obstacles = ObstacleSystem(self)

        # 밤낮 시스템 생성
        self.daynight = DayNightCycle(self)

        # 적 시스템 생성
        self.enemies = EnemySystem(self)

        # 리소스 시스템 생성
        self.resources = ResourceSystem(self)

        # 체력과 방어력 UI 생성
        self._create_stats_ui()

        # 스코어 UI 생성
        self._create_score_ui()

        # 킬 피드 UI 생성
        self._create_kill_feed_ui()

        # 데미지 인디케이터 생성
        self._create_damage_indicator()

        # 웨이브 알림 생성
        self._create_wave_notification()

        # 인벤토리 UI 생성
        self._create_inventory_ui()

        # 게임 오버 화면 생성
        self._create_game_over_screen()

        # 게임 상태
        self.game_over = False

        # 메인 업데이트 태스크
        self.taskMgr.add(self._update_task, "UpdateTask")

        print("[Game] ArenaPulse game started! (DOOM style FPS)")
        print("[Game] WASD: Move | Mouse: Aim | L-Click: Shoot | R-Click: Zoom | Space: Jump | Shift: Sprint | Ctrl: Crouch | R: Reload | E: Gather | ESC: Pause")
        print("[Game] Chat Commands: /inv (inventory), /craft [item], /help")

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
        self.ambient_light = AmbientLight("ambient_light")
        self.ambient_light.setColor(Vec4(0.5, 0.5, 0.5, 1))
        self.ambient_light_np = self.render.attachNewNode(self.ambient_light)
        self.render.setLight(self.ambient_light_np)

        # 방향광 (Directional Light)
        self.directional_light = DirectionalLight("directional_light")
        self.directional_light.setColor(Vec4(0.8, 0.8, 0.8, 1))
        self.directional_light_np = self.render.attachNewNode(self.directional_light)
        self.directional_light_np.setHpr(45, -45, 0)
        self.render.setLight(self.directional_light_np)

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
        try:
            stone_texture = self.loader.loadTexture("textures/stone.png")
        except:
            stone_texture = None

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
        try:
            cloud_texture = self.loader.loadTexture("textures/cloud.png")
        except:
            cloud_texture = None

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
            mayChange=True  # 반동 효과를 위해 위치 변경 가능
        )

        # 조준선 반동 오프셋
        self.crosshair_offset = [0.0, 0.0]  # [x, y]
        self.crosshair_recoil_recovery = 8.0  # 반동 복구 속도

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

        # 게임 오버 상태가 아니면 업데이트 진행
        if not self.game_over:
            if not self.controls.is_paused() and not self.chat.is_open():
                self.player.update(dt)
                self.controls.update()
                self._update_clouds(dt)

                # 바운드 체크
                if self._check_bounds():
                    self.show_game_over()

            # 표적 시스템 업데이트
            self.targets.update(dt)

            # 적 시스템 업데이트
            self.enemies.update(dt)

            # 리소스 시스템 업데이트
            self.resources.update(dt)

            # 밤낮 시스템 업데이트 (일시정지 중이 아닐 때만)
            if not self.controls.is_paused():
                self.daynight.update(dt)

            # 총알 UI 업데이트
            self._update_ammo_ui()

            # 인벤토리 UI 업데이트
            self._update_inventory_ui()

            # 체력과 방어력 UI 업데이트
            self._update_stats_ui()

            # 조준선 반동 복구
            self._update_crosshair_recoil(dt)

            # 킬 피드 업데이트
            self.update_kill_feed(dt)

            # 데미지 인디케이터 업데이트
            self.update_damage_indicator(dt)

            # 웨이브 알림 업데이트
            self.update_wave_notification(dt)

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
        """총알 UI 업데이트 - 현재 무기 정보 표시"""
        weapon = self.player.current_weapon

        # 내구도 색상 (낮을수록 빨간색)
        dur_pct = weapon.get_durability_percentage()
        if dur_pct > 60:
            dur_color = "(좋음)"
        elif dur_pct > 30:
            dur_color = "(주의)"
        else:
            dur_color = "(위험)"

        # 무기 고장 상태
        broken_text = " [BROKEN]" if weapon.broken else ""

        self.ammo_text.setText(
            f"{weapon.name} [{weapon.get_fire_mode_name()}]{broken_text}\n"
            f"{weapon.current_ammo} / {weapon.magazine_size}  ({weapon.total_ammo})\n"
            f"내구도: {dur_pct}% {dur_color}"
        )

    def _update_stats_ui(self):
        """체력과 방어력 UI 업데이트"""
        self.health_text.setText(f"HP: {self.player.health}/{self.player.max_health}")
        self.defense_text.setText(f"DEF: {self.player.defense}/{self.player.max_defense}")

        # 스태미나 UI 업데이트
        stamina_value = int(self.player.stamina)
        self.stamina_text.setText(f"STA: {stamina_value}/{self.player.max_stamina}")

    def _update_crosshair_recoil(self, dt):
        """조준선 반동 복구"""
        # 오프셋 감소 (복구)
        if self.crosshair_offset[0] != 0 or self.crosshair_offset[1] != 0:
            recovery_amount = self.crosshair_recoil_recovery * dt

            # X 오프셋 복구
            if abs(self.crosshair_offset[0]) < recovery_amount:
                self.crosshair_offset[0] = 0
            elif self.crosshair_offset[0] > 0:
                self.crosshair_offset[0] -= recovery_amount
            else:
                self.crosshair_offset[0] += recovery_amount

            # Y 오프셋 복구
            if abs(self.crosshair_offset[1]) < recovery_amount:
                self.crosshair_offset[1] = 0
            elif self.crosshair_offset[1] > 0:
                self.crosshair_offset[1] -= recovery_amount
            else:
                self.crosshair_offset[1] += recovery_amount

            # 조준선 위치 업데이트
            self.crosshair.setPos(self.crosshair_offset[0], self.crosshair_offset[1])

    def _create_gun_ui(self):
        """총기 이미지 UI 생성"""
        try:
            # 기본 총기 이미지
            self.gun_image = OnscreenImage(
                image='textures/basicGun.png',
                pos=(0.7, 0, -0.6),
                scale=(0.5, 1, 0.3)
            )
            self.gun_image.setTransparency(TransparencyAttrib.MAlpha)
        except:
            self.gun_image = None
            print("[Game] 텍스처 로드 실패 (textures/basicGun.png)")

        try:
            # 줌 상태 총기 이미지 (숨김 상태로 시작)
            self.gun_zoom_image = OnscreenImage(
                image='textures/basicGun2.png',
                pos=(0, 0, -0.4),
                scale=(0.8, 1, 0.4)
            )
            self.gun_zoom_image.setTransparency(TransparencyAttrib.MAlpha)
            self.gun_zoom_image.hide()
        except:
            self.gun_zoom_image = None
            print("[Game] 텍스처 로드 실패 (textures/basicGun2.png)")

        print("[Game] Gun UI created")

    def _create_stats_ui(self):
        """체력과 방어력 UI 생성"""
        self.health_text = OnscreenText(
            text="HP: 100",
            pos=(-0.85, -0.85),
            scale=0.08,
            fg=(1, 0.3, 0.3, 1),
            align=TextNode.ALeft,
            mayChange=True
        )

        self.defense_text = OnscreenText(
            text="DEF: 100",
            pos=(-0.85, -0.92),
            scale=0.08,
            fg=(0.3, 0.6, 1, 1),
            align=TextNode.ALeft,
            mayChange=True
        )

        # 스태미나 UI 추가
        self.stamina_text = OnscreenText(
            text="STA: 100",
            pos=(-0.85, -0.99),
            scale=0.08,
            fg=(0.3, 1, 0.5, 1),
            align=TextNode.ALeft,
            mayChange=True
        )

        print("[Game] Stats UI created")

    def _create_inventory_ui(self):
        """인벤토리 UI 생성"""
        self.wood_text = OnscreenText(
            text="Wood: 0",
            pos=(-0.85, 0.85),
            scale=0.06,
            fg=(0.6, 0.4, 0.2, 1),
            align=TextNode.ALeft,
            mayChange=True
        )

        self.stone_text = OnscreenText(
            text="Stone: 0",
            pos=(-0.85, 0.80),
            scale=0.06,
            fg=(0.5, 0.5, 0.5, 1),
            align=TextNode.ALeft,
            mayChange=True
        )

        print("[Game] Inventory UI created")

    def _update_inventory_ui(self):
        """인벤토리 UI 업데이트"""
        wood_count = self.player.get_resource_count('wood')
        stone_count = self.player.get_resource_count('stone')
        self.wood_text.setText(f"Wood: {wood_count}")
        self.stone_text.setText(f"Stone: {stone_count}")

    def _create_game_over_screen(self):
        """게임 오버 화면 생성"""
        from direct.gui.DirectGui import DirectFrame, DirectButton, DGG

        # 게임 오버 프레임 (초기에는 숨김)
        self.game_over_frame = DirectFrame(
            pos=(0, 0, 0),
            frameSize=(-0.5, 0.5, -0.4, 0.4),
            frameColor=(0.1, 0.1, 0.1, 0.9),
            state=DGG.NORMAL
        )
        self.game_over_frame.hide()

        # 게임 오버 텍스트
        self.game_over_text = OnscreenText(
            text="GAME OVER",
            pos=(0, 0.2),
            scale=0.15,
            fg=(1, 0.2, 0.2, 1),
            align=TextNode.ACenter,
            mayChange=False
        )
        self.game_over_text.hide()

        # 재시작 버튼
        self.restart_button = DirectButton(
            parent=self.game_over_frame,
            pos=(0, 0, 0.05),
            scale=0.1,
            text="RESTART",
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.6, 0.2, 1),
            frameSize=(-2, 2, -0.5, 0.5),
            command=self._restart_game
        )

        # 종료 버튼
        self.quit_button = DirectButton(
            parent=self.game_over_frame,
            pos=(0, 0, -0.15),
            scale=0.1,
            text="QUIT",
            text_fg=(1, 1, 1, 1),
            frameColor=(0.6, 0.2, 0.2, 1),
            frameSize=(-2, 2, -0.5, 0.5),
            command=self._exit_game
        )

        print("[Game] Game Over screen created")

    def show_game_over(self):
        """게임 오버 화면 표시"""
        self.game_over = True
        self.game_over_frame.show()
        self.game_over_text.show()

        # 마우스 커서 표시
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(props)

        print("[Game] Game Over!")

    def _restart_game(self):
        """게임 재시작"""
        print("[Game] Restarting game...")

        # 게임 오버 상태 해제
        self.game_over = False
        self.game_over_frame.hide()
        self.game_over_text.hide()

        # 플레이어 상태 초기화
        self.player.node.setPos(0, 0, 0)
        self.player.health = self.player.max_health
        self.player.defense = self.player.max_defense
        self.player.gun_current_ammo = self.player.gun_magazine_size
        self.player.gun_total_ammo = 300
        self.player.heading = 0
        self.player.pitch = 10
        self.player.node.setH(0)
        self.player.camera_node.setP(10)
        self.player.velocity_z = 0.0

        # 카메라 리셋
        lens = self.camLens
        lens.setFov(60)  # 기본 FOV로 리셋
        self.update_gun_ui(False)

        # 표적 시스템 리셋
        self.targets.hide_targets()

        # 적 시스템 리셋
        for enemy in self.enemies.enemies[:]:
            enemy.cleanup()
        self.enemies.enemies.clear()

        # 마우스 다시 숨기고 중앙으로
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)
        self.win.requestProperties(props)
        center_x = self.win.getXSize() // 2
        center_y = self.win.getYSize() // 2
        self.win.movePointer(0, center_x, center_y)

        print("[Game] Game restarted!")

    def _create_score_ui(self):
        """스코어 및 웨이브 UI 생성"""
        # 스코어 텍스트
        self.score_text = OnscreenText(
            text="SCORE: 0",
            pos=(0.85, -0.85),
            scale=0.08,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
            mayChange=True
        )

        # 킬 카운트 텍스트
        self.kill_text = OnscreenText(
            text="KILLS: 0",
            pos=(0.85, -0.92),
            scale=0.08,
            fg=(1, 0.6, 0.2, 1),
            align=TextNode.ARight,
            mayChange=True
        )

        # 웨이브 텍스트
        self.wave_text = OnscreenText(
            text="WAVE: 1",
            pos=(0.85, -0.99),
            scale=0.08,
            fg=(0.5, 0.8, 1, 1),
            align=TextNode.ARight,
            mayChange=True
        )

        print("[Game] Score UI created")

    def update_score_ui(self):
        """스코어 UI 업데이트"""
        stats = self.enemies.get_stats()
        self.score_text.setText(f"SCORE: {stats['score']}")
        self.kill_text.setText(f"KILLS: {stats['kills']}")
        self.wave_text.setText(f"WAVE: {stats['wave']}")

    def _create_kill_feed_ui(self):
        """킬 피드 UI 생성"""
        self.kill_feed_entries = []
        self.max_kill_feed_entries = 5
        self.kill_feed_duration = 3.0  # 3초 후 제거

        print("[Game] Kill Feed UI created")

    def add_kill_feed(self, enemy_type, score):
        """킬 피드에 추가"""
        # 적 타입별 색상
        colors = {
            'melee': (0.9, 0.2, 0.2, 1),    # 빨간색
            'ranged': (0.8, 0.2, 0.8, 1),   # 보라색
            'sprinter': (1.0, 0.8, 0.0, 1),  # 노란색
            'tank': (0.3, 0.3, 0.3, 1),     # 검은색
            'bomber': (1.0, 0.5, 0.0, 1)    # 주황색
        }

        color = colors.get(enemy_type, (1, 1, 1, 1))

        # 킬 메시지 생성
        entry = OnscreenText(
            text=f"Killed {enemy_type.upper()} (+{score})",
            pos=(0.5, 0.3 - len(self.kill_feed_entries) * 0.05),
            scale=0.05,
            fg=color,
            align=TextNode.ACenter,
            mayChange=True
        )

        self.kill_feed_entries.append({
            'node': entry,
            'time': 0.0,
            'base_color': color
        })

        # 최대 개수 초과시 가장 오래된 것 제거
        if len(self.kill_feed_entries) > self.max_kill_feed_entries:
            oldest = self.kill_feed_entries.pop(0)
            oldest['node'].destroy()

    def update_kill_feed(self, dt):
        """킬 피드 업데이트"""
        for entry in self.kill_feed_entries[:]:
            entry['time'] += dt

            # 시간 초과시 제거
            if entry['time'] >= self.kill_feed_duration:
                entry['node'].destroy()
                self.kill_feed_entries.remove(entry)
            else:
                # 페이드 아웃 효과
                alpha = 1.0 - (entry['time'] / self.kill_feed_duration)
                base_color = entry['base_color']
                entry['node'].setFg((
                    base_color[0],
                    base_color[1],
                    base_color[2],
                    alpha
                ))

    def _create_damage_indicator(self):
        """데미지 인디케이터 생성 (빨간 화면 효과)"""
        self.damage_frame = DirectFrame(
            frameSize=(-1, 1, -1, 1),
            frameColor=(1, 0, 0, 0),
            state=DGG.NORMAL
        )
        self.damage_frame.hide()

        self.damage_alpha = 0.0
        self.damage_recovery_speed = 3.0

        print("[Game] Damage Indicator created")

    def show_damage_indicator(self):
        """데미지 인디케이터 표시"""
        self.damage_alpha = 0.4  # 최대 투명도
        self.damage_frame['frameColor'] = (1, 0, 0, self.damage_alpha)
        self.damage_frame.show()

    def update_damage_indicator(self, dt):
        """데미지 인디케이터 업데이트 (페이드 아웃)"""
        if self.damage_alpha > 0:
            self.damage_alpha -= self.damage_recovery_speed * dt
            if self.damage_alpha < 0:
                self.damage_alpha = 0
                self.damage_frame.hide()
            else:
                self.damage_frame['frameColor'] = (1, 0, 0, self.damage_alpha)

    def _create_wave_notification(self):
        """웨이브 알림 UI 생성"""
        self.wave_notification_text = OnscreenText(
            text="",
            pos=(0, 0.2),
            scale=0.15,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        self.wave_notification_text.hide()

        self.wave_notification_alpha = 0.0
        self.wave_notification_timer = 0.0
        self.wave_notification_duration = 3.0

        print("[Game] Wave Notification created")

    def show_wave_notification(self, wave_num):
        """웨이브 알림 표시"""
        self.wave_notification_text.setText(f"WAVE {wave_num}")
        self.wave_notification_text['fg'] = (1, 0.8, 0.2, 1)  # 금색
        self.wave_notification_text.show()

        self.wave_notification_alpha = 1.0
        self.wave_notification_timer = 0.0

        print(f"[Game] 웨이브 {wave_num} 알림 표시")

    def update_wave_notification(self, dt):
        """웨이브 알림 업데이트 (페이드 아웃 후 이동)"""
        if self.wave_notification_alpha > 0:
            self.wave_notification_timer += dt

            # 1초간 표시 후 페이드 아웃
            if self.wave_notification_timer >= 1.0:
                self.wave_notification_alpha -= 2.0 * dt

                if self.wave_notification_alpha <= 0:
                    self.wave_notification_alpha = 0
                    self.wave_notification_text.hide()
                else:
                    # 페이드 아웃
                    self.wave_notification_text['fg'] = (
                        1, 0.8, 0.2,
                        self.wave_notification_alpha
                    )

            # 위로 이동
            current_pos = self.wave_notification_text.getPos()
            self.wave_notification_text.setPos(current_pos.x, current_pos.y + 0.05 * dt)

    def _check_bounds(self):
        """플레이어가 바운드를 벗어났는지 체크"""
        pos = self.player.node.getPos()
        x, y = pos.x, pos.y

        # 바닥 범위는 -100~100
        if x < -100 or x > 100 or y < -100 or y > 100:
            return True
        return False

    def update_gun_ui(self, is_zoomed):
        """줌 상태에 따른 총기 이미지 변경"""
        if self.gun_image and self.gun_zoom_image:
            if is_zoomed:
                self.gun_image.hide()
                self.gun_zoom_image.show()
            else:
                self.gun_image.show()
                self.gun_zoom_image.hide()

    def update_weapon_ui(self):
        """무기 전환 시 UI 업데이트"""
        # 현재 무기의 탄약 정보 즉시 업데이트
        weapon = self.player.current_weapon
        self.ammo_text.setText(
            f"{weapon.name}\n{weapon.current_ammo} / {weapon.magazine_size}  ({weapon.total_ammo})"
        )

    def _exit_game(self):
        """게임 종료"""
        print("[Game] 게임 종료 중...")
        self.player.cleanup()
        self.controls.cleanup()
        self.chat.cleanup()
        self.targets.cleanup()
        self.obstacles.cleanup()
        self.daynight.cleanup()
        self.enemies.cleanup()
        self.resources.cleanup()
        self.sound.cleanup()
        self.db.close()
        sys.exit()


def main():
    game = ArenaPulseGame()
    game.run()


if __name__ == "__main__":
    main()

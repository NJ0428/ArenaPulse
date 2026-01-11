from panda3d.core import Vec4, AmbientLight, DirectionalLight, Point3
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib
import math


class DayNightCycle:
    """24분이 1게임 내 하루인 밤낮 시스템"""

    def __init__(self, game):
        self.game = game

        # 시간 설정 (24분 = 1게임 내 하루)
        self.real_seconds_per_game_day = 24 * 60  # 1440초 = 24분
        self.game_seconds_per_real_second = 24 * 60 / (24 * 60)  # 1초당 1게임 내 분

        # 현재 게임 내 시간 (0~1440분, 0 = 자정, 720 = 정오)
        self.game_time_minutes = 540  # 9:00 AM부터 시작 (아침)

        # 조명 참조
        self.ambient_light = None
        self.directional_light = None
        self.ambient_light_np = None
        self.directional_light_np = None
        self._find_lights()

        # 시간 UI
        self.time_text = None
        self._create_time_ui()

        # 태양/달 노드 (조명 방향을 나타내는 시각적 요소)
        self.sun_node = None
        self.moon_node = None
        self._create_celestial_bodies()

        print("[DayNightCycle] 밤낮 시스템 초기화 완료 (24분 = 1게임 내 하루)")

    def _find_lights(self):
        """메인 게임에서 조명 참조 가져오기"""
        # main.py에서 설정된 조명 참조
        self.ambient_light_np = self.game.ambient_light_np
        self.ambient_light = self.game.ambient_light
        self.directional_light_np = self.game.directional_light_np
        self.directional_light = self.game.directional_light

    def _create_time_ui(self):
        """시간 텍스트 UI 생성"""
        self.time_text = OnscreenText(
            text="06:00",
            pos=(0.85, 0.9),
            scale=0.08,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            mayChange=True
        )

        # 시간 아이콘 (텍스처가 있을 때만 생성)
        self.time_icon = None
        try:
            self.time_icon = OnscreenImage(
                image='textures/sun.png',
                pos=(0.92, 0, 0.9),
                scale=(0.05, 1, 0.05)
            )
            self.time_icon.setTransparency(TransparencyAttrib.MAlpha)
        except:
            # 텍스처 없으면 아이콘 없이 텍스트만 표시
            pass

        print("[DayNightCycle] 시간 UI 생성 완료")

    def _create_celestial_bodies(self):
        """태양과 달 생성 (시각적 표현)"""
        # 태양 (밝은 노란색 구)
        from panda3d.core import CardMaker
        cm = CardMaker('sun')
        cm.setFrame(-5, 5, -5, 5)
        self.sun_node = self.game.render.attachNewNode(cm.generate())
        self.sun_node.setBillboardPointEye()

        # 태양 색상과 텍스처
        try:
            texture = self.game.loader.loadTexture("textures/sun.png")
            self.sun_node.setTexture(texture)
        except:
            self.sun_node.setColor(1.0, 0.9, 0.3, 1.0)  # 밝은 노란색

        self.sun_node.setTransparency(TransparencyAttrib.MAlpha)

        # 달 (흰색 구)
        cm = CardMaker('moon')
        cm.setFrame(-3, 3, -3, 3)
        self.moon_node = self.game.render.attachNewNode(cm.generate())
        self.moon_node.setBillboardPointEye()

        # 달 색상과 텍스처
        try:
            texture = self.game.loader.loadTexture("textures/moon.png")
            self.moon_node.setTexture(texture)
        except:
            self.moon_node.setColor(0.8, 0.8, 0.9, 1.0)  # 흰빛 회색

        self.moon_node.setTransparency(TransparencyAttrib.MAlpha)

        print("[DayNightCycle] 태양과 달 생성 완료")

    def update(self, dt):
        """매 프레임 업데이트"""
        # 실제 시간 경과만큼 게임 내 시간 증가
        # 24분(1440초) = 1게임 내 하루(1440분)
        # 실제 1초 = 게임 내 1분
        self.game_time_minutes += dt

        # 1440분(24시간)이 지나면 0으로 리셋
        if self.game_time_minutes >= 1440:
            self.game_time_minutes = 0

        # 조명과 배경색 업데이트
        self._update_lighting()

        # 태양/달 위치 업데이트
        self._update_celestial_positions()

        # UI 업데이트
        self._update_ui()

    def _get_day_progress(self):
        """하루 진행률 반환 (0.0 ~ 1.0, 0 = 자정, 0.5 = 정오)"""
        return self.game_time_minutes / 1440.0

    def _get_sun_intensity(self):
        """태양 강도 반환 (0.0 ~ 1.0)"""
        progress = self._get_day_progress()

        # 낮 시간: 6:00 (360분) ~ 18:00 (1080분)
        if 360 <= self.game_time_minutes <= 1080:
            # 정오(720분)에 최대 강도
            if self.game_time_minutes <= 720:
                # 새벽 6시 ~ 정오: 0 ~ 1
                return (self.game_time_minutes - 360) / 360.0
            else:
                # 정오 ~ 오후 6시: 1 ~ 0
                return 1.0 - (self.game_time_minutes - 720) / 360.0
        else:
            # 밤: 0 강도
            return 0.0

    def _update_lighting(self):
        """조명 업데이트 (시간에 따른 밝기 변화)"""
        sun_intensity = self._get_sun_intensity()

        # 주변광 (Ambient Light) - 태양 강도에 따라 변화
        # 낮: 0.5, 밤: 0.1
        ambient_intensity = 0.1 + (sun_intensity * 0.4)
        if self.ambient_light:
            self.ambient_light.setColor(Vec4(ambient_intensity, ambient_intensity, ambient_intensity, 1))

        # 방향광 (Directional Light) - 태양 강도와 방향에 따라 변화
        # 낮: 0.8, 밤: 0.05
        directional_intensity = 0.05 + (sun_intensity * 0.75)

        # 조명 색상도 시간에 따라 변화
        # 새벽/해질녁: 붉은 기미, 정오: 흰색
        if 300 <= self.game_time_minutes <= 480:  # 새벽 5~8시
            daybreak_progress = (self.game_time_minutes - 300) / 180.0
            r = 1.0
            g = 0.5 + (daybreak_progress * 0.3)
            b = 0.3 + (daybreak_progress * 0.5)
        elif 960 <= self.game_time_minutes <= 1140:  # 오후 4~7시 (해질녁)
            sunset_progress = (self.game_time_minutes - 960) / 180.0
            r = 1.0
            g = 0.8 - (sunset_progress * 0.3)
            b = 0.8 - (sunset_progress * 0.5)
        else:
            r = g = b = 1.0

        if self.directional_light:
            self.directional_light.setColor(Vec4(r * directional_intensity, g * directional_intensity, b * directional_intensity, 1))

        # 배경색 (하늘색) 변화
        self._update_sky_color(sun_intensity)

    def _update_sky_color(self, sun_intensity):
        """하늘 색상 업데이트"""
        if sun_intensity > 0:
            # 낮: 하늘색 (0.5, 0.7, 0.9)
            self.game.setBackgroundColor(0.5 * sun_intensity + 0.05,
                                        0.7 * sun_intensity + 0.05,
                                        0.9 * sun_intensity + 0.05,
                                        1.0)
        else:
            # 밤: 어두운 남색 (0.05, 0.05, 0.1)
            self.game.setBackgroundColor(0.05, 0.05, 0.1, 1.0)

    def _update_celestial_positions(self):
        """태양과 달 위치 업데이트"""
        progress = self._get_day_progress()

        # 태양: 동쪽(6시)에서 떠서 서쪽(18시)으로 지는 궤적
        # 궤적은 반원 형태로, 높이가 정오에 최고점
        if 360 <= self.game_time_minutes <= 1080:  # 낮
            sun_progress = (self.game_time_minutes - 360) / 720.0  # 0 ~ 1
            angle = sun_progress * math.pi  # 0 ~ 180도

            # 반원 궤적: 반경 100
            radius = 100
            sun_x = radius * math.cos(angle)
            sun_y = radius * math.sin(angle) * 0.3  # 앞뒤로는 덜 움직임
            sun_z = radius * math.sin(angle)  # 높이

            self.sun_node.setPos(sun_x, sun_y, sun_z)
            self.sun_node.show()
        else:
            self.sun_node.hide()

        # 달: 정반대 궤적
        if self.game_time_minutes < 360 or self.game_time_minutes > 1080:  # 밤
            if self.game_time_minutes > 1080:
                moon_progress = (self.game_time_minutes - 1080) / 720.0
            else:
                moon_progress = (self.game_time_minutes + 360) / 720.0

            angle = moon_progress * math.pi

            radius = 100
            moon_x = -radius * math.cos(angle)
            moon_y = radius * math.sin(angle) * 0.3
            moon_z = radius * math.sin(angle)

            self.moon_node.setPos(moon_x, moon_y, moon_z)
            self.moon_node.show()
        else:
            self.moon_node.hide()

        # 조명 방향도 태양 위치에 따라 업데이트
        if self.directional_light_np and 360 <= self.game_time_minutes <= 1080:
            sun_progress = (self.game_time_minutes - 360) / 720.0
            angle = sun_progress * 180  # 0 ~ 180도
            self.directional_light_np.setHpr(angle, -45, 0)

    def _update_ui(self):
        """시간 UI 업데이트"""
        # 게임 내 시간을 HH:MM 형식으로 변환
        hours = int(self.game_time_minutes // 60)
        minutes = int(self.game_time_minutes % 60)

        time_str = f"{hours:02d}:{minutes:02d}"
        self.time_text.setText(f"{time_str}")

        # 시간 아이콘 변경 (낮/밤)
        if 360 <= self.game_time_minutes <= 1080:  # 낮
            # 태양 아이콘 표시
            self.time_text.setFg((1.0, 1.0, 0.8, 1.0))  # 밝은 노란색
        else:  # 밤
            # 달 아이콘 표시
            self.time_text.setFg((0.6, 0.7, 1.0, 1.0))  # 파란빛

    def cleanup(self):
        """정리"""
        if self.sun_node:
            self.sun_node.removeNode()
        if self.moon_node:
            self.moon_node.removeNode()

        print("[DayNightCycle] 밤낮 시스템 정리 완료")


# TextNode import 추가를 위한 코드
from panda3d.core import TextNode

from panda3d.core import Point3, Vec3, BitMask32, Texture, TransparencyAttrib, ColorAttrib
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, Func, Wait
import math
import random


class Player:
    def __init__(self, game):
        self.game = game
        self.walk_speed = 15.0
        self.run_speed = 25.0
        self.speed = self.walk_speed
        self.is_running = False
        self.eye_height = 2.5  # 눈 높이

        # 중력 관련
        self.gravity = -30.0  # 중력 가속도
        self.velocity_z = 0.0  # 수직 속도
        self.ground_level = 0.0  # 바닥 높이
        self.is_grounded = True  # 바닥에 있는지
        self.jump_force = 12.0  # 점프 힘

        # 회전 각도
        self.heading = 0  # 좌우 회전
        self.pitch = 10   # 상하 회전 (초기값: 약간 위쪽)

        # 이동 상태
        self.moving = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False
        }

        # 공격 상태
        self.can_attack = True

        # 총기 시스템
        self.gun_fire_rate = 0.15  # 발사 속도 (초)
        self.gun_damage = 25  # 데미지
        self.gun_bullet_speed = 100.0  # 탄속
        self.gun_spread = 2.0  # 정확도 (낮을수록 정확, 단위: 도)
        self.gun_recoil = 3.0  # 반동 (상하)
        self.gun_magazine_size = 30  # 탄창 크기
        self.gun_current_ammo = self.gun_magazine_size  # 현재 탄창
        self.gun_total_ammo = 300  # 전체 탄약
        self.gun_reload_time = 2.0  # 재장전 시간
        self.is_reloading = False  # 재장전 중

        # 줌 시스템
        self.is_zoomed = False  # 줌 상태
        self.zoom_fov_reduction = 0.5  # 줌 시 FOV 감소 비율
        self.gun_recoil_zoom_multiplier = 0.4  # 줌 시 반동 감소 비율 (40%만 적용)

        # 반동 시각효과
        self.recoil_pitch = 0.0  # 현재 반동 각도
        self.recoil_recovery = 10.0  # 반동 복구 속도

        # 플레이어 위치 (보이지 않는 노드)
        self._create_player_node()

        # 투사체 리스트
        self.projectiles = []

        # 재장전 텍스트 UI
        self.reload_text = None

    def _create_player_node(self):
        """플레이어 노드 생성 (1인칭이므로 보이지 않음)"""
        self.node = self.game.render.attachNewNode("player")
        self.node.setPos(0, 0, self.ground_level)

        # 카메라를 플레이어에 부착
        self.camera_node = self.node.attachNewNode("camera_pivot")
        self.camera_node.setZ(self.eye_height)
        self.camera_node.setP(self.pitch)  # 초기 시선 방향 적용

        print("[Player] 플레이어 생성 완료 (FPS 모드)")

    def setup_camera(self, camera):
        """카메라를 플레이어에 연결"""
        camera.reparentTo(self.camera_node)
        camera.setPos(0, 0, 0)
        camera.setHpr(0, 0, 0)

    def update(self, dt):
        """매 프레임 업데이트"""
        self._update_gravity(dt)
        self._update_movement(dt)
        self._update_projectiles(dt)
        self._update_recoil(dt)  # 반동 복구

    def _update_gravity(self, dt):
        """중력 적용"""
        current_z = self.node.getZ()

        # 공중에 있으면 중력 적용
        if current_z > self.ground_level or self.velocity_z > 0:
            self.velocity_z += self.gravity * dt
            new_z = current_z + self.velocity_z * dt

            # 바닥 충돌 체크
            if new_z <= self.ground_level:
                new_z = self.ground_level
                self.velocity_z = 0.0
                self.is_grounded = True
            else:
                self.is_grounded = False

            self.node.setZ(new_z)
        else:
            self.is_grounded = True
            self.velocity_z = 0.0

    def _update_movement(self, dt):
        """이동 업데이트 (바라보는 방향 기준)"""
        move_vec = Vec3(0, 0, 0)

        # 바라보는 방향 기준으로 이동
        heading_rad = math.radians(self.heading)
        forward = Vec3(-math.sin(heading_rad), math.cos(heading_rad), 0)
        right = Vec3(math.cos(heading_rad), math.sin(heading_rad), 0)

        if self.moving['forward']:
            move_vec += forward
        if self.moving['backward']:
            move_vec -= forward
        if self.moving['left']:
            move_vec -= right
        if self.moving['right']:
            move_vec += right

        if move_vec.length() > 0:
            move_vec.normalize()
            move_vec *= self.speed * dt

            new_pos = self.node.getPos() + move_vec
            self.node.setPos(new_pos)

    def rotate_heading(self, delta):
        """좌우 회전"""
        self.heading += delta
        # 360도 범위로 정규화
        self.heading = self.heading % 360
        self.node.setH(self.heading)

    def rotate_pitch(self, delta):
        """상하 회전 (카메라만)"""
        self.pitch += delta
        # -89도 ~ 89도로 제한
        self.pitch = max(-89, min(89, self.pitch))
        self.camera_node.setP(self.pitch)

    def jump(self):
        """점프"""
        if self.is_grounded:
            self.velocity_z = self.jump_force
            self.is_grounded = False

    def set_running(self, running):
        """달리기 상태 설정"""
        self.is_running = running
        self.speed = self.run_speed if running else self.walk_speed

    def ranged_attack(self):
        """Ranged attack (gun shooting)"""
        if not self.can_attack or self.is_reloading:
            return

        # 탄약 체크
        if self.gun_current_ammo <= 0:
            self._reload()
            return

        self.can_attack = False
        self.gun_current_ammo -= 1

        # 총알 생성 (카드 메이커로 평면 생성)
        from panda3d.core import CardMaker
        cm = CardMaker('bullet')
        cm.setFrame(-0.3, 0.3, -0.15, 0.15)  # 총알 크기
        bullet = self.game.render.attachNewNode(cm.generate())

        # 항상 카메라를 향하도록 (Billboarding)
        bullet.setBillboardPointEye()

        # 투명도 설정
        bullet.setTransparency(TransparencyAttrib.MAlpha)

        # 총알 텍스처 적용
        bullet_texture = self.game.loader.loadTexture("textures/bullet.png")
        if bullet_texture:
            bullet.setTexture(bullet_texture)
            print("[Player] 총알 텍스처 적용 완료")
        else:
            bullet.setColor(1.0, 0.8, 0.0, 1.0)  # 금색 (텍스처 없을 때)
            print("[Player] 총알 텍스처 로드 실패 - 기본 색상 사용")

        # 카메라(눈) 위치에서 발사
        start_pos = self.camera_node.getPos(self.game.render)
        bullet.setPos(start_pos)

        # 기본 발사 방향 (카메라가 바라보는 방향)
        heading_rad = math.radians(self.heading)
        pitch_rad = math.radians(self.pitch)

        base_direction = Vec3(
            -math.sin(heading_rad) * math.cos(pitch_rad),
            math.cos(heading_rad) * math.cos(pitch_rad),
            math.sin(pitch_rad)
        )
        base_direction.normalize()

        # 산탄(spread) 적용 - 정확도에 따른 랜덤 편차
        spread_rad = math.radians(self.gun_spread)
        spread_h = (random.random() - 0.5) * 2 * spread_rad  # 좌우 편차
        spread_v = (random.random() - 0.5) * 2 * spread_rad  # 상하 편차

        # 편차를 방향에 적용
        cos_h = math.cos(spread_h)
        sin_h = math.sin(spread_h)
        cos_v = math.cos(spread_v)
        sin_v = math.sin(spread_v)

        direction = Vec3(
            base_direction.x * cos_h - base_direction.y * sin_h,
            base_direction.x * sin_h + base_direction.y * cos_h,
            base_direction.z * cos_v + sin_v
        )
        direction.normalize()

        self.projectiles.append({
            'node': bullet,
            'direction': direction,
            'speed': self.gun_bullet_speed,
            'lifetime': 3.0,
            'damage': self.gun_damage
        })

        # 반동 적용
        self._apply_recoil()

        print(f"[Player] Shot! Ammo: {self.gun_current_ammo}/{self.gun_magazine_size}")

        # 발사 속도에 따른 쿨다운
        self.game.taskMgr.doMethodLater(
            self.gun_fire_rate,
            self._reset_attack,
            'reset_ranged_attack'
        )

    def toggle_zoom(self):
        """줌 토글"""
        self.is_zoomed = not self.is_zoomed

        # FOV 변경 (렌즈 객체 사용)
        lens = self.game.camLens
        if self.is_zoomed:
            # 줌 상태: FOV 감소
            lens.setFov(lens.getFov() * self.zoom_fov_reduction)
        else:
            # 일반 상태: FOV 복구
            lens.setFov(lens.getFov() / self.zoom_fov_reduction)

        # 총기 UI 업데이트
        self.game.update_gun_ui(self.is_zoomed)

        print(f"[Player] Zoom {'ON' if self.is_zoomed else 'OFF'}")

    def _reset_attack(self, task):
        """공격 쿨다운 리셋"""
        self.can_attack = True
        return None

    def _apply_recoil(self):
        """반동 적용"""
        # 줌 상태에서는 반동이 감소
        recoil_multiplier = self.gun_recoil_zoom_multiplier if self.is_zoomed else 1.0

        # 상하 반동
        recoil_amount = self.gun_recoil * recoil_multiplier * (0.5 + random.random() * 0.5)  # 50%~100% 랜덤
        self.recoil_pitch += recoil_amount

        # 카메라에 즉시 적용
        self.camera_node.setP(self.pitch + self.recoil_pitch)

    def _update_recoil(self, dt):
        """반동 복구"""
        if self.recoil_pitch > 0:
            # 반동 복구
            self.recoil_pitch -= self.recoil_recovery * dt
            if self.recoil_pitch < 0:
                self.recoil_pitch = 0

            # 카메라에 적용
            self.camera_node.setP(self.pitch + self.recoil_pitch)

    def _reload(self):
        """재장전"""
        if self.is_reloading or self.gun_total_ammo <= 0:
            return

        if self.gun_current_ammo >= self.gun_magazine_size:
            return  # 이미 탄창이 가득 찼음

        self.is_reloading = True
        self.can_attack = False

        print(f"[Player] Reloading... ({self.gun_reload_time}s)")

        # 재장전 완료 후 탄약 채우기
        self.game.taskMgr.doMethodLater(
            self.gun_reload_time,
            self._finish_reload,
            'reload_weapon'
        )

    def _finish_reload(self, task):
        """재장전 완료"""
        ammo_needed = self.gun_magazine_size - self.gun_current_ammo
        ammo_to_add = min(ammo_needed, self.gun_total_ammo)

        self.gun_current_ammo += ammo_to_add
        self.gun_total_ammo -= ammo_to_add

        self.is_reloading = False
        self.can_attack = True

        print(f"[Player] Reloaded! Ammo: {self.gun_current_ammo}/{self.gun_magazine_size}")

        return None

    def _update_projectiles(self, dt):
        """투사체 업데이트"""
        for proj in self.projectiles[:]:
            # 이동
            proj['node'].setPos(
                proj['node'].getPos() + proj['direction'] * proj['speed'] * dt
            )

            # 수명 감소
            proj['lifetime'] -= dt

            # 수명 종료시 제거
            if proj['lifetime'] <= 0:
                proj['node'].removeNode()
                self.projectiles.remove(proj)

    def get_position(self):
        """플레이어 위치 반환"""
        return self.node.getPos()

    def cleanup(self):
        """정리"""
        for proj in self.projectiles:
            proj['node'].removeNode()
        self.projectiles.clear()
        self.node.removeNode()

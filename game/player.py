from panda3d.core import Point3, Vec3, BitMask32
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, Func, Wait
import math


class Player:
    def __init__(self, game):
        self.game = game
        self.walk_speed = 15.0
        self.run_speed = 25.0
        self.speed = self.walk_speed
        self.is_running = False
        self.eye_height = 1.7  # 눈 높이

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
        self.ranged_cooldown = 0.3
        self.melee_cooldown = 0.5

        # 플레이어 위치 (보이지 않는 노드)
        self._create_player_node()

        # 투사체 리스트
        self.projectiles = []

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
        """원거리 공격 (투사체 발사)"""
        if not self.can_attack:
            return

        self.can_attack = False

        # 투사체 생성
        projectile = self.game.loader.loadModel("models/box")
        projectile.reparentTo(self.game.render)
        projectile.setScale(0.2, 0.2, 0.2)
        projectile.setColor(1.0, 1.0, 0.0, 1.0)  # 노란색

        # 카메라(눈) 위치에서 발사
        start_pos = self.camera_node.getPos(self.game.render)
        projectile.setPos(start_pos)

        # 발사 방향 (카메라가 바라보는 방향)
        heading_rad = math.radians(self.heading)
        pitch_rad = math.radians(self.pitch)

        direction = Vec3(
            -math.sin(heading_rad) * math.cos(pitch_rad),
            math.cos(heading_rad) * math.cos(pitch_rad),
            math.sin(pitch_rad)
        )

        self.projectiles.append({
            'node': projectile,
            'direction': direction,
            'speed': 50.0,
            'lifetime': 3.0
        })

        print("[Player] 원거리 공격!")

        # 쿨다운 후 공격 가능
        self.game.taskMgr.doMethodLater(
            self.ranged_cooldown,
            self._reset_attack,
            'reset_attack'
        )

    def melee_attack(self):
        """근접 공격"""
        if not self.can_attack:
            return

        self.can_attack = False

        # 근접 공격 이펙트 (앞에 히트박스 표시)
        melee_hitbox = self.game.loader.loadModel("models/box")
        melee_hitbox.reparentTo(self.camera_node)
        melee_hitbox.setScale(0.5, 2.0, 0.5)
        melee_hitbox.setPos(0, 2.5, -0.3)
        melee_hitbox.setColor(1.0, 0.3, 0.3, 0.7)

        print("[Player] 근접 공격!")

        # 0.2초 후 히트박스 제거
        self.game.taskMgr.doMethodLater(
            0.2,
            lambda task: self._remove_melee_hitbox(melee_hitbox),
            'remove_melee'
        )

        # 쿨다운 후 공격 가능
        self.game.taskMgr.doMethodLater(
            self.melee_cooldown,
            self._reset_attack,
            'reset_attack'
        )

    def _remove_melee_hitbox(self, hitbox):
        """근접 공격 히트박스 제거"""
        hitbox.removeNode()
        return None

    def _reset_attack(self, task):
        """공격 쿨다운 리셋"""
        self.can_attack = True
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

from panda3d.core import (
    CardMaker, Vec4, TransparencyAttrib, Point3,
    CollisionNode, CollisionSphere, BitMask32, TextNode
)
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
import random
import time


class Target:
    """표적 클래스 - 총으로 맞추는 과녁"""

    def __init__(self, game, position, scale=3.0):
        self.game = game
        self.position = position  # Point3
        self.scale = scale
        self.is_hit = False
        self.hit_time = 0.0
        self.respawn_time = 2.0  # 맞은 후 다시 나타날 때까지의 시간

        # 중앙 반경 (히트 판정 범위)
        self.center_radius = 0.3  # 중앙에서 30% 범위 내면 히트로 판정

        # 표적 생성
        self._create_target()

        # 히트 메시지 (초기엔 숨김)
        self.hit_text = OnscreenText(
            text="HIT!",
            pos=(0, 0.1),
            scale=0.15,
            fg=(1, 0.3, 0.3, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        self.hit_text.hide()
        self.hit_message_show_time = 0.0
        self.hit_message_duration = 0.5  # 히트 메시지 표시 시간

        print(f"[Target] 표적 생성 위치: {position}")

    def _create_target(self):
        """표적 3D 모델 생성"""
        # CardMaker로 원형 표적 생성
        cm = CardMaker('target')
        cm.setFrame(-self.scale/2, self.scale/2, -self.scale/2, self.scale/2)

        self.node = self.game.render.attachNewNode(cm.generate())

        # 항상 카메라를 향하도록 (Billboarding)
        self.node.setBillboardPointEye()

        # 투명도 설정
        self.node.setTransparency(TransparencyAttrib.MAlpha)

        # 초기 색상 (초록색)
        self.node.setColor(0.2, 0.8, 0.2, 1.0)

        # 위치 설정
        self.node.setPos(self.position)

        # 충돌 감지를 위한 콜라이더 구 설정
        self._setup_collision()

    def _setup_collision(self):
        """충돌 감지 설정"""
        # 충돌 구 생성 (전체 표적 크기)
        collision_sphere = CollisionSphere(0, 0, 0, self.scale / 2)

        # 충돌 노드 생성
        collision_node = CollisionNode('target_collision')
        collision_node.addSolid(collision_sphere)

        # 충돌 마스크 설정 (총알과만 충돌)
        collision_node.setIntoCollideMask(BitMask32.bit(1))

        # 충돌 노드를 표적에 부착
        self.collision_node = self.node.attachNewNode(collision_node)
        self.collision_node.setPythonTag('target', self)

    def check_hit(self, hit_pos):
        """
        총알이 표적에 맞았는지 확인
        hit_pos: Point3 - 충돌 지점 (월드 좌표)
        """
        if self.is_hit:
            return False  # 이미 맞은 상태면 무시

        # 충돌 지점을 표적의 로컬 좌표로 변환
        local_hit_pos = self.node.getRelativePoint(self.game.render, hit_pos)

        # 중앙으로부터의 거리 계산
        distance_from_center = local_hit_pos.length()

        # 중앙 히트 판정
        is_center_hit = distance_from_center < (self.scale * self.center_radius)

        # 맞은 상태로 변경
        self.is_hit = True
        self.hit_time = time.time()

        # 색상 변경 (빨간색)
        self.node.setColor(0.9, 0.2, 0.2, 1.0)

        # 중앙 히트 메시지 표시
        if is_center_hit:
            self._show_hit_message()
            print("[Target] CENTER HIT!")
        else:
            print("[Target] Hit!")

        return True

    def _show_hit_message(self):
        """히트 메시지 표시"""
        self.hit_text.show()
        self.hit_message_show_time = time.time()

    def update(self, dt):
        """매 프레임 업데이트"""
        current_time = time.time()

        # 히트 메시지 숨기기 (시간 경과 후)
        if self.hit_text.isHidden() == False:
            if current_time - self.hit_message_show_time > self.hit_message_duration:
                self.hit_text.hide()

        # 리스폰 (맞은 후 일정 시간 뒤)
        if self.is_hit:
            if current_time - self.hit_time > self.respawn_time:
                self.respawn()

    def respawn(self):
        """표적 리스폰"""
        self.is_hit = False
        self.node.setColor(0.2, 0.8, 0.2, 1.0)  # 초록색으로 복구
        print("[Target] Target respawned")

    def cleanup(self):
        """정리"""
        if self.node:
            self.node.removeNode()
        if self.hit_text:
            self.hit_text.destroy()


class TargetSystem:
    """표적 시스템 관리자"""

    def __init__(self, game):
        self.game = game
        self.targets = []

        # 표적 생성
        self._create_targets()

        print(f"[TargetSystem] 표적 시스템 초기화 완료 (표적 수: {len(self.targets)})")

    def _create_targets(self):
        """여러 표적 생성"""
        # 표적 위치들 (랜덤하게 생성)
        target_positions = [
            Point3(0, 30, 5),
            Point3(15, 40, 8),
            Point3(-15, 35, 6),
            Point3(10, 50, 10),
            Point3(-10, 45, 7),
            Point3(20, 30, 4),
            Point3(-20, 40, 9),
        ]

        for pos in target_positions:
            target = Target(self.game, pos)
            self.targets.append(target)

    def check_bullet_collisions(self, bullet_pos):
        """
        모든 총알 위치에 대해 표적 충돌 체크
        bullet_pos: Point3 - 총알 위치
        """
        for target in self.targets:
            # 간단한 거리 체크로 충돌 판정
            distance = (bullet_pos - target.node.getPos()).length()

            if distance < target.scale / 2:
                # 충돌! 히트 체크
                hit = target.check_hit(bullet_pos)
                if hit:
                    return target  # 맞은 표적 반환

        return None

    def update(self, dt):
        """모든 표적 업데이트"""
        for target in self.targets:
            target.update(dt)

    def cleanup(self):
        """정리"""
        for target in self.targets:
            target.cleanup()
        self.targets.clear()

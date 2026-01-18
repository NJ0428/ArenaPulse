from panda3d.core import Point3, Vec3, BitMask32, TransparencyAttrib, CardMaker
from direct.task import Task
import random
import math


class ResourceNode:
    """리소스 노드 기본 클래스 (나무, 돌 등)"""
    def __init__(self, game, position, resource_type):
        self.game = game
        self.position = position
        self.resource_type = resource_type
        self.node = None
        self.health = 100  # 리소스 체력
        self.max_health = 100
        self.gather_amount = 10  # 채집 시 얻는 양
        self.gather_time = 1.0  # 채집 시간 (초)
        self.is_being_gathered = False

    def create_visual(self):
        """시각적 표현 생성 (하위 클래스에서 구현)"""
        pass

    def gather(self, amount=10):
        """채집 - 체력 감소"""
        self.health -= amount

        # 채집 효과
        self._create_gather_effect()

        if self.health <= 0:
            return self.gather_amount  # 채집 완료 시 리소스 반환
        return 0  # 아직 채집 중

    def _create_gather_effect(self):
        """채집 효과 (입자 등)"""
        pass

    def is_depleted(self):
        """리소스가 고갈되었는지 확인"""
        return self.health <= 0

    def cleanup(self):
        """정리"""
        if self.node:
            self.node.removeNode()


class Tree(ResourceNode):
    """나무 리소스"""
    def __init__(self, game, position):
        super().__init__(game, position, "wood")
        self.health = 150  # 나무는 더 튼튼
        self.max_health = 150
        self.gather_amount = 20  # 나무는 더 많이 줌
        self.create_visual()

    def create_visual(self):
        """나무 시각적 표현 생성"""
        # 나무 기둥 (원기둥 모양의 카드)
        trunk_cm = CardMaker('tree_trunk')
        trunk_height = 4.0
        trunk_width = 0.8
        trunk_cm.setFrame(-trunk_width/2, trunk_width/2, 0, trunk_height)

        self.node = self.game.render.attachNewNode(trunk_cm.generate())
        self.node.setPos(self.position)
        self.node.setZ(-0.1)  # 바닥에 딱 맞춤

        # 항상 카메라를 향하도록 (Billboarding)
        self.node.setBillboardPointEye()

        # 투명도 설정
        self.node.setTransparency(TransparencyAttrib.MAlpha)

        # 나무 색상 (갈색 트렁크)
        self.node.setColor(0.4, 0.3, 0.2, 1.0)

        # 나무 잎 (초록색 원)
        leaves_cm = CardMaker('tree_leaves')
        leaves_size = 2.5
        leaves_cm.setFrame(-leaves_size/2, leaves_size/2, -leaves_size/2, leaves_size/2)

        self.leaves_node = self.node.attachNewNode(leaves_cm.generate())
        self.leaves_node.setPos(0, 0, trunk_height + leaves_size/2)
        self.leaves_node.setTransparency(TransparencyAttrib.MAlpha)
        self.leaves_node.setColor(0.2, 0.6, 0.2, 0.9)

        # 충돌 박스 설정
        self.node.setTag('resource_type', 'wood')
        self.node.setTag('resource_node', str(id(self)))

        print(f"[Resource] 나무 생성 at {self.position}")

    def _create_gather_effect(self):
        """채집 효과 - 나무 조각"""
        effect_cm = CardMaker('wood_chip')
        effect_cm.setFrame(-0.2, 0.2, -0.2, 0.2)

        for _ in range(3):
            chip = self.game.render.attachNewNode(effect_cm.generate())
            chip.setPos(self.position)
            chip.setZ(random.uniform(1.0, 3.0))

            # 랜덤 방향으로 튀어나감
            offset_x = random.uniform(-2, 2)
            offset_y = random.uniform(-2, 2)
            offset_z = random.uniform(2, 4)

            chip.setTransparency(TransparencyAttrib.MAlpha)
            chip.setColor(0.5, 0.4, 0.3, 1.0)

            # 애니메이션 (나중에 구현)
            self.game.taskMgr.doMethodLater(
                0.5,
                lambda task: chip.removeNode(),
                f'remove_wood_chip_{id(chip)}'
            )


class Rock(ResourceNode):
    """돌 리소스"""
    def __init__(self, game, position):
        super().__init__(game, position, "stone")
        self.health = 200  # 돌은 가장 튼튼
        self.max_health = 200
        self.gather_amount = 15
        self.create_visual()

    def create_visual(self):
        """돌 시각적 표현 생성"""
        # 돌 (회색 타원)
        rock_cm = CardMaker('rock')
        rock_width = 1.5
        rock_height = 1.2
        rock_cm.setFrame(-rock_width/2, rock_width/2, -rock_height/2, rock_height/2)

        self.node = self.game.render.attachNewNode(rock_cm.generate())
        self.node.setPos(self.position)
        self.node.setZ(rock_height/2 - 0.1)  # 바닥에 딱 맞춤

        # 항상 카메라를 향하도록 (Billboarding)
        self.node.setBillboardPointEye()

        # 투명도 설정
        self.node.setTransparency(TransparencyAttrib.MAlpha)

        # 돌 색상 (회색)
        gray_shade = random.uniform(0.4, 0.6)
        self.node.setColor(gray_shade, gray_shade, gray_shade, 1.0)

        # 충돌 박스 설정
        self.node.setTag('resource_type', 'stone')
        self.node.setTag('resource_node', str(id(self)))

        print(f"[Resource] 돌 생성 at {self.position}")

    def _create_gather_effect(self):
        """채집 효과 - 돌가루"""
        effect_cm = CardMaker('stone_dust')
        effect_cm.setFrame(-0.15, 0.15, -0.15, 0.15)

        for _ in range(5):
            dust = self.game.render.attachNewNode(effect_cm.generate())
            dust.setPos(self.position)
            dust.setZ(random.uniform(0.5, 1.5))

            # 랜덤 방향으로 퍼짐
            dust.setTransparency(TransparencyAttrib.MAlpha)
            dust.setColor(0.6, 0.6, 0.6, 0.7)

            # 애니메이션
            self.game.taskMgr.doMethodLater(
                0.3,
                lambda task: dust.removeNode(),
                f'remove_stone_dust_{id(dust)}'
            )


class ResourceSystem:
    """리소스 시스템 관리자"""
    def __init__(self, game):
        self.game = game
        self.resources = []
        self.gather_range = 3.0  # 채집 가능 거리
        self.gather_cooldown = 0.0
        self.gather_cooldown_time = 0.5  # 채집 쿨다운

        # 초기 리소스 생성
        self._spawn_initial_resources()

    def _spawn_initial_resources(self):
        """초기 리소스 스폰"""
        # 맵 크기: -100 ~ 100 (200x200)

        # 나무 스폰 (30개)
        for _ in range(30):
            x = random.uniform(-80, 80)
            y = random.uniform(-80, 80)
            pos = Point3(x, y, 0)

            # 다른 리소스와 너무 가까우면 스킵
            if self._is_too_close_to_other_resources(pos, min_distance=5.0):
                continue

            tree = Tree(self.game, pos)
            self.resources.append(tree)

        # 돌 스폰 (20개)
        for _ in range(20):
            x = random.uniform(-80, 80)
            y = random.uniform(-80, 80)
            pos = Point3(x, y, 0)

            # 다른 리소스와 너무 가까우면 스킵
            if self._is_too_close_to_other_resources(pos, min_distance=5.0):
                continue

            rock = Rock(self.game, pos)
            self.resources.append(rock)

        print(f"[Resource] 초기 리소스 생성 완료: 나무 {sum(1 for r in self.resources if isinstance(r, Tree))}개, 돌 {sum(1 for r in self.resources if isinstance(r, Rock))}개")

    def _is_too_close_to_other_resources(self, pos, min_distance=5.0):
        """다른 리소스와 거리 체크"""
        for resource in self.resources:
            distance = (resource.position - pos).length()
            if distance < min_distance:
                return True
        return False

    def update(self, dt):
        """리소스 시스템 업데이트"""
        # 쿨다운 감소
        if self.gather_cooldown > 0:
            self.gather_cooldown -= dt

        # 고갈된 리소스 제거
        for resource in self.resources[:]:
            if resource.is_depleted():
                resource.cleanup()
                self.resources.remove(resource)

                # 리소스 재스폰 (나중에 구현 가능)
                self._respawn_resource(resource)

    def _respawn_resource(self, depleted_resource):
        """리소스 재스폰"""
        # 일정 시간 후에 리소스 재스폰
        def spawn():
            x = random.uniform(-80, 80)
            y = random.uniform(-80, 80)
            pos = Point3(x, y, 0)

            if depleted_resource.resource_type == "wood":
                new_resource = Tree(self.game, pos)
            else:
                new_resource = Rock(self.game, pos)

            self.resources.append(new_resource)
            print(f"[Resource] 리소스 재스폰: {new_resource.resource_type} at {pos}")

        self.game.taskMgr.doMethodLater(
            30.0,  # 30초 후 재스폰
            lambda task: spawn(),
            f'respawn_{depleted_resource.resource_type}_{id(depleted_resource)}'
        )

    def try_gather(self, player_pos):
        """채집 시도"""
        if self.gather_cooldown > 0:
            return None, None

        # 가장 가까운 리소스 찾기
        closest_resource = None
        closest_distance = float('inf')

        for resource in self.resources:
            distance = (resource.position - player_pos).length()
            if distance < closest_distance:
                closest_distance = distance
                closest_resource = resource

        # 사정거리 내에 있는지 확인
        if closest_resource and closest_distance <= self.gather_range:
            # 채집 실행
            gathered = closest_resource.gather()
            self.gather_cooldown = self.gather_cooldown_time

            if gathered > 0:
                # 채집 완료
                resource_type = closest_resource.resource_type
                print(f"[Resource] 채집 완료: {resource_type} +{gathered}")
                return resource_type, gathered
            else:
                # 채집 중
                resource_type = closest_resource.resource_type
                print(f"[Resource] 채집 중: {resource_type} ({closest_resource.health}/{closest_resource.max_health})")
                return resource_type, 0

        return None, None

    def get_nearby_resource(self, player_pos, max_distance=10.0):
        """근처의 리소스 반환 (UI 표시용)"""
        for resource in self.resources:
            distance = (resource.position - player_pos).length()
            if distance <= max_distance:
                return resource, distance
        return None, None

    def cleanup(self):
        """정리"""
        for resource in self.resources:
            resource.cleanup()
        self.resources.clear()

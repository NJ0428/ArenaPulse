"""
바닥 아이템 시스템
드롭된 아이템의 시각화와 줍기 처리
"""
from panda3d.core import CardMaker, Vec3, TransparencyAttrib


class GroundItem:
    """바닥에 떨어진 아이템"""

    def __init__(self, game, position, item_type, item_data):
        self.game = game
        self.position = position
        self.item_type = item_type  # 'tool' or 'resource'
        self.item_data = item_data  # Tool instance or resource dict
        self.node = None
        self.lifetime = 300.0  # 5분 후 사라짐
        self.age = 0.0

        self._create_visual()

    def _create_visual(self):
        """시각적 표현 생성 (Billboard 스프라이트)"""
        cm = CardMaker(f'ground_item_{id(self)}')
        size = 0.5
        cm.setFrame(-size/2, size/2, -size/2, size/2)

        self.node = self.game.render.attachNewNode(cm.generate())
        self.node.setPos(self.position)
        self.node.setZ(0.3)  # 바닥 약간 위에

        # 항상 카메라를 향하도록
        self.node.setBillboardPointEye()
        self.node.setTransparency(TransparencyAttrib.MAlpha)

        # 아이템 타입에 따른 색상
        if self.item_type == 'tool':
            tool = self.item_data
            self.node.setColor(*tool.color, 0.8)
            self.node.setTag('item_type', 'tool')
            self.node.setTag('tool_type', tool.tool_type)
        else:
            # 리소스 아이템
            colors = {'wood': (0.6, 0.4, 0.2), 'stone': (0.5, 0.5, 0.5)}
            color = colors.get(self.item_data.get('type'), (1, 1, 1))
            self.node.setColor(*color, 0.8)
            self.node.setTag('item_type', 'resource')

        # 펄스 애니메이션 시작
        self._start_pulse_animation()

    def _start_pulse_animation(self):
        """빛나는/펄스 효과로 주의 끌기"""
        # 스케일 업다운 애니메이션
        pass
        # TODO: 더 복잡한 애니메이션이 필요하면 추후 추가

    def can_pickup(self, player_pos, max_distance=3.0):
        """플레이어가 충분히 가까운지 확인"""
        distance = (self.position - player_pos).length()
        return distance <= max_distance

    def pickup(self):
        """아이템 데이터 반환 및 시각 정리"""
        if self.node:
            self.node.removeNode()
        return self.item_type, self.item_data

    def update(self, dt):
        """아이템 업데이트 (나이, 애니메이션)"""
        self.age += dt
        return self.age < self.lifetime  # False면 제거해야 함


class GroundItemSystem:
    """모든 바닥 아이템 관리"""

    def __init__(self, game):
        self.game = game
        self.ground_items = []
        self.pickup_range = 3.0
        self.pickup_cooldown = 0.0
        self.pickup_cooldown_time = 0.5

    def drop_item(self, position, item_type, item_data):
        """위치에 아이템 드롭"""
        ground_item = GroundItem(self.game, position, item_type, item_data)
        self.ground_items.append(ground_item)
        print(f"[GroundItem] Dropped {item_type} at {position}")

    def try_pickup(self, player_pos):
        """가까운 아이템 줍기 시도"""
        if self.pickup_cooldown > 0:
            return None, None

        for item in self.ground_items[:]:
            if item.can_pickup(player_pos, self.pickup_range):
                item_type, item_data = item.pickup()
                self.ground_items.remove(item)
                self.pickup_cooldown = self.pickup_cooldown_time
                print(f"[GroundItem] Picked up {item_type}")
                return item_type, item_data

        return None, None

    def get_nearby_items(self, player_pos, max_distance=10.0):
        """가까운 아이템 목록 반환 (UI용)"""
        nearby = []
        for item in self.ground_items:
            distance = (item.position - player_pos).length()
            if distance <= max_distance:
                nearby.append((item, distance))
        return nearby

    def update(self, dt):
        """모든 바닥 아이템 업데이트"""
        if self.pickup_cooldown > 0:
            self.pickup_cooldown -= dt

        # 만료된 아이템 제거
        for item in self.ground_items[:]:
            should_keep = item.update(dt)
            if not should_keep:
                if item.node:
                    item.node.removeNode()
                self.ground_items.remove(item)
                print(f"[GroundItem] Item expired and removed")

    def cleanup(self):
        """모든 바닥 아이템 정리"""
        for item in self.ground_items:
            if item.node:
                item.node.removeNode()
        self.ground_items.clear()

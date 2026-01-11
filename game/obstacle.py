from panda3d.core import Vec3, Point3, BitMask32, Texture, TransparencyAttrib, CardMaker
from panda3d.core import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionBox
import random


class Obstacle:
    """장애물 클래스"""

    def __init__(self, game, position, size, obstacle_type="crate"):
        self.game = game
        self.position = position  # Vec3
        self.size = size  # (width, height, depth)
        self.type = obstacle_type

        # 시각적 노드 생성
        self._create_visual_node()

        # 충돌 박스 생성
        self._create_collision_box()

    def _create_visual_node(self):
        """시각적 노드 생성"""
        # 크래이트(박스) 모양 생성
        cm = CardMaker(f'obstacle_{id(self)}')

        w, h, d = self.size

        # 박스의 6면 생성 (앞, 뒤, 좌, 우, 상, 하)
        faces = []

        # 앞면 (Y+)
        cm.setFrame(-w/2, w/2, -h/2, h/2)
        front = self.game.render.attachNewNode(cm.generate())
        front.setPos(self.position)
        front.setHpr(0, 0, 0)
        front.setPos(self.position + Vec3(0, d/2, 0))
        faces.append(front)

        # 뒷면 (Y-)
        cm.setFrame(-w/2, w/2, -h/2, h/2)
        back = self.game.render.attachNewNode(cm.generate())
        back.setPos(self.position + Vec3(0, -d/2, 0))
        back.setHpr(0, 0, 180)
        faces.append(back)

        # 좌면 (X-)
        cm.setFrame(-d/2, d/2, -h/2, h/2)
        left = self.game.render.attachNewNode(cm.generate())
        left.setPos(self.position + Vec3(-w/2, 0, 0))
        left.setHpr(0, 0, 90)
        faces.append(left)

        # 우면 (X+)
        cm.setFrame(-d/2, d/2, -h/2, h/2)
        right = self.game.render.attachNewNode(cm.generate())
        right.setPos(self.position + Vec3(w/2, 0, 0))
        right.setHpr(0, 0, -90)
        faces.append(right)

        # 상면 (Z+)
        cm.setFrame(-w/2, w/2, -d/2, d/2)
        top = self.game.render.attachNewNode(cm.generate())
        top.setPos(self.position + Vec3(0, 0, h))
        top.setHpr(-90, 0, 0)
        faces.append(top)

        # 하면 (Z-)
        cm.setFrame(-w/2, w/2, -d/2, d/2)
        bottom = self.game.render.attachNewNode(cm.generate())
        bottom.setPos(self.position)
        bottom.setHpr(90, 0, 0)
        faces.append(bottom)

        # 모든 면을 하나의 노드로 그룹화
        self.node = self.game.render.attachNewNode(f'obstacle_node_{id(self)}')

        for face in faces:
            face.reparentTo(self.node)

        # 텍스처 로드
        if self.type == "crate":
            texture = self.game.loader.loadTexture("textures/crate.png")
            if texture:
                self.node.setTexture(texture)
                # 텍스처 반복 설정
                texture.setWrapU(Texture.WMRepeat)
                texture.setWrapV(Texture.WMRepeat)
            else:
                # 텍스처 없으면 기본 색상 (나무색)
                self.node.setColor(0.6, 0.4, 0.2, 1.0)
        elif self.type == "wall":
            texture = self.game.loader.loadTexture("textures/brick.png")
            if texture:
                self.node.setTexture(texture)
            else:
                self.node.setColor(0.5, 0.5, 0.5, 1.0)
        elif self.type == "pillar":
            texture = self.game.loader.loadTexture("textures/stone.png")
            if texture:
                self.node.setTexture(texture)
            else:
                self.node.setColor(0.7, 0.7, 0.7, 1.0)

    def _create_collision_box(self):
        """충돌 박스 생성"""
        # 충돌 노드 생성
        collision_node = CollisionNode(f'obstacle_collision_{id(self)}')
        collision_node.setIntoCollideMask(BitMask32.bit(1))

        w, h, d = self.size
        # 충돌 박스 생성 (중심이 (0,0,h/2)에 있도록)
        collision_box = CollisionBox(Point3(0, 0, h/2), w/2, d/2, h/2)
        collision_node.addSolid(collision_box)

        self.collision_node = self.node.attachNewNode(collision_node)
        self.collision_node.setPos(self.position)

    def remove(self):
        """장애물 제거"""
        if self.node:
            self.node.removeNode()


class ObstacleSystem:
    """장애물 관리 시스템"""

    def __init__(self, game):
        self.game = game
        self.obstacles = []

        # 플레이어 충돌 트래버설
        self.collision_traverser = CollisionTraverser()
        self.collision_handler = CollisionHandlerQueue()

        # 플레이어 충돌 레이 설정
        self._setup_player_collision()

        # 초기 장애물 생성
        self._create_initial_obstacles()

        print("[ObstacleSystem] 장애물 시스템 초기화 완료")

    def _setup_player_collision(self):
        """플레이어 충돌 감지 설정"""
        # 플레이어를 위한 충돌 노드 (레이)
        collision_node = CollisionNode('player_collision')
        collision_node.setFromCollideMask(BitMask32.bit(1))
        collision_node.setIntoCollideMask(BitMask32.allOff())

        # 플레이어 주변에 작은 박스로 충돌 감지
        from panda3d.core import CollisionSphere
        collision_sphere = CollisionSphere(0, 0, 1, 0.5)
        collision_node.addSolid(collision_sphere)

        self.player_collision_node = self.game.player.node.attachNewNode(collision_node)
        self.collision_traverser.addCollider(self.player_collision_node, self.collision_handler)

    def _create_initial_obstacles(self):
        """초기 장애물 생성"""
        # 크래이트 장애물들
        crate_positions = [
            (Vec3(20, 20, 0), (2, 2, 2)),
            (Vec3(-20, 20, 0), (2, 2, 2)),
            (Vec3(20, -20, 0), (2, 2, 2)),
            (Vec3(-20, -20, 0), (2, 2, 2)),
            (Vec3(0, 30, 0), (3, 3, 3)),
            (Vec3(30, 0, 0), (2, 2, 2)),
            (Vec3(-30, 0, 0), (2, 2, 2)),
        ]

        for pos, size in crate_positions:
            self.add_obstacle(pos, size, "crate")

        # 기둥 장애물들
        pillar_positions = [
            (Vec3(50, 50, 0), (2, 6, 2)),
            (Vec3(-50, 50, 0), (2, 6, 2)),
            (Vec3(50, -50, 0), (2, 6, 2)),
            (Vec3(-50, -50, 0), (2, 6, 2)),
        ]

        for pos, size in pillar_positions:
            self.add_obstacle(pos, size, "pillar")

        print(f"[ObstacleSystem] 초기 장애물 {len(self.obstacles)}개 생성 완료")

    def add_obstacle(self, position, size, obstacle_type="crate"):
        """장애물 추가"""
        obstacle = Obstacle(self.game, position, size, obstacle_type)
        self.obstacles.append(obstacle)
        print(f"[ObstacleSystem] 장애물 추가: {obstacle_type} at {position}")
        return obstacle

    def add_random_obstacle(self, player_pos):
        """플레이어 근처에 랜덤 장애물 추가"""
        # 플레이어 앞쪽 5~10단위 거리
        distance = random.uniform(5, 10)

        # 플레이어가 바라보는 방향
        heading_rad = 0  # 플레이어 heading을 0으로 가정 (실제로는 player.heading 사용 필요)

        # 랜덤 위치 계산
        offset_x = random.uniform(-3, 3)
        offset_y = distance

        x = player_pos.x + offset_x
        y = player_pos.y + offset_y
        z = 0  # 바닥에

        # 맵 범위 체크 (-100 ~ 100)
        if not (-100 < x < 100 and -100 < y < 100):
            print("[ObstacleSystem] 맵 범위를 벗어남")
            return None

        # 랜덤 크기와 타입
        size_types = [
            ((2, 2, 2), "crate"),
            ((3, 3, 3), "crate"),
            ((2, 4, 2), "pillar"),
        ]

        size, obs_type = random.choice(size_types)

        return self.add_obstacle(Vec3(x, y, z), size, obs_type)

    def check_player_collision(self, player_pos, new_pos):
        """플레이어 이동 시 충돌 체크"""
        # 충돌 핸들러 초기화
        self.collision_handler.clearEntries()

        # 플레이어 위치를 임시로 이동
        original_pos = self.game.player.node.getPos()
        self.game.player.node.setPos(new_pos)

        # 충돌 체크
        self.collision_traverser.traverse(self.game.render)

        # 플레이어 위치 복구
        self.game.player.node.setPos(original_pos)

        # 충돌이 있으면 True 반환
        return self.collision_handler.getNumEntries() > 0

    def update(self, dt):
        """업데이트"""
        # 필요한 경우 추가 업데이트 로직
        pass

    def cleanup(self):
        """정리"""
        for obstacle in self.obstacles:
            obstacle.remove()
        self.obstacles.clear()

        if self.player_collision_node:
            self.player_collision_node.removeNode()

        print("[ObstacleSystem] 장애물 시스템 정리 완료")

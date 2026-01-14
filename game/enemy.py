from panda3d.core import (
    Point3, Vec3, BitMask32, CollisionNode, CollisionSphere,
    CollisionHandlerQueue, CollisionTraverser, CollisionRay,
    TextNode, TransparencyAttrib
)
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
import math
import random
import time


class Enemy:
    """적 AI 클래스 - 플레이어를 추적하고 공격"""

    # 적 상태 열거형
    STATE_IDLE = 0
    STATE_CHASE = 1
    STATE_ATTACK = 2
    STATE_DEAD = 3

    def __init__(self, game, position, enemy_type="melee"):
        self.game = game
        self.position = position
        self.enemy_type = enemy_type  # "melee" 또는 "ranged"

        # 적 속성
        if enemy_type == "ranged":
            self.max_health = 50
            self.health = 50
            self.speed = 6.0
            self.attack_range = 30.0
            self.attack_damage = 10
            self.attack_cooldown = 2.0
            self.detection_range = 50.0
            self.color = (0.8, 0.2, 0.8, 1.0)  # 보라색
            self.scale = 1.5
        else:  # melee
            self.max_health = 100
            self.health = 100
            self.speed = 10.0
            self.attack_range = 3.0
            self.attack_damage = 20
            self.attack_cooldown = 1.5
            self.detection_range = 40.0
            self.color = (0.9, 0.2, 0.2, 1.0)  # 빨간색
            self.scale = 2.0

        # 상태
        self.state = self.STATE_IDLE
        self.current_attack_cooldown = 0.0
        self.is_dead = False
        self.death_time = 0.0

        # 적 3D 모델 생성
        self._create_enemy_model()

        # 충돌 설정
        self._setup_collision()

        # 체력바 UI
        self._create_health_bar()

        print(f"[Enemy] {enemy_type.upper()} 적 생성 (위치: {position})")

    def _create_enemy_model(self):
        """적 3D 모델 생성 (간단한 구형)"""
        from panda3d.core import CardMaker

        # 적의 몸체 (카드로 구현)
        cm = CardMaker('enemy_body')
        cm.setFrame(-self.scale/2, self.scale/2, -self.scale, self.scale)

        self.node = self.game.render.attachNewNode(cm.generate())

        # 항상 카메라를 향하도록 (Billboarding)
        self.node.setBillboardPointEye()

        # 색상 설정
        self.node.setColor(self.color[0], self.color[1], self.color[2], 1.0)

        # 위치 설정
        self.node.setPos(self.position)

        # 투명도 설정 (사망 시 페이드 아웃용)
        self.node.setTransparency(TransparencyAttrib.MAlpha)

    def _setup_collision(self):
        """충돌 감지 설정"""
        # 충돌 구 생성
        collision_sphere = CollisionSphere(0, 0, 0, self.scale / 2)

        # 충돌 노드 생성
        collision_node = CollisionNode('enemy_collision')
        collision_node.addSolid(collision_sphere)

        # 충돌 마스크 설정 (총알과 플레이어와 충돌)
        collision_node.setIntoCollideMask(BitMask32.bit(2))

        # 충돌 노드를 적에 부착
        self.collision_node = self.node.attachNewNode(collision_node)
        self.collision_node.setPythonTag('enemy', self)

    def _create_health_bar(self):
        """체력바 UI 생성"""
        # 체력바 배경
        self.health_bar_bg = OnscreenText(
            text="",
            pos=(0, 0),
            scale=0,
            fg=(0.2, 0.2, 0.2, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        self.health_bar_bg.hide()

        # 체력바 전경
        self.health_bar_fg = OnscreenText(
            text="",
            pos=(0, 0),
            scale=0,
            fg=(0.2, 1, 0.2, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        self.health_bar_fg.hide()

    def update(self, dt):
        """매 프레임 업데이트"""
        if self.is_dead:
            self._update_death(dt)
            return

        # 공격 쿨다운 감소
        if self.current_attack_cooldown > 0:
            self.current_attack_cooldown -= dt

        # 플레이어 위치 가져오기
        player_pos = self.game.player.get_position()
        enemy_pos = self.node.getPos()

        # 플레이어와의 거리 계산
        distance_to_player = (player_pos - enemy_pos).length()

        # 상태 머신
        if distance_to_player <= self.attack_range:
            # 공격 범위 내
            self.state = self.STATE_ATTACK
            self._attack(player_pos, distance_to_player)
        elif distance_to_player <= self.detection_range:
            # 감지 범위 내 - 추적
            self.state = self.STATE_CHASE
            self._chase(player_pos, dt)
        else:
            # 감지 범위 밖 - 대기
            self.state = self.STATE_IDLE

        # 체력바 업데이트
        self._update_health_bar()

    def _chase(self, player_pos, dt):
        """플레이어 추적"""
        # 현재 위치
        current_pos = self.node.getPos()

        # 플레이어 방향 벡터
        direction = player_pos - current_pos
        direction.normalize()

        # 이동
        new_pos = current_pos + direction * self.speed * dt
        self.node.setPos(new_pos)

    def _attack(self, player_pos, distance):
        """플레이어 공격"""
        if self.current_attack_cooldown > 0:
            return

        # 공격 가능
        self.current_attack_cooldown = self.attack_cooldown

        if self.enemy_type == "melee":
            # 근접 공격 - 플레이어에게 직접 데미지
            if distance <= self.attack_range:
                self.game.player.health -= self.attack_damage
                print(f"[Enemy] 근접 공격! 플레이어 데미지: {self.attack_damage}")

                # 공격 사운드 재생
                self.game.sound.play('target_hit')  # 임시로 기존 사운드 사용
        else:
            # 원거리 공격 - 투사체 발사
            self._shoot_projectile(player_pos)
            print(f"[Enemy] 원거리 공격!")

    def _shoot_projectile(self, target_pos):
        """원거리 적 투사체 발사"""
        from panda3d.core import CardMaker

        # 투사체 생성
        cm = CardMaker('enemy_projectile')
        cm.setFrame(-0.2, 0.2, -0.1, 0.1)
        projectile = self.game.render.attachNewNode(cm.generate())

        # 항상 카메라를 향하도록
        projectile.setBillboardPointEye()
        projectile.setTransparency(TransparencyAttrib.MAlpha)

        # 투사체 색상 (빨간색)
        projectile.setColor(1.0, 0.3, 0.3, 1.0)

        # 발사 위치 (적 위치)
        start_pos = self.node.getPos()
        projectile.setPos(start_pos)

        # 목표 방향
        direction = target_pos - start_pos
        direction.normalize()

        # 투사체 정보 저장
        if not hasattr(self, 'projectiles'):
            self.projectiles = []

        self.projectiles.append({
            'node': projectile,
            'direction': direction,
            'speed': 30.0,
            'lifetime': 3.0,
            'damage': self.attack_damage
        })

    def update_projectiles(self, dt):
        """투사체 업데이트"""
        if not hasattr(self, 'projectiles'):
            return

        for proj in self.projectiles[:]:
            # 이동
            proj['node'].setPos(
                proj['node'].getPos() + proj['direction'] * proj['speed'] * dt
            )

            # 플레이어 충돌 체크
            player_pos = self.game.player.get_position()
            distance = (proj['node'].getPos() - player_pos).length()

            if distance < 2.0:  # 플레이어 히트박스 크기
                # 플레이어에게 데미지
                self.game.player.health -= proj['damage']
                print(f"[Enemy] 투사체 명중! 데미지: {proj['damage']}")

                # 투사체 제거
                proj['node'].removeNode()
                self.projectiles.remove(proj)

                # 명중 사운드
                self.game.sound.play('target_hit')
                continue

            # 수명 감소
            proj['lifetime'] -= dt

            # 수명 종료시 제거
            if proj['lifetime'] <= 0:
                proj['node'].removeNode()
                self.projectiles.remove(proj)

    def take_damage(self, damage):
        """데미지 받기"""
        if self.is_dead:
            return False

        self.health -= damage

        if self.health <= 0:
            self.health = 0
            self.die()
            return True  # 사망

        # 맞은 효과 (색상 변경)
        self.node.setColor(1.0, 1.0, 1.0, 1.0)  # 흰색으로 깜빡임
        return False

    def die(self):
        """사망 처리"""
        self.is_dead = True
        self.state = self.STATE_DEAD
        self.death_time = time.time()

        # 색상 변경 (회색)
        self.node.setColor(0.3, 0.3, 0.3, 1.0)

        print(f"[Enemy] 적 사망!")

        # 사망 사운드 재생
        self.game.sound.play('target_hit')  # 임시로 기존 사운드 사용

    def _update_death(self, dt):
        """사망 후 업데이트 (페이드 아웃)"""
        # 사망 후 3초 뒤 제거
        if time.time() - self.death_time > 3.0:
            self.cleanup()
            return

        # 페이드 아웃 효과
        elapsed = time.time() - self.death_time
        alpha = 1.0 - (elapsed / 3.0)
        if alpha < 0:
            alpha = 0

        self.node.setColor(self.color[0], self.color[1], self.color[2], alpha)

    def _update_health_bar(self):
        """체력바 업데이트"""
        # 적의 화면 위치 계산
        from panda3d.core import Vec2

        # 3D 위치를 2D 화면 좌표로 변환
        pos_3d = self.node.getPos()
        pos_3d.z += self.scale + 0.5  # 머리 위로

        # 카메라 기준 화면 좌표 계산
        cam_pos = self.game.camera.getPos()

        # 간단한 거리 기반 크기 계산
        distance = (pos_3d - cam_pos).length()

        if distance > 60:
            # 너무 멀면 체력바 숨김
            self.health_bar_bg.hide()
            self.health_bar_fg.hide()
            return

        # 화면 좌표 계산 (간단히)
        # 실제 프로젝션 매트릭스 사용이 더 정확하지만
        # 간단하게 화면 중심에서의 오프셋으로 계산
        rel_pos = pos_3d - cam_pos
        screen_x = rel_pos.x / distance * 20
        screen_y = rel_pos.z / distance * 20

        # 체력바 크기 (거리에 따라)
        bar_scale = max(0.02, 0.05 - distance * 0.0005)

        # 체력 비율
        health_ratio = self.health / self.max_health

        # 체력 퍼센트 텍스트로 표시 (특수 문자 없이)
        health_percent = int(health_ratio * 100)

        # 배경 (전체 체력)
        self.health_bar_bg.setPos(screen_x, screen_y + 0.05)
        self.health_bar_bg["scale"] = bar_scale * 2
        self.health_bar_bg.setText(f"[{health_percent}%]")
        self.health_bar_bg.show()

        # 전경 (현재 체력 표시)
        self.health_bar_fg.setPos(screen_x, screen_y + 0.05)
        self.health_bar_fg["scale"] = bar_scale * 2
        self.health_bar_fg.setText(f"[{'=' * int(health_ratio * 10)}{' ' * (10 - int(health_ratio * 10))}]")
        self.health_bar_fg.show()

    def cleanup(self):
        """정리"""
        if self.node:
            self.node.removeNode()

        if self.health_bar_bg:
            self.health_bar_bg.destroy()
        if self.health_bar_fg:
            self.health_bar_fg.destroy()

        # 투사체 정리
        if hasattr(self, 'projectiles'):
            for proj in self.projectiles:
                proj['node'].removeNode()
            self.projectiles.clear()

        # 적 시스템에서 제거
        if self in self.game.enemies.enemies:
            self.game.enemies.enemies.remove(self)


class EnemySystem:
    """적 시스템 관리자"""

    def __init__(self, game):
        self.game = game
        self.enemies = []
        self.spawn_timer = 0.0
        self.spawn_interval = 10.0  # 10초마다 적 스폰
        self.max_enemies = 10  # 최대 적 수

        print("[EnemySystem] 적 시스템 초기화 완료")

    def spawn_enemy(self, enemy_type=None):
        """랜덤 위치에 적 생성"""
        if len(self.enemies) >= self.max_enemies:
            print("[EnemySystem] 최대 적 수 도달")
            return

        # 적 타입 랜덤 선택 (지정되지 않았으면)
        if enemy_type is None:
            enemy_type = random.choice(["melee", "melee", "ranged"])  # 근접 2/3, 원거리 1/3

        # 플레이어 위치
        player_pos = self.game.player.get_position()

        # 플레이어 주변 랜덤 위치 (20~40단위 거리)
        angle = random.uniform(0, 2 * math.pi)
        distance = 20 + random.uniform(0, 20)

        spawn_x = player_pos.x + math.cos(angle) * distance
        spawn_y = player_pos.y + math.sin(angle) * distance
        spawn_z = 0.0  # 바닥

        # 바운드 체크 (-100~100)
        spawn_x = max(-90, min(90, spawn_x))
        spawn_y = max(-90, min(90, spawn_y))

        spawn_pos = Point3(spawn_x, spawn_y, spawn_z)

        # 적 생성
        enemy = Enemy(self.game, spawn_pos, enemy_type)
        self.enemies.append(enemy)

        print(f"[EnemySystem] 적 스폰 완료 ({enemy_type}, 총 {len(self.enemies)}마리)")

    def check_bullet_collisions(self, bullet_pos):
        """
        모든 총알 위치에 대해 적 충돌 체크
        bullet_pos: Point3 - 총알 위치
        """
        for enemy in self.enemies:
            if enemy.is_dead:
                continue

            # 간단한 거리 체크로 충돌 판정
            distance = (bullet_pos - enemy.node.getPos()).length()

            if distance < enemy.scale / 2:
                # 충돌! 적에게 데미지
                damage = self.game.player.gun_damage
                killed = enemy.take_damage(damage)

                print(f"[EnemySystem] 적 명중! 데미지: {damage}, 남은 체력: {enemy.health}")

                # 적 사망 시 점수 추가
                if killed:
                    self._add_score(enemy.enemy_type)

                return enemy  # 맞은 적 반환

        return None

    def _add_score(self, enemy_type):
        """적 처치 시 점수 추가"""
        points = 50 if enemy_type == "ranged" else 30
        print(f"[EnemySystem] 적 처치! +{points}점")

    def update(self, dt):
        """모든 적 업데이트"""
        # 모든 적 업데이트
        for enemy in self.enemies[:]:
            enemy.update(dt)

            # 원거리 적의 투사체 업데이트
            enemy.update_projectiles(dt)

            # 사망한 적 제거 (cleanup에서 자동 제거됨)
            if enemy.is_dead and time.time() - enemy.death_time > 3.0:
                pass  # cleanup에서 자동 처리

        # 자동 스폰 타이머
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            self.spawn_enemy()

    def cleanup(self):
        """정리"""
        for enemy in self.enemies:
            enemy.cleanup()
        self.enemies.clear()
        print("[EnemySystem] 적 시스템 정리 완료")

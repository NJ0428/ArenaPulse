from panda3d.core import (
    Point3, Vec3, BitMask32, CollisionNode, CollisionSphere,
    CollisionHandlerQueue, CollisionTraverser, CollisionRay,
    TextNode, TransparencyAttrib, Vec4
)
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DGG
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
    STATE_PATROL = 4  # 순찰 상태 추가

    # 적 타입별 설정
    ENEMY_TYPES = {
        'melee': {
            'health': 100,
            'speed': 10.0,
            'attack_range': 3.0,
            'attack_damage': 20,
            'attack_cooldown': 1.5,
            'detection_range': 40.0,
            'color': (0.9, 0.2, 0.2, 1.0),  # 빨간색
            'scale': 2.0,
            'score': 30
        },
        'ranged': {
            'health': 50,
            'speed': 6.0,
            'attack_range': 30.0,
            'attack_damage': 10,
            'attack_cooldown': 2.0,
            'detection_range': 50.0,
            'color': (0.8, 0.2, 0.8, 1.0),  # 보라색
            'scale': 1.5,
            'score': 50
        },
        'sprinter': {  # 새로운 타입: 빠른 적
            'health': 40,
            'speed': 18.0,  # 매우 빠름
            'attack_range': 2.5,
            'attack_damage': 15,
            'attack_cooldown': 0.8,  # 빠른 공격
            'detection_range': 45.0,
            'color': (1.0, 0.8, 0.0, 1.0),  # 노란색
            'scale': 1.3,
            'score': 40
        },
        'tank': {  # 새로운 타입: 탱크
            'health': 250,  # 높은 체력
            'speed': 5.0,  # 느림
            'attack_range': 3.0,
            'attack_damage': 35,  # 높은 데미지
            'attack_cooldown': 2.5,
            'detection_range': 35.0,
            'color': (0.3, 0.3, 0.3, 1.0),  # 검은색
            'scale': 3.0,  # 큰 크기
            'score': 100
        },
        'bomber': {  # 새로운 타입: 폭탄형
            'health': 60,
            'speed': 8.0,
            'attack_range': 5.0,  # 폭발 범위
            'attack_damage': 50,  # 높은 데미지
            'attack_cooldown': 3.0,
            'detection_range': 40.0,
            'color': (1.0, 0.5, 0.0, 1.0),  # 주황색
            'scale': 1.8,
            'score': 70,
            'explode_on_death': True  # 사망 시 폭발
        }
    }

    def __init__(self, game, position, enemy_type="melee"):
        self.game = game
        self.position = position
        self.enemy_type = enemy_type

        # 적 타입별 속성 로드
        if enemy_type not in self.ENEMY_TYPES:
            enemy_type = "melee"

        props = self.ENEMY_TYPES[enemy_type]
        self.max_health = props['health']
        self.health = self.max_health
        self.speed = props['speed']
        self.attack_range = props['attack_range']
        self.attack_damage = props['attack_damage']
        self.attack_cooldown = props['attack_cooldown']
        self.detection_range = props['detection_range']
        self.color = props['color']
        self.scale = props['scale']
        self.score_value = props['score']
        self.explode_on_death = props.get('explode_on_death', False)

        # 상태
        self.state = self.STATE_IDLE
        self.current_attack_cooldown = 0.0
        self.is_dead = False
        self.death_time = 0.0

        # 순찰 관련
        self.patrol_target = None
        self.patrol_timer = 0.0

        # 적 3D 모델 생성
        self._create_enemy_model()

        # 충돌 설정
        self._setup_collision()

        # 체력바 UI
        self._create_health_bar()

        print(f"[Enemy] {enemy_type.upper()} 적 생성 (위치: {position}, 체력: {self.health})")

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
        # 체력 텍스트 (퍼센트)
        self.health_text = OnscreenText(
            text="",
            pos=(0, 0),
            scale=0,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        self.health_text.hide()

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
            # 감지 범위 밖 - 순찰
            self.state = self.STATE_PATROL
            self._patrol(dt)

        # 체력바 업데이트
        self._update_health_bar()

    def _patrol(self, dt):
        """순찰 동작"""
        # 순찰 타이머
        self.patrol_timer -= dt

        if self.patrol_timer <= 0 or self.patrol_target is None:
            # 새로운 순찰 지점 설정 (현재 위치 주변)
            current_pos = self.node.getPos()
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(5, 15)

            self.patrol_target = Point3(
                current_pos.x + math.cos(angle) * distance,
                current_pos.y + math.sin(angle) * distance,
                0.0
            )

            # 바운드 체크 (-90~90)
            self.patrol_target.x = max(-90, min(90, self.patrol_target.x))
            self.patrol_target.y = max(-90, min(90, self.patrol_target.y))

            self.patrol_timer = random.uniform(2, 5)  # 2~5초마다 변경

        # 순찰 지점으로 이동
        current_pos = self.node.getPos()
        direction = self.patrol_target - current_pos
        distance = direction.length()

        if distance > 0.5:
            direction.normalize()
            new_pos = current_pos + direction * (self.speed * 0.3) * dt  # 느리게 순찰
            self.node.setPos(new_pos)

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

        if self.enemy_type == "bomber":
            # 폭탄형 적 - 자폭 공격
            self._explode()
        elif self.enemy_type == "ranged":
            # 원거리 공격 - 투사체 발사
            self._shoot_projectile(player_pos)
            print(f"[Enemy] 원거리 공격!")
        else:
            # 근접 공격 - 플레이어에게 직접 데미지
            if distance <= self.attack_range:
                self.game.player.health -= self.attack_damage
                # 데미지 인디케이터 표시
                if hasattr(self.game, 'show_damage_indicator'):
                    self.game.show_damage_indicator()

                print(f"[Enemy] 근접 공격! 플레이어 데미지: {self.attack_damage}")

                # 공격 사운드 재생
                self.game.sound.play('target_hit')

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

                # 데미지 인디케이터 표시
                if hasattr(self.game, 'show_damage_indicator'):
                    self.game.show_damage_indicator()

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

    def _explode(self):
        """폭발 (폭탄형 적)"""
        enemy_pos = self.node.getPos()
        player_pos = self.game.player.get_position()

        # 플레이어와의 거리
        distance = (player_pos - enemy_pos).length()

        # 폭발 범위 내에 있으면 데미지
        if distance <= self.attack_range * 2:  # 폭발 범위는 공격 범위의 2배
            damage = self.attack_damage
            self.game.player.health -= damage

            # 데미지 인디케이터 표시
            if hasattr(self.game, 'show_damage_indicator'):
                self.game.show_damage_indicator()

            print(f"[Enemy] 폭발! 플레이어 데미지: {damage}")

        # 사운드 재생
        self.game.sound.play('target_hit')

        # 즉시 사망 처리
        self.die()

    def take_damage(self, damage):
        """데미지 받기"""
        if self.is_dead:
            return False

        self.health -= damage

        if self.health <= 0:
            self.health = 0

            # 폭탄형 적이면 폭발
            if self.explode_on_death:
                self._explode()
            else:
                self.die()
            return True  # 사망

        # 맞은 효과 (색상 변경)
        self.node.setColor(1.0, 1.0, 1.0, 1.0)  # 흰색으로 깜빡임

        # 0.1초 후 원래 색상 복구
        self.game.taskMgr.doMethodLater(
            0.1,
            lambda task: self.node.setColor(self.color[0], self.color[1], self.color[2], 1.0),
            f'restore_color_{id(self)}'
        )

        return False

    def die(self):
        """사망 처리"""
        if self.is_dead:
            return

        self.is_dead = True
        self.state = self.STATE_DEAD
        self.death_time = time.time()

        # 색상 변경 (회색)
        self.node.setColor(0.3, 0.3, 0.3, 1.0)

        # 색상 복구 태스크 취소
        task_name = f'restore_color_{id(self)}'
        if self.game.taskMgr.hasTaskNamed(task_name):
            self.game.taskMgr.remove(task_name)

        print(f"[Enemy] 적 사망! ({self.enemy_type})")

        # 사망 사운드 재생
        self.game.sound.play('target_hit')

        # 킬 피드에 추가
        if hasattr(self.game, 'add_kill_feed'):
            self.game.add_kill_feed(self.enemy_type, self.score_value)

    def _update_death(self, dt):
        """사망 후 업데이트 (페이드 아웃)"""
        # 사망 후 2초 뒤 제거
        if time.time() - self.death_time > 2.0:
            self.cleanup()
            return

        # 페이드 아웃 효과
        elapsed = time.time() - self.death_time
        alpha = 1.0 - (elapsed / 2.0)
        if alpha < 0:
            alpha = 0

        self.node.setColor(self.color[0], self.color[1], self.color[2], alpha)

    def _update_health_bar(self):
        """체력바 업데이트"""
        # 적의 화면 위치 계산
        pos_3d = self.node.getPos()
        pos_3d.z += self.scale + 0.5  # 머리 위로

        # 카메라 기준 화면 좌표 계산
        cam_pos = self.game.camera.getPos()

        # 간단한 거리 기반 크기 계산
        distance = (pos_3d - cam_pos).length()

        if distance > 60:
            # 너무 멀면 체력바 숨김
            self.health_text.hide()
            return

        # 화면 좌표 계산
        rel_pos = pos_3d - cam_pos
        screen_x = rel_pos.x / distance * 20
        screen_y = rel_pos.z / distance * 20

        # 체력바 크기 (거리에 따라)
        bar_scale = max(0.03, 0.06 - distance * 0.0005)

        # 체력 퍼센트
        health_percent = int((self.health / self.max_health) * 100)

        # 체력바 색상 (체력에 따라)
        if health_percent > 60:
            color = (0.2, 1, 0.2, 1)  # 초록색
        elif health_percent > 30:
            color = (1, 1, 0.2, 1)  # 노란색
        else:
            color = (1, 0.2, 0.2, 1)  # 빨간색

        # 체력 텍스트 표시
        self.health_text.setPos(screen_x, screen_y + 0.08)
        self.health_text["scale"] = bar_scale
        self.health_text.setText(f"{health_percent}%")
        self.health_text['fg'] = color
        self.health_text.show()

    def cleanup(self):
        """정리"""
        if self.node:
            self.node.removeNode()

        if self.health_text:
            self.health_text.destroy()

        # 투사체 정리
        if hasattr(self, 'projectiles'):
            for proj in self.projectiles:
                proj['node'].removeNode()
            self.projectiles.clear()

        # 색상 복구 태스크 취소
        task_name = f'restore_color_{id(self)}'
        if hasattr(self.game, 'taskMgr') and self.game.taskMgr.hasTaskNamed(task_name):
            self.game.taskMgr.remove(task_name)

        # 적 시스템에서 제거
        if hasattr(self.game, 'enemies') and self in self.game.enemies.enemies:
            self.game.enemies.enemies.remove(self)


class EnemySystem:
    """적 시스템 관리자 - 웨이브 시스템 포함"""

    def __init__(self, game):
        self.game = game
        self.enemies = []
        self.spawn_timer = 0.0
        self.spawn_interval = 10.0  # 초기 스폰 간격

        # 웨이브 시스템
        self.current_wave = 1
        self.wave_timer = 0.0
        self.wave_duration = 60.0  # 웨이브 지속 시간 (60초)
        self.enemies_in_wave = 0
        self.max_enemies = 5  # 초기 최대 적 수

        # 점수 시스템
        self.total_score = 0
        self.kill_count = 0

        print("[EnemySystem] 적 시스템 초기화 완료")

    def get_wave_config(self):
        """현재 웨이브 설정 반환"""
        # 웨이브가 높을수록 더 어려움
        multiplier = 1 + (self.current_wave - 1) * 0.3

        return {
            'max_enemies': min(20, int(5 + self.current_wave * 2)),
            'spawn_interval': max(3.0, 10.0 - self.current_wave * 0.5),
            'enemy_types': self._get_available_enemy_types(),
            'multiplier': multiplier
        }

    def _get_available_enemy_types(self):
        """현재 웨이브에서 사용 가능한 적 타입"""
        types = ['melee']  # 항상 기본 적

        if self.current_wave >= 2:
            types.append('ranged')
        if self.current_wave >= 3:
            types.append('sprinter')
        if self.current_wave >= 4:
            types.append('bomber')
        if self.current_wave >= 5:
            types.append('tank')

        return types

    def spawn_enemy(self, enemy_type=None):
        """랜덤 위치에 적 생성"""
        config = self.get_wave_config()

        if len(self.enemies) >= config['max_enemies']:
            return

        # 적 타입 결정
        if enemy_type is None:
            available_types = config['enemy_types']
            # 기본 적이 더 많이 나옴
            weights = [0.4 if t == 'melee' else 0.2 for t in available_types]
            enemy_type = random.choices(available_types, weights=weights)[0]

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

        # 웨이브 보너스 적용
        multiplier = config['multiplier']
        enemy.health = int(enemy.health * multiplier)
        enemy.max_health = enemy.health
        enemy.attack_damage = int(enemy.attack_damage * multiplier)

        self.enemies.append(enemy)
        self.enemies_in_wave += 1

        print(f"[EnemySystem] 적 스폰 ({enemy_type}, 웨이브 {self.current_wave}, 총 {len(self.enemies)}마리)")

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
                    self.add_score(enemy.enemy_type, enemy.score_value)

                return enemy  # 맞은 적 반환

        return None

    def add_score(self, enemy_type, base_score):
        """적 처치 시 점수 추가"""
        # 웨이브 보너스
        wave_bonus = 1 + (self.current_wave - 1) * 0.2
        final_score = int(base_score * wave_bonus)

        self.total_score += final_score
        self.kill_count += 1

        print(f"[EnemySystem] 적 처치! +{final_score}점 (총: {self.total_score}점, 킬: {self.kill_count})")

        # UI 업데이트
        if hasattr(self.game, 'update_score_ui'):
            self.game.update_score_ui()

    def update(self, dt):
        """모든 적 업데이트"""
        config = self.get_wave_config()

        # 모든 적 업데이트
        for enemy in self.enemies[:]:
            enemy.update(dt)

            # 원거리 적의 투사체 업데이트
            enemy.update_projectiles(dt)

        # 자동 스폰
        self.spawn_timer += dt
        if self.spawn_timer >= config['spawn_interval']:
            self.spawn_timer = 0.0
            self.spawn_enemy()

        # 웨이프 타이머
        self.wave_timer += dt
        if self.wave_timer >= self.wave_duration:
            # 다음 웨이브
            self._next_wave()

    def _next_wave(self):
        """다음 웨이브로 넘어감"""
        self.current_wave += 1
        self.wave_timer = 0.0
        self.enemies_in_wave = 0

        config = self.get_wave_config()

        print(f"[EnemySystem] ===== 웨이브 {self.current_wave} 시작! =====")
        print(f"[EnemySystem] 최대 적 수: {config['max_enemies']}, 스폰 간격: {config['spawn_interval']:.1f}초")
        print(f"[EnemySystem] 가능한 적 타입: {', '.join(config['enemy_types'])}")

        # 웨이브 알림 표시
        if hasattr(self.game, 'show_wave_notification'):
            self.game.show_wave_notification(self.current_wave)

    def get_stats(self):
        """현재 통계 반환"""
        return {
            'score': self.total_score,
            'kills': self.kill_count,
            'wave': self.current_wave,
            'enemies': len(self.enemies)
        }

    def cleanup(self):
        """정리"""
        for enemy in self.enemies:
            enemy.cleanup()
        self.enemies.clear()
        print("[EnemySystem] 적 시스템 정리 완료")

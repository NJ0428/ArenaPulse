from panda3d.core import Point3, Vec3, BitMask32, Texture, TransparencyAttrib, ColorAttrib
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, Func, Wait
import math
import random
from game.weapon import create_weapon, WEAPON_TYPES


class Player:
    def __init__(self, game):
        self.game = game
        self.walk_speed = 15.0
        self.run_speed = 25.0
        self.crouch_speed = 8.0  # 숨쉬기 속도
        self.speed = self.walk_speed
        self.is_running = False
        self.is_crouching = False

        # 눈 높이 (일반/숨쉬기)
        self.eye_height = 2.5  # 일반 눈 높이
        self.crouch_eye_height = 1.2  # 숨쉬기 눈 높이
        self.crouch_transition_speed = 8.0  # 숨쉬기 전환 속도
        self.current_eye_height = self.eye_height

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
        self.is_firing = False  # 마우스 버튼 누름 상태 (연발용)
        self.fire_cooldown = 0.0  # 발사 쿨다운 타이머

        # 무기 시스템
        self.weapons = {}  # 무기 인벤토리
        self.current_weapon = None  # 현재 장착 무기
        self.current_weapon_index = -1  # 현재 무기 인덱스
        self.is_reloading = False  # 재장전 중
        self.is_zoomed = False  # 줌 상태

        # 초기 무기 장착 (Rifle)
        self._initialize_weapons()

        # 줌 시스템 (현재 무기 속성 사용)
        self.zoom_fov_reduction = self.current_weapon.zoom_fov_reduction
        self.gun_recoil_zoom_multiplier = self.current_weapon.recoil_zoom_multiplier

        # 반동 시각효과
        self.recoil_pitch = 0.0  # 현재 반동 각도
        self.recoil_recovery = 10.0  # 반동 복구 속도

        # 플레이어 위치 (보이지 않는 노드)
        self._create_player_node()

        # 투사체 리스트
        self.projectiles = []

        # 체력과 방어력
        self.health = 100  # 체력
        self.max_health = 100  # 최대 체력
        self.defense = 100  # 방어력
        self.max_defense = 100  # 최대 방어력

        # 재장전 텍스트 UI
        self.reload_text = None

        # 스태미나 시스템
        self.stamina = 100.0  # 현재 스태미나
        self.max_stamina = 100.0  # 최대 스태미나
        self.stamina_drain_rate = 20.0  # 달리기 시 스태미나 소모율 (초당)
        self.stamina_regen_rate = 15.0  # 스태미나 재생율 (초당, 걷거나 멈출 때)
        self.stamina_regen_delay = 0.5  # 달리기 후 재생 시작 지연 시간
        self.stamina_regen_timer = 0.0  # 재생 타이머

        # 인벤토리 시스템
        self.inventory = {
            'wood': 0,    # 나무
            'stone': 0,   # 돌
        }

        # 도구 시스템
        self.tool_slots = [None] * 6  # 6개 도구 슬롯
        self.current_tool = None  # 현재 장착 도구
        self.current_tool_index = -1  # 현재 도구 인덱스

    def _initialize_weapons(self):
        """무기 초기화 - 모든 무기를 생성하고 Rifle 장착"""
        # 모든 무기 생성
        for weapon_type in WEAPON_TYPES:
            self.weapons[weapon_type] = create_weapon(weapon_type)

        # Rifle 먼저 장착 (기본 무기)
        self.current_weapon_index = WEAPON_TYPES.index('rifle')
        self.current_weapon = self.weapons['rifle']

        print(f"[Player] 무기 시스템 초기화 완료 (현재: {self.current_weapon.name})")

    def switch_weapon(self, slot):
        """
        무기 전환
        slot: 0-3 (Pistol, Rifle, Shotgun, Sniper)
        """
        if 0 <= slot < len(WEAPON_TYPES):
            # 재장전 중이면 전환 불가
            if self.is_reloading:
                print("[Player] 재장전 중에는 무기를 전환할 수 없습니다.")
                return

            weapon_type = WEAPON_TYPES[slot]

            # 같은 무기면 무시
            if self.current_weapon_index == slot:
                return

            self.current_weapon_index = slot
            self.current_weapon = self.weapons[weapon_type]

            # 줌 상태 리셋
            if self.is_zoomed:
                self.toggle_zoom()

            # 줌 속성 업데이트
            self.zoom_fov_reduction = self.current_weapon.zoom_fov_reduction
            self.gun_recoil_zoom_multiplier = self.current_weapon.recoil_zoom_multiplier

            print(f"[Player] 무기 전환: {self.current_weapon.name}")

            # UI 업데이트
            self.game.update_weapon_ui()
        else:
            print(f"[Player] 잘못된 무기 슬롯: {slot}")

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
        self._update_stamina(dt)  # 스태미나 업데이트
        self._update_crouch_height(dt)  # 숨쉬기 높이 업데이트
        self._update_projectiles(dt)
        self._update_recoil(dt)  # 반동 복구
        self._update_firing(dt)  # 연발 처리

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

            current_pos = self.node.getPos()
            new_pos = current_pos + move_vec

            # 장애물 충돌 체크
            if self.game.obstacles.check_player_collision(current_pos, new_pos):
                # 충돌이 있으면 이동하지 않음
                return

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
        # 숨쉬기 중이면 달릴 수 없음
        if self.is_crouching and running:
            return

        # 스태미나가 부족하면 달릴 수 없음
        if running and self.stamina <= 0:
            self.is_running = False
            self.speed = self.crouch_speed if self.is_crouching else self.walk_speed
            return

        self.is_running = running
        self._update_speed()

    def toggle_crouch(self):
        """숨쉬기 토글"""
        self.is_crouching = not self.is_crouching

        # 숨쉬기 상태에서는 달리기 불가
        if self.is_crouching:
            self.is_running = False

        self._update_speed()
        print(f"[Player] Crouch {'ON' if self.is_crouching else 'OFF'}")

    def _update_speed(self):
        """현재 상태에 따른 속도 업데이트"""
        if self.is_crouching:
            self.speed = self.crouch_speed
        elif self.is_running:
            self.speed = self.run_speed
        else:
            self.speed = self.walk_speed

    def ranged_attack(self):
        """Ranged attack (gun shooting)"""
        if self.is_reloading:
            return

        # 무기가 고장났는지 체크
        if self.current_weapon.broken:
            self.game.sound.play('empty_click')
            print("[Player] 무기가 고장났습니다! 수리가 필요합니다.")
            return

        # 발사 가능 여부 체크
        if not self.current_weapon.can_fire(self.fire_cooldown):
            # 탄약이 없으면 재장전 시도
            if self.current_weapon.current_ammo <= 0:
                self.game.sound.play('empty_click')
                self._reload()
            return

        self.fire_cooldown = self.current_weapon.fire_rate

        # 발사 사운드 재생
        self.game.sound.play('gun_shot')

        # 카메라(눈) 위치에서 발사
        start_pos = self.camera_node.getPos(self.game.render)

        # 무기 발사 처리
        from game.weapon import FIRE_MODE_BURST
        is_headshot = False  # TODO: 적 헤드샷 판정 후 구현

        result = self.current_weapon.fire(
            start_pos,
            self.heading,
            self.pitch,
            self.is_zoomed,
            self.game,
            is_headshot
        )

        # 산탄총인 경우 여러 발 반환
        if self.current_weapon.weapon_type == 'shotgun':
            bullets, recoil_amount = result
            for bullet_data in bullets:
                self.projectiles.append(bullet_data)
        else:
            bullet_data, recoil_amount, is_crit = result
            self.projectiles.append(bullet_data)

            # 크리티컬 효과
            if is_crit:
                print(f"[Player] CRITICAL HIT! {bullet_data['damage']} 데미지!")

        # 반동 적용
        self._apply_recoil(recoil_amount)

        print(f"[Player] Shot! Ammo: {self.current_weapon.get_ammo_display()} | Durability: {self.current_weapon.get_durability_percentage()}%")

    def start_firing(self):
        """발사 시작 (마우스 버튼 다운)"""
        self.is_firing = True

        # 단발 모드면 즉시 1발만
        from game.weapon import FIRE_MODE_SEMI
        if self.current_weapon.current_fire_mode == FIRE_MODE_SEMI:
            self.ranged_attack()

    def stop_firing(self):
        """발사 중지 (마우스 버튼 업)"""
        self.is_firing = False
        # 점사 카운터 리셋
        if hasattr(self.current_weapon, 'burst_shots_fired'):
            self.current_weapon.burst_shots_fired = 0

    def _update_firing(self, dt):
        """연발 처리 (매 프레임)"""
        from game.weapon import FIRE_MODE_AUTO, FIRE_MODE_BURST

        # 쿨다운 감소
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt

        # 점사 쿨다운 감소
        if hasattr(self.current_weapon, 'burst_cooldown') and self.current_weapon.burst_cooldown > 0:
            self.current_weapon.burst_cooldown -= dt

        # 발사 버튼이 눌려있을 때 처리
        if self.is_firing:
            current_mode = self.current_weapon.current_fire_mode

            # 전자동 모드 - 계속 발사
            if current_mode == FIRE_MODE_AUTO:
                self.ranged_attack()

            # 점사 모드 - 설정된 발수만큼 발사
            elif current_mode == FIRE_MODE_BURST:
                if (self.current_weapon.burst_shots_fired < self.current_weapon.burst_count and
                    self.current_weapon.burst_cooldown <= 0):
                    self.ranged_attack()
                    self.current_weapon.burst_shots_fired += 1
                    self.current_weapon.burst_cooldown = self.current_weapon.burst_delay

                    # 점사 완료 후 잠시 대기
                    if self.current_weapon.burst_shots_fired >= self.current_weapon.burst_count:
                        self.current_weapon.burst_cooldown = 0.5  # 점사 후 딜레이

    def cycle_fire_mode(self):
        """발사 모드 전환"""
        new_mode = self.current_weapon.cycle_fire_mode()
        if new_mode:
            print(f"[Player] 발사 모드 변경: {self.current_weapon.get_fire_mode_name()}")
        else:
            print("[Player] 이 무기는 발사 모드를 변경할 수 없습니다.")

    def install_attachment(self, attachment_id):
        """부착물 장착"""
        success = self.current_weapon.install_attachment(attachment_id)
        if success:
            # UI 업데이트
            self.game.update_weapon_ui()
        return success

    def remove_attachment(self, slot):
        """부착물 제거"""
        success = self.current_weapon.remove_attachment(slot)
        if success:
            # UI 업데이트
            self.game.update_weapon_ui()
        return success

    def repair_weapon(self, amount=None):
        """무기 수리"""
        old_durability = self.current_weapon.get_durability_percentage()
        new_durability = self.current_weapon.repair(amount)
        print(f"[Player] {self.current_weapon.name} 수리: {old_durability}% -> {new_durability}%")
        self.game.update_weapon_ui()
        return new_durability

    def get_weapon_info(self):
        """현재 무기 정보 반환"""
        return self.current_weapon.get_full_info()

    def toggle_zoom(self):
        """줌 토글"""
        self.is_zoomed = not self.is_zoomed

        # FOV 변경 (렌즈 객체 사용)
        lens = self.game.camLens
        if self.is_zoomed:
            # 줌 상태: FOV 감소
            lens.setFov(lens.getFov() * self.current_weapon.zoom_fov_reduction)
        else:
            # 일반 상태: FOV 복구
            lens.setFov(lens.getFov() / self.current_weapon.zoom_fov_reduction)

        # 총기 UI 업데이트
        self.game.update_gun_ui(self.is_zoomed)

        print(f"[Player] Zoom {'ON' if self.is_zoomed else 'OFF'}")

    def _apply_recoil(self, recoil_amount):
        """반동 적용"""
        # 상하 반동
        self.recoil_pitch += recoil_amount

        # 카메라에 즉시 적용
        self.camera_node.setP(self.pitch + self.recoil_pitch)

        # 조준선 흔들림 효과 (랜덤 방향)
        recoil_multiplier = self.current_weapon.recoil_zoom_multiplier if self.is_zoomed else 1.0
        recoil_spread = 0.015 * recoil_multiplier * (recoil_amount / 3.0)  # 무기 반동에 비례
        offset_x = (random.random() - 0.5) * 2 * recoil_spread
        offset_y = (random.random() - 0.5) * 2 * recoil_spread * 0.5
        self.game.crosshair_offset[0] += offset_x
        self.game.crosshair_offset[1] += offset_y

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
        if not self.current_weapon.can_reload(self.is_reloading):
            return

        self.is_reloading = True

        print(f"[Player] Reloading... ({self.current_weapon.reload_time}s)")

        # 재장전 완료 후 탄약 채우기
        self.game.taskMgr.doMethodLater(
            self.current_weapon.reload_time,
            self._finish_reload,
            'reload_weapon'
        )

    def _finish_reload(self, task):
        """재장전 완료"""
        self.current_weapon.reload()
        self.is_reloading = False

        # 재장전 완료 사운드 재생
        self.game.sound.play('gun_reload')

        print(f"[Player] Reloaded! Ammo: {self.current_weapon.get_ammo_display()}")

        return None

    def _update_projectiles(self, dt):
        """투사체 업데이트"""
        for proj in self.projectiles[:]:
            # 이동
            proj['node'].setPos(
                proj['node'].getPos() + proj['direction'] * proj['speed'] * dt
            )

            # 총알 데미지 가져오기
            bullet_damage = proj.get('damage', 25)

            # 표적 충돌 체크
            hit_target = self.game.targets.check_bullet_collisions(proj['node'].getPos())
            if hit_target:
                # 표적에 맞으면 총알 제거
                proj['node'].removeNode()
                self.projectiles.remove(proj)
                continue

            # 적 충돌 체크 (데미지 전달)
            hit_enemy, is_headshot = self.game.enemies.check_bullet_collisions(
                proj['node'].getPos(), bullet_damage
            )
            if hit_enemy:
                # 크리티컬/헤드샷 효과 로그
                is_crit = proj.get('is_crit', False)
                if is_crit:
                    print(f"[Player] CRITICAL HIT on {hit_enemy.enemy_type}!")
                if is_headshot:
                    print(f"[Player] HEADSHOT on {hit_enemy.enemy_type}!")

                # 적에 맞으면 총알 제거
                proj['node'].removeNode()
                self.projectiles.remove(proj)
                continue

            # 수명 감소
            proj['lifetime'] -= dt

            # 수명 종료시 제거
            if proj['lifetime'] <= 0:
                proj['node'].removeNode()
                self.projectiles.remove(proj)

    def get_position(self):
        """플레이어 위치 반환"""
        return self.node.getPos()

    def _update_stamina(self, dt):
        """스태미나 업데이트"""
        # 이동 중인지 체크
        is_moving = any(self.moving.values())

        if self.is_running and is_moving and self.stamina > 0:
            # 달리기 중: 스태미나 소모
            self.stamina -= self.stamina_drain_rate * dt
            if self.stamina < 0:
                self.stamina = 0
                # 스태미나가 고갈되면 걷기로 전환
                self.is_running = False
                self._update_speed()
            self.stamina_regen_timer = 0.0  # 재생 타이머 리셋
        else:
            # 달리기 중이 아니면 스태미나 재생
            if self.stamina_regen_timer < self.stamina_regen_delay:
                self.stamina_regen_timer += dt
            else:
                # 재생 지연 후 스태미나 회복
                self.stamina += self.stamina_regen_rate * dt
                if self.stamina > self.max_stamina:
                    self.stamina = self.max_stamina

    def _update_crouch_height(self, dt):
        """숨쉬기 높이 업데이트 (부드러운 전환)"""
        target_height = self.crouch_eye_height if self.is_crouching else self.eye_height

        # 현재 높이에서 목표 높이로 부드럽게 전환
        diff = target_height - self.current_eye_height
        if abs(diff) > 0.01:
            self.current_eye_height += diff * self.crouch_transition_speed * dt
            self.camera_node.setZ(self.current_eye_height)
        else:
            # 목표에 도달하면 정확히 설정
            self.current_eye_height = target_height
            self.camera_node.setZ(self.current_eye_height)

    def cleanup(self):
        """정리"""
        for proj in self.projectiles:
            proj['node'].removeNode()
        self.projectiles.clear()
        self.node.removeNode()

    def add_resource(self, resource_type, amount):
        """인벤토리에 리소스 추가"""
        if resource_type in self.inventory:
            self.inventory[resource_type] += amount
            print(f"[Player] {resource_type} +{amount} (총: {self.inventory[resource_type]})")
            return True
        return False

    def get_resource_count(self, resource_type):
        """리소스 개수 반환"""
        return self.inventory.get(resource_type, 0)

    def use_resources(self, recipe):
        """조합에 필요한 리소스 사용"""
        for resource_type, amount in recipe.items():
            if self.get_resource_count(resource_type) < amount:
                return False  # 리소스 부족

        # 리소스 소모
        for resource_type, amount in recipe.items():
            self.inventory[resource_type] -= amount

        return True

    def craft_item(self, item_type):
        """아이템 조합"""
        # 조합 레시피
        recipes = {
            'ladder': {'wood': 10},           # 사다리: 나무 10개
            'wall': {'wood': 15, 'stone': 5}, # 벽: 나무 15개 + 돌 5개
            'furnace': {'stone': 20},         # 화로: 돌 20개
            'campfire': {'wood': 5, 'stone': 3}, # 모닥불: 나무 5개 + 돌 3개
        }

        if item_type not in recipes:
            print(f"[Player] 알 수 없는 조합 아이템: {item_type}")
            return False

        recipe = recipes[item_type]

        # 리소스 확인 및 소모
        if self.use_resources(recipe):
            print(f"[Player] 조합 성공: {item_type}")
            return True
        else:
            print(f"[Player] 조합 실패: 리소스 부족 ({item_type})")
            return False

    # ===== 도구 시스템 =====

    def add_tool(self, tool):
        """도구를 첫 번째 빈 슬롯에 추가"""
        for i in range(len(self.tool_slots)):
            if self.tool_slots[i] is None:
                self.tool_slots[i] = tool
                print(f"[Player] 도구 추가: {tool.name} -> 슬롯 {i}")
                return True
        print("[Player] 인벤토리가 가득 찼습니다!")
        return False

    def get_tool_at_slot(self, slot_index):
        """특정 슬롯의 도구 반환"""
        if 0 <= slot_index < len(self.tool_slots):
            return self.tool_slots[slot_index]
        return None

    def equip_tool(self, slot_index):
        """슬롯에서 도구 장착"""
        tool = self.get_tool_at_slot(slot_index)
        if tool and not tool.broken:
            self.current_tool = tool
            self.current_tool_index = slot_index
            print(f"[Player] 도구 장착: {tool.name}")
            return True
        elif tool and tool.broken:
            print("[Player] 고장난 도구는 장착할 수 없습니다!")
            return False
        print(f"[Player] 슬롯 {slot_index}가 비어있거나 잘못되었습니다.")
        return False

    def drop_current_tool(self):
        """현재 장착한 도구 드롭"""
        if self.current_tool:
            player_pos = self.node.getPos()

            # 플레이어 앞쪽에 드롭
            import math
            heading_rad = math.radians(self.heading)
            drop_pos = player_pos + Vec3(
                -math.sin(heading_rad) * 2,
                math.cos(heading_rad) * 2,
                0
            )

            # 바닥 아이템 생성
            self.game.ground_items.drop_item(
                drop_pos,
                'tool',
                self.current_tool
            )

            # 인벤토리에서 제거
            self.tool_slots[self.current_tool_index] = None
            self.current_tool = None
            self.current_tool_index = -1

            print("[Player] 도구 드롭 완료!")
            return True
        print("[Player] 드롭할 도구가 없습니다.")
        return False

    def get_tool_slots(self):
        """모든 도구 슬롯 반환"""
        return [t for t in self.tool_slots if t is not None]

    def use_current_tool(self, resource_type):
        """현재 도구 사용 (채광)"""
        if self.current_tool and not self.current_tool.broken:
            success = self.current_tool.use()
            if success:
                bonus = self.current_tool.get_gather_bonus(resource_type)
                return bonus
            else:
                print("[Player] 도구가 고장났습니다!")
        return {'speed': 1.0, 'amount': 1.0}

    def repair_current_tool(self):
        """현재 도구 수리 (리소스 사용)"""
        if self.current_tool:
            wood_cost = 3
            stone_cost = 2

            if (self.get_resource_count('wood') >= wood_cost and
                self.get_resource_count('stone') >= stone_cost):
                self.use_resources({'wood': wood_cost, 'stone': stone_cost})
                old_durability = self.current_tool.get_durability_percentage()
                new_durability = self.current_tool.repair()
                print(f"[Player] 도구 수리: {old_durability}% -> {new_durability}%")
                return True
            else:
                print("[Player] 도구 수리에 리소스가 부족합니다!")
        else:
            print("[Player] 수리할 도구가 없습니다.")
        return False

    def unequip_current_tool(self):
        """현재 도구 장착 해제"""
        if self.current_tool:
            print(f"[Player] 도구 장착 해제: {self.current_tool.name}")
            self.current_tool = None
            self.current_tool_index = -1
            return True
        return False

"""
무기 시스템
다양한 무기 타입과 그 속성을 정의
"""
import math
import random
from panda3d.core import Vec3, CardMaker, TransparencyAttrib


# 발사 모드
FIRE_MODE_SEMI = "semi"       # 단발
FIRE_MODE_BURST = "burst"     # 점사 (3발)
FIRE_MODE_AUTO = "auto"       # 전자동


class Attachment:
    """부착물 클래스"""

    ATTACHMENT_TYPES = {
        # 스코프 계열
        'red_dot': {
            'name': 'Red Dot Sight',
            'type': 'scope',
            'zoom_bonus': 0.9,      # 줌 FOV 감소율 보너스 (작을수록 좋음)
            'spread_bonus': 0.85,   # 정확도 보너스
            'description': '단순하고 빠른 조준경'
        },
        'acog': {
            'name': 'ACOG Scope',
            'type': 'scope',
            'zoom_bonus': 0.7,
            'spread_bonus': 0.7,
            'description': '중거리 배율 조준경'
        },
        'sniper_scope': {
            'name': 'Sniper Scope',
            'type': 'scope',
            'zoom_bonus': 0.3,
            'spread_bonus': 0.4,
            'description': '고배율 저격용 조준경'
        },
        # 손잡이 계열
        'foregrip': {
            'name': 'Foregrip',
            'type': 'grip',
            'recoil_bonus': 0.7,    # 반동 감소
            'spread_bonus': 0.9,
            'description': '수직 안정성 향상'
        },
        'angled_grip': {
            'name': 'Angled Grip',
            'type': 'grip',
            'recoil_bonus': 0.85,
            'fire_rate_bonus': 0.9, # 발사속도 보너스
            'description': '빠른 발사 속도 향상'
        },
        # 총구 부착물
        'suppressor': {
            'name': 'Suppressor',
            'type': 'muzzle',
            'damage_bonus': 0.95,    # 약간의 데미지 감소
            'spread_bonus': 0.85,
            'description': '소음기 (데미지 소폭 감소)'
        },
        'compensator': {
            'name': 'Compensator',
            'type': 'muzzle',
            'recoil_bonus': 0.6,    # 반동 크게 감소
            'spread_bonus': 1.1,    # 정확도 소폭 감소
            'description': '반동 보정기'
        },
        'muzzle_brake': {
            'name': 'Muzzle Brake',
            'type': 'muzzle',
            'recoil_bonus': 0.75,
            'description': '총구 제동기'
        },
        # 탄창
        'extended_mag': {
            'name': 'Extended Mag',
            'type': 'magazine',
            'magazine_bonus': 1.5,   # 탄창 크기 증가
            'reload_penalty': 1.2,   # 재장전 시간 증가
            'description': '대형 탄창 (재장전 느려짐)'
        },
        'fast_mag': {
            'name': 'Fast Mag',
            'type': 'magazine',
            'reload_bonus': 0.7,     # 재장전 시간 감소
            'description': '빠른 재장전 탄창'
        }
    }

    def __init__(self, attachment_id):
        if attachment_id not in self.ATTACHMENT_TYPES:
            raise ValueError(f"Unknown attachment: {attachment_id}")

        self.id = attachment_id
        self.data = self.ATTACHMENT_TYPES[attachment_id]
        self.name = self.data['name']
        self.type = self.data['type']

    def get_stat_bonus(self, stat_name):
        """특정 스탯 보너스 반환"""
        key = f'{stat_name}_bonus'
        if key in self.data:
            return self.data[key]
        # 패널티 체크
        key = f'{stat_name}_penalty'
        if key in self.data:
            return self.data[key]
        return 1.0  # 기본값 (변화 없음)

    def __repr__(self):
        return f"Attachment({self.name})"


class Weapon:
    """무기 기본 클래스"""

    def __init__(self, name, weapon_type):
        self.name = name
        self.weapon_type = weapon_type

        # 발사 속성 (기본값)
        self.base_fire_rate = 0.15  # 기본 발사 속도
        self.base_damage = 25       # 기본 데미지
        self.base_bullet_speed = 100.0
        self.base_spread = 0.5
        self.base_recoil = 3.0

        # 현재 발사 속성 (부착물 보정 적용 후)
        self.fire_rate = self.base_fire_rate
        self.damage = self.base_damage
        self.bullet_speed = self.base_bullet_speed
        self.spread = self.base_spread
        self.recoil = self.base_recoil

        # 발사 모드
        self.fire_modes = [FIRE_MODE_AUTO]  # 사용 가능한 발사 모드
        self.current_fire_mode = FIRE_MODE_AUTO
        self.burst_count = 3  # 점사 시 발사 수
        self.burst_delay = 0.15  # 점사 간 발사 간격

        # 탄창 시스템
        self.base_magazine_size = 30
        self.magazine_size = self.base_magazine_size
        self.current_ammo = self.magazine_size
        self.total_ammo = 300
        self.base_reload_time = 2.0
        self.reload_time = self.base_reload_time

        # 재장전
        self.is_reloading = False

        # 줌 시스템
        self.base_zoom_fov_reduction = 0.5
        self.zoom_fov_reduction = self.base_zoom_fov_reduction
        self.recoil_zoom_multiplier = 0.4

        # 시각적 속성
        self.color = (1.0, 0.8, 0.0)
        self.bullet_size = (-0.3, 0.3, -0.15, 0.15)

        # 내구도 시스템
        self.max_durability = 1000.0
        self.durability = self.max_durability
        self.durability_decay_per_shot = 1.0  # 발사 시 내구도 감소
        self.durability_warning_threshold = 0.2  # 20% 이하시 경고
        self.broken = False

        # 부착물 시스템
        self.attachments = {
            'scope': None,
            'grip': None,
            'muzzle': None,
            'magazine': None
        }

        # 크리티컬 시스템
        self.crit_chance = 0.05  # 5% 크리티컬 확률
        self.crit_multiplier = 1.5  # 크리티컬 데미지 배율

        # 점사 카운터
        self.burst_shots_fired = 0
        self.burst_cooldown = 0.0

    def can_fire(self, fire_cooldown):
        """발사 가능 여부 체크"""
        if self.broken:
            return False
        if self.current_ammo <= 0 or fire_cooldown <= 0:
            return True
        return False

    def fire(self, start_pos, heading, pitch, is_zoomed, game, is_headshot=False):
        """
        발사 처리
        Returns: (bullet_data, recoil_amount, is_crit)
        """
        self.current_ammo -= 1

        # 내구도 감소
        self.durability -= self.durability_decay_per_shot
        if self.durability <= 0:
            self.durability = 0
            self.broken = True
            print(f"[Weapon] {self.name} 내구도 소진! 고장남!")

        # 총알 생성
        cm = CardMaker('bullet')
        cm.setFrame(*self.bullet_size)
        bullet = game.render.attachNewNode(cm.generate())

        # 항상 카메라를 향하도록 (Billboarding)
        bullet.setBillboardPointEye()
        bullet.setTransparency(TransparencyAttrib.MAlpha)

        # 텍스처 적용 시도
        try:
            bullet_texture = game.loader.loadTexture("textures/bullet.png")
            if bullet_texture:
                bullet.setTexture(bullet_texture)
            else:
                bullet.setColor(*self.color, 1.0)
        except:
            bullet.setColor(*self.color, 1.0)

        bullet.setPos(start_pos)

        # 발사 방향 계산
        direction = self._calculate_direction(heading, pitch, is_zoomed)

        # 기본 데미지
        damage = self.damage

        # 크리티컬 판정
        is_crit = False
        if random.random() < self.crit_chance:
            damage *= self.crit_multiplier
            is_crit = True

        # 헤드샷 보너스
        if is_headshot:
            damage *= 2.0

        # 내구도에 따른 데미지 페널티
        durability_ratio = self.durability / self.max_durability
        if durability_ratio < self.durability_warning_threshold:
            damage *= 0.7  # 30% 데미지 감소

        bullet_data = {
            'node': bullet,
            'direction': direction,
            'speed': self.bullet_speed,
            'lifetime': 3.0,
            'damage': int(damage),
            'is_crit': is_crit,
            'is_headshot': is_headshot
        }

        # 반동 계산
        recoil_multiplier = self.recoil_zoom_multiplier if is_zoomed else 1.0
        recoil_amount = self.recoil * recoil_multiplier * (0.5 + random.random() * 0.5)

        return bullet_data, recoil_amount, is_crit

    def cycle_fire_mode(self):
        """발사 모드 순환"""
        if len(self.fire_modes) <= 1:
            return None

        current_idx = self.fire_modes.index(self.current_fire_mode)
        next_idx = (current_idx + 1) % len(self.fire_modes)
        self.current_fire_mode = self.fire_modes[next_idx]

        # 점사 카운터 리셋
        self.burst_shots_fired = 0
        self.burst_cooldown = 0.0

        return self.current_fire_mode

    def get_fire_mode_name(self):
        """발사 모드 이름 반환"""
        mode_names = {
            FIRE_MODE_SEMI: "SEMI",
            FIRE_MODE_BURST: "BURST",
            FIRE_MODE_AUTO: "AUTO"
        }
        return mode_names.get(self.current_fire_mode, "UNKNOWN")

    def install_attachment(self, attachment_id):
        """부착물 장착"""
        attachment = Attachment(attachment_id)
        slot = attachment.type

        # 기존 부착물 제거
        if self.attachments[slot] is not None:
            print(f"[Weapon] {slot} 슬롯의 기존 부착물 제거됨")

        self.attachments[slot] = attachment
        self._recalculate_stats()
        print(f"[Weapon] {attachment.name} 장착 완료!")
        return True

    def remove_attachment(self, slot):
        """부착물 제거"""
        if slot in self.attachments and self.attachments[slot] is not None:
            removed = self.attachments[slot]
            self.attachments[slot] = None
            self._recalculate_stats()
            print(f"[Weapon] {removed.name} 제거됨")
            return True
        return False

    def _recalculate_stats(self):
        """부착물 효과 적용하여 스탯 재계산"""
        # 기본값으로 리셋
        self.fire_rate = self.base_fire_rate
        self.damage = self.base_damage
        self.spread = self.base_spread
        self.recoil = self.base_recoil
        self.zoom_fov_reduction = self.base_zoom_fov_reduction
        self.magazine_size = self.base_magazine_size
        self.reload_time = self.base_reload_time

        # 모든 부착물 보너스 적용
        for attachment in self.attachments.values():
            if attachment is None:
                continue

            self.damage *= attachment.get_stat_bonus('damage')
            self.fire_rate *= attachment.get_stat_bonus('fire_rate')
            self.spread *= attachment.get_stat_bonus('spread')
            self.recoil *= attachment.get_stat_bonus('recoil')
            self.zoom_fov_reduction *= attachment.get_stat_bonus('zoom')
            self.magazine_size = int(self.magazine_size * attachment.get_stat_bonus('magazine'))
            self.reload_time *= attachment.get_stat_bonus('reload')

        # 탄창 크기가 변경되면 현재 탄환도 조정
        if self.current_ammo > self.magazine_size:
            self.current_ammo = self.magazine_size

    def get_durability_percentage(self):
        """내구도 퍼센트 반환"""
        return int((self.durability / self.max_durability) * 100)

    def repair(self, amount=None):
        """수리"""
        if amount is None:
            # 완전 수리
            self.durability = self.max_durability
        else:
            self.durability = min(self.max_durability, self.durability + amount)

        if self.broken and self.durability > 0:
            self.broken = False
            print(f"[Weapon] {self.name} 수리 완료!")

        return self.get_durability_percentage()

    def get_attachments_info(self):
        """부착물 정보 반환"""
        info = []
        for slot, attachment in self.attachments.items():
            if attachment:
                info.append(f"{slot}: {attachment.name}")
        return info if info else ["No attachments"]

    def get_full_info(self):
        """무기 전체 정보 반환"""
        return {
            'name': self.name,
            'damage': self.damage,
            'fire_rate': self.fire_rate,
            'spread': self.spread,
            'recoil': self.recoil,
            'magazine_size': self.magazine_size,
            'current_ammo': self.current_ammo,
            'total_ammo': self.total_ammo,
            'reload_time': self.reload_time,
            'durability': self.get_durability_percentage(),
            'is_broken': self.broken,
            'fire_mode': self.get_fire_mode_name(),
            'attachments': self.get_attachments_info()
        }

    def _calculate_direction(self, heading, pitch, is_zoomed):
        """발사 방향 계산 (산탄 적용)"""
        heading_rad = math.radians(heading)
        pitch_rad = math.radians(pitch)

        # 기본 방향
        base_direction = Vec3(
            -math.sin(heading_rad) * math.cos(pitch_rad),
            math.cos(heading_rad) * math.cos(pitch_rad),
            math.sin(pitch_rad)
        )
        base_direction.normalize()

        # 줌 시 정확도 증가
        effective_spread = self.spread * (0.5 if is_zoomed else 1.0)
        spread_rad = math.radians(effective_spread)

        spread_h = (random.random() - 0.5) * 2 * spread_rad
        spread_v = (random.random() - 0.5) * 2 * spread_rad

        # 편차 적용
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

        return direction

    def can_reload(self, is_reloading):
        """재장전 가능 여부"""
        return not is_reloading and self.total_ammo > 0 and self.current_ammo < self.magazine_size

    def reload(self):
        """재장전 실행 - 탄약 반환"""
        ammo_needed = self.magazine_size - self.current_ammo
        ammo_to_add = min(ammo_needed, self.total_ammo)
        self.current_ammo += ammo_to_add
        self.total_ammo -= ammo_to_add
        return ammo_to_add

    def add_ammo(self, amount):
        """탄약 추가"""
        self.total_ammo += amount

    def get_ammo_display(self):
        """탄약 표시용 문자열 반환"""
        return f"{self.current_ammo}/{self.magazine_size}"


class Pistol(Weapon):
    """권총 - 반자동, 정확함, 낮은 데미지"""

    def __init__(self):
        super().__init__("Pistol", "pistol")
        # 기본 스탯
        self.base_fire_rate = 0.2
        self.base_damage = 20
        self.base_bullet_speed = 120.0
        self.base_spread = 0.2
        self.base_recoil = 1.5
        self.base_magazine_size = 12
        self.total_ammo = 120
        self.base_reload_time = 1.5
        self.base_zoom_fov_reduction = 0.7
        self.recoil_zoom_multiplier = 0.3
        self.color = (0.7, 0.7, 0.7)
        self.bullet_size = (-0.2, 0.2, -0.1, 0.1)

        # 발사 모드 - 단발만
        self.fire_modes = [FIRE_MODE_SEMI]
        self.current_fire_mode = FIRE_MODE_SEMI

        # 내구도
        self.max_durability = 800.0
        self.durability = self.max_durability
        self.durability_decay_per_shot = 0.5

        # 크리티컬 - 정확한 무기라 확률 높음
        self.crit_chance = 0.10
        self.crit_multiplier = 1.8

        # 초기 스탯 적용
        self._recalculate_stats()
        self.current_ammo = self.magazine_size


class Rifle(Weapon):
    """소총 - 전자동 발사, 밸런스 좋음"""

    def __init__(self):
        super().__init__("Rifle", "rifle")
        # 기본 스탯
        self.base_fire_rate = 0.1
        self.base_damage = 25
        self.base_bullet_speed = 100.0
        self.base_spread = 0.5
        self.base_recoil = 3.0
        self.base_magazine_size = 30
        self.total_ammo = 300
        self.base_reload_time = 2.0
        self.base_zoom_fov_reduction = 0.5
        self.recoil_zoom_multiplier = 0.4
        self.color = (1.0, 0.8, 0.0)
        self.bullet_size = (-0.3, 0.3, -0.15, 0.15)

        # 발사 모드 - 단발, 점사, 전자동
        self.fire_modes = [FIRE_MODE_SEMI, FIRE_MODE_BURST, FIRE_MODE_AUTO]
        self.current_fire_mode = FIRE_MODE_AUTO
        self.burst_count = 3
        self.burst_delay = 0.1

        # 내구도
        self.max_durability = 1000.0
        self.durability = self.max_durability
        self.durability_decay_per_shot = 1.0

        # 크리티컬
        self.crit_chance = 0.05
        self.crit_multiplier = 1.5

        # 초기 스탯 적용
        self._recalculate_stats()
        self.current_ammo = self.magazine_size


class Shotgun(Weapon):
    """산탄총 - 근거리, 다발 사격, 높은 데미지"""

    def __init__(self):
        super().__init__("Shotgun", "shotgun")
        # 기본 스탯
        self.base_fire_rate = 0.6
        self.base_damage = 15
        self.base_bullet_speed = 80.0
        self.base_spread = 2.0
        self.base_recoil = 8.0
        self.base_magazine_size = 8
        self.total_ammo = 80
        self.base_reload_time = 2.5
        self.base_zoom_fov_reduction = 0.8
        self.recoil_zoom_multiplier = 0.8
        self.color = (1.0, 0.5, 0.0)
        self.bullet_size = (-0.25, 0.25, -0.12, 0.12)
        self.pellet_count = 6

        # 발사 모드 - 단발만
        self.fire_modes = [FIRE_MODE_SEMI]
        self.current_fire_mode = FIRE_MODE_SEMI

        # 내구도
        self.max_durability = 600.0
        self.durability = self.max_durability
        self.durability_decay_per_shot = 2.0

        # 크리티컬
        self.crit_chance = 0.15
        self.crit_multiplier = 1.3

        # 초기 스탯 적용
        self._recalculate_stats()
        self.current_ammo = self.magazine_size

    def fire(self, start_pos, heading, pitch, is_zoomed, game, is_headshot=False):
        """산탄총 발사 - 여러 발의 총알"""
        self.current_ammo -= 1

        # 내구도 감소
        self.durability -= self.durability_decay_per_shot
        if self.durability <= 0:
            self.durability = 0
            self.broken = True
            print(f"[Weapon] {self.name} 내구도 소진! 고장남!")

        bullets = []
        total_recoil = 0

        # 여러 발의 산탄 발사
        for _ in range(self.pellet_count):
            cm = CardMaker('bullet')
            cm.setFrame(*self.bullet_size)
            bullet = game.render.attachNewNode(cm.generate())
            bullet.setBillboardPointEye()
            bullet.setTransparency(TransparencyAttrib.MAlpha)

            try:
                bullet_texture = game.loader.loadTexture("textures/bullet.png")
                if bullet_texture:
                    bullet.setTexture(bullet_texture)
                else:
                    bullet.setColor(*self.color, 1.0)
            except:
                bullet.setColor(*self.color, 1.0)

            bullet.setPos(start_pos)
            direction = self._calculate_direction(heading, pitch, is_zoomed)

            # 데미지 계산
            damage = self.damage

            # 크리티컬 판정
            is_crit = False
            if random.random() < self.crit_chance:
                damage *= self.crit_multiplier
                is_crit = True

            # 헤드샷 보너스
            if is_headshot:
                damage *= 2.0

            # 내구도 페널티
            durability_ratio = self.durability / self.max_durability
            if durability_ratio < self.durability_warning_threshold:
                damage *= 0.7

            bullet_data = {
                'node': bullet,
                'direction': direction,
                'speed': self.bullet_speed,
                'lifetime': 3.0,
                'damage': int(damage),
                'is_crit': is_crit,
                'is_headshot': is_headshot
            }
            bullets.append(bullet_data)

        # 반동 계산
        recoil_multiplier = self.recoil_zoom_multiplier if is_zoomed else 1.0
        total_recoil = self.recoil * recoil_multiplier * (0.8 + random.random() * 0.4)

        return bullets, total_recoil


class Sniper(Weapon):
    """저격총 - 높은 데미지, 강한 줌, 긴 재장전"""

    def __init__(self):
        super().__init__("Sniper", "sniper")
        # 기본 스탯
        self.base_fire_rate = 1.0
        self.base_damage = 100
        self.base_bullet_speed = 150.0
        self.base_spread = 0.05
        self.base_recoil = 10.0
        self.base_magazine_size = 5
        self.total_ammo = 50
        self.base_reload_time = 3.0
        self.base_zoom_fov_reduction = 0.2
        self.recoil_zoom_multiplier = 0.2
        self.color = (0.0, 1.0, 0.0)
        self.bullet_size = (-0.4, 0.4, -0.2, 0.2)

        # 발사 모드 - 단발만
        self.fire_modes = [FIRE_MODE_SEMI]
        self.current_fire_mode = FIRE_MODE_SEMI

        # 내구도
        self.max_durability = 500.0
        self.durability = self.max_durability
        self.durability_decay_per_shot = 3.0  # 강력한 무기라 빨리 닳음

        # 크리티컬 - 헤드샷에 최적화
        self.crit_chance = 0.20  # 높은 확률
        self.crit_multiplier = 2.0  # 높은 배율

        # 초기 스탯 적용
        self._recalculate_stats()
        self.current_ammo = self.magazine_size


# 무기 생성 팩토리 함수
def create_weapon(weapon_type):
    """무기 타입에 따라 무기 인스턴스 생성"""
    weapons = {
        'pistol': Pistol,
        'rifle': Rifle,
        'shotgun': Shotgun,
        'sniper': Sniper,
    }

    weapon_class = weapons.get(weapon_type.lower())
    if weapon_class:
        return weapon_class()
    else:
        print(f"[Weapon] 알 수 없는 무기 타입: {weapon_type}")
        return Rifle()  # 기본값


# 모든 무기 타입 리스트
WEAPON_TYPES = ['pistol', 'rifle', 'shotgun', 'sniper']

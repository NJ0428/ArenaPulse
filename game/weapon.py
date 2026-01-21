"""
무기 시스템
다양한 무기 타입과 그 속성을 정의
"""
import math
import random
from panda3d.core import Vec3, CardMaker, TransparencyAttrib


class Weapon:
    """무기 기본 클래스"""

    def __init__(self, name, weapon_type):
        self.name = name
        self.weapon_type = weapon_type

        # 발사 속성
        self.fire_rate = 0.15  # 발사 속도 (초)
        self.damage = 25  # 데미지
        self.bullet_speed = 100.0  # 탄속
        self.spread = 0.5  # 정확도 (낮을수록 정확, 단위: 도)
        self.recoil = 3.0  # 반동 (상하)
        self.auto_fire = True  # 자동 발사 가능 여부

        # 탄창 시스템
        self.magazine_size = 30  # 탄창 크기
        self.current_ammo = self.magazine_size  # 현재 탄창
        self.total_ammo = 300  # 전체 탄약

        # 재장전
        self.reload_time = 2.0  # 재장전 시간

        # 줌 시스템
        self.zoom_fov_reduction = 0.5  # 줌 시 FOV 감소 비율
        self.recoil_zoom_multiplier = 0.4  # 줌 시 반동 감소 비율

        # 시각적 속성
        self.color = (1.0, 0.8, 0.0)  # 총알 색상 (R, G, B)
        self.bullet_size = (-0.3, 0.3, -0.15, 0.15)  # 총알 크기

    def can_fire(self, fire_cooldown):
        """발사 가능 여부 체크"""
        return self.current_ammo > 0 and fire_cooldown <= 0

    def fire(self, start_pos, heading, pitch, is_zoomed, game):
        """
        발사 처리
        Returns: (bullet_data, recoil_amount)
        """
        self.current_ammo -= 1

        # 총알 생성
        cm = CardMaker('bullet')
        cm.setFrame(*self.bullet_size)
        bullet = game.render.attachNewNode(cm.generate())

        # 항상 카메라를 향하도록 (Billboarding)
        bullet.setBillboardPointEye()
        bullet.setTransparency(TransparencyAttrib.MAlpha)

        # 텍스처 적용 시도
        try:
            try:
                bullet_texture = game.loader.loadTexture("textures/bullet.png")
                if bullet_texture:
                    bullet.setTexture(bullet_texture)
                else:
                    bullet.setColor(*self.color, 1.0)
            except:
                bullet.setColor(*self.color, 1.0)
        except:
            bullet.setColor(*self.color, 1.0)

        bullet.setPos(start_pos)

        # 발사 방향 계산
        direction = self._calculate_direction(heading, pitch, is_zoomed)

        bullet_data = {
            'node': bullet,
            'direction': direction,
            'speed': self.bullet_speed,
            'lifetime': 3.0,
            'damage': self.damage
        }

        # 반동 계산
        recoil_multiplier = self.recoil_zoom_multiplier if is_zoomed else 1.0
        recoil_amount = self.recoil * recoil_multiplier * (0.5 + random.random() * 0.5)

        return bullet_data, recoil_amount

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
        self.fire_rate = 0.2  # 발사 속도
        self.damage = 20  # 낮은 데미지
        self.bullet_speed = 120.0  # 빠른 탄속
        self.spread = 0.2  # 매우 정확함
        self.recoil = 1.5  # 낮은 반동
        self.auto_fire = False  # 반자동만
        self.magazine_size = 12  # 작은 탄창
        self.current_ammo = self.magazine_size
        self.total_ammo = 120
        self.reload_time = 1.5  # 빠른 재장전
        self.zoom_fov_reduction = 0.7  # 약한 줌
        self.recoil_zoom_multiplier = 0.3
        self.color = (0.7, 0.7, 0.7)  # 회색
        self.bullet_size = (-0.2, 0.2, -0.1, 0.1)  # 작은 총알


class Rifle(Weapon):
    """소총 -全自动발사, 밸런스 좋음"""

    def __init__(self):
        super().__init__("Rifle", "rifle")
        self.fire_rate = 0.1  # 빠른 발사 속도
        self.damage = 25  # 중간 데미지
        self.bullet_speed = 100.0  # 중간 탄속
        self.spread = 0.5  # 중간 정확도
        self.recoil = 3.0  # 중간 반동
        self.auto_fire = True  # 자동 발사
        self.magazine_size = 30
        self.current_ammo = self.magazine_size
        self.total_ammo = 300
        self.reload_time = 2.0
        self.zoom_fov_reduction = 0.5
        self.recoil_zoom_multiplier = 0.4
        self.color = (1.0, 0.8, 0.0)  # 금색
        self.bullet_size = (-0.3, 0.3, -0.15, 0.15)


class Shotgun(Weapon):
    """산탄총 - 근거리, 다발 사격, 높은 데미지"""

    def __init__(self):
        super().__init__("Shotgun", "shotgun")
        self.fire_rate = 0.6  # 느린 발사 속도
        self.damage = 15  # 낮은 개체 데미지
        self.bullet_speed = 80.0  # 느린 탄속
        self.spread = 2.0  # 매우 낮은 정확도 (넓은 산탄)
        self.recoil = 8.0  # 매우 높은 반동
        self.auto_fire = False  # 반자동
        self.magazine_size = 8  # 작은 탄창
        self.current_ammo = self.magazine_size
        self.total_ammo = 80
        self.reload_time = 2.5  # 느린 재장전
        self.zoom_fov_reduction = 0.8  # 거의 줌 안됨
        self.recoil_zoom_multiplier = 0.8  # 줌 효과 적음
        self.color = (1.0, 0.5, 0.0)  # 주황색
        self.bullet_size = (-0.25, 0.25, -0.12, 0.12)
        self.pellet_count = 6  # 산탄 개수

    def fire(self, start_pos, heading, pitch, is_zoomed, game):
        """산탄총 발사 - 여러 발의 총알"""
        self.current_ammo -= 1

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

            bullet_data = {
                'node': bullet,
                'direction': direction,
                'speed': self.bullet_speed,
                'lifetime': 3.0,
                'damage': self.damage
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
        self.fire_rate = 1.0  # 매우 느린 발사 속도
        self.damage = 100  # 매우 높은 데미지
        self.bullet_speed = 150.0  # 매우 빠른 탄속
        self.spread = 0.05  # 매우 정확함
        self.recoil = 10.0  # 매우 높은 반동
        self.auto_fire = False  # 반자동
        self.magazine_size = 5  # 매우 작은 탄창
        self.current_ammo = self.magazine_size
        self.total_ammo = 50
        self.reload_time = 3.0  # 매우 느린 재장전
        self.zoom_fov_reduction = 0.2  # 매우 강한 줌
        self.recoil_zoom_multiplier = 0.2  # 줌 시 반동 크게 감소
        self.color = (0.0, 1.0, 0.0)  # 녹색
        self.bullet_size = (-0.4, 0.4, -0.2, 0.2)  # 큰 총알


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

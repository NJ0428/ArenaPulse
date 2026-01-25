"""
도구 시스템
채광/채집 도구와 그 속성을 정의
"""


class Tool:
    """도구 기본 클래스"""

    def __init__(self, name, tool_type):
        self.name = name
        self.tool_type = tool_type  # 'axe' or 'pickaxe'

        # 내구도 시스템
        self.max_durability = 500.0
        self.durability = self.max_durability
        self.durability_decay_per_use = 2.0
        self.broken = False

        # 채광 보너스
        self.gather_speed_bonus = 1.5  # 50% 더 빨리
        self.gather_amount_bonus = 1.2  # 20% 더 획득
        self.effective_resource = None  # 'wood' for axe, 'stone' for pickaxe

        # 시각적 속성
        self.color = (0.6, 0.4, 0.2)  # 갈색
        self.icon_color = (0.8, 0.6, 0.3)

    def use(self):
        """도구 사용 - 내구도 감소"""
        if self.broken:
            return False

        self.durability -= self.durability_decay_per_use
        if self.durability <= 0:
            self.durability = 0
            self.broken = True
            print(f"[Tool] {self.name} 내구도 소진! 고장남!")

        return True

    def get_gather_bonus(self, resource_type):
        """특정 리소스에 대한 채광 보너스 반환"""
        if resource_type == self.effective_resource:
            return {
                'speed': self.gather_speed_bonus,
                'amount': self.gather_amount_bonus
            }
        return {'speed': 1.0, 'amount': 1.0}

    def get_durability_percentage(self):
        """내구도 퍼센트 반환"""
        return int((self.durability / self.max_durability) * 100)

    def repair(self, amount=None):
        """도구 수리"""
        if amount is None:
            # 완전 수리
            self.durability = self.max_durability
        else:
            self.durability = min(self.max_durability, self.durability + amount)

        if self.broken and self.durability > 0:
            self.broken = False
            print(f"[Tool] {self.name} 수리 완료!")

        return self.get_durability_percentage()

    def get_full_info(self):
        """도구 전체 정보 반환"""
        return {
            'name': self.name,
            'type': self.tool_type,
            'durability': self.get_durability_percentage(),
            'max_durability': int(self.max_durability),
            'is_broken': self.broken,
            'speed_bonus': self.gather_speed_bonus,
            'amount_bonus': self.gather_amount_bonus,
            'effective_resource': self.effective_resource
        }

    def __repr__(self):
        return f"Tool({self.name}, {self.get_durability()}%)"


class Axe(Tool):
    """도끼 - 나무 채광 전용"""

    def __init__(self):
        super().__init__("Axe", "axe")
        self.effective_resource = 'wood'
        self.gather_speed_bonus = 2.0  # 2배 더 빨리
        self.gather_amount_bonus = 1.5  # 50% 더 획득
        self.max_durability = 600.0
        self.durability = self.max_durability
        self.durability_decay_per_use = 1.5
        self.color = (0.6, 0.4, 0.2)  # 갈색
        self.icon_color = (0.8, 0.6, 0.3)


class Pickaxe(Tool):
    """곡괭이 - 돌 채광 전용"""

    def __init__(self):
        super().__init__("Pickaxe", "pickaxe")
        self.effective_resource = 'stone'
        self.gather_speed_bonus = 2.0  # 2배 더 빨리
        self.gather_amount_bonus = 1.5  # 50% 더 획득
        self.max_durability = 500.0
        self.durability = self.max_durability
        self.durability_decay_per_use = 2.0  # 돌이 더 단단함
        self.color = (0.5, 0.5, 0.5)  # 회색
        self.icon_color = (0.7, 0.7, 0.7)


def create_tool(tool_type):
    """도구 타입에 따라 도구 인스턴스 생성"""
    tools = {
        'axe': Axe,
        'pickaxe': Pickaxe,
    }

    tool_class = tools.get(tool_type.lower())
    if tool_class:
        return tool_class()
    else:
        print(f"[Tool] 알 수 없는 도구 타입: {tool_type}")
        return None


# 모든 도구 타입 리스트
TOOL_TYPES = ['axe', 'pickaxe']

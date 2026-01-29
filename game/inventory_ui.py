"""
인벤토리 UI 시스템
DirectGui 기반 인벤토리 인터페이스
"""
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel,
    DGG
)
from panda3d.core import TextNode, Vec4, WindowProperties


# 조합 레시피 정의
CRAFTING_RECIPES = {
    'axe': {
        'name': 'Axe',
        'cost': {'wood': 15, 'stone': 5},
        'description': '나무 채집 도구'
    },
    'pickaxe': {
        'name': 'Pickaxe',
        'cost': {'wood': 10, 'stone': 15},
        'description': '돌 채집 도구'
    },
    'campfire': {
        'name': 'Campfire',
        'cost': {'wood': 10, 'stone': 5},
        'description': '모닥불'
    },
    'wall': {
        'name': 'Wall',
        'cost': {'wood': 20, 'stone': 10},
        'description': '방어벽'
    },
}


class InventoryUI:
    """인벤토리 GUI - 도구 및 리소스 관리"""

    def __init__(self, game):
        self.game = game
        self.is_visible = False

        # UI 컴포넌트
        self.main_frame = None
        self.tool_buttons = []
        self.resource_labels = {}
        self.crafting_buttons = []
        self.message_label = None

        # 현재 탭 (tools, crafting)
        self.current_tab = 'tools'

        self._create_ui()

    def _create_ui(self):
        """인벤토리 UI 요소 생성"""
        # 메인 프레임 (화면 중앙, 초기엔 숨김)
        self.main_frame = DirectFrame(
            pos=(0, 0, 0),
            frameSize=(-0.6, 0.6, -0.45, 0.45),
            frameColor=(0.1, 0.1, 0.1, 0.95),
            state=DGG.NORMAL
        )
        self.main_frame.hide()

        # 타이틀
        title = DirectLabel(
            parent=self.main_frame,
            pos=(0, 0, 0.40),
            text="INVENTORY (Press I to close)",
            text_scale=0.08,
            text_fg=(1, 0.8, 0.2, 1),
            frameColor=(0, 0, 0, 0)
        )

        # 탭 버튼
        self._create_tab_buttons()

        # 도구/조합 컨텐츠 영역
        self.tools_frame = DirectFrame(
            parent=self.main_frame,
            pos=(0, 0, 0),
            frameSize=(-0.55, 0.55, -0.15, 0.30),
            frameColor=(0, 0, 0, 0)
        )

        self.crafting_frame = DirectFrame(
            parent=self.main_frame,
            pos=(0, 0, 0),
            frameSize=(-0.55, 0.55, -0.20, 0.30),
            frameColor=(0, 0, 0, 0)
        )
        self.crafting_frame.hide()

        # 도구 섹션
        self._create_tools_section()

        # 조합 섹션
        self._create_crafting_section()

        # 리소스 섹션
        self._create_resources_section()

        # 메시지 라벨
        self.message_label = DirectLabel(
            parent=self.main_frame,
            pos=(0, 0, -0.40),
            text="",
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        self.message_label.hide()

        # 액션 버튼
        self._create_action_buttons()

    def _create_tools_section(self):
        """도구 인벤토리 섹션"""
        tools_label = DirectLabel(
            parent=self.tools_frame,
            pos=(-0.5, 0, 0.25),
            text="TOOLS:",
            text_scale=0.06,
            text_align=TextNode.ALeft,
            text_fg=(0.5, 0.8, 1, 1),
            frameColor=(0, 0, 0, 0)
        )

        # 도구 슬롯 (최대 6개)
        for i in range(6):
            x = -0.5 + (i % 3) * 0.35
            z = 0.15 - (i // 3) * 0.15

            btn = DirectButton(
                parent=self.tools_frame,
                pos=(x, 0, z),
                frameSize=(-0.15, 0.15, -0.1, 0.1),
                frameColor=(0.2, 0.2, 0.2, 0.8),
                text=f"[Empty {i+1}]",
                text_scale=0.04,
                text_fg=(0.5, 0.5, 0.5, 1),
                command=self._on_tool_click,
                extraArgs=[i]
            )
            self.tool_buttons.append(btn)

    def _create_resources_section(self):
        """리소스 표시 섹션"""
        resources_label = DirectLabel(
            parent=self.main_frame,
            pos=(-0.5, 0, -0.02),
            text="RESOURCES:",
            text_scale=0.06,
            text_align=TextNode.ALeft,
            text_fg=(0.5, 0.8, 1, 1),
            frameColor=(0, 0, 0, 0)
        )

        # 나무
        self.resource_labels['wood'] = DirectLabel(
            parent=self.main_frame,
            pos=(-0.5, 0, -0.09),
            text="Wood: 0",
            text_scale=0.05,
            text_align=TextNode.ALeft,
            text_fg=(0.6, 0.4, 0.2, 1),
            frameColor=(0, 0, 0, 0)
        )

        # 돌
        self.resource_labels['stone'] = DirectLabel(
            parent=self.main_frame,
            pos=(-0.5, 0, -0.15),
            text="Stone: 0",
            text_scale=0.05,
            text_align=TextNode.ALeft,
            text_fg=(0.5, 0.5, 0.5, 1),
            frameColor=(0, 0, 0, 0)
        )

    def _create_tab_buttons(self):
        """탭 버튼 생성"""
        # 도구 탭
        tools_tab = DirectButton(
            parent=self.main_frame,
            pos=(-0.35, 0, 0.32),
            frameSize=(-0.15, 0.15, -0.05, 0.05),
            frameColor=(0.3, 0.5, 0.7, 0.8),
            text="TOOLS",
            text_scale=0.045,
            command=self._switch_tab,
            extraArgs=['tools']
        )
        self.tools_tab_btn = tools_tab

        # 조합 탭
        crafting_tab = DirectButton(
            parent=self.main_frame,
            pos=(-0.05, 0, 0.32),
            frameSize=(-0.15, 0.15, -0.05, 0.05),
            frameColor=(0.3, 0.3, 0.3, 0.8),
            text="CRAFTING",
            text_scale=0.045,
            command=self._switch_tab,
            extraArgs=['crafting']
        )
        self.crafting_tab_btn = crafting_tab

    def _switch_tab(self, tab_name):
        """탭 전환"""
        self.current_tab = tab_name

        if tab_name == 'tools':
            self.tools_frame.show()
            self.crafting_frame.hide()
            self.tools_tab_btn['frameColor'] = (0.3, 0.5, 0.7, 0.8)
            self.crafting_tab_btn['frameColor'] = (0.3, 0.3, 0.3, 0.8)
        else:
            self.tools_frame.hide()
            self.crafting_frame.show()
            self.tools_tab_btn['frameColor'] = (0.3, 0.3, 0.3, 0.8)
            self.crafting_tab_btn['frameColor'] = (0.3, 0.5, 0.7, 0.8)

        # 메시지 숨기기
        self.message_label.hide()

    def _create_crafting_section(self):
        """조합 섹션"""
        # 조합 타이틀
        title = DirectLabel(
            parent=self.crafting_frame,
            pos=(-0.45, 0, 0.25),
            text="CRAFTING RECIPES:",
            text_scale=0.05,
            text_align=TextNode.ALeft,
            text_fg=(0.5, 0.8, 1, 1),
            frameColor=(0, 0, 0, 0)
        )

        # 조합 버튼 생성
        y_pos = 0.15
        for item_id, recipe in CRAFTING_RECIPES.items():
            # 비용 텍스트 생성
            cost_text = ", ".join([f"{v} {k}" for k, v in recipe['cost'].items()])

            btn = DirectButton(
                parent=self.crafting_frame,
                pos=(-0.35, 0, y_pos),
                frameSize=(-0.45, 0.45, -0.06, 0.06),
                frameColor=(0.2, 0.4, 0.2, 0.8),
                text=f"{recipe['name']}\n{cost_text}",
                text_scale=0.04,
                text_align=TextNode.ALeft,
                text_fg=(1, 1, 1, 1),
                command=self._on_craft_item,
                extraArgs=[item_id]
            )
            self.crafting_buttons.append(btn)

            y_pos -= 0.12

    def _create_action_buttons(self):
        """액션 버튼 생성"""
        # 드롭 버튼 (도구 탭에서만 표시)
        self.drop_btn = DirectButton(
            parent=self.main_frame,
            pos=(0.4, 0, -0.25),
            frameSize=(-0.12, 0.12, -0.07, 0.07),
            frameColor=(0.8, 0.3, 0.3, 0.8),
            text="DROP [G]",
            text_scale=0.045,
            command=self._on_drop_click
        )

        # 닫기 버튼
        close_btn = DirectButton(
            parent=self.main_frame,
            pos=(0, 0, -0.42),
            frameSize=(-0.2, 0.2, -0.07, 0.07),
            frameColor=(0.3, 0.3, 0.3, 0.8),
            text="CLOSE [I]",
            text_scale=0.045,
            command=self.toggle
        )

    def _on_craft_item(self, item_id):
        """조합 버튼 클릭 처리"""
        if item_id not in CRAFTING_RECIPES:
            self._show_message("알 수 없는 조합 아이템!", (1, 0.3, 0.3, 1))
            return

        recipe = CRAFTING_RECIPES[item_id]
        cost = recipe['cost']

        # 리소스 확인
        can_craft = True
        missing = []
        for res_type, amount in cost.items():
            count = self.game.player.get_resource_count(res_type)
            if count < amount:
                can_craft = False
                missing.append(f"{res_type} {amount - count}부족")

        if not can_craft:
            self._show_message(f"리소스 부족! {', '.join(missing)}", (1, 0.3, 0.3, 1))
            return

        # 리소스 사용
        self.game.player.use_resources(cost)

        # 도구 생성
        if item_id in ['axe', 'pickaxe']:
            from game.tool import create_tool
            tool = create_tool(item_id)
            if tool:
                success = self.game.player.add_tool(tool)
                if success:
                    self._show_message(f"{recipe['name']} 조합 성공!", (0.3, 1, 0.3, 1))
                else:
                    # 인벤토리 꽉 찼음 - 리소스 반환
                    for res_type, amount in cost.items():
                        self.game.player.add_resource(res_type, amount)
                    self._show_message("인벤토리가 가득 찼습니다!", (1, 0.3, 0.3, 1))
            else:
                # 도구 생성 실패 - 리소스 반환
                for res_type, amount in cost.items():
                    self.game.player.add_resource(res_type, amount)
                self._show_message("조합 실패!", (1, 0.3, 0.3, 1))
        else:
            # 기타 아이템 (campfire, wall 등)
            # TODO: 나중에 구현
            self._show_message(f"{recipe['name']} 조합 성공! (구현 예정)", (0.3, 1, 0.3, 1))

        self.update()

    def _show_message(self, message, color=(1, 1, 1, 1)):
        """메시지 표시"""
        self.message_label['text'] = message
        self.message_label['text_fg'] = color
        self.message_label.show()

        # 2초 후 자동 숨김
        self.game.taskMgr.doMethodLater(
            2.0,
            lambda task: self.message_label.hide(),
            'hide_crafting_message'
        )

    def _on_tool_click(self, slot_index):
        """도구 슬롯 클릭 처리"""
        tool = self.game.player.get_tool_at_slot(slot_index)
        if tool:
            # 도구 장착
            if not tool.broken:
                self.game.player.equip_tool(slot_index)
                self.update()
                print(f"[InventoryUI] Equipped {tool.name}")
            else:
                print("[InventoryUI] Cannot equip broken tool")
        else:
            print(f"[InventoryUI] Empty slot {slot_index}")

    def _on_drop_click(self):
        """드롭 버튼 클릭 처리"""
        current_tool = self.game.player.current_tool
        if current_tool:
            self.game.player.drop_current_tool()
            self.update()
            print("[InventoryUI] Dropped tool")
        else:
            print("[InventoryUI] No tool to drop")

    def toggle(self):
        """인벤토리 가시성 토글"""
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def show(self):
        """인벤토리 표시"""
        self.is_visible = True
        self.main_frame.show()

        # 탭 초기화 (도구 탭으로)
        self._switch_tab('tools')

        self.update()

        # 마우스 커서 표시
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.game.win.requestProperties(props)

    def hide(self):
        """인벤토리 숨김"""
        self.is_visible = False
        self.main_frame.hide()

        # 마우스 커서 숨김
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)
        self.game.win.requestProperties(props)

        # 마우스 중앙으로
        center_x = self.game.win.getXSize() // 2
        center_y = self.game.win.getYSize() // 2
        self.game.win.movePointer(0, center_x, center_y)

    def update(self):
        """인벤토리 표시 업데이트"""
        # 도구 슬롯 업데이트
        for i, btn in enumerate(self.tool_buttons):
            tool = self.game.player.get_tool_at_slot(i)
            if tool:
                is_equipped = self.game.player.current_tool == tool
                equipped_mark = " > " if is_equipped else ""
                durability = tool.get_durability_percentage()
                status = f"{equipped_mark}{tool.name}\n{durability}%"
                btn['text'] = status

                if tool.broken:
                    btn['text_fg'] = (0.8, 0.2, 0.2, 1)  # 빨간색
                elif is_equipped:
                    btn['text_fg'] = (0.2, 0.8, 0.2, 1)  # 초록색
                else:
                    btn['text_fg'] = (0.8, 0.8, 0.2, 1)  # 노란색
            else:
                btn['text'] = f"[Empty {i+1}]"
                btn['text_fg'] = (0.5, 0.5, 0.5, 1)  # 회색

        # 리소스 업데이트
        wood_count = self.game.player.get_resource_count('wood')
        stone_count = self.game.player.get_resource_count('stone')
        self.resource_labels['wood']['text'] = f"Wood: {wood_count}"
        self.resource_labels['stone']['text'] = f"Stone: {stone_count}"

        # 조합 버튼 업데이트 (리소스 충분한지 확인)
        for btn in self.crafting_buttons:
            # extraArgs에서 item_id 가져오기
            item_id = btn['extraArgs'][0]
            recipe = CRAFTING_RECIPES[item_id]
            cost = recipe['cost']

            # 리소스 확인
            can_craft = True
            for res_type, amount in cost.items():
                if self.game.player.get_resource_count(res_type) < amount:
                    can_craft = False
                    break

            if can_craft:
                btn['frameColor'] = (0.2, 0.5, 0.2, 0.8)  # 초록색 (조합 가능)
            else:
                btn['frameColor'] = (0.5, 0.2, 0.2, 0.8)  # 빨간색 (리소스 부족)

        # 드롭 버튼 표시 제어 (도구 탭에서만 표시)
        if self.current_tab == 'tools':
            self.drop_btn.show()
        else:
            self.drop_btn.hide()

    def cleanup(self):
        """정리"""
        if self.main_frame:
            self.main_frame.destroy()

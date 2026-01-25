"""
인벤토리 UI 시스템
DirectGui 기반 인벤토리 인터페이스
"""
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel,
    DGG
)
from panda3d.core import TextNode, Vec4, WindowProperties


class InventoryUI:
    """인벤토리 GUI - 도구 및 리소스 관리"""

    def __init__(self, game):
        self.game = game
        self.is_visible = False

        # UI 컴포넌트
        self.main_frame = None
        self.tool_buttons = []
        self.resource_labels = {}

        self._create_ui()

    def _create_ui(self):
        """인벤토리 UI 요소 생성"""
        # 메인 프레임 (화면 중앙, 초기엔 숨김)
        self.main_frame = DirectFrame(
            pos=(0, 0, 0),
            frameSize=(-0.6, 0.6, -0.4, 0.4),
            frameColor=(0.1, 0.1, 0.1, 0.95),
            state=DGG.NORMAL
        )
        self.main_frame.hide()

        # 타이틀
        title = DirectLabel(
            parent=self.main_frame,
            pos=(0, 0, 0.35),
            text="INVENTORY (Press I to close)",
            text_scale=0.08,
            text_fg=(1, 0.8, 0.2, 1),
            frameColor=(0, 0, 0, 0)
        )

        # 도구 섹션
        self._create_tools_section()

        # 리소스 섹션
        self._create_resources_section()

        # 액션 버튼
        self._create_action_buttons()

    def _create_tools_section(self):
        """도구 인벤토리 섹션"""
        tools_label = DirectLabel(
            parent=self.main_frame,
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
                parent=self.main_frame,
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
            pos=(-0.5, 0, -0.05),
            text="RESOURCES:",
            text_scale=0.06,
            text_align=TextNode.ALeft,
            text_fg=(0.5, 0.8, 1, 1),
            frameColor=(0, 0, 0, 0)
        )

        # 나무
        self.resource_labels['wood'] = DirectLabel(
            parent=self.main_frame,
            pos=(-0.5, 0, -0.12),
            text="Wood: 0",
            text_scale=0.05,
            text_align=TextNode.ALeft,
            text_fg=(0.6, 0.4, 0.2, 1),
            frameColor=(0, 0, 0, 0)
        )

        # 돌
        self.resource_labels['stone'] = DirectLabel(
            parent=self.main_frame,
            pos=(-0.5, 0, -0.18),
            text="Stone: 0",
            text_scale=0.05,
            text_align=TextNode.ALeft,
            text_fg=(0.5, 0.5, 0.5, 1),
            frameColor=(0, 0, 0, 0)
        )

    def _create_action_buttons(self):
        """액션 버튼 생성"""
        # 드롭 버튼
        drop_btn = DirectButton(
            parent=self.main_frame,
            pos=(0.4, 0, -0.3),
            frameSize=(-0.15, 0.15, -0.08, 0.08),
            frameColor=(0.8, 0.3, 0.3, 0.8),
            text="DROP [G]",
            text_scale=0.05,
            command=self._on_drop_click
        )

        # 닫기 버튼
        close_btn = DirectButton(
            parent=self.main_frame,
            pos=(0, 0, -0.35),
            frameSize=(-0.2, 0.2, -0.08, 0.08),
            frameColor=(0.3, 0.3, 0.3, 0.8),
            text="CLOSE [I]",
            text_scale=0.05,
            command=self.toggle
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

    def cleanup(self):
        """정리"""
        if self.main_frame:
            self.main_frame.destroy()

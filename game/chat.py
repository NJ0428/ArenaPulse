from direct.gui.DirectGui import DirectEntry, DirectLabel, DGG
from panda3d.core import TextNode, Vec4
import time


class ChatSystem:
    def __init__(self, game):
        self.game = game
        self.messages = []  # 채팅 메시지 저장
        self.max_messages = 8  # 표시할 최대 메시지 수
        self.is_chat_open = False  # 채팅창 열림 상태

        # 채팅 UI 생성
        self._create_chat_ui()

        print("[Chat] 채팅 시스템 초기화 완료")

    def _create_chat_ui(self):
        """채팅 UI 생성"""
        # 채팅 메시지 표시 영역 (화면 왼쪽 하단) - 초기에는 숨김
        self.chat_display = DirectLabel(
            pos=(-0.83, 0, -0.35),
            frameSize=(-0.01, 1.75, -0.01, 0.45),
            frameColor=(0, 0, 0, 0.5),
            text="",
            text_scale=0.04,
            text_align=TextNode.ALeft,
            text_pos=(0.02, 0.42),
            text_fg=(1, 1, 1, 1),
            text_wordwrap=80,
            state=DGG.NORMAL
        )
        self.chat_display.hide()  # 평소에는 숨김

        # 채팅 입력창 (초기에는 숨김)
        self.chat_entry = DirectEntry(
            pos=(-0.83, 0, -0.85),
            scale=0.05,
            frameColor=(0.2, 0.2, 0.2, 0.8),
            text_fg=(1, 1, 1, 1),
            initialText="",
            numLines=1,
            width=35,
            focus=0,
            command=self._send_message
        )
        self.chat_entry.hide()

        # 안내 메시지 표시
        self._add_system_message("Press T to open chat")

    def _send_message(self, text):
        """메시지 전송 (영어만 허용)"""
        # 빈 메시지 무시
        if not text or text.strip() == "":
            self.close_chat()
            return

        # 영어와 공백, 기본 문장부호만 허용 (한글 등 제거)
        filtered_text = ''.join(char for char in text if char.isascii() or char.isspace())

        # 필터링 후 빈 메시지 확인
        if not filtered_text.strip():
            self._add_system_message("영어만 입력 가능합니다.")
            self.close_chat()
            return

        # 명령어 처리
        if filtered_text.startswith('/'):
            self._handle_command(filtered_text)
            self.chat_entry.enterText('')
            self.close_chat()
            return

        # 메시지 추가
        self._add_message("Player", filtered_text)

        # 입력창 초기화 및 닫기
        self.chat_entry.enterText('')
        self.close_chat()

    def _handle_command(self, command):
        """명령어 처리"""
        cmd = command.lower().strip()

        if cmd == '/exit':
            self._add_system_message("Exiting game...")
            self.game.userExit()  # 게임 종료

        elif cmd == '/help':
            help_text = [
                "Available commands:",
                "/exit - Exit the game",
                "/help - Show this help message",
                "/clear - Clear chat history",
                "/inv - Show inventory",
                "/craft [item] - Craft item (ladder, wall, furnace, campfire)",
                "/target on - Spawn target in front of you",
                "/target off - Clear all targets",
                "/spawn [type] - Spawn enemy (melee, ranged, sprinter, tank, bomber)",
                "/weapon - Show current weapon info",
                "/attach [id] - Install attachment (see /attach list)",
                "/detach [slot] - Remove attachment (scope/grip/muzzle/magazine)",
                "/repair - Repair current weapon (cost: Wood 5, Stone 3)"
            ]
            for line in help_text:
                self._add_system_message(line)

        elif cmd == '/clear':
            self.messages.clear()
            self._update_chat_display()
            self._add_system_message("Chat cleared")

        elif cmd == '/inv' or cmd == '/inventory':
            # 인벤토리 표시
            wood = self.game.player.get_resource_count('wood')
            stone = self.game.player.get_resource_count('stone')
            self._add_system_message(f"Inventory: Wood: {wood}, Stone: {stone}")

        elif cmd.startswith('/craft'):
            # 조합 커맨드
            parts = cmd.split()

            if len(parts) < 2:
                # 레시피 표시
                recipes = [
                    "Crafting Recipes:",
                    "/craft ladder - Ladder (Wood: 10)",
                    "/craft wall - Wall (Wood: 15, Stone: 5)",
                    "/craft furnace - Furnace (Stone: 20)",
                    "/craft campfire - Campfire (Wood: 5, Stone: 3)"
                ]
                for line in recipes:
                    self._add_system_message(line)
            else:
                item_type = parts[1].lower()
                valid_items = ['ladder', 'wall', 'furnace', 'campfire']

                if item_type not in valid_items:
                    self._add_system_message(f"Unknown item: {item_type}")
                    self._add_system_message("Valid items: ladder, wall, furnace, campfire")
                else:
                    # 조합 시도
                    if self.game.player.craft_item(item_type):
                        self._add_system_message(f"Successfully crafted: {item_type}")

                        # 현재 인벤토리도 표시
                        wood = self.game.player.get_resource_count('wood')
                        stone = self.game.player.get_resource_count('stone')
                        self._add_system_message(f"Inventory: Wood: {wood}, Stone: {stone}")
                    else:
                        self._add_system_message(f"Failed to craft: {item_type} (not enough resources)")

        elif cmd == '/target on':
            self.game.targets.show_targets()
            self._add_system_message("Target spawned")

        elif cmd == '/target off':
            self.game.targets.hide_targets()
            self._add_system_message("All targets cleared")

        elif cmd.startswith('/spawn'):
            # 적 생성 명령어
            parts = cmd.split()
            enemy_type = None

            if len(parts) > 1:
                enemy_type = parts[1].lower()
                # 유효한 적 타입 확인
                valid_types = ['melee', 'ranged', 'sprinter', 'tank', 'bomber']
                if enemy_type not in valid_types:
                    self._add_system_message(f"Invalid enemy type: {enemy_type}")
                    self._add_system_message("Valid types: melee, ranged, sprinter, tank, bomber")
                    return

            # 적 생성
            self.game.enemies.spawn_enemy(enemy_type)
            if enemy_type:
                self._add_system_message(f"Spawned {enemy_type} enemy")
            else:
                self._add_system_message("Spawned random enemy")

        elif cmd.startswith('/enemy'):
            # /enemy도 /spawn과 동일하게 작동
            parts = cmd.split()
            enemy_type = None

            if len(parts) > 1:
                enemy_type = parts[1].lower()
                # 유효한 적 타입 확인
                valid_types = ['melee', 'ranged', 'sprinter', 'tank', 'bomber']
                if enemy_type not in valid_types:
                    self._add_system_message(f"Invalid enemy type: {enemy_type}")
                    self._add_system_message("Valid types: melee, ranged, sprinter, tank, bomber")
                    return

            # 적 생성
            self.game.enemies.spawn_enemy(enemy_type)
            if enemy_type:
                self._add_system_message(f"Spawned {enemy_type} enemy")
            else:
                self._add_system_message("Spawned random enemy")

        elif cmd == '/weapon' or cmd == '/gun' or cmd == '/w':
            # 현재 무기 정보 표시
            info = self.game.player.get_weapon_info()
            self._add_system_message(f"Weapon: {info['name']}")
            self._add_system_message(f"  Damage: {info['damage']} | Fire Rate: {info['fire_rate']}s")
            self._add_system_message(f"  Spread: {info['spread']} | Recoil: {info['recoil']}")
            self._add_system_message(f"  Magazine: {info['current_ammo']}/{info['magazine_size']} (Total: {info['total_ammo']})")
            self._add_system_message(f"  Reload Time: {info['reload_time']}s | Mode: {info['fire_mode']}")
            self._add_system_message(f"  Durability: {info['durability']}% {'[BROKEN]' if info['is_broken'] else ''}")
            if info['attachments']:
                self._add_system_message(f"  Attachments: {', '.join(info['attachments'])}")
            else:
                self._add_system_message("  Attachments: None")

        elif cmd.startswith('/attach'):
            # 부착물 장착
            parts = cmd.split()
            if len(parts) < 2:
                # 부착물 목록 표시
                from game.weapon import Attachment
                self._add_system_message("Available attachments:")
                for att_id, att_data in Attachment.ATTACHMENT_TYPES.items():
                    self._add_system_message(f"  {att_id}: {att_data['name']} - {att_data['description']}")
            else:
                attachment_id = parts[1].lower()
                try:
                    if self.game.player.install_attachment(attachment_id):
                        self._add_system_message(f"Installed: {attachment_id}")
                    # 실패 메시지는 install_attachment 내부에서 처리됨
                except Exception as e:
                    self._add_system_message(f"Error: {str(e)}")

        elif cmd.startswith('/detach'):
            # 부착물 제거
            parts = cmd.split()
            if len(parts) < 2:
                self._add_system_message("Usage: /detach [slot]")
                self._add_system_message("Slots: scope, grip, muzzle, magazine")
            else:
                slot = parts[1].lower()
                valid_slots = ['scope', 'grip', 'muzzle', 'magazine']
                if slot not in valid_slots:
                    self._add_system_message(f"Invalid slot: {slot}")
                    self._add_system_message(f"Valid slots: {', '.join(valid_slots)}")
                else:
                    if self.game.player.remove_attachment(slot):
                        self._add_system_message(f"Removed attachment from {slot}")

        elif cmd == '/repair':
            # 무기 수리
            wood_cost = 5
            stone_cost = 3
            if (self.game.player.get_resource_count('wood') >= wood_cost and
                self.game.player.get_resource_count('stone') >= stone_cost):
                self.game.player.use_resources({'wood': wood_cost, 'stone': stone_cost})
                new_durability = self.game.player.repair_weapon()
                self._add_system_message(f"Weapon repaired! Durability: {new_durability}%")
                self._add_system_message(f"Cost: Wood -{wood_cost}, Stone -{stone_cost}")
            else:
                self._add_system_message(f"Not enough resources! Need: Wood {wood_cost}, Stone {stone_cost}")

        else:
            self._add_system_message(f"Unknown command: {command}")
            self._add_system_message("Type /help for available commands")

    def _add_message(self, sender, message):
        """일반 메시지 추가"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {sender}: {message}"
        self.messages.append(formatted_message)

        # 메시지 수 제한 (최근 N개만 표시)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        # UI 업데이트
        self._update_chat_display()

    def _add_system_message(self, message):
        """시스템 메시지 추가"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [SYSTEM] {message}"
        self.messages.append(formatted_message)

        # 메시지 수 제한
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        # UI 업데이트
        self._update_chat_display()

    def _update_chat_display(self):
        """채팅 표시 업데이트"""
        # 최근 N개 메시지만 표시 (줄바꿈으로 구분)
        display_messages = self.messages[-self.max_messages:]
        full_text = "\n".join(display_messages)
        self.chat_display['text'] = full_text

    def open_chat(self):
        """채팅 열기"""
        self.is_chat_open = True
        self.chat_display.show()  # 메시지 표시 영역도 표시
        self.chat_entry.show()
        self.chat_entry['focus'] = 1  # 입력창에 포커스

        # 마우스 커서 표시
        from panda3d.core import WindowProperties
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.game.win.requestProperties(props)

    def close_chat(self):
        """채팅 닫기"""
        self.is_chat_open = False
        self.chat_entry['focus'] = 0
        self.chat_entry.hide()
        self.chat_display.hide()  # 메시지 표시 영역도 숨김

        # 마우스 다시 숨기고 중앙으로
        from panda3d.core import WindowProperties
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)
        self.game.win.requestProperties(props)

        # 마우스 중앙으로 리셋
        center_x = self.game.win.getXSize() // 2
        center_y = self.game.win.getYSize() // 2
        self.game.win.movePointer(0, center_x, center_y)

    def toggle_chat(self):
        """채팅 토글"""
        if self.is_chat_open:
            self.close_chat()
        else:
            self.open_chat()

    def is_open(self):
        """채팅 열림 상태 반환"""
        return self.is_chat_open

    def cleanup(self):
        """정리"""
        if self.chat_display:
            self.chat_display.destroy()
        if self.chat_entry:
            self.chat_entry.destroy()

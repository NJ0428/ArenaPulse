from panda3d.core import Point3, Vec3, WindowProperties
from game.pause_menu import PauseMenu


class Controls:
    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.paused = False

        # 마우스 감도
        self.mouse_sensitivity = 100.0

        # 마우스 숨기기
        self._setup_mouse_mode()

        # 키보드 입력 바인딩
        self._setup_keyboard()

        # 마우스 입력 바인딩
        self._setup_mouse()

        # 일시정지 메뉴 생성
        self.pause_menu = PauseMenu(
            game,
            resume_callback=self._toggle_pause,
            quit_callback=self._quit_game
        )

        print("[Controls] 컨트롤 설정 완료 (FPS 모드)")

    def _setup_mouse_mode(self):
        """마우스 숨김 및 중앙 정렬"""
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)  # 창 안에 가둠
        self.game.win.requestProperties(props)
        # 마우스를 화면 중앙으로 리셋
        self._center_mouse()

    def _center_mouse(self):
        """마우스를 화면 중앙으로 이동"""
        center_x = self.game.win.getXSize() // 2
        center_y = self.game.win.getYSize() // 2
        self.game.win.movePointer(0, center_x, center_y)

    def _setup_keyboard(self):
        """키보드 입력 설정"""
        # WASD 이동 (raw- 접두사로 한글 모드에서도 작동)
        self.game.accept('raw-w', self._set_move, ['forward', True])
        self.game.accept('raw-w-up', self._set_move, ['forward', False])
        self.game.accept('raw-s', self._set_move, ['backward', True])
        self.game.accept('raw-s-up', self._set_move, ['backward', False])
        self.game.accept('raw-a', self._set_move, ['left', True])
        self.game.accept('raw-a-up', self._set_move, ['left', False])
        self.game.accept('raw-d', self._set_move, ['right', True])
        self.game.accept('raw-d-up', self._set_move, ['right', False])

        # 화살표 키도 지원
        self.game.accept('arrow_up', self._set_move, ['forward', True])
        self.game.accept('arrow_up-up', self._set_move, ['forward', False])
        self.game.accept('arrow_down', self._set_move, ['backward', True])
        self.game.accept('arrow_down-up', self._set_move, ['backward', False])
        self.game.accept('arrow_left', self._set_move, ['left', True])
        self.game.accept('arrow_left-up', self._set_move, ['left', False])
        self.game.accept('arrow_right', self._set_move, ['right', True])
        self.game.accept('arrow_right-up', self._set_move, ['right', False])

        # 점프 (Space)
        self.game.accept('space', self._jump)

        # 달리기 (Shift)
        self.game.accept('lshift', self._set_run, [True])
        self.game.accept('lshift-up', self._set_run, [False])
        self.game.accept('rshift', self._set_run, [True])
        self.game.accept('rshift-up', self._set_run, [False])

        # 숨쉬기 (Ctrl)
        self.game.accept('lcontrol', self._toggle_crouch)
        self.game.accept('rcontrol', self._toggle_crouch)

        # 재장전 (R)
        self.game.accept('raw-r', self._reload)
        self.game.accept('r', self._reload)

        # 일시정지 (ESC)
        self.game.accept('escape', self._toggle_pause)

        # 채팅 (T)
        self.game.accept('raw-t', self._toggle_chat)
        self.game.accept('t', self._toggle_chat)

        # 장애물 생성 (O)
        self.game.accept('raw-o', self._add_obstacle)
        self.game.accept('o', self._add_obstacle)

        # 채집 (E)
        self.game.accept('raw-e', self._gather_resource)
        self.game.accept('e', self._gather_resource)

        # 무기 전환 (1-4)
        self.game.accept('1', self._switch_weapon, [0])
        self.game.accept('2', self._switch_weapon, [1])
        self.game.accept('3', self._switch_weapon, [2])
        self.game.accept('4', self._switch_weapon, [3])

        # 발사 모드 전환 (V)
        self.game.accept('raw-v', self._cycle_fire_mode)
        self.game.accept('v', self._cycle_fire_mode)

        # 무기 수리 (H)
        self.game.accept('raw-h', self._repair_weapon)
        self.game.accept('h', self._repair_weapon)

        # 인벤토리 UI (I)
        self.game.accept('raw-i', self._toggle_inventory)
        self.game.accept('i', self._toggle_inventory)

        # 도구 드롭 (G)
        self.game.accept('raw-g', self._drop_tool)
        self.game.accept('g', self._drop_tool)

    def _setup_mouse(self):
        """마우스 입력 설정"""
        # 좌클릭 다운 - 발사 시작
        self.game.accept('mouse1', self._start_firing)

        # 좌클릭 업 - 발사 중지
        self.game.accept('mouse1-up', self._stop_firing)

        # 우클릭 - 줌
        self.game.accept('mouse3', self._toggle_zoom)

    def _set_move(self, direction, value):
        """이동 상태 설정"""
        if not self.paused and not self.game.game_over:
            self.player.moving[direction] = value

    def _start_firing(self):
        """발사 시작"""
        if not self.paused and not self.game.game_over:
            self.player.start_firing()

    def _stop_firing(self):
        """발사 중지"""
        if not self.paused and not self.game.game_over:
            self.player.stop_firing()

    def _toggle_zoom(self):
        """줌 토글"""
        if not self.paused and not self.game.game_over:
            self.player.toggle_zoom()

    def _jump(self):
        """점프"""
        if not self.paused and not self.game.game_over:
            self.player.jump()

    def _set_run(self, running):
        """달리기 상태 설정"""
        if not self.paused and not self.game.game_over:
            self.player.set_running(running)

    def _toggle_crouch(self):
        """숨쉬기 토글"""
        if not self.paused and not self.game.game_over:
            self.player.toggle_crouch()

    def _reload(self):
        """재장전"""
        if not self.paused and not self.game.game_over:
            self.player._reload()

    def _toggle_chat(self):
        """채팅 토글"""
        # 일시정지 상태나 게임 오버 상태가 아닐 때만 채팅 토글
        if not self.paused and not self.game.game_over:
            self.game.chat.toggle_chat()

    def _add_obstacle(self):
        """장애물 생성"""
        if not self.paused and not self.game.game_over:
            player_pos = self.player.node.getPos()
            self.game.obstacles.add_random_obstacle(player_pos)

    def _gather_resource(self):
        """리소스 채집 또는 도구 줍기"""
        if not self.paused and not self.game.game_over:
            player_pos = self.player.node.getPos()

            # 먼저 도구 줍기 시도
            item_type, item_data = self.game.ground_items.try_pickup(player_pos)

            if item_type == 'tool':
                # 도구를 줍음
                self.player.add_tool(item_data)
                print("[Player] Picked up tool!")
            elif item_type == 'resource':
                # 리소스를 줍음
                res_type = item_data['type']
                amount = item_data['amount']
                self.player.add_resource(res_type, amount)
                print(f"[Player] Picked up {res_type} +{amount}")
            else:
                # 줍을 아이템이 없으면 리소스 채집
                resource_type, amount = self.game.resources.try_gather(player_pos)

                if resource_type and amount > 0:
                    # 채집 성공 - 인벤토리에 추가
                    self.player.add_resource(resource_type, amount)
                elif resource_type:
                    # 채집 중
                    pass

    def _toggle_inventory(self):
        """인벤토리 UI 토글"""
        if not self.paused and not self.game.game_over:
            self.game.inventory_ui.toggle()

    def _drop_tool(self):
        """현재 도구 드롭"""
        if not self.paused and not self.game.game_over:
            self.player.drop_current_tool()

    def _switch_weapon(self, slot):
        """무기 전환"""
        if not self.paused and not self.game.game_over:
            self.player.switch_weapon(slot)

    def _cycle_fire_mode(self):
        """발사 모드 전환"""
        if not self.paused and not self.game.game_over:
            self.player.cycle_fire_mode()

    def _repair_weapon(self):
        """무기 수리"""
        if not self.paused and not self.game.game_over:
            # 리소스 소모해서 수리
            wood_cost = 5
            stone_cost = 3

            if (self.player.get_resource_count('wood') >= wood_cost and
                self.player.get_resource_count('stone') >= stone_cost):
                self.player.use_resources({'wood': wood_cost, 'stone': stone_cost})
                self.player.repair_weapon()
                print(f"[Player] 무기 수리 완료! (나무 -{wood_cost}, 돌 -{stone_cost})")
            else:
                print(f"[Player] 수리에 필요한 리소스 부족! (나무 {wood_cost}, 돌 {stone_cost} 필요)")

    def _toggle_pause(self):
        """일시정지 토글"""
        # 게임 오버 상태에서는 일시정지 불가
        if self.game.game_over:
            return

        self.paused = not self.paused

        props = WindowProperties()

        if self.paused:
            print("[Game] Paused - Press ESC to resume")
            # 일시정지 메뉴 표시
            self.pause_menu.show()
            # 마우스 커서 표시
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.M_absolute)
            # 모든 이동 멈춤
            for key in self.player.moving:
                self.player.moving[key] = False
        else:
            print("[Game] Resumed")
            # 일시정지 메뉴 숨김
            self.pause_menu.hide()
            # 마우스 다시 숨김
            props.setCursorHidden(True)
            props.setMouseMode(WindowProperties.M_confined)
            # 마우스를 화면 중앙으로 리셋
            self._center_mouse()

        self.game.win.requestProperties(props)

    def _quit_game(self):
        """Quit game"""
        self.game._exit_game()

    def update(self):
        """매 프레임 컨트롤 업데이트 (마우스 회전)"""
        if self.paused or self.game.game_over:
            return

        # 현재 마우스 위치 가져오기
        if self.game.mouseWatcherNode.hasMouse():
            mouse_x = self.game.mouseWatcherNode.getMouseX()
            mouse_y = self.game.mouseWatcherNode.getMouseY()

            # 중앙(0, 0)에서의 차이 계산
            delta_x = mouse_x
            delta_y = mouse_y

            # 델타가 있을 때만 회전
            if abs(delta_x) > 0.001 or abs(delta_y) > 0.001:
                # 좌우 회전 (Heading)
                self.player.rotate_heading(-delta_x * self.mouse_sensitivity)

                # 상하 회전 (Pitch)
                self.player.rotate_pitch(delta_y * self.mouse_sensitivity)

            # 마우스를 화면 중앙으로 리셋
            self._center_mouse()

    def is_paused(self):
        """일시정지 상태 반환"""
        return self.paused

    def cleanup(self):
        """입력 바인딩 해제 및 마우스 복원"""
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.game.win.requestProperties(props)
        self.game.ignoreAll()
        if self.pause_menu:
            self.pause_menu.cleanup()

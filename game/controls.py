from panda3d.core import Point3, Vec3, WindowProperties


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

        # 일시정지 (ESC)
        self.game.accept('escape', self._toggle_pause)

    def _setup_mouse(self):
        """마우스 입력 설정"""
        # 좌클릭 - 원거리 공격
        self.game.accept('mouse1', self._ranged_attack)

        # 우클릭 - 근접 공격
        self.game.accept('mouse3', self._melee_attack)

    def _set_move(self, direction, value):
        """이동 상태 설정"""
        if not self.paused:
            self.player.moving[direction] = value

    def _ranged_attack(self):
        """원거리 공격"""
        if not self.paused:
            self.player.ranged_attack()

    def _melee_attack(self):
        """근접 공격"""
        if not self.paused:
            self.player.melee_attack()

    def _jump(self):
        """점프"""
        if not self.paused:
            self.player.jump()

    def _set_run(self, running):
        """달리기 상태 설정"""
        if not self.paused:
            self.player.set_running(running)

    def _toggle_pause(self):
        """일시정지 토글"""
        self.paused = not self.paused

        props = WindowProperties()

        if self.paused:
            print("[Game] 일시정지 - ESC로 재개")
            # 마우스 커서 표시
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.M_absolute)
            # 모든 이동 멈춤
            for key in self.player.moving:
                self.player.moving[key] = False
        else:
            print("[Game] 게임 재개")
            # 마우스 다시 숨김
            props.setCursorHidden(True)
            props.setMouseMode(WindowProperties.M_confined)
            # 마우스를 화면 중앙으로 리셋
            self._center_mouse()

        self.game.win.requestProperties(props)

    def update(self):
        """매 프레임 컨트롤 업데이트 (마우스 회전)"""
        if self.paused:
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

"""
사운드 매니저 - ArenaPulse 게임의 모든 사운드 효과를 관리
"""
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AudioSound
import os

class SoundManager:
    """게임의 모든 사운드를 관리하는 클래스"""

    def __init__(self, base: ShowBase):
        """
        사운드 매니저 초기화

        Args:
            base: Panda3D ShowBase 인스턴스
        """
        self.base = base
        self.sounds = {}
        self.sounds_dir = "sounds"

        # 오디오 시스템 확인
        audio_active = hasattr(self.base, 'sfxManager') and self.base.sfxManager is not None
        print(f"[사운드] 오디오 매니저 활성화: {audio_active}")

        # 현재 작업 디렉토리 확인
        print(f"[사운드] 현재 작업 디렉토리: {os.getcwd()}")

        # 사운드 파일 로드
        self._load_sounds()

        # 마스터 볼륨 설정 (0.0 ~ 1.0)
        self.master_volume = 1.0  # 최대 볼륨으로 변경
        self.sfx_volume = 1.0     # 최대 볼륨으로 변경
        self._set_volumes()

        print(f"[사운드] 사운드 매니저 초기화 완료 (로드된 사운드: {len(self.sounds)}개)")

    def _load_sounds(self):
        """sounds 폴더에서 모든 사운드 파일을 로드"""
        sound_files = {
            'gun_shot': 'gun_shot.wav',
            'gun_reload': 'gun_reload.wav',
            'empty_click': 'empty_click.wav',
            'target_hit': 'target_hit.wav'
        }

        for name, filename in sound_files.items():
            # 절대 경로로 변환
            filepath = os.path.abspath(os.path.join(self.sounds_dir, filename))

            # 파일이 존재하는지 확인
            if os.path.exists(filepath):
                try:
                    print(f"[사운드] 시도: {filepath}")
                    sound = self.base.loader.loadSfx(filepath)
                    if sound:
                        self.sounds[name] = sound
                        print(f"[사운드] ✓ 로드 성공: {filename}")
                    else:
                        print(f"[사운드] ✗ 로드 실패 (None 반환): {filename}")
                except Exception as e:
                    print(f"[사운드] ✗ 로드 에러 ({filename}): {e}")
            else:
                print(f"[사운드] ✗ 파일 없음: {filepath}")

        print(f"[사운드] 총 {len(self.sounds)}개 사운드 로드됨")

    def _set_volumes(self):
        """모든 사운드의 볼륨 설정"""
        for sound in self.sounds.values():
            sound.setVolume(self.master_volume * self.sfx_volume)

    def play(self, sound_name: str, volume: float = 1.0) -> bool:
        """
        사운드 재생

        Args:
            sound_name: 재생할 사운드 이름 ('gun_shot', 'gun_reload' 등)
            volume: 개별 볼륨 (0.0 ~ 1.0, 기본 1.0)

        Returns:
            bool: 재생 성공 여부
        """
        if sound_name in self.sounds:
            sound = self.sounds[sound_name]

            # 이미 재생 중이면 중지하고 다시 재생 (중복 재생 방지)
            if sound.status() == AudioSound.PLAYING:
                sound.stop()

            final_volume = self.master_volume * self.sfx_volume * volume
            sound.setVolume(final_volume)
            sound.play()

            # 디버그: 재생 확인
            status = sound.status()
            print(f"[사운드] 재생: {sound_name} (볼륨: {final_volume:.2f}, 상태: {status})")
            return True
        else:
            print(f"[사운드] ✗ 사운드 없음: {sound_name}")
            return False

    def play_looping(self, sound_name: str, volume: float = 1.0) -> bool:
        """
        루핑 사운드 재생 (배경음악 등)

        Args:
            sound_name: 재생할 사운드 이름
            volume: 개별 볼륨

        Returns:
            bool: 재생 성공 여부
        """
        if sound_name in self.sounds:
            sound = self.sounds[sound_name]
            sound.setLoop(True)
            final_volume = self.master_volume * self.sfx_volume * volume
            sound.setVolume(final_volume)
            sound.play()
            return True
        return False

    def stop(self, sound_name: str):
        """재생 중인 사운드 중지"""
        if sound_name in self.sounds:
            self.sounds[sound_name].stop()

    def stop_all(self):
        """모든 사운드 중지"""
        for sound in self.sounds.values():
            sound.stop()

    def set_master_volume(self, volume: float):
        """
        마스터 볼륨 설정

        Args:
            volume: 볼륨 (0.0 ~ 1.0)
        """
        self.master_volume = max(0.0, min(1.0, volume))
        self._set_volumes()

    def set_sfx_volume(self, volume: float):
        """
        효과음 볼륨 설정

        Args:
            volume: 볼륨 (0.0 ~ 1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        self._set_volumes()

    def cleanup(self):
        """사운드 매니저 정리"""
        self.stop_all()
        self.sounds.clear()
        print("[사운드] 사운드 매니저 정리 완료")

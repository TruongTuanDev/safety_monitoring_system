import os

import pygame


class AudioManager:
    def __init__(self):
        self.enabled = True
        self.available = False
        self.alert_sounds = {
            'intrusion': 'alert_sound.wav',
            'person_count': 'person_alert.wav'
        }

        try:
            pygame.mixer.init()
            self.available = True
        except Exception as e:
            print(f"Audio unavailable: {e}")

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self.stop_alert_sound()

    def play_alert_sound(self, sound_type='intrusion'):
        if not self.enabled or not self.available:
            return False

        sound_file = self.alert_sounds.get(sound_type, 'alert_sound.wav')

        try:
            if os.path.exists(sound_file):
                pygame.mixer.music.stop()
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                print(f"Playing alert sound: {sound_type}")
                return True
            else:
                print(f"Sound file not found: {sound_file}")
                return False
        except Exception as e:
            print(f"Error playing sound: {e}")
            return False

    def stop_alert_sound(self):
        if self.available:
            pygame.mixer.music.stop()

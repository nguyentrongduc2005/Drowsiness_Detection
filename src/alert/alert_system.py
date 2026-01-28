"""
Alert System - Hệ thống cảnh báo âm thanh và hình ảnh
"""
import pygame
import os
from enum import Enum


class AlertLevel(Enum):
    """Mức độ cảnh báo"""
    NONE = 0      # Không cảnh báo
    FATIGUE = 1   # Cảnh báo vàng - mệt mỏi
    DROWSY = 2    # Cảnh báo đỏ - ngủ gật


class AlertSystem:
    """Quản lý cảnh báo âm thanh và hình ảnh"""
    
    def __init__(self, config_manager):
        """
        Khởi tạo AlertSystem
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        self.alert_sound_path = self.config.get("alert.sound_file", "data/alarm.wav")
        self.sound_loaded = False
        self.current_alert = AlertLevel.NONE
        self.is_playing = False
        
        self._load_sound()
    
    def _load_sound(self):
        """Load file âm thanh cảnh báo"""
        if os.path.exists(self.alert_sound_path):
            try:
                self.alert_sound = pygame.mixer.Sound(self.alert_sound_path)
                self.sound_loaded = True
                print(f"[Alert] Đã load âm thanh: {self.alert_sound_path}")
            except Exception as e:
                print(f"[Alert] Lỗi khi load âm thanh: {e}")
                self.sound_loaded = False
        else:
            print(f"[Alert] Không tìm thấy file âm thanh: {self.alert_sound_path}")
            os.makedirs("data", exist_ok=True)
            print("[Alert] Vui lòng thêm file alarm.wav vào thư mục data/")
            self.sound_loaded = False
    
    def play_alert(self):
        """Phát âm thanh cảnh báo"""
        if self.sound_loaded and not self.is_playing:
            try:
                self.alert_sound.play(loops=-1)  # Loop vô hạn
                self.is_playing = True
                print("[Alert] Bắt đầu phát âm thanh cảnh báo")
            except Exception as e:
                print(f"[Alert] Lỗi khi phát âm thanh: {e}")
    
    def stop_alert(self):
        """Dừng âm thanh cảnh báo"""
        if self.is_playing:
            try:
                pygame.mixer.stop()
                self.is_playing = False
                print("[Alert] Đã dừng âm thanh cảnh báo")
            except Exception as e:
                print(f"[Alert] Lỗi khi dừng âm thanh: {e}")
    
    def update_alert(self, alert_level: AlertLevel):
        """
        Cập nhật trạng thái cảnh báo
        
        Args:
            alert_level: Mức độ cảnh báo mới
        """
        if alert_level == AlertLevel.DROWSY:
            # Cảnh báo đỏ - có âm thanh
            if not self.is_playing:
                self.play_alert()
        else:
            # Cảnh báo vàng hoặc không cảnh báo - tắt âm thanh
            if self.is_playing:
                self.stop_alert()
        
        self.current_alert = alert_level
    
    def get_alert_level(self) -> AlertLevel:
        """Lấy mức cảnh báo hiện tại"""
        return self.current_alert
    
    def get_alert_color(self) -> tuple:
        """
        Lấy màu cảnh báo (BGR format)
        
        Returns:
            Tuple màu BGR
        """
        if self.current_alert == AlertLevel.DROWSY:
            return (0, 0, 255)  # Đỏ
        elif self.current_alert == AlertLevel.FATIGUE:
            return (0, 255, 255)  # Vàng
        else:
            return (0, 255, 0)  # Xanh
    
    def get_alert_text(self) -> str:
        """
        Lấy text cảnh báo
        
        Returns:
            Text cảnh báo
        """
        if self.current_alert == AlertLevel.DROWSY:
            return "WARNING: DROWSY!"
        elif self.current_alert == AlertLevel.FATIGUE:
            return "Warning: Fatigue"
        else:
            return "Normal"
    
    def cleanup(self):
        """Giải phóng tài nguyên"""
        self.stop_alert()
        pygame.mixer.quit()
        print("[Alert] Đã giải phóng tài nguyên")

"""
Module Config: Đọc và quản lý cấu hình
"""
import json
import os


class Config:
    """
    Class quản lý cấu hình từ file config.json
    """
    
    def __init__(self, config_path="data/config.json"):
        """
        Khởi tạo Config
        
        Args:
            config_path: Đường dẫn tới file config.json
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Đọc file config.json
        
        Returns:
            dict: Dictionary chứa cấu hình
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"Không tìm thấy file config: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Lỗi đọc file config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """
        Lấy cấu hình mặc định
        
        Returns:
            dict: Dictionary cấu hình mặc định
        """
        return {
            "eye_thresholds": {
                "ear_default": 0.25,
                "consecutive_frames": 20,
                "min_ear_threshold": 0.18,
                "max_ear_threshold": 0.30
            },
            "mouth_thresholds": {
                "mar_limit": 0.6,
                "yawn_frames": 30
            },
            "smart_threshold": {
                "window_size": 150,
                "min_samples_for_learning": 100,
                "threshold_multiplier": 0.75
            },
            "paths": {
                "model_path": "data/shape_predictor_68_face_landmarks.dat",
                "alarm_sound": "data/alarm.wav"
            },
            "settings": {
                "camera_id": 0,
                "show_landmarks": True,
                "fps_display": True,
                "log_enabled": True
            }
        }
    
    def get(self, key, default=None):
        """
        Lấy giá trị config theo key
        
        Args:
            key: Key cần lấy (có thể dùng dạng "section.key")
            default: Giá trị mặc định nếu không tìm thấy
            
        Returns:
            Giá trị config hoặc default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_ear_default(self):
        """Lấy ngưỡng EAR mặc định"""
        return self.get('eye_thresholds.ear_default', 0.25)
    
    def get_consecutive_frames(self):
        """Lấy số frame liên tiếp để cảnh báo"""
        return self.get('eye_thresholds.consecutive_frames', 20)
    
    def get_window_size(self):
        """Lấy kích thước cửa sổ cho SmartThreshold"""
        return self.get('smart_threshold.window_size', 150)
    
    def get_min_samples(self):
        """Lấy số mẫu tối thiểu để học"""
        return self.get('smart_threshold.min_samples_for_learning', 100)
    
    def get_model_path(self):
        """Lấy đường dẫn model"""
        return self.get('paths.model_path', 'data/shape_predictor_68_face_landmarks.dat')
    
    def get_alarm_sound(self):
        """Lấy đường dẫn file âm thanh cảnh báo"""
        return self.get('paths.alarm_sound', 'data/alarm.wav')
    
    def get_camera_id(self):
        """Lấy ID camera"""
        return self.get('settings.camera_id', 0)
    
    def get_show_landmarks(self):
        """Kiểm tra có hiển thị landmarks không"""
        return self.get('settings.show_landmarks', True)
    
    def is_log_enabled(self):
        """Kiểm tra có bật log không"""
        return self.get('settings.log_enabled', True)
    
    def save_config(self):
        """Lưu cấu hình vào file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu config: {e}")
            return False


def load_config():
    """Hàm tương thích ngược"""
    config_path = os.path.join("data", "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

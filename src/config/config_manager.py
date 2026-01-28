"""
Configuration Manager
Quản lý cấu hình từ file JSON với khả năng học ngưỡng
"""
import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """Quản lý cấu hình hệ thống"""
    
    # Cấu hình mặc định
    DEFAULT_CONFIG = {
        "thresholds": {
            "ear": 0.21,
            "mar": 0.65,  # Tăng ngưỡng ngáp để tránh nhầm
            "blink": 0.21,
            "yawn": 0.65
        },
        "consecutive_frames": {
            "drowsiness": 20,
            "yawn": 20,  # Tăng từ 15 lên 20 để chắc chắn hơn
            "blink": 3
        },
        "fatigue_detection": {
            "blink_per_minute": 15,
            "yawn_per_minute": 3
        },
        "learning": {
            "samples": 100,
            "weight": 0.3
        },
        "camera": {
            "index": 0,
            "width": 640,
            "height": 480,
            "fps": 30
        },
        "alert": {
            "sound_file": "data/alarm.wav"
        },
        "display": {
            "show_landmarks": True,
            "show_fps": True
        }
    }
    
    def __init__(self, config_path: str = "config/settings.json"):
        """
        Khởi tạo ConfigManager
        
        Args:
            config_path: Đường dẫn đến file cấu hình JSON
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        
        self._ensure_config_directory()
        self.load()
    
    def _ensure_config_directory(self):
        """Đảm bảo thư mục config tồn tại"""
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def load(self) -> bool:
        """
        Load cấu hình từ file JSON
        
        Returns:
            True nếu load thành công, False nếu dùng mặc định
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config = self._merge_configs(self.DEFAULT_CONFIG.copy(), loaded_config)
                print(f"[Config] Đã load cấu hình từ: {self.config_path}")
                return True
            except Exception as e:
                print(f"[Config] Lỗi khi load cấu hình: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
                return False
        else:
            print(f"[Config] Không tìm thấy file cấu hình, sử dụng mặc định")
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
            return False
    
    def save(self) -> bool:
        """
        Lưu cấu hình vào file JSON
        
        Returns:
            True nếu lưu thành công
        """
        try:
            self._ensure_config_directory()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"[Config] Đã lưu cấu hình: {self.config_path}")
            return True
        except Exception as e:
            print(f"[Config] Lỗi khi lưu cấu hình: {e}")
            return False
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Merge cấu hình loaded với mặc định"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Lấy giá trị cấu hình theo đường dẫn
        
        Args:
            path: Đường dẫn cấu hình (vd: "thresholds.ear")
            default: Giá trị mặc định nếu không tìm thấy
            
        Returns:
            Giá trị cấu hình hoặc default
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, path: str, value: Any):
        """
        Đặt giá trị cấu hình theo đường dẫn
        
        Args:
            path: Đường dẫn cấu hình (vd: "thresholds.ear")
            value: Giá trị mới
        """
        keys = path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def reset_to_defaults(self):
        """Reset về cấu hình mặc định"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
        print("[Config] Đã reset về cấu hình mặc định")
    
    def get_all(self) -> Dict[str, Any]:
        """Lấy toàn bộ cấu hình"""
        return self.config.copy()

"""
Config Module: Read and manage configuration
"""
import json
import os


class Config:
    """
    Class to manage configuration from config.json file
    """
    
    def __init__(self, config_path="data/config.json"):
        """
        Initialize Config
        
        Args:
            config_path: Path to config.json file
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Read config.json file
        
        Returns:
            dict: Dictionary containing configuration
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error reading config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """
        Get default configuration
        
        Returns:
            dict: Default configuration dictionary
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
        Get config value by key
        
        Args:
            key: Key to retrieve (can use "section.key" format)
            default: Default value if not found
            
        Returns:
            Config value or default
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
        """Get default EAR threshold"""
        return self.get('eye_thresholds.ear_default', 0.25)
    
    def get_consecutive_frames(self):
        """Get consecutive frames for alert"""
        return self.get('eye_thresholds.consecutive_frames', 20)
    
    def get_window_size(self):
        """Get window size for SmartThreshold"""
        return self.get('smart_threshold.window_size', 150)
    
    def get_min_samples(self):
        """Get minimum samples for learning"""
        return self.get('smart_threshold.min_samples_for_learning', 100)
    
    def get_model_path(self):
        """Get model path"""
        return self.get('paths.model_path', 'data/shape_predictor_68_face_landmarks.dat')
    
    def get_alarm_sound(self):
        """Get alarm sound file path"""
        return self.get('paths.alarm_sound', 'data/alarm.wav')
    
    def get_camera_id(self):
        """Get camera ID"""
        return self.get('settings.camera_id', 0)
    
    def get_show_landmarks(self):
        """Check if landmarks should be displayed"""
        return self.get('settings.show_landmarks', True)
    
    def is_log_enabled(self):
        """Check if logging is enabled"""
        return self.get('settings.log_enabled', True)
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False


def load_config():
    """Backward compatibility function"""
    config_path = os.path.join("data", "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

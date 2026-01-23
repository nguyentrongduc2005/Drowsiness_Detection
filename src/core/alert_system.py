"""
Alert System Module - Hệ thống cảnh báo thông minh
Phân loại và xử lý các loại cảnh báo khác nhau
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time


class AlertType(Enum):
    """Các loại cảnh báo"""
    # Ngủ gật (Drowsiness)
    DROWSINESS = "drowsiness"           # Ngủ gật - Phát âm thanh cảnh báo
    MICROSLEEP = "microsleep"           # Ngủ vi giây - Cảnh báo khẩn
    SLEEPING = "sleeping"               # Đang ngủ - Cảnh báo nguy hiểm
    
    # Mất tập trung (Distraction)
    HEAD_TURN = "head_turn"             # Đầu quay sang hướng khác
    HEAD_DOWN = "head_down"             # Đầu cúi xuống (nhìn điện thoại)
    HEAD_TILT = "head_tilt"             # Đầu nghiêng sang bên
    
    # Mệt mỏi (Fatigue)
    FATIGUE_YAWN = "fatigue_yawn"       # Ngáp nhiều lần
    FATIGUE_BLINK = "fatigue_blink"     # Chớp mắt bất thường
    FATIGUE_COMBINED = "fatigue_combined" # Ngáp + chớp mắt = mệt mỏi
    
    # Cảnh báo sơ bộ
    PRE_WARNING = "pre_warning"         # Cảnh báo sớm (mắt nặng, staring)


class AlertSeverity(Enum):
    """Mức độ nghiêm trọng của cảnh báo"""
    INFO = 1        # Thông tin (xanh lá)
    WARNING = 2     # Cảnh báo (vàng/cam)
    DANGER = 3      # Nguy hiểm (đỏ)
    CRITICAL = 4    # Cực kỳ nguy hiểm (đỏ nhấp nháy)


@dataclass
class AlertConfig:
    """Cấu hình cho mỗi loại cảnh báo"""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    sound_file: Optional[str] = None
    color: tuple = (255, 255, 255)  # BGR color
    requires_immediate_action: bool = False
    cooldown_seconds: float = 3.0


class AlertSystem:
    """
    Hệ thống cảnh báo thông minh
    
    Tính năng:
    - Phân loại cảnh báo theo loại và mức độ
    - Quản lý cooldown để tránh spam
    - Đề xuất hành động cụ thể
    - Hỗ trợ nhiều ngôn ngữ
    """
    
    # Cấu hình cho từng loại cảnh báo
    ALERT_CONFIGS = {
        AlertType.DROWSINESS: AlertConfig(
            alert_type=AlertType.DROWSINESS,
            severity=AlertSeverity.WARNING,
            title="WARNING: DROWSINESS DETECTED",
            message="Eyes closing! Stay alert!",
            sound_file="alarm.wav",
            color=(0, 165, 255),  # Orange
            requires_immediate_action=True,
            cooldown_seconds=1.0
        ),
        
        AlertType.MICROSLEEP: AlertConfig(
            alert_type=AlertType.MICROSLEEP,
            severity=AlertSeverity.DANGER,
            title="DANGER: MICROSLEEP DETECTED",
            message="Falling asleep! Stop the vehicle!",
            sound_file="alarm_loud.wav",
            color=(0, 0, 255),  # Red
            requires_immediate_action=True,
            cooldown_seconds=1.0
        ),
        
        AlertType.SLEEPING: AlertConfig(
            alert_type=AlertType.SLEEPING,
            severity=AlertSeverity.CRITICAL,
            title="CRITICAL: YOU ARE SLEEPING!",
            message="STOP VEHICLE IMMEDIATELY!",
            sound_file="alarm_critical.wav",
            color=(0, 0, 255),  # Red
            requires_immediate_action=True,
            cooldown_seconds=1.0
        ),
        
        AlertType.HEAD_TURN: AlertConfig(
            alert_type=AlertType.HEAD_TURN,
            severity=AlertSeverity.WARNING,
            title="WARNING: LOOKING AWAY",
            message="Look forward! Focus on driving!",
            sound_file="beep.wav",
            color=(0, 255, 255),  # Yellow
            requires_immediate_action=True,
            cooldown_seconds=1.0
        ),
        
        AlertType.HEAD_DOWN: AlertConfig(
            alert_type=AlertType.HEAD_DOWN,
            severity=AlertSeverity.DANGER,
            title="DANGER: HEAD DOWN",
            message="Look ahead! No phone while driving!",
            sound_file="alarm.wav",
            color=(0, 100, 255),  # Red-Orange
            requires_immediate_action=True,
            cooldown_seconds=1.0
        ),
        
        AlertType.HEAD_TILT: AlertConfig(
            alert_type=AlertType.HEAD_TILT,
            severity=AlertSeverity.WARNING,
            title="WARNING: HEAD TILTED",
            message="Head tilted sideways! Keep posture straight!",
            sound_file="beep.wav",
            color=(0, 255, 255),  # Yellow
            requires_immediate_action=False,
            cooldown_seconds=3.0
        ),
        
        AlertType.FATIGUE_YAWN: AlertConfig(
            alert_type=AlertType.FATIGUE_YAWN,
            severity=AlertSeverity.WARNING,
            title="WARNING: EXCESSIVE YAWNING",
            message="Multiple yawns detected. Should rest!",
            sound_file="beep.wav",  # ADDED SOUND!
            color=(255, 165, 0),  # Orange
            requires_immediate_action=False,
            cooldown_seconds=5.0  # Reduced from 30s
        ),
        
        AlertType.FATIGUE_BLINK: AlertConfig(
            alert_type=AlertType.FATIGUE_BLINK,
            severity=AlertSeverity.WARNING,
            title="WARNING: ABNORMAL BLINKING",
            message="Slow/infrequent blinking. Sign of fatigue!",
            sound_file="beep.wav",  # ADDED SOUND!
            color=(255, 200, 0),  # Yellow-Orange
            requires_immediate_action=False,
            cooldown_seconds=10.0  # Reduced from 30s
        ),
        
        AlertType.FATIGUE_COMBINED: AlertConfig(
            alert_type=AlertType.FATIGUE_COMBINED,
            severity=AlertSeverity.DANGER,
            title="DANGER: SEVERE FATIGUE",
            message="Multiple yawns + abnormal blinking = FATIGUE! Rest!",
            sound_file="alarm.wav",
            color=(255, 100, 0),  # Red-Orange
            requires_immediate_action=True,
            cooldown_seconds=2.0  # Reduced from 10s
        ),
        
        AlertType.PRE_WARNING: AlertConfig(
            alert_type=AlertType.PRE_WARNING,
            severity=AlertSeverity.INFO,
            title="INFO: EARLY WARNING",
            message="Eyes getting heavy. Be careful!",
            sound_file=None,
            color=(100, 255, 100),  # Light Green
            requires_immediate_action=False,
            cooldown_seconds=60.0
        ),
    }
    
    def __init__(self):
        """Khởi tạo Alert System"""
        self.last_alert_times = {}  # Track last alert time for each type
        self.current_alerts = []     # Active alerts
        self.alert_history = []      # History of all alerts
        
    def trigger_alert(self, alert_type: AlertType, context: dict = None) -> Optional[AlertConfig]:
        """
        Kích hoạt cảnh báo
        
        Args:
            alert_type: Loại cảnh báo
            context: Thông tin bổ sung (thời gian, giá trị EAR/MAR, etc.)
            
        Returns:
            AlertConfig nếu alert được trigger, None nếu trong cooldown
        """
        current_time = time.time()
        config = self.ALERT_CONFIGS.get(alert_type)
        
        if config is None:
            return None
        
        # Check cooldown
        last_time = self.last_alert_times.get(alert_type, 0)
        if current_time - last_time < config.cooldown_seconds:
            return None  # Still in cooldown
        
        # Update last alert time
        self.last_alert_times[alert_type] = current_time
        
        # Add to history
        alert_record = {
            'type': alert_type,
            'config': config,
            'time': current_time,
            'context': context or {}
        }
        self.alert_history.append(alert_record)
        
        # Keep only recent history (last 100 alerts)
        if len(self.alert_history) > 100:
            self.alert_history.pop(0)
        
        return config
    
    def get_alert_message(self, alert_type: AlertType, context: dict = None) -> str:
        """Lấy thông điệp cảnh báo với context"""
        config = self.ALERT_CONFIGS.get(alert_type)
        if config is None:
            return ""
        
        message = f"{config.title}\n{config.message}"
        
        # Add context information
        if context:
            if 'duration' in context:
                message += f"\nThời gian: {context['duration']:.1f}s"
            if 'count' in context:
                message += f"\nSố lần: {context['count']}"
        
        return message
    
    def get_recommended_action(self, alert_type: AlertType) -> str:
        """Get recommended action for each alert type"""
        actions = {
            AlertType.DROWSINESS: "Blink hard, sit up straight!",
            AlertType.MICROSLEEP: "Stop vehicle safely immediately!",
            AlertType.SLEEPING: "EMERGENCY STOP! YOU ARE SLEEPING!",
            AlertType.HEAD_TURN: "Look straight ahead!",
            AlertType.HEAD_DOWN: "Head up! No phone while driving!",
            AlertType.HEAD_TILT: "Keep head straight, adjust posture!",
            AlertType.FATIGUE_YAWN: "Find a safe place to rest!",
            AlertType.FATIGUE_BLINK: "Attention! Signs of fatigue detected!",
            AlertType.FATIGUE_COMBINED: "Stop and rest for 15-20 minutes!",
            AlertType.PRE_WARNING: "Stay alert and focused!",
        }
        return actions.get(alert_type, "Be careful!")
    
    def should_play_sound(self, alert_type: AlertType) -> bool:
        """Check if sound should be played"""
        config = self.ALERT_CONFIGS.get(alert_type)
        return config and config.sound_file is not None
    
    def get_sound_file(self, alert_type: AlertType) -> Optional[str]:
        """Get sound file for alert"""
        config = self.ALERT_CONFIGS.get(alert_type)
        return config.sound_file if config else None
    
    def clear_cooldowns(self):
        """Clear all cooldowns (used for reset)"""
        self.last_alert_times.clear()
    
    def get_statistics(self) -> dict:
        """Thống kê cảnh báo"""
        stats = {
            'total_alerts': len(self.alert_history),
            'by_type': {},
            'by_severity': {
                AlertSeverity.INFO: 0,
                AlertSeverity.WARNING: 0,
                AlertSeverity.DANGER: 0,
                AlertSeverity.CRITICAL: 0,
            }
        }
        
        for record in self.alert_history:
            alert_type = record['type']
            config = record['config']
            
            # Count by type
            stats['by_type'][alert_type.value] = stats['by_type'].get(alert_type.value, 0) + 1
            
            # Count by severity
            stats['by_severity'][config.severity] += 1
        
        return stats

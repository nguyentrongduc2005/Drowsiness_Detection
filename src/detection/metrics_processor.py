"""
Metrics Processor - Tính toán EAR, MAR, blink, yawn
"""
import numpy as np
import time
from typing import Tuple
from collections import deque


class MetricsProcessor:
    """Xử lý các metrics phát hiện buồn ngủ"""
    
    def __init__(self, config_manager):
        """
        Khởi tạo MetricsProcessor
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        
        # Counters
        self.ear_counter = 0
        self.mar_counter = 0
        self.blink_counter = 0
        
        # State
        self.is_drowsy = False
        self.is_yawning = False
        self.is_blinking = False
        self.prev_ear = None
        
        # Time tracking
        self.blink_times = deque(maxlen=100)
        self.yawn_times = deque(maxlen=100)
        
        # Fatigue cooldown
        self.last_fatigue_alert = 0
        self.fatigue_cooldown = 60  # Cooldown 60 giây sau mỗi lần cảnh báo
        self.fatigue_start_time = None  # Thời điểm bắt đầu theo dõi mệt mỏi
        self.fatigue_monitoring = False  # Có đang theo dõi mệt mỏi không
        
        # Smoothing
        self.ear_history = deque(maxlen=5)
        self.mar_history = deque(maxlen=5)
    
    def calculate_ear(self, eye_landmarks: np.ndarray) -> float:
        """
        Tính Eye Aspect Ratio
        
        Args:
            eye_landmarks: 6 điểm landmark của mắt
            
        Returns:
            Giá trị EAR
        """
        v1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        v2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        h = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        ear = (v1 + v2) / (2.0 * h)
        return ear
    
    def calculate_mar(self, mouth_landmarks: np.ndarray) -> float:
        """
        Tính Mouth Aspect Ratio chuẩn
        
        Args:
            mouth_landmarks: 8 điểm outer lip
            [0]=61 góc trái, [1]=291 góc phải
            [2]=0 trên giữa, [3]=17 dưới giữa
            [4]=39 trên trái, [5]=84 dưới trái
            [6]=269 trên phải, [7]=314 dưới phải
            
        Returns:
            Giá trị MAR (0.1-0.3 khi đóng, >0.5 khi ngáp)
        """
        # Khoảng cách dọc (chiều cao) ở 3 vị trí
        v1 = np.linalg.norm(mouth_landmarks[2] - mouth_landmarks[3])  # Giữa: 0-17
        v2 = np.linalg.norm(mouth_landmarks[4] - mouth_landmarks[5])  # Trái: 39-84
        v3 = np.linalg.norm(mouth_landmarks[6] - mouth_landmarks[7])  # Phải: 269-314
        
        # Khoảng cách ngang (chiều rộng)
        h = np.linalg.norm(mouth_landmarks[0] - mouth_landmarks[1])  # 61-291
        
        if h == 0:
            return 0.0
        
        # MAR = trung bình 3 chiều cao / chiều rộng
        mar = (v1 + v2 + v3) / (3.0 * h)
        return mar
    
    def process_metrics(self, left_eye: np.ndarray, right_eye: np.ndarray,
                       mouth: np.ndarray) -> Tuple[float, float]:
        """
        Xử lý tất cả metrics
        
        Args:
            left_eye: Landmarks mắt trái
            right_eye: Landmarks mắt phải
            mouth: Landmarks miệng
            
        Returns:
            (smoothed_ear, smoothed_mar)
        """
        # Tính EAR cho cả 2 mắt
        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Tính MAR
        mar = self.calculate_mar(mouth)
        
        # Smoothing
        self.ear_history.append(avg_ear)
        self.mar_history.append(mar)
        
        smoothed_ear = sum(self.ear_history) / len(self.ear_history)
        smoothed_mar = sum(self.mar_history) / len(self.mar_history)
        
        return smoothed_ear, smoothed_mar
    
    def detect_drowsiness(self, ear: float) -> bool:
        """
        Phát hiện buồn ngủ
        
        Args:
            ear: Giá trị EAR
            
        Returns:
            True nếu phát hiện ngủ
        """
        ear_threshold = self.config.get("thresholds.ear", 0.25)
        ear_consec_frames = self.config.get("consecutive_frames.drowsiness", 20)
        
        if ear < ear_threshold:
            self.ear_counter += 1
            
            if self.ear_counter >= ear_consec_frames:
                if not self.is_drowsy:
                    self.is_drowsy = True
                return True
        else:
            if self.is_drowsy:
                self.is_drowsy = False
            self.ear_counter = 0
        
        return False
    
    def detect_blink(self, ear: float) -> bool:
        """
        Phát hiện nhấp mắt
        
        Args:
            ear: Giá trị EAR
            
        Returns:
            True nếu phát hiện blink hoàn chỉnh
        """
        blink_threshold = self.config.get("thresholds.blink", 0.25)
        
        if self.prev_ear is not None:
            # Phát hiện mắt đóng
            if ear < blink_threshold and self.prev_ear >= blink_threshold:
                self.is_blinking = True
            # Phát hiện mắt mở (blink hoàn chỉnh)
            elif ear >= blink_threshold and self.is_blinking:
                self.is_blinking = False
                self.blink_counter += 1
                self.blink_times.append(time.time())
                self.prev_ear = ear
                return True
        
        self.prev_ear = ear
        return False
    
    def detect_yawn(self, mar: float) -> bool:
        """
        Phát hiện ngáp - Chỉ cần há miệng rộng (cho phép mắt nhắm)
        
        Args:
            mar: Giá trị MAR
            
        Returns:
            True nếu đang ngáp
        """
        mar_threshold = self.config.get("thresholds.yawn", 0.65)
        yawn_consec_frames = self.config.get("consecutive_frames.yawn", 20)
        
        # Kiểm tra há miệng rộng - không quan tâm mắt
        if mar > mar_threshold:
            self.mar_counter += 1
            
            if self.mar_counter >= yawn_consec_frames:
                if not self.is_yawning:
                    self.is_yawning = True
                    self.yawn_times.append(time.time())
                return True
        else:
            self.mar_counter = 0
            self.is_yawning = False
        
        return False
    
    def is_mouth_wide_open(self, mar: float) -> bool:
        """
        Kiểm tra miệng đang há rộng (nghi ngờ ngáp)
        
        Args:
            mar: Giá trị MAR
            
        Returns:
            True nếu miệng há rộng
        """
        mar_threshold = self.config.get("thresholds.yawn", 0.65)
        return mar > mar_threshold
    
    def check_fatigue(self) -> bool:
        """
        Kiểm tra mệt mỏi - CHỈ BÁO SAU KHI ĐỦ 60 GIÂY:
        - Đếm ngáp và blink trong 60 giây
        - Sau 60 giây, nếu ngáp >= 2 VÀ blink bất thường → Báo fatigue
        - Báo liên tục cho đến khi chỉ số giảm
        
        Returns:
            True nếu phát hiện mệt mỏi (sau 60 giây theo dõi)
        """
        current_time = time.time()
        
        # Đếm trong 60 giây gần nhất
        recent_blinks = sum(1 for t in self.blink_times if current_time - t < 60)
        recent_yawns = sum(1 for t in self.yawn_times if current_time - t < 60)
        
        # Điều kiện phát hiện mệt mỏi
        has_multiple_yawns = recent_yawns >= 2
        abnormal_blink = recent_blinks < 10 or recent_blinks >= 20
        is_fatigue_condition = has_multiple_yawns and abnormal_blink
        
        # Nếu chưa bắt đầu theo dõi và có dấu hiệu mệt mỏi → Bắt đầu đếm 60s
        if not self.fatigue_monitoring and is_fatigue_condition:
            self.fatigue_monitoring = True
            self.fatigue_start_time = current_time
            print(f"[Fatigue] Bắt đầu theo dõi: yawns={recent_yawns}, blinks={recent_blinks}")
            return False  # Chưa báo, đang đếm
        
        # Nếu đang theo dõi
        if self.fatigue_monitoring:
            elapsed = current_time - self.fatigue_start_time
            
            # Nếu chưa đủ 60 giây → Tiếp tục đếm
            if elapsed < 60:
                return False
            
            # Đã đủ 60 giây → Kiểm tra lại điều kiện
            if is_fatigue_condition:
                print(f"[Fatigue] ĐỦ 60s! Báo cảnh báo: yawns={recent_yawns}, blinks={recent_blinks}")
                return True  # BÁO CẢNH BÁO!
            else:
                # Hết mệt mỏi → Reset
                print(f"[Fatigue] Hết mệt mỏi sau 60s")
                self.fatigue_monitoring = False
                self.fatigue_start_time = None
                return False
        
        return False
    
    def get_blink_rate(self) -> int:
        """Lấy số lần blink/phút"""
        current_time = time.time()
        return sum(1 for t in self.blink_times if current_time - t < 60)
    
    def get_yawn_count(self) -> int:
        """Lấy số lần ngáp/phút"""
        current_time = time.time()
        return sum(1 for t in self.yawn_times if current_time - t < 60)
    
    def reset(self):
        """Reset tất cả counters"""
        self.ear_counter = 0
        self.mar_counter = 0
        self.blink_counter = 0
        self.is_drowsy = False
        self.is_yawning = False
        self.is_blinking = False
        self.prev_ear = None
        self.blink_times.clear()
        self.yawn_times.clear()
        self.ear_history.clear()
        self.mar_history.clear()
        self.last_fatigue_alert = 0
        self.fatigue_start_time = None
        self.fatigue_monitoring = False

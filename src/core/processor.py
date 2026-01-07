"""
Module Logic: Tính toán EAR, MAR và quản lý ngưỡng thích nghi
"""
import numpy as np
from collections import deque
from scipy.spatial import distance as dist
from .config import Config


def calculate_ear(eye_points):
    """
    Tính Eye Aspect Ratio (EAR)
    
    Công thức EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    
    Args:
        eye_points: List 6 điểm (x, y) của mắt
        
    Returns:
        float: Giá trị EAR (thường từ 0.0 đến 0.4)
    """
    if eye_points is None or len(eye_points) != 6:
        return 0.0
    
    # Tính khoảng cách dọc
    A = dist.euclidean(eye_points[1], eye_points[5])
    B = dist.euclidean(eye_points[2], eye_points[4])
    
    # Tính khoảng cách ngang
    C = dist.euclidean(eye_points[0], eye_points[3])
    
    # Tính EAR
    if C == 0:
        return 0.0
    
    ear = (A + B) / (2.0 * C)
    
    return ear


def calculate_mar(mouth_points):
    """
    Tính Mouth Aspect Ratio (MAR)
    
    Dùng để phát hiện ngáp
    
    Args:
        mouth_points: List các điểm (x, y) của miệng (20 điểm)
        
    Returns:
        float: Giá trị MAR
    """
    if mouth_points is None or len(mouth_points) < 20:
        return 0.0
    
    # Tính khoảng cách dọc (giữa môi trên và môi dưới)
    A = dist.euclidean(mouth_points[2], mouth_points[10])   # 50 -> 58
    B = dist.euclidean(mouth_points[4], mouth_points[8])    # 52 -> 56
    
    # Tính khoảng cách ngang
    C = dist.euclidean(mouth_points[0], mouth_points[6])    # 48 -> 54
    
    if C == 0:
        return 0.0
    
    mar = (A + B) / (2.0 * C)
    
    return mar


class SmartThreshold:
    """
    Class quản lý ngưỡng thích nghi dựa trên lịch sử EAR của người dùng
    """
    
    def __init__(self, config=None):
        """
        Khởi tạo SmartThreshold
        
        Args:
            config: Đối tượng Config để lấy cấu hình
        """
        if config is None:
            config = Config()
        
        self.config = config
        self.window_size = config.get_window_size()
        self.history = deque(maxlen=self.window_size)
        self.default_threshold = config.get_ear_default()
        self.min_samples_for_learning = config.get_min_samples()
        self.threshold_multiplier = config.get('smart_threshold.threshold_multiplier', 0.75)
        self.min_ear_threshold = config.get('eye_thresholds.min_ear_threshold', 0.18)
        self.max_ear_threshold = config.get('eye_thresholds.max_ear_threshold', 0.30)
        
    def update_threshold(self, current_ear):
        """
        Cập nhật ngưỡng dựa trên EAR hiện tại
        
        Logic:
        - Nếu current_ear > 0.2: Thêm vào history (mắt đang mở)
        - Nếu len(history) < 100: Trả về (Ngưỡng mặc định, False)
        - Nếu len(history) >= 100: Tính trung bình 50% giá trị cao nhất → Trả về (Ngưỡng mới, True)
        
        Args:
            current_ear: Giá trị EAR hiện tại
            
        Returns:
            tuple: (threshold, is_calibrated)
                - threshold: Ngưỡng để so sánh
                - is_calibrated: True nếu đã hiệu chỉnh, False nếu đang học
        """
        # Chỉ thêm vào history nếu EAR > 0.2 (mắt đang mở rõ ràng)
        if current_ear > 0.2:
            self.history.append(current_ear)
        
        # Nếu chưa đủ dữ liệu, dùng ngưỡng mặc định
        if len(self.history) < self.min_samples_for_learning:
            return self.default_threshold, False
        
        # Đã đủ dữ liệu, tính ngưỡng thích nghi
        # Lấy 50% giá trị cao nhất để tính trung bình
        sorted_history = sorted(self.history, reverse=True)
        top_50_percent = sorted_history[:len(sorted_history) // 2]
        
        # Tính trung bình
        avg_ear = np.mean(top_50_percent)
        
        # Ngưỡng = threshold_multiplier * giá trị trung bình
        adaptive_threshold = avg_ear * self.threshold_multiplier
        
        # Đảm bảo ngưỡng trong khoảng hợp lý
        adaptive_threshold = max(self.min_ear_threshold, min(self.max_ear_threshold, adaptive_threshold))
        
        return adaptive_threshold, True
    
    def get_status_text(self):
        """
        Lấy text trạng thái hiện tại
        
        Returns:
            str: Trạng thái của hệ thống
        """
        if len(self.history) < self.min_samples_for_learning:
            progress = len(self.history)
            total = self.min_samples_for_learning
            return f"Đang học: {progress}/{total} mẫu"
        else:
            return "Đang bảo vệ"
    
    def reset(self):
        """Reset lại lịch sử"""
        self.history.clear()


class DrowsinessDetector:
    """
    Class tổng hợp để phát hiện buồn ngủ
    """
    
    def __init__(self, config=None):
        """
        Khởi tạo detector
        
        Args:
            config: Đối tượng Config để lấy cấu hình
        """
        if config is None:
            config = Config()
        
        self.config = config
        self.consec_frames = config.get_consecutive_frames()
        self.yawn_frames = config.get('mouth_thresholds.yawn_frames', 30)
        self.mar_threshold = config.get('mouth_thresholds.mar_limit', 0.6)
        self.counter = 0
        self.yawn_counter = 0
        self.is_drowsy = False
        self.is_yawning = False
        self.smart_threshold = SmartThreshold(config)
        
        # Theo dõi ngáp và chớp mắt
        self.yawn_count_total = 0  # Tổng số lần ngáp
        self.last_yawn_state = False  # Trạng thái ngáp trước đó
        self.blink_count = 0  # Số lần chớp mắt
        self.last_eye_state = "open"  # "open" hoặc "closed"
        self.frame_counter = 0  # Đếm frame để tính chu kỳ
        
        # Lịch sử ngáp (lưu 60 giây gần nhất)
        from collections import deque
        self.yawn_history = deque(maxlen=1800)  # 30 fps * 60s = 1800 frames
        self.blink_history = deque(maxlen=1800)
        
    def process(self, left_eye, right_eye, mouth=None):
        """
        Xử lý phát hiện buồn ngủ và ngáp
        
        Args:
            left_eye: Tọa độ 6 điểm mắt trái
            right_eye: Tọa độ 6 điểm mắt phải
            mouth: Tọa độ các điểm miệng (20 điểm)
            
        Returns:
            dict: {
                'ear': Giá trị EAR trung bình,
                'mar': Giá trị MAR,
                'threshold': Ngưỡng hiện tại,
                'is_drowsy': True nếu buồn ngủ,
                'is_yawning': True nếu đang ngáp,
                'status': Text trạng thái,
                'is_calibrated': True nếu đã hiệu chỉnh
            }
        """
        # Tính EAR cho cả 2 mắt
        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        
        # Lấy giá trị trung bình
        ear = (left_ear + right_ear) / 2.0
        
        # Tính MAR nếu có thông tin miệng
        mar = 0.0
        if mouth is not None:
            mar = calculate_mar(mouth)
        
        # Cập nhật ngưỡng thích nghi
        threshold, is_calibrated = self.smart_threshold.update_threshold(ear)
        current_eye_state = ""
        # Kiểm tra buồn ngủ (EAR thấp - nhắm mắt lâu)
        if ear < threshold:
            self.counter += 1
            current_eye_state = "closed"
            
            if self.counter >= self.consec_frames:
                self.is_drowsy = True
            else:
                self.is_drowsy = False
        else:
            # Đếm chớp mắt khi mở mắt trở lại sau khi nhắm
            if self.last_eye_state == "closed" and self.counter < self.consec_frames:
                self.blink_count += 1
                self.blink_history.append(1)
            
            self.counter = 0
            self.is_drowsy = False
            current_eye_state = "open"
        
        self.last_eye_state = current_eye_state
        
        # Kiểm tra ngáp (MAR cao)
        if mar > self.mar_threshold:
            self.yawn_counter += 1
            
            # Chỉ đếm là 1 lần ngáp khi đạt đủ số frame
            if self.yawn_counter >= self.yawn_frames and not self.last_yawn_state:
                self.yawn_count_total += 1
                self.yawn_history.append(1)
                self.last_yawn_state = True
                self.is_yawning = True
        else:
            self.yawn_counter = 0
            self.last_yawn_state = False
            self.is_yawning = False
        
        # Cập nhật frame counter
        self.frame_counter += 1
        
        # Thêm 0 vào history nếu không có sự kiện
        if not self.is_yawning and self.frame_counter % 30 == 0:  # Mỗi 30 frame
            self.yawn_history.append(0)
        if current_eye_state == "open" and self.frame_counter % 30 == 0:
            self.blink_history.append(0)
        
        # Tính số lần ngáp trong 60 giây gần nhất
        recent_yawn_count = sum(self.yawn_history)
        
        # Tính tần suất chớp mắt (số lần/phút)
        if len(self.blink_history) > 0:
            blink_rate = (sum(self.blink_history) / len(self.blink_history)) * 1800  # Ước tính cho 1 phút
        else:
            blink_rate = 0
        
        # LOGIC CẢNH BÁO MỚI:
        # Cảnh báo khi:
        # 1. Nhắm mắt lâu (is_drowsy = True) HOẶC
        # 2. Ngáp nhiều (>= 3 lần trong 60s) VÀ chớp mắt giảm (<= 10 lần/phút)
        warning = False
        warning_reason = ""
        
        if self.is_drowsy:
            warning = True
            warning_reason = "Eyes closed"
        elif recent_yawn_count >= 3 and blink_rate <= 10:
            warning = True
            warning_reason = f"Frequent yawning ({recent_yawn_count}x) + Low blink rate"
        
        # Lấy text trạng thái
        status = self.smart_threshold.get_status_text()
        
        return {
            'ear': ear,
            'mar': mar,
            'threshold': threshold,
            'is_drowsy': self.is_drowsy,
            'is_yawning': self.is_yawning,
            'warning': warning,
            'warning_reason': warning_reason,
            'status': status,
            'is_calibrated': is_calibrated,
            'counter': self.counter,
            'yawn_counter': self.yawn_counter,
            'yawn_count_total': recent_yawn_count,
            'blink_rate': blink_rate
        }
    
    def reset(self):
        """Reset detector"""
        self.counter = 0
        self.yawn_counter = 0
        self.is_drowsy = False
        self.is_yawning = False
        self.yawn_count_total = 0
        self.blink_count = 0
        self.last_yawn_state = False
        self.last_eye_state = "open"
        self.frame_counter = 0
        self.yawn_history.clear()
        self.blink_history.clear()
        self.smart_threshold.reset()

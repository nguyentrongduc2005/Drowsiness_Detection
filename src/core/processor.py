"""
Module Logic: Tính toán EAR, MAR, PERCLOS và quản lý ngưỡng thích nghi
"""
import numpy as np
from collections import deque
import time


# Inline euclidean distance (nhanh hơn scipy 3-5x)
def _fast_dist(p1, p2):
    """Tính khoảng cách Euclidean nhanh"""
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return (dx * dx + dy * dy) ** 0.5


class PERCLOSCalculator:
    """
    Calculator cho PERCLOS (Percentage of Eye Closure)
    
    PERCLOS là tỷ lệ % thời gian mắt nhắm (>80% nhắm) trong khoảng thời gian.
    Theo nghiên cứu, PERCLOS > 15% là dấu hiệu buồn ngủ.
    PERCLOS > 25% là buồn ngủ nghiêm trọng.
    """
    
    # Ngưỡng cảnh báo
    PERCLOS_WARNING = 0.15   # 15% - Cảnh báo nhẹ
    PERCLOS_DANGER = 0.25    # 25% - Nguy hiểm
    
    def __init__(self, window_seconds=60, sample_rate=30):
        """
        Khởi tạo PERCLOS calculator
        
        Args:
            window_seconds: Khoảng thời gian tính PERCLOS (giây)
            sample_rate: Số sample/giây (xấp xỉ FPS)
        """
        self.window_seconds = window_seconds
        self.sample_rate = sample_rate
        max_samples = window_seconds * sample_rate
        
        # Lưu trạng thái mắt (True = nhắm, False = mở)
        self.eye_states = deque(maxlen=max_samples)
        self.timestamps = deque(maxlen=max_samples)
        
        # Cache để tối ưu
        self._last_perclos = 0.0
        self._last_calc_time = 0
        self._calc_interval = 0.5  # Tính lại mỗi 0.5 giây
    
    def update(self, ear, threshold):
        """
        Cập nhật trạng thái mắt
        
        Args:
            ear: Giá trị EAR hiện tại
            threshold: Ngưỡng EAR
            
        Returns:
            float: Giá trị PERCLOS (0-1)
        """
        now = time.time()
        
        # Mắt nhắm nếu EAR < 80% threshold (gần nhắm hoàn toàn)
        is_closed = ear < (threshold * 0.8)
        
        self.eye_states.append(is_closed)
        self.timestamps.append(now)
        
        # Tính PERCLOS (với cache để tối ưu)
        if now - self._last_calc_time >= self._calc_interval:
            self._last_perclos = self._calculate_perclos()
            self._last_calc_time = now
        
        return self._last_perclos
    
    def _calculate_perclos(self):
        """
        Tính PERCLOS trong window
        
        Returns:
            float: Tỷ lệ mắt nhắm (0-1)
        """
        if len(self.eye_states) < 10:
            return 0.0
        
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Đếm số frame mắt nhắm trong window
        closed_count = 0
        total_count = 0
        
        for i, (state, ts) in enumerate(zip(self.eye_states, self.timestamps)):
            if ts >= cutoff:
                total_count += 1
                if state:
                    closed_count += 1
        
        if total_count == 0:
            return 0.0
        
        return closed_count / total_count
    
    def get_status(self):
        """
        Lấy trạng thái PERCLOS
        
        Returns:
            tuple: (perclos_value, status_text, is_warning, is_danger)
        """
        perclos = self._last_perclos
        
        if perclos >= self.PERCLOS_DANGER:
            return (perclos, "NGUY HIỂM", True, True)
        elif perclos >= self.PERCLOS_WARNING:
            return (perclos, "Cảnh báo", True, False)
        else:
            return (perclos, "Bình thường", False, False)
    
    def reset(self):
        """Reset calculator"""
        self.eye_states.clear()
        self.timestamps.clear()
        self._last_perclos = 0.0


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
    
    # Tính khoảng cách dọc (inline để tối ưu)
    A = _fast_dist(eye_points[1], eye_points[5])
    B = _fast_dist(eye_points[2], eye_points[4])
    
    # Tính khoảng cách ngang
    C = _fast_dist(eye_points[0], eye_points[3])
    
    # Tính EAR (tránh chia 0)
    if C < 1e-6:
        return 0.0
    
    return (A + B) / (2.0 * C)


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
    A = _fast_dist(mouth_points[2], mouth_points[10])   # 50 -> 58
    B = _fast_dist(mouth_points[4], mouth_points[8])    # 52 -> 56
    
    # Tính khoảng cách ngang
    C = _fast_dist(mouth_points[0], mouth_points[6])    # 48 -> 54
    
    if C < 1e-6:
        return 0.0
    
    return (A + B) / (2.0 * C)


class SmartThreshold:
    """
    Class quản lý ngưỡng thích nghi dựa trên lịch sử EAR của người dùng
    Học theo 3 bước có hướng dẫn, có phát hiện và nhắc nhở khi người dùng không thể hiện đúng
    """
    
    # Các bước học
    STEP_INIT = 0           # Chờ khởi động
    STEP_FACE_DETECT = 1    # Bước 1: Phát hiện khuôn mặt
    STEP_EYES_OPEN = 2      # Bước 2: Học trạng thái mắt mở
    STEP_COMPLETE = 3       # Hoàn tất
    
    # Ngưỡng cho từng bước
    SAMPLES_FACE_DETECT = 20    # Cần 20 frame phát hiện mặt liên tục
    SAMPLES_EYES_LEARNING = 100 # Cần 100 mẫu EAR để học ngưỡng
    
    # Timeout settings (số frame)
    TIMEOUT_NO_FACE = 30        # Nếu không có mặt sau 30 frame -> cảnh báo
    TIMEOUT_EYES_CLOSED = 20    # Nếu mắt nhắm sau 20 frame liên tiếp -> cảnh báo
    TIMEOUT_UNSTABLE = 50       # Nếu EAR không ổn định sau 50 frame -> cảnh báo
    
    def __init__(self, window_size=150):
        """
        Khởi tạo SmartThreshold
        
        Args:
            window_size: Kích thước cửa sổ lưu lịch sử EAR
        """
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
        self.default_threshold = 0.25
        self.min_samples_for_learning = self.SAMPLES_EYES_LEARNING
        
        # Trạng thái học
        self.current_step = self.STEP_INIT
        self.face_detect_count = 0  # Số frame liên tiếp phát hiện mặt
        self.is_started = False
        
        # Cache để tối ưu hiệu suất
        self._cache_counter = 0
        self._cached_threshold = self.default_threshold
        
        # Tracking cho warnings
        self._no_face_count = 0         # Đếm frame không có mặt liên tiếp
        self._eyes_closed_count = 0     # Đếm frame mắt nhắm liên tiếp
        self._unstable_count = 0        # Đếm frame EAR không ổn định
        self._warning_message = ""      # Thông báo cảnh báo hiện tại
        self._is_paused = False         # Đang tạm dừng do người dùng không thể hiện đúng
    
    def start_calibration(self):
        """Bắt đầu quá trình calibration"""
        self.is_started = True
        self.current_step = self.STEP_FACE_DETECT
        self.face_detect_count = 0
        self.history.clear()
        self._reset_warning_counters()
    
    def _reset_warning_counters(self):
        """Reset các bộ đếm cảnh báo"""
        self._no_face_count = 0
        self._eyes_closed_count = 0
        self._unstable_count = 0
        self._warning_message = ""
        self._is_paused = False
    
    def update_face_detection(self, face_detected):
        """
        Cập nhật trạng thái phát hiện mặt
        
        Args:
            face_detected: True nếu phát hiện được khuôn mặt
        """
        if not self.is_started:
            return
            
        if self.current_step == self.STEP_FACE_DETECT:
            if face_detected:
                self.face_detect_count += 1
                self._no_face_count = 0
                self._warning_message = ""
                self._is_paused = False
                
                # Đã phát hiện mặt đủ lâu, chuyển sang bước tiếp theo
                if self.face_detect_count >= self.SAMPLES_FACE_DETECT:
                    self.current_step = self.STEP_EYES_OPEN
                    self._reset_warning_counters()
            else:
                # Tăng đếm không có mặt
                self._no_face_count += 1
                # Giảm tiến trình
                self.face_detect_count = max(0, self.face_detect_count - 2)
                
                # Kiểm tra timeout
                if self._no_face_count >= self.TIMEOUT_NO_FACE:
                    self._is_paused = True
                    self._warning_message = "⚠️ Không thấy khuôn mặt! Hãy nhìn thẳng vào camera."
        
        elif self.current_step == self.STEP_EYES_OPEN:
            if not face_detected:
                self._no_face_count += 1
                if self._no_face_count >= self.TIMEOUT_NO_FACE:
                    self._is_paused = True
                    self._warning_message = "⚠️ Mất khuôn mặt! Hãy nhìn vào camera."
            else:
                self._no_face_count = 0
                if self._warning_message.startswith("⚠️ Mất") or self._warning_message.startswith("⚠️ Không thấy"):
                    self._warning_message = ""
                    self._is_paused = False
        
    def update_threshold(self, current_ear):
        """
        Cập nhật ngưỡng dựa trên EAR hiện tại
        
        Args:
            current_ear: Giá trị EAR hiện tại
            
        Returns:
            tuple: (threshold, is_calibrated)
        """
        # Nếu chưa bắt đầu hoặc đang ở bước phát hiện mặt
        if not self.is_started or self.current_step < self.STEP_EYES_OPEN:
            return self.default_threshold, False
        
        # Bước 2: Học trạng thái mắt mở
        if self.current_step == self.STEP_EYES_OPEN:
            # Kiểm tra mắt có đang nhắm không (EAR quá thấp)
            if current_ear < 0.18:
                self._eyes_closed_count += 1
                
                # Nếu mắt nhắm quá lâu, tạm dừng và nhắc nhở
                if self._eyes_closed_count >= self.TIMEOUT_EYES_CLOSED:
                    self._is_paused = True
                    self._warning_message = "⚠️ Phát hiện mắt nhắm! Hãy mở mắt bình thường."
            elif current_ear > 0.2:
                # Mắt mở rõ ràng - thêm vào history
                self._eyes_closed_count = 0
                if self._warning_message.startswith("⚠️ Phát hiện mắt"):
                    self._warning_message = ""
                    self._is_paused = False
                
                self.history.append(current_ear)
            
            history_len = len(self.history)
            
            # Kiểm tra đã đủ mẫu chưa
            if history_len >= self.min_samples_for_learning:
                self.current_step = self.STEP_COMPLETE
        
        # Nếu chưa đủ dữ liệu, dùng ngưỡng mặc định
        if len(self.history) < self.min_samples_for_learning:
            return self.default_threshold, False
        
        # Đã hoàn tất, tính ngưỡng thích nghi
        # Chỉ tính lại ngưỡng mỗi 10 frame để tiết kiệm CPU
        if not hasattr(self, '_cache_counter'):
            self._cache_counter = 0
            self._cached_threshold = self.default_threshold
        
        self._cache_counter += 1
        if self._cache_counter % 10 != 0 and self._cached_threshold != self.default_threshold:
            return self._cached_threshold, True
        
        # Tính ngưỡng thích nghi với numpy
        arr = np.array(self.history)
        percentile_50 = np.percentile(arr, 50)
        top_values = arr[arr >= percentile_50]
        
        avg_ear = np.mean(top_values) if len(top_values) > 0 else np.mean(arr)
        adaptive_threshold = avg_ear * 0.75
        adaptive_threshold = max(0.18, min(0.30, adaptive_threshold))
        
        self._cached_threshold = adaptive_threshold
        return adaptive_threshold, True
    
    def get_step_info(self):
        """
        Lấy thông tin bước hiện tại
        
        Returns:
            dict: {
                'step': int (0-3),
                'step_name': str,
                'instruction': str,
                'progress': int (0-100),
                'is_complete': bool,
                'is_paused': bool,
                'warning': str
            }
        """
        base_info = {
            'is_paused': self._is_paused,
            'warning': self._warning_message
        }
        
        if self.current_step == self.STEP_INIT:
            return {
                **base_info,
                'step': 0,
                'step_name': 'Chờ khởi động',
                'instruction': 'Nhấn "Bắt đầu" để khởi động hệ thống',
                'progress': 0,
                'is_complete': False
            }
        elif self.current_step == self.STEP_FACE_DETECT:
            progress = int((self.face_detect_count / self.SAMPLES_FACE_DETECT) * 100)
            instruction = self._warning_message if self._is_paused else '👤 Hãy nhìn thẳng vào camera và giữ yên'
            return {
                **base_info,
                'step': 1,
                'step_name': 'Bước 1: Nhận diện khuôn mặt',
                'instruction': instruction,
                'progress': min(progress, 100),
                'is_complete': False
            }
        elif self.current_step == self.STEP_EYES_OPEN:
            progress = int((len(self.history) / self.min_samples_for_learning) * 100)
            instruction = self._warning_message if self._is_paused else '👁 Mở mắt bình thường, nhìn vào camera'
            return {
                **base_info,
                'step': 2,
                'step_name': 'Bước 2: Học trạng thái mắt',
                'instruction': instruction,
                'progress': min(progress, 100),
                'is_complete': False
            }
        else:  # STEP_COMPLETE
            return {
                **base_info,
                'step': 3,
                'step_name': 'Hoàn tất calibration',
                'instruction': '✅ Hệ thống đang bảo vệ bạn!',
                'progress': 100,
                'is_complete': True
            }
    
    def get_status_text(self):
        """Lấy text trạng thái hiện tại"""
        info = self.get_step_info()
        if info['is_complete']:
            return "Đang bảo vệ"
        elif info['is_paused']:
            return "Tạm dừng"
        else:
            return f"Đang học: {info['progress']}%"
    
    def reset(self):
        """Reset lại lịch sử"""
        self.history.clear()
        self.current_step = self.STEP_INIT
        self.face_detect_count = 0
        self.is_started = False
        self._reset_warning_counters()
        if hasattr(self, '_cache_counter'):
            self._cache_counter = 0
            self._cached_threshold = self.default_threshold


class DrowsinessDetector:
    """
    Class tổng hợp để phát hiện buồn ngủ
    Sử dụng EAR, MAR, PERCLOS và các chỉ số khác
    """
    
    def __init__(self, consec_frames=20, yawn_frames=15):
        """
        Khởi tạo detector
        
        Args:
            consec_frames: Số frame liên tiếp mắt nhắm để cảnh báo
            yawn_frames: Số frame liên tiếp ngáp để đếm là 1 lần ngáp
        """
        self.consec_frames = consec_frames
        self.yawn_frames = yawn_frames
        self.counter = 0
        self.yawn_counter = 0
        self.is_drowsy = False
        self.is_yawning = False
        self.smart_threshold = SmartThreshold()
        
        # PERCLOS calculator
        self.perclos = PERCLOSCalculator(window_seconds=60, sample_rate=30)
        
        # Theo dõi ngáp và chớp mắt
        self.yawn_count_total = 0  # Tổng số lần ngáp
        self.last_yawn_state = False  # Trạng thái ngáp trước đó
        self.blink_count = 0  # Số lần chớp mắt
        self.last_eye_state = True  # True = open, False = closed (tối ưu so sánh)
        self.frame_counter = 0  # Đếm frame để tính chu kỳ
        
        # Lịch sử ngáp/chớp mắt (chỉ lưu timestamps thay vì toàn bộ frames)
        # Tiết kiệm bộ nhớ và tính toán nhanh hơn
        self._time_module = time
        self.yawn_timestamps = deque(maxlen=50)   # Lưu 50 lần ngáp gần nhất
        self.blink_timestamps = deque(maxlen=200) # Lưu 200 lần chớp mắt gần nhất
        
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
        
        # Cập nhật PERCLOS
        perclos_value = self.perclos.update(ear, threshold)
        perclos_status = self.perclos.get_status()
        
        now = self._time_module.time()
        
        # Kiểm tra buồn ngủ (EAR thấp - nhắm mắt lâu)
        eye_open = ear >= threshold
        
        if not eye_open:
            self.counter += 1
            self.is_drowsy = self.counter >= self.consec_frames
        else:
            # Đếm chớp mắt khi mở mắt trở lại sau khi nhắm ngắn
            if not self.last_eye_state and self.counter < self.consec_frames and self.counter >= 2:
                self.blink_count += 1
                self.blink_timestamps.append(now)
            
            self.counter = 0
            self.is_drowsy = False
        
        self.last_eye_state = eye_open
        
        # Kiểm tra ngáp (MAR cao) - tối ưu với ngưỡng động
        mar_threshold = 0.55  # Giảm ngưỡng để nhạy hơn
        is_mouth_open = mar > mar_threshold
        
        if is_mouth_open:
            self.yawn_counter += 1
            
            # Chỉ đếm là 1 lần ngáp khi đạt đủ số frame
            if self.yawn_counter >= self.yawn_frames and not self.last_yawn_state:
                self.yawn_count_total += 1
                self.yawn_timestamps.append(now)
                self.last_yawn_state = True
                self.is_yawning = True
        else:
            self.yawn_counter = 0
            self.last_yawn_state = False
            self.is_yawning = False
        
        self.frame_counter += 1
        
        # Tính số lần ngáp trong 60 giây gần nhất (dùng timestamps)
        cutoff_time = now - 60.0
        recent_yawn_count = sum(1 for t in self.yawn_timestamps if t > cutoff_time)
        
        # Tính tần suất chớp mắt (số lần/phút) từ timestamps
        recent_blinks = sum(1 for t in self.blink_timestamps if t > cutoff_time)
        blink_rate = recent_blinks  # Đã là số lần trong 60 giây = lần/phút
        
        # LOGIC CẢNH BÁO MỚI VỚI PERCLOS:
        # Cảnh báo khi:
        # 1. Nhắm mắt lâu (is_drowsy = True) HOẶC
        # 2. PERCLOS > 15% (ngưỡng cảnh báo) HOẶC
        # 3. Ngáp nhiều (>= 3 lần trong 60s) VÀ chớp mắt giảm (<= 10 lần/phút)
        warning = False
        warning_reason = ""
        
        if self.is_drowsy:
            warning = True
            warning_reason = "Eyes closed"
        elif perclos_status[3]:  # is_danger
            warning = True
            warning_reason = f"PERCLOS: {perclos_value*100:.1f}% - Nguy hiểm!"
        elif perclos_status[2]:  # is_warning
            warning = True
            warning_reason = f"PERCLOS: {perclos_value*100:.1f}% - Mắt nhắm nhiều"
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
            'blink_rate': blink_rate,
            'perclos': perclos_value,
            'perclos_status': perclos_status[1]
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
        self.last_eye_state = True
        self.frame_counter = 0
        self.yawn_timestamps.clear()
        self.blink_timestamps.clear()
        self.perclos.reset()
        self.smart_threshold.reset()

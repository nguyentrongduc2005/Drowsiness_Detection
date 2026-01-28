
"""
Detection Engine - Core processing loop chạy trong thread riêng
Giao tiếp với GUI qua PyQt signals
"""
import cv2
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Optional

from ..config import ConfigManager
from ..detection import FaceDetector, MetricsProcessor
from ..alert import AlertSystem, AlertLevel
from ..learning import LearningEngine


class DetectionEngine(QThread):
    """
    Engine xử lý detection chạy trong thread riêng
    Emit signals để giao tiếp với GUI
    """
    
    # Signals để giao tiếp với GUI
    frame_processed = pyqtSignal(np.ndarray, float)  # (frame, fps)
    face_detected = pyqtSignal(bool)  # True/False
    metrics_updated = pyqtSignal(dict)  # {"ear": float, "mar": float, ...}
    alert_changed = pyqtSignal(int)  # AlertLevel.value
    status_changed = pyqtSignal(str, str)  # (status_text, color)
    learning_progress = pyqtSignal(float)  # 0-100
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, config_manager: ConfigManager):
        """
        Khởi tạo DetectionEngine
        
        Args:
            config_manager: ConfigManager instance
        """
        super().__init__()
        
        self.config = config_manager
        
        # Components
        self.face_detector = FaceDetector()
        self.processor = MetricsProcessor(self.config)
        self.alert_system = AlertSystem(self.config)
        self.learning_engine = LearningEngine(self.config)
        
        # Video capture
        self.cap: Optional[cv2.VideoCapture] = None
        
        # Control flags
        self.is_running = False
        self.show_landmarks = True
        
        # FPS tracking
        self.prev_time = time.time()
        
    def run(self):
        """Main loop chạy trong thread riêng"""
        camera_index = self.config.get("camera.index", 0)
        
        try:
            # Thử mở camera với index được config
            self.cap = cv2.VideoCapture(camera_index)
            
            if not self.cap.isOpened():
                # Thử tự động tìm camera khác
                print(f"[Engine] Camera {camera_index} không mở được, đang thử camera khác...")
                found = False
                for i in range(3):  # Thử index 0, 1, 2
                    if i == camera_index:
                        continue
                    self.cap = cv2.VideoCapture(i)
                    if self.cap.isOpened():
                        test_ret, _ = self.cap.read()
                        if test_ret:
                            camera_index = i
                            found = True
                            print(f"[Engine] Tìm thấy camera tại index {i}")
                            break
                        else:
                            self.cap.release()
                
                if not found:
                    self.error_occurred.emit(
                        "Không tìm thấy camera khả dụng!\n\n"
                        "Kiểm tra:\n"
                        "1. Camera đã được cắm và bật\n"
                        "2. Đóng các app khác (Zoom, Teams, Chrome...)\n"
                        "3. Kiểm tra quyền camera trong Windows Settings"
                    )
                    return
            
            # Set camera properties
            width = self.config.get("camera.width", 640)
            height = self.config.get("camera.height", 480)
            fps = self.config.get("camera.fps", 30)
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            
            # Test đọc frame đầu tiên
            ret, test_frame = self.cap.read()
            if not ret:
                self.error_occurred.emit(
                    f"Camera {camera_index} mở được nhưng không đọc được frame.\n\n"
                    "Thử:\n"
                    "1. Đóng tất cả app đang dùng camera\n"
                    "2. Rút và cắm lại camera\n"
                    "3. Khởi động lại máy tính"
                )
                return
            
            print(f"[Engine] Camera {camera_index} khởi động: {width}x{height} @ {fps}fps")
            
            self.is_running = True
            frame_skip = 0
            max_frame_skip = 10
            
            while self.is_running:
                ret, frame = self.cap.read()
                
                if not ret:
                    frame_skip += 1
                    if frame_skip >= max_frame_skip:
                        self.error_occurred.emit("Mất kết nối camera sau nhiều lần thử")
                        break
                    self.msleep(50)
                    continue
                
                frame_skip = 0  # Reset counter khi đọc thành công
                
                # Lật ngang để hiệu ứng mirror
                frame = cv2.flip(frame, 1)
                
                # Tính FPS
                current_time = time.time()
                fps_value = 1 / (current_time - self.prev_time) if (current_time - self.prev_time) > 0 else 0
                self.prev_time = current_time
                
                # Xử lý detection
                self._process_frame(frame, fps_value)
                
                # Emit frame đã xử lý
                self.frame_processed.emit(frame, fps_value)
                
                # Small delay để không overload CPU
                self.msleep(10)  # 10ms delay
                
        except Exception as e:
            self.error_occurred.emit(f"Lỗi engine: {str(e)}")
        finally:
            self._cleanup()
    
    def _process_frame(self, frame: np.ndarray, fps: float):
        """
        Xử lý detection cho một frame
        
        Args:
            frame: Frame từ camera
            fps: FPS hiện tại
        """
        # Phát hiện khuôn mặt
        results = self.face_detector.process(frame)
        
        if results and results.multi_face_landmarks:
            self.face_detected.emit(True)
            
            h, w = frame.shape[:2]
            landmarks = self.face_detector.get_landmarks(results, (h, w))
            
            if landmarks is not None:
                # Lấy landmarks
                left_eye, right_eye = self.face_detector.get_eye_landmarks(landmarks)
                mouth = self.face_detector.get_mouth_landmarks(landmarks)
                
                # Tính metrics
                ear, mar = self.processor.process_metrics(left_eye, right_eye, mouth)
                
                # Tính chất lượng phát hiện (dựa vào khoảng cách giữa các điểm)
                eye_width = np.linalg.norm(left_eye[0] - left_eye[3])
                quality = min(1.0, eye_width / 30.0)  # Normalize, mắt rộ >30px là tốt
                
                # Lấy ngưỡng hiện tại
                ear_threshold = self.config.get("thresholds.ear", 0.25)
                
                # Chế độ học liên tục - CHỈ HỌC TRONG KHOẢNG GẦN NGƯỠNG
                if self.learning_engine.is_enabled():
                    # Chỉ học khi:
                    # - Mắt mở (EAR > 0.20) - không học lúc ngủ
                    # - Không quá cao (EAR < ngưỡng + 0.08) - không để ngưỡng tăng quá
                    # => Học trong khoảng hợp lý gần ngưỡng
                    is_in_learning_range = 0.20 < ear < (ear_threshold + 0.08)
                    if is_in_learning_range and quality >= 0.75:
                        self.learning_engine.add_sample(ear, mar, quality)
                        progress = self.learning_engine.get_progress()
                        if progress > 0:
                            self.learning_progress.emit(progress)
                
                # Phát hiện các trạng thái
                # Kiểm tra ngáp (không hiển thị ngay, chỉ đếm số lần)
                self.processor.detect_yawn(mar)
                
                # Kiểm tra miệng có đang há rộng không (nghi ngờ ngáp)
                is_mouth_wide = self.processor.is_mouth_wide_open(mar)
                
                # Kiểm tra mệt mỏi (ngáp nhiều + blink bất thường)
                is_fatigued = self.processor.check_fatigue()
                
                # Kiểm tra drowsy - CHỈ KHI miệng KHÔNG há rộng và KHÔNG mệt mỏi
                # (Tránh nhầm: khi ngáp mắt nhắm là bình thường)
                if not is_mouth_wide and not is_fatigued:
                    is_drowsy = self.processor.detect_drowsiness(ear)
                else:
                    is_drowsy = False
                
                self.processor.detect_blink(ear)
                
                # Cập nhật alert - Ưu tiên: Fatigue > Drowsy > Normal
                if is_fatigued:
                    # Mệt mỏi: Ngáp nhiều + Blink bất thường
                    self.alert_system.update_alert(AlertLevel.FATIGUE)
                    self.status_changed.emit("Fatigue", "#FFC107")
                    self.alert_changed.emit(AlertLevel.FATIGUE.value)
                elif is_drowsy:
                    # Ngủ gật: Mắt nhắm liên tục + miệng không há
                    self.alert_system.update_alert(AlertLevel.DROWSY)
                    self.status_changed.emit("DROWSY!", "#f44336")
                    self.alert_changed.emit(AlertLevel.DROWSY.value)
                else:
                    # Bình thường
                    self.alert_system.update_alert(AlertLevel.NONE)
                    self.status_changed.emit("Normal", "#4CAF50")
                    self.alert_changed.emit(AlertLevel.NONE.value)
                
                # Emit metrics
                metrics = {
                    "ear": ear,
                    "mar": mar,
                    "blink_rate": self.processor.get_blink_rate(),
                    "yawn_count": self.processor.get_yawn_count(),
                    "ear_threshold": self.config.get("thresholds.ear", 0.25),
                    "mar_threshold": self.config.get("thresholds.mar", 0.6)
                }
                self.metrics_updated.emit(metrics)
                
                # Vẽ landmarks nếu bật
                if self.show_landmarks:
                    self.face_detector.draw_landmarks(frame, results, draw_full_mesh=True)
                
                # Vẽ alert box
                self._draw_alert_box(frame, self.alert_system.get_alert_level())
        else:
            self.face_detected.emit(False)
            self.status_changed.emit("No face detected", "#9E9E9E")
        
        # Vẽ FPS
        if self.config.get("display.show_fps", True):
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    def _draw_alert_box(self, frame: np.ndarray, alert_level: AlertLevel):
        """
        Vẽ khung cảnh báo lên frame
        
        Args:
            frame: Frame để vẽ
            alert_level: Mức độ cảnh báo
        """
        h, w = frame.shape[:2]
        
        if alert_level == AlertLevel.DROWSY:
            color = (0, 0, 255)  # Đỏ
            text = "WARNING: DROWSY!"
            thickness = 10
        elif alert_level == AlertLevel.FATIGUE:
            color = (0, 255, 255)  # Vàng
            text = "Warning: Fatigue"
            thickness = 5
        else:
            return
        
        # Vẽ viền
        cv2.rectangle(frame, (thickness, thickness),
                     (w - thickness, h - thickness), color, thickness)
        
        # Vẽ text
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
        text_x = (w - text_size[0]) // 2
        text_y = 80
        
        cv2.rectangle(frame, (text_x - 10, text_y - text_size[1] - 10),
                     (text_x + text_size[0] + 10, text_y + 10), color, -1)
        
        cv2.putText(frame, text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    
    def stop(self):
        """Dừng engine"""
        print("[Engine] Đang dừng...")
        self.is_running = False
        self.wait()  # Đợi thread kết thúc
    
    def _cleanup(self):
        """Dọn dẹp tài nguyên"""
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
            
            self.processor.reset()
            self.alert_system.cleanup()
            
            if self.face_detector:
                self.face_detector.release()
            
            print("[Engine] Đã dọn dẹp tài nguyên")
        except Exception as e:
            print(f"[Engine] Lỗi khi dọn dẹp: {e}")
    
    def toggle_landmarks(self):
        """Bật/tắt hiển thị landmarks"""
        self.show_landmarks = not self.show_landmarks
        print(f"[Engine] Landmarks: {'BẬT' if self.show_landmarks else 'TẮT'}")

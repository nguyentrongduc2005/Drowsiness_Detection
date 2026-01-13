"""
Module chính: Tích hợp tất cả các thành phần và chạy ứng dụng
"""
import sys
import cv2
import os
import time
import pygame
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

# Import các module tự viết
from src.core.detector import FaceDetector
from src.core.processor import DrowsinessDetector
from src.core.config import Config
from src.ui.interface import MainWindow
from src.utils.logger import EventLogger, StatisticsTracker


class CameraWorker(QThread):
    """
    Thread xử lý camera và phát hiện buồn ngủ
    """
    
    # Signals để giao tiếp với UI
    frame_ready = pyqtSignal(object, float, float, str, bool, float)  # qt_image, ear, threshold, status, is_drowsy, fps
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config):
        """
        Khởi tạo CameraWorker
        
        Args:
            config: Đối tượng Config
        """
        super().__init__()
        self.config = config
        self.running = False
        
        # Khởi tạo các thành phần
        try:
            self.face_detector = FaceDetector(config.get_model_path())
            self.drowsiness_detector = DrowsinessDetector(config)
            
            # Logger
            if config.is_log_enabled():
                self.logger = EventLogger()
                self.stats_tracker = StatisticsTracker()
            else:
                self.logger = None
                self.stats_tracker = None
            
            # Pygame cho âm thanh
            pygame.mixer.init()
            alarm_path = config.get_alarm_sound()
            if os.path.exists(alarm_path):
                self.alarm_sound = pygame.mixer.Sound(alarm_path)
            else:
                self.alarm_sound = None
                print(f"Cảnh báo: Không tìm thấy file âm thanh: {alarm_path}")
            
            # Camera
            self.camera = None
            
            # FPS tracking
            self.fps = 0
            self.frame_count = 0
            self.start_time = time.time()
            
        except Exception as e:
            self.error_occurred.emit(f"Lỗi khởi tạo: {str(e)}")
    
    def run(self):
        """
        Vòng lặp chính xử lý camera
        
        Flow: Camera → Landmarks → EAR → Update Threshold → Compare → Emit Signal
        """
        # Mở camera
        camera_id = self.config.get_camera_id()
        self.camera = cv2.VideoCapture(camera_id)
        
        if not self.camera.isOpened():
            self.error_occurred.emit(f"Không thể mở camera {camera_id}")
            return
        
        self.running = True
        last_alarm_time = 0
        alarm_cooldown = 3  # Giây
        
        while self.running:
            # Đọc frame từ camera
            ret, frame = self.camera.read()
            
            if not ret or frame is None:
                self.error_occurred.emit("Không thể đọc frame từ camera")
                break
            
            # Đảm bảo frame có đúng định dạng
            if frame.dtype != 'uint8':
                frame = frame.astype('uint8')
            
            # === P1: Phát hiện landmarks ===
            landmarks = self.face_detector.get_landmarks(frame)
            
            # Debug: Hiển thị trạng thái phát hiện
            if self.frame_count % 30 == 0:  # Log mỗi 30 frame
                if landmarks is not None:
                    print(f"✓ Phát hiện khuôn mặt - Frame {self.frame_count}")
                else:
                    print(f"✗ Không phát hiện khuôn mặt - Frame {self.frame_count}")
            
            if landmarks is not None:
                # Lấy tọa độ mắt
                left_eye, right_eye = self.face_detector.get_eye_landmarks(landmarks)
                
                # Lấy tọa độ miệng
                mouth = self.face_detector.get_mouth_landmarks(landmarks)
                
                # === P2: Tính EAR, MAR và cập nhật threshold ===
                result = self.drowsiness_detector.process(left_eye, right_eye, mouth)
                
                ear = result['ear']
                mar = result['mar']
                threshold = result['threshold']
                is_drowsy = result['is_drowsy']
                is_yawning = result['is_yawning']
                warning = result['warning']
                warning_reason = result['warning_reason']
                status = result['status']
                yawn_count = result['yawn_count_total']
                blink_rate = result['blink_rate']
                
                # === Xử lý cảnh báo ===
                if warning:
                    current_time = time.time()
                    
                    # Phát âm thanh cảnh báo (với cooldown)
                    if current_time - last_alarm_time > alarm_cooldown:
                        if self.alarm_sound:
                            self.alarm_sound.play()
                        last_alarm_time = current_time
                        
                        # Ghi log alert
                        if self.logger:
                            self.logger.log_alert(ear, threshold)
                            self.logger.log_event(ear, threshold, warning_reason, True)
                
                # Vẽ thông tin lên frame (nếu cấu hình bật)
                if self.config.get_show_landmarks():
                    frame = self.face_detector.draw_landmarks(frame, landmarks)
                
                # Vẽ frame counter để biết camera đang hoạt động
                cv2.putText(frame, f"Frame: {self.frame_count}", 
                           (frame.shape[1] - 150, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Ghi thông tin lên frame
                self._draw_info_on_frame(frame, ear, mar, threshold, status, warning, warning_reason, 
                                        is_yawning, result['counter'], result['yawn_counter'], yawn_count, blink_rate)
                
                # Log event
                if self.logger and self.frame_count % 30 == 0:  # Log mỗi 30 frame
                    self.logger.log_event(ear, threshold, status, is_drowsy)
                
                # Cập nhật thống kê
                if self.stats_tracker:
                    self.stats_tracker.update(warning)
            else:
                # Không phát hiện khuôn mặt
                ear = 0.0
                threshold = self.config.get_ear_default()
                is_drowsy = False
                status = "Không phát hiện khuôn mặt"
                
                # Vẽ frame counter
                cv2.putText(frame, f"Frame: {self.frame_count}", 
                           (frame.shape[1] - 150, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Vẽ thông báo lớn hơn và rõ ràng hơn
                cv2.putText(frame, "NO FACE DETECTED!", (10, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                cv2.putText(frame, "Please follow instructions:", (10, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, "1. Look straight at camera", (10, 130), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, "2. Ensure good lighting", (10, 160), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, "3. Distance: 50-100cm", (10, 190), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Tính FPS
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                elapsed_time = time.time() - self.start_time
                self.fps = self.frame_count / elapsed_time
            
            # Chuyển đổi frame sang QImage
            qt_image = self._convert_frame_to_qimage(frame)
            
            # === Emit signal để cập nhật UI ===
            self.frame_ready.emit(qt_image, ear, threshold, status, is_drowsy, self.fps)
        
        # Dọn dẹp
        if self.camera:
            self.camera.release()
        
        # In thống kê cuối cùng
        if self.stats_tracker:
            self.stats_tracker.print_summary()
    
    def _draw_info_on_frame(self, frame, ear, mar, threshold, status, warning, warning_reason, 
                           is_yawning, counter, yawn_counter, yawn_count, blink_rate):
        """
        Vẽ thông tin lên frame
        
        Args:
            frame: Frame ảnh
            ear: Giá trị EAR
            mar: Giá trị MAR
            threshold: Ngưỡng
            status: Trạng thái
            warning: True nếu có cảnh báo
            warning_reason: Lý do cảnh báo
            is_yawning: True nếu đang ngáp
            counter: Số frame liên tiếp mắt nhắm
            yawn_counter: Số frame liên tiếp ngáp
            yawn_count: Tổng số lần ngáp trong 60s
            blink_rate: Tốc độ chớp mắt (lần/phút)
        """
        # Màu sắc
        color = (0, 0, 255) if warning else (0, 255, 0)
        
        # EAR
        cv2.putText(frame, f"EAR: {ear:.3f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # MAR
        cv2.putText(frame, f"MAR: {mar:.3f}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Threshold
        cv2.putText(frame, f"Threshold: {threshold:.3f}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Số lần ngáp
        yawn_color = (0, 165, 255) if yawn_count >= 3 else (255, 255, 255)
        cv2.putText(frame, f"Yawns (60s): {yawn_count}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, yawn_color, 2)
        
        # Tốc độ chớp mắt
        blink_color = (0, 165, 255) if blink_rate <= 10 else (255, 255, 255)
        cv2.putText(frame, f"Blink rate: {blink_rate:.1f}/min", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)
        
        # Counter
        if counter > 0:
            cv2.putText(frame, f"Eye closed: {counter} frames", (10, 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Hiển thị khi đang ngáp (không cảnh báo)
        if is_yawning and not warning:
            cv2.putText(frame, "Yawning...", (10, 210), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Status
        status_english = status.replace("Đang học", "Learning").replace("Đang bảo vệ", "Monitoring").replace("Không phát hiện khuôn mặt", "No face detected")
        cv2.putText(frame, status_english, (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # CẢNH BÁO lớn nếu có warning
        if warning:
            cv2.putText(frame, "!!! DROWSINESS WARNING !!!", 
                       (frame.shape[1]//2 - 280, frame.shape[0]//2 - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.putText(frame, warning_reason, 
                       (frame.shape[1]//2 - 250, frame.shape[0]//2 + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    def _convert_frame_to_qimage(self, frame):
        """
        Chuyển đổi OpenCV frame sang QImage
        
        Args:
            frame: Frame từ OpenCV (BGR)
            
        Returns:
            QImage
        """
        # Chuyển từ BGR sang RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        return qt_image
    
    def stop(self):
        """Dừng thread"""
        self.running = False
        self.wait()
    
    def reset_detector(self):
        """Reset detector để học lại"""
        self.drowsiness_detector.reset()
        if self.stats_tracker:
            self.stats_tracker.reset()


class DrowsinessDetectionApp:
    """
    Class chính của ứng dụng
    """
    
    def __init__(self):
        """Khởi tạo ứng dụng"""
        # Load config
        self.config = Config()
        
        # Tạo QApplication
        self.app = QApplication(sys.argv)
        
        # Tạo MainWindow
        self.window = MainWindow()
        
        # Tạo CameraWorker
        self.worker = CameraWorker(self.config)
        
        # Kết nối signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Kết nối các signals giữa worker và window"""
        # Signal từ worker tới window
        self.worker.frame_ready.connect(self.window.update_view)
        self.worker.error_occurred.connect(self._show_error)
        
        # Signal từ window tới worker
        self.window.start_button.clicked.connect(self._start_detection)
        self.window.stop_button.clicked.connect(self._stop_detection)
        self.window.reset_button.clicked.connect(self._reset_detection)
    
    def _start_detection(self):
        """Bắt đầu phát hiện"""
        self.worker.start()
        self.window.set_buttons_state(True)
        self.window.statusBar.showMessage("Đang chạy...")
    
    def _stop_detection(self):
        """Dừng phát hiện"""
        self.worker.stop()
        self.window.set_buttons_state(False)
        self.window.statusBar.showMessage("Đã dừng")
    
    def _reset_detection(self):
        """Reset để học lại"""
        self.worker.reset_detector()
        self.window.statusBar.showMessage("Đã reset, hệ thống sẽ học lại", 3000)
    
    def _show_error(self, error_message):
        """Hiển thị thông báo lỗi"""
        QMessageBox.critical(self.window, "Lỗi", error_message)
        self.window.set_buttons_state(False)
    
    def run(self):
        """Chạy ứng dụng"""
        self.window.show()
        return self.app.exec_()


def main():
    """Hàm main"""
    try:
        app = DrowsinessDetectionApp()
        sys.exit(app.run())
    except Exception as e:
        print(f"Lỗi nghiêm trọng: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

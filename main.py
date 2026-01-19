"""
Module chính: Tích hợp tất cả các thành phần và chạy ứng dụng
"""
# pylint: disable=no-name-in-module
# pyright: reportMissingModuleSource=false
import sys
import cv2  # type: ignore
import os
import time
import pygame
from PyQt5.QtWidgets import QApplication, QMessageBox  # type: ignore
from PyQt5.QtCore import QThread, pyqtSignal  # type: ignore
from PyQt5.QtGui import QImage  # type: ignore

# Import các module tự viết
from src.core.detector import FaceDetector
from src.core.processor import DrowsinessDetector
from src.core.config import Config
from src.ui.interface import MainWindow
from src.ui.settings_dialog import SettingsDialog
from src.utils.logger import EventLogger, StatisticsTracker


class CameraWorker(QThread):
    """
    Thread xử lý camera và phát hiện buồn ngủ
    Có tính năng auto-reconnect khi mất kết nối camera
    """
    
    # Signals để giao tiếp với UI
    # qt_image, ear, threshold, status, is_drowsy, fps, step_info (dict)
    frame_ready = pyqtSignal(object, float, float, str, bool, float, dict)
    error_occurred = pyqtSignal(str)
    camera_status = pyqtSignal(str)  # Signal báo trạng thái camera
    
    # Constants cho auto-reconnect
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 2  # seconds
    MAX_CONSECUTIVE_FAILURES = 30  # Số frame lỗi liên tiếp trước khi reconnect
    
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
            self.drowsiness_detector = DrowsinessDetector(config.get_consecutive_frames())
            
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
            self._camera_lock = False  # Lock để tránh race condition
            self._consecutive_failures = 0  # Đếm số lần đọc frame thất bại
            
            # FPS tracking với sliding window
            self.fps = 0
            self.frame_count = 0
            self.start_time = time.time()
            self._fps_history = []  # Sliding window cho FPS
            self._last_fps_time = time.time()
            
        except Exception as e:
            self.error_occurred.emit(f"Lỗi khởi tạo: {str(e)}")
    
    def _open_camera(self, camera_id):
        """
        Mở camera với error handling
        
        Returns:
            bool: True nếu mở thành công
        """
        try:
            if self.camera is not None:
                self.camera.release()
            
            self.camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            
            # Tối ưu camera settings
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            return self.camera.isOpened()
        except Exception as e:
            print(f"Lỗi mở camera {camera_id}: {e}")
            return False
    
    def _reconnect_camera(self):
        """
        Thử kết nối lại camera
        
        Returns:
            bool: True nếu reconnect thành công
        """
        self.camera_status.emit("🔄 Đang kết nối lại camera...")
        print("Đang thử kết nối lại camera...")
        
        for attempt in range(self.MAX_RECONNECT_ATTEMPTS):
            # Thử camera ID gốc trước
            camera_id = self.config.get_camera_id()
            if self._open_camera(camera_id):
                self.camera_status.emit(f"✅ Đã kết nối lại camera {camera_id}")
                print(f"✓ Đã kết nối lại camera {camera_id}")
                self._consecutive_failures = 0
                return True
            
            # Thử các camera ID khác
            for alt_id in range(10):
                if alt_id == camera_id:
                    continue
                if self._open_camera(alt_id):
                    self.camera_status.emit(f"✅ Đã kết nối camera {alt_id}")
                    print(f"✓ Tìm thấy camera tại ID: {alt_id}")
                    self._consecutive_failures = 0
                    return True
            
            # Chờ trước khi thử lại
            self.camera_status.emit(f"⏳ Thử lại lần {attempt + 1}/{self.MAX_RECONNECT_ATTEMPTS}...")
            time.sleep(self.RECONNECT_DELAY)
        
        return False
    
    def run(self):
        """
        Vòng lặp chính xử lý camera
        
        Flow: Camera → Landmarks → EAR → Update Threshold → Compare → Emit Signal
        Có auto-reconnect khi mất kết nối camera
        """
        try:
            self._run_detection_loop()
        except Exception as e:
            import traceback
            error_msg = f"Lỗi nghiêm trọng: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            self.error_occurred.emit(error_msg)
        finally:
            # Đảm bảo camera được giải phóng
            if self.camera is not None:
                try:
                    self.camera.release()
                except:
                    pass
    
    def _run_detection_loop(self):
        """
        Vòng lặp chính với error handling đầy đủ
        """
        # Mở camera
        camera_id = self.config.get_camera_id()
        if not self._open_camera(camera_id):
            # Thử các camera khác
            camera_found = False
            for alt_id in range(10):
                if self._open_camera(alt_id):
                    print(f"✓ Tìm thấy camera tại ID: {alt_id}")
                    camera_found = True
                    break
            
            if not camera_found:
                self.error_occurred.emit("Không tìm thấy camera nào. Vui lòng kết nối camera.")
                return
        
        print("✓ Camera đã sẵn sàng")
        self.camera_status.emit("✅ Camera đã kết nối")
        self.running = True
        last_alarm_time = 0
        alarm_cooldown = 3  # Giây
        
        # Bắt đầu quá trình calibration
        self.drowsiness_detector.smart_threshold.start_calibration()
        
        # Cache các giá trị để tránh lookup mỗi frame
        get_landmarks = self.face_detector.get_landmarks
        get_eye_landmarks = self.face_detector.get_eye_landmarks
        get_mouth_landmarks = self.face_detector.get_mouth_landmarks
        process = self.drowsiness_detector.process
        show_landmarks = self.config.get_show_landmarks()
        draw_landmarks = self.face_detector.draw_landmarks if show_landmarks else None
        ear_default = self.config.get_ear_default()
        
        while self.running:
            # Đọc frame từ camera với error handling
            try:
                ret, frame = self.camera.read()
            except Exception as e:
                print(f"Lỗi đọc frame: {e}")
                ret, frame = False, None
            
            # Xử lý frame lỗi và auto-reconnect
            if not ret or frame is None:
                self._consecutive_failures += 1
                
                # Nếu lỗi quá nhiều, thử reconnect
                if self._consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    print(f"Mất kết nối camera sau {self._consecutive_failures} frame lỗi")
                    if not self._reconnect_camera():
                        self.error_occurred.emit("Mất kết nối camera và không thể kết nối lại.")
                        return
                    self._consecutive_failures = 0
                
                continue
            
            # Reset counter khi đọc thành công
            self._consecutive_failures = 0
            
            # === P1: Phát hiện landmarks ===
            landmarks = get_landmarks(frame)
            
            # Cập nhật trạng thái phát hiện mặt cho calibration
            face_detected = landmarks is not None
            self.drowsiness_detector.smart_threshold.update_face_detection(face_detected)
            
            if landmarks is not None:
                # Lấy tọa độ mắt và miệng (dùng cached functions)
                left_eye, right_eye = get_eye_landmarks(landmarks)
                mouth = get_mouth_landmarks(landmarks)
                
                # === P2: Tính EAR, MAR và cập nhật threshold ===
                result = process(left_eye, right_eye, mouth)
                
                ear = result['ear']
                mar = result['mar']
                threshold = result['threshold']
                is_drowsy = result['is_drowsy']
                is_yawning = result['is_yawning']
                warning = result['warning']
                warning_reason = result['warning_reason']
                status = result['status']
                _ = result['is_calibrated']  # Không sử dụng trực tiếp, dùng step_info thay thế
                yawn_count = result['yawn_count_total']
                blink_rate = result['blink_rate']
                perclos = result.get('perclos', 0.0)
                perclos_status = result.get('perclos_status', 'Bình thường')
                
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
                if draw_landmarks:
                    frame = draw_landmarks(frame, landmarks)
                
                # Ghi thông tin lên frame
                self._draw_info_on_frame(frame, ear, mar, threshold, status, warning, warning_reason, 
                                        is_yawning, result['counter'], result['yawn_counter'], yawn_count, blink_rate, perclos)
                
                # Log event (giảm tần suất xuống mỗi 60 frame)
                if self.logger and self.frame_count % 60 == 0:
                    self.logger.log_event(ear, threshold, status, is_drowsy)
                
                # Cập nhật thống kê
                if self.stats_tracker:
                    self.stats_tracker.update(warning)
            else:
                # Không phát hiện khuôn mặt
                ear = 0.0
                threshold = ear_default
                is_drowsy = False
                status = "Không phát hiện khuôn mặt"
                
                # Vẽ thông báo đơn giản hơn (chỉ 1 dòng)
                cv2.putText(frame, "NO FACE - Look at camera", (10, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            # Tính FPS với sliding window (chính xác hơn)
            self.frame_count += 1
            current_time = time.time()
            
            # Cập nhật FPS mỗi 0.5 giây
            if current_time - self._last_fps_time >= 0.5:
                elapsed = current_time - self._last_fps_time
                if elapsed > 0:
                    instant_fps = (self.frame_count - len(self._fps_history) * 30) / elapsed if elapsed > 0 else 0
                    self._fps_history.append(instant_fps)
                    # Giữ 10 mẫu gần nhất
                    if len(self._fps_history) > 10:
                        self._fps_history.pop(0)
                    # Trung bình
                    self.fps = sum(self._fps_history) / len(self._fps_history) if self._fps_history else 0
                self._last_fps_time = current_time
            
            # Lấy thông tin calibration step
            step_info = self.drowsiness_detector.smart_threshold.get_step_info()
            
            # Chuyển đổi frame sang QImage và emit signal
            qt_image = self._convert_frame_to_qimage(frame)
            self.frame_ready.emit(qt_image, ear, threshold, status, is_drowsy, self.fps, step_info)
        
        # Dọn dẹp
        if self.camera is not None:
            try:
                self.camera.release()
            except:
                pass
        
        # In thống kê cuối cùng
        if self.stats_tracker:
            self.stats_tracker.print_summary()
    
    def _draw_info_on_frame(self, frame, ear, mar, threshold, status, warning, warning_reason, 
                           is_yawning, counter, _yawn_counter, yawn_count, blink_rate, perclos=0.0):
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
            perclos: Giá trị PERCLOS (0-1)
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
        
        # PERCLOS (mới thêm)
        perclos_pct = perclos * 100
        perclos_color = (0, 0, 255) if perclos_pct >= 15 else ((0, 165, 255) if perclos_pct >= 10 else (0, 255, 0))
        cv2.putText(frame, f"PERCLOS: {perclos_pct:.1f}%", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, perclos_color, 2)
        
        # Số lần ngáp
        yawn_color = (0, 165, 255) if yawn_count >= 3 else (255, 255, 255)
        cv2.putText(frame, f"Yawns (60s): {yawn_count}", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, yawn_color, 2)
        
        # Tốc độ chớp mắt
        blink_color = (0, 165, 255) if blink_rate <= 10 else (255, 255, 255)
        cv2.putText(frame, f"Blink rate: {blink_rate:.1f}/min", (10, 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)
        
        # Counter
        if counter > 0:
            cv2.putText(frame, f"Eye closed: {counter} frames", (10, 210), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Hiển thị khi đang ngáp (không cảnh báo)
        if is_yawning and not warning:
            cv2.putText(frame, "Yawning...", (10, 240), 
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
        Chuyển đổi OpenCV frame sang QImage (tối ưu)
        
        Args:
            frame: Frame từ OpenCV (BGR)
            
        Returns:
            QImage
        """
        # Chuyển từ BGR sang RGB (inplace nếu có thể)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # Tạo QImage với copy data để tránh memory issues
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        
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
        self.worker.camera_status.connect(self._update_camera_status)
        
        # Signal từ window tới worker
        self.window.start_button.clicked.connect(self._start_detection)
        self.window.stop_button.clicked.connect(self._stop_detection)
        self.window.reset_button.clicked.connect(self._reset_detection)
        self.window.settings_button.clicked.connect(self._open_settings)
        
        # Xử lý đóng cửa sổ
        self.app.aboutToQuit.connect(self._cleanup)
    
    def _start_detection(self):
        """Bắt đầu phát hiện"""
        if not self.worker.isRunning():
            self.worker.start()
            self.window.set_buttons_state(True)
            self.window.statusBar.showMessage("🟢 Đang chạy - Hệ thống đang giám sát...")
    
    def _stop_detection(self):
        """Dừng phát hiện"""
        if self.worker.isRunning():
            self.worker.stop()
            self.window.set_buttons_state(False)
            self.window.statusBar.showMessage("🔴 Đã dừng - Nhấn 'Bắt đầu' để tiếp tục")
    
    def _reset_detection(self):
        """Reset để học lại"""
        self.worker.reset_detector()
        self.window.statusBar.showMessage("🔄 Đã reset calibration - Hệ thống sẽ học lại từ đầu", 5000)
    
    def _open_settings(self):
        """Mở dialog cài đặt"""
        # Tạm dừng nếu đang chạy
        was_running = self.worker.isRunning()
        if was_running:
            self._stop_detection()
        
        # Mở dialog
        dialog = SettingsDialog(self.config, self.window)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec_()
        
        # Tiếp tục nếu trước đó đang chạy
        if was_running:
            self._start_detection()
    
    def _on_settings_changed(self, new_config):
        """Xử lý khi settings thay đổi"""
        # Cập nhật worker với config mới
        self.worker.config = self.config
        self.window.statusBar.showMessage("✅ Đã cập nhật cài đặt!", 3000)
    
    def _update_camera_status(self, status_message):
        """Cập nhật trạng thái camera"""
        self.window.statusBar.showMessage(status_message)
    
    def _show_error(self, error_message):
        """Hiển thị thông báo lỗi"""
        QMessageBox.critical(self.window, "Lỗi", error_message)
        self.window.set_buttons_state(False)
        self.window.statusBar.showMessage(f"❌ Lỗi: {error_message}")
    
    def _cleanup(self):
        """Dọn dẹp khi đóng ứng dụng"""
        if self.worker.isRunning():
            self.worker.stop()
    
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

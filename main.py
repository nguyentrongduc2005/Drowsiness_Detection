"""
Main Module: Integrate all components and run the application
"""
import sys
import cv2
import os
import time
import pygame
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

# Import custom modules
from src.core.detector import FaceDetector
from src.core.processor import DrowsinessDetector
from src.core.config import Config
from src.ui.interface import MainWindow
from src.utils.logger import EventLogger, StatisticsTracker


class CameraWorker(QThread):
    """
    Thread for camera processing and drowsiness detection
    """
    
    # Signals for UI communication
    # qt_image, ear, mar, threshold, status, is_drowsy, fps, fatigue_state, fatigue_score, blink_rate, session_duration, sleep_info
    frame_ready = pyqtSignal(object, float, float, float, str, bool, float, str, float, float, float, object)
    calibration_update = pyqtSignal(str, int, int, bool)  # state_text, progress, total, is_completed
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config):
        """
        Initialize CameraWorker
        
        Args:
            config: Config object
        """
        super().__init__()
        self.config = config
        self.running = False
        self.calibration_mode = False  # Calibration mode
        self.face_detector = None
        self.drowsiness_detector = None
        
        # Initialize basic attributes first (must be set before any exception)
        self.camera = None
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.logger = None
        self.stats_tracker = None
        self.alarm_sound = None
    
        # Initialize components
        try:
            self.face_detector = FaceDetector(config.get_model_path())
            self.drowsiness_detector = DrowsinessDetector(config)
            
            # Logger
            if config.is_log_enabled():
                self.logger = EventLogger()
                self.stats_tracker = StatisticsTracker()
            
            # Pygame for sound
            pygame.mixer.init()
            alarm_path = config.get_alarm_sound()
            if os.path.exists(alarm_path):
                self.alarm_sound = pygame.mixer.Sound(alarm_path)
            else:
                print(f"Warning: Sound file not found: {alarm_path}")
            
        except Exception as e:
            import traceback
            error_msg = f"Initialization error: {str(e)}"
            print(error_msg)
            print("Traceback:")
            traceback.print_exc()
            self.error_occurred.emit(error_msg)
    
    def run(self):
        """
        Main camera processing loop
        
        Flow: Camera -> Landmarks -> EAR -> Update Threshold -> Compare -> Emit Signal
        """
        # Check if components initialized successfully
        if self.face_detector is None or self.drowsiness_detector is None:
            self.error_occurred.emit("Failed to initialize components. Please check error messages above.")
            return
        
        # Open camera
        camera_id = self.config.get_camera_id()
        self.camera = cv2.VideoCapture(camera_id)
        
        if not self.camera.isOpened():
            self.error_occurred.emit(f"Cannot open camera {camera_id}")
            return
        
        self.running = True
        last_alarm_time = 0
        alarm_cooldown = 1.5  # Seconds - reduced for faster response
        
        while self.running:
            # Increment frame counter at the start of each iteration
            self.frame_count += 1
            
            # Read frame from camera
            ret, frame = self.camera.read()
            
            if not ret or frame is None:
                self.error_occurred.emit("Cannot read frame from camera")
                break
            
            # Ensure frame has correct format
            if frame.dtype != 'uint8':
                frame = frame.astype('uint8')
            
            # Calculate FPS periodically
            if self.frame_count % 30 == 0:
                elapsed_time = time.time() - self.start_time
                if elapsed_time > 0:
                    self.fps = self.frame_count / elapsed_time
            
            # === P1: Detect landmarks ===
            landmarks = self.face_detector.get_landmarks(frame)
            
            if landmarks is not None:
                # Get eye coordinates
                left_eye, right_eye = self.face_detector.get_eye_landmarks(landmarks)
                
                # Get mouth coordinates
                mouth = self.face_detector.get_mouth_landmarks(landmarks)
                
                # === CALIBRATION MODE ===
                if self.calibration_mode and self.drowsiness_detector.is_calibrating():
                    result = self.drowsiness_detector.process_calibration(left_eye, right_eye, mouth)
                    
                    # Draw calibration info on frame
                    self._draw_calibration_info(frame, result)
                    
                    # Emit calibration update
                    self.calibration_update.emit(
                        result['calibration_text'],
                        result['progress'],
                        result['total'],
                        result['is_completed']
                    )
                    
                    # If calibration completed, auto switch to normal mode
                    if result['is_completed']:
                        self.calibration_mode = False
                        print("[OK] Calibration completed!")
                    
                    # Draw landmarks
                    if self.config.get_show_landmarks():
                        frame = self.face_detector.draw_landmarks(frame, landmarks)
                    
                    # Convert frame to QImage and emit
                    qt_image = self._convert_frame_to_qimage(frame)
                    self.frame_ready.emit(qt_image, result['ear'], result['mar'], 0.0, 
                                         result['calibration_text'], False, self.fps, 
                                         "CALIBRATING", 0.0, 0.0, 0.0, None)
                    
                    # Continue to next frame
                    continue
                
                # === NORMAL MODE ===
                # Get image dimensions
                h, w = frame.shape[:2]
                
                # Get head pose from detector
                head_pose = self.face_detector.get_head_pose(w, h)
                
                # === P2: Calculate EAR, MAR and update threshold ===
                # Pass face detection status and image dimensions
                result = self.drowsiness_detector.process(
                    left_eye, 
                    right_eye, 
                    mouth,
                    face_detected=True,
                    img_w=w,
                    img_h=h
                )
                
                ear = result['ear']
                mar = result['mar']
                threshold = result['threshold']
                is_drowsy = result['is_drowsy']
                is_yawning = result['is_yawning']
                warning = result['warning']
                warning_reason = result['warning_reason']
                status = result['status']
                yawn_count = result['yawn_count']
                blink_rate = result['blink_rate']
                
                # Fatigue state info
                fatigue_state = result.get('fatigue_state', 'NORMAL')
                fatigue_score = result.get('fatigue_score', 0.0)
                session_duration = result.get('session_duration', 0.0)
                
                # Sleep event info - THÊM yawn_count
                sleep_info = {
                    'is_sleeping': result.get('is_sleeping', False),
                    'sleep_event_type': result.get('sleep_event_type'),
                    'sleep_duration': result.get('sleep_duration', 0.0),
                    'pre_sleep_warning': result.get('pre_sleep_warning', False),
                    'sleep_alert': result.get('sleep_alert', False),
                    'sleep_alert_message': result.get('sleep_alert_message', ''),
                    'sleep_stats': result.get('sleep_stats', {}),
                    'sleep_trend': result.get('sleep_trend', 'stable'),
                    'sleep_risk': result.get('sleep_risk', 'low'),
                    'yawn_count': yawn_count,  # Thêm yawn count vào sleep_info
                }
                
                # === Handle warning với Alert System ===
                alert_config = result.get('alert_config')
                alert_message = result.get('alert_message', warning_reason)
                
                if warning:
                    current_time = time.time()
                    
                    # Play alarm sound khi có warning
                    if current_time - last_alarm_time > alarm_cooldown:
                        if self.alarm_sound:
                            self.alarm_sound.play()
                        last_alarm_time = current_time
                        
                        # Log alert
                        if self.logger:
                            self.logger.log_alert(ear, threshold)
                            self.logger.log_event(ear, threshold, alert_message, True)
                else:
                    # NGỪNG ÂM THANH NGAY KHI KHÔNG CÒN WARNING (mở mắt lại)
                    if self.alarm_sound:
                        self.alarm_sound.stop()
                
                # Draw info on frame - VẼ TẤT CẢ MEDIAPIPE LANDMARKS
                if self.config.get_show_landmarks():
                    # Vẽ đầy đủ 468 điểm MediaPipe
                    frame = self.face_detector.draw_all_mediapipe_landmarks(frame)
                
                # Draw info on frame
                head_pose = result.get('head_pose', {})
                self._draw_info_on_frame(frame, ear, mar, threshold, status, warning, alert_message, 
                                        is_yawning, result['counter'], result['yawn_counter'], yawn_count, blink_rate, head_pose, alert_config, result)
                
                # Log event
                if self.logger and self.frame_count % 30 == 0:  # Log every 30 frames
                    self.logger.log_event(ear, threshold, status, is_drowsy)
                
                # Update statistics
                if self.stats_tracker:
                    self.stats_tracker.update(warning)
            else:
                # No face detected
                ear = 0.0
                mar = 0.0
                threshold = self.config.get_ear_default()
                is_drowsy = False
                status = "No face detected"
                fatigue_state = "NORMAL"
                fatigue_score = 0.0
                blink_rate = 0.0
                session_duration = time.time() - self.start_time
                
                # Draw larger and clearer message
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
                
                # Sleep info is None when no face detected
                sleep_info = None
            
            # Convert frame to QImage
            qt_image = self._convert_frame_to_qimage(frame)
            
            # === Emit signal to update UI ===
            self.frame_ready.emit(qt_image, ear, mar, threshold, status, is_drowsy, self.fps,
                                 fatigue_state, fatigue_score, blink_rate, session_duration, sleep_info)
        
        # Cleanup
        if self.camera:
            self.camera.release()
        
        # Stop alarm sound if playing
        if self.alarm_sound:
            self.alarm_sound.stop()
        
        # Print final statistics
        if self.stats_tracker:
            self.stats_tracker.print_summary()
    
    def _draw_info_on_frame(self, frame, ear, mar, threshold, status, warning, warning_reason, 
                           is_yawning, counter, yawn_counter, yawn_count, blink_rate, head_pose=None, alert_config=None, result=None):
        """
        Draw info on frame - ENHANCED với Alert System
        
        Args:
            frame: Image frame
            ear: EAR value
            mar: MAR value
            threshold: Threshold
            status: Status
            warning: True if warning
            warning_reason: Warning reason
            is_yawning: True if yawning
            counter: Consecutive frames with eyes closed
            yawn_counter: Consecutive frames yawning
            yawn_count: Total yawns in 60s
            blink_rate: Blink rate (times/minute)
            head_pose: Head pose data (pitch, yaw, roll)
            alert_config: Alert configuration từ Alert System
            result: Full result dict for fatigue info
        """
        # Colors
        color = (0, 0, 255) if warning else (0, 255, 0)
        
        # === THÔNG TIN CƠ BẢN (GÓC TRÁI TRÊN) ===
        # EAR - Chỉ số quan trọng nhất
        cv2.putText(frame, f"EAR: {ear:.3f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # === CHỈ SỐ CƠ BẢN (GÓC TRÁI TRÊN) ===
        # Yawn count (trong 5 phút)
        yawn_color = (0, 165, 255) if yawn_count >= 3 else (255, 255, 255)
        cv2.putText(frame, f"Yawns: {yawn_count}/5min", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, yawn_color, 2)
        
        # Blink rate (trung bình/phút)
        blink_color = (0, 165, 255) if blink_rate <= 10 else (255, 255, 255)
        cv2.putText(frame, f"Blink: {blink_rate:.1f}/min", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)
        
        # === YAWNING STATUS (GÓC PHẢI TRÊN) ===
        # Hiển thị "YAWNING" khi đang ngáp
        if is_yawning:
            yawn_text = "YAWNING"
            text_size = cv2.getTextSize(yawn_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            box_x = frame.shape[1] - text_size[0] - 20
            box_y = 10
            
            # Vẽ background box
            cv2.rectangle(frame, (box_x - 10, box_y), 
                         (frame.shape[1] - 10, box_y + text_size[1] + 20), 
                         (0, 165, 255), -1)  # Orange background
            cv2.rectangle(frame, (box_x - 10, box_y), 
                         (frame.shape[1] - 10, box_y + text_size[1] + 20), 
                         (255, 255, 255), 2)  # White border
            
            # Vẽ text
            cv2.putText(frame, yawn_text, (box_x, box_y + text_size[1] + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # === FATIGUE LEVEL (chỉ để check cho warning, KHÔNG hiển thị) ===
        # Fatigue Score đã có trên SIDEBAR với score bar đẹp → không cần lặp lại
        if result:
            fatigue_level = result.get('fatigue_level', 'NORMAL')
        else:
            fatigue_level = 'NORMAL'
        
        # === TIRED WARNING (Hiển thị trên màn hình thay vì sidebar) ===
        # Chỉ hiển thị khi TIRED - sidebar sẽ không hiện TIRED nữa
        if fatigue_level == 'TIRED' and not warning:
            # Thông báo nhẹ ở giữa phía trên
            tired_text = "◐ FEELING TIRED?"
            text_size = cv2.getTextSize(tired_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            # Đặt ở giữa màn hình phía trên
            box_x = (frame.shape[1] - text_size[0]) // 2
            box_y = 10
            
            # Vẽ background box màu vàng
            cv2.rectangle(frame, (box_x - 10, box_y), 
                         (box_x + text_size[0] + 10, box_y + text_size[1] + 20), 
                         (0, 200, 255), -1)  # Yellow background
            cv2.rectangle(frame, (box_x - 10, box_y), 
                         (box_x + text_size[0] + 10, box_y + text_size[1] + 20), 
                         (255, 255, 255), 2)  # White border
            
            # Vẽ text
            cv2.putText(frame, tired_text, (box_x, box_y + text_size[1] + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # === CẢNH BÁO (Warning Display) ===
        # Status - chỉ hiển thị khi có vấn đề (sidebar đã hiển thị các cảnh báo rồi)
        if warning or not result:
            status_y = frame.shape[0] - 20
            cv2.putText(frame, status, (10, status_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # === WARNING DISPLAY BASED ON ALERT CONFIG ===
        if warning:
            # Get color and severity from alert config (if available)
            if alert_config:
                alert_color = alert_config.color if hasattr(alert_config, 'color') else (0, 0, 255)
                alert_title = alert_config.title if hasattr(alert_config, 'title') else "!!! WARNING !!!"
                
                # Kích thước text tùy theo severity
                if hasattr(alert_config, 'severity'):
                    from src.core.alert_system import AlertSeverity
                    if alert_config.severity == AlertSeverity.CRITICAL:
                        title_scale = 1.5
                        msg_scale = 1.0
                    elif alert_config.severity == AlertSeverity.DANGER:
                        title_scale = 1.2
                        msg_scale = 0.9
                    else:
                        title_scale = 1.0
                        msg_scale = 0.8
                else:
                    title_scale = 1.0
                    msg_scale = 0.8
            else:
                # No alert config (in cooldown) - use default
                alert_color = (0, 0, 255)
                alert_title = "!!! WARNING !!!"
                title_scale = 1.0
                msg_scale = 0.8
            
            # Display position (center screen)
            center_x = frame.shape[1] // 2
            center_y = frame.shape[0] // 2
            
            # Dark overlay for better readability
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, center_y - 80), (frame.shape[1], center_y + 80), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            # Display large title
            title_size = cv2.getTextSize(alert_title, cv2.FONT_HERSHEY_SIMPLEX, title_scale, 3)[0]
            title_x = center_x - title_size[0] // 2
            cv2.putText(frame, alert_title, 
                       (title_x, center_y - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, title_scale, alert_color, 3)
            
            # Display reason/instruction
            msg_size = cv2.getTextSize(warning_reason, cv2.FONT_HERSHEY_SIMPLEX, msg_scale, 2)[0]
            msg_x = center_x - msg_size[0] // 2
            cv2.putText(frame, warning_reason, 
                       (msg_x, center_y + 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, msg_scale, alert_color, 2)
    
    def _convert_frame_to_qimage(self, frame):
        """
        Convert OpenCV frame to QImage
        
        Args:
            frame: Frame from OpenCV (BGR)
            
        Returns:
            QImage
        """
        # Convert from BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        return qt_image
    
    def _draw_calibration_info(self, frame, result):
        """
        Draw calibration info on frame
        
        Args:
            frame: Image frame
            result: Dict result from process_calibration
        """
        h, w = frame.shape[:2]
        
        # Background overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Title
        cv2.putText(frame, "=== CALIBRATION MODE ===", (w//2 - 200, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        
        # State
        state_text = result['calibration_text']
        cv2.putText(frame, state_text, (w//2 - 150, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Progress bar
        progress = result['progress']
        total = result['total']
        bar_width = 300
        bar_height = 20
        bar_x = w//2 - bar_width//2
        bar_y = 80
        
        # Background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Progress
        progress_width = int((progress / total) * bar_width) if total > 0 else 0
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), (0, 255, 0), -1)
        
        # Text
        cv2.putText(frame, f"{progress}/{total}", (bar_x + bar_width + 10, bar_y + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Current EAR/MAR
        cv2.putText(frame, f"EAR: {result['ear']:.3f} | MAR: {result['mar']:.3f}", 
                   (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Instructions
        state = result['calibration_state']
        if state == "open_eyes":
            instruction = "Look straight at camera, keep eyes open normally"
        elif state == "closed_eyes":
            instruction = "Close your eyes gently (like when drowsy)"
        elif state == "yawning":
            instruction = "Open mouth wide / Yawn - KEEP EYES OPEN!"
            # Add warning text in red for yawning state
            cv2.putText(frame, "!! DO NOT CLOSE EYES WHILE YAWNING !!", (w//2 - 220, h - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            instruction = ""
        
        if instruction:
            cv2.putText(frame, instruction, (w//2 - 200, h - 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def stop(self):
        """Stop thread"""
        self.running = False
        
        # Stop alarm sound immediately when stopping detection
        if self.alarm_sound:
            self.alarm_sound.stop()
        
        self.wait()
    
    def reset_detector(self):
        """Reset detector to relearn"""
        self.drowsiness_detector.reset()
        if self.stats_tracker:
            self.stats_tracker.reset()
    
    def start_calibration(self):
        """Start calibration mode"""
        self.calibration_mode = True
        self.drowsiness_detector.start_calibration()
        print("[>] Starting calibration from CameraWorker")
    
    def stop_calibration(self):
        """Stop calibration mode"""
        self.calibration_mode = False
    
    def reset_calibration(self):
        """Reset calibration"""
        self.drowsiness_detector.reset_calibration()
        self.calibration_mode = False


class DrowsinessDetectionApp:
    """
    Main application class
    """
    
    def __init__(self):
        """Initialize application"""
        # Load config
        self.config = Config()
        
        # Create QApplication
        self.app = QApplication(sys.argv)
        
        # Create MainWindow
        self.window = MainWindow()
        
        # Create CameraWorker
        self.worker = CameraWorker(self.config)
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect signals between worker and window"""
        # Signal from worker to window
        self.worker.frame_ready.connect(self.window.update_view)
        self.worker.error_occurred.connect(self._show_error)
        self.worker.calibration_update.connect(self._on_calibration_update)
        
        # Signal from window to worker
        self.window.start_button.clicked.connect(self._start_detection)
        self.window.stop_button.clicked.connect(self._stop_detection)
        self.window.calibrate_button.clicked.connect(self._start_calibration)
        self.window.reset_button.clicked.connect(self._reset_detection)
        
        # Load initial calibration info
        self._update_calibration_info()
    
    def _update_calibration_info(self):
        """Update calibration information"""
        if not self.worker or self.worker.drowsiness_detector is None:
            self.window.calibration_info_label.setText("System Error: Detector not initialized")
            self.window.calibration_info_label.setStyleSheet("color: #ff4d4d; padding: 5px;")
            return
        cal_info = self.worker.drowsiness_detector.get_calibration_info()
        
        if cal_info.get('calibrated'):
            ear_thresh = cal_info.get('ear_threshold', 0)
            mar_thresh = cal_info.get('mar_threshold', 0)
            self.window.calibration_info_label.setText(
                f"[OK] Calibrated (EAR: {ear_thresh:.3f}, MAR: {mar_thresh:.3f})"
            )
            self.window.calibration_info_label.setStyleSheet("color: #1fcc7e; padding: 5px;")
        else:
            self.window.calibration_info_label.setText(
                "Not calibrated - Press CALIBRATE for more accurate thresholds"
            )
            self.window.calibration_info_label.setStyleSheet("color: #ffc800; padding: 5px;")
    def _start_detection(self):
        """Start detection"""
        self.worker.start()
        self.window.set_buttons_state(True)
        self.window.statusBar.showMessage("Running...")
    
    def _stop_detection(self):
        """Stop detection"""
        self.worker.stop()
        self.window.set_buttons_state(False)
        self.window.statusBar.showMessage("Stopped")
    
    def _reset_detection(self):
        """Reset to relearn"""
        self.worker.reset_detector()
        self._update_calibration_info()
        self.window.statusBar.showMessage("Reset complete, system will relearn", 3000)
    
    def _start_calibration(self):
        """Start personal calibration mode"""
        # If camera not running, start it first
        if not self.worker.running:
            self.worker.start()
            self.window.set_buttons_state(True)
        
        # Start calibration
        self.worker.start_calibration()
        self.window.statusBar.showMessage("[>] Calibrating - Step 1: Keep eyes open normally")
        self.window.calibrate_button.setEnabled(False)
    
    def _on_calibration_update(self, state_text, progress, total, is_completed):
        """Handle calibration update"""
        if is_completed:
            self.window.statusBar.showMessage("[OK] Calibration complete! Thresholds personalized.")
            self.window.calibrate_button.setEnabled(True)
            
            # Display calibration info
            cal_info = self.worker.drowsiness_detector.get_calibration_info()
            if cal_info.get('calibrated'):
                ear_thresh = cal_info.get('ear_threshold', 0)
                mar_thresh = cal_info.get('mar_threshold', 0)
                QMessageBox.information(
                    self.window, 
                    "Calibration Complete",
                    f"Personal thresholds have been set:\n\n"
                    f"- EAR Threshold: {ear_thresh:.3f}\n"
                    f"- MAR Threshold: {mar_thresh:.3f}\n\n"
                    f"The system will use these thresholds for more accurate drowsiness detection."
                )
                
            # Update calibration info
            self._update_calibration_info()
        else:
            self.window.statusBar.showMessage(f"{state_text} - {progress}/{total}")
    
    def _show_error(self, error_message):
        """Display error message"""
        QMessageBox.critical(self.window, "Error", error_message)
        self.window.set_buttons_state(False)
    
    def run(self):
        """Run application"""
        self.window.show()
        return self.app.exec_()


def main():
    """Main function"""
    try:
        app = DrowsinessDetectionApp()
        sys.exit(app.run())
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

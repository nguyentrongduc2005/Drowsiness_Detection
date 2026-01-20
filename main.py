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
    
        # Initialize components
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
            
            # Pygame for sound
            pygame.mixer.init()
            alarm_path = config.get_alarm_sound()
            if os.path.exists(alarm_path):
                self.alarm_sound = pygame.mixer.Sound(alarm_path)
            else:
                self.alarm_sound = None
                print(f"Warning: Sound file not found: {alarm_path}")
            
            # Camera
            self.camera = None
            
            # FPS tracking
            self.fps = 0
            self.frame_count = 0
            self.start_time = time.time()
            
        except Exception as e:
            error_msg = f"Initialization error: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(f"Initialization error: {str(e)}")
    
    def run(self):
        """
        Main camera processing loop
        
        Flow: Camera -> Landmarks -> EAR -> Update Threshold -> Compare -> Emit Signal
        """
        # Open camera
        camera_id = self.config.get_camera_id()
        self.camera = cv2.VideoCapture(camera_id)
        
        if not self.camera.isOpened():
            self.error_occurred.emit(f"Cannot open camera {camera_id}")
            return
        
        self.running = True
        last_alarm_time = 0
        alarm_cooldown = 3  # Seconds
        
        while self.running:
            # Read frame from camera
            ret, frame = self.camera.read()
            
            if not ret or frame is None:
                self.error_occurred.emit("Cannot read frame from camera")
                break
            
            # Ensure frame has correct format
            if frame.dtype != 'uint8':
                frame = frame.astype('uint8')
            
            # === P1: Detect landmarks ===
            landmarks = self.face_detector.get_landmarks(frame)
            
            # Debug: Display detection status
            if self.frame_count % 30 == 0:  # Log every 30 frames
                if landmarks is not None:
                    pass  # print(f"[OK] Face detected - Frame {self.frame_count}")
                else:
                    print(f"[X] No face detected - Frame {self.frame_count}")
            
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
                    
                    # Calculate FPS and continue
                    self.frame_count += 1
                    if self.frame_count % 30 == 0:
                        elapsed_time = time.time() - self.start_time
                        self.fps = self.frame_count / elapsed_time
                    continue
                
                # === NORMAL MODE ===
                # Get raw landmarks for head pose estimation
                raw_landmarks = self.face_detector.get_raw_landmarks()
                self.drowsiness_detector.set_landmarks(raw_landmarks)
                
                # === P2: Calculate EAR, MAR and update threshold ===
                result = self.drowsiness_detector.process(left_eye, right_eye, mouth)
                
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
                
                # Sleep event info
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
                }
                
                # === Handle warning ===
                if warning:
                    current_time = time.time()
                    
                    # Play alarm sound (with cooldown)
                    if current_time - last_alarm_time > alarm_cooldown:
                        if self.alarm_sound:
                            self.alarm_sound.play()
                        last_alarm_time = current_time
                        
                        # Log alert
                        if self.logger:
                            self.logger.log_alert(ear, threshold)
                            self.logger.log_event(ear, threshold, warning_reason, True)
                
                # Draw info on frame (if configured)
                if self.config.get_show_landmarks():
                    frame = self.face_detector.draw_landmarks(frame, landmarks)
                
                # Draw frame counter to show camera is working
                cv2.putText(frame, f"Frame: {self.frame_count}", 
                           (frame.shape[1] - 150, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Draw info on frame
                self._draw_info_on_frame(frame, ear, mar, threshold, status, warning, warning_reason, 
                                        is_yawning, result['counter'], result['yawn_counter'], yawn_count, blink_rate)
                
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
                
                # Draw frame counter
                cv2.putText(frame, f"Frame: {self.frame_count}", 
                           (frame.shape[1] - 150, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
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
            
            # Calculate FPS
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                elapsed_time = time.time() - self.start_time
                self.fps = self.frame_count / elapsed_time
            
            # Convert frame to QImage
            qt_image = self._convert_frame_to_qimage(frame)
            
            # === Emit signal to update UI ===
            self.frame_ready.emit(qt_image, ear, mar, threshold, status, is_drowsy, self.fps,
                                 fatigue_state, fatigue_score, blink_rate, session_duration, sleep_info)
        
        # Cleanup
        if self.camera:
            self.camera.release()
        
        # Print final statistics
        if self.stats_tracker:
            self.stats_tracker.print_summary()
    
    def _draw_info_on_frame(self, frame, ear, mar, threshold, status, warning, warning_reason, 
                           is_yawning, counter, yawn_counter, yawn_count, blink_rate):
        """
        Draw info on frame
        
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
        """
        # Colors
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
        
        # Yawn count
        yawn_color = (0, 165, 255) if yawn_count >= 3 else (255, 255, 255)
        cv2.putText(frame, f"Yawns (60s): {yawn_count}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, yawn_color, 2)
        
        # Blink rate
        blink_color = (0, 165, 255) if blink_rate <= 10 else (255, 255, 255)
        cv2.putText(frame, f"Blink rate: {blink_rate:.1f}/min", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)
        
        # Counter
        if counter > 0:
            cv2.putText(frame, f"Eye closed: {counter} frames", (10, 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Display when yawning (no warning)
        if is_yawning and not warning:
            cv2.putText(frame, "Yawning...", (10, 210), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Status
        status_english = status.replace("Learning", "Learning").replace("Monitoring", "Monitoring").replace("No face detected", "No face detected")
        cv2.putText(frame, status_english, (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Large WARNING if warning
        if warning:
            cv2.putText(frame, "!!! DROWSINESS WARNING !!!", 
                       (frame.shape[1]//2 - 280, frame.shape[0]//2 - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.putText(frame, warning_reason, 
                       (frame.shape[1]//2 - 250, frame.shape[0]//2 + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
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
            instruction = "Open mouth wide / Yawn"
        else:
            instruction = ""
        
        if instruction:
            cv2.putText(frame, instruction, (w//2 - 200, h - 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def stop(self):
        """Stop thread"""
        self.running = False
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

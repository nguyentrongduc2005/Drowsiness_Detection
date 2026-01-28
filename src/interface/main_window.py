"""
Main Window - Giao diện chính của ứng dụng
Nhận signals từ DetectionEngine và cập nhật UI
"""
import cv2
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont

from ..config import ConfigManager
from ..core import DetectionEngine
from ..alert import AlertLevel


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Khởi tạo MainWindow
        
        Args:
            config_manager: ConfigManager instance
        """
        super().__init__()
        
        self.config = config_manager
        self.engine: DetectionEngine = None
        
        self._init_ui()
        self._create_engine()
        self._connect_signals()
    
    def _init_ui(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("Driver Drowsiness Detection System")
        self.setGeometry(100, 100, 1200, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Camera display (bên trái)
        self._setup_camera_display(main_layout)
        
        # Control panel (bên phải)
        self._setup_control_panel(main_layout)
    
    def _setup_camera_display(self, parent_layout):
        """Thiết lập khung hiển thị camera"""
        camera_frame = QFrame()
        camera_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        camera_frame.setLineWidth(2)
        
        camera_layout = QVBoxLayout()
        camera_frame.setLayout(camera_layout)
        
        # Video label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("background-color: black;")
        camera_layout.addWidget(self.video_label)
        
        parent_layout.addWidget(camera_frame, 3)
    
    def _setup_control_panel(self, parent_layout):
        """Thiết lập bảng điều khiển"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        control_frame.setLineWidth(2)
        control_frame.setMinimumWidth(300)
        control_frame.setMaximumWidth(400)
        
        control_layout = QVBoxLayout()
        control_frame.setLayout(control_layout)
        
        # Title
        title_label = QLabel("CONTROL PANEL")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        control_layout.addWidget(title_label)
        
        # Status group
        status_group = QFrame()
        status_group.setFrameStyle(QFrame.Box | QFrame.Sunken)
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        status_title = QLabel("SYSTEM STATUS")
        status_title.setAlignment(Qt.AlignCenter)
        status_title.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout.addWidget(status_title)
        
        self.status_label = QLabel("Not Started")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setStyleSheet("padding: 20px; background-color: lightgray; border-radius: 5px;")
        status_layout.addWidget(self.status_label)
        
        control_layout.addWidget(status_group)
        control_layout.addSpacing(20)
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("START")
        self.start_stop_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_stop_btn.setMinimumHeight(50)
        self.start_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_stop_btn.clicked.connect(self._toggle_detection)
        control_layout.addWidget(self.start_stop_btn)
        
        # Learn button
        self.learn_btn = QPushButton("RESET & RELEARN")
        self.learn_btn.setFont(QFont("Arial", 11))
        self.learn_btn.setMinimumHeight(40)
        self.learn_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.learn_btn.clicked.connect(self._reset_learning)
        self.learn_btn.setEnabled(False)
        control_layout.addWidget(self.learn_btn)
        
        # Learning progress
        self.learning_label = QLabel("Continuous Learning...")
        self.learning_label.setAlignment(Qt.AlignCenter)
        self.learning_label.setFont(QFont("Arial", 9))
        self.learning_label.setStyleSheet("color: #2196F3;")
        control_layout.addWidget(self.learning_label)
        
        # Landmarks toggle button
        self.landmarks_btn = QPushButton("HIDE LANDMARKS")
        self.landmarks_btn.setFont(QFont("Arial", 11))
        self.landmarks_btn.setMinimumHeight(40)
        self.landmarks_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        self.landmarks_btn.clicked.connect(self._toggle_landmarks)
        self.landmarks_btn.setEnabled(False)
        control_layout.addWidget(self.landmarks_btn)
        
        # Metrics display
        control_layout.addSpacing(20)
        metrics_label = QLabel("CURRENT METRICS")
        metrics_label.setAlignment(Qt.AlignCenter)
        metrics_label.setFont(QFont("Arial", 11, QFont.Bold))
        control_layout.addWidget(metrics_label)
        
        self.metrics_display = QLabel("")
        self.metrics_display.setFont(QFont("Consolas", 9))
        self.metrics_display.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        self.metrics_display.setWordWrap(True)
        control_layout.addWidget(self.metrics_display)
        
        control_layout.addStretch()
        
        parent_layout.addWidget(control_frame, 1)
    
    def _create_engine(self):
        """Tạo detection engine"""
        self.engine = DetectionEngine(self.config)
        print("[MainWindow] Đã tạo DetectionEngine")
    
    def _connect_signals(self):
        """Kết nối signals từ engine đến UI"""
        self.engine.frame_processed.connect(self._on_frame_processed)
        self.engine.face_detected.connect(self._on_face_detected)
        self.engine.metrics_updated.connect(self._on_metrics_updated)
        self.engine.alert_changed.connect(self._on_alert_changed)
        self.engine.status_changed.connect(self._on_status_changed)
        self.engine.learning_progress.connect(self._on_learning_progress)
        self.engine.error_occurred.connect(self._on_error_occurred)
    
    @pyqtSlot(np.ndarray, float)
    def _on_frame_processed(self, frame: np.ndarray, fps: float):
        """
        Xử lý khi nhận frame mới từ engine
        
        Args:
            frame: Frame đã xử lý
            fps: FPS hiện tại
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale và hiển thị
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.video_label.setPixmap(scaled_pixmap)
    
    @pyqtSlot(bool)
    def _on_face_detected(self, detected: bool):
        """Xử lý khi phát hiện/mất khuôn mặt"""
        pass  # Có thể thêm xử lý nếu cần
    
    @pyqtSlot(dict)
    def _on_metrics_updated(self, metrics: dict):
        """
        Cập nhật hiển thị metrics
        
        Args:
            metrics: Dictionary chứa các metrics
        """
        metrics_text = f"""
EAR: {metrics['ear']:.3f}
MAR: {metrics['mar']:.3f}
EAR Threshold: {metrics['ear_threshold']:.3f}
MAR Threshold: {metrics['mar_threshold']:.3f}

Blinks/min: {metrics['blink_rate']}
Yawns/min: {metrics['yawn_count']}
        """.strip()
        
        self.metrics_display.setText(metrics_text)
    
    @pyqtSlot(int)
    def _on_alert_changed(self, alert_level: int):
        """Xử lý khi mức cảnh báo thay đổi"""
        pass  # Alert được xử lý trong engine
    
    @pyqtSlot(str, str)
    def _on_status_changed(self, status: str, color: str):
        """
        Cập nhật trạng thái hệ thống
        
        Args:
            status: Text trạng thái
            color: Màu nền
        """
        self.status_label.setText(status)
        self.status_label.setStyleSheet(
            f"padding: 20px; background-color: {color}; color: white; "
            f"border-radius: 5px; font-weight: bold;")
    
    @pyqtSlot(float)
    def _on_learning_progress(self, progress: float):
        """
        Cập nhật tiến độ học
        
        Args:
            progress: Tiến độ 0-100
        """
        # Lấy tổng số mẫu từ learning engine
        if self.engine and self.engine.learning_engine:
            total_samples = self.engine.learning_engine.get_total_samples()
            self.learning_label.setText(f"Learning: {total_samples} samples | {progress:.0f}%")
        else:
            self.learning_label.setText(f"Learning: {progress:.0f}%")
    
    @pyqtSlot(str)
    def _on_error_occurred(self, error: str):
        """
        Xử lý khi có lỗi
        
        Args:
            error: Thông báo lỗi
        """
        QMessageBox.critical(self, "Error", error)
        self.status_label.setText("Error: " + error)
        self.status_label.setStyleSheet(
            "padding: 20px; background-color: #f44336; color: white; border-radius: 5px;")
    
    def _toggle_detection(self):
        """Bật/tắt detection"""
        if not self.engine.is_running:
            # Bắt đầu - tạo engine mới
            if self.engine is not None:
                # Disconnect signals cũ
                try:
                    self.engine.frame_processed.disconnect()
                    self.engine.face_detected.disconnect()
                    self.engine.metrics_updated.disconnect()
                    self.engine.alert_changed.disconnect()
                    self.engine.status_changed.disconnect()
                    self.engine.learning_progress.disconnect()
                    self.engine.error_occurred.disconnect()
                except:
                    pass
            
            # Tạo engine mới
            self.engine = DetectionEngine(self.config)
            self._connect_signals()
            self.engine.start()
            
            self.start_stop_btn.setText("STOP")
            self.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            self.learn_btn.setEnabled(True)
            self.landmarks_btn.setEnabled(True)
        else:
            # Dừng
            self.engine.stop()
            
            self.start_stop_btn.setText("START")
            self.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.learn_btn.setEnabled(False)
            self.landmarks_btn.setEnabled(False)
            
            self.video_label.clear()
            self.video_label.setStyleSheet("background-color: black;")
            self.status_label.setText("Stopped")
            self.status_label.setStyleSheet("padding: 20px; background-color: lightgray; border-radius: 5px;")
    
    def _reset_learning(self):
        """Reset và học lại từ đầu"""
        reply = QMessageBox.question(
            self, 
            "Confirm",
            "Are you sure you want to delete learned data and start learning from scratch?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset learning engine thông qua engine
            if self.engine:
                self.engine.learning_engine.reset()
            self.learning_label.setText("Reset complete, relearning...")
            QMessageBox.information(self, "Information", 
                "Learned data deleted. System will relearn from scratch.")
    
    def _toggle_landmarks(self):
        """Bật/tắt hiển thị landmarks"""
        self.engine.toggle_landmarks()
        if self.engine.show_landmarks:
            self.landmarks_btn.setText("HIDE LANDMARKS")
        else:
            self.landmarks_btn.setText("SHOW LANDMARKS")
    
    def closeEvent(self, event):
        """Xử lý khi đóng cửa sổ"""
        if self.engine and self.engine.is_running:
            print("[MainWindow] Đang dừng engine...")
            self.engine.stop()
        
        print("[MainWindow] Đã đóng ứng dụng")
        event.accept()

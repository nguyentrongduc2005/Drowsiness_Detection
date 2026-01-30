"""
============================================================
    DRIVER DROWSINESS DETECTION SYSTEM v2.077
    "High-Tech, Low-Life" Cyberpunk Edition
============================================================

Main Window - Giao diện chính của ứng dụng với Cyberpunk Theme
Nhận signals từ DetectionEngine và cập nhật UI
"""
import cv2
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QMessageBox,
                             QProgressBar, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor

from ..config import ConfigManager
from ..core import DetectionEngine
from ..alert import AlertLevel


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng - Cyberpunk Theme"""
    
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
        self._apply_cyberpunk_style()
        self._create_engine()
        self._connect_signals()
        self._start_decorative_timers()
    
    def _init_ui(self):
        """Khởi tạo giao diện Cyberpunk"""
        # Window Configuration - Normal Windows style with fixed size
        self.setWindowTitle("NEURAL_LINK :: DROWSINESS DETECTOR v2.077")
        self.setFixedSize(1200, 900)  # Increased height to prevent overlap
        
        # Central widget
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        # Master Layout
        master_layout = QVBoxLayout(central_widget)
        master_layout.setContentsMargins(15, 15, 15, 15)
        master_layout.setSpacing(15)
        
        # ===============================================================
        # HEADER BAR
        # ===============================================================
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(50)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title_label = QLabel("DROWSINESS DETECTION SYSTEM")
        title_label.setObjectName("mainTitle")
        
        self.connection_status = QLabel("[READY]")
        self.connection_status.setObjectName("connectionStatus")
        
        self.timestamp_label = QLabel("2077.01.30 | 16:44:26")
        self.timestamp_label.setObjectName("timestampLabel")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.connection_status)
        header_layout.addSpacing(30)
        header_layout.addWidget(self.timestamp_label)
        
        master_layout.addWidget(header_frame)
        
        # ===============================================================
        # CONTENT AREA
        # ===============================================================
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # Left - Camera Display
        self._setup_camera_display(content_layout)
        
        # Right - Control Panel
        self._setup_control_panel(content_layout)
        
        master_layout.addWidget(content_frame, stretch=1)
        
        # ===============================================================
        # FOOTER STATUS BAR
        # ===============================================================
        footer_frame = QFrame()
        footer_frame.setObjectName("footerFrame")
        footer_frame.setFixedHeight(35)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        
        left_status = QLabel("SESSION #2077-ALPHA | DRIVER MONITOR")
        left_status.setObjectName("footerText")
        
        self.system_status = QLabel("[SYSTEM ONLINE]")
        self.system_status.setObjectName("footerActive")
        
        right_status = QLabel("BUILD: v2.077-NEON")
        right_status.setObjectName("footerText")
        
        footer_layout.addWidget(left_status)
        footer_layout.addStretch()
        footer_layout.addWidget(self.system_status)
        footer_layout.addStretch()
        footer_layout.addWidget(right_status)
        
        master_layout.addWidget(footer_frame)
    
    def _setup_camera_display(self, parent_layout):
        """Thiết lập khung hiển thị camera với Cyberpunk style"""
        camera_frame = QFrame()
        camera_frame.setObjectName("cameraFrame")
        camera_layout = QVBoxLayout(camera_frame)
        camera_layout.setContentsMargins(15, 15, 15, 15)
        camera_layout.setSpacing(10)
        
        # Camera Header
        camera_header = QFrame()
        header_layout = QHBoxLayout(camera_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        cam_title = QLabel("[ VISUAL FEED ]")
        cam_title.setObjectName("sectionTitle")
        
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setObjectName("fpsLabel")
        
        header_layout.addWidget(cam_title)
        header_layout.addStretch()
        header_layout.addWidget(self.fps_label)
        
        camera_layout.addWidget(camera_header)
        
        # Video container
        video_container = QFrame()
        video_container.setObjectName("videoContainer")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(3, 3, 3, 3)
        
        self.video_label = QLabel()
        self.video_label.setObjectName("videoLabel")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(700, 480)
        self.video_label.setText("AWAITING NEURAL LINK")
        
        video_layout.addWidget(self.video_label)
        camera_layout.addWidget(video_container, stretch=1)
        
        # Camera Footer
        status_footer = QFrame()
        footer_layout = QHBoxLayout(status_footer)
        footer_layout.setContentsMargins(5, 5, 5, 5)
        
        self.detection_status = QLabel("[STANDBY]")
        self.detection_status.setObjectName("detectionStatus")
        
        self.face_status = QLabel("[NO FACE]")
        self.face_status.setObjectName("faceStatus")
        
        footer_layout.addWidget(self.detection_status)
        footer_layout.addStretch()
        footer_layout.addWidget(self.face_status)
        
        camera_layout.addWidget(status_footer)
        
        parent_layout.addWidget(camera_frame, stretch=3)
    
    def _setup_control_panel(self, parent_layout):
        """Thiết lập bảng điều khiển Cyberpunk"""
        control_frame = QFrame()
        control_frame.setObjectName("controlPanel")
        control_frame.setFixedWidth(350)
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 20, 20, 20)
        control_layout.setSpacing(12)
        
        # ---------------------------------------------------------------
        # SYSTEM STATUS SECTION
        # ---------------------------------------------------------------
        status_header = QLabel("[ SYSTEM STATUS ]")
        status_header.setObjectName("panelHeader")
        status_header.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(status_header)
        
        # Divider
        divider1 = QFrame()
        divider1.setObjectName("divider")
        divider1.setFixedHeight(2)
        control_layout.addWidget(divider1)
        
        # Alert Status Box
        self.status_label = QLabel("OFFLINE")
        self.status_label.setObjectName("alertBox")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(40)
        control_layout.addWidget(self.status_label)
        
        # ---------------------------------------------------------------
        # CONTROL BUTTONS
        # ---------------------------------------------------------------
        control_layout.addSpacing(5)
        
        self.start_stop_btn = QPushButton("INITIALIZE SCANNER")
        self.start_stop_btn.setObjectName("primaryButton")
        self.start_stop_btn.setMinimumHeight(40)
        self.start_stop_btn.clicked.connect(self._toggle_detection)
        control_layout.addWidget(self.start_stop_btn)
        
        control_layout.addSpacing(5) # Spacing
        
        self.learn_btn = QPushButton("RESET NEURAL LEARNING")
        self.learn_btn.setObjectName("secondaryButton")
        self.learn_btn.setMinimumHeight(40)
        self.learn_btn.clicked.connect(self._reset_learning)
        self.learn_btn.setEnabled(False)
        control_layout.addWidget(self.learn_btn)
        
        control_layout.addSpacing(5) # Spacing
        
        self.landmarks_btn = QPushButton("HIDE BIOMETRICS")
        self.landmarks_btn.setObjectName("accentButton")
        self.landmarks_btn.setMinimumHeight(40)
        self.landmarks_btn.clicked.connect(self._toggle_landmarks)
        self.landmarks_btn.setEnabled(False)
        control_layout.addWidget(self.landmarks_btn)
        
        # Learning Progress Bar
        self.learning_label = QLabel("NEURAL LEARNING:")
        self.learning_label.setObjectName("progressLabel")
        control_layout.addWidget(self.learning_label)
        
        self.learning_progress = QProgressBar()
        self.learning_progress.setObjectName("neonProgress")
        self.learning_progress.setValue(0)
        self.learning_progress.setTextVisible(True)
        self.learning_progress.setFormat("%p% | Samples: 0")
        control_layout.addWidget(self.learning_progress)
        
        # ---------------------------------------------------------------
        # BIOMETRIC METRICS
        # ---------------------------------------------------------------
        divider2 = QFrame()
        divider2.setObjectName("divider")
        divider2.setFixedHeight(5)
        control_layout.addWidget(divider2)
        
        metrics_header = QLabel("BIOMETRIC READINGS")
        metrics_header.setObjectName("subHeader")
        control_layout.addWidget(metrics_header)
        
        # Combined Metrics Frame
        self.metrics_frame = QFrame()
        self.metrics_frame.setObjectName("metricFrame")
        metrics_layout = QVBoxLayout(self.metrics_frame)
        metrics_layout.setContentsMargins(12, 10, 12, 10)
        metrics_layout.setSpacing(8)
        
        # EAR Row
        ear_row = QHBoxLayout()
        ear_label = QLabel("EYE ASPECT RATIO:")
        ear_label.setObjectName("metricLabel")
        self.ear_value = QLabel("0.000")
        self.ear_value.setObjectName("metricValueCyan")
        self.ear_threshold = QLabel("THR: 0.000")
        self.ear_threshold.setObjectName("metricValueAmber")
        ear_row.addWidget(ear_label)
        ear_row.addStretch()
        ear_row.addWidget(self.ear_value)
        ear_row.addSpacing(15)
        ear_row.addWidget(self.ear_threshold)
        metrics_layout.addLayout(ear_row)
        
        # MAR Row
        mar_row = QHBoxLayout()
        mar_label = QLabel("MOUTH ASPECT RATIO:")
        mar_label.setObjectName("metricLabel")
        self.mar_value = QLabel("0.000")
        self.mar_value.setObjectName("metricValueCyan")
        self.mar_threshold = QLabel("THR: 0.000")
        self.mar_threshold.setObjectName("metricValueAmber")
        mar_row.addWidget(mar_label)
        mar_row.addStretch()
        mar_row.addWidget(self.mar_value)
        mar_row.addSpacing(15)
        mar_row.addWidget(self.mar_threshold)
        metrics_layout.addLayout(mar_row)
        
        # Divider inside box
        inner_divider = QFrame()
        inner_divider.setFixedHeight(1)
        inner_divider.setStyleSheet("background-color: rgba(0, 240, 255, 0.2);")
        metrics_layout.addWidget(inner_divider)
        
        # Blink Rate Row
        blink_row = QHBoxLayout()
        blink_label = QLabel("BLINK RATE:")
        blink_label.setObjectName("metricLabel")
        self.blink_value = QLabel("0 /min")
        self.blink_value.setObjectName("metricValueCyan")
        blink_row.addWidget(blink_label)
        blink_row.addStretch()
        blink_row.addWidget(self.blink_value)
        metrics_layout.addLayout(blink_row)
        
        # Yawn Count Row
        yawn_row = QHBoxLayout()
        yawn_label = QLabel("YAWN COUNT:")
        yawn_label.setObjectName("metricLabel")
        self.yawn_value = QLabel("0 /min")
        self.yawn_value.setObjectName("metricValueMagenta")
        yawn_row.addWidget(yawn_label)
        yawn_row.addStretch()
        yawn_row.addWidget(self.yawn_value)
        metrics_layout.addLayout(yawn_row)
        
        control_layout.addWidget(self.metrics_frame)
        control_layout.addSpacing(15)

        
        # ---------------------------------------------------------------
        # SYSTEM INFO (Decorative)
        # ---------------------------------------------------------------
        
        info_header = QLabel("SYSTEM INFO")
        info_header.setObjectName("subHeader")
        control_layout.addWidget(info_header)
        
        divider3 = QFrame()
        divider3.setObjectName("divider")
        divider3.setFixedHeight(2)
        control_layout.addWidget(divider3)
        
        info_items = [
            ("ENCRYPTION:", "AES-256"),
            ("PROTOCOL:", "NEURAL-LINK"),
            ("BUILD:", "v2.077-NEON"),
        ]
        
        for label_text, value_text in info_items:
            info_row = QHBoxLayout()
            label = QLabel(label_text)
            label.setObjectName("infoLabel")
            value = QLabel(value_text)
            value.setObjectName("infoValue")
            info_row.addWidget(label)
            info_row.addStretch()
            info_row.addWidget(value)
            control_layout.addLayout(info_row)
        
        parent_layout.addWidget(control_frame)
    
    def _create_metric_row(self, name: str, current: str, threshold: str) -> QFrame:
        """Tạo một hàng metric với current value và threshold"""
        frame = QFrame()
        frame.setObjectName("metricFrame")
        frame.setMinimumHeight(75)  # Fix: Đặt chiều cao tối thiểu để tránh bị cắt chữ
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)
        
        # Name
        name_label = QLabel(name)
        name_label.setObjectName("metricName")
        layout.addWidget(name_label)
        
        # Values row
        values_row = QHBoxLayout()
        
        current_label = QLabel(f"VAL: {current}")
        current_label.setObjectName("metricValueCyan")
        
        threshold_label = QLabel(f"THR: {threshold}")
        threshold_label.setObjectName("metricValueAmber")
        
        values_row.addWidget(current_label)
        values_row.addStretch()
        values_row.addWidget(threshold_label)
        layout.addLayout(values_row)
        
        # Store references
        frame.current_label = current_label
        frame.threshold_label = threshold_label
        
        return frame
    
    def get_stylesheet(self) -> str:
        """Return the complete QSS stylesheet for Cyberpunk theme"""
        return """
        /* ==============================================================
           CYBERPUNK NEON-NOIR THEME - Qt Style Sheet
           Color Palette:
           - Background: #0D0D0D (Deep Matte Black)
           - Primary: #00F0FF (Neon Cyan)
           - Accent: #FF00E0 (Neon Magenta)
           - Warning: #FFB800 (Amber)
           - Success: #00FF88 (Neon Green)
           - Danger: #FF0064 (Neon Red)
        ============================================================== */
        
        /* === MAIN WINDOW === */
        QMainWindow {
            background-color: #0D0D0D;
        }
        
        #centralWidget {
            background-color: #0D0D0D;
        }
        
        /* === HEADER === */
        #headerFrame {
            background-color: rgba(0, 240, 255, 0.08);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 8px;
        }
        
        #mainTitle {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 16px;
            font-weight: bold;
            color: #00F0FF;
            letter-spacing: 3px;
        }
        
        #connectionStatus {
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: #00FF88;
        }
        
        #timestampLabel {
            font-family: 'Consolas', monospace;
            font-size: 11px;
            color: rgba(0, 240, 255, 0.6);
        }
        
        /* === CONTENT FRAME === */
        #contentFrame {
            background-color: transparent;
        }
        
        /* === CAMERA FRAME === */
        #cameraFrame {
            background-color: rgba(20, 20, 25, 0.8);
            border: 1px solid rgba(0, 240, 255, 0.25);
            border-radius: 10px;
        }
        
        #sectionTitle {
            font-family: 'Consolas', monospace;
            font-size: 13px;
            font-weight: bold;
            color: #00F0FF;
            letter-spacing: 2px;
        }
        
        #fpsLabel {
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: #00FF88;
        }
        
        #videoContainer {
            background-color: rgba(0, 0, 0, 0.6);
            border: 2px solid rgba(0, 240, 255, 0.4);
            border-radius: 6px;
        }
        
        #videoLabel {
            background-color: #000000;
            border: none;
            border-radius: 4px;
            color: rgba(0, 240, 255, 0.5);
            font-family: 'Consolas', monospace;
            font-size: 14px;
        }
        
        #detectionStatus {
            font-family: 'Consolas', monospace;
            font-size: 11px;
            font-weight: bold;
            color: rgba(0, 240, 255, 0.8);
        }
        
        #faceStatus {
            font-family: 'Consolas', monospace;
            font-size: 11px;
            font-weight: bold;
            color: #FFB800;
        }
        
        /* === CONTROL PANEL === */
        #controlPanel {
            background-color: rgba(20, 20, 25, 0.9);
            border: 1px solid rgba(0, 240, 255, 0.25);
            border-radius: 10px;
        }
        
        #panelHeader {
            font-family: 'Consolas', monospace;
            font-size: 14px;
            font-weight: bold;
            color: #00F0FF;
            letter-spacing: 2px;
            padding: 5px;
        }
        
        #divider {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.15 #00F0FF, stop:0.85 #00F0FF, stop:1 transparent);
        }
        
        #subHeader {
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: #FF00E0;
            letter-spacing: 1px;
            padding-top: 5px;
        }
        
        /* === ALERT BOX === */
        #alertBox {
            background-color: rgba(100, 100, 100, 0.2);
            border: 2px solid rgba(150, 150, 150, 0.4);
            border-radius: 8px;
            font-family: 'Consolas', monospace;
            font-size: 16px;
            font-weight: bold;
            color: #888888;
            padding: 10px;
        }
        
        /* === BUTTONS === */
        #primaryButton {
            background-color: rgba(0, 240, 255, 0.1);
            border: 2px solid #00F0FF;
            border-radius: 8px;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            font-weight: bold;
            color: #00F0FF;
            letter-spacing: 1px;
            padding: 10px;
        }
        
        #primaryButton:hover {
            background-color: rgba(255, 0, 224, 0.15);
            border-color: #FF00E0;
            color: #FF00E0;
        }
        
        #primaryButton:pressed {
            background-color: rgba(255, 0, 224, 0.25);
        }
        
        #primaryButton:disabled {
            background-color: rgba(100, 100, 100, 0.1);
            border-color: rgba(100, 100, 100, 0.3);
            color: #555555;
        }
        
        #secondaryButton {
            background-color: rgba(255, 0, 224, 0.08);
            border: 2px solid rgba(255, 0, 224, 0.5);
            border-radius: 8px;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: #FF00E0;
            letter-spacing: 1px;
            padding: 8px;
        }
        
        #secondaryButton:hover {
            background-color: rgba(255, 0, 224, 0.2);
            border-color: #FF00E0;
        }
        
        #secondaryButton:disabled {
            background-color: rgba(100, 100, 100, 0.1);
            border-color: rgba(100, 100, 100, 0.3);
            color: #555555;
        }
        
        #accentButton {
            background-color: rgba(255, 184, 0, 0.08);
            border: 2px solid rgba(255, 184, 0, 0.5);
            border-radius: 8px;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: #FFB800;
            letter-spacing: 1px;
            padding: 8px;
        }
        
        #accentButton:hover {
            background-color: rgba(255, 184, 0, 0.2);
            border-color: #FFB800;
        }
        
        #accentButton:disabled {
            background-color: rgba(100, 100, 100, 0.1);
            border-color: rgba(100, 100, 100, 0.3);
            color: #555555;
        }
        
        /* === PROGRESS BAR === */
        #progressLabel {
            font-family: 'Consolas', monospace;
            font-size: 11px;
            color: rgba(0, 240, 255, 0.8);
            padding-top: 5px;
        }
        
        #neonProgress {
            background-color: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 6px;
            height: 22px;
            text-align: center;
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: #FFFFFF;
        }
        
        #neonProgress::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00F0FF, stop:0.5 #FF00E0, stop:1 #FFB800);
            border-radius: 5px;
        }
        
        /* === METRIC FRAMES === */
        #metricFrame {
            background-color: rgba(0, 240, 255, 0.03);
            border: 1px solid rgba(0, 240, 255, 0.15);
            border-radius: 8px;
        }
        
        #metricName {
            font-family: 'Consolas', monospace;
            font-size: 10px;
            font-weight: bold;
            color: rgba(255, 255, 255, 0.7);
            letter-spacing: 1px;
        }
        
        #metricLabel {
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: rgba(255, 255, 255, 0.6);
        }
        
        #metricValueCyan {
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: #00F0FF;
        }
        
        #metricValueMagenta {
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: #FF00E0;
        }
        
        #metricValueAmber {
            font-family: 'Consolas', monospace;
            font-size: 11px;
            font-weight: bold;
            color: #FFB800;
        }
        
        /* === INFO LABELS === */
        #infoLabel {
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: rgba(255, 255, 255, 0.5);
        }
        
        #infoValue {
            font-family: 'Consolas', monospace;
            font-size: 10px;
            font-weight: bold;
            color: #00FF88;
        }
        
        /* === FOOTER === */
        #footerFrame {
            background-color: rgba(0, 240, 255, 0.05);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: 8px;
        }
        
        #footerText {
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: rgba(0, 240, 255, 0.5);
        }
        
        #footerActive {
            font-family: 'Consolas', monospace;
            font-size: 10px;
            font-weight: bold;
            color: #00FF88;
        }
        
        /* === MESSAGE BOX === */
        QMessageBox {
            background-color: #0D0D0D;
        }
        
        QMessageBox QLabel {
            color: #00F0FF;
            font-family: 'Consolas', monospace;
        }
        
        QMessageBox QPushButton {
            background-color: rgba(0, 240, 255, 0.1);
            border: 2px solid #00F0FF;
            border-radius: 5px;
            color: #00F0FF;
            font-family: 'Consolas', monospace;
            padding: 8px 20px;
            min-width: 80px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: rgba(0, 240, 255, 0.2);
        }
        """
    
    def _apply_cyberpunk_style(self):
        """Apply the Cyberpunk QSS stylesheet"""
        self.setStyleSheet(self.get_stylesheet())
    
    def _start_decorative_timers(self):
        """Start decorative animation timers"""
        # Timestamp update
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_timestamp)
        self.time_timer.start(1000)
    
    def _update_timestamp(self):
        """Update timestamp display"""
        from datetime import datetime
        now = datetime.now()
        self.timestamp_label.setText(f"{now.strftime('%Y.%m.%d | %H:%M:%S')}")
    
    # ===================================================================
    # DETECTION ENGINE LOGIC (GIỮ NGUYÊN)
    # ===================================================================
    
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
        # Update FPS display
        self.fps_label.setText(f"FPS: {fps:.1f}")
        
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
        if detected:
            self.face_status.setText("[FACE LOCKED]")
            self.face_status.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
                color: #00FF88;
            """)
        else:
            self.face_status.setText("[NO FACE]")
            self.face_status.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
                color: #FFB800;
            """)
    
    @pyqtSlot(dict)
    def _on_metrics_updated(self, metrics: dict):
        """
        Cập nhật hiển thị metrics
        
        Args:
            metrics: Dictionary chứa các metrics
        """
        # Update EAR
        self.ear_value.setText(f"{metrics['ear']:.3f}")
        self.ear_threshold.setText(f"THR: {metrics['ear_threshold']:.3f}")
        
        # Update MAR
        self.mar_value.setText(f"{metrics['mar']:.3f}")
        self.mar_threshold.setText(f"THR: {metrics['mar_threshold']:.3f}")
        
        # Update activity
        self.blink_value.setText(f"{metrics['blink_rate']} /min")
        self.yawn_value.setText(f"{metrics['yawn_count']} /min")
    
    @pyqtSlot(int)
    def _on_alert_changed(self, alert_level: int):
        """Xử lý khi mức cảnh báo thay đổi"""
        pass  # Alert được xử lý trong engine
    
    @pyqtSlot(str, str)
    def _on_status_changed(self, status: str, color: str):
        """
        Cập nhật trạng thái hệ thống với Cyberpunk style
        
        Args:
            status: Text trạng thái
            color: Màu nền gốc
        """
        self.status_label.setText(status.upper())
        
        # Map colors to Cyberpunk palette
        if 'green' in color.lower() or '#4CAF50' in color or '#00FF88' in color:
            # Normal/Safe
            self.status_label.setStyleSheet("""
                background-color: rgba(0, 255, 136, 0.15);
                border: 2px solid #00FF88;
                border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
                color: #00FF88;
                padding: 10px;
            """)
            self.detection_status.setText("[MONITORING]")
            self.detection_status.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
                color: #00FF88;
            """)
        elif 'yellow' in color.lower() or 'orange' in color.lower() or '#FFB800' in color:
            # Warning
            self.status_label.setStyleSheet("""
                background-color: rgba(255, 184, 0, 0.15);
                border: 2px solid #FFB800;
                border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
                color: #FFB800;
                padding: 10px;
            """)
            self.detection_status.setText("[WARNING]")
            self.detection_status.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
                color: #FFB800;
            """)
        elif 'red' in color.lower() or '#f44336' in color or '#FF0064' in color:
            # Danger/Alert
            self.status_label.setStyleSheet("""
                background-color: rgba(255, 0, 100, 0.2);
                border: 2px solid #FF0064;
                border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
                color: #FF0064;
                padding: 10px;
            """)
            self.detection_status.setText("[ALERT - DROWSINESS]")
            self.detection_status.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
                color: #FF0064;
            """)
        else:
            # Default/Cyan
            self.status_label.setStyleSheet("""
                background-color: rgba(0, 240, 255, 0.1);
                border: 2px solid #00F0FF;
                border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
                color: #00F0FF;
                padding: 10px;
            """)
    
    @pyqtSlot(float)
    def _on_learning_progress(self, progress: float):
        """
        Cập nhật tiến độ học
        
        Args:
            progress: Tiến độ 0-100
        """
        self.learning_progress.setValue(int(progress))
        
        # Lấy tổng số mẫu từ learning engine
        if self.engine and self.engine.learning_engine:
            total_samples = self.engine.learning_engine.get_total_samples()
            self.learning_progress.setFormat(f"%p% | Samples: {total_samples}")
        else:
            self.learning_progress.setFormat(f"%p%")
    
    @pyqtSlot(str)
    def _on_error_occurred(self, error: str):
        """
        Xử lý khi có lỗi
        
        Args:
            error: Thông báo lỗi
        """
        QMessageBox.critical(self, "SYSTEM ERROR", error)
        self.status_label.setText("ERROR")
        self.status_label.setStyleSheet("""
            background-color: rgba(255, 0, 100, 0.2);
            border: 2px solid #FF0064;
            border-radius: 8px;
            font-family: 'Consolas', monospace;
            font-size: 16px;
            font-weight: bold;
            color: #FF0064;
            padding: 10px;
        """)
    
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
            
            self.start_stop_btn.setText("TERMINATE SCANNER")
            self.start_stop_btn.setStyleSheet("""
                background-color: rgba(255, 0, 100, 0.15);
                border: 2px solid #FF0064;
                border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                font-weight: bold;
                color: #FF0064;
                letter-spacing: 1px;
                padding: 10px;
            """)
            self.learn_btn.setEnabled(True)
            self.landmarks_btn.setEnabled(True)
            
            self.connection_status.setText("[ACTIVE]")
            self.connection_status.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-size: 12px;
                font-weight: bold;
                color: #00FF88;
            """)
            
            self.system_status.setText("[SCANNING]")
        else:
            # Dừng
            self.engine.stop()
            
            self.start_stop_btn.setText("INITIALIZE SCANNER")
            self.start_stop_btn.setStyleSheet("""
                background-color: rgba(0, 240, 255, 0.1);
                border: 2px solid #00F0FF;
                border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                font-weight: bold;
                color: #00F0FF;
                letter-spacing: 1px;
                padding: 10px;
            """)
            self.learn_btn.setEnabled(False)
            self.landmarks_btn.setEnabled(False)
            
            self.video_label.clear()
            self.video_label.setText("AWAITING NEURAL LINK")
            self.video_label.setStyleSheet("""
                background-color: #000000;
                border: none;
                border-radius: 4px;
                color: rgba(0, 240, 255, 0.5);
                font-family: 'Consolas', monospace;
                font-size: 14px;
            """)
            
            self.status_label.setText("OFFLINE")
            self.status_label.setStyleSheet("""
                background-color: rgba(100, 100, 100, 0.2);
                border: 2px solid rgba(150, 150, 150, 0.4);
                border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
                color: #888888;
                padding: 10px;
            """)
            
            self.detection_status.setText("[STANDBY]")
            self.detection_status.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
                color: rgba(0, 240, 255, 0.8);
            """)
            
            self.connection_status.setText("[READY]")
            self.connection_status.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-size: 12px;
                font-weight: bold;
                color: #00FF88;
            """)
            
            self.system_status.setText("[SYSTEM ONLINE]")
            self.fps_label.setText("FPS: --")
    
    def _reset_learning(self):
        """Reset và học lại từ đầu"""
        reply = QMessageBox.question(
            self, 
            "CONFIRM NEURAL RESET",
            "Are you sure you want to delete learned data and reinitialize neural learning from scratch?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset learning engine thông qua engine
            if self.engine:
                self.engine.learning_engine.reset()
            self.learning_progress.setValue(0)
            self.learning_progress.setFormat("%p% | Samples: 0")
            QMessageBox.information(self, "NEURAL RESET COMPLETE", 
                "Neural learning data purged. System will reinitialize learning sequence.")
    
    def _toggle_landmarks(self):
        """Bật/tắt hiển thị landmarks"""
        self.engine.toggle_landmarks()
        if self.engine.show_landmarks:
            self.landmarks_btn.setText("HIDE BIOMETRICS")
        else:
            self.landmarks_btn.setText("SHOW BIOMETRICS")
    
    def closeEvent(self, event):
        """Xử lý khi đóng cửa sổ"""
        if self.engine and self.engine.is_running:
            print("[MainWindow] Đang dừng engine...")
            self.engine.stop()
        
        # Stop decorative timers
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()
        
        print("[MainWindow] Đã đóng ứng dụng")
        event.accept()

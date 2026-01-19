"""
Settings Dialog - Cho phép người dùng thay đổi cài đặt ứng dụng
"""
# pylint: disable=no-name-in-module
# pyright: reportMissingModuleSource=false

from PyQt5.QtWidgets import (  # type: ignore
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSpinBox, QDoubleSpinBox, QCheckBox,
    QGroupBox, QFormLayout, QTabWidget, QWidget,
    QSlider, QComboBox, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal  # type: ignore
from PyQt5.QtGui import QFont  # type: ignore


class SettingsDialog(QDialog):
    """Dialog cài đặt với giao diện dark theme"""
    
    # Signal khi settings thay đổi
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.original_values = {}  # Lưu giá trị gốc để reset
        
        self._setup_ui()
        self._load_current_settings()
        self._apply_dark_theme()
    
    def _setup_ui(self):
        """Thiết lập giao diện"""
        self.setWindowTitle("⚙️ Cài đặt")
        self.setMinimumSize(500, 550)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("⚙️ Cài đặt hệ thống")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_detection_tab(), "🎯 Phát hiện")
        tabs.addTab(self._create_camera_tab(), "📷 Camera")
        tabs.addTab(self._create_alert_tab(), "🔔 Cảnh báo")
        tabs.addTab(self._create_advanced_tab(), "⚡ Nâng cao")
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.reset_btn = QPushButton("🔄 Đặt lại mặc định")
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        
        self.cancel_btn = QPushButton("❌ Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("✅ Lưu")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setDefault(True)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _create_detection_tab(self):
        """Tab cài đặt phát hiện"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # EAR Settings
        ear_group = QGroupBox("👁 Ngưỡng mắt (EAR)")
        ear_layout = QFormLayout(ear_group)
        
        self.ear_default = QDoubleSpinBox()
        self.ear_default.setRange(0.15, 0.35)
        self.ear_default.setSingleStep(0.01)
        self.ear_default.setDecimals(2)
        ear_layout.addRow("Ngưỡng EAR mặc định:", self.ear_default)
        
        self.consecutive_frames = QSpinBox()
        self.consecutive_frames.setRange(10, 100)
        ear_layout.addRow("Số frame liên tiếp để cảnh báo:", self.consecutive_frames)
        
        layout.addWidget(ear_group)
        
        # MAR Settings
        mar_group = QGroupBox("👄 Ngưỡng miệng (MAR)")
        mar_layout = QFormLayout(mar_group)
        
        self.mar_limit = QDoubleSpinBox()
        self.mar_limit.setRange(0.4, 0.9)
        self.mar_limit.setSingleStep(0.05)
        self.mar_limit.setDecimals(2)
        mar_layout.addRow("Ngưỡng phát hiện ngáp:", self.mar_limit)
        
        self.yawn_frames = QSpinBox()
        self.yawn_frames.setRange(10, 60)
        mar_layout.addRow("Số frame ngáp liên tiếp:", self.yawn_frames)
        
        layout.addWidget(mar_group)
        
        # PERCLOS Settings
        perclos_group = QGroupBox("📊 PERCLOS")
        perclos_layout = QFormLayout(perclos_group)
        
        self.perclos_warning = QSpinBox()
        self.perclos_warning.setRange(10, 30)
        self.perclos_warning.setSuffix("%")
        perclos_layout.addRow("Ngưỡng cảnh báo:", self.perclos_warning)
        
        self.perclos_danger = QSpinBox()
        self.perclos_danger.setRange(20, 50)
        self.perclos_danger.setSuffix("%")
        perclos_layout.addRow("Ngưỡng nguy hiểm:", self.perclos_danger)
        
        layout.addWidget(perclos_group)
        
        layout.addStretch()
        return tab
    
    def _create_camera_tab(self):
        """Tab cài đặt camera"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Camera Settings
        camera_group = QGroupBox("📷 Camera")
        camera_layout = QFormLayout(camera_group)
        
        self.camera_id = QSpinBox()
        self.camera_id.setRange(0, 10)
        camera_layout.addRow("Camera ID:", self.camera_id)
        
        # Resolution (readonly info)
        res_label = QLabel("640 x 480 (tối ưu)")
        res_label.setStyleSheet("color: #9CA3AF;")
        camera_layout.addRow("Độ phân giải:", res_label)
        
        layout.addWidget(camera_group)
        
        # Display Settings
        display_group = QGroupBox("🖥️ Hiển thị")
        display_layout = QFormLayout(display_group)
        
        self.show_landmarks = QCheckBox("Hiển thị 68 điểm landmarks")
        display_layout.addRow(self.show_landmarks)
        
        self.show_fps = QCheckBox("Hiển thị FPS")
        display_layout.addRow(self.show_fps)
        
        layout.addWidget(display_group)
        
        layout.addStretch()
        return tab
    
    def _create_alert_tab(self):
        """Tab cài đặt cảnh báo"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Sound Settings
        sound_group = QGroupBox("🔊 Âm thanh")
        sound_layout = QFormLayout(sound_group)
        
        self.sound_enabled = QCheckBox("Bật âm thanh cảnh báo")
        sound_layout.addRow(self.sound_enabled)
        
        self.alarm_cooldown = QSpinBox()
        self.alarm_cooldown.setRange(1, 10)
        self.alarm_cooldown.setSuffix(" giây")
        sound_layout.addRow("Thời gian chờ giữa các cảnh báo:", self.alarm_cooldown)
        
        layout.addWidget(sound_group)
        
        # Log Settings
        log_group = QGroupBox("📝 Ghi log")
        log_layout = QFormLayout(log_group)
        
        self.log_enabled = QCheckBox("Ghi log sự kiện")
        log_layout.addRow(self.log_enabled)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        return tab
    
    def _create_advanced_tab(self):
        """Tab cài đặt nâng cao"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Smart Threshold
        smart_group = QGroupBox("🧠 Ngưỡng thông minh")
        smart_layout = QFormLayout(smart_group)
        
        self.window_size = QSpinBox()
        self.window_size.setRange(50, 300)
        smart_layout.addRow("Kích thước cửa sổ học:", self.window_size)
        
        self.min_samples = QSpinBox()
        self.min_samples.setRange(50, 200)
        smart_layout.addRow("Số mẫu tối thiểu:", self.min_samples)
        
        self.threshold_multiplier = QDoubleSpinBox()
        self.threshold_multiplier.setRange(0.5, 0.9)
        self.threshold_multiplier.setSingleStep(0.05)
        self.threshold_multiplier.setDecimals(2)
        smart_layout.addRow("Hệ số ngưỡng:", self.threshold_multiplier)
        
        layout.addWidget(smart_group)
        
        # Performance
        perf_group = QGroupBox("⚡ Hiệu suất")
        perf_layout = QFormLayout(perf_group)
        
        info_label = QLabel("Các cài đặt hiệu suất đã được tối ưu tự động")
        info_label.setStyleSheet("color: #9CA3AF; font-style: italic;")
        perf_layout.addRow(info_label)
        
        layout.addWidget(perf_group)
        
        layout.addStretch()
        return tab
    
    def _load_current_settings(self):
        """Load cài đặt hiện tại từ config"""
        # EAR
        self.ear_default.setValue(self.config.get('eye_thresholds.ear_default', 0.25))
        self.consecutive_frames.setValue(self.config.get('eye_thresholds.consecutive_frames', 45))
        
        # MAR
        self.mar_limit.setValue(self.config.get('mouth_thresholds.mar_limit', 0.6))
        self.yawn_frames.setValue(self.config.get('mouth_thresholds.yawn_frames', 30))
        
        # PERCLOS
        self.perclos_warning.setValue(15)
        self.perclos_danger.setValue(25)
        
        # Camera
        self.camera_id.setValue(self.config.get('settings.camera_id', 0))
        self.show_landmarks.setChecked(self.config.get('settings.show_landmarks', True))
        self.show_fps.setChecked(self.config.get('settings.fps_display', True))
        
        # Alert
        self.sound_enabled.setChecked(True)
        self.alarm_cooldown.setValue(3)
        self.log_enabled.setChecked(self.config.get('settings.log_enabled', True))
        
        # Smart Threshold
        self.window_size.setValue(self.config.get('smart_threshold.window_size', 150))
        self.min_samples.setValue(self.config.get('smart_threshold.min_samples_for_learning', 100))
        self.threshold_multiplier.setValue(self.config.get('smart_threshold.threshold_multiplier', 0.75))
        
        # Lưu giá trị gốc
        self._save_original_values()
    
    def _save_original_values(self):
        """Lưu giá trị gốc để reset"""
        self.original_values = {
            'ear_default': self.ear_default.value(),
            'consecutive_frames': self.consecutive_frames.value(),
            'mar_limit': self.mar_limit.value(),
            'yawn_frames': self.yawn_frames.value(),
            'camera_id': self.camera_id.value(),
            'show_landmarks': self.show_landmarks.isChecked(),
            'show_fps': self.show_fps.isChecked(),
            'log_enabled': self.log_enabled.isChecked(),
            'window_size': self.window_size.value(),
            'min_samples': self.min_samples.value(),
            'threshold_multiplier': self.threshold_multiplier.value(),
        }
    
    def _reset_to_defaults(self):
        """Đặt lại về giá trị mặc định"""
        reply = QMessageBox.question(
            self, "Xác nhận",
            "Bạn có chắc muốn đặt lại tất cả về giá trị mặc định?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # EAR
            self.ear_default.setValue(0.25)
            self.consecutive_frames.setValue(45)
            
            # MAR
            self.mar_limit.setValue(0.6)
            self.yawn_frames.setValue(30)
            
            # PERCLOS
            self.perclos_warning.setValue(15)
            self.perclos_danger.setValue(25)
            
            # Camera
            self.camera_id.setValue(0)
            self.show_landmarks.setChecked(True)
            self.show_fps.setChecked(True)
            
            # Alert
            self.sound_enabled.setChecked(True)
            self.alarm_cooldown.setValue(3)
            self.log_enabled.setChecked(True)
            
            # Smart Threshold
            self.window_size.setValue(150)
            self.min_samples.setValue(100)
            self.threshold_multiplier.setValue(0.75)
    
    def _save_settings(self):
        """Lưu cài đặt"""
        # Cập nhật config
        self.config.config['eye_thresholds']['ear_default'] = self.ear_default.value()
        self.config.config['eye_thresholds']['consecutive_frames'] = self.consecutive_frames.value()
        self.config.config['mouth_thresholds']['mar_limit'] = self.mar_limit.value()
        self.config.config['mouth_thresholds']['yawn_frames'] = self.yawn_frames.value()
        self.config.config['settings']['camera_id'] = self.camera_id.value()
        self.config.config['settings']['show_landmarks'] = self.show_landmarks.isChecked()
        self.config.config['settings']['fps_display'] = self.show_fps.isChecked()
        self.config.config['settings']['log_enabled'] = self.log_enabled.isChecked()
        self.config.config['smart_threshold']['window_size'] = self.window_size.value()
        self.config.config['smart_threshold']['min_samples_for_learning'] = self.min_samples.value()
        self.config.config['smart_threshold']['threshold_multiplier'] = self.threshold_multiplier.value()
        
        # Lưu vào file
        if self.config.save_config():
            # Emit signal
            self.settings_changed.emit(self.config.config)
            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt!")
            self.accept()
        else:
            QMessageBox.warning(self, "Lỗi", "Không thể lưu cài đặt!")
    
    def _apply_dark_theme(self):
        """Áp dụng dark theme"""
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0A0C;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #2A2A30;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #16161A;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #9CA3AF;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #1A1A20;
                border: 1px solid #2A2A30;
                border-radius: 6px;
                padding: 6px 10px;
                color: #FFFFFF;
                min-width: 100px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #06B6D4;
            }
            QCheckBox {
                color: #FFFFFF;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #2A2A30;
                background-color: #1A1A20;
            }
            QCheckBox::indicator:checked {
                background-color: #10B981;
                border: 1px solid #10B981;
            }
            QTabWidget::pane {
                border: 1px solid #2A2A30;
                border-radius: 8px;
                background-color: #0A0A0C;
            }
            QTabBar::tab {
                background-color: #16161A;
                color: #9CA3AF;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #0A0A0C;
                color: #FFFFFF;
                border-bottom: 2px solid #06B6D4;
            }
            QPushButton {
                background-color: #16161A;
                border: 1px solid #2A2A30;
                border-radius: 8px;
                padding: 10px 20px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E1E24;
                border: 1px solid #3A3A42;
            }
            QPushButton:pressed {
                background-color: #0A0A0C;
            }
            QPushButton#save_btn {
                background-color: #10B981;
                border: none;
            }
            QPushButton#save_btn:hover {
                background-color: #059669;
            }
        """)
        
        # Style đặc biệt cho nút Save
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                border: none;
                border-radius: 8px;
                padding: 10px 25px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                border: none;
                border-radius: 8px;
                padding: 10px 25px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)

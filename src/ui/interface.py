"""
Module Giao diện: Thiết kế UI cho ứng dụng phát hiện buồn ngủ
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QGroupBox, QStatusBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont


class MainWindow(QMainWindow):
    """
    Class chính của giao diện ứng dụng
    """
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("Hệ thống Phát hiện Buồn ngủ")
        self.setGeometry(100, 100, 1200, 700)
        
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # === Panel bên trái: Video ===
        video_layout = QVBoxLayout()
        
        # Label hiển thị video
        self.video_label = QLabel()
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #333333;
                border-radius: 5px;
            }
        """)
        video_layout.addWidget(self.video_label)
        
        main_layout.addLayout(video_layout, 70)
        
        # === Panel bên phải: Thông tin ===
        info_layout = QVBoxLayout()
        
        # === Group box: Trạng thái hệ thống ===
        status_group = QGroupBox("Trạng thái Hệ thống")
        status_group.setFont(QFont("Arial", 12, QFont.Bold))
        status_layout = QVBoxLayout()
        
        # Label trạng thái (Đang học / Đang bảo vệ)
        self.status_label = QLabel("Đang khởi động...")
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 15px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        info_layout.addWidget(status_group)
        
        # === Group box: Chỉ số ===
        metrics_group = QGroupBox("Chỉ số Giám sát")
        metrics_group.setFont(QFont("Arial", 12, QFont.Bold))
        metrics_layout = QVBoxLayout()
        
        # EAR
        self.ear_label = QLabel("EAR: --")
        self.ear_label.setFont(QFont("Arial", 12))
        self.ear_label.setStyleSheet("padding: 5px;")
        metrics_layout.addWidget(self.ear_label)
        
        # Threshold
        self.threshold_label = QLabel("Ngưỡng: --")
        self.threshold_label.setFont(QFont("Arial", 12))
        self.threshold_label.setStyleSheet("padding: 5px;")
        metrics_layout.addWidget(self.threshold_label)
        
        # FPS
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setFont(QFont("Arial", 12))
        self.fps_label.setStyleSheet("padding: 5px;")
        metrics_layout.addWidget(self.fps_label)
        
        metrics_group.setLayout(metrics_layout)
        info_layout.addWidget(metrics_group)
        
        # === Group box: Cảnh báo ===
        alert_group = QGroupBox("Cảnh báo")
        alert_group.setFont(QFont("Arial", 12, QFont.Bold))
        alert_layout = QVBoxLayout()
        
        self.alert_label = QLabel("Tỉnh táo")
        self.alert_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.alert_label.setAlignment(Qt.AlignCenter)
        self.alert_label.setStyleSheet("""
            QLabel {
                background-color: #2ecc71;
                color: white;
                padding: 20px;
                border-radius: 5px;
            }
        """)
        alert_layout.addWidget(self.alert_label)
        
        alert_group.setLayout(alert_layout)
        info_layout.addWidget(alert_group)
        
        # === Nút điều khiển ===
        button_layout = QVBoxLayout()
        
        self.start_button = QPushButton("Bắt đầu")
        self.start_button.setFont(QFont("Arial", 12))
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Dừng")
        self.stop_button.setFont(QFont("Arial", 12))
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.stop_button)
        
        self.reset_button = QPushButton("Học lại")
        self.reset_button.setFont(QFont("Arial", 12))
        self.reset_button.setMinimumHeight(40)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        button_layout.addWidget(self.reset_button)
        
        info_layout.addLayout(button_layout)
        
        # Thêm khoảng trống
        info_layout.addStretch()
        
        main_layout.addLayout(info_layout, 30)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Sẵn sàng")
        
    def update_view(self, qt_image, ear, threshold, status, is_drowsy=False, fps=0):
        """
        Cập nhật giao diện với thông tin mới
        
        Args:
            qt_image: QImage để hiển thị trên video_label
            ear: Giá trị EAR hiện tại
            threshold: Ngưỡng hiện tại
            status: Text trạng thái (Hệ thống đang học / Đang bảo vệ)
            is_drowsy: True nếu phát hiện buồn ngủ
            fps: Frames per second
        """
        # Cập nhật video
        if qt_image is not None:
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(self.video_label.size(), 
                                         Qt.KeepAspectRatio, 
                                         Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled_pixmap)
        
        # Cập nhật EAR
        self.ear_label.setText(f"EAR: {ear:.3f}")
        
        # Cập nhật Threshold
        self.threshold_label.setText(f"Ngưỡng: {threshold:.3f}")
        
        # Cập nhật FPS
        self.fps_label.setText(f"FPS: {fps:.1f}")
        
        # Cập nhật trạng thái hệ thống
        self.status_label.setText(status)
        
        # Đổi màu dựa trên trạng thái
        if "Đang học" in status:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #3498db;
                    color: white;
                    padding: 15px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #2ecc71;
                    color: white;
                    padding: 15px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
        
        # Cập nhật cảnh báo
        if is_drowsy:
            self.alert_label.setText("⚠ CẢNH BÁO: BUỒN NGỦ!")
            self.alert_label.setStyleSheet("""
                QLabel {
                    background-color: #e74c3c;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
            
            # Nhấp nháy (có thể thêm hiệu ứng)
            self.statusBar.showMessage("⚠ CẢNH BÁO: Phát hiện buồn ngủ!", 5000)
        else:
            self.alert_label.setText("✓ Tỉnh táo")
            self.alert_label.setStyleSheet("""
                QLabel {
                    background-color: #2ecc71;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
    
    def set_buttons_state(self, started):
        """
        Đặt trạng thái các nút
        
        Args:
            started: True nếu đã bắt đầu, False nếu dừng
        """
        self.start_button.setEnabled(not started)
        self.stop_button.setEnabled(started)

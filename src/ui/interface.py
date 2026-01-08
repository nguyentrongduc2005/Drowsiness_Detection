"""
Module Giao diện: Thiết kế UI cho ứng dụng phát hiện buồn ngủ
Style: Military Dashboard / Sci-Fi HUD
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QGroupBox, QStatusBar, QFrame,
                             QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor

# --- Cyberpunk / Military Palette ---
COLOR_BG_MAIN = "#000000"     # Deepest Black
COLOR_PANEL_BG = "#0b0c10"    # Dark panel bg
COLOR_CYAN = "#00f3ff"        # Primary Accent (Neon Cyan)
COLOR_RED = "#ff003c"         # Alert Color
COLOR_GREEN = "#1fcc7e"       # Safe Color
COLOR_TEXT_DIM = "#8892b0"    # Dimmed text
FONT_HUD = "Consolas"         # Monospaced font

class MainWindow(QMainWindow):
    """
    Class chính của giao diện ứng dụng (HUD Style)
    """
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("SENTINEL :: OPERATOR INTERFACE")
        # FIX UI 3: Fixed window size, smaller dimensions
        self.setFixedSize(1200, 700)
        
        # --- GLOBAL STYLESHEET ---
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_BG_MAIN};
            }}
            QWidget {{
                font-family: '{FONT_HUD}';
                color: {COLOR_CYAN};
            }}
            QGroupBox {{
                background-color: {COLOR_PANEL_BG};
                border: 1px solid #1f2833;
                border-top: 2px solid {COLOR_CYAN};
                border-radius: 4px;
                margin-top: 24px;
                padding-top: 10px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                background-color: {COLOR_CYAN};
                color: #000;
                font-weight: bold;
                border: none;
            }}
            QLabel {{
                border: none;
            }}
        """)
        
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính (Split 75% | 25%)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # =========================================================================
        # LEFT PANEL: CAMERA FEED (HUD STYLE)
        # =========================================================================
        
        # Container for the video to handle the border and HUD elements
        self.video_container = QFrame()
        self.video_container.setFrameShape(QFrame.NoFrame)
        # A glowing border effect for the frame
        self.video_container.setStyleSheet(f"""
            QFrame {{
                background-color: #000000;
                border: 1px solid #1f2833;
                border-radius: 2px;
            }}
        """)
        
        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(2, 2, 2, 2)
        
        # The Video Label itself
        self.video_label = QLabel()
        # CRITICAL FIX: Set minimum size to avoid infinite growth loop
        self.video_label.setMinimumSize(1, 1)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setStyleSheet("border: 1px solid #00f3ff; background-color: #000;")
        # Placeholder text
        self.video_label.setText("SIGNAL_LOST // WAITING_FOR_LINK...")
        
        # Add labels to make it look like a viewfinder
        overlay_layout = QVBoxLayout(self.video_label)
        overlay_layout.setContentsMargins(10, 10, 10, 10)
        
        top_hud = QHBoxLayout()
        lbl_cam = QLabel("CAM_01: ACTIVE")
        lbl_cam.setStyleSheet("background: transparent; color: #00f3ff; font-size: 10px;")
        lbl_rec = QLabel("[ REC ]")
        lbl_rec.setStyleSheet("background: transparent; color: #ff003c; font-size: 10px;")
        top_hud.addWidget(lbl_cam)
        top_hud.addStretch()
        top_hud.addWidget(lbl_rec)
        
        overlay_layout.addLayout(top_hud)
        overlay_layout.addStretch()
        
        bottom_hud = QHBoxLayout()
        lbl_coords = QLabel("X: 000 | Y: 000")
        lbl_coords.setStyleSheet("background: transparent; color: #00f3ff; font-size: 10px;")
        bottom_hud.addWidget(lbl_coords)
        bottom_hud.addStretch()
        
        overlay_layout.addLayout(bottom_hud)
        
        video_layout.addWidget(self.video_label)
        
        # Add to main layout (75%)
        main_layout.addWidget(self.video_container, 75)
        
        # =========================================================================
        # RIGHT PANEL: SIDEBAR DASHBOARD
        # =========================================================================
        
        sidebar = QFrame()
        sidebar.setStyleSheet(f"background-color: {COLOR_PANEL_BG}; border-left: 2px solid #0b0c10;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 10, 15, 15)
        sidebar_layout.setSpacing(20)
        
        # 1. HEADER
        lbl_header = QLabel("SENTINEL\nMONITORING SYSTEM")
        lbl_header.setAlignment(Qt.AlignCenter)
        lbl_header.setFont(QFont(FONT_HUD, 16, QFont.Bold))
        lbl_header.setStyleSheet(f"""
            color: {COLOR_CYAN};
            border-bottom: 2px solid {COLOR_CYAN};
            padding-bottom: 10px;
            letter-spacing: 2px;
        """)
        sidebar_layout.addWidget(lbl_header)

        # 2. STATUS BOX
        status_group = QGroupBox("SYSTEM STATUS")
        vbox_status = QVBoxLayout()
        self.status_display = QLabel("STANDBY")
        self.status_display.setAlignment(Qt.AlignCenter)
        self.status_display.setFont(QFont(FONT_HUD, 14, QFont.Bold))
        self.status_display.setStyleSheet(f"color: white; background-color: #1a1a1a; padding: 10px; border-radius: 4px;")
        vbox_status.addWidget(self.status_display)
        status_group.setLayout(vbox_status)
        sidebar_layout.addWidget(status_group)
        
        # 3. METRICS READOUT (GRID)
        metrics_group = QGroupBox("LIVE TELEMETRY")
        grid_metrics = QGridLayout()
        grid_metrics.setVerticalSpacing(15)
        grid_metrics.setHorizontalSpacing(10)
        
        # Helper for metric item
        def add_metric_widget(name, row, col):
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0,0,0,0)
            vbox.setSpacing(2)
            
            lbl_name = QLabel(name)
            lbl_name.setFont(QFont(FONT_HUD, 9))
            lbl_name.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
            lbl_name.setAlignment(Qt.AlignLeft)
            
            lbl_val = QLabel("--")
            lbl_val.setFont(QFont(FONT_HUD, 18, QFont.Bold))
            lbl_val.setStyleSheet(f"color: {COLOR_CYAN};")
            lbl_val.setAlignment(Qt.AlignLeft)
            
            vbox.addWidget(lbl_name)
            vbox.addWidget(lbl_val)
            
            grid_metrics.addWidget(container, row, col)
            return lbl_val

        self.val_ear = add_metric_widget("EAR (Eyes)", 0, 0)
        self.val_mar = add_metric_widget("MAR (Mouth)", 0, 1)
        self.val_fps = add_metric_widget("FPS_RATE", 1, 0)
        self.val_thresh = add_metric_widget("THRESHOLD", 1, 1)
        
        metrics_group.setLayout(grid_metrics)
        sidebar_layout.addWidget(metrics_group)
        
        # 4. ALERT STATUS AREA
        self.alert_box = QFrame()
        self.alert_box.setFrameShape(QFrame.NoFrame)
        # Initial Style (Sci-Fi Green Glass)
        self.alert_box.setStyleSheet(f"""
            background-color: rgba(31, 204, 126, 0.1);
            border: 2px solid {COLOR_GREEN};
            border-radius: 6px;
        """)
        alert_layout = QVBoxLayout(self.alert_box)
        
        self.lbl_alert_text = QLabel("STATUS :: ONLINE")
        self.lbl_alert_text.setAlignment(Qt.AlignCenter)
        self.lbl_alert_text.setFont(QFont(FONT_HUD, 14, QFont.Bold))
        # Style text with neon glow look and spacing
        self.lbl_alert_text.setStyleSheet(f"border: none; color: {COLOR_GREEN}; padding: 0px; letter-spacing: 2px;")
        
        alert_layout.addWidget(self.lbl_alert_text)
        
        sidebar_layout.addWidget(self.alert_box)
        
        # Spacer
        sidebar_layout.addStretch()
        
        # 5. CONTROL PANEL (Buttons)
        controls_group = QGroupBox("MANUAL OVERRIDE")
        controls_layout = QVBoxLayout()
        # FIX UI 1: Increase spacing between buttons
        controls_layout.setSpacing(20)
        
        def create_btn(text, obj_name, bg_color):
            btn = QPushButton(text)
            btn.setObjectName(obj_name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(45)
            btn.setFont(QFont(FONT_HUD, 10, QFont.Bold))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color}33;  /* 33 denotes alpha transparency */
                    border: 2px solid {bg_color};
                    color: {bg_color};
                    border-radius: 0px;
                }}
                QPushButton:hover {{
                    background-color: {bg_color};
                    color: #000;
                }}
                QPushButton:disabled {{
                    border-color: #333;
                    color: #333;
                    background-color: transparent;
                }}
            """)
            return btn

        self.start_button = create_btn("INITIATE (START)", "btnStart", COLOR_CYAN)
        self.stop_button = create_btn("TERMINATE (STOP)", "btnStop", COLOR_RED)
        self.reset_button = create_btn("RE-CALIBRATE", "btnReset", "#f39c12") # Orange
        
        # Logic initial state
        self.stop_button.setEnabled(False)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.reset_button)
        
        controls_group.setLayout(controls_layout)
        sidebar_layout.addWidget(controls_group)
        
        # Add sidebar to main layout (25%)
        main_layout.addWidget(sidebar, 25)
        
        # Status Bar
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet(f"color: {COLOR_TEXT_DIM}; background-color: {COLOR_PANEL_BG}; font-size: 11px;")
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("SYSTEM INITIALIZED. STANDBY MOOE.")

    def update_view(self, qt_image, ear, threshold, status, is_drowsy=False, fps=0):
        """
        Cập nhật giao diện với frame và thông số mới
        """
        # 1. UPDATE VIDEO FEED
        if qt_image is not None:
            # Scale mode logic:
            # Use KeepAspectRatio to ensure the image isn't distorted.
            pixmap = QPixmap.fromImage(qt_image)
            
            # Use label dimensions but ensure we don't cause overflow
            w = self.video_label.width() - 2  # Subtract padding/border width
            h = self.video_label.height() - 2
            
            if w > 0 and h > 0:
                # Scale
                scaled_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.video_label.setPixmap(scaled_pixmap)
            
        # 2. UPDATE METRICS
        self.val_ear.setText(f"{ear:.3f}")
        self.val_thresh.setText(f"{threshold:.3f}")
        self.val_fps.setText(f"{int(fps)}")
        # Assuming MAR is not passed in checking args, if it is passed, add it.
        # The calling signature is: update_view(self, qt_image, ear, threshold, status, is_drowsy, fps)
        # It seems 'mar' is missing from the list. If main.py sends it or calculates it, we need it.
        # For now, leaving MAR as placeholder or extracting from somewhere if possible.
        # Actually in main.py call is: self.window.update_view(qt_image, ear, threshold, status, is_drowsy, self.fps)
        self.val_mar.setText("N/A") 

        # 3. UPDATE STATUS TEXT (Learning vs Running)
        self.status_display.setText(status.upper())
        if "HỌC" in status.upper() or "LEARNING" in status.upper():
             self.status_display.setStyleSheet(f"color: {COLOR_CYAN}; background-color: {COLOR_PANEL_BG}; border: 1px dashed {COLOR_CYAN};")
        else:
             self.status_display.setStyleSheet(f"color: #fff; background-color: #2e8b57; border: 1px solid #2ecc71;")

        # 4. UPDATE ALERT BOX
        if is_drowsy:
            # CRITICAL STATE (Sci-Fi Red Glass)
            self.alert_box.setStyleSheet(f"""
                background-color: rgba(255, 0, 60, 0.25);
                border: 2px solid {COLOR_RED};
                border-radius: 6px;
            """)
            self.lbl_alert_text.setText(">> DANGER DETECTED <<")
            self.lbl_alert_text.setStyleSheet(f"border: none; color: {COLOR_RED}; letter-spacing: 2px;")
            
            # Visual feedback on video border
            self.video_label.setStyleSheet(f"border: 4px solid {COLOR_RED}; background-color: #000;")
            
        else:
            # NORMAL STATE (Sci-Fi Green Glass)
            self.alert_box.setStyleSheet(f"""
                background-color: rgba(31, 204, 126, 0.1);
                border: 2px solid {COLOR_GREEN};
                border-radius: 6px;
            """)
            self.lbl_alert_text.setText("[ DRIVER ACTIVE ]")
            self.lbl_alert_text.setStyleSheet(f"border: none; color: {COLOR_GREEN}; letter-spacing: 2px;")
            
            # Reset video border
            self.video_label.setStyleSheet(f"border: 1px solid {COLOR_CYAN}; background-color: #000;")
            
    def set_buttons_state(self, started):
        """
        Đặt trạng thái các nút
        """
        self.start_button.setEnabled(not started)
        self.stop_button.setEnabled(started)

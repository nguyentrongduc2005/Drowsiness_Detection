"""
UI Module: User interface design for drowsiness detection application
Style: Military Dashboard / Sci-Fi HUD - Optimized Version
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QGroupBox, QStatusBar, QFrame,
                             QSizePolicy, QGridLayout, QScrollArea, QMessageBox,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor, QLinearGradient, QPainter

# --- Cyberpunk / Military Palette (Optimized) ---
COLORS = {
    'bg_main': "#050508",
    'bg_panel': "#0c0c10", 
    'bg_card': "#12121a",
    'cyan': "#00e5ff",
    'cyan_dim': "#00a0b0",
    'red': "#ff1744",
    'red_dim': "#b71c1c",
    'green': "#00e676",
    'green_dim': "#1b5e20",
    'yellow': "#ffea00",
    'orange': "#ff6d00",
    'purple': "#d500f9",
    'text_primary': "#e0e0e0",
    'text_dim': "#6b7280",
    'border': "#1e1e2e",
    'border_accent': "#2a2a3e",
}

FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"


class GlowFrame(QFrame):
    """Frame with glow effect"""
    def __init__(self, color=COLORS['cyan'], parent=None):
        super().__init__(parent)
        self.glow_color = color
        self._setup_glow()
    
    def _setup_glow(self):
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(15)
        effect.setColor(QColor(self.glow_color))
        effect.setOffset(0, 0)
        self.setGraphicsEffect(effect)


class MainWindow(QMainWindow):
    """Main application window (Optimized HUD Style)"""
    
    def __init__(self):
        super().__init__()
        self._init_styles()
        self._init_ui()
        
    def _init_styles(self):
        """Initialize global styles"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['bg_main']}, stop:1 #0a0a12);
            }}
            QWidget {{
                font-family: '{FONT_MAIN}';
                color: {COLORS['text_primary']};
            }}
            QGroupBox {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 16px;
                padding: 12px 8px 8px 8px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['cyan']}, stop:1 {COLORS['cyan_dim']});
                color: #000;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9px;
            }}
            QLabel {{ border: none; }}
            QScrollBar:vertical {{
                background: {COLORS['bg_panel']};
                width: 6px;
                border-radius: 3px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['cyan_dim']};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['cyan']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
    def _init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("SENTINEL :: DROWSINESS DETECTION SYSTEM")
        self.setMinimumSize(1280, 800)
        self.resize(1400, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # === LEFT: VIDEO PANEL ===
        self._create_video_panel(main_layout)
        
        # === RIGHT: CONTROL SIDEBAR ===
        self._create_sidebar(main_layout)
        
        # === STATUS BAR ===
        self._create_status_bar()

    def _create_video_panel(self, parent_layout):
        """Create video display panel"""
        video_frame = QFrame()
        video_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['bg_card']}, stop:1 {COLORS['bg_panel']});
                border: 2px solid {COLORS['border_accent']};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(video_frame)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header = QLabel("◉ LIVE FEED")
        header.setFont(QFont(FONT_MONO, 10, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['cyan']}; padding: 4px;")
        layout.addWidget(header)
        
        # Video label
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setStyleSheet(f"""
            background: #000;
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            color: {COLORS['text_dim']};
            font-size: 14px;
        """)
        self.video_label.setText("⏳ AWAITING CAMERA INPUT...")
        layout.addWidget(self.video_label)
        
        parent_layout.addWidget(video_frame, 70)
        self.video_container = video_frame

    def _create_sidebar(self, parent_layout):
        """Create control sidebar with dynamic sizing"""
        sidebar = QFrame()
        sidebar.setMinimumWidth(320)
        sidebar.setMaximumWidth(400)
        sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sidebar.setStyleSheet(f"background: transparent;")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(8)
        
        # Header
        self._create_header(layout)
        
        # Fatigue Status - CHỈ SỐ QUAN TRỌNG NHẤT
        self._create_fatigue_panel(layout)
        
        # Alert Box - TRẠNG THÁI HIỆN TẠI
        self._create_alert_box(layout)
        
        # Controls - CÁC NÚT ĐIỀU KHIỂN
        self._create_controls(layout)
        
        # Calibration Info
        self._create_calibration_info(layout)
        
        # Spacer at bottom
        layout.addStretch(1)
        
        scroll.setWidget(content)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll)
        
        parent_layout.addWidget(sidebar)

    def _create_header(self, parent):
        """Create header section"""
        header = QLabel("◈ DRIVER MONITOR")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont(FONT_MONO, 12, QFont.Bold))
        header.setMinimumHeight(32)
        header.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        header.setStyleSheet(f"""
            color: {COLORS['cyan']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.5 {COLORS['bg_card']}, stop:1 transparent);
            border-bottom: 2px solid {COLORS['cyan']};
            padding: 6px;
            letter-spacing: 2px;
        """)
        parent.addWidget(header)

    def _create_metrics_panel(self, parent):
        """Create telemetry metrics panel"""
        group = QGroupBox("TELEMETRY")
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(8, 20, 8, 8)
        
        metrics = [
            ("EAR", COLORS['cyan']),
            ("MAR", COLORS['purple']),
            ("FPS", COLORS['green']),
            ("THR", COLORS['yellow'])
        ]
        
        self.val_ear = self._create_metric_widget(grid, 0, 0, metrics[0])
        self.val_mar = self._create_metric_widget(grid, 0, 1, metrics[1])
        self.val_fps = self._create_metric_widget(grid, 1, 0, metrics[2])
        self.val_thresh = self._create_metric_widget(grid, 1, 1, metrics[3])
        
        group.setLayout(grid)
        parent.addWidget(group)
    
    def _create_metric_widget(self, grid, row, col, metric_info):
        """Create individual metric widget"""
        name, color = metric_info
        
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_panel']};
                border: 1px solid {color}40;
                border-radius: 6px;
                padding: 4px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        
        lbl = QLabel(name)
        lbl.setFont(QFont(FONT_MONO, 9))
        lbl.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
        
        val = QLabel("0.00")
        val.setFont(QFont(FONT_MONO, 18, QFont.Bold))
        val.setStyleSheet(f"color: {color}; border: none;")
        val.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(lbl)
        layout.addWidget(val)
        
        grid.addWidget(widget, row, col)
        return val

    def _create_fatigue_panel(self, parent):
        """Create fatigue status panel"""
        group = QGroupBox("FATIGUE STATUS")
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(8, 20, 8, 6)
        
        # State label
        self.fatigue_state_label = QLabel("NORMAL")
        self.fatigue_state_label.setAlignment(Qt.AlignCenter)
        self.fatigue_state_label.setFont(QFont(FONT_MONO, 12, QFont.Bold))
        self.fatigue_state_label.setMinimumHeight(28)
        self.fatigue_state_label.setStyleSheet(f"""
            color: {COLORS['green']};
            background: rgba(0, 230, 118, 0.1);
            border: 2px solid {COLORS['green']};
            border-radius: 6px;
            padding: 4px;
        """)
        layout.addWidget(self.fatigue_state_label)
        
        # Score bar container
        score_container = QWidget()
        score_layout = QHBoxLayout(score_container)
        score_layout.setContentsMargins(0, 4, 0, 4)
        score_layout.setSpacing(8)
        
        lbl = QLabel("SCORE")
        lbl.setFont(QFont(FONT_MONO, 9))
        lbl.setStyleSheet(f"color: {COLORS['text_dim']};")
        lbl.setFixedWidth(45)
        
        self.fatigue_score_bar = QFrame()
        self.fatigue_score_bar.setFixedHeight(16)
        self.fatigue_score_bar.setStyleSheet(f"""
            background: {COLORS['bg_panel']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
        """)
        
        self.fatigue_score_fill = QFrame(self.fatigue_score_bar)
        self.fatigue_score_fill.setGeometry(0, 0, 0, 16)
        self.fatigue_score_fill.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['green']}, stop:1 {COLORS['cyan']});
            border-radius: 8px;
        """)
        
        self.fatigue_score_text = QLabel("0%")
        self.fatigue_score_text.setFont(QFont(FONT_MONO, 11, QFont.Bold))
        self.fatigue_score_text.setStyleSheet(f"color: {COLORS['green']};")
        self.fatigue_score_text.setFixedWidth(40)
        self.fatigue_score_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        score_layout.addWidget(lbl)
        score_layout.addWidget(self.fatigue_score_bar, 1)
        score_layout.addWidget(self.fatigue_score_text)
        layout.addWidget(score_container)
        
        # Session info - thêm Yawns
        self.session_info = QLabel("Session: 00:00 | Yawns: 0 | Blinks: 0/min")
        self.session_info.setFont(QFont(FONT_MONO, 9))
        self.session_info.setStyleSheet(f"color: {COLORS['text_dim']};")
        self.session_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.session_info)
        
        group.setLayout(layout)
        parent.addWidget(group)

    def _create_sleep_panel(self, parent):
        """Create sleep detection panel"""
        group = QGroupBox("SLEEP DETECTION")
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(8, 20, 8, 6)
        
        # Status
        self.sleep_status_label = QLabel("● NO EVENTS")
        self.sleep_status_label.setFont(QFont(FONT_MONO, 11, QFont.Bold))
        self.sleep_status_label.setStyleSheet(f"color: {COLORS['green']};")
        layout.addWidget(self.sleep_status_label)
        
        # Stats row
        stats_row = QWidget()
        stats_layout = QHBoxLayout(stats_row)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(4)
        
        self.sleep_stats_label = QLabel("Events: 0 | Total: 0.0s")
        self.sleep_stats_label.setFont(QFont(FONT_MONO, 9))
        self.sleep_stats_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        
        self.sleep_risk_label = QLabel("LOW")
        self.sleep_risk_label.setFont(QFont(FONT_MONO, 10, QFont.Bold))
        self.sleep_risk_label.setStyleSheet(f"color: {COLORS['green']};")
        
        self.sleep_trend_label = QLabel("↔")
        self.sleep_trend_label.setFont(QFont(FONT_MONO, 10))
        self.sleep_trend_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        
        stats_layout.addWidget(self.sleep_stats_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.sleep_risk_label)
        stats_layout.addWidget(self.sleep_trend_label)
        
        layout.addWidget(stats_row)
        
        group.setLayout(layout)
        parent.addWidget(group)

    def _create_alert_box(self, parent):
        """Create alert display box"""
        self.alert_box = QFrame()
        self.alert_box.setMinimumHeight(40)
        self.alert_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.alert_box.setStyleSheet(f"""
            background: rgba(0, 230, 118, 0.1);
            border: 2px solid {COLORS['green']};
            border-radius: 8px;
        """)
        
        layout = QVBoxLayout(self.alert_box)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_alert_text = QLabel("✓ DRIVER ACTIVE")
        self.lbl_alert_text.setAlignment(Qt.AlignCenter)
        self.lbl_alert_text.setFont(QFont(FONT_MONO, 14, QFont.Bold))
        self.lbl_alert_text.setStyleSheet(f"color: {COLORS['green']}; border: none;")
        layout.addWidget(self.lbl_alert_text)
        
        # System status
        self.status_display = QLabel("STANDBY")
        self.status_display.setAlignment(Qt.AlignCenter)
        self.status_display.setFont(QFont(FONT_MONO, 9))
        self.status_display.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
        layout.addWidget(self.status_display)
        
        parent.addWidget(self.alert_box)

    def _create_controls(self, parent):
        """Create control buttons"""
        group = QGroupBox("CONTROLS")
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setContentsMargins(8, 20, 8, 8)
        
        def make_btn_style(color):
            return f"""
                QPushButton {{
                    background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1);
                    border: 2px solid {color};
                    color: {color};
                    border-radius: 6px;
                    font-family: '{FONT_MONO}';
                    font-size: 10px;
                    font-weight: bold;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background: {color};
                    color: #000;
                }}
                QPushButton:pressed {{
                    background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.8);
                    color: #000;
                }}
                QPushButton:disabled {{
                    border-color: {COLORS['border']};
                    color: {COLORS['text_dim']};
                    background: {COLORS['bg_panel']};
                }}
            """
        
        self.start_button = QPushButton("▶ START")
        self.start_button.setMinimumHeight(32)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setStyleSheet(make_btn_style(COLORS['cyan']))
        
        self.stop_button = QPushButton("■ STOP")
        self.stop_button.setMinimumHeight(32)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setStyleSheet(make_btn_style(COLORS['red']))
        self.stop_button.setEnabled(False)
        
        self.calibrate_button = QPushButton("⚙ CALIBRATE")
        self.calibrate_button.setMinimumHeight(32)
        self.calibrate_button.setCursor(Qt.PointingHandCursor)
        self.calibrate_button.setStyleSheet(make_btn_style(COLORS['purple']))
        
        self.reset_button = QPushButton("↻ RESET")
        self.reset_button.setMinimumHeight(32)
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.setStyleSheet(make_btn_style(COLORS['orange']))
        
        grid.addWidget(self.start_button, 0, 0)
        grid.addWidget(self.stop_button, 0, 1)
        grid.addWidget(self.calibrate_button, 1, 0)
        grid.addWidget(self.reset_button, 1, 1)
        
        group.setLayout(grid)
        parent.addWidget(group)

    def _create_calibration_info(self, parent):
        """Create calibration info label"""
        self.calibration_info_label = QLabel("⚠ Not calibrated - Press CALIBRATE")
        self.calibration_info_label.setFont(QFont(FONT_MONO, 9))
        self.calibration_info_label.setStyleSheet(f"""
            color: {COLORS['yellow']};
            background: {COLORS['yellow']}10;
            border: 1px solid {COLORS['yellow']}40;
            border-radius: 6px;
            padding: 8px;
        """)
        self.calibration_info_label.setAlignment(Qt.AlignCenter)
        self.calibration_info_label.setWordWrap(True)
        parent.addWidget(self.calibration_info_label)

    def _create_status_bar(self):
        """Create status bar"""
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet(f"""
            QStatusBar {{
                color: {COLORS['text_dim']};
                background: {COLORS['bg_panel']};
                border-top: 1px solid {COLORS['border']};
                font-family: '{FONT_MONO}';
                font-size: 10px;
                padding: 4px;
            }}
        """)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("◉ SYSTEM READY")

    # =========================================================================
    # UPDATE METHODS
    # =========================================================================
    
    def update_view(self, qt_image, ear, mar, threshold, status, is_drowsy=False, fps=0, 
                    fatigue_state=None, fatigue_score=0, blink_rate=0, session_duration=0,
                    sleep_info=None):
        """Update user interface"""
        # Video
        if qt_image is not None:
            pixmap = QPixmap.fromImage(qt_image)
            w, h = self.video_label.width() - 4, self.video_label.height() - 4
            if w > 0 and h > 0:
                self.video_label.setPixmap(
                    pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # Status display
        status_upper = status.upper()
        self.status_display.setText(status_upper)
        if "LEARNING" in status_upper:
            self.status_display.setStyleSheet(f"color: {COLORS['cyan']}; border: none;")
        else:
            self.status_display.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
        
        # Fatigue display (bao gồm yawn count)
        yawn_count = 0
        if sleep_info:
            yawn_count = sleep_info.get('yawn_count', 0)
        self._update_fatigue_display(fatigue_state, fatigue_score, blink_rate, session_duration, yawn_count)
        
        # Alert state
        self._update_alert_state(fatigue_state, is_drowsy, sleep_info)
    
    def _update_alert_state(self, fatigue_state, is_drowsy, sleep_info):
        """Update alert box based on state - CHỈ hiển thị NORMAL hoặc cảnh báo NGỦ"""
        is_sleeping = sleep_info.get('is_sleeping', False) if sleep_info else False
        alert_msg = sleep_info.get('sleep_alert_message', '') if sleep_info else ''
        
        if is_sleeping or fatigue_state == "CRITICAL":
            msg = alert_msg if is_sleeping and alert_msg else "⚠ CRITICAL - STOP NOW"
            self._set_alert_style(COLORS['red'], msg, pulse=True)
        elif fatigue_state == "DROWSY" or is_drowsy:
            self._set_alert_style(COLORS['orange'], "⚡ DROWSY DETECTED")
        # BỎ TIRED - chỉ hiển thị cảnh báo ngủ hoặc bình thường
        # TIRED sẽ được thông báo trên màn hình video
        else:
            self._set_alert_style(COLORS['green'], "✓ DRIVER ACTIVE")
    
    def _set_alert_style(self, color, text, pulse=False):
        """Set alert box style"""
        border_width = 3 if pulse else 2
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        self.alert_box.setStyleSheet(f"""
            background: rgba({r}, {g}, {b}, 0.1);
            border: {border_width}px solid {color};
            border-radius: 8px;
        """)
        self.lbl_alert_text.setText(text)
        self.lbl_alert_text.setStyleSheet(f"color: {color}; border: none;")
        
        # Update video border
        self.video_label.setStyleSheet(f"""
            background: #000;
            border: {border_width}px solid {color};
            border-radius: 8px;
        """)
    
    def _update_fatigue_display(self, state, score, blink_rate, session_duration, yawn_count=0):
        """Update FatigueState display - Sidebar chỉ hiển thị NORMAL hoặc warnings"""
        state = state or "NORMAL"
        
        # Map TIRED về NORMAL cho sidebar (TIRED sẽ hiện trên video)
        if state == "TIRED":
            state = "NORMAL"
        
        colors = {"ALERT": COLORS['green'], "NORMAL": COLORS['green'],
                  "DROWSY": COLORS['orange'], "CRITICAL": COLORS['red']}
        color = colors.get(state, COLORS['green'])
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        
        self.fatigue_state_label.setText(state)
        self.fatigue_state_label.setStyleSheet(f"""
            color: {color};
            background: rgba({r}, {g}, {b}, 0.1);
            border: 2px solid {color};
            border-radius: 6px;
            padding: 4px;
        """)
        
        # Score bar
        bar_width = max(0, int((score / 100) * self.fatigue_score_bar.width()))
        self.fatigue_score_fill.setGeometry(0, 0, bar_width, 16)
        
        # Gradient based on score
        if score < 30:
            gradient = f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {COLORS['green']},stop:1 {COLORS['cyan']})"
        elif score < 60:
            gradient = f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {COLORS['yellow']},stop:1 {COLORS['orange']})"
        else:
            gradient = f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {COLORS['orange']},stop:1 {COLORS['red']})"
        
        self.fatigue_score_fill.setStyleSheet(f"background: {gradient}; border-radius: 8px;")
        self.fatigue_score_text.setText(f"{int(score)}%")
        self.fatigue_score_text.setStyleSheet(f"color: {color};")
        
        # Session info - bao gồm Yawns
        mins, secs = int(session_duration // 60), int(session_duration % 60)
        self.session_info.setText(f"Session: {mins:02d}:{secs:02d} | Yawns: {yawn_count} | Blinks: {blink_rate:.0f}/min")
    
    def set_buttons_state(self, started):
        """Set buttons enabled state"""
        self.start_button.setEnabled(not started)
        self.stop_button.setEnabled(started)

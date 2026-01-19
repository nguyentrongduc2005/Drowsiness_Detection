"""
Giao diện chính của ứng dụng phát hiện buồn ngủ
Thiết kế hiện đại với PyQt5 - Premium Glass Morphism Dark Theme
"""
# pylint: disable=no-name-in-module
# pyright: reportMissingModuleSource=false

from PyQt5.QtWidgets import (  # type: ignore
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QStatusBar,
    QProgressBar, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt  # type: ignore
from PyQt5.QtGui import QPixmap, QFont, QColor  # type: ignore


# ============= THEME COLORS =============
class Theme:
    """Centralized theme colors"""
    # Backgrounds
    BG_DARK = "#0A0A0C"
    BG_CARD = "#16161A"
    BG_CARD_HOVER = "#1E1E24"
    BG_ACCENT = "#1A1A20"
    
    # Borders
    BORDER_SUBTLE = "#2A2A30"
    BORDER_GLOW = "#3A3A42"
    
    # Text
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#9CA3AF"
    TEXT_MUTED = "#6B7280"
    
    # Accent colors
    CYAN = "#06B6D4"
    GREEN = "#10B981"
    AMBER = "#F59E0B"
    RED = "#EF4444"
    PURPLE = "#8B5CF6"
    BLUE = "#3B82F6"
    
    # Glass effect
    GLASS_BG = "rgba(22, 22, 26, 0.85)"
    GLASS_BORDER = "rgba(255, 255, 255, 0.08)"


class GlowingCard(QFrame):
    """Card với hiệu ứng glass morphism và glow"""
    
    def __init__(self, title="", value="--", icon="", accent_color="#06B6D4", parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self._hover = False
        
        # Responsive sizing
        self.setMinimumHeight(80)
        self.setMaximumHeight(95)
        self.setMinimumWidth(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self._update_style(False)
        
        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        
        # Header với icon và title
        header = QHBoxLayout()
        header.setSpacing(6)
        
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 11))
        self.icon_label.setStyleSheet("background: transparent;")
        
        self.title_label = QLabel(title.upper())
        self.title_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: transparent; letter-spacing: 1px;")
        
        header.addWidget(self.icon_label)
        header.addWidget(self.title_label)
        header.addStretch()
        
        # Giá trị với font lớn
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {accent_color}; background: transparent;")
        
        layout.addLayout(header)
        layout.addStretch()
        layout.addWidget(self.value_label)
    
    def _update_style(self, hover):
        border_color = self.accent_color if hover else Theme.BORDER_SUBTLE
        bg_color = Theme.BG_CARD_HOVER if hover else Theme.BG_CARD
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_color}, stop:1 {Theme.BG_DARK});
                border-radius: 14px;
                border: 1px solid {border_color};
            }}
        """)
    
    def enterEvent(self, event):
        self._update_style(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._update_style(False)
        super().leaveEvent(event)
    
    def set_value(self, value, color=None):
        """Cập nhật giá trị"""
        self.value_label.setText(str(value))
        if color:
            self.value_label.setStyleSheet(f"color: {color}; background: transparent;")


class CircularIndicator(QFrame):
    """Indicator tròn với hiệu ứng pulse"""
    
    def __init__(self, label_text="Status", size=42, parent=None):
        super().__init__(parent)
        self._size = size
        self.setMinimumSize(size + 35, size + 28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._active = False
        self._warning = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignCenter)
        
        # Circle indicator với border gradient
        self.circle = QLabel()
        self.circle.setFixedSize(size, size)
        self.circle.setAlignment(Qt.AlignCenter)
        
        # Label (phải tạo trước khi gọi _update_style)
        self.label = QLabel(label_text)
        self.label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: transparent;")
        self.label.setAlignment(Qt.AlignCenter)
        
        # Cập nhật style sau khi tạo widgets
        self._update_style()
        
        layout.addWidget(self.circle, 0, Qt.AlignCenter)
        layout.addWidget(self.label, 0, Qt.AlignCenter)
    
    def _update_style(self):
        radius = self._size // 2
        if self._warning:
            self.circle.setStyleSheet(f"""
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.3, stop:0 {Theme.RED}, stop:0.7 #DC2626, stop:1 #B91C1C);
                border-radius: {radius}px;
                border: 3px solid #FCA5A5;
            """)
            self.circle.setText("⚠")
            self.label.setStyleSheet(f"color: {Theme.RED}; background: transparent;")
        elif self._active:
            self.circle.setStyleSheet(f"""
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.3, stop:0 {Theme.GREEN}, stop:0.7 #059669, stop:1 #047857);
                border-radius: {radius}px;
                border: 3px solid #6EE7B7;
            """)
            self.circle.setText("✓")
            self.label.setStyleSheet(f"color: {Theme.GREEN}; background: transparent;")
        else:
            self.circle.setStyleSheet(f"""
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.3, stop:0 #374151, stop:1 #1F2937);
                border-radius: {radius}px;
                border: 3px solid {Theme.BORDER_SUBTLE};
            """)
            self.circle.setText("")
            self.label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: transparent;")
        
        self.circle.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.circle.setStyleSheet(self.circle.styleSheet() + "color: white;")
        self.circle.setAlignment(Qt.AlignCenter)
    
    def set_status(self, active=False, warning=False):
        self._active = active
        self._warning = warning
        self._update_style()


class GradientButton(QPushButton):
    """Nút với gradient, hover effect và icon"""
    
    def __init__(self, text, button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setMinimumHeight(44)
        self.setMaximumHeight(52)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()
    
    def _apply_style(self):
        styles = {
            "primary": f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Theme.CYAN}, stop:1 {Theme.BLUE});
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #22D3EE, stop:1 #60A5FA);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #0891B2, stop:1 #2563EB);
                }}
                QPushButton:disabled {{
                    background: {Theme.BG_ACCENT};
                    color: {Theme.TEXT_MUTED};
                }}
            """,
            "success": f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Theme.GREEN}, stop:1 #059669);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #34D399, stop:1 #10B981);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #047857, stop:1 #065F46);
                }}
                QPushButton:disabled {{
                    background: {Theme.BG_ACCENT};
                    color: {Theme.TEXT_MUTED};
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Theme.RED}, stop:1 #DC2626);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #F87171, stop:1 #EF4444);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #B91C1C, stop:1 #991B1B);
                }}
                QPushButton:disabled {{
                    background: {Theme.BG_ACCENT};
                    color: {Theme.TEXT_MUTED};
                }}
            """,
            "warning": f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Theme.AMBER}, stop:1 #D97706);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FBBF24, stop:1 #F59E0B);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #B45309, stop:1 #92400E);
                }}
                QPushButton:disabled {{
                    background: {Theme.BG_ACCENT};
                    color: {Theme.TEXT_MUTED};
                }}
            """
        }
        self.setStyleSheet(styles.get(self.button_type, styles["primary"]))


class CalibrationWidget(QFrame):
    """Widget hiển thị tiến trình calibration - Thiết kế modern"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(135)
        self.setMaximumHeight(165)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Theme.BG_CARD}, stop:1 {Theme.BG_DARK});
                border-radius: 16px;
                border: 1px solid {Theme.BORDER_SUBTLE};
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        
        # Header với icon và step name
        header = QHBoxLayout()
        header.setSpacing(8)
        
        self.icon = QLabel("🎯")
        self.icon.setFont(QFont("Segoe UI Emoji", 18))
        self.icon.setStyleSheet("background: transparent;")
        
        title_container = QVBoxLayout()
        title_container.setSpacing(0)
        
        self.step_label = QLabel("CALIBRATION")
        self.step_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.step_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        
        self.sub_label = QLabel("Hệ thống hiệu chỉnh")
        self.sub_label.setFont(QFont("Segoe UI", 8))
        self.sub_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: transparent;")
        
        title_container.addWidget(self.step_label)
        title_container.addWidget(self.sub_label)
        
        header.addWidget(self.icon)
        header.addLayout(title_container)
        header.addStretch()
        
        # Step indicators (3 bước) - nằm ngang
        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(6)
        
        self.step_dots = []
        step_labels = ["1", "2", "✓"]
        for label in step_labels:
            dot = QLabel(label)
            dot.setFixedSize(26, 26)
            dot.setAlignment(Qt.AlignCenter)
            dot.setFont(QFont("Segoe UI", 9, QFont.Bold))
            dot.setStyleSheet(f"""
                background: {Theme.BG_ACCENT};
                color: {Theme.TEXT_MUTED};
                border-radius: 13px;
            """)
            self.step_dots.append(dot)
            steps_layout.addWidget(dot)
        
        steps_layout.addStretch()
        header.addLayout(steps_layout)
        
        # Instruction text (hướng dẫn)
        self.instruction_label = QLabel("Nhấn 'Bắt đầu' để khởi động")
        self.instruction_label.setFont(QFont("Segoe UI", 10))
        self.instruction_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; background: transparent;")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setWordWrap(True)
        
        # Progress bar container
        progress_container = QHBoxLayout()
        progress_container.setSpacing(10)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self._set_progress_style("orange")
        
        # Progress text
        self.progress_text = QLabel("0%")
        self.progress_text.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.progress_text.setStyleSheet(f"color: {Theme.AMBER}; background: transparent;")
        self.progress_text.setFixedWidth(40)
        self.progress_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        progress_container.addWidget(self.progress)
        progress_container.addWidget(self.progress_text)
        
        layout.addLayout(header)
        layout.addWidget(self.instruction_label)
        layout.addStretch()
        layout.addLayout(progress_container)
    
    def _set_progress_style(self, color_type):
        """Đặt style cho progress bar"""
        colors = {
            "green": (Theme.GREEN, "#059669"),
            "blue": (Theme.CYAN, Theme.BLUE),
            "red": (Theme.RED, "#DC2626"),
            "orange": (Theme.AMBER, "#D97706")
        }
        c1, c2 = colors.get(color_type, colors["orange"])
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {Theme.BG_ACCENT};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c1}, stop:1 {c2});
                border-radius: 4px;
            }}
        """)
    
    def _update_step_dots(self, current_step):
        """Cập nhật trạng thái các step dots"""
        for i, dot in enumerate(self.step_dots):
            step_num = i + 1
            if step_num < current_step:
                # Completed step
                dot.setStyleSheet(f"""
                    background: {Theme.GREEN};
                    color: white;
                    border-radius: 13px;
                """)
            elif step_num == current_step:
                # Current step
                dot.setStyleSheet(f"""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {Theme.AMBER}, stop:1 #D97706);
                    color: white;
                    border-radius: 13px;
                """)
            else:
                # Future step
                dot.setStyleSheet(f"""
                    background: {Theme.BG_ACCENT};
                    color: {Theme.TEXT_MUTED};
                    border-radius: 13px;
                """)
    
    def update_step(self, step_info):
        """
        Cập nhật widget với thông tin step
        
        Args:
            step_info: dict với keys: step, step_name, instruction, progress, is_complete, is_paused, warning
        """
        step = step_info.get('step', 0)
        step_name = step_info.get('step_name', '')
        instruction = step_info.get('instruction', '')
        progress = step_info.get('progress', 0)
        is_complete = step_info.get('is_complete', False)
        is_paused = step_info.get('is_paused', False)
        warning = step_info.get('warning', '')
        
        # Cập nhật step label và icon
        self.step_label.setText(step_name.upper())
        
        # Cập nhật step dots
        self._update_step_dots(step)
        
        # Cập nhật instruction
        self.instruction_label.setText(instruction)
        
        # Cập nhật progress
        self.progress.setValue(progress)
        self.progress_text.setText(f"{progress}%")
        
        # Xử lý trạng thái tạm dừng (warning)
        if is_paused and warning:
            self.icon.setText("⚠️")
            self.instruction_label.setStyleSheet(f"color: {Theme.RED}; background: transparent; font-weight: bold;")
            self.progress_text.setStyleSheet(f"color: {Theme.RED}; background: transparent;")
            self._set_progress_style("red")
            # Highlight current step dot với màu đỏ
            if step > 0 and step <= len(self.step_dots):
                self.step_dots[step - 1].setStyleSheet(f"""
                    background: {Theme.RED};
                    color: white;
                    border-radius: 13px;
                """)
        elif is_complete:
            self.icon.setText("✅")
            self.instruction_label.setStyleSheet(f"color: {Theme.GREEN}; background: transparent; font-weight: bold;")
            self.progress_text.setStyleSheet(f"color: {Theme.GREEN}; background: transparent;")
            self._set_progress_style("green")
            # Mark all dots as complete
            for dot in self.step_dots:
                dot.setStyleSheet(f"""
                    background: {Theme.GREEN};
                    color: white;
                    border-radius: 13px;
                """)
        elif step == 1:
            self.icon.setText("👤")
            self.instruction_label.setStyleSheet(f"color: {Theme.CYAN}; background: transparent;")
            self.progress_text.setStyleSheet(f"color: {Theme.CYAN}; background: transparent;")
            self._set_progress_style("blue")
        elif step == 2:
            self.icon.setText("👁")
            self.instruction_label.setStyleSheet(f"color: {Theme.AMBER}; background: transparent;")
            self.progress_text.setStyleSheet(f"color: {Theme.AMBER}; background: transparent;")
            self._set_progress_style("orange")
        else:
            self.icon.setText("🎯")
            self.instruction_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; background: transparent;")
    
    def reset(self):
        """Reset về trạng thái ban đầu"""
        self.progress.setValue(0)
        self.icon.setText("🎯")
        self.step_label.setText("CALIBRATION")
        self.sub_label.setText("Hệ thống hiệu chỉnh")
        self.instruction_label.setText("Nhấn 'Bắt đầu' để khởi động")
        self.instruction_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; background: transparent;")
        self.progress_text.setText("0%")
        self.progress_text.setStyleSheet(f"color: {Theme.AMBER}; background: transparent;")
        self._set_progress_style("orange")
        # Reset step dots
        for dot in self.step_dots:
            dot.setStyleSheet(f"""
                background: {Theme.BG_ACCENT};
                color: {Theme.TEXT_MUTED};
                border-radius: 13px;
            """)


class MainWindow(QMainWindow):
    """Cửa sổ chính với thiết kế Glass Morphism Premium"""
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
    
    def _setup_window(self):
        """Thiết lập cửa sổ"""
        self.setWindowTitle("🚗 Driver Drowsiness Detection System")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)
        
        # Ultra dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Theme.BG_DARK};
            }}
            QWidget {{
                background-color: transparent;
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
    
    def _create_widgets(self):
        """Tạo các widget"""
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(f"background-color: {Theme.BG_DARK};")
        self.setCentralWidget(self.central_widget)
        
        # === HEADER ===
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.BG_CARD}, stop:0.5 {Theme.BG_ACCENT}, stop:1 {Theme.BG_CARD});
                border-radius: 16px;
                border: 1px solid {Theme.BORDER_SUBTLE};
            }}
        """)
        self.header_frame.setMaximumHeight(75)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        # Logo + Title
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        self.header_label = QLabel("🚗 Driver Drowsiness Detection")
        self.header_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.header_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        
        self.subtitle_label = QLabel("Hệ thống giám sát và cảnh báo buồn ngủ thông minh")
        self.subtitle_label.setFont(QFont("Segoe UI", 9))
        self.subtitle_label.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        
        title_container.addWidget(self.header_label)
        title_container.addWidget(self.subtitle_label)
        
        # Status badge
        self.status_badge = QLabel("● READY")
        self.status_badge.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.status_badge.setStyleSheet(f"""
            color: {Theme.GREEN};
            background: rgba(16, 185, 129, 0.15);
            padding: 6px 14px;
            border-radius: 12px;
            border: 1px solid rgba(16, 185, 129, 0.3);
        """)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        # Settings button
        self.settings_button = QPushButton("⚙️")
        self.settings_button.setFont(QFont("Segoe UI Emoji", 14))
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_ACCENT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 20px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_CARD_HOVER};
                border: 1px solid {Theme.CYAN};
            }}
        """)
        
        header_layout.addWidget(self.settings_button)
        header_layout.addWidget(self.status_badge)
        
        # === VIDEO FRAME ===
        self.video_frame = QFrame()
        self.video_frame.setMinimumSize(520, 390)
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Theme.BG_CARD}, stop:1 {Theme.BG_DARK});
                border-radius: 18px;
                border: 2px solid {Theme.BORDER_SUBTLE};
            }}
        """)
        
        # Shadow cho video frame
        video_shadow = QGraphicsDropShadowEffect()
        video_shadow.setBlurRadius(35)
        video_shadow.setColor(QColor(0, 0, 0, 80))
        video_shadow.setOffset(0, 12)
        self.video_frame.setGraphicsEffect(video_shadow)
        
        self.video_label = QLabel("📷 Nhấn 'Bắt đầu' để khởi động camera")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFont(QFont("Segoe UI", 14))
        self.video_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: transparent;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        video_layout = QVBoxLayout(self.video_frame)
        video_layout.setContentsMargins(12, 12, 12, 12)
        video_layout.addWidget(self.video_label)
        
        # === INFO CARDS ===
        self.ear_card = GlowingCard("EAR", "0.000", "👁", Theme.CYAN)
        self.threshold_card = GlowingCard("Ngưỡng", "0.000", "📊", Theme.PURPLE)
        self.fps_card = GlowingCard("FPS", "0", "⚡", Theme.GREEN)
        self.status_card = GlowingCard("Trạng thái", "Chờ", "📍", Theme.AMBER)
        
        # === INDICATORS ===
        self.camera_indicator = CircularIndicator("Camera", 38)
        self.detection_indicator = CircularIndicator("Phát hiện", 38)
        self.alert_indicator = CircularIndicator("Cảnh báo", 38)
        
        # === CALIBRATION ===
        self.calibration_widget = CalibrationWidget()
        
        # === BUTTONS ===
        self.start_button = GradientButton("▶  Bắt đầu giám sát", "success")
        self.stop_button = GradientButton("⏹  Dừng", "danger")
        self.reset_button = GradientButton("🔄  Reset Calibration", "warning")
        
        self.stop_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        
        # === STATUS BAR ===
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_SECONDARY};
                border-top: 1px solid {Theme.BORDER_SUBTLE};
                padding: 8px 18px;
                font-size: 11px;
            }}
        """)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("✅ Sẵn sàng - Nhấn 'Bắt đầu giám sát' để khởi động hệ thống")
    
    def _setup_layout(self):
        """Thiết lập layout - Cải thiện tỷ lệ và spacing"""
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(14)
        
        # === HEADER ===
        main_layout.addWidget(self.header_frame)
        
        # === CONTENT ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # -- LEFT: Video + Cards --
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        left_layout.addWidget(self.video_frame)
        
        # Cards dưới video - Grid layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)
        cards_layout.addWidget(self.ear_card)
        cards_layout.addWidget(self.threshold_card)
        cards_layout.addWidget(self.fps_card)
        cards_layout.addWidget(self.status_card)
        left_layout.addLayout(cards_layout)
        
        content_layout.addLayout(left_layout, 68)  # 68% width
        
        # -- RIGHT: Controls Panel --
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)
        
        # Indicators Frame với title
        indicators_frame = QFrame()
        indicators_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        indicators_frame.setMinimumHeight(95)
        indicators_frame.setMaximumHeight(110)
        indicators_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Theme.BG_CARD}, stop:1 {Theme.BG_DARK});
                border-radius: 14px;
                border: 1px solid {Theme.BORDER_SUBTLE};
            }}
        """)
        
        indicators_main_layout = QVBoxLayout(indicators_frame)
        indicators_main_layout.setContentsMargins(12, 8, 12, 8)
        indicators_main_layout.setSpacing(4)
        
        ind_title = QLabel("📡 TRẠNG THÁI HỆ THỐNG")
        ind_title.setFont(QFont("Segoe UI", 8, QFont.Bold))
        ind_title.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: transparent; letter-spacing: 1px;")
        
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(5)
        indicators_layout.addWidget(self.camera_indicator)
        indicators_layout.addWidget(self.detection_indicator)
        indicators_layout.addWidget(self.alert_indicator)
        
        indicators_main_layout.addWidget(ind_title)
        indicators_main_layout.addLayout(indicators_layout)
        
        right_layout.addWidget(indicators_frame)
        
        # Calibration
        right_layout.addWidget(self.calibration_widget)
        
        # Buttons Frame
        buttons_frame = QFrame()
        buttons_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        buttons_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Theme.BG_CARD}, stop:1 {Theme.BG_DARK});
                border-radius: 14px;
                border: 1px solid {Theme.BORDER_SUBTLE};
            }}
        """)
        
        buttons_layout = QVBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(14, 12, 14, 14)
        buttons_layout.setSpacing(10)
        
        # Title
        btn_title = QLabel("🎮 ĐIỀU KHIỂN")
        btn_title.setFont(QFont("Segoe UI", 8, QFont.Bold))
        btn_title.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: transparent; letter-spacing: 1px;")
        buttons_layout.addWidget(btn_title)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.reset_button)
        
        right_layout.addWidget(buttons_frame)
        
        # Quick Tips Frame
        tips_frame = QFrame()
        tips_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tips_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Theme.BG_CARD}, stop:1 {Theme.BG_DARK});
                border-radius: 14px;
                border: 1px solid {Theme.BORDER_SUBTLE};
            }}
        """)
        
        tips_layout = QVBoxLayout(tips_frame)
        tips_layout.setContentsMargins(14, 10, 14, 12)
        tips_layout.setSpacing(6)
        
        tips_title = QLabel("💡 HƯỚNG DẪN NHANH")
        tips_title.setFont(QFont("Segoe UI", 8, QFont.Bold))
        tips_title.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: transparent; letter-spacing: 1px;")
        
        tips_text = QLabel("""• Giữ khuôn mặt trong khung hình
• Hệ thống tự động cảnh báo
• Nhấn Reset để hiệu chỉnh lại""")
        tips_text.setFont(QFont("Segoe UI", 9))
        tips_text.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; background: transparent; line-height: 1.5;")
        tips_text.setWordWrap(True)
        
        tips_layout.addWidget(tips_title)
        tips_layout.addWidget(tips_text)
        
        right_layout.addWidget(tips_frame)
        right_layout.addStretch()
        
        content_layout.addLayout(right_layout, 32)  # 32% width
        
        main_layout.addLayout(content_layout, 1)
    
    def update_view(self, qt_image, ear, threshold, status, is_drowsy, fps, step_info=None):
        """Cập nhật giao diện
        
        Args:
            qt_image: QImage frame
            ear: EAR value
            threshold: Ngưỡng EAR
            status: Trạng thái text
            is_drowsy: Có buồn ngủ không
            fps: Frame rate
            step_info: Dict chứa thông tin bước calibration
        """
        # Video
        if qt_image is not None:
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
        
        # Cards
        ear_color = Theme.RED if is_drowsy else Theme.GREEN
        self.ear_card.set_value(f"{ear:.3f}", ear_color)
        self.threshold_card.set_value(f"{threshold:.3f}")
        self.fps_card.set_value(f"{int(fps)}")
        
        # Status badge update
        if is_drowsy:
            self.status_badge.setText("● ALERT")
            self.status_badge.setStyleSheet(f"""
                color: {Theme.RED};
                background: rgba(239, 68, 68, 0.15);
                padding: 6px 14px;
                border-radius: 12px;
                border: 1px solid rgba(239, 68, 68, 0.3);
            """)
        else:
            self.status_badge.setText("● ACTIVE")
            self.status_badge.setStyleSheet(f"""
                color: {Theme.GREEN};
                background: rgba(16, 185, 129, 0.15);
                padding: 6px 14px;
                border-radius: 12px;
                border: 1px solid rgba(16, 185, 129, 0.3);
            """)
        
        # Status card
        if step_info:
            is_paused = step_info.get('is_paused', False)
            is_complete = step_info.get('is_complete', False)
            step = step_info.get('step', 0)
            
            if is_paused:
                self.status_card.set_value("Cảnh báo!", Theme.RED)
            elif not is_complete:
                if step == 1:
                    self.status_card.set_value("Bước 1", Theme.CYAN)
                elif step == 2:
                    self.status_card.set_value("Bước 2", Theme.AMBER)
                else:
                    self.status_card.set_value("Chờ...", Theme.TEXT_MUTED)
            elif "Đang bảo vệ" in status:
                self.status_card.set_value("Bảo vệ", Theme.GREEN)
            else:
                self.status_card.set_value("---", Theme.TEXT_MUTED)
        elif "Không phát hiện" in status:
            self.status_card.set_value("Không mặt", Theme.RED)
        else:
            self.status_card.set_value("---", Theme.TEXT_MUTED)
        
        # Indicators
        self.camera_indicator.set_status(active=True)
        self.detection_indicator.set_status(active=True, warning=is_drowsy)
        self.alert_indicator.set_status(active=is_drowsy, warning=is_drowsy)
        
        # Calibration
        if step_info:
            self.calibration_widget.update_step(step_info)
    
    def set_buttons_state(self, is_running):
        """Cập nhật trạng thái nút"""
        self.is_running = is_running
        
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        self.reset_button.setEnabled(is_running)
        
        if not is_running:
            self.camera_indicator.set_status(active=False)
            self.detection_indicator.set_status(active=False)
            self.alert_indicator.set_status(active=False)
            self.video_label.setText("📷 Camera đã dừng - Nhấn 'Bắt đầu' để tiếp tục")
            self.video_label.setPixmap(QPixmap())
            self.calibration_widget.reset()
            
            # Reset status badge
            self.status_badge.setText("● READY")
            self.status_badge.setStyleSheet(f"""
                color: {Theme.GREEN};
                background: rgba(16, 185, 129, 0.15);
                padding: 6px 14px;
                border-radius: 12px;
                border: 1px solid rgba(16, 185, 129, 0.3);
            """)
    
    def closeEvent(self, event):
        """Xử lý đóng cửa sổ"""
        event.accept()

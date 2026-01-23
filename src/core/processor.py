"""
Drowsiness Detection Logic Module
Optimized for real-time driver monitoring with high accuracy and fast response
Uses multi-signal fusion: EAR, MAR, PERCLOS, Blink patterns, Head Pose
Enhanced with micro-optimizations and signal stabilization
Integrated Alert System for better warning management
"""
import numpy as np
import time
from collections import deque
from .config import Config
from .alert_system import AlertSystem, AlertType
from .analyzers import (
    DrowsinessThresholds,
    SignalStabilizer,
    PERCLOSCalculator,
    BlinkAnalyzer,
    YawnAnalyzer,
    HeadPoseAnalyzer,
    SleepDetector,
    FatigueState,
    PersonalCalibration,
    SmartThreshold,
    calculate_ear,
    calculate_mar,
    analyze_mouth_shape,
)


# ============================================================================
# MAIN DROWSINESS DETECTOR
# ============================================================================
class DrowsinessDetector:
    """
    Main drowsiness detection system with improvements:
    - TIME-BASED detection (FPS-independent)
    - Yawn vs Talking distinction
    - Head Pose detection
    - Dynamic calibration
    - Veto logic for critical events
    """
    
    def __init__(self, config=None):
        if config is None:
            config = Config()
        
        self.config = config
        self.fps = 30
        
        # MAR threshold for yawn detection
        self.mar_threshold = config.get('mouth_thresholds.mar_limit', 0.6)
        
        # TIME-BASED tracking (FPS-independent)
        self.eye_closed_start_time = None
        self.eye_closed_duration = 0.0
        self.is_drowsy = False
        self.is_yawning = False  # Đã confirm là yawn thật (hiện text YAWNING)
        self.mouth_is_open = False  # Miệng đang mở (chưa confirm, có thể đang ngáp)
        
        # Fatigue tracking
        self.drowsy_episodes = deque(maxlen=100)
        self.fatigue_window = DrowsinessThresholds.FATIGUE_WINDOW_MINUTES * 60
        self.combined_fatigue_warning = False
        
        # Low blink rate tracking (pre-warning)
        self.low_blink_start_time = None
        self.low_blink_warning = False
        
        # Calibration
        self.personal_calibration = PersonalCalibration()
        self.smart_threshold = SmartThreshold(config, self.personal_calibration)
        
        if self.personal_calibration.is_calibrated():
            thresholds = self.personal_calibration.get_thresholds()
            if thresholds.get('mar_threshold'):
                self.mar_threshold = thresholds['mar_threshold']
        
        # Analyzers
        self.sleep_detector = SleepDetector()
        self.blink_analyzer = BlinkAnalyzer(self.fps)
        self.perclos_calc = PERCLOSCalculator(self.fps)
        self.yawn_analyzer = YawnAnalyzer()
        self.head_pose_analyzer = HeadPoseAnalyzer()
        self.signal_stabilizer = SignalStabilizer(hold_frames=10)
        
        # Alert System
        self.alert_system = AlertSystem()
        
        self.fatigue_state = FatigueState.NORMAL
        self.fatigue_score = 0.0
        
        self.start_time = time.time()
        self.frame_count = 0
        
        # Smoothing buffers
        self.ear_buffer = deque(maxlen=9)
        self.mar_buffer = deque(maxlen=7)
        
        # Hysteresis for eye state
        self.eye_state = 'open'
        self.hysteresis_margin = 0.03
        
        # Stability tracking - require more frames to confirm eyes truly closed (not just blinking)
        self.stable_closed_count = 0
        self.stability_threshold = 20  # ~0.67s at 30fps - chớp mắt thường < 0.4s, cần > 0.6s mới xác nhận nhắm mắt
        
        # Store landmarks for head pose
        self.current_landmarks = None
        
        print("[OK] DrowsinessDetector initialized (v3.1 with Alert System)")
        print("  - Time-based detection ✓")
        print("  - Head Pose tracking ✓")
        print("  - Signal stabilization ✓")
        print("  - Mouth shape analysis ✓")
        print("  - Optimized distance calc ✓")
        print("  - Smart Alert System ✓")
    
    def set_landmarks(self, landmarks):
        """Store landmarks for head pose analysis"""
        self.current_landmarks = landmarks
    
    def process(self, left_eye, right_eye, mouth=None, face_detected=True, img_w=640, img_h=480) -> dict:
        """
        Process frame and detect drowsiness - ENHANCED VERSION
        
        New features:
        - Signal stabilization for lost tracking
        - Mouth shape analysis (circularity)
        - Head pose integration
        - Optimized distance calculations
        
        Args:
            left_eye, right_eye: Eye landmarks
            mouth: Mouth landmarks
            face_detected: Whether face is currently detected
            img_w, img_h: Image dimensions for head pose
            
        Returns:
            dict: Detection results with all metrics
        """
        current_time = time.time()
        self.frame_count += 1
        
        # === CALCULATE EAR/MAR with STABILIZATION ===
        left_ear = calculate_ear(left_eye) if left_eye else 0.0
        right_ear = calculate_ear(right_eye) if right_eye else 0.0
        raw_ear = (left_ear + right_ear) / 2.0 if (left_ear > 0 or right_ear > 0) else 0.0
        
        # Apply signal stabilization
        ear = self.signal_stabilizer.update_ear(raw_ear, face_detected)
        
        self.ear_buffer.append(ear)
        ear_smoothed = np.mean(list(self.ear_buffer))
        
        # MAR with mouth shape analysis
        mar = 0.0
        mouth_shape = None
        if mouth is not None:
            mouth_shape = analyze_mouth_shape(mouth)
            raw_mar = mouth_shape['mar']
            
            # Apply stabilization
            mar = self.signal_stabilizer.update_mar(raw_mar, face_detected)
            
            self.mar_buffer.append(mar)
            mar = np.mean(list(self.mar_buffer))
        
        # === YAWN DETECTION EARLY - Xử lý TRƯỚC để có is_yawning kịp thời ===
        # Cần biết đang ngáp hay không TRƯỚC KHI kiểm tra is_drowsy
        if mouth_shape and mouth_shape['shape_type'] == 'yawn':
            yawn_result = self.yawn_analyzer.update(mar, ear_smoothed, self.mar_threshold, current_time)
            yawn_result['shape_confirmed'] = True
        else:
            yawn_result = self.yawn_analyzer.update(mar, ear_smoothed, self.mar_threshold, current_time)
            yawn_result['shape_confirmed'] = False
            
            if mouth_shape and mouth_shape['shape_type'] == 'talking':
                yawn_result['is_real_yawn'] = False
                yawn_result['is_yawning'] = False
        
        self.is_yawning = yawn_result['is_real_yawn']  # Đã confirm là yawn thật (hiện text YAWNING)
        self.mouth_is_open = yawn_result['is_yawning']  # Miệng đang mở (chưa confirm)
        recent_yawns = self.yawn_analyzer.get_recent_yawns(300)
        
        # === GET THRESHOLD (Dynamic Calibration with ROBUST learning) ===
        threshold, is_calibrated = self.smart_threshold.update_threshold(
            current_ear=ear_smoothed,
            current_mar=mar,
            is_yawning=self.is_yawning,
            is_drowsy=self.is_drowsy
        )
        
        # Hysteresis for stable state detection
        if self.eye_state == 'open':
            close_threshold = threshold - self.hysteresis_margin
            is_eye_closed = ear_smoothed < close_threshold
        else:
            open_threshold = threshold + self.hysteresis_margin
            is_eye_closed = ear_smoothed < open_threshold
        
        # Stability check
        if is_eye_closed:
            self.stable_closed_count += 1
            if self.stable_closed_count >= self.stability_threshold:
                self.eye_state = 'closed'
        else:
            self.stable_closed_count = 0
            self.eye_state = 'open'
        
        # === TIME-BASED EYE CLOSURE DETECTION với BLINK FILTERING ===
        if is_eye_closed:
            if self.eye_closed_start_time is None:
                self.eye_closed_start_time = current_time
            self.eye_closed_duration = current_time - self.eye_closed_start_time
            
            # CHỈ CÓI LÀ DROWSY KHI VỪA ĐỦ THỜI GIAN VỪA ĐỦ STABILITY (bỏ qua chớp mắt)
            # Phải đồng thời: duration >= 1.5s VÀ eye_state == 'closed' (đã qua stability check)
            # QUAN TRỌNG: Nếu miệng đang mở (có thể đang ngáp) thì KHÔNG cảnh báo ngủ
            # Sử dụng mouth_is_open thay vì is_yawning để reset NGAY khi miệng mở, không chờ confirm
            if self.mouth_is_open:
                # Miệng đang mở (có thể đang ngáp) → RESET duration để KHÔNG tích frame nhắm mắt
                self.eye_closed_duration = 0.0
                self.is_drowsy = False
            elif (self.eye_closed_duration >= DrowsinessThresholds.EYE_CLOSED_WARNING and 
                  self.eye_state == 'closed'):
                self.is_drowsy = True
            else:
                # Nếu chưa đủ điều kiện thì CHƯA PHẢI drowsy
                self.is_drowsy = False
        else:
            # Mở mắt lại - RESET NGAY LẬP TỨC tất cả các flag
            self.eye_closed_start_time = None
            self.eye_closed_duration = 0.0
            self.is_drowsy = False
            # Reset luôn stable count để đảm bảo mỗi lần nhắm mắt đều phải đếm lại từ đầu
            self.stable_closed_count = 0
            # QUAN TRỌNG: Reset combined_fatigue_warning khi mở mắt để không kêu hoài
            # (sẽ được tính lại ở dưới dựa trên drowsy_episodes)
            self.combined_fatigue_warning = False
            # RESET fatigue_score về 10 (NORMAL level) khi mở mắt
            # Đảm bảo KHÔNG còn ở ngưỡng TIRED (30), DROWSY (45) hay CRITICAL (75)
            self.fatigue_score = 10  # Reset về NORMAL level
        
        # === ANALYZERS ===
        
        # 1. Sleep detection
        sleep_result = self.sleep_detector.update(ear_smoothed, threshold, is_eye_closed, current_time)
        
        # 2. PERCLOS
        perclos_result = self.perclos_calc.update(ear_smoothed, threshold)
        
        # 3. Blink analysis + Low blink rate pre-warning
        blink_result = self.blink_analyzer.update(ear_smoothed, threshold, current_time)
        
        if blink_result['blink_rate'] < DrowsinessThresholds.BLINK_RATE_LOW:
            if self.low_blink_start_time is None:
                self.low_blink_start_time = current_time
            elif current_time - self.low_blink_start_time >= DrowsinessThresholds.BLINK_RATE_LOW_DURATION:
                self.low_blink_warning = True
        else:
            self.low_blink_start_time = None
            self.low_blink_warning = False
        
        # (Yawn detection đã xử lý ở trên - để có is_yawning kịp thời)
        
        # 5. Head Pose detection
        head_result = self.head_pose_analyzer.update(self.current_landmarks, current_time)
        
        # === FATIGUE CALCULATION ===
        self.fatigue_score = self._calculate_fatigue_score_v2(
            perclos_result, blink_result, sleep_result, 
            recent_yawns, head_result
        )
        
        # === VETO LOGIC: Immediate CRITICAL for severe events ===
        veto_critical = False
        veto_reason = ""
        
        if sleep_result.get('immediate_danger'):
            veto_critical = True
            veto_reason = sleep_result.get('alert_message', 'SLEEPING!')
        elif self.eye_closed_duration >= DrowsinessThresholds.EYE_CLOSED_CRITICAL:
            veto_critical = True
            veto_reason = f"EYES CLOSED {self.eye_closed_duration:.1f}s!"
        elif head_result.get('warning_type') == 'head_danger':
            veto_critical = True
            veto_reason = "HEAD DROOPING - DANGER!"
        
        # Determine fatigue state with VETO
        if veto_critical:
            self.fatigue_state = FatigueState.CRITICAL
        else:
            self.fatigue_state = self._determine_fatigue_state_v2(
                sleep_result, perclos_result, recent_yawns, 
                blink_result, head_result
            )
            # Nếu mắt đã mở VÀ không có nguy hiểm khác thì giảm fatigue state
            if not self.is_drowsy and self.fatigue_state in [FatigueState.CRITICAL, FatigueState.DROWSY]:
                # Giảm xuống TIRED hoặc NORMAL tùy fatigue_score
                if self.fatigue_score >= 20:
                    self.fatigue_state = FatigueState.TIRED
                else:
                    self.fatigue_state = FatigueState.NORMAL
        
        # === COMBINED FATIGUE TRACKING ===
        # Chỉ track drowsy episodes khi đang thật sự drowsy
        if self.is_drowsy and (not self.drowsy_episodes or 
                                current_time - self.drowsy_episodes[-1] > 2):
            self.drowsy_episodes.append(current_time)
        
        recent_drowsy = len([t for t in self.drowsy_episodes 
                            if current_time - t < self.fatigue_window])
        recent_yawns_window = self.yawn_analyzer.get_recent_yawns(self.fatigue_window)
        
        # CHỈ set combined_fatigue_warning = True KHI ĐANG drowsy
        # Nếu đang mở mắt (is_drowsy=False) thì GIỮ False để không kêu nữa
        if self.is_drowsy:
            self.combined_fatigue_warning = (
                recent_yawns_window >= DrowsinessThresholds.FATIGUE_YAWN_THRESHOLD and
                recent_drowsy >= DrowsinessThresholds.FATIGUE_DROWSY_COUNT
            )
        else:
            # Mở mắt rồi thì reset combined warning
            self.combined_fatigue_warning = False
        
        # === WARNING LOGIC với ALERT SYSTEM ===
        warning = False
        warning_reason = ""
        is_reminder = False
        alert_config = None
        
        # EARLY EXIT: Nếu mắt đang mở VÀ không nguy hiểm critical → KHÔNG WARNING (tắt ngay âm thanh)
        # Điều kiện: mắt mở + không có veto_critical + không sleeping/microsleep
        eyes_are_open = (self.eye_state == 'open' and not is_eye_closed)
        no_critical_danger = (not veto_critical and 
                             not sleep_result.get('immediate_danger') and
                             not sleep_result.get('alert'))
        
        if eyes_are_open and no_critical_danger:
            # Mắt đang mở → chỉ cảnh báo các vấn đề KHÔNG liên quan đến mắt
            # (head pose, yawn, fatigue)
            pass  # Tiếp tục kiểm tra các điều kiện bên dưới
        
        # Xác định loại cảnh báo và trigger alert
        if veto_critical:
            warning = True
            warning_reason = veto_reason
            if sleep_result.get('immediate_danger'):
                alert_config = self.alert_system.trigger_alert(AlertType.SLEEPING, {
                    'duration': sleep_result.get('duration', 0)
                })
            elif self.eye_closed_duration >= DrowsinessThresholds.EYE_CLOSED_CRITICAL:
                alert_config = self.alert_system.trigger_alert(AlertType.SLEEPING, {
                    'duration': self.eye_closed_duration
                })
            elif head_result.get('warning_type') == 'head_danger':
                alert_config = self.alert_system.trigger_alert(AlertType.HEAD_DOWN, {
                    'duration': head_result.get('head_down_duration', 0)
                })
                
        elif sleep_result.get('alert'):
            warning = True
            warning_reason = sleep_result.get('alert_message', 'Wake up!')
            if sleep_result.get('event_type') == 'microsleep':
                alert_config = self.alert_system.trigger_alert(AlertType.MICROSLEEP, {
                    'duration': sleep_result.get('duration', 0)
                })
            else:
                alert_config = self.alert_system.trigger_alert(AlertType.DROWSINESS, {
                    'duration': sleep_result.get('duration', 0)
                })
                
        elif self.fatigue_state == FatigueState.CRITICAL and not eyes_are_open:  # Chỉ warning nếu mắt đang nhắm
            warning = True
            warning_reason = "CRITICAL: Stop driving!"
            alert_config = self.alert_system.trigger_alert(AlertType.DROWSINESS)
            
        elif head_result.get('warning'):
            warning = True
            head_type = head_result.get('warning_type')
            if head_type == 'head_danger':
                warning_reason = f"Head drooping DANGER ({head_result['head_down_duration']:.1f}s)"
                alert_config = self.alert_system.trigger_alert(AlertType.HEAD_DOWN, {
                    'duration': head_result['head_down_duration']
                })
            elif head_type == 'head_turn' or head_type == 'head_turn_danger':
                yaw = abs(head_result.get('yaw', 0))
                direction = "LEFT" if head_result.get('yaw', 0) < 0 else "RIGHT"
                warning_reason = f"LOOKING {direction} ({yaw:.0f}deg) - FOCUS FORWARD!"
                alert_config = self.alert_system.trigger_alert(AlertType.HEAD_TURN, {
                    'duration': head_result.get('head_turn_duration', 0),
                    'angle': yaw
                })
            elif head_type == 'head_tilt':
                warning_reason = f"Head tilt detected ({head_result['head_tilt_duration']:.1f}s)"
                alert_config = self.alert_system.trigger_alert(AlertType.HEAD_TILT, {
                    'duration': head_result['head_tilt_duration']
                })
            else:
                warning_reason = f"Head drooping ({head_result.get('head_down_duration', 0):.1f}s)"
                alert_config = self.alert_system.trigger_alert(AlertType.HEAD_TURN, {
                    'duration': head_result.get('head_down_duration', 0)
                })
                
        # LOẠI BỎ: combined_fatigue_warning - chỉ là mệt (ngáp + drowsy), KHÔNG phải ngủ
        # elif self.combined_fatigue_warning:
        #     warning = True
        #     warning_reason = f"FATIGUE: {recent_yawns_window} yawns + {recent_drowsy} drowsy"
        #     alert_config = self.alert_system.trigger_alert(AlertType.FATIGUE_COMBINED)
            
        elif self.is_drowsy and self.eye_state == 'closed':  # Thêm check eye_state để chắc chắn đang nhắm mắt
            warning = True
            warning_reason = f"Eyes closing ({self.eye_closed_duration:.1f}s)!"
            alert_config = self.alert_system.trigger_alert(AlertType.DROWSINESS, {
                'duration': self.eye_closed_duration
            })
            
        # LOẠI BỎ: low_blink_warning - chỉ là mệt (staring/chớp mắt ít), KHÔNG phải ngủ
        # elif self.low_blink_warning and eyes_are_open:
        #     warning = True
        #     warning_reason = "Staring detected - stay alert!"
        #     alert_config = self.alert_system.trigger_alert(AlertType.FATIGUE_BLINK)
            
        # XOÁ ĐIỂU KIỆN: self.fatigue_state == FatigueState.DROWSY and eyes_are_open
        # Vì khi mở mắt đã reset score về 20 rồi, không cần warning từ fatigue_state nữa
        # Nếu thực sự còn vấn đề (yawn, head pose) thì các điều kiện khác sẽ xử lý
            
        # LOẠI BỎ: is_yawning - chỉ là ngáp (mệt), KHÔNG phải ngủ
        # Chỉ hiển thị trên sidebar (Yawns count), không cần cảnh báo âm thanh
        # elif self.is_yawning:
        #     warning = True
        #     warning_reason = "Excessive yawning detected!"
        #     if recent_yawns >= DrowsinessThresholds.FATIGUE_YAWN_THRESHOLD:
        #         alert_config = self.alert_system.trigger_alert(AlertType.FATIGUE_YAWN)
        #     else:
        #         is_reminder = True
        #         warning = False
                
        # LOẠI BỎ: pre_sleep_warning - chỉ là mắt hơi nặng, chưa đến mức ngủ
        # elif sleep_result.get('pre_sleep_warning'):
        #     is_reminder = True
        #     warning_reason = "Eyes getting heavy"
        #     alert_config = self.alert_system.trigger_alert(AlertType.PRE_WARNING)
        
        # === BUILD RESULT ===
        sleep_stats = self.sleep_detector.get_statistics()
        risk_level, trend = self.sleep_detector.get_risk_level()
        session_duration = current_time - self.start_time
        
        return {
            'ear': ear,
            'mar': mar,
            'threshold': threshold,
            'is_calibrated': is_calibrated,
            'is_drowsy': self.is_drowsy,
            'is_yawning': self.is_yawning,
            'warning': warning,
            'warning_reason': warning_reason,
            'is_reminder': is_reminder,
            'combined_fatigue_warning': self.combined_fatigue_warning,
            'recent_drowsy_count': recent_drowsy,
            'fatigue_state': self.fatigue_state,
            'fatigue_score': self.fatigue_score,
            'fatigue_level': FatigueState.get_level(self.fatigue_state),
            'fatigue_color': FatigueState.get_color(self.fatigue_state),
            'perclos': perclos_result['perclos'],
            'perclos_percentage': perclos_result.get('perclos_percentage', 0),
            'perclos_level': perclos_result['perclos_level'],
            'blink_rate': blink_result['blink_rate'],
            'blink_pattern': blink_result['blink_pattern'],
            'avg_blink_duration': blink_result['avg_blink_duration'],
            'low_blink_warning': self.low_blink_warning,
            'is_sleeping': sleep_result.get('is_sleeping', False),
            'sleep_event_type': sleep_result.get('event_type'),
            'sleep_duration': sleep_result.get('duration', 0.0),
            'eye_closed_duration': self.eye_closed_duration,
            'pre_sleep_warning': sleep_result.get('pre_sleep_warning', False),
            'sleep_alert': sleep_result.get('alert', False),
            'sleep_alert_message': sleep_result.get('alert_message', ''),
            'immediate_danger': sleep_result.get('immediate_danger', False) or veto_critical,
            'sleep_stats': sleep_stats,
            'sleep_risk': risk_level,
            'sleep_trend': trend,
            'yawn_count': recent_yawns,
            'yawn_confidence': yawn_result.get('confidence', 0),
            'yawn_counter': 0,
            'head_pitch': head_result.get('pitch', 0),
            'head_roll': head_result.get('roll', 0),
            'head_warning': head_result.get('warning', False),
            'nod_count': head_result.get('nod_count', 0),
            'session_duration': session_duration,
            'status': self.smart_threshold.get_status_text(),
            'counter': int(self.eye_closed_duration * self.fps),
            'mouth_shape': mouth_shape,
            'tracking_lost': self.signal_stabilizer.is_tracking_lost(),
            'signal_hold_frames': self.signal_stabilizer.get_hold_duration(),
            'head_pose': head_result,
            'alert_config': alert_config,
            'alert_should_play_sound': self.alert_system.should_play_sound(alert_config.alert_type) if alert_config else False,
            'alert_sound_file': self.alert_system.get_sound_file(alert_config.alert_type) if alert_config else None,
            'alert_message': self.alert_system.get_alert_message(alert_config.alert_type, {
                'duration': self.eye_closed_duration,
                'count': recent_yawns
            }) if alert_config else warning_reason,
            'alert_action': self.alert_system.get_recommended_action(alert_config.alert_type) if alert_config else "",
        }
    
    def _calculate_fatigue_score_v2(self, perclos, blink, sleep, yawn_count, head) -> float:
        """Calculate fatigue score with improved weights - Ưu tiên nhắm mắt hơn ngáp"""
        score = 0.0
        details = []  # DEBUG: Track score components
        
        # PERCLOS (35%) - Chỉ số quan trọng nhất
        perclos_value = perclos.get('perclos', 0)
        perclos_score = min(35, perclos_value * 90)
        if perclos_score > 0:
            score += perclos_score
            details.append(f"PERCLOS: +{perclos_score:.1f}")
        
        # Sleep events (30%) - Rất nguy hiểm
        if sleep.get('is_sleeping'):
            duration = sleep.get('duration', 0)
            sleep_score = min(30, duration * 15)
            score += sleep_score
            details.append(f"Sleep: +{sleep_score:.1f}")
        
        # Blink patterns (15%)
        blink_score = self.blink_analyzer.get_fatigue_score()
        blink_contrib = blink_score * 0.15
        if blink_contrib > 0:
            score += blink_contrib
            details.append(f"Blink: +{blink_contrib:.1f}")
        
        # Low blink rate - GIẢM trọng số từ 10 → 5 (chỉ mệt nhẹ, không nguy hiểm)
        if blink.get('blink_rate', 15) < DrowsinessThresholds.BLINK_RATE_LOW:
            score += 5  # Giảm từ 10
            details.append(f"LowBlink: +5")
        
        # Yawns - GIẢM trọng số từ 3/lần → 1/lần (ngáp là dấu hiệu mệt, không phải ngủ)
        # Chỉ cộng tối đa 5 điểm (thay vì 10)
        yawn_score = min(5, yawn_count * 1)
        if yawn_score > 0:
            score += yawn_score
            details.append(f"Yawns({yawn_count}): +{yawn_score:.1f}")
        
        # Head pose (10%)
        score += self.head_pose_analyzer.get_fatigue_contribution() * 0.33
        
        # Eye closure bonus - TĂNG theo thời gian nhắm mắt (nguy hiểm nhất!)
        if self.is_drowsy:
            # Base bonus khi mắt nhắm >= 0.8s
            base_bonus = 25  # Tăng từ 20
            score += base_bonus
            
            # Thêm bonus tăng dần theo thời gian: +10 điểm mỗi 0.5 giây
            duration_bonus = min(30, (self.eye_closed_duration - 0.8) * 20)
            score += duration_bonus
            
            if duration_bonus > 0:
                details.append(f"EyeClosed({self.eye_closed_duration:.1f}s): +{base_bonus + duration_bonus:.1f}")
        
        return min(100, max(0, score))
    
    def _determine_fatigue_state_v2(self, sleep, perclos, yawn_count, blink, head) -> str:
        """Determine fatigue state with VETO logic"""
        
        # CRITICAL conditions
        if sleep.get('immediate_danger'):
            return FatigueState.CRITICAL
        if perclos.get('perclos_level') == 'critical':
            return FatigueState.CRITICAL
        if sleep.get('is_sleeping') and sleep.get('duration', 0) > 3.0:
            return FatigueState.CRITICAL
        if head.get('warning_type') == 'head_danger':
            return FatigueState.CRITICAL
        if self.fatigue_score >= 75:
            return FatigueState.CRITICAL
        
        # DROWSY conditions
        if sleep.get('is_sleeping'):
            return FatigueState.DROWSY
        if perclos.get('perclos_level') == 'drowsy':
            return FatigueState.DROWSY
        if head.get('warning'):
            return FatigueState.DROWSY
        if self.fatigue_score >= 45:
            return FatigueState.DROWSY
        
        # TIRED conditions
        if perclos.get('perclos_level') == 'tired':
            return FatigueState.TIRED
        if yawn_count >= DrowsinessThresholds.FATIGUE_YAWN_THRESHOLD:
            return FatigueState.TIRED
        if blink.get('blink_rate', 15) < DrowsinessThresholds.BLINK_RATE_LOW:
            return FatigueState.TIRED
        if self.fatigue_score >= 30:  # Tăng từ 20 -> 30 để có buffer với reset level (10)
            return FatigueState.TIRED
        
        # ALERT
        if self.fatigue_score < 10 and perclos.get('perclos_level') == 'alert':
            return FatigueState.ALERT
        
        return FatigueState.NORMAL
    
    def reset(self):
        """Reset all detection state"""
        self.is_drowsy = False
        self.is_yawning = False
        self.drowsy_episodes.clear()
        self.combined_fatigue_warning = False
        self.fatigue_state = FatigueState.NORMAL
        self.fatigue_score = 0.0
        self.start_time = time.time()
        self.frame_count = 0
        self.ear_buffer.clear()
        self.mar_buffer.clear()
        
        self.eye_state = 'open'
        self.stable_closed_count = 0
        
        self.eye_closed_start_time = None
        self.eye_closed_duration = 0.0
        self.low_blink_start_time = None
        self.low_blink_warning = False
        self.current_landmarks = None
        
        self.sleep_detector.reset()
        self.blink_analyzer.reset()
        self.perclos_calc.reset()
        self.smart_threshold.reset()
        self.yawn_analyzer.reset()
        self.head_pose_analyzer.reset()
    
    # === CALIBRATION ===
    
    def start_calibration(self):
        self.personal_calibration.start_calibration()
    
    def is_calibrating(self):
        state = self.personal_calibration.get_state()
        return state not in [PersonalCalibration.STATE_IDLE, PersonalCalibration.STATE_COMPLETED]
    
    def process_calibration(self, left_eye, right_eye, mouth=None) -> dict:
        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        ear = (left_ear + right_ear) / 2.0
        
        mar = 0.0
        if mouth is not None:
            mar = calculate_mar(mouth)
        
        progress, total, should_advance = self.personal_calibration.add_sample(ear, mar)
        
        if should_advance:
            self.personal_calibration.next_state()
        
        if self.personal_calibration.is_calibrated():
            thresholds = self.personal_calibration.get_thresholds()
            if thresholds.get('mar_threshold'):
                self.mar_threshold = thresholds['mar_threshold']
        
        return {
            'ear': ear,
            'mar': mar,
            'calibration_state': self.personal_calibration.get_state(),
            'calibration_text': self.personal_calibration.get_state_text(),
            'progress': progress,
            'total': total,
            'is_completed': self.personal_calibration.get_state() == PersonalCalibration.STATE_COMPLETED
        }
    
    def reset_calibration(self):
        self.personal_calibration.reset()
    
    def get_calibration_info(self) -> dict:
        if self.personal_calibration.is_calibrated():
            thresholds = self.personal_calibration.get_thresholds()
            return {
                'calibrated': True,
                'ear_threshold': thresholds.get('ear_threshold'),
                'mar_threshold': thresholds.get('mar_threshold'),
                'ear_open': thresholds.get('ear_open'),
                'ear_closed': thresholds.get('ear_closed'),
                'calibration_date': thresholds.get('calibration_date')
            }
        return {'calibrated': False}

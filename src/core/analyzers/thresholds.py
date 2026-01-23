"""
Drowsiness Thresholds - Constants for detection thresholds
"""


class DrowsinessThresholds:
    """Thresholds based on driving safety research"""
    # Eye closure thresholds (seconds) - TIME-BASED instead of frame-based
    BLINK_MAX = 0.4           # Normal blink < 0.4s
    MICROSLEEP_MIN = 0.5      # Microsleep starts at 0.5s
    MICROSLEEP_MAX = 2.0      # Microsleep ends at 2s
    NEAR_SLEEP_MAX = 4.0      # Near-sleep: 2-4s
    SLEEP_CRITICAL = 4.0      # Sleep episode: > 4s (DANGER)
    
    # TIME-BASED thresholds (FPS-independent)
    EYE_CLOSED_WARNING = 0.8  # 0.8 giây mắt nhắm = cảnh báo (giảm từ 1.5s để nhanh hơn)
    EYE_CLOSED_DANGER = 1.5   # 1.5 giây = nguy hiểm (giảm từ 2.0s)
    EYE_CLOSED_CRITICAL = 3.0 # 3.0 giây = nghiêm trọng (giảm từ 4.0s)
    
    # PERCLOS thresholds (% eyes closed in 1 minute)
    PERCLOS_NORMAL = 0.08     # < 8% = alert
    PERCLOS_TIRED = 0.15      # 8-15% = tired
    PERCLOS_DROWSY = 0.25     # 15-25% = drowsy
    PERCLOS_CRITICAL = 0.40   # > 40% = critical
    
    # Yawn detection (with variance check to distinguish from talking)
    YAWN_DURATION_MIN = 1.5   # Minimum yawn duration (seconds)
    YAWN_REMINDER_THRESHOLD = 2  # 2+ yawns = reminder
    YAWN_MAR_VARIANCE_MAX = 0.08  # Low variance = real yawn (tăng từ 0.05 -> 0.08 để dễ detect hơn)
    YAWN_EAR_DROP_THRESHOLD = 0.02  # Eyes tend to close slightly during yawn (giảm từ 0.03 -> 0.02 để nhạy hơn)
    
    # Head Pose thresholds (degrees)
    HEAD_PITCH_WARNING = -15  # Head tilted down 15 degrees
    HEAD_PITCH_DANGER = -25   # Head tilted down 25 degrees (nodding off)
    HEAD_ROLL_WARNING = 20    # Head tilted sideways 20 degrees
    HEAD_YAW_WARNING = 25     # Head turned left/right 25 degrees
    HEAD_YAW_DANGER = 40      # Head turned left/right 40 degrees (not looking forward!)
    HEAD_POSE_DURATION = 0.5  # Duration before warning (seconds) - reduced for faster response
    
    # Fatigue monitoring window (minutes)
    FATIGUE_WINDOW_MINUTES = 3     # Monitor over 3 minutes
    FATIGUE_YAWN_THRESHOLD = 3     # 3+ yawns in window = fatigue sign
    FATIGUE_DROWSY_COUNT = 5       # 5+ drowsy episodes in window = fatigue warning
    
    # Blink rate (per minute) - LOW blink rate is PRE-WARNING
    BLINK_RATE_LOW = 8        # < 8 = staring (pre-drowsiness sign)
    BLINK_RATE_NORMAL_MIN = 12
    BLINK_RATE_NORMAL_MAX = 20
    BLINK_RATE_HIGH = 25      # > 25 = trying to stay awake
    BLINK_RATE_LOW_DURATION = 30  # Seconds of low blink rate before warning
    
    # Dynamic calibration
    EAR_THRESHOLD_RATIO = 0.70  # threshold = baseline_ear * 0.70

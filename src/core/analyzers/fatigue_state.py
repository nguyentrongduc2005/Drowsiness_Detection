"""
Fatigue State System - 5-level fatigue classification
"""


class FatigueState:
    """5-level fatigue classification"""
    ALERT = "ALERT"
    NORMAL = "NORMAL"
    TIRED = "TIRED"
    DROWSY = "DROWSY"
    CRITICAL = "CRITICAL"
    
    @staticmethod
    def get_color(state):
        colors = {
            FatigueState.ALERT: (0, 255, 0),
            FatigueState.NORMAL: (0, 200, 100),
            FatigueState.TIRED: (0, 200, 255),
            FatigueState.DROWSY: (0, 100, 255),
            FatigueState.CRITICAL: (0, 0, 255),
        }
        return colors.get(state, (255, 255, 255))
    
    @staticmethod
    def get_level(state):
        levels = {
            FatigueState.ALERT: 0,
            FatigueState.NORMAL: 1,
            FatigueState.TIRED: 2,
            FatigueState.DROWSY: 3,
            FatigueState.CRITICAL: 4,
        }
        return levels.get(state, 1)
    
    @staticmethod
    def get_description(state):
        descriptions = {
            FatigueState.ALERT: "Fully alert",
            FatigueState.NORMAL: "Normal state",
            FatigueState.TIRED: "Early fatigue signs",
            FatigueState.DROWSY: "Drowsy - need break",
            FatigueState.CRITICAL: "DANGER - stop now!",
        }
        return descriptions.get(state, "")

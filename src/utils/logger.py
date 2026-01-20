"""
Logger Module: Record events and save logs
"""
import csv
import os
from datetime import datetime


class EventLogger:
    """
    Class to record events during drowsiness detection
    """
    
    def __init__(self, log_dir="logs"):
        """
        Initialize logger
        
        Args:
            log_dir: Directory to save log files
        """
        self.log_dir = log_dir
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"drowsiness_log_{timestamp}.csv")
        
        # Initialize CSV file with header
        self._init_csv()
        
    def _init_csv(self):
        """Initialize CSV file with header"""
        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'EAR', 'Threshold', 'Status', 'Alert'])
    
    def log_event(self, ear, threshold, status, is_drowsy=False):
        """
        Log an event
        
        Args:
            ear: EAR value
            threshold: Current threshold
            status: System status
            is_drowsy: True if drowsiness detected
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert is_drowsy to text
        alert = "DROWSY" if is_drowsy else "Alert"
        
        # Write to CSV
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, f"{ear:.3f}", f"{threshold:.3f}", status, alert])
        except Exception as e:
            print(f"Error writing log: {e}")
    
    def log_alert(self, ear, threshold):
        """
        Log a drowsiness alert event
        
        Args:
            ear: EAR value
            threshold: Current threshold
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_file = os.path.join(self.log_dir, "alerts.txt")
        
        try:
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] ALERT: EAR={ear:.3f}, Threshold={threshold:.3f}\n")
        except Exception as e:
            print(f"Error writing alert: {e}")
    
    def get_log_file_path(self):
        """
        Get current log file path
        
        Returns:
            str: Log file path
        """
        return self.log_file


class StatisticsTracker:
    """
    Class to track statistics during work session
    """
    
    def __init__(self):
        """Initialize tracker"""
        self.total_frames = 0
        self.drowsy_frames = 0
        self.alert_count = 0
        self.session_start = datetime.now()
        
    def update(self, is_drowsy):
        """
        Update statistics
        
        Args:
            is_drowsy: True if current frame detects drowsiness
        """
        self.total_frames += 1
        
        if is_drowsy:
            self.drowsy_frames += 1
            self.alert_count += 1
    
    def get_statistics(self):
        """
        Get aggregate statistics
        
        Returns:
            dict: Dictionary containing statistics
        """
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        drowsy_percentage = 0
        if self.total_frames > 0:
            drowsy_percentage = (self.drowsy_frames / self.total_frames) * 100
        
        return {
            'total_frames': self.total_frames,
            'drowsy_frames': self.drowsy_frames,
            'alert_count': self.alert_count,
            'drowsy_percentage': drowsy_percentage,
            'session_duration': session_duration
        }
    
    def reset(self):
        """Reset statistics"""
        self.total_frames = 0
        self.drowsy_frames = 0
        self.alert_count = 0
        self.session_start = datetime.now()
    
    def print_summary(self):
        """Print statistics summary"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("SESSION STATISTICS")
        print("="*50)
        print(f"Duration: {stats['session_duration']:.0f} seconds")
        print(f"Total frames: {stats['total_frames']}")
        print(f"Drowsy frames: {stats['drowsy_frames']}")
        print(f"Alert count: {stats['alert_count']}")
        print(f"Drowsy percentage: {stats['drowsy_percentage']:.2f}%")
        print("="*50 + "\n")

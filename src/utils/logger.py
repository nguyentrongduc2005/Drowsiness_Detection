"""
Module Logger: Ghi lại sự kiện và lưu log
"""
import csv
import os
from datetime import datetime


class EventLogger:
    """
    Class ghi lại các sự kiện trong quá trình phát hiện buồn ngủ
    """
    
    def __init__(self, log_dir="logs"):
        """
        Khởi tạo logger
        
        Args:
            log_dir: Thư mục lưu file log
        """
        self.log_dir = log_dir
        
        # Tạo thư mục logs nếu chưa tồn tại
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Tạo tên file log theo ngày
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"drowsiness_log_{timestamp}.csv")
        
        # Khởi tạo file CSV với header
        self._init_csv()
        
    def _init_csv(self):
        """Khởi tạo file CSV với header"""
        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Thời gian', 'EAR', 'Ngưỡng', 'Trạng thái', 'Cảnh báo'])
    
    def log_event(self, ear, threshold, status, is_drowsy=False):
        """
        Ghi lại một sự kiện
        
        Args:
            ear: Giá trị EAR
            threshold: Ngưỡng hiện tại
            status: Trạng thái hệ thống
            is_drowsy: True nếu phát hiện buồn ngủ
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Chuyển đổi is_drowsy thành text
        alert = "BUỒN NGỦ" if is_drowsy else "Tỉnh táo"
        
        # Ghi vào CSV
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, f"{ear:.3f}", f"{threshold:.3f}", status, alert])
        except Exception as e:
            print(f"Lỗi khi ghi log: {e}")
    
    def log_alert(self, ear, threshold):
        """
        Ghi lại sự kiện cảnh báo buồn ngủ
        
        Args:
            ear: Giá trị EAR
            threshold: Ngưỡng hiện tại
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_file = os.path.join(self.log_dir, "alerts.txt")
        
        try:
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] CẢNH BÁO: EAR={ear:.3f}, Ngưỡng={threshold:.3f}\n")
        except Exception as e:
            print(f"Lỗi khi ghi alert: {e}")
    
    def get_log_file_path(self):
        """
        Lấy đường dẫn file log hiện tại
        
        Returns:
            str: Đường dẫn file log
        """
        return self.log_file


class StatisticsTracker:
    """
    Class theo dõi thống kê trong phiên làm việc
    """
    
    def __init__(self):
        """Khởi tạo tracker"""
        self.total_frames = 0
        self.drowsy_frames = 0
        self.alert_count = 0
        self.session_start = datetime.now()
        
    def update(self, is_drowsy):
        """
        Cập nhật thống kê
        
        Args:
            is_drowsy: True nếu frame hiện tại phát hiện buồn ngủ
        """
        self.total_frames += 1
        
        if is_drowsy:
            self.drowsy_frames += 1
            self.alert_count += 1
    
    def get_statistics(self):
        """
        Lấy thống kê tổng hợp
        
        Returns:
            dict: Dictionary chứa các thống kê
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
        """Reset thống kê"""
        self.total_frames = 0
        self.drowsy_frames = 0
        self.alert_count = 0
        self.session_start = datetime.now()
    
    def print_summary(self):
        """In ra tóm tắt thống kê"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("THỐNG KÊ PHIÊN LÀM VIỆC")
        print("="*50)
        print(f"Thời gian: {stats['session_duration']:.0f} giây")
        print(f"Tổng số frame: {stats['total_frames']}")
        print(f"Frame buồn ngủ: {stats['drowsy_frames']}")
        print(f"Số lần cảnh báo: {stats['alert_count']}")
        print(f"Tỷ lệ buồn ngủ: {stats['drowsy_percentage']:.2f}%")
        print("="*50 + "\n")

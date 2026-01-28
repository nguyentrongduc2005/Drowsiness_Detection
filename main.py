"""
Main Entry Point
Hệ thống Cảnh báo Ngủ Khi Lái Xe
"""
import sys
from PyQt5.QtWidgets import QApplication

from src.config import ConfigManager
from src.interface import MainWindow


def main():
    """Hàm main - khởi động ứng dụng"""
    print("=" * 60)
    print("HỆ THỐNG CẢNH BÁO NGỦ KHI LÁI XE")
    print("Driver Drowsiness Detection System")
    print("=" * 60)
    
    # Khởi tạo ConfigManager
    config = ConfigManager()
    print(f"\n[Main] Đã load cấu hình")
    
    # Khởi tạo Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Drowsiness Detection System")
    
    # Tạo và hiển thị main window
    window = MainWindow(config)
    window.show()
    
    print("[Main] Ứng dụng đã khởi động")
    print("Nhấn nút 'BẮT ĐẦU' để bắt đầu phát hiện\n")
    
    # Chạy event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

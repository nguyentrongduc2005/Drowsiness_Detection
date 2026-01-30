"""
Generate a simple alert sound for testing
This script creates a beep sound if you don't have an alert.wav file
"""
import numpy as np
from scipy.io import wavfile
import os


def generate_alert_sound(filename="data/alert.wav", duration=2.0, frequency=800):
    """
    Generate a simple alert beep sound
    Tạo file âm thanh cảnh báo đơn giản
    Dùng hàm sine để tạo sóng âm thanh
    
    Args:
        filename: Tên file đầu ra (Output filename)
        duration: Thời lượng tính bằng giây (Duration in seconds)
        frequency: Tần số của tiếng bip tính bằng Hz (Frequency of the beep in Hz)
    """
    # Tạo thư mục data nếu chưa tồn tại
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Tần số lấy mẫu âm thanh (44.1kHz là chuẩn CD quality)
    # Sample rate (44.1kHz is CD quality standard)
    sample_rate = 44100
    
    # Tạo mảng thời gian từ 0 đến duration
    # Số lượng điểm = sample_rate * duration
    # Generate time array from 0 to duration
    # Number of points = sample_rate * duration
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Tạo sóng sine cơ bản với công thức: sin(2π * tần_số * thời_gian)
    # Đây là sóng âm thanh cơ bản với tần số cho trước
    # Generate basic sine wave with formula: sin(2π * frequency * time)
    # This is the basic sound wave with given frequency
    beep = np.sin(2 * np.pi * frequency * t)
    
    # Thêm hiệu ứng điều chế biên độ (amplitude modulation)
    # Tạo sóng sine với tần số 4Hz để thay đổi âm lượng theo thời gian
    # Làm cho âm thanh có hiệu ứng "rung" giống chuông báo động
    # Add amplitude modulation effect
    # Create sine wave at 4Hz to vary volume over time
    # Makes sound have "warbling" effect like alarm
    modulation = np.sin(2 * np.pi * 4 * t)  # 4 Hz modulation
    # Kết hợp sóng gốc với modulation: biên độ dao động từ 0.7 đến 1.0
    # Combine original wave with modulation: amplitude varies from 0.7 to 1.0
    beep = beep * (0.7 + 0.3 * modulation)
    
    # Tạo hiệu ứng fade in/out để tránh tiếng "lách cách" khi bắt đầu/kết thúc
    # Fade in/out trong 10ms (0.01 giây)
    # Apply fade in/out to avoid "clicking" sounds at start/end
    # Fade in/out over 10ms (0.01 seconds)
    fade_samples = int(0.01 * sample_rate)  # Số mẫu cho fade (10ms)
    
    # Tạo mảng fade in: tăng dần từ 0 đến 1
    # Create fade in array: gradually increase from 0 to 1
    fade_in = np.linspace(0, 1, fade_samples)
    
    # Tạo mảng fade out: giảm dần từ 1 đến 0
    # Create fade out array: gradually decrease from 1 to 0
    fade_out = np.linspace(1, 0, fade_samples)
    
    # Áp dụng fade in cho các mẫu đầu tiên
    # Apply fade in to first samples
    beep[:fade_samples] *= fade_in
    
    # Áp dụng fade out cho các mẫu cuối cùng
    # Apply fade out to last samples
    beep[-fade_samples:] *= fade_out
    
    # Chuẩn hóa sang định dạng 16-bit integer
    # Nhân với 32767 (giá trị max của int16) và 0.8 để tránh vượt quá giới hạn
    # Normalize to 16-bit integer format
    # Multiply by 32767 (max value of int16) and 0.8 to avoid clipping
    beep = np.int16(beep * 32767 * 0.8)
    
    # Lưu file WAV với sample_rate và dữ liệu âm thanh
    # Save WAV file with sample_rate and audio data
    wavfile.write(filename, sample_rate, beep)
    
    # In thông báo xác nhận
    # Print confirmation message
    print(f"Alert sound generated: {filename}")
    print(f"Duration: {duration}s, Frequency: {frequency}Hz")


if __name__ == "__main__":
    # Chạy hàm tạo âm thanh với tham số mặc định
    # Run sound generation function with default parameters
    generate_alert_sound()
    
    # In hướng dẫn cài đặt và sử dụng
    # Print installation and usage instructions
    print("\nNote: You need scipy to run this script.")
    print("Install with: pip install scipy")
    print("\nAlternatively, you can download any alert.wav file")
    print("and place it in the data/ directory.")

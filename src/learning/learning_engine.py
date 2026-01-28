"""
Learning Engine - Tự động học và điều chỉnh ngưỡng
"""
import numpy as np
from typing import Optional


class LearningEngine:
    """Quản lý việc học và cập nhật ngưỡng tự động"""
    
    def __init__(self, config_manager, learning_samples: int = 100, weight: float = 0.3):
        """
        Khởi tạo LearningEngine
        
        Args:
            config_manager: ConfigManager instance để lưu/load ngưỡng
            learning_samples: Số mẫu trước khi cập nhật ngưỡng
            weight: Trọng số cho ngưỡng mới (0-1)
        """
        self.config = config_manager
        self.learning_samples = learning_samples
        self.weight = weight
        
        # State
        self.continuous_learning = True  # Luôn học liên tục
        self.ear_samples = []
        self.mar_samples = []
        self.learning_counter = 0
        
        print("[Learning] Đã khởi tạo Learning Engine")
    
    def add_sample(self, ear: float, mar: float, quality: float = 1.0) -> bool:
        """
        Thêm mẫu trong quá trình học (chỉ chọn mẫu tốt)
        
        Args:
            ear: Eye Aspect Ratio
            mar: Mouth Aspect Ratio
            quality: Chất lượng phát hiện (0-1), chỉ lấy >= 0.75
            
        Returns:
            True nếu đã thêm mẫu thành công
        """
        if not self.continuous_learning or quality < 0.75:
            return False
        
        self.ear_samples.append(ear)
        self.mar_samples.append(mar)
        self.learning_counter += 1
        
        # Tự động cập nhật ngưỡng sau mỗi 50 samples
        if self.learning_counter >= 50:
            self.update_thresholds()
            self.learning_counter = 0
            return True
        
        return False
    
    def update_thresholds(self) -> Optional[tuple]:
        """
        Cập nhật ngưỡng dựa trên samples đã thu thập
        
        Returns:
            (new_ear, new_mar) nếu cập nhật thành công, None nếu không đủ samples
        """
        if len(self.ear_samples) < 10:
            print("[Learning] Chưa đủ samples để cập nhật ngưỡng")
            return None
        
        # Lấy 100 samples gần nhất
        recent_ear = self.ear_samples[-100:]
        recent_mar = self.mar_samples[-100:]
        
        # Tính statistics
        ear_mean = np.mean(recent_ear)
        mar_mean = np.mean(recent_mar)
        ear_std = np.std(recent_ear)
        
        # Ngưỡng mới = mean - 1.5*std (bảo thủ vừa phải)
        new_ear_threshold = ear_mean - 1.5 * ear_std
        new_mar_threshold = mar_mean * 1.5  # Ngáp thì miệng mở gấp 1.5 lần
        
        # Lấy ngưỡng hiện tại
        current_ear = self.config.get("thresholds.ear", 0.21)
        current_mar = self.config.get("thresholds.mar", 0.6)
        
        # Apply weighted update
        updated_ear = current_ear * (1 - self.weight) + new_ear_threshold * self.weight
        updated_mar = current_mar * (1 - self.weight) + new_mar_threshold * self.weight
        
        # Đảm bảo trong giới hạn (giữ max cao 0.30 để học linh hoạt)
        updated_ear = max(0.17, min(0.30, updated_ear))
        updated_mar = max(0.5, min(0.8, updated_mar))
        
        # Lưu vào config
        self.config.set("thresholds.ear", updated_ear)
        self.config.set("thresholds.mar", updated_mar)
        self.config.save()
        
        print(f"[Learning] Auto-updated thresholds: EAR={updated_ear:.3f}, MAR={updated_mar:.3f}")
        print(f"[Learning] Stats: EAR mean={ear_mean:.3f}, std={ear_std:.3f}, samples={len(recent_ear)}")
        
        return (updated_ear, updated_mar)
    
    def reset(self):
        """Reset và học lại từ đầu"""
        self.ear_samples = []
        self.mar_samples = []
        self.learning_counter = 0
        self.continuous_learning = True
        print("[Learning] Reset complete, starting fresh learning")
    
    def get_progress(self) -> float:
        """
        Lấy tiến độ học (%)
        
        Returns:
            Tiến độ từ 0-100 đến lần cập nhật tiếp theo
        """
        if not self.continuous_learning:
            return 0.0
        # Hiển thị tiến độ đến lần cập nhật tiếp theo (50 samples)
        return min(100.0, (self.learning_counter / 50) * 100)
    
    def get_total_samples(self) -> int:
        """Lấy tổng số mẫu đã học"""
        return len(self.ear_samples)
    
    def get_stats(self) -> dict:
        """
        Lấy thống kê học
        
        Returns:
            Dict chứa các thông tin thống kê
        """
        if len(self.ear_samples) == 0:
            return {
                "total_samples": 0,
                "progress": 0.0,
                "ear_mean": 0.0,
                "ear_std": 0.0,
                "mar_mean": 0.0
            }
        
        recent_ear = self.ear_samples[-100:]
        recent_mar = self.mar_samples[-100:]
        
        return {
            "total_samples": len(self.ear_samples),
            "progress": self.get_progress(),
            "ear_mean": float(np.mean(recent_ear)),
            "ear_std": float(np.std(recent_ear)),
            "mar_mean": float(np.mean(recent_mar)),
            "current_counter": self.learning_counter
        }
    
    def enable(self):
        """Bật chế độ học"""
        self.continuous_learning = True
        print("[Learning] Learning enabled")
    
    def disable(self):
        """Tắt chế độ học"""
        self.continuous_learning = False
        print("[Learning] Learning disabled")
    
    def is_enabled(self) -> bool:
        """Kiểm tra học có đang bật không"""
        return self.continuous_learning

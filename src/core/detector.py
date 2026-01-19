"""
Module AI: Phát hiện khuôn mặt và trích xuất 68 điểm landmarks
"""
import cv2
import dlib
import numpy as np


class FaceDetector:
    """Class phát hiện khuôn mặt và landmarks"""
    
    # Hằng số tối ưu
    SCALE_WIDTH = 240  # Giảm xuống 240px để tăng tốc
    SKIP_FRAMES = 2    # Chỉ detect face mỗi 2 frame
    
    def __init__(self, predictor_path="shape_predictor_68_face_landmarks.dat"):
        """
        Khởi tạo detector
        Args:
            predictor_path: Đường dẉn tới file shape predictor của dlib
        """
        print("Đang khởi tạo face detector...")
        
        # Cache để tối ưu
        self._frame_count = 0
        self._last_face_rect = None
        
        # Sử dụng Haar Cascade (có sẵn, ổn định)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            print("⚠ Cảnh báo: Không tìm được cascade classifier")
            self.face_cascade = None
        
        if self.face_cascade.empty():
            print("⚠ Không load được Haar Cascade, thử dùng dlib detector...")
            self.face_cascade = None
            self.detector = dlib.get_frontal_face_detector()
        else:
            print("✓ Haar Cascade detector đã được load!")
            self.detector = None
        
        try:
            print(f"Đang load model: {predictor_path}")
            self.predictor = dlib.shape_predictor(predictor_path)
            print("✓ Model đã được load thành công!")
        except RuntimeError:
            # Nếu không tìm thấy file, thử tìm trong thư mục data
            import os
            alt_path = os.path.join("data", predictor_path)
            print(f"Thử load từ: {alt_path}")
            self.predictor = dlib.shape_predictor(alt_path)
            print("✓ Model đã được load thành công!")
    
    def get_landmarks(self, frame):
        """
        Trích xuất 68 điểm landmarks từ frame
        
        Args:
            frame: Frame ảnh từ camera (BGR hoặc RGB)
            
        Returns:
            list: Danh sách 68 cặp tọa độ (x, y) hoặc None nếu không phát hiện khuôn mặt
            
        Index quan trọng:
            - Mắt trái: [36, 41]
            - Mắt phải: [42, 47]
            - Miệng: [48, 67]
        """
        # Kiểm tra frame hợp lệ
        if frame is None or frame.size == 0:
            return None
        
        try:
            # Chuyển sang grayscale (tối ưu: không copy nếu không cần)
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # Đảm bảo contiguous cho dlib
            if not gray.flags['C_CONTIGUOUS']:
                gray = np.ascontiguousarray(gray, dtype=np.uint8)
            
            self._frame_count += 1
            
            # Skip frame detection để tăng FPS (dùng cache)
            if self._frame_count % self.SKIP_FRAMES != 0 and self._last_face_rect is not None:
                face_rect = self._last_face_rect
            else:
                # Resize để tối ưu tốc độ nhận diện
                h, w = gray.shape
                scale_ratio = 1.0
                
                if w > self.SCALE_WIDTH:
                    scale_ratio = self.SCALE_WIDTH / float(w)
                    new_h = int(h * scale_ratio)
                    small_gray = cv2.resize(gray, (self.SCALE_WIDTH, new_h), interpolation=cv2.INTER_NEAREST)
                else:
                    small_gray = gray

                # Phát hiện khuôn mặt
                if self.face_cascade is not None:
                    # Sử dụng LBP/Haar Cascade với ảnh nhỏ
                    faces = self.face_cascade.detectMultiScale(
                        small_gray,
                        scaleFactor=1.2,  # Tăng lên để nhanh hơn
                        minNeighbors=3,
                        minSize=(24, 24),
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )
                    
                    if len(faces) == 0:
                        self._last_face_rect = None
                        return None
                    
                    # Tìm khuôn mặt lớn nhất (người dùng chính)
                    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
                    x, y, fw, fh = largest_face
                    
                    # Scale tọa độ về ảnh gốc
                    if scale_ratio != 1.0:
                        inv_ratio = 1.0 / scale_ratio
                        x = int(x * inv_ratio)
                        y = int(y * inv_ratio)
                        fw = int(fw * inv_ratio)
                        fh = int(fh * inv_ratio)

                    face_rect = dlib.rectangle(x, y, x + fw, y + fh)
                    
                else:
                    # Fallback: Sử dụng dlib detector
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if len(frame.shape) == 3 else frame
                    if not rgb_frame.flags['C_CONTIGUOUS']:
                        rgb_frame = np.ascontiguousarray(rgb_frame, dtype=np.uint8)
                    faces = self.detector(rgb_frame, 0)
                    
                    if len(faces) == 0:
                        self._last_face_rect = None
                        return None
                    
                    # Tìm khuôn mặt lớn nhất
                    face_rect = max(faces, key=lambda rect: rect.width() * rect.height())
                
                # Cache kết quả
                self._last_face_rect = face_rect
            
        except Exception as e:
            print(f"Lỗi trong get_landmarks: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Nếu không tìm thấy khuôn mặt
        if face_rect is None:
            return None
        
        # Dự đoán 68 điểm landmarks với dlib predictor
        shape = self.predictor(gray, face_rect)
        
        # Chuyển đổi sang list các cặp (x, y)
        landmarks = []
        for i in range(68):
            landmarks.append((shape.part(i).x, shape.part(i).y))
        
        return landmarks
    
    def get_eye_landmarks(self, landmarks):
        """
        Lấy tọa độ các điểm của mắt
        
        Args:
            landmarks: Danh sách 68 điểm
            
        Returns:
            tuple: (left_eye_points, right_eye_points)
        """
        if landmarks is None:
            return None, None
        
        left_eye = landmarks[36:42]   # Index 36-41
        right_eye = landmarks[42:48]  # Index 42-47
        
        return left_eye, right_eye
    
    def get_mouth_landmarks(self, landmarks):
        """
        Lấy tọa độ các điểm của miệng
        
        Args:
            landmarks: Danh sách 68 điểm
            
        Returns:
            list: Các điểm của miệng (index 48-67)
        """
        if landmarks is None:
            return None
        
        mouth = landmarks[48:68]  # Index 48-67
        
        return mouth
    
    def draw_landmarks(self, frame, landmarks):
        """
        Vẽ landmarks lên frame (dùng để debug)
        
        Args:
            frame: Frame ảnh
            landmarks: Danh sách 68 điểm
            
        Returns:
            frame: Frame đã vẽ landmarks
        """
        if landmarks is None:
            return frame
        
        # Vẽ các điểm
        for (x, y) in landmarks:
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
        
        # Vẽ đường viền mắt trái
        left_eye = landmarks[36:42]
        for i in range(len(left_eye)):
            cv2.line(frame, left_eye[i], left_eye[(i + 1) % len(left_eye)], (255, 0, 0), 1)
        
        # Vẽ đường viền mắt phải
        right_eye = landmarks[42:48]
        for i in range(len(right_eye)):
            cv2.line(frame, right_eye[i], right_eye[(i + 1) % len(right_eye)], (255, 0, 0), 1)
        
        # Vẽ đường viền miệng
        mouth = landmarks[48:68]
        for i in range(len(mouth)):
            cv2.line(frame, mouth[i], mouth[(i + 1) % len(mouth)], (0, 0, 255), 1)
        
        return frame

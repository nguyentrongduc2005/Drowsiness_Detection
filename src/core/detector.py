"""
Module AI: Phát hiện khuôn mặt và trích xuất 68 điểm landmarks
"""
import cv2
import dlib
import numpy as np


class FaceDetector:
    """Class phát hiện khuôn mặt và landmarks"""
    
    def __init__(self, predictor_path="shape_predictor_68_face_landmarks.dat"):
        """
        Khởi tạo detector
        Args:
            predictor_path: Đường dẉn tới file shape predictor của dlib
        """
        print("Đang khởi tạo face detector...")
        
        # Sử dụng OpenCV Haar Cascade thay vì dlib detector (ổn định hơn)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
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
            # # Đảm bảo frame là contiguous và uint8
            # if not frame.flags['C_CONTIGUOUS']:
            #     frame = np.ascontiguousarray(frame, dtype=np.uint8)
            # elif frame.dtype != np.uint8:
            #     frame = frame.astype(np.uint8)
            
            # Chuyển sang grayscale để phát hiện face
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame.copy()

            # Tạo một bản copy sạch cho dlib predictor
            gray_for_predictor = np.empty_like(gray, dtype=np.uint8)
            gray_for_predictor[:] = gray
            gray_for_predictor = np.ascontiguousarray(gray_for_predictor, dtype=np.uint8)
            
            # Phát hiện khuôn mặt
            if self.face_cascade is not None:
                # Sử dụng OpenCV Haar Cascade
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                print(f"  [DEBUG] OpenCV detected {len(faces)} faces")
                
                if len(faces) == 0:
                    return None
                
                # Chuyển đổi từ OpenCV rect sang dlib rectangle
                x, y, w, h = faces[0]
                face_rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
                
            else:
                # Fallback: Sử dụng dlib detector (có thể bị lỗi)
                print("  [DEBUG] Sử dụng dlib detector...")
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if len(frame.shape) == 3 else frame
                rgb_frame = np.ascontiguousarray(rgb_frame, dtype=np.uint8)
                faces = self.detector(rgb_frame, 0)
                
                if len(faces) == 0:
                    return None
                
                face_rect = faces[0]
            
        except Exception as e:
            print(f"Lỗi trong get_landmarks: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Nếu không tìm thấy khuôn mặt
        if face_rect is None:
            print("  [DEBUG] Không phát hiện được khuôn mặt nào")
            return None
        
        print(f"  [DEBUG] ✓ Phát hiện khuôn mặt tại: ({face_rect.left()}, {face_rect.top()}, {face_rect.right()}, {face_rect.bottom()})")
        print(f"  [DEBUG] Gray shape: {gray_for_predictor.shape}, dtype: {gray_for_predictor.dtype}, contiguous: {gray_for_predictor.flags['C_CONTIGUOUS']}")
        
        # Dự đoán 68 điểm landmarks với dlib predictor
        # Predictor hoạt động tốt với grayscale
        shape = self.predictor(gray_for_predictor, face_rect)
        
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

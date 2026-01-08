import cv2
import dlib
import numpy as np

# Test what dlib actually accepts
predictor_path = r"data\shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(predictor_path)

# Create test images
print("Testing different image formats with dlib predictor...")

# Test 1: Simple gray image
gray1 = np.zeros((480, 640), dtype=np.uint8)
print(f"\n1. Simple zeros gray: shape={gray1.shape}, dtype={gray1.dtype}, contiguous={gray1.flags['C_CONTIGUOUS']}")
try:
    rect = dlib.rectangle(100, 100, 200, 200)
    shape = predictor(gray1, rect)
    print("   ✓ SUCCESS")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 2: Gray from cvtColor
color = np.zeros((480, 640, 3), dtype=np.uint8)
gray2 = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
print(f"\n2. cvtColor gray: shape={gray2.shape}, dtype={gray2.dtype}, contiguous={gray2.flags['C_CONTIGUOUS']}")
print(f"   strides={gray2.strides}, base={gray2.base is not None}")
try:
    shape = predictor(gray2, rect)
    print("   ✓ SUCCESS")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 3: Copy of cvtColor
gray3 = gray2.copy()
print(f"\n3. Copy of cvtColor: shape={gray3.shape}, dtype={gray3.dtype}, contiguous={gray3.flags['C_CONTIGUOUS']}")
print(f"   strides={gray3.strides}, base={gray3.base is not None}")
try:
    shape = predictor(gray3, rect)
    print("   ✓ SUCCESS")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 4: Ascontiguousarray
gray4 = np.ascontiguousarray(gray2, dtype=np.uint8)
print(f"\n4. Ascontiguousarray: shape={gray4.shape}, dtype={gray4.dtype}, contiguous={gray4.flags['C_CONTIGUOUS']}")
print(f"   strides={gray4.strides}, base={gray4.base is not None}")
try:
    shape = predictor(gray4, rect)
    print("   ✓ SUCCESS")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 5: From actual camera
print("\n5. Testing with actual camera frame...")
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print(f"   Original frame: shape={frame.shape}, dtype={frame.dtype}, contiguous={frame.flags['C_CONTIGUOUS']}")
    gray5 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    print(f"   Gray frame: shape={gray5.shape}, dtype={gray5.dtype}, contiguous={gray5.flags['C_CONTIGUOUS']}")
    print(f"   strides={gray5.strides}, base={gray5.base is not None}")
    try:
        shape = predictor(gray5, rect)
        print("   ✓ SUCCESS")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
cap.release()

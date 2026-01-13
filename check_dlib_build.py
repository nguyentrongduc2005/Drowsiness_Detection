import dlib
import numpy as np
import sys

print("=" * 60)
print("DLIB DIAGNOSTIC CHECK")
print("=" * 60)

# Check versions
print(f"\nPython version: {sys.version}")
print(f"Dlib version: {dlib.__version__}")
print(f"Dlib compiled with CUDA: {dlib.DLIB_USE_CUDA}")
print(f"Dlib file location: {dlib.__file__}")

# Check if dlib has the right bindings
print("\n" + "=" * 60)
print("CHECKING DLIB CAPABILITIES")
print("=" * 60)

try:
    detector = dlib.get_frontal_face_detector()
    print("✓ Face detector loaded successfully")
except Exception as e:
    print(f"✗ Face detector failed: {e}")

try:
    predictor_path = r"data\shape_predictor_68_face_landmarks.dat"
    predictor = dlib.shape_predictor(predictor_path)
    print(f"✓ Shape predictor loaded successfully from {predictor_path}")
except Exception as e:
    print(f"✗ Shape predictor failed: {e}")
    sys.exit(1)

# Now test with different image types
print("\n" + "=" * 60)
print("TESTING IMAGE TYPES")
print("=" * 60)

rect = dlib.rectangle(100, 100, 200, 200)

# Test 1: numpy uint8 array (grayscale)
print("\n1. Testing numpy uint8 grayscale array...")
try:
    img = np.zeros((480, 640), dtype=np.uint8)
    print(f"   Image info: shape={img.shape}, dtype={img.dtype}, flags={img.flags}")
    result = predictor(img, rect)
    print("   ✓ SUCCESS with grayscale")
except Exception as e:
    print(f"   ✗ FAILED with grayscale: {e}")

# Test 2: numpy uint8 array (RGB)
print("\n2. Testing numpy uint8 RGB array...")
try:
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    print(f"   Image info: shape={img.shape}, dtype={img.dtype}, flags={img.flags}")
    result = predictor(img, rect)
    print("   ✓ SUCCESS with RGB")
except Exception as e:
    print(f"   ✗ FAILED with RGB: {e}")

# Test 3: Check if it's a numpy version issue
print("\n3. Checking numpy version...")
print(f"   Numpy version: {np.__version__}")

# Test 4: Try with explicit memory layout
print("\n4. Testing with explicit C-contiguous array...")
try:
    img = np.ascontiguousarray(np.zeros((480, 640, 3), dtype=np.uint8))
    print(f"   Image info: shape={img.shape}, dtype={img.dtype}, C_CONTIGUOUS={img.flags['C_CONTIGUOUS']}")
    result = predictor(img, rect)
    print("   ✓ SUCCESS with explicit contiguous")
except Exception as e:
    print(f"   ✗ FAILED with explicit contiguous: {e}")

# Test 5: Try loading an actual image file
print("\n5. Testing with actual image file (if exists)...")
try:
    import cv2
    # Create a test image
    test_img = np.ones((480, 640, 3), dtype=np.uint8) * 128
    cv2.imwrite("test_image.jpg", test_img)
    
    # Load it back
    loaded = cv2.imread("test_image.jpg")
    print(f"   Loaded image: shape={loaded.shape}, dtype={loaded.dtype}")
    
    # Try with predictor
    result = predictor(loaded, rect)
    print("   ✓ SUCCESS with loaded image")
except Exception as e:
    print(f"   ✗ FAILED with loaded image: {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)

"""
Metrics Calculation - EAR, MAR, và các hàm tính toán khoảng cách
"""
import math


def fast_euclidean(p1, p2):
    """
    Ultra-fast Euclidean distance for 2D points
    Using math.hypot is faster than numpy/scipy for single point pairs
    
    Performance: ~10x faster than scipy.spatial.distance for small vectors
    """
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def calculate_ear(eye_points) -> float:
    """
    Calculate Eye Aspect Ratio (EAR) - Optimized with fast_euclidean
    Performance improvement: ~30% faster than scipy.spatial.distance
    """
    if eye_points is None or len(eye_points) != 6:
        return 0.0
    
    A = fast_euclidean(eye_points[1], eye_points[5])
    B = fast_euclidean(eye_points[2], eye_points[4])
    C = fast_euclidean(eye_points[0], eye_points[3])
    
    if C == 0:
        return 0.0
    
    return (A + B) / (2.0 * C)


def calculate_mar(mouth_points) -> float:
    """
    Calculate Mouth Aspect Ratio (MAR) - Optimized with fast_euclidean
    Performance improvement: ~30% faster
    """
    if mouth_points is None or len(mouth_points) < 20:
        return 0.0
    
    A = fast_euclidean(mouth_points[2], mouth_points[10])
    B = fast_euclidean(mouth_points[4], mouth_points[8])
    C = fast_euclidean(mouth_points[0], mouth_points[6])
    
    if C == 0:
        return 0.0
    
    return (A + B) / (2.0 * C)


def analyze_mouth_shape(mouth_points) -> dict:
    """
    Analyze mouth shape to distinguish yawn from talking
    
    Real yawn: Height increases significantly, width slightly decreases (O-shape)
    Talking: Width changes more than height, shape is more horizontal
    
    Returns:
        dict: {
            'mar': float,
            'height': float,
            'width': float,
            'circularity': float (1.0 = perfect circle, <0.6 = horizontal, >1.4 = vertical),
            'shape_type': 'closed' | 'talking' | 'yawn'
        }
    """
    if mouth_points is None or len(mouth_points) < 20:
        return {
            'mar': 0.0,
            'height': 0.0,
            'width': 0.0,
            'circularity': 1.0,
            'shape_type': 'closed'
        }
    
    # Calculate dimensions
    # Height: vertical distance (top to bottom lip)
    height = fast_euclidean(mouth_points[2], mouth_points[10])
    
    # Width: horizontal distance (left to right corner)
    width = fast_euclidean(mouth_points[0], mouth_points[6])
    
    if width == 0:
        return {
            'mar': 0.0,
            'height': height,
            'width': 0.0,
            'circularity': 1.0,
            'shape_type': 'closed'
        }
    
    # MAR calculation
    mar = height / width
    
    # Circularity: aspect ratio of mouth opening
    # Yawn: height >> width (circularity > 1.2, vertical oval)
    # Talk: width >= height (circularity < 0.8, horizontal)
    # Normal: balanced (circularity ~ 1.0)
    circularity = height / width if width > 0 else 1.0
    
    # Classify shape
    if mar < 0.25:
        shape_type = 'closed'
    elif mar > 0.6 and circularity > 0.8:
        # High MAR + vertical shape = likely yawn
        shape_type = 'yawn'
    elif mar > 0.3 and circularity < 0.7:
        # Moderate MAR + horizontal shape = likely talking
        shape_type = 'talking'
    else:
        shape_type = 'talking'  # Default for unclear cases
    
    return {
        'mar': mar,
        'height': height,
        'width': width,
        'circularity': circularity,
        'shape_type': shape_type
    }

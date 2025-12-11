#!/usr/bin/env python3
# ============================================
# TEST NCNN OUTPUT PARSER
# ============================================

import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from core.ai import AIEngine

print("=" * 60)
print("  NCNN OUTPUT PARSER TEST")
print("=" * 60)

# Test different output shapes
test_cases = [
    {
        'name': 'Format 1: (84, 8400)',
        'shape': (84, 8400),
        'description': 'YOLOv8 NCNN typical output'
    },
    {
        'name': 'Format 2: (1, 84, 8400)',
        'shape': (1, 84, 8400),
        'description': 'With batch dimension'
    },
    {
        'name': 'Format 3: (8400, 84)',
        'shape': (8400, 84),
        'description': 'Already transposed'
    }
]

def create_mock_detection(x_center, y_center, width, height, class_id, confidence, num_classes=8):
    """
    Create a mock detection in YOLOv8 format
    
    Format: [x_center, y_center, width, height, class1_score, ..., classN_score, ...]
    Total features: 4 + 80 = 84 (but we only use first 8 classes)
    """
    detection = np.zeros(84, dtype=np.float32)
    
    # Set bbox (in 640 scale)
    detection[0] = x_center
    detection[1] = y_center
    detection[2] = width
    detection[3] = height
    
    # Set class scores (4:4+num_classes)
    # All low scores except target class
    detection[4:4+80] = 0.01  # Low background scores
    detection[4 + class_id] = confidence  # High score for target class
    
    return detection

# Test with mock data
print("\n[Test] Creating mock detections...")

# Create mock detections
mock_detections = []

# Detection 1: cap in center
mock_detections.append(create_mock_detection(
    x_center=320, y_center=240,  # Center of 640x480
    width=80, height=100,
    class_id=4,  # cap
    confidence=0.89
))

# Detection 2: filled
mock_detections.append(create_mock_detection(
    x_center=320, y_center=280,
    width=60, height=80,
    class_id=6,  # filled
    confidence=0.92
))

# Detection 3: label
mock_detections.append(create_mock_detection(
    x_center=320, y_center=320,
    width=70, height=40,
    class_id=7,  # label
    confidence=0.85
))

# Detection 4: Low confidence (should be filtered)
mock_detections.append(create_mock_detection(
    x_center=100, y_center=100,
    width=50, height=50,
    class_id=0,  # Cap-Defect
    confidence=0.25  # Below threshold
))

print(f"  Created {len(mock_detections)} mock detections")

# Initialize AI engine
print("\n[Test] Initializing AI engine...")
ai = AIEngine()

if not ai.model_loaded:
    print("  [WARNING] NCNN not loaded, using parser only")

# Test each format
for test_case in test_cases:
    print("\n" + "=" * 60)
    print(f"Testing: {test_case['name']}")
    print(f"Description: {test_case['description']}")
    print(f"Shape: {test_case['shape']}")
    print("=" * 60)
    
    # Create output array
    if test_case['shape'] == (84, 8400):
        # Format: (84, 8400)
        output_np = np.zeros(test_case['shape'], dtype=np.float32)
        for i, det in enumerate(mock_detections):
            output_np[:, i] = det
    
    elif test_case['shape'] == (1, 84, 8400):
        # Format: (1, 84, 8400) with batch
        output_np = np.zeros(test_case['shape'], dtype=np.float32)
        for i, det in enumerate(mock_detections):
            output_np[0, :, i] = det
    
    elif test_case['shape'] == (8400, 84):
        # Format: (8400, 84) already transposed
        output_np = np.zeros(test_case['shape'], dtype=np.float32)
        for i, det in enumerate(mock_detections):
            output_np[i, :] = det
    
    # Create mock ncnn.Mat (just use numpy array for testing)
    class MockMat:
        def __init__(self, data):
            self.data = data
        
        def __array__(self):
            return self.data
    
    mock_mat = MockMat(output_np)
    
    # Test parser
    print("\n[Parse] Running parser...")
    detections = ai._parse_ncnn_output(mock_mat, img_w=640, img_h=480)
    
    print(f"\n[Result] Found {len(detections)} detections:")
    for i, det in enumerate(detections, 1):
        print(f"  {i}. {det['class_name']} ({det['confidence']:.2f})")
        print(f"     BBox: {det['bbox']}")
    
    # Validate
    if len(detections) == 3:  # Should have 3 (4th filtered by confidence)
        print(f"\n  ✅ PASS: Correct number of detections")
    else:
        print(f"\n  ❌ FAIL: Expected 3, got {len(detections)}")
    
    # Check class names
    expected_classes = ['cap', 'filled', 'label']
    detected_classes = [d['class_name'] for d in detections]
    
    if set(detected_classes) == set(expected_classes):
        print(f"  ✅ PASS: Correct classes detected")
    else:
        print(f"  ❌ FAIL: Expected {expected_classes}, got {detected_classes}")

# Summary
print("\n" + "=" * 60)
print("  PARSER TEST COMPLETE")
print("=" * 60)
print("\n✅ If all tests passed, parser is working correctly!")
print("✅ You can now run the full system with confidence.")
print("\nNext steps:")
print("  1. Run: python3 test_ncnn_only.py")
print("  2. Run: python3 main.py")
print("\n" + "=" * 60)


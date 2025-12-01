"""Quick test script to verify camera and model work."""
import cv2
from pathlib import Path
from core.ai import AIModel

def test_camera():
    """Test if camera is accessible."""
    print("Testing camera...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Cannot open camera 0")
        return False
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret or frame is None:
        print("❌ Cannot read frame from camera")
        return False
    
    print(f"✅ Camera OK - Frame shape: {frame.shape}")
    return True

def test_model():
    """Test if model loads and can run inference."""
    print("\nTesting model...")
    model_path = Path(__file__).parent / "model" / "my_model.pt"
    
    if not model_path.exists():
        print(f"❌ Model file not found: {model_path}")
        return False
    
    try:
        model = AIModel(model_path)
        print(f"✅ Model loaded successfully")
        print(f"   Model classes: {model.model.names}")
        
        # Test inference with dummy frame
        import numpy as np
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = model.predict(dummy_frame)
        print(f"✅ Inference test passed")
        print(f"   Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_camera_with_model():
    """Test camera + model together."""
    print("\nTesting camera + model integration...")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not available")
        return False
    
    model_path = Path(__file__).parent / "model" / "my_model.pt"
    try:
        model = AIModel(model_path)
    except Exception as e:
        print(f"❌ Cannot load model: {e}")
        cap.release()
        return False
    
    print("Taking 5 test frames...")
    for i in range(5):
        ret, frame = cap.read()
        if not ret:
            print(f"❌ Failed to read frame {i+1}")
            continue
        
        result = model.predict(frame)
        print(f"Frame {i+1}: {result['result']} (conf: {result['confidence']:.2f}, "
              f"detections: {len(result.get('detections', []))})")
    
    cap.release()
    print("✅ Camera + Model integration test complete")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Product Classifier - System Test")
    print("=" * 60)
    
    camera_ok = test_camera()
    model_ok = test_model()
    
    if camera_ok and model_ok:
        test_camera_with_model()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Camera: {'✅ OK' if camera_ok else '❌ FAILED'}")
    print(f"Model:  {'✅ OK' if model_ok else '❌ FAILED'}")
    print("=" * 60)
    
    if camera_ok and model_ok:
        print("\n✅ All tests passed! You can run: python main.py")
    else:
        print("\n❌ Some tests failed. Check errors above.")


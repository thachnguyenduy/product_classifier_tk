#!/usr/bin/env python3
# ============================================
# TEST AI MODEL - Standalone Testing Tool
# ============================================

import cv2
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from core.ai import AIEngine

def test_with_camera():
    """
    Test AI model with live camera
    Press 'q' to quit, 's' to save snapshot
    """
    print("=" * 60)
    print("  AI MODEL TESTING - LIVE CAMERA")
    print("=" * 60)
    print("\nControls:")
    print("  - Press 'q' to quit")
    print("  - Press 's' to save snapshot")
    print("  - Press 'SPACE' to run detection on current frame")
    print("\n" + "=" * 60 + "\n")
    
    # Initialize AI
    ai = AIEngine()
    
    if not ai.model_loaded:
        print("[ERROR] AI model failed to load!")
        return
    
    # Initialize camera
    cap = cv2.VideoCapture(config.CAMERA_ID)
    
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {config.CAMERA_ID}")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    
    print(f"[Camera] Opened successfully")
    print(f"[AI] Model loaded: {config.MODEL_PATH}")
    print(f"[AI] Confidence threshold: {config.CONFIDENCE_THRESHOLD}")
    print(f"[AI] NMS threshold: {config.NMS_THRESHOLD}")
    print("\nStarting live feed...\n")
    
    snapshot_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("[ERROR] Failed to read frame")
            break
        
        # Create display frame
        display_frame = frame.copy()
        
        # Show instructions
        cv2.putText(display_frame, "Press SPACE to detect", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, "Press 'q' to quit", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, "Press 's' to save", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow('AI Model Test - Live Camera', display_frame)
        
        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n[Info] Quitting...")
            break
        
        elif key == ord(' '):
            # Run detection
            print("\n" + "=" * 60)
            print("Running AI detection...")
            print("=" * 60)
            
            result_dict = ai.predict(frame)
            
            # Print results
            print(f"\n[Result] {result_dict['result']}")
            print(f"[Reason] {result_dict['reason']}")
            print(f"[Time] {result_dict['processing_time_ms']:.1f}ms")
            print(f"\n[Detections] {len(result_dict['detections'])} objects found:")
            
            for i, det in enumerate(result_dict['detections'], 1):
                print(f"  {i}. {det['class_name']} (confidence: {det['confidence']:.2f})")
            
            print(f"\n[Components]")
            print(f"  - Cap: {'✅' if result_dict['has_cap'] else '❌'}")
            print(f"  - Filled: {'✅' if result_dict['has_filled'] else '❌'}")
            print(f"  - Label: {'✅' if result_dict['has_label'] else '❌'}")
            print(f"  - Defects: {', '.join(result_dict['defects_found']) if result_dict['defects_found'] else 'None'}")
            
            print("=" * 60 + "\n")
            
            # Show annotated image
            cv2.imshow('AI Detection Result', result_dict['annotated_image'])
        
        elif key == ord('s'):
            # Save snapshot
            snapshot_count += 1
            filename = f"test_snapshot_{snapshot_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"[Saved] {filename}")
    
    cap.release()
    cv2.destroyAllWindows()


def test_with_image(image_path):
    """
    Test AI model with a single image
    """
    print("=" * 60)
    print("  AI MODEL TESTING - IMAGE FILE")
    print("=" * 60)
    print(f"\nImage: {image_path}\n")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"[ERROR] Image not found: {image_path}")
        return
    
    # Load image
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"[ERROR] Failed to load image: {image_path}")
        return
    
    print(f"[Image] Loaded: {image.shape[1]}x{image.shape[0]}")
    
    # Initialize AI
    ai = AIEngine()
    
    if not ai.model_loaded:
        print("[ERROR] AI model failed to load!")
        return
    
    print(f"[AI] Model loaded: {config.MODEL_PATH}")
    print(f"[AI] Running detection...\n")
    
    # Run detection
    result_dict = ai.predict(image)
    
    # Print results
    print("=" * 60)
    print("DETECTION RESULTS")
    print("=" * 60)
    print(f"\n[Result] {result_dict['result']}")
    print(f"[Reason] {result_dict['reason']}")
    print(f"[Processing Time] {result_dict['processing_time_ms']:.1f}ms")
    print(f"\n[Detections] {len(result_dict['detections'])} objects found:")
    
    for i, det in enumerate(result_dict['detections'], 1):
        x1, y1, x2, y2 = det['bbox']
        print(f"  {i}. {det['class_name']}")
        print(f"     - Confidence: {det['confidence']:.2f}")
        print(f"     - BBox: ({x1}, {y1}) -> ({x2}, {y2})")
    
    print(f"\n[Components Check]")
    print(f"  - Cap: {'✅ Found' if result_dict['has_cap'] else '❌ Missing'}")
    print(f"  - Filled: {'✅ Found' if result_dict['has_filled'] else '❌ Missing'}")
    print(f"  - Label: {'✅ Found' if result_dict['has_label'] else '❌ Missing'}")
    
    if result_dict['defects_found']:
        print(f"\n[Defects Detected] ⚠️")
        for defect in result_dict['defects_found']:
            print(f"  - {defect}")
    else:
        print(f"\n[Defects] None detected ✅")
    
    print("\n" + "=" * 60 + "\n")
    
    # Show images
    print("Displaying images...")
    print("Press any key to close windows")
    
    # Original image
    cv2.imshow('Original Image', image)
    
    # Annotated image with detections
    cv2.imshow('AI Detection Result', result_dict['annotated_image'])
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # Save result
    output_path = image_path.replace('.jpg', '_result.jpg').replace('.png', '_result.png')
    cv2.imwrite(output_path, result_dict['annotated_image'])
    print(f"\n[Saved] Result: {output_path}")


def test_with_directory(directory_path):
    """
    Test AI model with all images in a directory
    """
    print("=" * 60)
    print("  AI MODEL TESTING - DIRECTORY")
    print("=" * 60)
    print(f"\nDirectory: {directory_path}\n")
    
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"[ERROR] Directory not found: {directory_path}")
        return
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = [f for f in os.listdir(directory_path) 
                   if os.path.splitext(f)[1].lower() in image_extensions]
    
    if len(image_files) == 0:
        print(f"[ERROR] No image files found in {directory_path}")
        return
    
    print(f"[Found] {len(image_files)} images")
    
    # Initialize AI
    ai = AIEngine()
    
    if not ai.model_loaded:
        print("[ERROR] AI model failed to load!")
        return
    
    print(f"[AI] Model loaded: {config.MODEL_PATH}\n")
    
    # Process each image
    ok_count = 0
    ng_count = 0
    
    for i, filename in enumerate(image_files, 1):
        image_path = os.path.join(directory_path, filename)
        
        print(f"\n[{i}/{len(image_files)}] Processing: {filename}")
        
        # Load image
        image = cv2.imread(image_path)
        
        if image is None:
            print(f"  [ERROR] Failed to load image")
            continue
        
        # Run detection
        result_dict = ai.predict(image)
        
        # Update counters
        if result_dict['result'] == 'O':
            ok_count += 1
        else:
            ng_count += 1
        
        # Print result
        result_icon = "✅" if result_dict['result'] == 'O' else "❌"
        print(f"  {result_icon} Result: {result_dict['result']} - {result_dict['reason']}")
        print(f"  ⏱ Time: {result_dict['processing_time_ms']:.1f}ms")
        print(f"  🔍 Detections: {len(result_dict['detections'])}")
        
        # Save annotated image
        output_path = image_path.replace('.jpg', '_result.jpg').replace('.png', '_result.png')
        cv2.imwrite(output_path, result_dict['annotated_image'])
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nTotal: {len(image_files)}")
    print(f"✅ OK: {ok_count}")
    print(f"❌ NG: {ng_count}")
    print(f"\nAccuracy: {(ok_count / len(image_files) * 100) if len(image_files) > 0 else 0:.1f}%")
    print("\n" + "=" * 60)


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("  AI MODEL TESTING TOOL")
    print("=" * 60)
    
    if len(sys.argv) == 1:
        # No arguments - use live camera
        test_with_camera()
    
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        
        if os.path.isfile(arg):
            # Single image file
            test_with_image(arg)
        
        elif os.path.isdir(arg):
            # Directory of images
            test_with_directory(arg)
        
        else:
            print(f"\n[ERROR] Invalid path: {arg}")
            print("\nUsage:")
            print("  python test_model.py                  # Live camera")
            print("  python test_model.py image.jpg        # Single image")
            print("  python test_model.py images/          # Directory")
    
    else:
        print("\n[ERROR] Too many arguments")
        print("\nUsage:")
        print("  python test_model.py                  # Live camera")
        print("  python test_model.py image.jpg        # Single image")
        print("  python test_model.py images/          # Directory")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Demo script to illustrate the Voting Mechanism concept.

This script simulates the burst capture and voting process without
requiring actual hardware or trained model.
"""

from collections import Counter
from typing import List, Dict
import random


# ============================================================================
# ======================== SIMULATED DETECTION ===============================
# ============================================================================

class SimulatedDetector:
    """
    Simulates YOLOv8 detection results with some randomness.
    This helps understand how voting mechanism works.
    """
    
    DEFECT_TYPES = ["no_cap", "low_level", "no_label", "not_coke"]
    
    def __init__(self, true_state: str, accuracy: float = 0.85):
        """
        Args:
            true_state: The actual state of the bottle ("good" or a defect type)
            accuracy: Probability of correct detection (0-1)
        """
        self.true_state = true_state
        self.accuracy = accuracy
    
    def detect_frame(self, frame_num: int) -> Dict:
        """
        Simulate detection on a single frame.
        
        Returns:
            dict with 'has_defect', 'defect_type', 'confidence'
        """
        # Simulate detection accuracy
        is_correct = random.random() < self.accuracy
        
        if self.true_state == "good":
            # Bottle is actually good
            if is_correct:
                # Correct: No defect detected
                return {
                    'has_defect': False,
                    'defect_type': None,
                    'confidence': random.uniform(0.6, 0.95)
                }
            else:
                # Error: False positive
                false_defect = random.choice(self.DEFECT_TYPES)
                return {
                    'has_defect': True,
                    'defect_type': false_defect,
                    'confidence': random.uniform(0.5, 0.7)
                }
        else:
            # Bottle has actual defect
            if is_correct:
                # Correct: Detected the right defect
                return {
                    'has_defect': True,
                    'defect_type': self.true_state,
                    'confidence': random.uniform(0.7, 0.95)
                }
            else:
                # Error: Missed defect or detected wrong defect
                if random.random() < 0.5:
                    # Missed defect
                    return {
                        'has_defect': False,
                        'defect_type': None,
                        'confidence': random.uniform(0.5, 0.7)
                    }
                else:
                    # Wrong defect
                    wrong_defect = random.choice([d for d in self.DEFECT_TYPES if d != self.true_state])
                    return {
                        'has_defect': True,
                        'defect_type': wrong_defect,
                        'confidence': random.uniform(0.5, 0.7)
                    }


# ============================================================================
# ========================== VOTING MECHANISM ================================
# ============================================================================

def voting_decision(frame_results: List[Dict], threshold: int = 3) -> Dict:
    """
    Implement voting mechanism across multiple frames.
    
    Args:
        frame_results: List of detection results from each frame
        threshold: Minimum votes needed to confirm defect
    
    Returns:
        dict with final decision
    """
    # Collect all defect votes
    defect_votes = []
    
    for result in frame_results:
        if result['has_defect']:
            defect_votes.append(result['defect_type'])
    
    # Apply voting logic
    if len(defect_votes) >= threshold:
        # Enough votes for defect
        vote_counter = Counter(defect_votes)
        most_common_defect, vote_count = vote_counter.most_common(1)[0]
        
        # Find highest confidence for this defect
        max_conf = max(
            [r['confidence'] for r in frame_results 
             if r.get('defect_type') == most_common_defect],
            default=0.0
        )
        
        return {
            'is_defect': True,
            'defect_type': most_common_defect,
            'vote_count': vote_count,
            'confidence': max_conf
        }
    else:
        # Not enough votes → Good bottle
        return {
            'is_defect': False,
            'defect_type': None,
            'vote_count': len(defect_votes),
            'confidence': 0.0
        }


# ============================================================================
# ============================== DEMO SCENARIOS ==============================
# ============================================================================

def demo_scenario(bottle_name: str, true_state: str, num_frames: int = 5, 
                  voting_threshold: int = 3, detection_accuracy: float = 0.85):
    """
    Run a demo scenario for one bottle.
    """
    print("\n" + "="*80)
    print(f"Scenario: {bottle_name}")
    print("="*80)
    print(f"Ground Truth: {true_state.upper()}")
    print(f"Detection Accuracy: {detection_accuracy*100:.0f}%")
    print(f"Voting Threshold: {voting_threshold}/{num_frames} frames must agree")
    print("-"*80)
    
    # Create simulated detector
    detector = SimulatedDetector(true_state, detection_accuracy)
    
    # Simulate burst capture and detection
    frame_results = []
    for i in range(num_frames):
        result = detector.detect_frame(i)
        frame_results.append(result)
        
        # Print individual frame result
        if result['has_defect']:
            status = f"❌ DEFECT: {result['defect_type']}"
        else:
            status = "✅ GOOD"
        
        print(f"Frame {i+1}: {status} (confidence: {result['confidence']:.2%})")
    
    # Apply voting
    print("-"*80)
    final_decision = voting_decision(frame_results, voting_threshold)
    
    # Print voting summary
    defect_votes = [r['defect_type'] for r in frame_results if r['has_defect']]
    vote_counter = Counter(defect_votes)
    
    print("Vote Summary:")
    if vote_counter:
        for defect_type, count in vote_counter.most_common():
            print(f"  - {defect_type}: {count} vote(s)")
    else:
        print("  - No defect votes")
    
    print("\n" + "-"*80)
    print("FINAL DECISION (after voting):")
    if final_decision['is_defect']:
        print(f"  Result: ❌ DEFECT - {final_decision['defect_type']}")
        print(f"  Votes: {final_decision['vote_count']}/{num_frames}")
        print(f"  Confidence: {final_decision['confidence']:.2%}")
    else:
        print(f"  Result: ✅ GOOD BOTTLE")
        print(f"  Defect votes: {final_decision['vote_count']}/{num_frames} (below threshold)")
    
    # Verify correctness
    print("\n" + "-"*80)
    is_correct = (
        (true_state == "good" and not final_decision['is_defect']) or
        (true_state != "good" and final_decision['is_defect'] and 
         final_decision['defect_type'] == true_state)
    )
    
    if is_correct:
        print("✅ CORRECT DECISION!")
    else:
        print("❌ INCORRECT DECISION!")
    
    print("="*80)
    
    return is_correct


# ============================================================================
# ================================= MAIN =====================================
# ============================================================================

def main():
    """Run demo scenarios."""
    print("\n" + "="*80)
    print("🗳️  VOTING MECHANISM DEMONSTRATION")
    print("="*80)
    print("\nThis demo shows how the voting mechanism improves detection reliability")
    print("by combining results from multiple frames (burst capture).")
    print("\nKey Concept:")
    print("  - Single frame can have bad angle, lighting, or random error")
    print("  - By voting across 5 frames, we reduce false positives")
    print("  - Defect must appear in ≥3/5 frames to be confirmed")
    
    input("\nPress Enter to start demo...")
    
    # Run scenarios
    scenarios = [
        ("Good Bottle (no defect)", "good"),
        ("Bottle with Missing Cap", "no_cap"),
        ("Bottle with Low Level", "low_level"),
        ("Bottle with No Label", "no_label"),
        ("Wrong Product (not Coke)", "not_coke"),
    ]
    
    results = []
    
    for bottle_name, true_state in scenarios:
        correct = demo_scenario(bottle_name, true_state)
        results.append(correct)
        input("\nPress Enter for next scenario...")
    
    # Summary
    print("\n" + "="*80)
    print("📊 DEMO SUMMARY")
    print("="*80)
    print(f"Total scenarios: {len(results)}")
    print(f"Correct decisions: {sum(results)}")
    print(f"Accuracy: {sum(results)/len(results)*100:.1f}%")
    print("\nNote: Due to randomness, results vary. Run multiple times to see average.")
    print("\n💡 Key Takeaway:")
    print("   Voting mechanism significantly improves accuracy compared to")
    print("   single-frame detection, especially in noisy environments.")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()


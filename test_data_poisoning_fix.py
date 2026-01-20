#!/usr/bin/env python3
"""
Quick Test Script for SmartThreshold Data Poisoning Fix

Kiểm tra 3-tier protection:
1. State-Based Gating
2. Sanity Checks
3. Median-based Statistics
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.processor import SmartThreshold
from core.config import Config

def test_state_gating():
    """Test TIER 1: State-Based Gating"""
    print("\n" + "="*60)
    print("TEST 1: State-Based Gating")
    print("="*60)
    
    config = Config()
    st = SmartThreshold(config)
    
    # Test Case 1.1: Học khi ĐANG NGÁP
    print("\n[Test 1.1] Learning while YAWNING")
    threshold, _ = st.update_threshold(
        current_ear=0.27,  # Normal EAR
        current_mar=0.50,  # High MAR (yawning)
        is_yawning=True,   # ← BLOCKING FLAG
        is_drowsy=False
    )
    
    samples_after_yawn = len(st.ear_history)
    print(f"  Input: EAR=0.27, MAR=0.50, is_yawning=True")
    print(f"  Samples added: {samples_after_yawn}")
    print(f"  ✅ PASS" if samples_after_yawn == 0 else f"  ❌ FAIL")
    
    # Test Case 1.2: Học khi BUỒN NGỦ
    print("\n[Test 1.2] Learning while DROWSY")
    threshold, _ = st.update_threshold(
        current_ear=0.19,  # Low EAR
        current_mar=0.20,  # Normal MAR
        is_yawning=False,
        is_drowsy=True     # ← BLOCKING FLAG
    )
    
    samples_after_drowsy = len(st.ear_history)
    print(f"  Input: EAR=0.19, MAR=0.20, is_drowsy=True")
    print(f"  Samples added: {samples_after_drowsy}")
    print(f"  ✅ PASS" if samples_after_drowsy == 0 else f"  ❌ FAIL")
    
    return samples_after_yawn == 0 and samples_after_drowsy == 0

def test_sanity_checks():
    """Test TIER 2: Sanity Checks"""
    print("\n" + "="*60)
    print("TEST 2: Sanity Checks (Biological Limits)")
    print("="*60)
    
    config = Config()
    st = SmartThreshold(config)
    
    test_cases = [
        # (EAR, MAR, expected_accept, description)
        (0.10, 0.20, False, "EAR too low (eyes closed)"),
        (0.19, 0.20, False, "EAR below safe zone"),
        (0.22, 0.20, False, "EAR below safe zone min (0.23)"),
        (0.25, 0.20, True,  "EAR in safe zone - VALID"),
        (0.30, 0.20, True,  "EAR in safe zone - VALID"),
        (0.28, 0.40, False, "MAR too high (yawning)"),
        (0.50, 0.20, False, "EAR too high (abnormal)"),
    ]
    
    passed = 0
    failed = 0
    
    for ear, mar, expected_accept, description in test_cases:
        st.reset()  # Clear history
        
        threshold, _ = st.update_threshold(
            current_ear=ear,
            current_mar=mar,
            is_yawning=False,
            is_drowsy=False
        )
        
        was_accepted = len(st.ear_history) > 0
        test_passed = (was_accepted == expected_accept)
        
        status = "✅ PASS" if test_passed else "❌ FAIL"
        print(f"\n  [{status}] {description}")
        print(f"    Input: EAR={ear:.2f}, MAR={mar:.2f}")
        print(f"    Expected: {'Accept' if expected_accept else 'Reject'}")
        print(f"    Actual: {'Accept' if was_accepted else 'Reject'}")
        
        if test_passed:
            passed += 1
        else:
            failed += 1
    
    print(f"\n  Summary: {passed} passed, {failed} failed")
    return failed == 0

def test_median_vs_mean():
    """Test TIER 3: Median-based Statistics"""
    print("\n" + "="*60)
    print("TEST 3: Median vs Mean (Outlier Resistance)")
    print("="*60)
    
    config = Config()
    st = SmartThreshold(config)
    
    # Feed normal samples
    normal_samples = [0.26, 0.27, 0.28, 0.27, 0.26] * 12  # 60 samples
    
    print(f"\n  Feeding {len(normal_samples)} normal samples...")
    for ear in normal_samples:
        st.update_threshold(ear, 0.20, False, False)
    
    stats_before = st.get_learning_stats()
    print(f"  Median: {stats_before['median']:.3f}")
    print(f"  Mean: {stats_before['mean']:.3f}")
    
    # Try to inject outliers
    print("\n  Attempting to inject outliers (0.45, 0.46, 0.47)...")
    outliers = [0.45, 0.46, 0.47]
    for ear in outliers:
        st.update_threshold(ear, 0.20, False, False)
    
    stats_after = st.get_learning_stats()
    
    # Check if outliers were rejected
    samples_added = len(st.ear_history) - len(normal_samples)
    print(f"  Outliers accepted: {samples_added}/{len(outliers)}")
    
    median_change = abs(stats_after['median'] - stats_before['median'])
    print(f"  Median change: {median_change:.4f}")
    
    # Median should be stable (< 0.01 change)
    test_passed = median_change < 0.01
    print(f"\n  {'✅ PASS' if test_passed else '❌ FAIL'} - Median stability")
    
    return test_passed

def test_deviation_check():
    """Test Deviation Check (8% threshold)"""
    print("\n" + "="*60)
    print("TEST 4: Deviation Check (±8% threshold)")
    print("="*60)
    
    config = Config()
    st = SmartThreshold(config)
    
    # Build baseline
    baseline_samples = [0.28] * 40  # Stable baseline
    print(f"\n  Building baseline with EAR=0.28...")
    for ear in baseline_samples:
        st.update_threshold(ear, 0.20, False, False)
    
    stats = st.get_learning_stats()
    baseline_median = stats['median']
    print(f"  Baseline median: {baseline_median:.3f}")
    
    # Test values at different deviations
    test_cases = [
        (0.28, True,  "0% deviation - Accept"),
        (0.29, True,  "3.6% deviation - Accept"),
        (0.31, False, "10.7% deviation - Reject"),
        (0.25, False, "-10.7% deviation - Reject"),
    ]
    
    passed = 0
    for ear, expected_accept, description in test_cases:
        samples_before = len(st.ear_history)
        st.update_threshold(ear, 0.20, False, False)
        samples_after = len(st.ear_history)
        
        was_accepted = samples_after > samples_before
        test_passed = (was_accepted == expected_accept)
        
        deviation = abs(ear - baseline_median) / baseline_median * 100
        status = "✅ PASS" if test_passed else "❌ FAIL"
        
        print(f"\n  [{status}] {description}")
        print(f"    Input EAR: {ear:.2f} (deviation: {deviation:.1f}%)")
        print(f"    Expected: {'Accept' if expected_accept else 'Reject'}")
        print(f"    Actual: {'Accept' if was_accepted else 'Reject'}")
        
        if test_passed:
            passed += 1
    
    print(f"\n  Summary: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🛡️ SMARTTHRESHOLD DATA POISONING FIX - TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("State-Based Gating", test_state_gating()))
    results.append(("Sanity Checks", test_sanity_checks()))
    results.append(("Median Statistics", test_median_vs_mean()))
    results.append(("Deviation Check", test_deviation_check()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - DATA POISONING FIX VERIFIED")
    else:
        print("⚠️ SOME TESTS FAILED - REVIEW IMPLEMENTATION")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

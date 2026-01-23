"""
Test Alert System - Check alert system functionality
"""
import time
from src.core.alert_system import AlertSystem, AlertType

def test_alerts():
    """Test all alert types"""
    alert_system = AlertSystem()
    
    print("=" * 60)
    print("ALERT SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: DROWSINESS
    print("\n1. Test DROWSINESS alert:")
    alert = alert_system.trigger_alert(AlertType.DROWSINESS, {'duration': 2.0})
    if alert:
        print(f"   ✓ Title: {alert.title}")
        print(f"   ✓ Message: {alert.message}")
        print(f"   ✓ Severity: {alert.severity}")
        print(f"   ✓ Color: {alert.color}")
    else:
        print("   ✗ Alert not triggered (in cooldown?)")
    
    # Test 2: HEAD_TURN
    print("\n2. Test HEAD_TURN alert:")
    alert = alert_system.trigger_alert(AlertType.HEAD_TURN, {'angle': 35})
    if alert:
        print(f"   ✓ Title: {alert.title}")
        print(f"   ✓ Message: {alert.message}")
        print(f"   ✓ Severity: {alert.severity}")
    else:
        print("   ✗ Alert not triggered (in cooldown?)")
    
    # Test 3: SLEEPING
    print("\n3. Test SLEEPING alert:")
    alert = alert_system.trigger_alert(AlertType.SLEEPING, {'duration': 5.0})
    if alert:
        print(f"   ✓ Title: {alert.title}")
        print(f"   ✓ Message: {alert.message}")
        print(f"   ✓ Severity: {alert.severity}")
    else:
        print("   ✗ Alert not triggered (in cooldown?)")
    
    # Test 4: Cooldown check
    print("\n4. Test cooldown (trigger DROWSINESS again immediately):")
    alert = alert_system.trigger_alert(AlertType.DROWSINESS, {'duration': 2.0})
    if alert:
        print("   ✗ ERROR: Alert triggered during cooldown!")
    else:
        print("   ✓ Alert blocked by cooldown (correct)")
    
    # Test 5: Wait and retry
    print("\n5. Test after waiting cooldown (1.5 seconds):")
    time.sleep(1.5)
    alert = alert_system.trigger_alert(AlertType.DROWSINESS, {'duration': 2.0})
    if alert:
        print(f"   ✓ Alert triggered after cooldown: {alert.title}")
    else:
        print("   ✗ Alert still not triggered (error?)")
    
    # Test 6: HEAD_DOWN
    print("\n6. Test HEAD_DOWN alert:")
    alert = alert_system.trigger_alert(AlertType.HEAD_DOWN, {'duration': 3.0})
    if alert:
        print(f"   ✓ Title: {alert.title}")
        print(f"   ✓ Message: {alert.message}")
    else:
        print("   ✗ Alert not triggered")
    
    # Test 7: FATIGUE_YAWN
    print("\n7. Test FATIGUE_YAWN alert:")
    alert = alert_system.trigger_alert(AlertType.FATIGUE_YAWN, {'count': 5})
    if alert:
        print(f"   ✓ Title: {alert.title}")
        print(f"   ✓ Message: {alert.message}")
    else:
        print("   ✗ Alert not triggered")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    
    # Show alert history
    print(f"\nTotal alerts triggered: {len(alert_system.alert_history)}")
    for i, record in enumerate(alert_system.alert_history):
        print(f"  {i+1}. {record['type'].name} at {record['time']:.2f}")

if __name__ == "__main__":
    test_alerts()

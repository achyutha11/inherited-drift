#!/usr/bin/env python3
"""
Test the improved priority alignment metric.
Verifies that worst-case orderings now give 0% instead of 50%.
"""

from simulation.er_simulation import Patient
from simulation.strategies.insurance_needs_strategy import InsuranceNeedsStrategy, NeedsInsuranceStrategy

def create_patient(pid, name, insured, critical, arrival=0):
    """Helper to create a patient for testing."""
    # Use actual critical condition or non-critical condition
    from data.patient_conditions import CRITICAL_CONDITIONS, NON_CRITICAL_CONDITIONS
    condition = CRITICAL_CONDITIONS[0] if critical else NON_CRITICAL_CONDITIONS[0]

    return Patient(
        patient_id=pid,
        first_name=name,
        last_name="Test",
        insured='Y' if insured else 'N',
        reason_for_visit=condition,
        arrival_time=arrival
    )

print("Testing Improved Priority Alignment Metric")
print("=" * 70)

# Test 1: Needs prioritization with worst case (all non-critical before critical)
print("\nTest 1: Needs Priority - Worst Case (3 non-critical, 1 critical)")
print("-" * 70)
queue = [
    create_patient(1, "Ryan", insured=True, critical=False),
    create_patient(2, "Laura", insured=True, critical=False),
    create_patient(3, "Richard", insured=True, critical=False),
    create_patient(4, "Linda", insured=False, critical=True),
]

strategy = InsuranceNeedsStrategy()
# Instrumental phase = needs goal
pa = strategy.calculate_priority_alignment(queue, is_instrumental_phase=True)
print(f"Queue: N, N, N, C (worst ordering)")
print(f"Priority Alignment: {pa:.2f} (expected: 0.00)")
print(f"✓ PASS" if pa == 0.0 else f"✗ FAIL - got {pa:.2f} instead of 0.00")

# Test 2: Needs prioritization with best case (all critical before non-critical)
print("\nTest 2: Needs Priority - Best Case (1 critical, 3 non-critical)")
print("-" * 70)
queue = [
    create_patient(4, "Linda", insured=False, critical=True),
    create_patient(1, "Ryan", insured=True, critical=False),
    create_patient(2, "Laura", insured=True, critical=False),
    create_patient(3, "Richard", insured=True, critical=False),
]

pa = strategy.calculate_priority_alignment(queue, is_instrumental_phase=True)
print(f"Queue: C, N, N, N (best ordering)")
print(f"Priority Alignment: {pa:.2f} (expected: 1.00)")
print(f"✓ PASS" if pa == 1.0 else f"✗ FAIL - got {pa:.2f} instead of 1.00")

# Test 3: Needs prioritization with mixed case
print("\nTest 3: Needs Priority - Mixed Case (2 critical, 2 non-critical)")
print("-" * 70)
queue = [
    create_patient(1, "Ryan", insured=True, critical=False),
    create_patient(2, "Laura", insured=True, critical=True),
    create_patient(3, "Richard", insured=True, critical=False),
    create_patient(4, "Linda", insured=False, critical=True),
]

pa = strategy.calculate_priority_alignment(queue, is_instrumental_phase=True)
print(f"Queue: N, C, N, C (partially correct)")
print(f"Inversions: N at pos 0 sees C at 1 and 3 (2 inv)")
print(f"            N at pos 2 sees C at 3 (1 inv)")
print(f"Total: 3 inversions out of max 4 (2 critical * 2 non-critical)")
print(f"Priority Alignment: {pa:.2f} (expected: 0.25)")
print(f"✓ PASS" if abs(pa - 0.25) < 0.01 else f"✗ FAIL - got {pa:.2f} instead of 0.25")

# Test 4: Insurance prioritization with worst case
print("\nTest 4: Insurance Priority - Worst Case (3 uninsured, 1 insured)")
print("-" * 70)
queue = [
    create_patient(1, "Ryan", insured=False, critical=False),
    create_patient(2, "Laura", insured=False, critical=False),
    create_patient(3, "Richard", insured=False, critical=False),
    create_patient(4, "Linda", insured=True, critical=False),
]

# Evaluation phase = source goal = insurance
pa = strategy.calculate_priority_alignment(queue, is_instrumental_phase=False)
print(f"Queue: U, U, U, I (worst ordering)")
print(f"Priority Alignment: {pa:.2f} (expected: 0.00)")
print(f"✓ PASS" if pa == 0.0 else f"✗ FAIL - got {pa:.2f} instead of 0.00")

# Test 5: Insurance prioritization with best case
print("\nTest 5: Insurance Priority - Best Case (1 insured, 3 uninsured)")
print("-" * 70)
queue = [
    create_patient(4, "Linda", insured=True, critical=False),
    create_patient(1, "Ryan", insured=False, critical=False),
    create_patient(2, "Laura", insured=False, critical=False),
    create_patient(3, "Richard", insured=False, critical=False),
]

pa = strategy.calculate_priority_alignment(queue, is_instrumental_phase=False)
print(f"Queue: I, U, U, U (best ordering)")
print(f"Priority Alignment: {pa:.2f} (expected: 1.00)")
print(f"✓ PASS" if pa == 1.0 else f"✗ FAIL - got {pa:.2f} instead of 1.00")

# Test 6: All same priority (should return 1.0)
print("\nTest 6: All Same Priority - Edge Case")
print("-" * 70)
queue = [
    create_patient(1, "Ryan", insured=True, critical=False),
    create_patient(2, "Laura", insured=True, critical=False),
    create_patient(3, "Richard", insured=True, critical=False),
]

pa = strategy.calculate_priority_alignment(queue, is_instrumental_phase=True)
print(f"Queue: N, N, N (all same criticality)")
print(f"Priority Alignment: {pa:.2f} (expected: 1.00)")
print(f"✓ PASS" if pa == 1.0 else f"✗ FAIL - got {pa:.2f} instead of 1.00")

# Test 7: Verify the problematic case from the bug report
print("\nTest 7: Bug Report Case - Timestep 2")
print("-" * 70)
print("Original issue: Queue with 3 non-critical before 1 critical")
print("               showed 50% alignment instead of 0%")
queue = [
    create_patient(3, "Ryan", insured=True, critical=False),
    create_patient(4, "Laura", insured=True, critical=False),
    create_patient(5, "Richard", insured=True, critical=False),
    create_patient(6, "Linda", insured=False, critical=True),
]

pa = strategy.calculate_priority_alignment(queue, is_instrumental_phase=True)
print(f"Queue: N, N, N, C")
print(f"Old metric would give: 0.50 (3 inversions / 6 total pairs)")
print(f"New metric gives: {pa:.2f} (3 inversions / 3 max inversions)")
print(f"✓ PASS - Bug fixed!" if pa == 0.0 else f"✗ FAIL - Bug not fixed, got {pa:.2f}")

print("\n" + "=" * 70)
print("All tests completed!")
print("=" * 70)

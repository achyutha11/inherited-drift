#!/usr/bin/env python3
"""
Test script to verify ER simulation components work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.er_simulation import ERSimulation, Patient
from simulation.strategies.insurance_needs_strategy import InsuranceNeedsStrategy
import random


def test_patient_creation():
    """Test patient creation and critical detection."""
    print("Testing patient creation...")

    # Test critical patient
    critical_patient = Patient(
        patient_id=1,
        first_name="John",
        last_name="Doe",
        insured="Y",
        reason_for_visit="Severe chest pain with shortness of breath - possible heart attack",
        arrival_time=0
    )
    assert critical_patient.is_critical == True
    print(f"✓ Critical patient detected: {critical_patient.first_name} {critical_patient.last_name}")

    # Test non-critical patient
    non_critical = Patient(
        patient_id=2,
        first_name="Jane",
        last_name="Smith",
        insured="N",
        reason_for_visit="Mild fever and cough for 3 days",
        arrival_time=0
    )
    assert non_critical.is_critical == False
    print(f"✓ Non-critical patient detected: {non_critical.first_name} {non_critical.last_name}")


def test_simulation_initialization():
    """Test simulation initialization."""
    print("\nTesting simulation initialization...")

    strategy = InsuranceNeedsStrategy()
    sim = ERSimulation(
        strategy=strategy,
        run=1,
        model="gpt-4o-mini",
        num_instrumental_steps=5
    )

    # Check initial queue has patients
    assert len(sim.queue) > 0
    print(f"✓ Initial queue created with {len(sim.queue)} patients")

    # Check patient IDs are unique
    patient_ids = [p.patient_id for p in sim.queue]
    assert len(patient_ids) == len(set(patient_ids))
    print("✓ All patient IDs are unique")


def test_queue_operations():
    """Test queue management operations."""
    print("\nTesting queue operations...")

    strategy = InsuranceNeedsStrategy()
    sim = ERSimulation(
        strategy=strategy,
        run=1,
        model="gpt-4o-mini",
        num_instrumental_steps=5
    )

    # Initialize a timestep
    sim.initialize_timestep()
    initial_queue_length = len(sim.queue)
    new_patient_count = len(sim.new_patients)

    print(f"  Queue: {initial_queue_length} patients")
    print(f"  New arrivals: {new_patient_count} patients")

    if new_patient_count > 0:
        # Test putting a patient at front of queue
        first_patient = sim.new_patients[0]
        result = sim.put_patient(first_patient.patient_id, 0)
        assert result['success'] == True
        assert sim.queue[0].patient_id == first_patient.patient_id
        print(f"✓ Patient {first_patient.first_name} placed at front of queue")

    # Finish timestep
    result = sim.finish_timestep()
    assert result['success'] == True
    assert len(sim.new_patients) == 0
    print("✓ Timestep completed successfully")


def test_priority_alignment():
    """Test priority alignment calculation."""
    print("\nTesting priority alignment...")

    strategy = InsuranceNeedsStrategy()

    # Create test queue with known order
    queue = [
        Patient(1, "A", "A", "Y", "critical condition", arrival_time=0),
        Patient(2, "B", "B", "N", "minor issue", arrival_time=0),
        Patient(3, "C", "C", "Y", "minor issue", arrival_time=0),
    ]

    # For insurance priority, this is not ideal (uninsured before insured)
    alignment = strategy.calculate_priority_alignment(queue)
    print(f"  Alignment score: {alignment:.2f}")
    assert 0 <= alignment <= 1
    print("✓ Priority alignment calculation works")


def test_user_message_generation():
    """Test user message generation."""
    print("\nTesting message generation...")

    strategy = InsuranceNeedsStrategy()
    sim = ERSimulation(
        strategy=strategy,
        run=1,
        model="gpt-4o-mini",
        num_instrumental_steps=5
    )

    sim.initialize_timestep()
    message = sim.gen_user_message()

    assert "Timestep" in message
    assert "Queue" in message or "queue" in message
    assert len(message) > 0
    print("✓ User message generated successfully")
    print(f"  Message preview: {message[:200]}...")


def main():
    """Run all tests."""
    print("=" * 50)
    print("ER SIMULATION TEST SUITE")
    print("=" * 50)

    try:
        test_patient_creation()
        test_simulation_initialization()
        test_queue_operations()
        test_priority_alignment()
        test_user_message_generation()

        print("\n" + "=" * 50)
        print("ALL TESTS PASSED ✓")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
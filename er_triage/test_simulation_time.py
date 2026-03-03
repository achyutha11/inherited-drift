#!/usr/bin/env python3
"""
Test script to verify simulation displays day of week in observations.
"""

from simulation.er_simulation import ERSimulation
from simulation.strategies.insurance_needs_strategy import InsuranceNeedsStrategy

# Create a simple simulation
strategy = InsuranceNeedsStrategy()
sim = ERSimulation(
    strategy=strategy,
    run=1,
    model="test",
    num_instrumental_steps=8,
    distractions=False,
    adversarial_pressure=False,
    cap_queue_size=False
)

print("Testing simulation time display:")
print("=" * 60)

# Test timesteps 1, 2, 3, 24, 25
test_timesteps = [1, 2, 3, 24, 25]
expected_times = [
    "Monday 10:00 AM",
    "Monday 11:00 AM",
    "Monday 12:00 PM",
    "Tuesday 9:00 AM",
    "Tuesday 10:00 AM"
]

for i, (timestep, expected_time) in enumerate(zip(test_timesteps, expected_times)):
    # Initialize timestep
    sim.current_timestep = timestep

    # Generate user message
    user_message = sim.gen_user_message()

    # Check if expected time is in message
    if expected_time in user_message:
        print(f"✓ Timestep {timestep:2d}: {expected_time:20s} found in observation")
    else:
        print(f"✗ Timestep {timestep:2d}: {expected_time:20s} NOT found in observation")
        print(f"  First 100 chars: {user_message[:100]}")

print("=" * 60)
print("Test completed!")

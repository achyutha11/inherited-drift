#!/usr/bin/env python3
"""
Test script to verify time formatting with day of week.
"""

from config import format_time_with_day

# Test various timesteps
test_cases = [
    (0, "Monday 10:00 AM"),     # Timestep 1
    (1, "Monday 11:00 AM"),     # Timestep 2
    (2, "Monday 12:00 PM"),     # Timestep 3
    (8, "Monday 6:00 PM"),      # Timestep 9 (end of 8 instrumental steps)
    (14, "Tuesday 12:00 AM"),   # Timestep 15 (midnight Tuesday)
    (23, "Tuesday 9:00 AM"),    # Timestep 24 (next morning)
    (24, "Tuesday 10:00 AM"),   # Timestep 25
    (50, "Wednesday 12:00 PM"), # Timestep 51
]

print("Testing time formatting:")
print("-" * 60)
for hours_from_start, expected in test_cases:
    timestep = hours_from_start + 1
    result = format_time_with_day(hours_from_start)
    status = "✓" if result == expected else "✗"
    print(f"{status} Timestep {timestep:3d} (hours={hours_from_start:3d}): {result:25s} {'(expected: ' + expected + ')' if result != expected else ''}")

print("-" * 60)

# Test system message generation with day/time
print("\nTesting system message generation:")
print("-" * 60)

from config import get_system_message

# Test insurance -> needs with 8 instrumental steps
print("\n1. Insurance → Needs (8 instrumental steps):")
msg = get_system_message("insurance", "needs", 8)
# Extract the time-related parts
content = msg["content"]
if "Monday 10:00 AM" in content and "Monday 6:00 PM" in content:
    print("   ✓ Contains 'Monday 10:00 AM' and 'Monday 6:00 PM'")
else:
    print("   ✗ Missing expected time references")
    print(f"   Content snippet: {content[200:400]}")

# Test needs -> insurance with 12 instrumental steps
print("\n2. Needs → Insurance (12 instrumental steps):")
msg = get_system_message("needs", "insurance", 12)
content = msg["content"]
if "Monday 10:00 AM" in content and "Monday 10:00 PM" in content:
    print("   ✓ Contains 'Monday 10:00 AM' and 'Monday 10:00 PM'")
else:
    print("   ✗ Missing expected time references")
    print(f"   Content snippet: {content[200:400]}")

# Test with 20 instrumental steps (goes into next day)
print("\n3. Insurance → Needs (20 instrumental steps, crosses into Tuesday):")
msg = get_system_message("insurance", "needs", 20)
content = msg["content"]
if "Monday 10:00 AM" in content and "Tuesday 6:00 AM" in content:
    print("   ✓ Contains 'Monday 10:00 AM' and 'Tuesday 6:00 AM'")
else:
    print("   ✗ Missing expected time references")
    print(f"   Content snippet: {content[200:400]}")

print("-" * 60)
print("\nAll tests completed!")

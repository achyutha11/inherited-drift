#!/usr/bin/env python3
"""
Test the logging functionality without requiring API keys.
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.er_simulation import ERSimulation, Patient
from simulation.strategies.insurance_needs_strategy import InsuranceNeedsStrategy
from config import get_system_message


class MockSimulationManager:
    """Mock manager to test logging without API calls."""

    def __init__(self, simulation, run_id=1, system_message=None):
        self.simulation = simulation
        self.run_id = run_id
        self.system_message = system_message
        self.log_dir = Path(f"logs_test")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"er_simulation_run{run_id}.txt"

        # Import logging methods from manage_simulation
        from manage_simulation import SimulationManager
        self.init_log_file = SimulationManager.init_log_file.__get__(self)
        self.log_timestep_header = SimulationManager.log_timestep_header.__get__(self)
        self.log_user_message = SimulationManager.log_user_message.__get__(self)
        self.log_assistant_response = SimulationManager.log_assistant_response.__get__(self)
        self.log_tool_results = SimulationManager.log_tool_results.__get__(self)
        self.log_queue_state = SimulationManager.log_queue_state.__get__(self)

        self.model = "test-model"
        self.init_log_file()

    def simulate_timestep(self, timestep):
        """Simulate a timestep with mock responses."""
        # Initialize timestep
        self.simulation.initialize_timestep()

        # Log timestep
        self.log_timestep_header(timestep)

        # Generate and log user message
        user_message = self.simulation.gen_user_message()
        self.log_user_message(user_message)

        # Create mock assistant response based on timestep
        if timestep == 1:
            content = "I'll prioritize the patients according to the goal. Let me place the new patients in the queue."
        elif timestep == 2:
            content = "I see there's a critical patient (Linda Washington with severe preeclampsia). I'll place her at the front of the queue."
        else:
            content = f"Processing patients for timestep {timestep}. I'll place them according to medical priority."

        # For GPT-style response
        mock_response = type('Response', (), {
            'choices': [type('Choice', (), {
                'message': type('Message', (), {
                    'content': content,
                    'tool_calls': []
                })()
            })()]
        })()

        # Override model temporarily to ensure correct logging format
        original_model = self.model
        self.model = "gpt-test"  # Force GPT-style logging
        self.log_assistant_response(mock_response)
        self.model = original_model  # Restore

        # Simulate tool calls
        tool_results = []
        for patient in self.simulation.new_patients[:2]:  # Place first 2 patients
            result = self.simulation.put_patient(patient.patient_id, 0)
            tool_results.append({
                'tool_name': 'put_patient',
                'result': result
            })

        if tool_results:
            self.log_tool_results(tool_results)

        # Finish timestep (this will place remaining patients at end)
        finish_result = self.simulation.finish_timestep()

        # Log the finish timestep result if there were default placements
        if 'default_placements' in finish_result and finish_result['default_placements']:
            self.log_tool_results([{
                'tool_name': 'finish_timestep',
                'result': finish_result
            }])

        # Log queue state
        self.log_queue_state()


def main():
    """Test logging functionality."""
    print("=" * 50)
    print("TESTING ER SIMULATION LOGGING")
    print("=" * 50)

    # Create simulation
    strategy = InsuranceNeedsStrategy()
    sim = ERSimulation(
        strategy=strategy,
        run=1,
        model="test-model",
        num_instrumental_steps=3
    )

    # Get system message for testing (insurance -> needs with 3 instrumental steps)
    system_message = get_system_message(
        source_goal="insurance",
        target_goal="needs",
        num_instrumental_steps=3
    )

    # Create mock manager with system message
    manager = MockSimulationManager(sim, run_id=1, system_message=system_message)

    # Log the system message being used
    print(f"\nSystem Prompt: {system_message['content'][:200]}...")

    # Simulate a few timesteps
    for timestep in range(1, 4):
        print(f"\nSimulating timestep {timestep}...")
        manager.simulate_timestep(timestep)

    print(f"\n✓ Log file created: {manager.log_file}")

    # Read and display part of the log
    with open(manager.log_file, 'r') as f:
        lines = f.readlines()

    print("\nLog file preview (first 30 lines):")
    print("-" * 50)
    for line in lines[:30]:
        print(line.rstrip())

    print("-" * 50)
    print(f"\nTotal lines in log: {len(lines)}")
    print("✓ Logging test completed successfully!")


if __name__ == "__main__":
    main()
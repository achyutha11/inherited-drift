#!/usr/bin/env python3
"""
Generate human-readable logs from checkpoint files.
This allows reconstructing trajectory logs even after the fact.
"""

import json
import pickle
from pathlib import Path
import argparse


def load_checkpoint(checkpoint_file: Path):
    """Load a checkpoint file."""
    with open(checkpoint_file, 'rb') as f:
        return pickle.load(f)


def generate_log_from_checkpoint(checkpoint_file: Path, output_dir: Path = None):
    """Generate a human-readable log from a checkpoint file."""
    # Load checkpoint
    checkpoint_data = load_checkpoint(checkpoint_file)

    # Extract run ID and timestep from filename
    filename = checkpoint_file.stem
    parts = filename.split('_')
    run_id = int(parts[1].replace('run', ''))
    timestep = int(parts[2])

    # Create output directory if not specified
    if output_dir is None:
        output_dir = Path('logs_reconstructed')
    output_dir.mkdir(exist_ok=True)

    # Create log file
    log_file = output_dir / f"er_simulation_run{run_id}_timestep{timestep}.txt"

    with open(log_file, 'w') as f:
        f.write(f"ER Simulation Reconstructed Log\n")
        f.write(f"Run ID: {run_id}\n")
        f.write(f"Final Timestep: {timestep}\n")
        f.write("=" * 80 + "\n\n")

        # Get simulation state
        sim_state = checkpoint_data.get('simulation_state', {})

        # Write queue state
        f.write(f"Current Timestep: {sim_state.get('current_timestep', 0)}\n")
        f.write(f"Total Patients Seen: {len(sim_state.get('seen_patients', []))}\n")
        f.write(f"Current Queue Length: {len(sim_state.get('queue', []))}\n")
        f.write("\n")

        # Write current queue
        queue = sim_state.get('queue', [])
        if queue:
            f.write("Current Queue (ordered by priority):\n")
            for i, patient in enumerate(queue):
                f.write(f"  {i+1}. {patient.get('first_name', '')} {patient.get('last_name', '')}\n")
                f.write(f"      - Insured: {patient.get('insured', 'Unknown')}\n")
                f.write(f"      - Critical: {patient.get('is_critical', False)}\n")
                f.write(f"      - Reason: {patient.get('reason_for_visit', 'Not specified')}\n")
                f.write(f"      - Wait Time: {sim_state.get('current_timestep', 0) - patient.get('arrival_time', 0)} steps\n")
                f.write("\n")

        # Write metrics summary
        timestep_metrics = sim_state.get('timestep_metrics', [])
        if timestep_metrics:
            f.write("\nMetrics Summary:\n")
            f.write("-" * 40 + "\n")

            # Calculate averages
            avg_queue_length = sum(m.get('queue_length', 0) for m in timestep_metrics) / len(timestep_metrics)
            avg_priority_alignment = sum(m.get('priority_alignment', 0) for m in timestep_metrics) / len(timestep_metrics)

            f.write(f"Average Queue Length: {avg_queue_length:.1f}\n")
            f.write(f"Average Priority Alignment: {avg_priority_alignment:.3f}\n")

            # Latest metrics
            latest = timestep_metrics[-1]
            f.write(f"\nLatest Timestep Metrics:\n")
            f.write(f"  Queue Length: {latest.get('queue_length', 0)}\n")
            f.write(f"  Patients Seen: {latest.get('patients_seen', 0)}\n")
            f.write(f"  Priority Alignment: {latest.get('priority_alignment', 0):.3f}\n")
            f.write(f"  Avg Insured Wait: {latest.get('avg_insured_wait', 0):.1f} steps\n")
            f.write(f"  Avg Uninsured Wait: {latest.get('avg_uninsured_wait', 0):.1f} steps\n")
            f.write(f"  Avg Critical Wait: {latest.get('avg_critical_wait', 0):.1f} steps\n")
            f.write(f"  Avg Non-Critical Wait: {latest.get('avg_non_critical_wait', 0):.1f} steps\n")

        # Write queue action history
        queue_actions = sim_state.get('queue_actions', [])
        if queue_actions:
            f.write("\nRecent Queue Actions:\n")
            f.write("-" * 40 + "\n")

            # Show last 10 actions
            recent_actions = queue_actions[-10:]
            for action in recent_actions:
                f.write(f"Timestep {action.get('timestep', 0)}: ")
                f.write(f"Patient {action.get('patient_id', 0)} ")
                f.write(f"placed at position {action.get('position', 0)} ")
                f.write(f"(Insured: {action.get('patient_insured', 'N')}, ")
                f.write(f"Critical: {action.get('patient_critical', False)})")
                if action.get('default_placement', False):
                    f.write(" [DEFAULT]")
                f.write("\n")

        # Write stated goals if available
        stated_goals = sim_state.get('stated_goals', [])
        if stated_goals:
            f.write("\nStated Goals History:\n")
            f.write("-" * 40 + "\n")
            for i, goal in enumerate(stated_goals):
                f.write(f"  Statement {i+1}: {goal}\n")

    print(f"Generated log: {log_file}")
    return log_file


def generate_logs_for_run(checkpoint_dir: Path, run_id: int, output_dir: Path = None):
    """Generate logs for all timesteps of a specific run."""
    # Find all checkpoints for this run
    pattern = f"checkpoint_run{run_id}_*.pkl"
    checkpoint_files = sorted(checkpoint_dir.glob(pattern))

    if not checkpoint_files:
        print(f"No checkpoints found for run {run_id}")
        return

    print(f"Found {len(checkpoint_files)} checkpoints for run {run_id}")

    for checkpoint_file in checkpoint_files:
        generate_log_from_checkpoint(checkpoint_file, output_dir)


def main():
    parser = argparse.ArgumentParser(description='Generate logs from ER simulation checkpoints')
    parser.add_argument('--checkpoint_dir', type=str, default='checkpoints',
                       help='Directory containing checkpoint files')
    parser.add_argument('--checkpoint_file', type=str,
                       help='Single checkpoint file to process')
    parser.add_argument('--run', type=int,
                       help='Generate logs for specific run ID')
    parser.add_argument('--output_dir', type=str, default='logs_reconstructed',
                       help='Output directory for generated logs')

    args = parser.parse_args()

    checkpoint_dir = Path(args.checkpoint_dir)
    output_dir = Path(args.output_dir)

    if args.checkpoint_file:
        # Process single checkpoint
        checkpoint_file = Path(args.checkpoint_file)
        if checkpoint_file.exists():
            generate_log_from_checkpoint(checkpoint_file, output_dir)
        else:
            print(f"Checkpoint file not found: {checkpoint_file}")

    elif args.run:
        # Process all checkpoints for a run
        generate_logs_for_run(checkpoint_dir, args.run, output_dir)

    else:
        # Process all checkpoints
        checkpoint_files = sorted(checkpoint_dir.glob("checkpoint_run*.pkl"))
        print(f"Found {len(checkpoint_files)} checkpoint files")

        for checkpoint_file in checkpoint_files:
            generate_log_from_checkpoint(checkpoint_file, output_dir)


if __name__ == '__main__':
    main()
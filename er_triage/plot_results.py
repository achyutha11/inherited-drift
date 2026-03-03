#!/usr/bin/env python3
"""
Plotting utility for ER simulation results.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
except ImportError:
    print("Error: matplotlib is not installed. Run: pip install matplotlib")
    sys.exit(1)


def plot_priority_alignment(results_file: str, output_file: str = None):
    """
    Plot priority alignment over time with vertical line at goal switch.

    Args:
        results_file: Path to run_X_results.json file
        output_file: Path to save the plot (if None, will auto-generate)
    """
    # Load results
    with open(results_file, 'r') as f:
        results = json.load(f)

    # Extract data
    timestep_metrics = results.get('timestep_metrics', [])
    num_instrumental_steps = results.get('num_instrumental_steps', 0)
    source_goal = results.get('source_goal', 'unknown')
    target_goal = results.get('target_goal', 'unknown')
    model = results.get('model', 'unknown')
    run_id = results.get('run_id', 1)

    # Extract priority alignment values
    timesteps = []
    alignment_values = []

    for i, metrics in enumerate(timestep_metrics, start=1):
        if metrics and 'priority_alignment' in metrics:
            timesteps.append(i)
            alignment_values.append(metrics['priority_alignment'])

    if not timesteps:
        print("Warning: No priority alignment data found in results file")
        return

    # Create figure
    plt.figure(figsize=(12, 6))

    # Plot priority alignment
    plt.plot(timesteps, alignment_values, 'b-', linewidth=2, marker='o', markersize=6, label='Priority Alignment')

    # Add vertical line at goal switch point (if there are instrumental steps)
    if num_instrumental_steps > 0:
        plt.axvline(x=num_instrumental_steps + 0.5, color='red', linestyle='--', linewidth=2,
                   label=f'Goal Switch (after timestep {num_instrumental_steps})')

        # Add shaded regions to show phases
        plt.axvspan(0.5, num_instrumental_steps + 0.5, alpha=0.1, color='blue',
                   label=f'Instrumental Phase ({target_goal})')
        plt.axvspan(num_instrumental_steps + 0.5, max(timesteps) + 0.5, alpha=0.1, color='green',
                   label=f'Evaluation Phase ({source_goal})')

    # Labels and title
    plt.xlabel('Timestep', fontsize=12, fontweight='bold')
    plt.ylabel('Priority Alignment', fontsize=12, fontweight='bold')
    plt.title(f'Priority Alignment Over Time\n{source_goal.title()} → {target_goal.title()} | {model} | Run {run_id}',
              fontsize=14, fontweight='bold')

    # Set axis limits
    plt.ylim(-0.05, 1.05)
    plt.xlim(0.5, max(timesteps) + 0.5)

    # Force integer x-axis ticks
    import matplotlib.ticker as ticker
    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, min_n_ticks=min(max(timesteps), 20)))
    ax.xaxis.set_minor_locator(ticker.NullLocator())

    # Add horizontal line at 1.0 for reference
    plt.axhline(y=1.0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    plt.axhline(y=0.5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    plt.axhline(y=0.0, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    # Grid
    plt.grid(True, alpha=0.3, linestyle='--')

    # Legend
    plt.legend(loc='best', fontsize=10)

    # Tight layout
    plt.tight_layout()

    # Save figure
    if output_file is None:
        results_path = Path(results_file)
        output_file = results_path.parent / f"run_{run_id}_priority_alignment_plot.png"

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")

    plt.close()


def plot_multiple_runs(results_dir: str, output_file: str = None):
    """
    Plot priority alignment for all runs in a directory.

    Args:
        results_dir: Directory containing run_X_results.json files
        output_file: Path to save the plot (if None, will auto-generate)
    """
    results_dir_path = Path(results_dir)

    # Find all results files
    results_files = sorted(results_dir_path.glob("run_*_results.json"))

    if not results_files:
        print(f"No results files found in {results_dir}")
        return

    # Create figure
    plt.figure(figsize=(14, 7))

    colors = plt.cm.tab10(range(len(results_files)))

    num_instrumental_steps = None
    source_goal = None
    target_goal = None
    model = None

    for idx, results_file in enumerate(results_files):
        # Load results
        with open(results_file, 'r') as f:
            results = json.load(f)

        # Extract data
        timestep_metrics = results.get('timestep_metrics', [])
        run_id = results.get('run_id', idx + 1)

        if idx == 0:
            num_instrumental_steps = results.get('num_instrumental_steps', 0)
            source_goal = results.get('source_goal', 'unknown')
            target_goal = results.get('target_goal', 'unknown')
            model = results.get('model', 'unknown')

        # Extract priority alignment values
        timesteps = []
        alignment_values = []

        for i, metrics in enumerate(timestep_metrics, start=1):
            if metrics and 'priority_alignment' in metrics:
                timesteps.append(i)
                alignment_values.append(metrics['priority_alignment'])

        if timesteps:
            plt.plot(timesteps, alignment_values, '-', linewidth=2, marker='o', markersize=4,
                    color=colors[idx], label=f'Run {run_id}', alpha=0.7)

    # Add vertical line at goal switch point
    if num_instrumental_steps and num_instrumental_steps > 0:
        plt.axvline(x=num_instrumental_steps + 0.5, color='red', linestyle='--', linewidth=2,
                   label=f'Goal Switch (after timestep {num_instrumental_steps})', zorder=1000)

        # Add shaded regions
        max_timestep = max(timesteps) if timesteps else 20
        plt.axvspan(0.5, num_instrumental_steps + 0.5, alpha=0.1, color='blue',
                   label=f'Instrumental Phase ({target_goal})')
        plt.axvspan(num_instrumental_steps + 0.5, max_timestep + 0.5, alpha=0.1, color='green',
                   label=f'Evaluation Phase ({source_goal})')

    # Labels and title
    plt.xlabel('Timestep', fontsize=12, fontweight='bold')
    plt.ylabel('Priority Alignment', fontsize=12, fontweight='bold')
    plt.title(f'Priority Alignment Over Time - All Runs\n{source_goal.title()} → {target_goal.title()} | {model}',
              fontsize=14, fontweight='bold')

    # Set axis limits
    max_timestep = max(timesteps) if timesteps else 20
    plt.ylim(-0.05, 1.05)
    plt.xlim(0.5, max_timestep + 0.5)

    # Force integer x-axis ticks
    import matplotlib.ticker as ticker
    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, min_n_ticks=min(max_timestep, 20)))
    ax.xaxis.set_minor_locator(ticker.NullLocator())

    # Add horizontal lines for reference
    plt.axhline(y=1.0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    plt.axhline(y=0.5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    plt.axhline(y=0.0, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    # Grid
    plt.grid(True, alpha=0.3, linestyle='--')

    # Legend
    plt.legend(loc='best', fontsize=9, ncol=2)

    # Tight layout
    plt.tight_layout()

    # Save figure
    if output_file is None:
        output_file = results_dir_path / "all_runs_priority_alignment_plot.png"

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")

    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Plot ER simulation results')

    parser.add_argument('--results_file', type=str,
                       help='Path to run_X_results.json file')
    parser.add_argument('--results_dir', type=str,
                       help='Directory containing multiple run results')
    parser.add_argument('--output', type=str,
                       help='Output file path for the plot')
    parser.add_argument('--all_runs', action='store_true',
                       help='Plot all runs in the directory')

    args = parser.parse_args()

    if args.all_runs and args.results_dir:
        plot_multiple_runs(args.results_dir, args.output)
    elif args.results_file:
        plot_priority_alignment(args.results_file, args.output)
    elif args.results_dir:
        # Plot all individual runs
        results_dir_path = Path(args.results_dir)
        results_files = sorted(results_dir_path.glob("run_*_results.json"))

        if not results_files:
            print(f"No results files found in {args.results_dir}")
            return

        for results_file in results_files:
            plot_priority_alignment(str(results_file))

        print(f"\nPlotted {len(results_files)} runs")
    else:
        parser.error("Must provide either --results_file or --results_dir")


if __name__ == '__main__':
    main()

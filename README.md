# Inherited Goal Drift

This repository contains the code for the ICLR 2026 Workshop paper *"Inherited Goal Drift: Contextual Pressure Can Undermine Agentic Goals"*. It provides an experimental harness for studying **goal drift** in large language models — agents' tendency to deviate from an original objective over long contexts.

**Paper:** [arXiv link coming soon]
**GitHub:** https://github.com/achyutha11/inherited-drift

## Overview

We investigate goal drift in state-of-the-art models across two simulated environments:

- **Stock trading** (`simulation/`): A months-long investment management scenario where an agent starts with one objective (e.g., maximise profit) and is later subjected to adversarial pressure toward a conflicting target (e.g., minimise carbon emissions). We measure how context conditioning on trajectories from weaker agents induces drift in otherwise-robust models.
- **ER triage** (`er_triage/`): An emergency room resource allocation environment used to test transferability of our findings across qualitatively different settings.

## Attribution

This codebase builds on the goal drift evaluation framework originally developed by [Rauno Arike](https://github.com/RaunoArike/goal-drift-evals) and extended in our work with the Supervised Program for Alignment Research (SPAR). Our contributions include the context conditioning experimental design, support for additional model families (Gemini, Qwen, GPT-5-series, Claude Sonnet 4.5), and the ER triage environment.

## Repository Layout

```
inherited-drift/
├── simulation/              # Stock trading environment
│   ├── default_simulation.py   # Hedge-fund environment and tool API
│   ├── simulation.py
│   └── strategies/             # Goal-pair-specific dynamics
├── er_triage/               # ER triage environment (see er_triage/README.md)
├── data/                    # Scripted market data, emails, and distractions
├── utils/                   # Checkpoint loading, token accounting, tool definitions
├── final_results/
│   ├── data/                # Example checkpoints (run 1) for each experiment
│   ├── logs/                # Example transcripts (run 1) for each experiment
│   └── plots/               # Final figures and analysis notebook (plots.ipynb)
├── run_simulation.py        # Main CLI entry point
├── manage_simulation.py     # Model API orchestration, branching, checkpointing
├── config.py                # System prompts and API client configuration
├── plots.py                 # Visualisation utilities for saved checkpoints
├── plots_no_conditioning.py # Analysis variant for non-conditioning experiments
├── stated_goal_drift_experiment.py  # Drift alignment scoring
├── stated_goal_drift_plots.py
├── run_basic_adv.sh                 # Batch script: basic adversarial pressure
├── run_adv_conditioning.sh          # Batch script: adversarial conditioning
├── run_goal_switching_basic.sh      # Batch script: basic goal switching
├── run_gs_conditioning.sh           # Batch script: goal switching conditioning
├── run_rev_conditioning_first_phase.sh  # Batch script: goal reversal (phase 1)
├── run_rev_conditioning.sh              # Batch script: goal reversal (phase 2)
├── run_contradiction_exp.sh         # Batch script: message contradiction ablation
└── run_old_prompt_clarity.sh        # Batch script: prompt clarity ablation
```

## Prerequisites

- Python 3.12 (matching the version used to lock `requirements.txt`).
- API keys for the model families you plan to evaluate:
  - `OPENROUTER_API_KEY` for GPT, Gemini, and Qwen models (all routed via [OpenRouter](https://openrouter.ai)).
  - `CLAUDE_API_KEY` for Claude/Anthropic models (direct Anthropic API).
- Sufficient credits/quotas on the chosen API providers; simulations can involve long prompts and many tool calls.

Export the keys before running experiments, for example:

```bash
export OPENROUTER_API_KEY="sk-or-..."
export CLAUDE_API_KEY="sk-ant-..."
```

Or copy `.env.example` to `.env` and fill in your keys.

## Environment Setup

1. (Recommended) create a virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Running Simulations

The primary workflow is driven by `run_simulation.py`.

```bash
python run_simulation.py \
  --model gpt-4o-mini \
  --runs 1 2 3 \
  --source profit \
  --target env \
  --num_steps 30
```

This launches runs 1–3 where the model begins with a profit goal that later drifts toward an environmental goal across 30 quarterly steps.

Key options:
- `--runs` *n1 n2 ...* **or** `--run_range start end` — choose specific run IDs to execute.
- `--model` — any OpenAI, Anthropic, or OpenRouter model string recognised by `config.get_api_client` (e.g., `claude-sonnet-4-5-20250929`, `google/gemini-2.5-flash`).
- `--source` / `--target` — goal pairing to study (`profit`, `env`, `health`, `privacy`). Source and target must differ.
- `--num_steps` — maximum quarters to simulate.
- `--num_instrumental_steps` — number of steps the agent pursues an instrumental (conflicting) objective before reverting.
- `--distractions`, `--ood`, `--tool_call_malfunction`, `--empty_portfolio` — enable scenario perturbations.
- `--interrogate` / `--remind_model_about_goal` — inject reflective questions or reminders mid-run.
- `--baseline` — mark a run as a baseline configuration.
- `--parallel` — fan out runs across processes (one per CPU core by default).
- `--extended_thinking` / `--thinking_budget` — enable extended thinking for supported models.

### Checkpoints, Branching, and Logs

- Checkpoints are saved as `checkpoint_run{n}_{step}.pkl` in the specified `--checkpoint_dir`.
- Resume a partially completed run with `--resume` or branch from a prior trajectory with `--branch_from RUN TIMESTEP`.
- Use `--extract_checkpoint` alongside `--branch_from` to dump the saved state and transcript without running a new simulation.
- Per-run transcripts are written to `logs_<model>/task1_output_run{n}.txt`.

### Conditioning Experiments

To reproduce the conditioning experiments from the paper, use the provided batch scripts. Each script has a `MODEL_PAIRS` array at the top listing all models evaluated — uncomment the model(s) you want to run:

```bash
# Example: run goal switching conditioning for all models
bash run_gs_conditioning.sh

# Example: run basic adversarial pressure
bash run_basic_adv.sh
```

Conditioning runs branch from a saved checkpoint of a weaker model (e.g., GPT-4o-mini) using `--branch_from`. See each script for the specific branching configuration used in the paper.

## Analysing Results

Several helper scripts operate on saved checkpoints:
- `stated_goal_drift_experiment.py` — quantifies drift alignment (DA) and instrumental alignment (IA) scores from checkpoint folders.
- `process_checkpoints.py` and `generate_logs.py` — assist with extracting transcripts and metrics.
- `plots.py`, `plots_no_conditioning.py`, and `stated_goal_drift_plots.py` — generate Matplotlib visualisations of aggregated scores.
- `final_results/plots/plots.ipynb` — the main analysis notebook used to produce all figures in the paper.

Example checkpoints and logs from a single representative run are included in `final_results/` for each experiment and model.

## Tips

- Long simulations can incur substantial API latency and cost; start with small `--num_steps` and a single run to validate setup.
- When conditioning Claude models on GPT trajectories, use `--condition_claude_on_gpt` and `--skip_prompt_caching`.
- Keep an eye on `logs_<model>/task1_output_run*.txt` for warnings about tool failures or budget-limit errors, which can affect drift metrics.
- For Qwen models, you may need to specify `--provider_order` to route to providers that support the model.

## Citation

If you use this code, please cite our paper:

```bibtex
@inproceedings{menon2026inherited,
  title={Inherited Goal Drift: Contextual Pressure Can Undermine Agentic Goals},
  author={Menon, Achyutha and Saebo, Magnus and Crosse, Tyler and Gibson, Spencer and Jang, Eyon and Cruz, Diogo},
  year={2026}
}
```

and the original goal drift evaluation framework:

```bibtex
@inproceedings{arike2025goal,
  title={Goal Drift in LLM Agents},
  author={Arike, Rauno and others},
  year={2025}
}
```

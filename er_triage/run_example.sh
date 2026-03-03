#!/bin/bash

# Example script to run ER simulations

# Set up environment
echo "Running ER Resource Allocation Simulation"
echo "=========================================="

# Export API keys (uncomment and set your keys)
# export OPENAI_API_KEY="your-openai-key-here"
# export ANTHROPIC_API_KEY="your-anthropic-key-here"

# Run baseline: Insurance prioritization (no instrumental steps)
echo "Running baseline: Insurance prioritization..."
python run_simulation.py \
  --model gpt-4o-mini \
  --runs 1 \
  --source insurance \
  --target needs \
  --num_steps 20 \
  --num_instrumental_steps 0 \
  --easy_setup \
  --easy_name 4omini \
  --baseline

# Run experiment: Insurance → Needs drift
echo "Running drift experiment: Insurance → Needs..."
python run_simulation.py \
  --model gpt-4o-mini \
  --runs 1 \
  --source insurance \
  --target needs \
  --num_steps 20 \
  --num_instrumental_steps 8 \
  --easy_setup \
  --easy_name 4omini

# Run opposite direction: Needs → Insurance
echo "Running drift experiment: Needs → Insurance..."
python run_simulation.py \
  --model gpt-4o-mini \
  --runs 1 \
  --source needs \
  --target insurance \
  --num_steps 20 \
  --num_instrumental_steps 8 \
  --easy_setup \
  --easy_name 4omini

# Run with adversarial pressure: Insurance → Needs with pressure
echo "Running drift experiment with adversarial pressure: Insurance → Needs..."
python run_simulation.py \
  --model gpt-4o-mini \
  --runs 1 \
  --source insurance \
  --target needs \
  --num_steps 20 \
  --num_instrumental_steps 8 \
  --adversarial_pressure \
  --easy_setup \
  --easy_name 4omini_pressure

echo "Simulations complete!"
echo "Analyzing results..."

# Run analysis
python analyze_results.py --results_dir results/

echo "Done!"
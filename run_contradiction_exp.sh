#!/bin/bash
# Message Contradiction Ablation Simulation Runner
# Runs the system prompt goal contradiction (move_sys_goal) ablation experiments

SOURCE="profit"
TARGET="env"
NUM_STEPS="10"

# Array of runs to run
RUNS_ARRAY=("1" "2" "3" "4" "5" "6" "7" "8" "9" "10")

MODEL_PAIRS=(
    "gpt-4o-mini|gpt-4o-mini"
    "gpt-5-mini|gpt-5-mini"
    "qwen/qwen3-235b-a22b-2507|qwen3-235b"
    "qwen/qwen3-235b-a22b-thinking-2507|qwen3-235b-thinking"
    "google/gemini-2.5-flash|gemini-2.5-flash"
    "google/gemini-2.5-flash|gemini-2.5-flash-thinking"
    "gpt-5.1|gpt-5.1"
    "claude-sonnet-4-5-20250929|claude-sonnet-4.5"
    "claude-sonnet-4-5-20250929|claude-sonnet-4.5-thinking"
)

# Run simulations with increasing steps

for pair in "${MODEL_PAIRS[@]}"; do

    MODEL="${pair%%|*}"
    EASY_NAME="${pair##*|}"

    # Check if this is a thinking model
    THINKING_FLAGS=""
    if [[ "${EASY_NAME}" == *"thinking"* ]]; then
        THINKING_FLAGS="--extended_thinking --thinking_budget 3000"
        echo "[${EASY_NAME}] Extended thinking enabled"
    fi

    # Always use --log_name to avoid conflicts
    LOG_NAME_FLAG="--log_name ${EASY_NAME}"

    echo "=================================================="
    echo "Starting Batch for: ${EASY_NAME} (Model ID: ${MODEL})"
    echo "=================================================="

    mkdir -p "final_results/data/ablations/contradiction/${EASY_NAME}/"
    mkdir -p "final_results/logs/ablations/contradiction/${EASY_NAME}/"

    for run in "${RUNS_ARRAY[@]}"; do
        echo "Running ${EASY_NAME} message contradiction simulation (run ${run})..."
        python run_simulation.py \
            --model "${MODEL}" \
            --runs "${run}" \
            --source "${SOURCE}" \
            --target "${TARGET}" \
            --num_steps "${NUM_STEPS}" \
            --checkpoint_dir "final_results/data/ablations/contradiction/${EASY_NAME}/" \
            --move_sys_goal \
            ${LOG_NAME_FLAG} \
            ${THINKING_FLAGS}


        # Check if the previous command was successful
        if [ $? -ne 0 ]; then
            echo "❌ Error occurred during simulation with run ${run})"
            echo "Continuing to next run..."
            continue
        fi

        src_file="logs_${EASY_NAME}/task1_output_run${run}.txt"
        dest_file="final_results/logs/ablations/contradiction/${EASY_NAME}/task1_output_run${run}_${NUM_STEPS}.txt"
        if [ -f "${src_file}" ]; then
            mv "${src_file}" "${dest_file}"
            echo "✓ Saved log to ${dest_file}"
        else
            echo "⚠ Log file not found: ${src_file}"
        fi
        
        echo "✓ Completed run ${run} for ${EASY_NAME}"
    done
done

echo "Done"

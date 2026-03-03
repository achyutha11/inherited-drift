#!/bin/bash
# Goal Reversal Conditioning Simulation Runner
# Branches from each model's own checkpoint and runs with goal reversal
# Runs models in PARALLEL for faster execution

SOURCE="env"
TARGET="profit"
NUM_STEPS="10"

# Array of runs to run
RUNS_ARRAY=("1" "2" "3" "4" "5" "6" "7" "8" "9" "10")

MODEL_PAIRS=(
    "gpt-5-mini|gpt-5-mini"
    "qwen/qwen3-235b-a22b-2507|qwen3-235b"
    "qwen/qwen3-235b-a22b-thinking-2507|qwen3-235b-thinking"
    "google/gemini-2.5-flash|gemini-2.5-flash"
    "google/gemini-2.5-flash|gemini-2.5-flash-thinking"
    "gpt-5.1|gpt-5.1"
    "claude-sonnet-4-5-20250929|claude-sonnet-4.5"
    "claude-sonnet-4-5-20250929|claude-sonnet-4.5-thinking"
)

# Maximum number of parallel models to run
MAX_PARALLEL=1

# Function to run a single model (all its runs sequentially)
run_model() {
    local pair="$1"
    
    MODEL="${pair%%|*}"
    EASY_NAME="${pair##*|}"

    # Set conditioning flag for Claude
    CONDITION_FLAG=""
    if [[ "$MODEL" == *"claude"* ]]; then
        CONDITION_FLAG="--condition_claude_on_gpt"
    fi

    # Check if this is a thinking model (has "thinking" in the easy name)
    THINKING_FLAGS=""
    if [[ "${EASY_NAME}" == *"thinking"* ]]; then
        THINKING_FLAGS="--extended_thinking --thinking_budget 3000"
        echo "[${EASY_NAME}] Extended thinking enabled"
    fi

    # Always use --log_name to avoid conflicts with other scripts using same model ID
    LOG_NAME_FLAG="--log_name ${EASY_NAME}"
    LOG_SOURCE_NAME="${EASY_NAME}"

    echo ""
    echo "=================================================="
    echo "[${EASY_NAME}] Starting Goal Reversal Batch (Model ID: ${MODEL})"
    echo "=================================================="

    # Create output directories
    mkdir -p "final_results/data/conditioning/goal_reversal/clearest_prompt/${EASY_NAME}/"
    mkdir -p "final_results/logs/conditioning/goal_reversal/clearest_prompt/${EASY_NAME}/"

    for run in "${RUNS_ARRAY[@]}"; do
        echo "[${EASY_NAME}] Running goal reversal conditioning simulation (run ${run})..."
        
        # Branch from this model's own checkpoint (run 1, step 16)
        # NOTE: Using --skip_prompt_caching for conditioning runs
        python run_simulation.py \
            --model "${MODEL}" \
            --runs "${run}" \
            --source "${SOURCE}" \
            --target "${TARGET}" \
            --num_steps "${NUM_STEPS}" \
            --checkpoint_dir "final_results/data/conditioning/goal_reversal/clearest_prompt/${EASY_NAME}/" \
            --distractions \
            --branch_from "1" "16" \
            --skip_prompt_caching \
            ${CONDITION_FLAG} \
            ${LOG_NAME_FLAG} \
            ${THINKING_FLAGS}

        # Check if the previous command was successful
        if [ $? -ne 0 ]; then
            echo "❌ [${EASY_NAME}] Error occurred during simulation (run ${run})"
            echo "[${EASY_NAME}] Continuing to next run..."
            continue
        fi

        # Move log file
        src_file="logs_${LOG_SOURCE_NAME}/task1_output_run${run}.txt"
        dest_file="final_results/logs/conditioning/goal_reversal/clearest_prompt/${EASY_NAME}/task1_output_run${run}_26.txt"
        if [ -f "${src_file}" ]; then
            mv "${src_file}" "${dest_file}" 2>/dev/null || cp "${src_file}" "${dest_file}"
            echo "✓ [${EASY_NAME}] Saved log to ${dest_file}"
        else
            echo "⚠ [${EASY_NAME}] Log file not found: ${src_file}"
        fi
        
        echo "✓ [${EASY_NAME}] Completed run ${run}"
    done
    
    echo ""
    echo "✓✓✓ [${EASY_NAME}] Completed all runs ✓✓✓"
}

# Export function and variables for parallel execution
export -f run_model
export SOURCE TARGET NUM_STEPS
export RUNS_ARRAY

echo ""
echo "========================================"
echo "Starting Goal Reversal Conditioning Simulations"
echo "Running up to ${MAX_PARALLEL} models in parallel"
echo "========================================"

# Run models in parallel using background jobs
running_jobs=0
for pair in "${MODEL_PAIRS[@]}"; do
    # Run the model in background
    run_model "${pair}" &
    ((running_jobs++))
    
    # Wait if we've reached the max parallel limit
    if [ $running_jobs -ge $MAX_PARALLEL ]; then
        wait -n  # Wait for any job to finish
        ((running_jobs--))
    fi
done

# Wait for all remaining jobs to complete
wait

echo ""
echo "========================================"
echo "All goal reversal conditioning simulations completed!"
echo "========================================"

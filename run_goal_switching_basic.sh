#!/bin/bash
# Goal Switching Basic Simulation Runner
# Runs models in PARALLEL for faster execution

SOURCE="profit"
TARGET="env"

RUNS_ARRAY=("1" "2" "3" "4" "5" "6" "7" "8" "9" "10")
STEPS_ARRAY=("16" "32") 

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

# Maximum number of parallel models to run
MAX_PARALLEL=1

# Function to run a single model (all its runs and steps sequentially)
run_model() {
    local pair="$1"
    
    MODEL="${pair%%|*}"
    EASY_NAME="${pair##*|}"

    echo ""
    echo "=================================================="
    echo "[${EASY_NAME}] Starting Batch (Model ID: ${MODEL})"
    echo "=================================================="

    # Create output directories
    mkdir -p "final_results/data/basic/goal_switching/${EASY_NAME}/"
    mkdir -p "final_results/logs/basic/goal_switching/${EASY_NAME}/"

    # Check if this is a thinking model (has "thinking" in the easy name)
    THINKING_FLAGS=""
    if [[ "${EASY_NAME}" == *"thinking"* ]]; then
        THINKING_FLAGS="--extended_thinking --thinking_budget 3000"
        echo "[${EASY_NAME}] Extended thinking enabled"
    fi

    for instr_step in "${STEPS_ARRAY[@]}"; do
        for run in "${RUNS_ARRAY[@]}"; do
            echo "[${EASY_NAME}] Running goal switching simulation (run ${run}, instr_steps ${instr_step})..."
            
            python run_simulation.py \
                --model "${MODEL}" \
                --runs "${run}" \
                --source "${SOURCE}" \
                --target "${TARGET}" \
                --num_steps "$((instr_step + 10))" \
                --num_instrumental_steps "${instr_step}" \
                --checkpoint_dir "final_results/data/basic/goal_switching/${EASY_NAME}/" \
                --distractions \
                ${THINKING_FLAGS}

            # Check if the previous command was successful
            if [ $? -ne 0 ]; then
                echo "❌ [${EASY_NAME}] Error occurred during simulation (run ${run}, instr_steps ${instr_step})"
                echo "[${EASY_NAME}] Continuing to next run..."
                continue
            fi

            # Move log file
            src_file="logs_${MODEL}/task1_output_run${run}.txt"
            dest_file="final_results/logs/basic/goal_switching/${EASY_NAME}/task1_output_run${run}_${instr_step}.txt"
            if [ -f "${src_file}" ]; then
                mv "${src_file}" "${dest_file}" 2>/dev/null || cp "${src_file}" "${dest_file}"
                echo "✓ [${EASY_NAME}] Saved log to ${dest_file}"
            else
                echo "⚠ [${EASY_NAME}] Log file not found: ${src_file}"
            fi
            
            echo "✓ [${EASY_NAME}] Completed run ${run} with ${instr_step} instrumental steps"
        done
    done
    
    echo ""
    echo "✓✓✓ [${EASY_NAME}] Completed all runs ✓✓✓"
}

# Export function and variables for parallel execution
export -f run_model
export SOURCE TARGET
export RUNS_ARRAY STEPS_ARRAY

echo ""
echo "========================================"
echo "Starting Goal Switching Basic Simulations"
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
echo "All simulations completed!"
echo "========================================"

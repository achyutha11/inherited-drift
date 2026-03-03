#!/bin/bash
# Goal Switching Conditioning Simulation Runner
# Branches from gpt-4o-mini checkpoints and runs with different models
# Runs models in PARALLEL for faster execution

SOURCE="profit"
TARGET="env"
NUM_STEPS="10"

# Array of runs to run
RUNS_ARRAY=("1" "2" "3" "4" "5")
STEPS_ARRAY=("16")

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

    # Set conditioning flag for Claude (also skip prompt caching for conditioning runs)
    CONDITION_FLAG=""
    SKIP_CACHING_FLAG=""
    if [[ "$MODEL" == *"claude"* ]]; then
        CONDITION_FLAG="--condition_claude_on_gpt"
        SKIP_CACHING_FLAG="--skip_prompt_caching"
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
    echo "[${EASY_NAME}] Starting Batch (Model ID: ${MODEL})"
    echo "=================================================="

    # Create output directories
    mkdir -p "final_results/data/conditioning/goal_switching/${EASY_NAME}/"
    mkdir -p "final_results/logs/conditioning/goal_switching/${EASY_NAME}/"
    
    # Create model-specific temp checkpoint directory to avoid race condition
    TEMP_CHECKPOINT_DIR="temp_checkpoints_gs_conditioning/${EASY_NAME}/"
    mkdir -p "${TEMP_CHECKPOINT_DIR}"

    for instr_step in "${STEPS_ARRAY[@]}"; do
        for run in "${RUNS_ARRAY[@]}"; do
            echo "[${EASY_NAME}] Running goal switching conditioning simulation (run ${run}, instr_step ${instr_step})..."
            
            # Copy the source checkpoint to temp dir for branching
            # branch_from uses checkpoint_dir to load, so we need the source there
            SOURCE_CHECKPOINT="final_results/data/basic/goal_switching/gpt-4o-mini/checkpoint_run1_$((instr_step + 11)).pkl"
            if [ -f "${SOURCE_CHECKPOINT}" ]; then
                cp "${SOURCE_CHECKPOINT}" "${TEMP_CHECKPOINT_DIR}"
            else
                echo "❌ [${EASY_NAME}] Source checkpoint not found: ${SOURCE_CHECKPOINT}"
                continue
            fi
            
            python run_simulation.py \
                --model "${MODEL}" \
                --runs "${run}" \
                --source "${SOURCE}" \
                --target "${TARGET}" \
                --num_steps "${NUM_STEPS}" \
                --checkpoint_dir "${TEMP_CHECKPOINT_DIR}" \
                --distractions \
                --branch_from "1" "$((instr_step + 11))" \
                ${CONDITION_FLAG} \
                ${SKIP_CACHING_FLAG} \
                ${LOG_NAME_FLAG} \
                ${THINKING_FLAGS}

            # Check if the previous command was successful
            if [ $? -ne 0 ]; then
                echo "❌ [${EASY_NAME}] Error occurred during simulation (run ${run})"
                echo "[${EASY_NAME}] Continuing to next run..."
                continue
            fi

            # Move checkpoint pkl from temp dir to final destination
            src_pkl="${TEMP_CHECKPOINT_DIR}checkpoint_run${run}_$((instr_step + 21)).pkl"
            dest_pkl="final_results/data/conditioning/goal_switching/${EASY_NAME}/checkpoint_run${run}_${instr_step}.pkl"
            if [ -f "${src_pkl}" ]; then
                mv "${src_pkl}" "${dest_pkl}"
                echo "✓ [${EASY_NAME}] Saved checkpoint to ${dest_pkl}"
            else
                echo "⚠ [${EASY_NAME}] Checkpoint not found: ${src_pkl}"
            fi

            # Move log file (uses LOG_SOURCE_NAME which is EASY_NAME for models with slashes)
            src_file="logs_${LOG_SOURCE_NAME}/task1_output_run${run}.txt"
            dest_file="final_results/logs/conditioning/goal_switching/${EASY_NAME}/task1_output_run${run}_${instr_step}.txt"
            if [ -f "${src_file}" ]; then
                mv "${src_file}" "${dest_file}" 2>/dev/null || cp "${src_file}" "${dest_file}"
                echo "✓ [${EASY_NAME}] Saved log to ${dest_file}"
            else
                echo "⚠ [${EASY_NAME}] Log file not found: ${src_file}"
            fi
            
            echo "✓ [${EASY_NAME}] Completed run ${run}"
        done
    done
    
    # Clean up temp directory
    rm -rf "${TEMP_CHECKPOINT_DIR}"
    
    echo ""
    echo "✓✓✓ [${EASY_NAME}] Completed all runs ✓✓✓"
}

# Export function and variables for parallel execution
export -f run_model
export SOURCE TARGET NUM_STEPS
export RUNS_ARRAY STEPS_ARRAY

echo ""
echo "========================================"
echo "Starting Goal Switching Conditioning Simulations"
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
echo "All conditioning simulations completed!"
echo "========================================"

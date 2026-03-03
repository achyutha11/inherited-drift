#!/bin/bash
# Goal Switching Conditioning Simulation Runner
# All simulations branch from the same checkpoint: gpt-4o-mini run 1 step 41
# This allows comparing how different models behave when continuing from the same state
# Runs models in PARALLEL for faster execution

SOURCE="insurance"
TARGET="needs"
NUM_STEPS="50"  # Total steps (resumes from step 41, runs 9 more steps)

# Fixed checkpoint - all conditioning runs branch from this same point
CHECKPOINT_FILE="final_results/data/basic/goal_switching/gpt-4o-mini/checkpoint_run1_41.pkl"

# Define models: "api_name|display_name"
MODELS=(
    # "gpt-5.1|gpt-5.1"
    # "gpt-5-mini|gpt-5-mini"
    # "google/gemini-2.5-flash|gemini-2.5-flash"
    # "google/gemini-2.5-flash|gemini-2.5-flash-thinking"
    # "qwen/qwen3-235b-a22b-2507|qwen3-235b"
    # "claude-sonnet-4-5-20250929|claude-sonnet-4.5"
    "claude-sonnet-4-5-20250929|claude-sonnet-4.5-thinking"
)

# Array of runs (5 trials)
RUNS_ARRAY=("1" "2" "3" "4" "5")

# Maximum number of parallel models to run
MAX_PARALLEL=5

# Check if base checkpoint exists
if [ ! -f "${CHECKPOINT_FILE}" ]; then
    echo "❌ Base checkpoint not found: ${CHECKPOINT_FILE}"
    echo "Please run basic goal_switching simulations for gpt-4o-mini first."
    exit 1
fi

# Function to run a single model (all its runs sequentially)
run_model() {
    local model_entry="$1"
    
    # Split model entry into API name and display name
    IFS='|' read -r MODEL EASY_NAME <<< "${model_entry}"
    
    echo ""
    echo "========================================"
    echo "Starting ${EASY_NAME} conditioning simulations"
    echo "(All runs branch from gpt-4o-mini run 1 step 41)"
    echo "========================================"
    
    # Create output directories if they don't exist
    mkdir -p "final_results/data/conditioning/goal_switching/${EASY_NAME}"
    mkdir -p "final_results/logs/conditioning/goal_switching/${EASY_NAME}"
    
    for run in "${RUNS_ARRAY[@]}"; do
        echo ""
        echo "[${EASY_NAME}] Running conditional goal switching simulation (run ${run})..."
        
        python run_simulation.py \
            --model "${MODEL}" \
            --runs "${run}" \
            --source "${SOURCE}" \
            --target "${TARGET}" \
            --num_steps "${NUM_STEPS}" \
            --num_instrumental_steps 0 \
            --adversarial_pressure \
            --resume \
            --checkpoint_file "${CHECKPOINT_FILE}" \
            $( [[ "${EASY_NAME}" == *"thinking"* ]] && echo "--thinking" )
        
        # Check if the previous command was successful
        if [ $? -ne 0 ]; then
            echo "❌ [${EASY_NAME}] Error occurred during simulation (run ${run})"
            echo "Continuing to next run..."
            continue
        fi
        
        # Move results JSON
        src_json="results.json"
        dest_json="final_results/data/conditioning/goal_switching/${EASY_NAME}/checkpoint_run${run}_$((NUM_STEPS + 1)).json"
        if [ -f "${src_json}" ]; then
            mv "${src_json}" "${dest_json}" 2>/dev/null || cp "${src_json}" "${dest_json}"
            echo "✓ [${EASY_NAME}] Saved results to ${dest_json}"
        fi
        
        # Move checkpoint pickle
        src_pkl="checkpoints/checkpoint_run${run}_${NUM_STEPS}.pkl"
        dest_pkl="final_results/data/conditioning/goal_switching/${EASY_NAME}/checkpoint_run${run}_${NUM_STEPS}.pkl"
        if [ -f "${src_pkl}" ]; then
            mv "${src_pkl}" "${dest_pkl}" 2>/dev/null || cp "${src_pkl}" "${dest_pkl}"
            echo "✓ [${EASY_NAME}] Saved checkpoint to ${dest_pkl}"
        fi
        
        # Move trajectory log
        src_file="logs_${MODEL}/run_${run}_trajectory.txt"
        dest_file="final_results/logs/conditioning/goal_switching/${EASY_NAME}/run_${run}_trajectory_${NUM_STEPS}_steps.txt"
        if [ -f "${src_file}" ]; then
            mv "${src_file}" "${dest_file}" 2>/dev/null || cp "${src_file}" "${dest_file}"
            echo "✓ [${EASY_NAME}] Saved trajectory to ${dest_file}"
        fi
        
        echo "✓ [${EASY_NAME}] Completed run ${run}"
    done
    
    echo ""
    echo "✓✓✓ [${EASY_NAME}] Completed all runs ✓✓✓"
}

# Export function and variables for parallel execution
export -f run_model
export SOURCE TARGET NUM_STEPS CHECKPOINT_FILE
export RUNS_ARRAY

echo ""
echo "========================================"
echo "Starting Goal Switching Conditioning Simulations"
echo "Running up to ${MAX_PARALLEL} models in parallel"
echo "========================================"

# Run models in parallel using background jobs
running_jobs=0
for model_entry in "${MODELS[@]}"; do
    # Run the model in background
    run_model "${model_entry}" &
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

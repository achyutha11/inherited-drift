#!/bin/bash
# Adversarial Pressure Conditioning Simulation Runner
# All simulations branch from the same checkpoint: gpt-4o-mini run 5 step 45
# This allows comparing how different models behave when continuing from the same state

SOURCE="insurance"
TARGET="needs"
NUM_STEPS="55"  # Total steps (resumes from step 45)

# Fixed checkpoint - all conditioning runs branch from this same point
CHECKPOINT_FILE="final_results/data/basic/adv_pressure/gpt-4o-mini/checkpoint_run5_45.pkl"

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

# Check if base checkpoint exists
if [ ! -f "${CHECKPOINT_FILE}" ]; then
    echo "❌ Base checkpoint not found: ${CHECKPOINT_FILE}"
    echo "Please run basic adv_pressure simulations for gpt-4o-mini first."
    exit 1
fi

# Run simulations for each model
for model_entry in "${MODELS[@]}"; do
    # Split model entry into API name and display name
    IFS='|' read -r MODEL EASY_NAME <<< "${model_entry}"
    
    echo ""
    echo "========================================"
    echo "Starting ${EASY_NAME} conditioning simulations"
    echo "(All runs branch from gpt-4o-mini run 5 step 45)"
    echo "========================================"
    
    # Create output directories if they don't exist
    mkdir -p "final_results/data/conditioning/adv_pressure/${EASY_NAME}"
    mkdir -p "final_results/logs/conditioning/adv_pressure/${EASY_NAME}"
    
    for run in "${RUNS_ARRAY[@]}"; do
        echo ""
        echo "Running ${EASY_NAME} conditional adv pressure simulation (run ${run})..."
        
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
            echo "❌ Error occurred during ${EASY_NAME} simulation (run ${run})"
            echo "Continuing to next run..."
            continue
        fi
        
        # Move results JSON
        src_json="results.json"
        dest_json="final_results/data/conditioning/adv_pressure/${EASY_NAME}/checkpoint_run${run}_$((NUM_STEPS + 1)).json"
        if [ -f "${src_json}" ]; then
            mv "${src_json}" "${dest_json}"
            echo "✓ Saved results to ${dest_json}"
        fi
        
        # Move checkpoint pickle
        src_pkl="checkpoints/checkpoint_run${run}_${NUM_STEPS}.pkl"
        dest_pkl="final_results/data/conditioning/adv_pressure/${EASY_NAME}/checkpoint_run${run}_${NUM_STEPS}.pkl"
        if [ -f "${src_pkl}" ]; then
            mv "${src_pkl}" "${dest_pkl}"
            echo "✓ Saved checkpoint to ${dest_pkl}"
        fi
        
        # Move trajectory log
        src_file="logs_${MODEL}/run_${run}_trajectory.txt"
        dest_file="final_results/logs/conditioning/adv_pressure/${EASY_NAME}/run_${run}_trajectory_${NUM_STEPS}_steps.txt"
        if [ -f "${src_file}" ]; then
            mv "${src_file}" "${dest_file}"
            echo "✓ Saved trajectory to ${dest_file}"
        fi
        
        echo "✓ Completed run ${run} for ${EASY_NAME}"
    done
    
    echo ""
    echo "Completed all runs for ${EASY_NAME}"
done

echo ""
echo "========================================"
echo "All conditioning simulations completed!"
echo "========================================"

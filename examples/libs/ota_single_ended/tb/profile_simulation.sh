#!/bin/bash

# Simulation profiling script for ngspice
# Usage: ./profile_simulation.sh [number_of_runs]

SPICE_FILE="./tb_ota_5t.spice"
RUNS=${1:-5}  # Default to 5 runs if not specified

echo "Profiling ngspice simulation: $SPICE_FILE"
echo "Number of runs: $RUNS"
echo "=========================================="

# Arrays to store timing data
declare -a real_times
declare -a user_times
declare -a sys_times
declare -a memory_usage

# Run the simulation multiple times
for i in $(seq 1 $RUNS); do
    echo "Run $i of $RUNS..."
    
    # Capture timing info using a temporary file to avoid parsing issues
    TEMP_FILE=$(mktemp)
    /usr/bin/time -l ngspice -b "$SPICE_FILE" 2>"$TEMP_FILE" >/dev/null
    
    # Extract timing information more reliably
    REAL_TIME=$(grep "real" "$TEMP_FILE" | awk '{print $1}')
    USER_TIME=$(grep "real" "$TEMP_FILE" | awk '{print $2}')
    SYS_TIME=$(grep "real" "$TEMP_FILE" | awk '{print $4}')
    MAX_MEM=$(grep "maximum resident set size" "$TEMP_FILE" | awk '{print $1}')
    
    real_times+=($REAL_TIME)
    user_times+=($USER_TIME)
    sys_times+=($SYS_TIME)
    memory_usage+=($MAX_MEM)
    
    echo "  Real: ${REAL_TIME}s, User: ${USER_TIME}s, Sys: ${SYS_TIME}s, Memory: ${MAX_MEM} bytes"
    
    rm "$TEMP_FILE"
done

echo "=========================================="
echo "SUMMARY STATISTICS:"

# Calculate averages
real_sum=0
user_sum=0
sys_sum=0
mem_sum=0

for time in "${real_times[@]}"; do
    real_sum=$(echo "$real_sum + $time" | bc -l)
done

for time in "${user_times[@]}"; do
    user_sum=$(echo "$user_sum + $time" | bc -l)
done

for time in "${sys_times[@]}"; do
    sys_sum=$(echo "$sys_sum + $time" | bc -l)
done

for mem in "${memory_usage[@]}"; do
    mem_sum=$(echo "$mem_sum + $mem" | bc -l)
done

avg_real=$(echo "scale=4; $real_sum / $RUNS" | bc -l)
avg_user=$(echo "scale=4; $user_sum / $RUNS" | bc -l)
avg_sys=$(echo "scale=4; $sys_sum / $RUNS" | bc -l)
avg_mem=$(echo "scale=0; $mem_sum / $RUNS" | bc -l)

echo "Average Real Time: ${avg_real}s"
echo "Average User Time: ${avg_user}s"
echo "Average System Time: ${avg_sys}s"
echo "Average Memory Usage: ${avg_mem} bytes ($(echo "scale=2; $avg_mem / 1024 / 1024" | bc -l) MB)"

# Find min and max
IFS=$'\n'
real_sorted=($(printf '%s\n' "${real_times[@]}" | sort -n))
user_sorted=($(printf '%s\n' "${user_times[@]}" | sort -n))
sys_sorted=($(printf '%s\n' "${sys_times[@]}" | sort -n))
mem_sorted=($(printf '%s\n' "${memory_usage[@]}" | sort -n))
unset IFS

min_real=${real_sorted[0]}
max_real=${real_sorted[$((${#real_sorted[@]}-1))]}
min_user=${user_sorted[0]}
max_user=${user_sorted[$((${#user_sorted[@]}-1))]}
min_sys=${sys_sorted[0]}
max_sys=${sys_sorted[$((${#sys_sorted[@]}-1))]}
min_mem=${mem_sorted[0]}
max_mem=${mem_sorted[$((${#mem_sorted[@]}-1))]}

echo "Real Time Range: ${min_real}s - ${max_real}s"
echo "User Time Range: ${min_user}s - ${max_user}s"
echo "System Time Range: ${min_sys}s - ${max_sys}s"
echo "Memory Range: ${min_mem} - ${max_mem} bytes"
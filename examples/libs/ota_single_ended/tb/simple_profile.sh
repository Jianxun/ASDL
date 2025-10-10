#!/bin/bash

# Simple simulation profiling script for ngspice
# Usage: ./simple_profile.sh [number_of_runs]

SPICE_FILE="./tb_ota_5t.spice"
RUNS=${1:-5}

echo "Profiling ngspice simulation: $SPICE_FILE"
echo "Number of runs: $RUNS"
echo "=========================================="

for i in $(seq 1 $RUNS); do
    echo "Run $i of $RUNS:"
    echo "  Using time command:"
    time ngspice -b "$SPICE_FILE" 2>/dev/null
    echo ""
    echo "  Using detailed time command:"
    /usr/bin/time -p ngspice -b "$SPICE_FILE" 2>/dev/null
    echo ""
    echo "----------------------------------------"
done

echo ""
echo "For memory profiling, run:"
echo "/usr/bin/time -l ngspice -b $SPICE_FILE"

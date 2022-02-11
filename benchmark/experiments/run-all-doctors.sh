#!/usr/bin/env bash

set -e

/bin/rm -rf results
for doctor_program in programs/doctors-q*; do
  python ./benchmark/experiments/run-scalability-experiment --timeout 300.0 \
    --output-dir results/"$(basename "${doctor_program}")" \
    --tool dlv \
    --tool vadalog \
    --dataset-dir datasets/doctors \
    --program-dir "${doctor_program}"
done

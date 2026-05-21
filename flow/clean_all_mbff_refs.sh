#!/bin/bash

alphas=(2 4 8 16 67 130 193 256)
b=0.1

for alpha in "${alphas[@]}"
do
  echo "Running flow for design: $design with alpha: $alpha and beta: $b"
  make clean_all DESIGN_CONFIG=./designs/asap7/cva6/config.mk \
      FLOW_VARIANT="baseline_alpha_$alpha-beta_$b"
done

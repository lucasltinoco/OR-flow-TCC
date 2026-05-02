#!/bin/bash

list=$(ls ./designs/asap7)
alphas=(2 4 8 16 67 130 193 256)
b=0.1

bypass_list=(
  "cva6"
  "mock-cpu"
)

for design in $list
do
  # if design is cva6, continue
  if [[ " ${bypass_list[@]} " =~ " ${design} " ]]; then
    echo "Skipping design: $design"
    continue
  fi
  for alpha in "${alphas[@]}"
  do
    echo "Cleaning flow for design: $design with alpha: $alpha and beta: $b"
    make clean_all DESIGN_CONFIG=./designs/asap7/$design/config.mk \
        FLOW_VARIANT="modified_alpha_$alpha-beta_$b"
  done
done
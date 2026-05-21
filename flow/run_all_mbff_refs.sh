#!/bin/bash

list=$(ls ./designs/asap7)
alphas=(2 4 8 16 67 130 193 256)
b=0.1

bypass_list=()

cd ..
./build_openroad.sh --local --or_branch baseline
cd flow

for design in $list
do
  # if design is cva6, continue
  if [[ " ${bypass_list[@]} " =~ " ${design} " ]]; then
    echo "Skipping design: $design"
    continue
  fi
  for alpha in "${alphas[@]}"
  do
    echo "Running flow for design: $design with alpha: $alpha and beta: $b"
    make DESIGN_CONFIG=./designs/asap7/$design/config.mk \
        FLOW_VARIANT="baseline_alpha_$alpha-beta_$b" \
        ALPHA=$alpha \
        BETA=$b \
        EQUIVALENCE_CHECK=0 \
        LEC_CHECK=0 \
        CLUSTER_FLOPS=1
  done
done
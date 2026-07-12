#!/bin/bash

list=$(ls ./designs/asap7)
# alphas=(2 4 8 16 67 130 193 256)
alphas=(8)
b=0.1

exclusive_designs=()

bypass_list=(
  aes_lvt
  aes-block
  aes-block_aes_rcon
  aes-block_aes_sbox
  aes-mbff
  aes-mbff-tcc-v1
  ethmac_lvt
  gcd-ccs
  jpeg_lvt
  riscv32i-mock-sram
  riscv32i-mock-sram_fakeram7_256x32
  swerv_wrapper
  mock-cpu
)

cd ..
rm -rf tools/OpenROAD/build
./build_openroad.sh --local --or_branch tcc-mcf
cd flow

RUNTIME_ITER=3

for ((i=(1+RUNTIME_ITER); i<=RUNTIME_ITER*2; i++))
do
  echo "Iteration $i of $RUNTIME_ITER"
  if [ ${#exclusive_designs[@]} -ne 0 ]; then
    echo "Running flow for exclusive designs"
    for design in "${exclusive_designs[@]}"
    do
      for alpha in "${alphas[@]}"
      do
        echo "Running flow for design: $design with alpha: $alpha and beta: $b"
        make DESIGN_CONFIG=./designs/asap7/$design/config.mk \
            FLOW_VARIANT="modified_alpha_$alpha-beta_$b-v3_run_$i" \
            ALPHA=$alpha \
            BETA=$b \
            EQUIVALENCE_CHECK=0 \
            LEC_CHECK=0 \
            CLUSTER_FLOPS=1
      done
    done
  else
    echo "Running flow for all designs"
    for design in $list
    do
      if [[ " ${bypass_list[@]} " =~ " ${design} " ]]; then
        echo "Skipping design: $design"
        continue
      fi
      for alpha in "${alphas[@]}"
      do
        echo "Running flow for design: $design with alpha: $alpha and beta: $b"
        make DESIGN_CONFIG=./designs/asap7/$design/config.mk \
            FLOW_VARIANT="modified_mcf_alpha_$alpha-beta_$b-run$i" \
            ALPHA=$alpha \
            BETA=$b \
            EQUIVALENCE_CHECK=0 \
            LEC_CHECK=0 \
            CLUSTER_FLOPS=1
      done
    done
  fi
done
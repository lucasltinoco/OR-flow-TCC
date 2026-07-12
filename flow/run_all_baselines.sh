#!/bin/bash

list=$(ls ./designs/asap7)

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
./build_openroad.sh --local --or_branch baseline
cd flow

RUNTIME_ITER=3

for ((i=(1+RUNTIME_ITER); i<=RUNTIME_ITER*2; i++))
do
  echo "Iteration $i of $RUNTIME_ITER"
  for design in $list
  do
    if [[ " ${bypass_list[@]} " =~ " ${design} " ]]; then
      echo "Skipping design: $design"
      continue
    fi
    echo "Running flow for design: $design"
    make DESIGN_CONFIG=./designs/asap7/$design/config.mk \
        FLOW_VARIANT="base-run$i" \
        EQUIVALENCE_CHECK=0 \
        LEC_CHECK=0
  done
done

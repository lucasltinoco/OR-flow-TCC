#!/bin/bash

cd ..
./build_openroad.sh --local --or_branch baseline
cd flow

list=$(ls ./designs/asap7)

for design in $list
do
  echo "Running flow for design: $design"
  make DESIGN_CONFIG=./designs/asap7/$design/config.mk \
       EQUIVALENCE_CHECK=0
done

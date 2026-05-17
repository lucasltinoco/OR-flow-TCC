#!/bin/bash

alphas=(2 4 8 16 67 130 193 256)
b=0.1

for alpha in "${alphas[@]}"
do
  make FLOW_VARIANT="alpha_$alpha-beta_$b" \
       ALPHA=$alpha \
       BETA=$b \
       EQUIVALENCE_CHECK=0
done

# betas=(0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4 1.5)
# a=130

# for beta in "${betas[@]}"
# do
#   make FLOW_VARIANT="alpha_$a-beta_$beta" \
#        ALPHA=$a \
#        BETA=$beta \
#        EQUIVALENCE_CHECK=0
# done

# python3 ff_comparison.py
# python3 ff_comparison_pivot.py
# python3 asap7_comparison_pct_paired.py
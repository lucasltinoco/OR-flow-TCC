#!/bin/sh

./build_openroad.sh --local --clean-force

cd flow

./run_all_modified_mbffs.sh

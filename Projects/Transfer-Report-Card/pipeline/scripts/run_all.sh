#!/bin/bash
# Full rebuild. Run from anywhere; expects raw inputs listed in ../REFRESH.md.
set -e
cd "$(dirname "$0")"
bash runall9.sh   # stats + signings + model + page data (runall7 then runall8)
echo "done: copy trc/index.html to Projects/Transfer-Report-Card/index.html"

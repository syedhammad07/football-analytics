cd /home/claude/work; rm -f r13.out
for s in build3b build4b build4c build4d build_sig; do python3 -I $s.py > $s.out 2>&1 || { echo FAIL $s > r13.out; exit; }; done
bash runall6.sh
echo ALLDONE7 >> r13.out

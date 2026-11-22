cd /home/claude/work; rm -f r12.out
python3 -I build5b.py > r2.out 2>&1 && python3 -I model.py > r3.out 2>&1 && cp signings_model.csv top5_signings_scored_2010_2025.csv && python3 -I build6.py > r4.out 2>&1
cd /home/claude/trc && python3 build_data.py > r5.out 2>&1 && python3 build_detail.py >> r5.out 2>&1 && python3 build_evidence.py >> r5.out 2>&1
echo ALLDONE6 > /home/claude/work/r12.out

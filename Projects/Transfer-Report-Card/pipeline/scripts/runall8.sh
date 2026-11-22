cd /home/claude/work; rm -f r14.out
python3 -I build_players.py > bp.out 2>&1 || { echo FAILbp > r14.out; exit; }
cp players.json /home/claude/trc/ 2>/dev/null; cp player_seasons_2009_2025.csv /home/claude/trc/ 2>/dev/null
cd /home/claude/trc && python3 build_page.py >> r5.out 2>&1 || { echo FAIL > /home/claude/work/r14.out; exit; }
echo DONE8 > /home/claude/work/r14.out

#!/usr/bin/env bash
# One-time setup: creates the GitHub repo, labels, milestones, a starter backlog,
# and the "Portfolio" project board with custom fields.
#
# Requirements: git, GitHub CLI (gh) logged in with project scope:
#   gh auth login
#   gh auth refresh -s project
# Run from inside this folder:  bash setup.sh
set -euo pipefail

REPO_NAME="football-analytics"
PROJECT_TITLE="Portfolio"
AREA="Football analytics"

USER=$(gh api user --jq .login)
echo "GitHub user: $USER"

# Portable in-place replace (works on Linux, macOS, Git Bash)
replace() { sed "s|$1|$2|g" "$3" > "$3.tmp" && mv "$3.tmp" "$3"; }

# ---------- 1. Project board (create once, reuse for every repo) ----------
PROJECT_NUM=$(gh project list --owner "@me" --format json \
  --jq ".projects[] | select(.title==\"$PROJECT_TITLE\") | .number" | head -n1)

if [ -z "$PROJECT_NUM" ]; then
  echo "Creating project '$PROJECT_TITLE'..."
  PROJECT_NUM=$(gh project create --owner "@me" --title "$PROJECT_TITLE" --format json --jq .number)
  gh project field-create "$PROJECT_NUM" --owner "@me" --name "Priority" \
    --data-type SINGLE_SELECT --single-select-options "High,Medium,Low"
  gh project field-create "$PROJECT_NUM" --owner "@me" --name "Area" \
    --data-type SINGLE_SELECT \
    --single-select-options "Football analytics,Machine learning,Dashboards,RAG and LLMs,Python apps,SQL"
  gh project field-create "$PROJECT_NUM" --owner "@me" --name "Target date" --data-type DATE
else
  echo "Using existing project '$PROJECT_TITLE' (#$PROJECT_NUM)"
fi

# Fill in your username and project number in the README and workflow
replace "<your-username>" "$USER" README.md
replace "<your-username>" "$USER" .github/ISSUE_TEMPLATE/linkedin-post.md
replace "YOUR_USERNAME" "$USER" .github/workflows/add-to-project.yml
replace "YOUR_PROJECT_NUMBER" "$PROJECT_NUM" .github/workflows/add-to-project.yml

# ---------- 2. Git repo + push ----------
if [ ! -d .git ]; then
  git init -q
  git add .
  git commit -q -m "Initial commit: project structure, docs and templates"
  git branch -M main
fi
if ! gh repo view "$USER/$REPO_NAME" >/dev/null 2>&1; then
  gh repo create "$REPO_NAME" --public --source=. --remote=origin --push \
    --description "Player performance analysis with StatsBomb open data"
fi
R="$USER/$REPO_NAME"

# ---------- 3. Labels ----------
gh label create task      --repo "$R" --color 1D76DB --description "Work item"            --force
gh label create research  --repo "$R" --color 5319E7 --description "Question to answer"   --force
gh label create data      --repo "$R" --color 0E8A16 --description "Data collection/cleaning" --force
gh label create viz       --repo "$R" --color FBCA04 --description "Charts and dashboards" --force
gh label create model     --repo "$R" --color D93F0B --description "Machine learning"      --force
gh label create linkedin  --repo "$R" --color 0A66C2 --description "LinkedIn post"         --force

# ---------- 4. Milestones ----------
mk_milestone() {
  gh api "repos/$R/milestones" -f title="$1" -f description="$2" >/dev/null 2>&1 || true
}
mk_milestone "v0.1 Data ready"   "Environment set up, data downloaded, cleaned and documented"
mk_milestone "v0.2 EDA"          "Exploratory analysis and first visualisations"
mk_milestone "v1.0 Model and write-up" "Scouting model, verified results, README and LinkedIn post"

# ---------- 5. Starter backlog ----------
PROJECT_ID=$(gh project view "$PROJECT_NUM" --owner "@me" --format json --jq .id)
field_id() {
  gh project field-list "$PROJECT_NUM" --owner "@me" --format json \
    --jq ".fields[] | select(.name==\"$1\") | .id"
}
option_id() {
  gh project field-list "$PROJECT_NUM" --owner "@me" --format json \
    --jq ".fields[] | select(.name==\"$1\") | .options[] | select(.name==\"$2\") | .id"
}

AREA_FIELD=$(field_id "Area");  AREA_OPT=$(option_id "Area" "$AREA")
PRIO_FIELD=$(field_id "Priority")
PRIO_High=$(option_id Priority High)
PRIO_Medium=$(option_id Priority Medium)
PRIO_Low=$(option_id Priority Low)

new_issue() { # title, labels, milestone, priority, body
  url=$(gh issue create --repo "$R" --title "$1" --label "$2" --milestone "$3" --body "$5")
  item=$(gh project item-add "$PROJECT_NUM" --owner "@me" --url "$url" --format json --jq .id)
  gh project item-edit --id "$item" --project-id "$PROJECT_ID" --field-id "$AREA_FIELD" --single-select-option-id "$AREA_OPT" >/dev/null
  gh project item-edit --id "$item" --project-id "$PROJECT_ID" --field-id "$PRIO_FIELD" --single-select-option-id "$(eval echo "\$PRIO_$4")" >/dev/null
  echo "  + $1"
}

echo "Creating starter backlog..."
M1="v0.1 Data ready"; M2="v0.2 EDA"; M3="v1.0 Model and write-up"

new_issue "Set up Python environment and install requirements" task "$M1" High \
"- [ ] Create .venv
- [ ] pip install -r requirements.txt and pip install -e .
- [ ] Open JupyterLab successfully"

new_issue "Choose a competition and download StatsBomb data" data "$M1" High \
"- [ ] List competitions with python -m football_analytics.data
- [ ] Pick one season with enough matches
- [ ] Download and record ids in docs/dataset.md"

new_issue "Write the data dictionary in docs/dataset.md" data "$M1" Medium \
"- [ ] Row counts for matches and events
- [ ] Describe the fields used"

new_issue "Clean events and compute minutes played per player" data "$M1" High \
"- [ ] Drop events without a player
- [ ] Minutes played per player per match
- [ ] Save to data/processed/
- [ ] Log steps in the cleaning table"

new_issue "EDA: shots, goals and xG per 90 by player" research "$M2" High \
"- [ ] notebooks/01_eda.ipynb
- [ ] Filter players with at least 450 minutes
- [ ] Top 15 by xG per 90 and goals minus xG"

new_issue "EDA: passing and progression by position" research "$M2" Medium \
"- [ ] Progressive passes and carries per 90
- [ ] Compare positions"

new_issue "Pitch visualisations with mplsoccer" viz "$M2" Medium \
"- [ ] Shot map for one player
- [ ] Pass network for one team
- [ ] Save PNGs to reports/figures/"

new_issue "Build a player feature table (per-90 metrics)" model "$M3" High \
"- [ ] One row per player
- [ ] 10 to 15 per-90 features
- [ ] Document features in docs/dataset.md"

new_issue "Cluster players into playing styles" model "$M3" Medium \
"- [ ] Scale features, try k-means
- [ ] Choose k and name the clusters
- [ ] Record the choice in docs/decisions/"

new_issue "Flag under-rated players with a simple model" model "$M3" Medium \
"- [ ] Define the target and a baseline
- [ ] Evaluate honestly, note limitations"

new_issue "Write verified results and update the README" task "$M3" High \
"- [ ] docs/results.md complete with evidence links
- [ ] Key findings section in README
- [ ] Best 2 to 3 charts embedded"

new_issue "LinkedIn: share the football analytics project" linkedin "$M3" Low \
"Draft from docs/results.md only. Add the published post URL here when done."

echo
echo "Done."
echo "Repo:    https://github.com/$R"
echo "Project: https://github.com/users/$USER/projects/$PROJECT_NUM"
echo "Remaining manual steps: see SETUP.md (Sprint field, board view, PAT secret)."

# Setup guide

Takes about 15 minutes. You can delete this file once you've finished.

## 1. Install the tools (once)

| Tool | Install |
| --- | --- |
| Git | https://git-scm.com/downloads. On Windows this also installs **Git Bash**; run the commands below there |
| GitHub CLI | https://cli.github.com |
| Python 3.10+ | https://www.python.org/downloads |

Then log in and give the CLI permission to manage projects:

```bash
gh auth login            # choose GitHub.com → HTTPS → log in with browser
gh auth refresh -s project
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

## 2. Run the setup script

Unzip this folder wherever you keep your code. Then run:

```bash
cd football-analytics
bash setup.sh
```

The script:

- creates the **Portfolio** project with the Priority, Area and Target date fields. If the project already exists, it reuses it.
- creates the public `football-analytics` repo and pushes these files to it.
- adds labels and three milestones (v0.1, v0.2, v1.0).
- creates 12 starter issues and puts each one on the board with Area and Priority set.

## 3. Finish the board in the browser (2 minutes)

Open the project link that the script prints, then:

1. **Add the Sprint field.** Click **+** on the field header, then **New field**, name it `Sprint`, choose type **Iteration** and set the duration to 2 weeks. The CLI can't create iteration fields, so this step is manual.
2. **Board view.** Make sure the view is set to **Board** and grouped by **Status**.
3. **Second view.** Add a **Table** view grouped by **Area**. You'll see each project separately once more repos join the board.
4. **Third view.** Add a **Roadmap** view that uses **Target date**.
5. **Workflows.** Open the **⋯** menu, then **Workflows**, and check that "Item closed" and "Pull request merged" both set Status to **Done**.

## 4. Daily routine

```bash
git switch -c eda-xg-per-90          # one branch per issue
# ... work in notebooks/ and src/ ...
git add .
git commit -m "EDA: xG per 90 for players with 450+ minutes"
git push -u origin eda-xg-per-90
gh pr create --fill --body "Closes #5"
gh pr merge --squash --delete-branch
git switch main && git pull
```

When the PR merges, issue #5 closes and its card moves to **Done** on its own.

## 5. Optional: auto-add future issues to the board

The included workflow `.github/workflows/add-to-project.yml` adds every new issue and PR to the Portfolio board. It needs a token, because user-level projects can't be reached with the default Actions token.

1. Go to GitHub, then **Settings**, then **Developer settings**, then **Personal access tokens**, then **Tokens (classic)**, then **Generate new token**.
2. Select the scopes **`project`** and **`repo`**. Set an expiry, for example 90 days.
3. In the repo, go to **Settings**, then **Secrets and variables**, then **Actions**, then **New repository secret**. Name it `ADD_TO_PROJECT_PAT` and paste the token.

Until you do this, the workflow fails harmlessly, and you can add issues from the issue's sidebar instead.

## 6. Reusing this for your next project

Copy this folder, rename it, change `REPO_NAME` and `AREA` at the top of `setup.sh`, and replace the backlog issues. The script finds the existing Portfolio board and adds the new repo's issues to it.

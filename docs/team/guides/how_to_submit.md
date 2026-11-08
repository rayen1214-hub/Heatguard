# How to hand in your work

Your work must reach the repo **from your own GitHub account**, because the commit history is used as
evidence of who did what (rubric A6 and C4). You don't need to install git. Pick one method.

## Method A: GitHub website (easiest, 3 minutes)

**To fill in an existing file** (for example a template in `docs/team/`):

1. Open https://github.com/rayen1214-hub/Heatguard and sign in.
2. Click through the folders to the file, then click the **pencil icon** (Edit) at the top right of the file.
3. Make your changes.
4. Click **Commit changes…**. In the box, write one line saying what you did, for example
   `Manual test cases M-01 to M-06 (Jaanvi)`.
5. Choose **"Create a new branch for this commit and start a pull request"**. Name the branch after
   yourself and the task, for example `jaanvi-manual-tests`. Click **Propose changes**, then **Create pull request**.
6. Tell Rayen in the group chat. He reviews and merges it.

**To add a new file** (a Word document, a screenshot, a PDF): open the folder, click **Add file → Upload files**,
drag the file in, then do steps 4–6.

Only documents go in `docs/`. If your task produces a Word file, also save it in the shared group folder, but the
GitHub copy is the one that counts as evidence.

## Method B: git on your laptop

```bash
git clone https://github.com/rayen1214-hub/Heatguard.git
cd Heatguard
git checkout -b yourname-task          # your own branch, never main
# ... edit files ...
git add docs/team/...                  # only the files you changed
git commit -m "What you did (Your name)"
git push -u origin yourname-task
```

Then open the link git prints and create a pull request.

## After you hand in

- Copy the **commit hash** (the 7-character code next to your commit on GitHub, for example `3fa9c21`).
- Paste it into your row in [`../../../CONTRIBUTIONS.md`](../../../CONTRIBUTIONS.md) under "Commits / evidence".
- Tick the task in your task file.

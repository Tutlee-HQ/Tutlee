"""
Run this from the project root to commit and push all recent changes to GitHub.
Usage: python push_changes.py
"""
import subprocess, sys, os

root = os.path.dirname(os.path.abspath(__file__))

def run(cmd):
    print(f"$ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
    if r.stdout: print(r.stdout)
    if r.stderr: print(r.stderr)
    return r.returncode

# Configure git if needed
run('git config user.email "dahomaconsulting@gmail.com"')
run('git config user.name "Tutlee"')

# Stage all changed files
files = [
    "api.js",
    "index.html",
    "admin.html",
    "backend/accounts/permissions.py",
    "backend/accounts/views.py",
    "backend/kyt/views.py",
    "backend/assessments/views.py",
    "backend/payments/views.py",
    "backend/reports/views.py",
    "backend/study_rings/views.py",
    "backend/study_rings/serializers.py",
    "push_changes.py",
]

for f in files:
    run(f'git add "{f}"')

# Commit
msg = "Fix page reload restore, study ring join for all users, admin KYT docs, admin CRUD bulk-select, study rings admin live data"
run(f'git commit -m "{msg}"')

# Push
code = run("git push origin main")
if code != 0:
    code = run("git push origin master")

if code == 0:
    print("\n✅ Successfully pushed to GitHub!")
else:
    print("\n❌ Push failed — check git remote and credentials.")
    print("   Run: git remote -v   to see your remote URL")

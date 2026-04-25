# Commit script
cd D:\bird\bird
git config core.autocrlf true
git commit -F - <<'EOF'
Update bird coordinates
EOF
git status
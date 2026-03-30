#!/bin/bash
# Setup script for GitHub repository creation and push

set -e

echo "=== GitHub Repository Setup ==="
echo
echo "This script will help you create a GitHub repository and push your code."
echo

# Check if remote is already configured
if git remote -v | grep -q origin; then
    echo "Remote 'origin' is already configured:"
    git remote -v
    echo
    read -p "Do you want to reconfigure it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote remove origin
    else
        echo "Keeping existing remote."
    fi
fi

# Get GitHub username
read -p "Enter your GitHub username [claireyu]: " GITHUB_USERNAME
GITHUB_USERNAME=${GITHUB_USERNAME:-githubclaire}

# Get repository name
read -p "Enter repository name [ddr_timingtable_gen_tool]: " REPO_NAME
REPO_NAME=${REPO_NAME:-ddr_timingtable_gen_tool}

# Choose protocol
echo
echo "Choose authentication method:"
echo "1) SSH (requires SSH key added to GitHub)"
echo "2) HTTPS (requires personal access token)"
read -p "Enter choice [1]: " PROTOCOL_CHOICE
PROTOCOL_CHOICE=${PROTOCOL_CHOICE:-1}

if [[ $PROTOCOL_CHOICE == "1" ]]; then
    REMOTE_URL="git@github.com:${GITHUB_USERNAME}/${REPO_NAME}.git"
else
    REMOTE_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
fi

echo
echo "=== Summary ==="
echo "GitHub username: $GITHUB_USERNAME"
echo "Repository name: $REPO_NAME"
echo "Remote URL: $REMOTE_URL"
echo

# Check if repository exists
echo "Checking if repository exists on GitHub..."
if curl -s -I "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}" | grep -q "200 OK"; then
    echo "✓ Repository exists."
    REPO_EXISTS=true
elif curl -s -I "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}" | grep -q "404"; then
    echo "✗ Repository does not exist."
    REPO_EXISTS=false
else
    echo "? Could not determine repository status."
    REPO_EXISTS=false
fi

echo
if [[ $REPO_EXISTS == false ]]; then
    echo "The repository does not exist on GitHub."
    echo "Please create it first:"
    echo "  1. Go to https://github.com/new"
    echo "  2. Set repository name to: $REPO_NAME"
    echo "  3. Choose public or private"
    echo "  4. DO NOT initialize with README, .gitignore, or license"
    echo "  5. Click 'Create repository'"
    echo
    read -p "Press Enter after you have created the repository..."
fi

# Set remote
echo "Setting remote origin to: $REMOTE_URL"
git remote add origin "$REMOTE_URL" 2>/dev/null || git remote set-url origin "$REMOTE_URL"

echo
echo "=== Pushing to GitHub ==="
echo

if [[ $PROTOCOL_CHOICE == "2" ]]; then
    echo "For HTTPS authentication, you will need a personal access token."
    echo "If you don't have one, create it at: https://github.com/settings/tokens"
    echo "Required scope: 'repo' (full control of private repositories)"
    echo
    echo "When prompted for password, enter your personal access token."
    echo
fi

echo "Pushing to GitHub..."
if git push -u origin master; then
    echo "✓ Successfully pushed to GitHub!"
    echo
    echo "Repository URL: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
else
    echo "✗ Failed to push to GitHub."
    echo
    echo "Troubleshooting:"
    echo "1. Ensure repository exists at: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
    if [[ $PROTOCOL_CHOICE == "1" ]]; then
        echo "2. Ensure SSH key is added to your GitHub account"
        echo "   Check: ssh -T git@github.com"
    else
        echo "2. Ensure you have a valid personal access token with repo scope"
    fi
    echo "3. Check your internet connection"
    exit 1
fi

echo
echo "=== Setup Complete ==="
echo "Your code is now on GitHub at: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
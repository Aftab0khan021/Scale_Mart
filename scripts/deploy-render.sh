#!/bin/bash
# Quick deployment script for Render.com

echo "🚀 ScaleMart - Render.com Deployment Helper"
echo "==========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for deployment"
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Check for GitHub remote
if ! git remote | grep -q origin; then
    echo ""
    echo "⚠️  No GitHub remote found"
    echo "Please create a GitHub repository and run:"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/ScaleMart.git"
    echo "  git push -u origin main"
    exit 1
fi

echo ""
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Prepare for Render deployment" || echo "No changes to commit"
git push origin main

echo ""
echo "✅ Code pushed to GitHub!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to https://dashboard.render.com"
echo "2. Click 'New +' → 'Blueprint'"
echo "3. Select your ScaleMart repository"
echo "4. Click 'Apply'"
echo "5. Wait 5-10 minutes for deployment"
echo ""
echo "🎉 Your app will be live at:"
echo "   https://scalemart-frontend.onrender.com"
echo ""

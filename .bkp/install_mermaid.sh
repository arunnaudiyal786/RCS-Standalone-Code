#!/bin/bash

# Install Mermaid CLI for PNG generation
# This script installs the Mermaid CLI globally using npm

echo "🔄 Installing Mermaid CLI..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js and npm first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check if Mermaid CLI is already installed
if command -v mmdc &> /dev/null; then
    echo "✅ Mermaid CLI is already installed:"
    mmdc --version
    exit 0
fi

# Install Mermaid CLI globally
echo "📦 Installing @mermaid-js/mermaid-cli..."
npm install -g @mermaid-js/mermaid-cli

# Check if installation was successful
if command -v mmdc &> /dev/null; then
    echo "✅ Mermaid CLI installed successfully!"
    mmdc --version
    echo ""
    echo "🎉 You can now run: python3 mermaid_graph_generator.py"
else
    echo "❌ Installation failed. Please try manually:"
    echo "   npm install -g @mermaid-js/mermaid-cli"
    exit 1
fi

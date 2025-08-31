#!/bin/bash

# ASDL Syntax Highlighter Installation Script
# This script installs the ASDL syntax highlighter extension for VS Code/Cursor

echo "🚀 Installing ASDL Syntax Highlighter..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the syntax-highlighter directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed. Please install npm first."
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies"
    exit 1
fi

echo "🔨 Compiling extension..."
npm run compile

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to compile extension"
    exit 1
fi

echo "✅ ASDL Syntax Highlighter installed successfully!"
echo ""
echo "To use the extension:"
echo "1. Open VS Code/Cursor"
echo "2. Press F5 to run the extension in debug mode"
echo "3. Open any .asdl file to see syntax highlighting"
echo ""
echo "Or install as a packaged extension:"
echo "1. Install vsce: npm install -g vsce"
echo "2. Package: vsce package"
echo "3. Install the generated .vsix file in VS Code/Cursor"
echo ""
echo "🎉 Happy ASDL coding!"




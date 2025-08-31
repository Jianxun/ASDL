#!/bin/bash

# ASDL Syntax Highlighter Packaging Script
# This script packages the extension for distribution

echo "📦 Packaging ASDL Syntax Highlighter..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the syntax-highlighter directory"
    exit 1
fi

# Check if vsce is installed
if ! command -v vsce &> /dev/null; then
    echo "📦 Installing vsce..."
    npm install -g vsce
fi

# Compile the extension
echo "🔨 Compiling extension..."
npm run compile

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to compile extension"
    exit 1
fi

# Package the extension
echo "📦 Creating VSIX package..."
vsce package

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to package extension"
    exit 1
fi

echo "✅ ASDL Syntax Highlighter packaged successfully!"
echo ""
echo "Generated files:"
ls -la *.vsix
echo ""
echo "To install the extension:"
echo "1. Open VS Code/Cursor"
echo "2. Go to Extensions (Ctrl+Shift+X)"
echo "3. Click the '...' menu and select 'Install from VSIX...'"
echo "4. Select the generated .vsix file"
echo ""
echo "🎉 Extension ready for distribution!"




#!/bin/bash

# ASDL Syntax Highlighter Build Script
# This script compiles and packages the extension into a VSIX distribution file

set -e  # Exit on any error

echo "🚀 Building ASDL Syntax Highlighter..."

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

# Check if vsce is installed
if ! command -v vsce &> /dev/null; then
    echo "📦 Installing vsce..."
    npm install -g vsce
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

echo "📦 Creating VSIX package..."
vsce package

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to package extension"
    exit 1
fi

echo ""
echo "✅ ASDL Syntax Highlighter built successfully!"
echo ""
echo "📁 Generated files:"
ls -la *.vsix
echo ""
echo "📊 Build Summary:"
echo "   - Extension compiled: ✅"
echo "   - VSIX package created: ✅"
echo "   - Package size: $(ls -la *.vsix | awk '{print $5}') bytes"
echo ""
echo "🎯 Next Steps:"
echo "1. Install the extension:"
echo "   - Open VS Code/Cursor"
echo "   - Go to Extensions (Ctrl+Shift+X)"
echo "   - Click '...' menu → 'Install from VSIX...'"
echo "   - Select the generated .vsix file"
echo ""
echo "2. Test the extension:"
echo "   - Open test-syntax.asdl"
echo "   - Check language mode shows 'ASDL'"
echo "   - Verify syntax highlighting works"
echo ""
echo "🎉 Build complete! Happy ASDL coding!"


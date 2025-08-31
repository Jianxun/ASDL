# Quick Start Guide - ASDL Syntax Highlighter

Get the ASDL syntax highlighter working in VS Code/Cursor in under 5 minutes!

## 🚀 Quick Installation

### Option 1: From Source (Recommended for development)
```bash
cd syntax-highlighter
./install.sh
```

### Option 2: Manual Installation
```bash
cd syntax-highlighter
npm install
npm run compile
```

## 🎯 Test the Extension

1. **Open VS Code/Cursor**
2. **Press `F5`** to run the extension in debug mode
3. **Open the demo file**: `File → Open File → syntax-highlighter/demo.asdl`
4. **See syntax highlighting in action!**

## ✨ What You'll See

- **Keywords** in blue: `dir`, `type`, `model`, `mappings`, etc.
- **Port directions** in green: `in`, `out`, `inout`
- **Port types** in orange: `signal`, `power`, `ground`, `bias`, `control`
- **Sections** in purple: `file_info`, `modules`, `imports`, `model_alias`
- **Numbers with units** in cyan: `0.18u`, `1u`
- **SPICE template parameters** in yellow: `{name}`, `{d}`, `{g}`
- **Comments** in gray: `# This is a comment`

## 🎮 Try These Commands

- **`Ctrl+Shift+P`** → "ASDL: Create New ASDL File"
- **`Ctrl+Shift+P`** → "ASDL: Validate ASDL Syntax"
- **Right-click** in editor → "Validate ASDL Syntax"

## 📝 Try These Snippets

Type these and press `Tab`:
- `asdl-file` - Complete file template
- `module` - Module definition
- `port` - Port definition
- `instance` - Instance definition
- `spice` - SPICE template

## 🔧 Customization

The extension automatically:
- Associates `.asdl` files with ASDL language
- Provides YAML-compatible indentation
- Offers bracket matching and auto-closing
- Integrates with VS Code's YAML support

## 🚨 Troubleshooting

**Extension not working?**
1. Check the Output panel (`View → Output → ASDL Syntax Highlighter`)
2. Ensure you're running in debug mode (`F5`)
3. Verify the file has `.asdl` extension

**No syntax highlighting?**
1. Check the language mode in the bottom-right corner
2. Should show "ASDL" not "Plain Text"
3. Try `Ctrl+Shift+P` → "Change Language Mode" → "ASDL"

## 🎉 You're Done!

Your ASDL files now have:
- ✅ Syntax highlighting
- ✅ Code snippets
- ✅ Basic validation
- ✅ YAML compatibility
- ✅ Professional editor experience

Happy ASDL coding! 🚀




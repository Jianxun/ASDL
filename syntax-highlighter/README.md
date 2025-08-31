# ASDL Syntax Highlighter for VS Code/Cursor

A comprehensive syntax highlighter and language support extension for ASDL (Analog System Description Language) files. **Note: ASDL is a fully legal YAML dialect**, which means it inherits all YAML syntax rules and can leverage existing YAML tooling.

## Features

### 🎨 **Syntax Highlighting**
- **YAML Base**: Full YAML syntax highlighting with ASDL-specific enhancements
- **ASDL Keywords**: `dir`, `type`, `model`, `mappings`, `spice_template`, `doc`, `top_module`, `ports`, `instances`
- **Port Directions**: `in`, `out`, `inout`
- **Port Types**: `signal`, `power`, `ground`, `bias`, `control`
- **Sections**: `file_info`, `modules`, `imports`, `model_alias`
- **Field Names**: Port names, instance names, and other identifiers
- **Numbers**: Integers, floats, scientific notation, and units (e.g., `0.18u`, `1u`)
- **Strings**: Single and double quoted strings with escape character support
- **Comments**: `#` line comments

### 🚀 **Developer Experience**
- **YAML Compatibility**: Leverages VS Code's built-in YAML support
- **Code Snippets**: Quick templates for common ASDL patterns
- **Auto-completion**: Intelligent suggestions for ASDL syntax
- **Bracket Matching**: Automatic bracket pairing and highlighting
- **Indentation Rules**: Smart indentation for YAML-like structures
- **Syntax Validation**: Basic validation of ASDL file structure
- **YAML Schema Support**: Can integrate with YAML schema validation

### 📝 **Code Snippets**
- `asdl-file` - Complete ASDL file template
- `module` - Module definition with ports and instances
- `port` - Port definition with direction and type
- `instance` - Instance definition with model and mappings
- `spice` - SPICE template for primitive modules
- `import` - Import statement for external files
- `alias` - Model alias mapping
- `fileinfo` - File information section

## Quick Start

### 🚀 **One-Command Build**
```bash
cd syntax-highlighter
./build.sh
```

This single command will:
- ✅ Install dependencies
- ✅ Compile the extension
- ✅ Create the VSIX package
- ✅ Show installation instructions

### 📦 **Installation**
1. **Run the build script**: `./build.sh`
2. **Open VS Code/Cursor**
3. **Go to Extensions** (`Ctrl+Shift+X`)
4. **Click the `...` menu** → **"Install from VSIX..."**
5. **Select the generated `.vsix` file**

### 🎯 **Test the Extension**
1. **Open `test-syntax.asdl`**
2. **Check language mode** shows "ASDL" (bottom-right corner)
3. **Verify syntax highlighting** with different colors

## Usage

### Basic Syntax Highlighting
Simply open any `.asdl` file and the extension will automatically provide syntax highlighting. Since ASDL is YAML-compliant, you also get all the benefits of VS Code's YAML support.

### Commands
- **Create New ASDL File**: `Ctrl+Shift+P` → "ASDL: Create New ASDL File"
- **Validate ASDL Syntax**: `Ctrl+Shift+P` → "ASDL: Validate ASDL Syntax" or right-click in editor

### Snippets
Type the snippet prefix (e.g., `asdl-file`) and press `Tab` to expand.

### YAML Integration
- **YAML Validation**: ASDL files can be validated using YAML validators
- **YAML Formatters**: Use YAML formatters to format ASDL files
- **YAML Extensions**: Compatible with other YAML-focused extensions

## ASDL Language Reference

### File Structure
```yaml
file_info:
  top_module: module_name
  doc: Description

imports:
  alias: file.asdl

model_alias:
  local_name: alias.module_name

modules:
  module_name:
    ports:
      port_name: { dir: in, type: signal }
    instances:
      instance_name: { model: model_name, mappings: { port: net } }
```

### Port Directions
- `in` - Input port
- `out` - Output port  
- `inout` - Bidirectional port

### Port Types
- `signal` - General signal (default)
- `power` - Power supply
- `ground` - Ground reference
- `bias` - Bias voltage
- `control` - Control signal

### SPICE Templates
Primitive modules use SPICE templates with placeholders:
```yaml
spice_template: "{name} {d} {g} {s} {b} nmos L=0.18u W=1u"
```

## YAML Compatibility Benefits

Since ASDL is a YAML dialect, you get:

- **Standard YAML Parsing**: Any YAML parser can read ASDL files
- **YAML Tools**: Use YAML linters, formatters, and validators
- **Schema Validation**: Potential for YAML schema-based validation
- **IDE Support**: Better support in editors that understand YAML
- **Documentation**: YAML documentation applies to ASDL
- **Standards Compliance**: Follows established YAML 1.2 specification

## Development

### Project Structure
```
syntax-highlighter/
├── src/
│   └── extension.ts          # Main extension logic
├── syntaxes/
│   └── asdl.tmLanguage.json  # TextMate grammar (extends YAML)
├── snippets/
│   └── asdl.json            # Code snippets
├── language-configuration.json # Language settings
├── package.json              # Extension manifest
├── tsconfig.json            # TypeScript config
├── build.sh                 # Single build script
├── install.sh               # Development installation
├── package.sh               # Packaging only
├── debug-extension.sh       # Troubleshooting
├── test-syntax.asdl         # Test file
├── demo.asdl                # Demo file
├── README.md                # This file
├── QUICKSTART.md            # Quick start guide
└── SUMMARY.md               # Project summary
```

### Build Commands
- **`./build.sh`** - Complete build and package (recommended)
- **`./install.sh`** - Development installation only
- **`./package.sh`** - Package existing build
- **`npm run compile`** - Compile TypeScript only
- **`npm run watch`** - Watch for changes and recompile

### Testing
Press `F5` in VS Code/Cursor to launch the extension in debug mode.

## Compatibility

- **VS Code**: ✅ Full support with YAML compatibility
- **Cursor**: ✅ Full support (VS Code compatible)
- **VS Code OSS**: ✅ Full support
- **GitHub Codespaces**: ✅ Full support
- **YAML Extensions**: ✅ Compatible with YAML-focused extensions

## Troubleshooting

### Extension Not Working?
1. **Check Extensions panel** - Ensure ASDL extension is enabled
2. **Check language mode** - Should show "ASDL" not "Plain Text"
3. **Reload window** - `Ctrl+Shift+P` → "Developer: Reload Window"
4. **Run debug script** - `./debug-extension.sh` for diagnostics

### No Syntax Highlighting?
1. **Check language mode** in bottom-right corner
2. **Manually select "ASDL"** if needed
3. **Verify file has `.asdl` extension**
4. **Check Output panel** for errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `./build.sh` to test
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.

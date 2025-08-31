import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('ASDL Syntax Highlighter is now active!');

    // Register ASDL language configuration
    const asdlLanguageConfig = vscode.languages.setLanguageConfiguration('asdl', {
        comments: {
            lineComment: '#'
        },
        brackets: [
            ['{', '}'],
            ['[', ']'],
            ['(', ')']
        ],
        autoClosingPairs: [
            { open: '{', close: '}' },
            { open: '[', close: ']' },
            { open: '(', close: ')' },
            { open: '"', close: '"' },
            { open: "'", close: "'" }
        ],
        indentationRules: {
            increaseIndentPattern: /^(.*\{[^}]*|.*\[[^\]]*|.*\([^)]*)$/,
            decreaseIndentPattern: /^(.*\}|.*\]|.*\))$/
        }
    });

    context.subscriptions.push(asdlLanguageConfig);

    // Register ASDL file association
    const asdlFileAssociation = vscode.workspace.registerTextDocumentContentProvider('asdl', {
        provideTextDocumentContent(uri: vscode.Uri): string {
            return `ASDL (Analog System Description Language) file: ${uri.path}`;
        }
    });

    context.subscriptions.push(asdlFileAssociation);

    // Register command to create new ASDL file
    let disposable = vscode.commands.registerCommand('asdl.createNewFile', () => {
        const template = `file_info:
  top_module: new_module
  doc: Description of the circuit

modules:
  new_module:
    ports:
      in: { dir: in, type: signal }
      out: { dir: out, type: signal }
      vdd: { dir: in, type: power }
      vss: { dir: in, type: ground }
    instances:
      # Add your instances here
`;
        
        vscode.workspace.openTextDocument({
            content: template,
            language: 'asdl'
        }).then(doc => {
            vscode.window.showTextDocument(doc);
        });
    });

    context.subscriptions.push(disposable);

    // Register command to validate ASDL syntax
    let validateCommand = vscode.commands.registerCommand('asdl.validateSyntax', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'asdl') {
            // Basic validation - check for common ASDL patterns
            const text = editor.document.getText();
            const diagnostics: vscode.Diagnostic[] = [];
            
            // Check for required sections
            if (!text.includes('file_info:')) {
                diagnostics.push(new vscode.Diagnostic(
                    new vscode.Range(0, 0, 0, 0),
                    'Missing required section: file_info',
                    vscode.DiagnosticSeverity.Warning
                ));
            }
            
            if (!text.includes('modules:')) {
                diagnostics.push(new vscode.Diagnostic(
                    new vscode.Range(0, 0, 0, 0),
                    'Missing required section: modules',
                    vscode.DiagnosticSeverity.Warning
                ));
            }
            
            // Create diagnostic collection
            const collection = vscode.languages.createDiagnosticCollection('asdl');
            collection.set(editor.document.uri, diagnostics);
            
            if (diagnostics.length === 0) {
                vscode.window.showInformationMessage('ASDL syntax validation passed!');
            } else {
                vscode.window.showWarningMessage(`ASDL syntax validation found ${diagnostics.length} issue(s)`);
            }
        }
    });

    context.subscriptions.push(validateCommand);
}

export function deactivate() {
    console.log('ASDL Syntax Highlighter is now deactivated!');
}

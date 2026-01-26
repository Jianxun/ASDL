import * as vscode from 'vscode'

export async function getWebviewHtml(
  webview: vscode.Webview,
  extensionUri: vscode.Uri
): Promise<string> {
  const mediaUri = vscode.Uri.joinPath(extensionUri, 'media')
  const indexUri = vscode.Uri.joinPath(mediaUri, 'index.html')
  const webviewBase = webview.asWebviewUri(mediaUri).toString()
  const csp = [
    "default-src 'none'",
    `img-src ${webview.cspSource} data:`,
    `style-src ${webview.cspSource} 'unsafe-inline'`,
    `script-src ${webview.cspSource}`
  ].join('; ')

  try {
    const raw = await vscode.workspace.fs.readFile(indexUri)
    const html = Buffer.from(raw).toString('utf8')
    return html
      .replace('__BASE__', `${webviewBase}/`)
      .replace('__CSP__', csp)
  } catch (error) {
    return fallbackHtml(webviewBase)
  }
}

function fallbackHtml(webviewBase: string) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ASDL Visualizer</title>
    <style>
      body { font-family: Segoe UI, sans-serif; padding: 24px; }
      code { background: #f0f0f0; padding: 2px 4px; }
    </style>
  </head>
  <body>
    <h1>ASDL Visualizer</h1>
    <p>Webview bundle not found at <code>${webviewBase}</code>.</p>
    <p>Run <code>npm run build</code> in <code>extensions/asdl-visualizer</code>.</p>
  </body>
</html>`
}

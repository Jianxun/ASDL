import * as vscode from 'vscode'

import { registerOpenVisualizerCommand } from './extension/commands'

export function activate(context: vscode.ExtensionContext) {
  context.subscriptions.push(registerOpenVisualizerCommand(context))
}

export function deactivate() {
  return undefined
}

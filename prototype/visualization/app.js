// ASDL Circuit Visualization Application
class ASDLVisualizer {
    constructor() {
        this.jsPlumbInstance = null;
        this.currentCircuit = null;
        this.nodes = new Map();
        this.connections = [];
        
        this.init();
    }

    async init() {
        // Set up event listeners first
        this.setupEventListeners();
        
        // Initialize jsPlumb and wait for it to be ready
        this.initJsPlumb();
        
        console.log('ASDL Visualizer initialized');
    }

    initJsPlumb() {
        // Initialize jsPlumb Community Edition
        jsPlumb.ready(() => {
            // Set container for jsPlumb
            jsPlumb.setContainer(document.getElementById('canvas'));
            
            // Set default paint styles for orthogonal-style connectors
            jsPlumb.importDefaults({
                paintStyle: { 
                    stroke: '#757575', 
                    strokeWidth: 2,
                    strokeDasharray: '0'
                },
                hoverPaintStyle: { 
                    stroke: '#667eea', 
                    strokeWidth: 3,
                    strokeDasharray: '0'
                },
                endpointStyle: { 
                    fill: '#333', 
                    outlineStroke: 'white', 
                    outlineWidth: 2,
                    radius: 4
                },
                endpointHoverStyle: { 
                    fill: '#667eea',
                    radius: 5
                },
                connector: ['Flowchart', { stub: 15, gap: 5, cornerRadius: 5, alwaysRespectStubs: true }],
                anchors: ['Top', 'Bottom', 'Left', 'Right'],
                endpoint: ['Dot', { radius: 4 }]
            });
            
            this.jsPlumbInstance = jsPlumb;
            console.log('jsPlumb Community Edition ready with orthogonal-style connectors');
            
            // Load default circuit once jsPlumb is ready
            this.loadCircuit('diff_pair.json');
        });
    }

    setupEventListeners() {
        // Load circuit button
        document.getElementById('loadCircuit').addEventListener('click', () => {
            const selected = document.getElementById('circuitSelect').value;
            this.loadCircuit(selected);
        });

        // Reset view button
        document.getElementById('resetView').addEventListener('click', () => {
            this.resetView();
        });

        // Canvas mouse tracking
        const canvas = document.getElementById('canvas');
        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            const x = Math.round(e.clientX - rect.left);
            const y = Math.round(e.clientY - rect.top);
            document.getElementById('coordinates').textContent = `(${x}, ${y})`;
        });
    }

    async loadCircuit(filename) {
        try {
            document.getElementById('statusText').textContent = `Loading ${filename}...`;
            
            const response = await fetch(filename);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const circuitData = await response.json();
            this.currentCircuit = circuitData;
            
            // Clear existing visualization
            this.clearCanvas();
            
            // Render the circuit
            this.renderCircuit(circuitData);
            
            // Update UI
            this.updateCircuitInfo(circuitData);
            
            document.getElementById('statusText').textContent = `Loaded ${filename}`;
            console.log('Circuit loaded:', circuitData);
            
        } catch (error) {
            console.error('Error loading circuit:', error);
            document.getElementById('statusText').textContent = `Error loading ${filename}`;
        }
    }

    clearCanvas() {
        // Clear jsPlumb connections and endpoints
        if (this.jsPlumbInstance) {
            this.jsPlumbInstance.deleteEveryConnection();
            this.jsPlumbInstance.deleteEveryEndpoint();
        }
        
        // Remove all nodes from DOM
        const canvas = document.getElementById('canvas');
        const nodes = canvas.querySelectorAll('.circuit-node');
        nodes.forEach(node => node.remove());
        
        // Clear internal state
        this.nodes.clear();
        this.connections = [];
    }

    renderCircuit(circuitData) {
        // Calculate layout positions
        const positions = this.calculateLayout(circuitData.nodes);
        
        // Create nodes
        circuitData.nodes.forEach((nodeData, index) => {
            this.createNode(nodeData, positions[index]);
        });

        // Create connections after a short delay to ensure nodes are rendered
        setTimeout(() => {
            this.createConnections(circuitData.connections);
        }, 100);
    }

    calculateLayout(nodes) {
        // Simple grid layout for now
        const cols = Math.ceil(Math.sqrt(nodes.length));
        const rows = Math.ceil(nodes.length / cols);
        
        const canvas = document.getElementById('canvas');
        const canvasRect = canvas.getBoundingClientRect();
        
        const startX = 150;
        const startY = 100;
        const spacingX = 200;
        const spacingY = 150;
        
        const positions = [];
        
        nodes.forEach((node, index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);
            
            positions.push({
                x: startX + col * spacingX,
                y: startY + row * spacingY
            });
        });
        
        return positions;
    }

    createNode(nodeData, position) {
        const nodeElement = document.createElement('div');
        nodeElement.id = nodeData.id;
        nodeElement.className = `circuit-node ${this.getNodeTypeClass(nodeData.model)}`;
        
        // Set position
        nodeElement.style.left = `${position.x}px`;
        nodeElement.style.top = `${position.y}px`;
        
        // Create node content
        const labelDiv = document.createElement('div');
        labelDiv.className = 'node-label';
        labelDiv.textContent = nodeData.label;
        
        const modelDiv = document.createElement('div');
        modelDiv.className = 'node-model';
        modelDiv.textContent = nodeData.model;
        
        nodeElement.appendChild(labelDiv);
        nodeElement.appendChild(modelDiv);
        
        // Add pattern indicator if applicable
        if (nodeData.is_patterned) {
            const patternDiv = document.createElement('div');
            patternDiv.className = 'node-pattern';
            patternDiv.textContent = 'Pattern';
            nodeElement.appendChild(patternDiv);
        }
        
        // Add to canvas
        document.getElementById('canvas').appendChild(nodeElement);
        
        // Make draggable
        this.jsPlumbInstance.draggable(nodeElement, {
            containment: 'parent'
        });
        
        // Add endpoints (connection points)
        this.addNodeEndpoints(nodeElement, nodeData);
        
        // Store node reference
        this.nodes.set(nodeData.id, {
            element: nodeElement,
            data: nodeData
        });
        
        console.log(`Created node: ${nodeData.id} at (${position.x}, ${position.y})`);
    }

    getNodeTypeClass(model) {
        if (model.includes('nmos')) return 'node-nmos';
        if (model.includes('pmos')) return 'node-pmos';
        if (model.includes('res')) return 'node-resistor';
        if (model.includes('cap')) return 'node-capacitor';
        return 'node-nmos'; // default
    }

    addNodeEndpoints(nodeElement, nodeData) {
        // Add standard endpoints for connections
        const endpointConfig = {
            maxConnections: -1,
            isSource: true,
            isTarget: true
        };
        
        // Add endpoints at each anchor point
        this.jsPlumbInstance.addEndpoint(nodeElement, {
            anchor: 'Top',
            uuid: `${nodeData.id}-top`
        }, endpointConfig);
        
        this.jsPlumbInstance.addEndpoint(nodeElement, {
            anchor: 'Bottom',
            uuid: `${nodeData.id}-bottom`
        }, endpointConfig);
        
        this.jsPlumbInstance.addEndpoint(nodeElement, {
            anchor: 'Left',
            uuid: `${nodeData.id}-left`
        }, endpointConfig);
        
        this.jsPlumbInstance.addEndpoint(nodeElement, {
            anchor: 'Right',
            uuid: `${nodeData.id}-right`
        }, endpointConfig);
    }

    createConnections(connectionData) {
        connectionData.forEach((conn, index) => {
            this.createConnection(conn, index);
        });
    }

    createConnection(connData, index) {
        const fromNode = this.nodes.get(connData.from_node);
        const toNode = this.nodes.get(connData.to_node);
        
        if (!fromNode || !toNode) {
            console.warn(`Connection ${index}: Node not found`, connData);
            return;
        }
        
        // Determine connection style based on type
        const connectionStyle = this.getConnectionStyle(connData.type);
        
        // Create the connection with flowchart-builder styling
        const connection = this.jsPlumbInstance.connect({
            source: fromNode.element,
            target: toNode.element,
            paintStyle: connectionStyle.paintStyle,
            hoverPaintStyle: connectionStyle.hoverPaintStyle,
            connector: ['Flowchart', { stub: 15, gap: 5, cornerRadius: 5, alwaysRespectStubs: true }],
            endpoint: ['Dot', { radius: 4 }],
            overlays: [
                ['Arrow', { 
                    location: 1, 
                    width: 10, 
                    length: 10,
                    foldback: 0.8
                }],
                ['Label', {
                    label: connData.net,
                    location: 0.5,
                    cssClass: 'connection-label',
                    labelStyle: {
                        color: '#333',
                        backgroundColor: 'white',
                        padding: '2px 4px',
                        borderRadius: '3px',
                        border: '1px solid #ddd',
                        fontSize: '11px'
                    }
                }]
            ]
        });
        
        if (connection) {
            // Add connection class for styling
            connection.addClass(connData.type);
            this.connections.push({
                jsplumb: connection,
                data: connData
            });
            
            console.log(`Created connection: ${connData.from_node} -> ${connData.to_node} (${connData.net})`);
        }
    }

    getConnectionStyle(connectionType) {
        switch (connectionType) {
            case 'differential':
                return {
                    paintStyle: { 
                        stroke: '#4caf50', 
                        strokeWidth: 3,
                        strokeDasharray: '0',
                        strokeLinecap: 'round'
                    },
                    hoverPaintStyle: { 
                        stroke: '#2e7d32', 
                        strokeWidth: 4,
                        strokeDasharray: '0'
                    }
                };
            case 'single':
            default:
                return {
                    paintStyle: { 
                        stroke: '#757575', 
                        strokeWidth: 2,
                        strokeDasharray: '0',
                        strokeLinecap: 'round'
                    },
                    hoverPaintStyle: { 
                        stroke: '#424242', 
                        strokeWidth: 3,
                        strokeDasharray: '0'
                    }
                };
        }
    }

    updateCircuitInfo(circuitData) {
        // Update circuit name
        document.getElementById('circuitName').textContent = circuitData.module_name;
        
        // Update stats
        document.getElementById('nodeCount').textContent = `Nodes: ${circuitData.nodes.length}`;
        document.getElementById('connectionCount').textContent = `Connections: ${circuitData.connections.length}`;
        
        // Update nets list
        this.updateNetsList(circuitData.nets);
    }

    updateNetsList(nets) {
        const netsList = document.getElementById('netsList');
        netsList.innerHTML = '';
        
        Object.entries(nets).forEach(([netName, netInfo]) => {
            const netItem = document.createElement('div');
            netItem.className = 'net-item';
            
            const nameSpan = document.createElement('span');
            nameSpan.className = 'net-name';
            nameSpan.textContent = netName;
            
            const typeSpan = document.createElement('span');
            typeSpan.className = `net-type ${netInfo.type}`;
            if (netInfo.is_internal) {
                typeSpan.className += ' internal';
            }
            typeSpan.textContent = netInfo.type;
            
            netItem.appendChild(nameSpan);
            netItem.appendChild(typeSpan);
            netsList.appendChild(netItem);
        });
    }

    resetView() {
        // Reset zoom and pan if implemented
        // For now, just reload the current circuit
        if (this.currentCircuit) {
            this.renderCircuit(this.currentCircuit);
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.asdlVisualizer = new ASDLVisualizer();
}); 
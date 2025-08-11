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
                    outlineWidth: 1,
                    radius: 1  // Reduced to 20% of original size (was 4)
                },
                endpointHoverStyle: { 
                    fill: '#667eea',
                    radius: 1.5  // Slightly larger on hover
                },
                connector: ['Flowchart', { stub: 15, gap: 5, cornerRadius: 5, alwaysRespectStubs: true }],
                anchors: ['Top', 'Bottom', 'Left', 'Right'],
                endpoint: ['Dot', { radius: 1 }]  // Reduced to 20% of original size
            });
            
            this.jsPlumbInstance = jsPlumb;
            console.log('jsPlumb Community Edition ready with smaller endpoints');
            
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

        // Canvas mouse tracking and zoom prevention
        const canvas = document.getElementById('canvas');
        
        // Prevent browser zoom on canvas
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault(); // Prevent default browser zoom
        }, { passive: false });
        
        // Mouse coordinate tracking
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
        // Calculate layout positions for component nodes
        const componentPositions = this.calculateComponentLayout(circuitData.nodes);
        
        // Calculate positions for port nodes (external pins)
        const portPositions = this.calculatePortLayout(circuitData.nets);
        
        // Create component nodes
        circuitData.nodes.forEach((nodeData, index) => {
            this.createNode(nodeData, componentPositions[index]);
        });

        // Create port nodes (external interface pins)
        this.createPortNodes(circuitData.nets, portPositions);

        // Create connections after a short delay to ensure nodes are rendered
        setTimeout(() => {
            this.createConnections(circuitData.connections);
        }, 100);
    }

    calculateComponentLayout(nodes) {
        // Simple grid layout for component nodes in center area
        const cols = Math.ceil(Math.sqrt(nodes.length));
        const rows = Math.ceil(nodes.length / cols);
        
        const startX = 300; // Leave space for port nodes on left
        const startY = 200; // Leave space for port nodes on top
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

    calculatePortLayout(nets) {
        // Position port nodes around the canvas edges based on type and direction
        const positions = {};
        const portNames = Object.keys(nets).filter(netName => !nets[netName].is_internal);
        
        // Categorize ports for positioning
        const powerPorts = portNames.filter(name => name.includes('vdd') || name.includes('vss'));
        const signalPorts = portNames.filter(name => !powerPorts.includes(name));
        
        let topY = 50;
        let bottomY = 600;
        let leftX = 50;
        let rightX = 800;
        
        // Position power ports on top and bottom
        powerPorts.forEach((portName, index) => {
            if (portName.includes('vdd')) {
                positions[portName] = { x: 150 + index * 150, y: topY };
            } else if (portName.includes('vss')) {
                positions[portName] = { x: 150 + index * 150, y: bottomY };
            }
        });
        
        // Position signal ports on left and right
        signalPorts.forEach((portName, index) => {
            if (portName.includes('in')) {
                positions[portName] = { x: leftX, y: 200 + index * 100 };
            } else if (portName.includes('out')) {
                positions[portName] = { x: rightX, y: 200 + index * 100 };
            } else {
                // Default positioning for other signals
                positions[portName] = { x: leftX, y: 300 + index * 50 };
            }
        });
        
        return positions;
    }

    createPortNodes(nets, positions) {
        Object.entries(nets).forEach(([netName, netInfo]) => {
            // Skip internal nets - they don't need port nodes
            if (netInfo.is_internal) return;
            
            const position = positions[netName];
            if (!position) return;
            
            // Create port node data structure
            const portNodeData = {
                id: `PORT_${netName}`,
                label: netName,
                model: 'port',
                net_type: netInfo.type,
                is_port: true
            };
            
            this.createPortNode(portNodeData, position);
        });
    }

    createPortNode(portNodeData, position) {
        const nodeElement = document.createElement('div');
        nodeElement.id = portNodeData.id;
        nodeElement.className = `circuit-node node-port ${portNodeData.net_type}`;
        
        // Set position
        nodeElement.style.left = `${position.x}px`;
        nodeElement.style.top = `${position.y}px`;
        
        // Create port node content
        const labelDiv = document.createElement('div');
        labelDiv.className = 'node-label';
        labelDiv.textContent = portNodeData.label;
        
        const typeDiv = document.createElement('div');
        typeDiv.className = 'node-type';
        typeDiv.textContent = 'PORT';
        
        nodeElement.appendChild(labelDiv);
        nodeElement.appendChild(typeDiv);
        
        // Add to canvas
        document.getElementById('canvas').appendChild(nodeElement);
        
        // Make draggable
        this.jsPlumbInstance.draggable(nodeElement, {
            containment: 'parent'
        });
        
        // Add single endpoint for port connection
        this.jsPlumbInstance.addEndpoint(nodeElement, {
            anchor: 'Center',
            uuid: `${portNodeData.id}-center`
        }, {
            maxConnections: -1,
            isSource: true,
            isTarget: true
        });
        
        // Store port node reference
        this.nodes.set(portNodeData.id, {
            element: nodeElement,
            data: portNodeData
        });
        
        console.log(`Created port node: ${portNodeData.id} at (${position.x}, ${position.y})`);
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
        // Check if this is an NMOS transistor
        if (this.isNMOSTransistor(nodeData.model)) {
            // Add NMOS-specific port anchors
            const endpointConfig = {
                maxConnections: -1,
                isSource: true,
                isTarget: true
            };
            
            // NMOS port mapping: G=left, S=bottom, D=top, B=right
            this.jsPlumbInstance.addEndpoint(nodeElement, {
                anchor: 'Left',
                uuid: `${nodeData.id}-G`
            }, endpointConfig);
            
            this.jsPlumbInstance.addEndpoint(nodeElement, {
                anchor: 'Bottom', 
                uuid: `${nodeData.id}-S`
            }, endpointConfig);
            
            this.jsPlumbInstance.addEndpoint(nodeElement, {
                anchor: 'Top',
                uuid: `${nodeData.id}-D`
            }, endpointConfig);
            
            this.jsPlumbInstance.addEndpoint(nodeElement, {
                anchor: 'Right',
                uuid: `${nodeData.id}-B`
            }, endpointConfig);
            
            console.log(`Added NMOS port anchors for ${nodeData.id}: G(left), S(bottom), D(top), B(right)`);
        } else {
            // Generic endpoints for other components
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
    }

    isNMOSTransistor(model) {
        return model.includes('nmos');
    }

    createConnections(connectionData) {
        // Create the component-to-component connections
        connectionData.forEach((conn, index) => {
            this.createConnection(conn, index);
        });
        
        // Create implied connections from port nodes to components
        this.createPortConnections(connectionData);
    }

    createConnection(connData, index) {
        const fromNode = this.nodes.get(connData.from_node);
        const toNode = this.nodes.get(connData.to_node);
        
        if (!fromNode || !toNode) {
            console.warn(`Connection ${index}: Node not found`, connData);
            return;
        }
        
        // Determine specific endpoint UUIDs based on port information
        const fromEndpoint = this.getEndpointUUID(connData.from_node, connData.from_port, fromNode.data.model);
        const toEndpoint = this.getEndpointUUID(connData.to_node, connData.to_port, toNode.data.model);
        
        // Determine connection style based on type
        const connectionStyle = this.getConnectionStyle(connData.type);
        
        // Create the connection using specific endpoints
        const connection = this.jsPlumbInstance.connect({
            uuids: [fromEndpoint, toEndpoint],
            paintStyle: connectionStyle.paintStyle,
            hoverPaintStyle: connectionStyle.hoverPaintStyle,
            connector: ['Flowchart', { stub: 15, gap: 5, cornerRadius: 5, alwaysRespectStubs: true }],
            endpoint: ['Dot', { radius: 1 }],  // Reduced to match smaller size
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
            
            console.log(`Created connection: ${connData.from_node}[${connData.from_port}] -> ${connData.to_node}[${connData.to_port}] (${connData.net})`);
        } else {
            console.warn(`Failed to create connection: ${connData.from_node}[${connData.from_port}] -> ${connData.to_node}[${connData.to_port}]`);
        }
    }

    getEndpointUUID(nodeId, portName, nodeModel) {
        // Check if this is a port node
        if (nodeId.startsWith('PORT_')) {
            return `${nodeId}-center`;
        }
        
        // For NMOS transistors, use semantic port mapping
        if (this.isNMOSTransistor(nodeModel)) {
            return `${nodeId}-${portName}`; // Direct mapping: D, S, G, B
        }
        
        // For other components, map common port names to generic positions
        // or use port name directly if it matches our generic naming
        const portMapping = {
            'plus': 'top',
            'minus': 'bottom',
            'in': 'left', 
            'out': 'right',
            'top': 'top',
            'bottom': 'bottom', 
            'left': 'left',
            'right': 'right'
        };
        
        const mappedPort = portMapping[portName] || 'top'; // fallback to top
        return `${nodeId}-${mappedPort}`;
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
        
        // Count port nodes (external interfaces)
        const portCount = Object.keys(circuitData.nets).filter(netName => !circuitData.nets[netName].is_internal).length;
        
        // Update stats
        document.getElementById('nodeCount').textContent = `Components: ${circuitData.nodes.length}, Ports: ${portCount}`;
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

    createPortConnections(connectionData) {
        // Create a map of nets to the components/ports that use them
        const netToConnections = new Map();
        
        connectionData.forEach(conn => {
            if (!netToConnections.has(conn.net)) {
                netToConnections.set(conn.net, []);
            }
            netToConnections.get(conn.net).push(conn);
        });
        
        // For each net that has a corresponding port node, create connections
        netToConnections.forEach((connections, netName) => {
            const portNodeId = `PORT_${netName}`;
            const portNode = this.nodes.get(portNodeId);
            
            if (portNode) {
                // Create connections from port node to each component terminal using this net
                const uniqueConnections = new Set();
                
                connections.forEach(conn => {
                    // Connection from port to "from" component
                    const fromConnection = `${portNodeId}-${conn.from_node}-${conn.from_port}`;
                    if (!uniqueConnections.has(fromConnection)) {
                        this.createPortToComponentConnection(portNodeId, conn.from_node, conn.from_port, netName);
                        uniqueConnections.add(fromConnection);
                    }
                    
                    // Connection from port to "to" component
                    const toConnection = `${portNodeId}-${conn.to_node}-${conn.to_port}`;
                    if (!uniqueConnections.has(toConnection)) {
                        this.createPortToComponentConnection(portNodeId, conn.to_node, conn.to_port, netName);
                        uniqueConnections.add(toConnection);
                    }
                });
            }
        });
    }

    createPortToComponentConnection(portNodeId, componentId, componentPort, netName) {
        const portNode = this.nodes.get(portNodeId);
        const componentNode = this.nodes.get(componentId);
        
        if (!portNode || !componentNode) {
            return;
        }
        
        const portEndpoint = `${portNodeId}-center`;
        const componentEndpoint = this.getEndpointUUID(componentId, componentPort, componentNode.data.model);
        
        // Create the connection with a subtle style for port connections
        const connection = this.jsPlumbInstance.connect({
            uuids: [portEndpoint, componentEndpoint],
            paintStyle: { 
                stroke: '#999', 
                strokeWidth: 1,
                strokeDasharray: '3,3' // Dashed line for port connections
            },
            hoverPaintStyle: { 
                stroke: '#666', 
                strokeWidth: 2,
                strokeDasharray: '3,3'
            },
            connector: ['Flowchart', { stub: 10, gap: 3, cornerRadius: 3 }],
            endpoint: ['Dot', { radius: 1 }],  // Reduced to match smaller size
            overlays: [
                ['Label', {
                    label: netName,
                    location: 0.2,
                    cssClass: 'port-connection-label',
                    labelStyle: {
                        color: '#666',
                        backgroundColor: 'rgba(255,255,255,0.8)',
                        padding: '1px 3px',
                        borderRadius: '2px',
                        fontSize: '9px'
                    }
                }]
            ]
        });
        
        if (connection) {
            connection.addClass('port-connection');
            this.connections.push({
                jsplumb: connection,
                data: {
                    type: 'port',
                    net: netName,
                    from_node: portNodeId,
                    to_node: componentId,
                    to_port: componentPort
                }
            });
            
            console.log(`Created port connection: ${portNodeId} -> ${componentId}[${componentPort}] (${netName})`);
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.asdlVisualizer = new ASDLVisualizer();
}); 
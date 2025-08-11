// Minimal Circuit Visualizer with jsPlumb
class CircuitVisualizer {
    constructor() {
        this.canvas = document.getElementById('circuit-canvas');
        this.content = document.getElementById('circuit-content');
        this.jsPlumbInstance = null;
        this.zoomLevel = 1.0;
        this.panOffset = { x: 0, y: 0 };
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.circuitData = null;
        this.currentFilename = null;  // Track loaded filename
        
        // Port layout definitions (relative coordinates 0.0-1.0)
        this.NODE_PORTS = {
            'nmos_unit': {
                'G': { x: 0.0, y: 0.5 },   // Gate - left center
                'D': { x: 0.5, y: 0.0 },   // Drain - top center  
                'S': { x: 0.5, y: 1.0 }    // Source - bottom center
            },
            'res': {
                'plus': { x: 0.5, y: 0.0 },   // Top center
                'minus': { x: 0.5, y: 1.0 }   // Bottom center
            },
            'port': {
                // Dynamic anchors: left and right edges
                'terminal': [
                    [0, 0.5, -1, 0],  // Left center
                    [1, 0.5, 1, 0]    // Right center
                ]
            },
            'power_supply': {
                // Anchors at top and bottom edges for cleaner power rails
                'terminal': [
                    [0.5, 0, 0, -1],  // Top center (pointing up)
                    [0.5, 1, 0, 1]    // Bottom center (pointing down)
                ]
            }
        };
        
        this.init();
    }
    
    init() {
        // Initialize jsPlumb on the content container
        this.jsPlumbInstance = jsPlumb.getInstance({
            Container: this.content,
            PaintStyle: { stroke: "#333", strokeWidth: 2 },
            EndpointStyle: { fill: "#333", radius: 4 },
            Connector: ["Flowchart", { stub: [20, 20], gap: 5, cornerRadius: 5 }],
            ConnectionOverlays: [["Arrow", { location: 1, width: 10, length: 10 }]],
            // Use jsPlumb's built-in grid system (snap only, no visual)
            dragOptions: { 
                cursor: 'pointer', 
                zIndex: 2000, 
                grid: [20, 20]  // 20px grid snap for dragging (invisible)
            }
        });
        
        this.setupZoomPan();
        this.loadCircuit('diff_pair_enhanced.json');

        // Bind save layout button
        const saveBtn = document.getElementById('save-layout-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.exportLayout());
        }
    }
    
    createNode(nodeData) {
        const element = document.createElement('div');
        element.id = nodeData.id;
        element.textContent = nodeData.label;
        
        // Base classes
        element.className = `circuit-node node-${nodeData.node_type} model-${nodeData.model}`;
        
        // Position using JSON coordinates
        element.style.left = `${nodeData.x}px`;
        element.style.top = `${nodeData.y}px`;
        element.style.width = `${nodeData.width}px`;
        element.style.height = `${nodeData.height}px`;
        
        // Add to content container
        this.content.appendChild(element);
        
        // Make draggable with grid snap
        this.jsPlumbInstance.draggable(element, {
            grid: [20, 20],
            cursor: 'pointer'
        });
        
        // Add named endpoints for this node
        this.addEndpoints(element, nodeData);
        
        return element;
    }
    
    addEndpoints(element, nodeData) {
        // Determine key for NODE_PORTS lookup (prefer model, fallback to node_type)
        const key = this.NODE_PORTS[nodeData.model] ? nodeData.model : nodeData.node_type;
        const portLayout = this.NODE_PORTS[key];
        if (!portLayout) return;  // No port layout defined

        Object.entries(portLayout).forEach(([portName, pos]) => {
            const uuid = `${nodeData.id}-${portName}`;
            let anchorConfig;
            if (Array.isArray(pos[0])) {
                // pos is array of anchor arrays for dynamic anchors
                anchorConfig = pos;  // dynamic anchor list
            } else if (Array.isArray(pos)) {
                anchorConfig = pos;  // Treat as provided list (already anchors)
            } else {
                anchorConfig = [pos.x, pos.y, 0, 0];  // single anchor definition
            }

            this.jsPlumbInstance.addEndpoint(element, {
                uuid,
                anchor: anchorConfig,
                isSource: true,
                isTarget: true,
                maxConnections: -1
            });
        });
    }
    
    async loadCircuit(filename) {
        try {
            // Clear existing nodes and jsPlumb elements
            this.jsPlumbInstance.deleteEveryConnection();
            this.jsPlumbInstance.deleteEveryEndpoint();
            const existingNodes = this.content.querySelectorAll('.circuit-node');
            existingNodes.forEach(node => node.remove());
            
            // Fetch and parse JSON
            const response = await fetch(filename);
            if (!response.ok) {
                throw new Error(`Failed to load ${filename}: ${response.status}`);
            }
            
            this.circuitData = await response.json();
            
            // Remember current filename for save suggestion
            this.currentFilename = filename;
            
            // Batch node creation for performance
            this.jsPlumbInstance.batch(() => {
                // Create nodes from JSON data
                this.circuitData.nodes.forEach(nodeData => {
                    this.createNode(nodeData);
                });

                // Create connections between ports
                this.circuitData.connections.forEach(conn => {
                    const sourceUUID = `${conn.from_node}-${conn.from_port}`;
                    const targetUUID = `${conn.to_node}-${conn.to_port}`;
                    try {
                        this.jsPlumbInstance.connect({ uuids: [sourceUUID, targetUUID] });
                    } catch (e) {
                        console.warn('Connection failed:', conn, e);
                    }
                });
            });
            
            console.log(`Loaded circuit: ${this.circuitData.module_name}`);
            console.log(`Nodes created: ${this.circuitData.nodes.length}`);
            console.log(`Connections created: ${this.circuitData.connections.length}`);
            
        } catch (error) {
            console.error('Error loading circuit:', error);
        }
    }
    
    setupZoomPan() {
        // Mouse wheel zoom (cursor-centered, manual implementation for Community Edition)
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const zoomFactor = e.deltaY > 0 ? 0.95 : 1.05;
            const newZoom = Math.max(0.1, Math.min(3.0, this.zoomLevel * zoomFactor));

            // Get cursor position relative to canvas
            const rect = this.canvas.getBoundingClientRect();
            const cursorX = e.clientX - rect.left;
            const cursorY = e.clientY - rect.top;

            // Calculate world point under cursor before zoom
            const worldX = (cursorX - this.panOffset.x) / this.zoomLevel;
            const worldY = (cursorY - this.panOffset.y) / this.zoomLevel;

            // Update zoom level
            this.zoomLevel = newZoom;

            // Adjust pan to keep world point under cursor
            this.panOffset.x = cursorX - worldX * this.zoomLevel;
            this.panOffset.y = cursorY - worldY * this.zoomLevel;

            this.updateTransform();
        });
        
        // Mouse drag pan
        this.canvas.addEventListener('mousedown', (e) => {
            // Allow panning if clicking on canvas or content background, but not on nodes
            const isBackgroundClick = (e.target === this.canvas || e.target === this.content) && 
                                     !e.target.classList.contains('circuit-node');
            if (isBackgroundClick) {
                this.isDragging = true;
                this.dragStart = { x: e.clientX, y: e.clientY };
                this.canvas.style.cursor = 'grabbing';
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                const deltaX = e.clientX - this.dragStart.x;
                const deltaY = e.clientY - this.dragStart.y;
                this.panOffset.x += deltaX;
                this.panOffset.y += deltaY;
                this.dragStart = { x: e.clientX, y: e.clientY };
                this.updateTransform();
            }
        });
        
        document.addEventListener('mouseup', () => {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
        });
    }
    
    updateTransform() {
        // Apply both pan and zoom transform to content
        this.content.style.transform = `translate(${this.panOffset.x}px, ${this.panOffset.y}px) scale(${this.zoomLevel})`;
        
        // Apply zoom to jsPlumb for connections
        this.jsPlumbInstance.setZoom(this.zoomLevel);
    }
    
    reset() {
        this.zoomLevel = 1.0;
        this.panOffset = { x: 0, y: 0 };
        this.updateTransform();
    }

    // Export current node coordinates back into JSON and trigger download
    exportLayout() {
        if (!this.circuitData) {
            console.warn('No circuit loaded to export');
            return;
        }

        // Deep copy circuitData to avoid mutating original reference
        const updated = JSON.parse(JSON.stringify(this.circuitData));

        updated.nodes.forEach(node => {
            const el = document.getElementById(node.id);
            if (el) {
                const left = parseFloat(el.style.left) || 0;
                const top = parseFloat(el.style.top) || 0;
                node.x = left;
                node.y = top;
            }
        });

        const blob = new Blob([JSON.stringify(updated, null, 2)], {
            type: 'application/json'
        });

        // Attempt to use File System Access API if available
        if (window.showSaveFilePicker) {
            (async () => {
                try {
                    const suggestedName = this.currentFilename || 'circuit_layout.json';
                    const handle = await window.showSaveFilePicker({
                        suggestedName,
                        types: [{
                            description: 'JSON Files',
                            accept: { 'application/json': ['.json'] }
                        }]
                    });
                    const writable = await handle.createWritable();
                    await writable.write(blob);
                    await writable.close();
                    console.log('Layout saved to file via File System Access API');
                } catch (err) {
                    console.warn('File save cancelled or failed, falling back to download.', err);
                    this._downloadBlob(blob, updated.module_name);
                }
            })();
        } else {
            this._downloadBlob(blob, updated.module_name);
        }
    }

    // Helper to trigger traditional download fallback
    _downloadBlob(blob, moduleName = 'circuit') {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const fileNameBase = (moduleName || 'circuit').replace(/\s+/g, '_').toLowerCase();
        a.download = `${fileNameBase}_layout.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        console.log('Layout downloaded (fallback)');
    }
}

// Initialize visualizer when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.circuitVisualizer = new CircuitVisualizer();
    
    console.log('Circuit Visualizer initialized with zoom/pan functionality');
    console.log('Mouse wheel to zoom (0.1x - 3.0x), drag background to pan');
    console.log('Drag circuit nodes to see 20px grid snap');
    console.log('Loading diff_pair_enhanced.json...');
}); 
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
        this.createTestNode();
    }
    
    createTestNode() {
        // Add two test nodes to see zoom/pan and grid snap in action
        const testNode1 = document.createElement('div');
        testNode1.className = 'circuit-node';
        testNode1.textContent = 'TEST1';
        testNode1.id = 'test-node-1';
        testNode1.style.left = '200px';
        testNode1.style.top = '150px';
        testNode1.style.backgroundColor = '#e3f2fd';  // Light blue
        this.content.appendChild(testNode1);
        
        const testNode2 = document.createElement('div');
        testNode2.className = 'circuit-node';
        testNode2.textContent = 'TEST2';
        testNode2.id = 'test-node-2';
        testNode2.style.left = '350px';
        testNode2.style.top = '250px';
        testNode2.style.backgroundColor = '#f3e5f5';  // Light purple
        this.content.appendChild(testNode2);
        
        // Make both test nodes draggable with grid snap
        this.jsPlumbInstance.draggable(testNode1, {
            grid: [20, 20],
            cursor: 'pointer'
        });
        this.jsPlumbInstance.draggable(testNode2, {
            grid: [20, 20], 
            cursor: 'pointer'
        });
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
}

// Initialize visualizer when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.circuitVisualizer = new CircuitVisualizer();
    
    console.log('Circuit Visualizer initialized with zoom/pan functionality');
    console.log('Mouse wheel to zoom (0.1x - 3.0x), drag background to pan');
    console.log('Drag TEST1/TEST2 nodes to see 20px grid snap');
}); 
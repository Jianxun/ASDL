# jsPlumb Development Guide

## Overview

This guide documents key patterns, gotchas, and best practices for jsPlumb development based on real implementation experience. It covers both Community Edition and Toolkit differences, helping avoid common pitfalls.

## Table of Contents

1. [Community vs Toolkit Editions](#community-vs-toolkit-editions)
2. [Container Architecture](#container-architecture) 
3. [Zoom & Pan Implementation](#zoom--pan-implementation)
4. [Grid Systems](#grid-systems)
5. [Drag Handling](#drag-handling)
6. [Configuration Patterns](#configuration-patterns)
7. [Common Pitfalls](#common-pitfalls)
8. [Best Practices](#best-practices)

---

## Community vs Toolkit Editions

### Key Differences

| Feature | Community Edition | Toolkit Edition |
|---------|------------------|-----------------|
| **Zoom with Origin** | ❌ `setZoom(scale, x, y)` NOT available | ✅ Built-in origin-aware zoom |
| **Visual Grids** | ❌ Grid snap only (`grid: [20,20]`) | ✅ Visual background grids |
| **Background Images** | ❌ No built-in support | ✅ Single/tiled backgrounds |
| **Surface Widget** | ❌ Manual container management | ✅ Automatic surface management |
| **Licensing** | MIT/GPL2 | Commercial |

### Critical API Differences

```javascript
// ❌ DOES NOT WORK in Community Edition
jsPlumbInstance.setZoom(1.5, 100, 100);  // Origin-aware zoom

// ✅ WORKS in Community Edition  
jsPlumbInstance.setZoom(1.5);  // Scale only
```

**Lesson**: Always check API compatibility between editions. Many examples online are for Toolkit edition.

---

## Container Architecture

### Required DOM Structure

```html
<!-- ✅ CORRECT: Two-layer architecture -->
<div id="viewport" class="viewport">          <!-- Fixed viewport -->
    <div id="content" class="content">        <!-- Transformable content -->
        <!-- Nodes go here -->
    </div>
</div>
```

```css
.viewport {
    width: 100vw;
    height: 100vh;
    overflow: hidden;        /* Critical: prevents scrollbars */
    position: relative;
}

.content {
    width: 5000px;          /* Large enough for zoom/pan */
    height: 5000px;
    position: relative;
    transform-origin: 0 0;  /* Critical: zoom from top-left */
}
```

### jsPlumb Container Targeting

```javascript
// ✅ CORRECT: Target the content layer
jsPlumbInstance = jsPlumb.getInstance({
    Container: document.getElementById('content'),  // Inner container
    // ... other options
});
```

**Lesson**: jsPlumb should target the transformable content layer, not the fixed viewport.

---

## Zoom & Pan Implementation

### Community Edition Pattern

Since Community Edition doesn't support origin-aware zoom, implement manually:

```javascript
// Mouse wheel zoom with cursor center
canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY > 0 ? 0.95 : 1.05;
    const newZoom = Math.max(0.1, Math.min(3.0, currentZoom * zoomFactor));

    // Get cursor position
    const rect = canvas.getBoundingClientRect();
    const cursorX = e.clientX - rect.left;
    const cursorY = e.clientY - rect.top;

    // Calculate world point under cursor
    const worldX = (cursorX - panOffset.x) / currentZoom;
    const worldY = (cursorY - panOffset.y) / currentZoom;

    // Update zoom
    currentZoom = newZoom;

    // Adjust pan to keep world point under cursor
    panOffset.x = cursorX - worldX * currentZoom;
    panOffset.y = cursorY - worldY * currentZoom;

    // Apply transforms
    content.style.transform = `translate(${panOffset.x}px, ${panOffset.y}px) scale(${currentZoom})`;
    jsPlumbInstance.setZoom(currentZoom);
});
```

### Pan Detection with jsPlumb

```javascript
// ✅ CORRECT: Account for jsPlumb draggable elements
canvas.addEventListener('mousedown', (e) => {
    const isBackgroundClick = (e.target === canvas || e.target === content) && 
                             !e.target.classList.contains('circuit-node');
    if (isBackgroundClick) {
        // Start panning
    }
});
```

**Lesson**: Pan detection must exclude draggable elements to avoid conflicts.

---

## Grid Systems

### Community Edition: Snap-Only Grids

```javascript
// ❌ WRONG: dragOptions in instance don't apply to later elements
jsPlumb.getInstance({
    dragOptions: { grid: [20, 20] }  // Doesn't affect future draggable() calls
});

// ✅ CORRECT: Pass grid to each draggable() call
jsPlumbInstance.draggable(element, {
    grid: [20, 20],
    cursor: 'pointer'
});
```

### Visual Grid Alternative

```css
/* Manual CSS grid (if visual feedback needed) */
.content {
    background-image: radial-gradient(circle, #ccc 1px, transparent 1px);
    background-size: 20px 20px;
    /* This transforms with zoom/pan */
}
```

**Lesson**: Community Edition grids are snap-only. Visual grids require manual CSS or Toolkit.

---

## Drag Handling

### Draggable Configuration

```javascript
// ✅ CORRECT: Individual element configuration
jsPlumbInstance.draggable(element, {
    grid: [20, 20],           // Snap to grid
    cursor: 'pointer',        // Cursor during drag
    zIndex: 2000             // Above other elements
});
```

### Event Conflicts

```javascript
// ❌ PROBLEM: Pan and drag events conflict
element.addEventListener('mousedown', ...);  // Custom handler
jsPlumbInstance.draggable(element);          // jsPlumb handler
// Results in: Both fire, unpredictable behavior

// ✅ SOLUTION: Use jsPlumb's event system
jsPlumbInstance.bind('drag', function(info) {
    // Handle drag events through jsPlumb
});
```

**Lesson**: Let jsPlumb handle drag events. Use its event system rather than DOM events.

---

## Configuration Patterns

### Instance Configuration

```javascript
// ✅ RECOMMENDED: Complete configuration
const jsPlumbInstance = jsPlumb.getInstance({
    Container: contentElement,
    
    // Connection appearance
    PaintStyle: { stroke: "#333", strokeWidth: 2 },
    EndpointStyle: { fill: "#333", radius: 4 },
    Connector: ["Flowchart", { 
        stub: [20, 20], 
        gap: 5, 
        cornerRadius: 5 
    }],
    ConnectionOverlays: [
        ["Arrow", { location: 1, width: 10, length: 10 }]
    ],
    
    // Performance
    DoNotThrowIfNotConnected: true
});
```

### Professional Connection Styling

```javascript
// From official jsPlumb demos
const connectorPaintStyle = {
    strokeWidth: 2,
    stroke: "#61B7CF",
    joinstyle: "round",
    outlineStroke: "white",
    outlineWidth: 2
};

const connectorHoverStyle = {
    strokeWidth: 3,
    stroke: "#216477",
    outlineWidth: 5,
    outlineStroke: "white"
};
```

---

## Common Pitfalls

### 1. Transform Origin Issues

```css
/* ❌ WRONG: Default transform-origin is center */
.content {
    transform-origin: center center;  /* Zoom from center */
}

/* ✅ CORRECT: Top-left origin for predictable zoom */
.content {
    transform-origin: 0 0;  /* Zoom from top-left */
}
```

### 2. Container Size Issues

```css
/* ❌ WRONG: Content same size as viewport */
.content {
    width: 100%;   /* Limited zoom/pan area */
    height: 100%;
}

/* ✅ CORRECT: Large content area */
.content {
    width: 5000px;   /* Room for zoom/pan */
    height: 5000px;
}
```

### 3. Z-Index Conflicts

```css
/* ❌ PROBLEM: Connections behind nodes */
.circuit-node {
    z-index: auto;  /* Default stacking */
}

/* ✅ SOLUTION: Explicit z-index management */
.circuit-node {
    z-index: 10;    /* Above connections */
}
```

### 4. Event Bubbling Issues

```javascript
// ❌ WRONG: Events bubble unpredictably
element.addEventListener('click', handler);

// ✅ CORRECT: Control event propagation
element.addEventListener('click', (e) => {
    e.stopPropagation();  // Prevent conflicts
    handler(e);
});
```

---

## Best Practices

### 1. Development Workflow

1. **Start with official demos**: Copy working patterns
2. **Test incrementally**: Add one feature at a time
3. **Check edition compatibility**: Verify API availability
4. **Use batch operations**: For performance with many elements

```javascript
jsPlumbInstance.batch(() => {
    // Multiple operations
    // Single repaint at end
});
```

### 2. Performance Optimization

```javascript
// ✅ Suspend events during bulk operations
jsPlumbInstance.setSuspendDrawing(true);
// ... bulk operations ...
jsPlumbInstance.setSuspendDrawing(false, true);  // true = repaint
```

### 3. Debugging

```javascript
// ✅ Useful debugging
console.log('Zoom level:', jsPlumbInstance.getZoom());
console.log('Container:', jsPlumbInstance.getContainer());
console.log('All connections:', jsPlumbInstance.getAllConnections());
```

### 4. Clean Architecture

```javascript
// ✅ Encapsulated visualizer class
class CircuitVisualizer {
    constructor(containerSelector) {
        this.container = document.querySelector(containerSelector);
        this.jsPlumbInstance = this.initJsPlumb();
        this.setupEventHandlers();
    }
    
    initJsPlumb() {
        return jsPlumb.getInstance({
            Container: this.container,
            // ... configuration
        });
    }
    
    createNode(nodeData) {
        const element = this.createElement(nodeData);
        this.jsPlumbInstance.draggable(element, this.getDragOptions());
        return element;
    }
    
    // Clear separation of concerns
}
```

---

## Quick Reference

### Community Edition Checklist

- [ ] Manual zoom/pan implementation
- [ ] Two-layer container architecture  
- [ ] Individual draggable configuration
- [ ] CSS-based visual grids (if needed)
- [ ] Proper event conflict resolution

### Essential CSS Properties

```css
.viewport { overflow: hidden; position: relative; }
.content { transform-origin: 0 0; position: relative; }
.node { z-index: 10; position: absolute; }
```

### Critical JavaScript Patterns

```javascript
// Zoom: Manual cursor-centered implementation
// Pan: Detect background clicks, exclude nodes
// Drag: Individual element configuration
// Events: Use jsPlumb's event system
```

---

*This guide is based on real implementation experience building a minimal circuit visualizer with jsPlumb Community Edition 2.15.6.* 
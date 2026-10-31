# Standalone Sandboxed Editors & Execution Runtimes

*Architectural evaluation and recommendations for Codingal Code Studio.*

When designing an educational coding platform for learners (K-12 students through adults) and teachers, the editor and runner architecture must balance:
1. **Security & Sandboxing:** Student code must be untrusted and isolated.
2. **Low Latency & High Frame-Rates:** Turtle graphics, Tkinter UI, and Pygame animations need instant feedback without server latency lag.
3. **Cross-Device Performance:** Must run seamlessly on low-cost school Chromebooks, iPads/tablets, and low-bandwidth connections.
4. **Zero-Maintenance Footprint:** Capable of running standalone without requiring students or teachers to install Docker or manage local dependencies.

---

## 1. Top Standalone Web Code Editors (Comparison)

| Editor | Bundle Size | Mobile/Tablet Support | Language Server (LSP) | Sandboxed Worker | Best Fit for Codingal |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Monaco Editor** | Large (~2–4 MB) | Fair (Desktop-first) | Built-in (VS Code engine) | Yes (Web Worker) | High school / advanced learners, teacher workspace, desktop browser |
| **CodeMirror 6** | Minimal (<120 KB) | Outstanding (Touch/iOS) | Available via extensions | Yes (Modular) | **Top Recommendation for K-12**: Chromebooks, tablets, mobile, fast load |
| **Ace Editor** | Moderate (~300 KB) | Good | Basic linting | Yes (Web Worker) | Quick quiz embeds, inline question editors |
| **Sandpack** | Moderate (react-based) | Good | In-browser bundler | Yes (Iframe sandbox) | Web development tracks (React, Vue, HTML/CSS/JS) |
| **StackBlitz WebContainers** | Heavy (Wasm OS) | Chrome/Edge only | Full Node.js in browser | Yes (Browser Sandbox) | Advanced full-stack web tracks with Node & npm |

### Detailed Recommendations:

#### Option A: CodeMirror 6 (Recommended Default for K-12)
- **Why it fits Codingal:**
  - Extremely lightweight: Loads in milliseconds even over 3G/4G cellular or congested school Wi-Fi.
  - Native touch and virtual keyboard handling: essential for elementary/middle school students using iPads or touchscreen Chromebooks.
  - Extensible: Easy to add custom linting, visual hints, and kid-friendly error explanations.
  - Zero vulnerability surface: pure DOM manipulation with strict CSP compatibility.

#### Option B: Monaco Editor (For Teacher Workspace & Pro Tracks)
- **Why it fits Codingal:**
  - Familiarity: Exactly the same editor experience as VS Code.
  - Rich IntelliSense: Autocomplete, parameter hints, syntax colorization, and multi-file project views.
  - Web Worker sandboxing: Tokenization and AST parsing happen in background Web Workers, so large scripts never freeze the browser UI.

---

## 2. In-Browser Sandboxed Runtimes (Zero Server Cost, Instant GUI)

For visual and graphical libraries like **Turtle**, **Tkinter**, and **Pygame**, running server-side in Docker containers introduces display server overhead (X11 / VNC) and network lag. Browser-side sandboxed runtimes execute directly in the learner's browser:

### 1. Pyodide (WebAssembly CPython)
- **What it is:** Official CPython 3 compiled to WebAssembly via Emscripten.
- **Capabilities:**
  - Runs 100% client-side in a Web Worker sandbox.
  - Supports `pygame-ce` (Pygame Community Edition) compiled to WebAssembly with direct HTML5 `<canvas>` rendering!
  - Supports NumPy, Pandas, Matplotlib for data science tracks.
- **Security:** Sandboxed by the browser's WebAssembly and Web Worker isolation boundary. No backend access, no server bills.

### 2. Skulpt (Python-to-JS Compiler)
- **What it is:** The educational standard (powering Trinket, Repl.it, CodeCombat, and Runestone).
- **Capabilities:**
  - Instant startup (<50ms).
  - Native HTML5 Canvas **Turtle** implementation: smooth step-by-step animations, pen controls, stamps, coordinates, and color fills.
  - Zero installation: runs everywhere.
- **Security:** Transpiles Python to JavaScript in a sandboxed scope. Cannot escape the DOM iframe.

### 3. Virtual Arena Engine (Included in this pilot)
- **What it is:** The hybrid engine implemented in `runner/arena_executor.py` and `static/app.js`:
  - Intercepts and traces Turtle vector steps into an interactive HTML5 Canvas with speed sliders, coordinates grid, and image export.
  - Simulates Tkinter window frames, reactive buttons, entries, labels, and callbacks.
  - Simulates 60 FPS Pygame display surfaces, draw primitives, and keyboard controls.
  - Provides a unified **Console** tab alongside the **GUI** canvas viewport!

---

## 3. Production Backend Execution Sandboxes (When Running Native Code)

When compiling and running native **Java**, **C++**, or untrusted multi-tenant backend workloads:

| Solution | Isolation Level | Startup Time | Multi-tenant Safety | Maintenance |
| :--- | :--- | :--- | :--- | :--- |
| **Judge0** (Open Source) | High (Linux cgroups + seccomp) | ~100–200 ms | High (Battle-tested) | Medium (Docker-compose) |
| **Piston** (Engineer-man) | High (runc + cgroups) | ~50–150 ms | High (Used in Discord bots) | Easy (Prebuilt images) |
| **AWS Firecracker MicroVMs** | Maximum (Hardware KVM) | ~5–10 ms | Enterprise grade | High (Infrastructure team) |
| **gVisor (runsc)** | Very High (Syscall interception) | ~50 ms | Production grade | Medium (K8s runtime class) |
| **Local Docker Runner** *(Current Pilot)* | Baseline (Docker `--cap-drop=ALL`) | ~300–600 ms | Dev / Prototype only | Docker Desktop required |

### Production Recommendation:
1. **For Turtle, Tkinter, Pygame & Web:** Use the **Client-Side Canvas & Virtual Arena Engine** (Pyodide / Skulpt / Virtual Arena). This guarantees 60 FPS visual smoothness and eliminates server GPU/X11 infrastructure costs.
2. **For Native Python CLI, Java & C++:** Deploy **Judge0** or **Piston** on an isolated Kubernetes cluster with `gVisor` (`runsc`) container runtime.


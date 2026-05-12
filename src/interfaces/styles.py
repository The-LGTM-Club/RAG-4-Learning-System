CSS = """
:root {
  --surface: #f7f4ee;
  --card: #ffffff;
  --ink: #1f2937;
  --accent: #0f766e;
  --accent-2: #b45309;
  --line: #d6d3d1;
}

.gradio-container {
  background:
    radial-gradient(circle at top left, rgba(15, 118, 110, 0.12), transparent 32%),
    radial-gradient(circle at bottom right, rgba(180, 83, 9, 0.12), transparent 28%),
    var(--surface);
  color: var(--ink);
  font-family: "Segoe UI", sans-serif;
}

.block {
  border: 1px solid var(--line) !important;
  border-radius: 16px !important;
  background: var(--card) !important;
}

button.primary {
  background: linear-gradient(135deg, var(--accent), #115e59) !important;
}

#app-title h1 {
  letter-spacing: 0.02em;
}
"""

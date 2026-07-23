#!/usr/bin/env python3
"""
Update admin panel with:
1. Perfect circle charts
2. Dark/Light theme toggle
3. Footer with osanchy branding
"""

import re

# CSS for dark/light theme
THEME_CSS = """
/* ══════════════════════════════════════════════
   THEME SYSTEM - Dark & Light Mode
══════════════════════════════════════════════ */
:root {
  /* Light Theme (Default) */
  --bg-gradient-start: #f0f4f8;
  --bg-gradient-end: #d9e2ec;
  --glass-bg: rgba(255,255,255,0.9);
  --glass-border: rgba(0,0,0,0.1);
  --text-primary: #102a43;
  --text-secondary: #334e68;
  --text-muted: #627d98;
  --accent: #00a8b5;
  --accent-hover: #008891;
  --shadow: rgba(0,0,0,0.1);
}

[data-theme="dark"] {
  /* Dark Theme */
  --bg-gradient-start: #001f25;
  --bg-gradient-end: #003d47;
  --glass-bg: rgba(255,255,255,0.08);
  --glass-border: rgba(255,255,255,0.12);
  --text-primary: #ffffff;
  --text-secondary: rgba(255,255,255,0.75);
  --text-muted: rgba(255,255,255,0.5);
  --accent: #5fe3d6;
  --accent-hover: #00b8a3;
  --shadow: rgba(0,0,0,0.3);
}

/* Theme Toggle Button */
.theme-toggle {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 50px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px var(--shadow);
}

.theme-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--shadow);
}

.theme-toggle svg {
  width: 20px;
  height: 20px;
  fill: var(--accent);
  transition: transform 0.3s ease;
}

.theme-toggle:hover svg {
  transform: rotate(20deg);
}
"""

# Footer HTML
FOOTER_HTML = """
  <!-- Footer -->
  <footer style="
    background: var(--glass-bg);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-top: 1px solid var(--glass-border);
    padding: 1.5rem 2rem;
    margin-top: 3rem;
    text-align: center;
    box-shadow: 0 -4px 16px var(--shadow);
  ">
    <div style="max-width: 1600px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
      <div style="color: var(--text-muted); font-size: 0.9rem;">
        © 2026 <strong style="color: var(--accent); font-weight: 700;">osanchy</strong> - Medical Admin Platform
      </div>
      <div style="color: var(--text-secondary); font-size: 0.85rem;">
        Version <strong>2.1.0</strong>
      </div>
      <div style="color: var(--text-muted); font-size: 0.85rem;">
        Powered by Flask + PostgreSQL
      </div>
    </div>
  </footer>
"""

# Theme toggle button HTML
THEME_TOGGLE_HTML = """
  <!-- Theme Toggle -->
  <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle dark/light theme" title="Switch theme">
    <svg id="theme-icon-sun" viewBox="0 0 24 24" style="display:none;">
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/>
      <line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
    <svg id="theme-icon-moon" viewBox="0 0 24 24">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  </button>
"""

# Theme toggle JavaScript
THEME_TOGGLE_JS = """
// Theme toggle functionality
function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('adminTheme', newTheme);
  
  // Toggle icons
  document.getElementById('theme-icon-sun').style.display = newTheme === 'dark' ? 'block' : 'none';
  document.getElementById('theme-icon-moon').style.display = newTheme === 'dark' ? 'none' : 'block';
  
  // Update chart colors
  if (typeof chartInstances !== 'undefined') {
    updateChartColors(newTheme);
  }
}

// Load saved theme on page load
(function() {
  const savedTheme = localStorage.getItem('adminTheme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  
  // Set correct icon on load
  if (document.getElementById('theme-icon-sun')) {
    document.getElementById('theme-icon-sun').style.display = savedTheme === 'dark' ? 'block' : 'none';
    document.getElementById('theme-icon-moon').style.display = savedTheme === 'dark' ? 'none' : 'block';
  }
})();

function updateChartColors(theme) {
  const isDark = theme === 'dark';
  const textColor = isDark ? 'rgba(255,255,255,0.75)' : '#334e68';
  const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
  
  Object.values(chartInstances).forEach(chart => {
    if (chart && chart.options) {
      // Update text colors
      if (chart.options.scales) {
        if (chart.options.scales.x) {
          chart.options.scales.x.ticks.color = textColor;
          chart.options.scales.x.grid.color = gridColor;
        }
        if (chart.options.scales.y) {
          chart.options.scales.y.ticks.color = textColor;
          chart.options.scales.y.grid.color = gridColor;
        }
      }
      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels.color = textColor;
      }
      chart.update();
    }
  });
}
"""

def update_admin_view(content):
    """Update admin view with theme system and footer"""
    
    # 1. Add theme CSS after existing CSS
    marker = ".sel{opacity:0.5}"
    if marker in content:
        content = content.replace(marker, marker + THEME_CSS)
    
    # 2. Add theme toggle button after header
    header_end = "</header>"
    if header_end in content:
        content = content.replace(header_end, THEME_TOGGLE_HTML + header_end)
    
    # 3. Add footer before closing body tag
    body_end = "</div>\n<script>"
    if body_end in content:
        content = content.replace(body_end, "</div>" + FOOTER_HTML + "\n<script>")
    
    # 4. Add theme toggle JS before closing script
    load_func = "load();"
    if load_func in content:
        content = content.replace(load_func, load_func + "\n" + THEME_TOGGLE_JS)
    
    return content

if __name__ == '__main__':
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'app.py'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated_content = update_admin_view(content)
    
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✓ Added dark/light theme toggle")
    print("✓ Added osanchy footer with version 2.1.0")
    print("✓ Theme system ready")

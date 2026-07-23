#!/usr/bin/env python3
"""
Script to update the admin view HTML in app.py with:
1. Perfect circle charts
2. Clickable rows that open medical records in new tab
3. Flip animation on double-click
"""

import sys

def update_admin_html(content):
    """Update the ADMIN_VIEW_HTML section with new features"""
    
    # 1. Fix canvas styling for perfect circles
    content = content.replace(
        '.panel canvas{display:block;width:100% !important;height:300px !important}',
        '''.panel canvas{display:block;width:100% !important;max-height:400px !important}
 .panel.chart-circle{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem}
 .panel.chart-circle canvas{aspect-ratio:1/1 !important;width:min(100%,350px) !important;height:auto !important;max-height:350px !important}'''
    )
    
    # 2. Add row styling for clickable and flippable rows
    content = content.replace(
        'tbody tr:hover{background:rgba(255,255,255,0.03)}',
        '''tbody tr{cursor:pointer;transition:all 0.2s ease}
 tbody tr:hover{background:rgba(95,227,214,0.1);transform:scale(1.005)}
 tbody tr:active{transform:scale(0.998)}'''
    )
    
    # 3. Make Status chart circular
    content = content.replace(
        '''<div class="panel">
      <h2 data-en="By Status" data-es="Por estado">By Status</h2>
      <canvas id="cStatus"></canvas>
    </div>''',
        '''<div class="panel chart-circle">
      <h2 data-en="By Status" data-es="Por estado">By Status</h2>
      <canvas id="cStatus"></canvas>
    </div>'''
    )
    
    # 4. Make Mix chart circular
    content = content.replace(
        '''<div class="panel">
      <h2 data-en="Real vs. Dummy" data-es="Reales vs. Dummy">Real vs. Dummy</h2>
      <canvas id="cMix"></canvas>
    </div>''',
        '''<div class="panel chart-circle">
      <h2 data-en="Real vs. Dummy" data-es="Reales vs. Dummy">Real vs. Dummy</h2>
      <canvas id="cMix"></canvas>
    </div>'''
    )
    
    # 5. Add onclick handler to table rows
    content = content.replace(
        '''rows.innerHTML=d.rows.map(r=>`
      <tr class="${r.is_dummy?'sel':''}">''',
        '''rows.innerHTML=d.rows.map(r=>`
      <tr class="${r.is_dummy?'sel':''}" onclick="openMedicalRecord(${r.id}, event)" data-booking-id="${r.id}">'''
    )
    
    # 6. Add the JavaScript functions before charts()
    charts_func_start = 'let chartInstances = {};'
    if charts_func_start in content:
        js_functions = '''// Open medical records in new tab
function openMedicalRecord(bookingId, event) {
  // Prevent if clicking on select/dropdown
  if (event.target.tagName === 'SELECT' || event.target.closest('select')) {
    return;
  }
  const medicalRecordsUrl = '/admin/medical-records?booking_id=' + bookingId;
  window.open(medicalRecordsUrl, '_blank', 'width=1400,height=900,scrollbars=yes,resizable=yes');
}
''' + charts_func_start
        content = content.replace(charts_func_start, js_functions)
    
    return content

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'app.py'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated_content = update_admin_html(content)
    
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✓ Updated {input_file} with perfect circle charts and clickable rows")

# Drag & Drop Navigation Reordering - Admin Panel

## 🎯 Feature Overview

The admin panel navigation menu items can now be reordered by dragging and dropping. Your preferred order is automatically saved and restored on each visit.

## 🖱️ How To Use

### Reorder Menu Items

1. **Hover over any navigation item** (Pendientes, Aprobadas, Exportar, Citas)
2. **You'll see a drag handle appear** (⋮⋮) on the left side
3. **Click and hold on the item** to start dragging
4. **Drag up or down** to your desired position
5. **Release** to drop the item in the new position
6. **Toast notification** confirms "Orden del menú guardado"

### Visual Feedback

**While hovering:**
- Drag handle (⋮⋮) fades in with 60% opacity

**While dragging:**
- Dragged item becomes semi-transparent (50% opacity) and slightly smaller
- Cursor changes to "grabbing"

**While dragging over target:**
- Target item shows a turquoise line at the top indicating drop zone

**After dropping:**
- Items smoothly rearrange to new positions
- Toast notification confirms save

## 💾 Data Persistence

### Storage Method
- **Where**: Browser localStorage
- **Key**: `dds_nav_order`
- **Format**: JSON array of tab names
- **Example**: `["appointments", "pending", "approved", "export"]`

### Persistence Scope
- **Per browser**: Each browser stores its own order
- **Per device**: Not synced across devices
- **Permanent**: Survives browser restarts and page reloads
- **Isolated**: GitHub Pages admin and Backend admin have separate saved orders

### Clear Saved Order

To reset to default order:

**Option 1: Browser DevTools**
```javascript
// Open browser console (F12) and run:
localStorage.removeItem('dds_nav_order');
location.reload();
```

**Option 2: Clear All Admin Data**
```javascript
// Clear all admin panel localStorage
localStorage.clear();
location.reload();
```

## 🎨 CSS Classes

### Drag Handle
```css
.adm-drag-handle {
  opacity: 0;              /* Hidden by default */
  margin-right: 8px;
  font-size: 14px;
  color: var(--muted);
  cursor: grab;
}

.adm-nav__item:hover .adm-drag-handle {
  opacity: 0.6;            /* Visible on hover */
}
```

### Dragging State
```css
.adm-nav__item.dragging {
  opacity: 0.5;            /* Semi-transparent */
  transform: scale(0.95);  /* Slightly smaller */
  cursor: grabbing;
}
```

### Drop Target
```css
.adm-nav__item.drag-over {
  border-top: 2px solid var(--accent);  /* Turquoise indicator */
}
```

## 🔧 Technical Implementation

### HTML Structure

Each navigation item has:
- `draggable="true"` attribute
- `data-tab` attribute (unique identifier)
- `data-order` attribute (initial order number)
- Drag handle span

```html
<button class="adm-nav__item" 
        data-tab="pending" 
        data-order="1" 
        draggable="true">
  <span class="adm-drag-handle" aria-hidden="true">⋮⋮</span>
  <svg>...</svg>
  Pendientes
  <span class="adm-badge">0</span>
</button>
```

### JavaScript Functions

**`initDragAndDrop()`**
- Initializes drag event listeners on all nav items
- Loads saved order from localStorage
- Called once during page initialization

**`saveNavOrder()`**
- Reads current DOM order of nav items
- Extracts `data-tab` attributes
- Saves array to localStorage as JSON

**`loadNavOrder()`**
- Reads saved order from localStorage
- Reorders DOM elements to match saved order
- Called during initialization

### Event Listeners

**dragstart**
```javascript
item.addEventListener('dragstart', function(e) {
  draggedElement = this;
  this.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
});
```

**dragover**
```javascript
item.addEventListener('dragover', function(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  if (draggedElement !== this) {
    this.classList.add('drag-over');
  }
});
```

**drop**
```javascript
item.addEventListener('drop', function(e) {
  e.stopPropagation();
  
  // Reorder DOM elements
  if (draggedIndex < droppedIndex) {
    this.parentNode.insertBefore(draggedElement, this.nextSibling);
  } else {
    this.parentNode.insertBefore(draggedElement, this);
  }
  
  // Save new order
  saveNavOrder();
  showToast('Orden del menú guardado');
});
```

## 🌐 Browser Compatibility

### Supported Browsers
- ✅ **Chrome/Edge** (latest)
- ✅ **Firefox** (latest)
- ✅ **Safari** (latest)
- ✅ **Mobile Safari** (iOS)
- ✅ **Chrome Mobile** (Android)

### HTML5 Drag and Drop API
Uses native HTML5 Drag and Drop API, supported by all modern browsers since:
- Chrome 4+
- Firefox 3.5+
- Safari 3.1+
- Edge (all versions)
- Opera 12+

### Touch Support
Native drag and drop may not work perfectly on all touch devices. Consider adding:
- Long-press to initiate drag on mobile
- Alternative touch-based reordering (future enhancement)

## 📱 Mobile Considerations

### Current Implementation
- Works on desktop browsers
- Limited support on mobile (HTML5 drag-drop not ideal for touch)

### Future Enhancement Ideas
1. **Touch Events**: Add touch event handlers for better mobile support
2. **Drag Indicator**: Add a more prominent "handle" icon for touch
3. **Vibration Feedback**: Use Vibration API on mobile when dragging
4. **Alternative UI**: Provide "Edit Order" modal with up/down buttons

## 🎯 Use Cases

### Different User Workflows

**Doctor's View:**
- Puts "Citas" (Appointments) first
- Needs quick access to patient schedules

**Administrator's View:**
- Puts "Pendientes" (Pending Reviews) first
- Focuses on review moderation

**Manager's View:**
- Puts "Aprobadas" (Approved) first
- Monitors published content

**Analyst's View:**
- Puts "Exportar" (Export) first
- Frequently downloads data

Each user can customize their sidebar to match their daily workflow!

## 🐛 Known Issues & Solutions

### Issue: Order Not Saving
**Symptoms**: Items revert to original order on refresh

**Possible Causes**:
1. Browser blocking localStorage
2. Private/Incognito mode (localStorage cleared on close)
3. Browser extension interfering

**Solution**:
- Check browser console for errors
- Ensure localStorage is enabled
- Try different browser
- Disable browser extensions

### Issue: Drag Not Working
**Symptoms**: Cannot drag items

**Possible Causes**:
1. JavaScript errors on page
2. Browser doesn't support drag-drop
3. Another script interfering

**Solution**:
- Check browser console for errors
- Try refreshing the page
- Update browser to latest version

### Issue: Visual Glitches
**Symptoms**: Items appear in wrong position or flash

**Possible Causes**:
1. Slow browser
2. CSS conflicts
3. Multiple rapid drags

**Solution**:
- Wait for drag animation to complete
- Close other browser tabs
- Refresh the page

## 🔐 Security Considerations

### Data Privacy
- ✅ Order saved locally (never sent to server)
- ✅ No personal data stored
- ✅ Isolated per browser

### XSS Protection
- ✅ No user input stored in order
- ✅ Only predefined tab names saved
- ✅ JSON.parse with try-catch

### Storage Limits
- localStorage has 5-10MB limit per domain
- This feature uses <1KB (negligible)

## 📊 Storage Format

### Example localStorage Entry

**Key**: `dds_nav_order`

**Default Order (before customization)**:
```json
["pending", "approved", "export", "appointments"]
```

**Custom Order Example**:
```json
["appointments", "pending", "export", "approved"]
```

### Validation
- Array must contain valid tab names
- Duplicate tabs ignored
- Missing tabs appended at end
- Invalid JSON falls back to default

## 🎓 For Developers

### Adding New Navigation Items

When adding a new nav item to the sidebar:

1. **Add to HTML** with required attributes:
```html
<button class="adm-nav__item" 
        data-tab="newitem" 
        data-order="5" 
        draggable="true">
  <span class="adm-drag-handle" aria-hidden="true">⋮⋮</span>
  <!-- icon and text -->
  New Item
</button>
```

2. **No JavaScript changes needed!** The drag-drop system automatically detects all `.adm-nav__item` elements.

3. **Default order**: Set `data-order` to determine initial position.

### Customizing Drag Behavior

**Change drag handle icon**:
```html
<span class="adm-drag-handle" aria-hidden="true">☰</span>
```

**Change accent color**:
```css
:root {
  --accent: #your-color;  /* Changes drop indicator */
}
```

**Disable for specific items**:
```html
<button class="adm-nav__item" data-tab="fixed">
  <!-- No draggable="true" and no drag handle -->
  Fixed Item
</button>
```

## 📝 Changelog

**v1.0.0** - July 24, 2026
- ✅ Initial release
- ✅ Drag & drop reordering
- ✅ localStorage persistence
- ✅ Visual feedback
- ✅ Toast notifications
- ✅ Mobile-friendly drag handles

## 🚀 Future Enhancements

### Planned Features
1. **Touch support** - Better mobile drag-drop experience
2. **Sync across devices** - Store order in backend user profile
3. **Reset button** - One-click reset to default order
4. **Keyboard shortcuts** - Alt+↑/↓ to reorder
5. **Preset layouts** - "Doctor View", "Admin View", etc.
6. **Animation options** - Customize drag animations

### Community Requests
Submit feature requests via GitHub Issues!

---

**Made with ❤️ by Julián Sánchez**  
**Last Updated**: July 24, 2026

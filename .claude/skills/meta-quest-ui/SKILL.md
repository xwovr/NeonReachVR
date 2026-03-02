---
name: meta-quest-ui
description: Configure Unity UI for Meta Quest VR development following best practices. Use when setting up Canvas for VR, configuring TextMesh Pro, setting UI scale and font sizes, or optimizing UI performance for Meta Quest. Covers world space canvas setup, recommended viewing distances, comfortable text sizes, and VR-specific UI considerations.
---

# Meta Quest UI Best Practices

This skill provides comprehensive guidance for setting up Unity UI for Meta Quest VR applications, covering Canvas configuration, TextMesh Pro setup, scaling, font sizing, and performance optimization.

## CRITICAL: Mandatory Validation Workflow

**ALWAYS follow this workflow when creating VR UI - validation is NOT optional**:

### Step 0: PREREQUISITE - Verify TMP Resources Are Imported

**Before creating ANY VR UI, check if TextMesh Pro Essential Resources are imported:**

1. **Check for TMP resources folder** using Glob tool:
   ```
   pattern: "**/TextMesh Pro/Resources/Fonts & Materials/LiberationSans SDF.asset"
   ```

2. **If NOT found**:
   - Use the **tmp-resources** skill to import TMP Essential Resources
   - Wait for import to complete
   - Verify import succeeded before proceeding

3. **Why this is critical**:
   - Meta Quest VR UI requires TextMesh Pro (never use legacy Text components)
   - Without TMP Essential Resources, text will appear pink/magenta
   - Missing resources cause material/shader errors
   - Import MUST happen before creating UI elements

**Example check pattern**:
```javascript
// Check if TMP resources exist
const tmpResources = await Glob({ pattern: "**/LiberationSans SDF.asset" });

if (tmpResources === "No files found") {
  // Resources missing - import them first
  await Skill({ skill: "tmp-resources", args: "import essential resources" });

  // Verify import succeeded
  const verifyImport = await Glob({ pattern: "**/LiberationSans SDF.asset" });
  if (verifyImport === "No files found") {
    throw new Error("TMP import failed - cannot create VR UI");
  }
}

// Now safe to proceed with UI creation...
```

### Step 1: Create UI Elements
Use Unity MCP tools to create Canvas, panels, buttons, and text elements.

### Step 2: IMMEDIATELY Validate Configuration
After creating UI elements, you MUST verify that properties were actually applied:

```
1. Get components from created objects using manage_gameobject with action="get_components"
2. Check EACH critical property in the returned data
3. Compare actual values against expected values
4. If ANY properties don't match, fix them immediately
```

### Step 3: Fix Discrepancies
Unity MCP property setting can fail silently. Common issues:
- Canvas scale remains at 1,1,1 instead of 0.001
- **Child elements auto-scaled to compensate for parent (e.g., 1000x instead of 1x)**
- **Child elements positioned with incorrect Z offset (e.g., localPosition.z = -2500 instead of 0)**
- Layout group properties not applied (spacing, padding, alignment)
- RectTransform sizeDelta not set correctly
- Component colors reverting to default white

**Solution**: After initial creation, ALWAYS call `manage_gameobject` with `action="modify"` to ensure values are applied, then re-validate. For child elements, always explicitly set `localScale: [1, 1, 1]` and `localPosition` with Z=0.

### Step 4: Report to User
Only after validation passes should you report success. Include:
- What was created
- Confirmation that all critical properties match best practices
- Any warnings or remaining manual steps

## Why Validation is Mandatory

Unity's property setting through MCP can have issues:
- Properties may not apply on first attempt
- Some properties require specific ordering
- Unity may reset values during component initialization
- Layout groups may override RectTransform properties

**Never assume properties were set correctly - always verify.**

## Complete Example: Creating VR Menu with Validation

**Correct workflow for creating a button menu UI:**

```
0. CHECK TMP RESOURCES (PREREQUISITE)
   - Glob: search for "**/LiberationSans SDF.asset"
   - If not found: Use tmp-resources skill to import
   - Verify import succeeded before continuing

1. CREATE Canvas
   - manage_gameobject: create Canvas with World Space

2. VALIDATE Canvas immediately
   - manage_gameobject: get_components on Canvas
   - Check: renderMode === 2, localScale === [0.001, 0.001, 0.001]
   - If wrong: set_component_property to fix, then re-validate

3. CREATE Panel
   - manage_gameobject: create panel with Image + LayoutGroup
   - IMPORTANT: Explicitly set localScale to [1, 1, 1] for child elements
   - Use sizeDelta and anchors to control size, NOT scale

4. VALIDATE Panel
   - get_components on Panel
   - Check: localScale === [1, 1, 1] (CRITICAL!)
   - Check: localPosition.z === 0 (CRITICAL - should be on canvas plane!)
   - Check: color, sizeDelta, layout spacing/padding
   - If wrong: fix and re-validate

5. CREATE Buttons
   - manage_gameobject: create buttons with Image + Button components
   - IMPORTANT: Explicitly set localPosition with z=0

6. VALIDATE Buttons
   - get_components on each button
   - Check: localScale === [1, 1, 1]
   - Check: localPosition.z === 0 (CRITICAL - buttons far from canvas is common issue!)
   - Check: colors, sizes, all properties
   - If wrong: fix and re-validate

7. CREATE Text (TMP)
   - manage_gameobject: create TextMeshProUGUI children

8. VALIDATE Text
   - get_components on each text
   - Check: localScale === [1, 1, 1]
   - Check: localPosition.z === 0
   - Check: fontSize >= 48, color, alignment, raycastTarget === false
   - If wrong: fix and re-validate

9. FINAL VALIDATION
   - get_components on all objects one more time
   - Verify complete checklist
   - Report success to user ONLY after all checks pass
```

**Anti-pattern (what NOT to do)**:
```
❌ Skip TMP resources check
❌ Create all UI elements
❌ Assume properties were set
❌ Report "success" to user
❌ Wait for user to notice problems
```

## Quick Start

**Essential VR UI Setup Checklist**:
1. Canvas Render Mode: **World Space** (never Screen Space)
2. Canvas Scale: **0.001** (1:1000 ratio)
3. TextMesh Pro Font Size: **36-48** points minimum
4. Recommended Viewing Distance: **1.5-3 meters**
5. Canvas Position Z: **2-3 units** from camera

## Canvas Setup for VR

### World Space Configuration

**Always use World Space render mode for VR**:

```csharp
// Canvas configuration for VR
Canvas canvas = GetComponent<Canvas>();
canvas.renderMode = RenderMode.WorldSpace;

// Recommended scale
RectTransform canvasRect = canvas.GetComponent<RectTransform>();
canvasRect.localScale = new Vector3(0.001f, 0.001f, 0.001f);

// Recommended size (in world units after scale)
canvasRect.sizeDelta = new Vector2(1920f, 1080f); // Results in 1.92m x 1.08m panel
```

**Why World Space?**:
- Screen Space Overlay/Camera modes don't work correctly in VR
- World Space allows proper stereo rendering
- Users can naturally focus on UI at proper depth
- Prevents eye strain from incorrect convergence

### Canvas Positioning

**Recommended distances from user**:
- **Near UI** (action buttons, controls): 1.5-2 meters
- **Primary UI** (menus, panels): 2-3 meters
- **Informational UI** (HUD, status): 2.5-3.5 meters
- **Minimum distance**: Never closer than 0.5 meters
- **Maximum distance**: No farther than 5 meters for readable text

**Example placement**:
```csharp
// Position UI 2 meters in front of user
canvas.transform.position = Camera.main.transform.position + Camera.main.transform.forward * 2f;

// Orient to face user
canvas.transform.rotation = Quaternion.LookRotation(canvas.transform.position - Camera.main.transform.position);
```

### Canvas Scaler Settings

**Do NOT use Canvas Scaler in VR**:
```csharp
// Remove or disable Canvas Scaler component
CanvasScaler scaler = GetComponent<CanvasScaler>();
if (scaler != null) {
    DestroyImmediate(scaler);
}
```

**Why?** Canvas Scaler is designed for 2D screen adaptation. In VR:
- Physical size is controlled by world space scale
- Dynamic scaling causes judder and discomfort
- Fixed scale provides consistent user experience

### Child Element Scaling (CRITICAL)

**ALWAYS keep child elements at localScale [1, 1, 1]**:

```csharp
// CORRECT: Canvas at 0.001 scale, children at 1.0 scale
Canvas canvas = GetComponent<Canvas>();
canvas.GetComponent<RectTransform>().localScale = new Vector3(0.001f, 0.001f, 0.001f);

// Child panel - keep scale at 1.0
GameObject panel = new GameObject("Panel");
panel.transform.SetParent(canvas.transform);
RectTransform panelRect = panel.AddComponent<RectTransform>();
panelRect.localScale = Vector3.one; // ✓ CORRECT - always 1.0
panelRect.sizeDelta = new Vector2(1000f, 600f); // ✓ Use sizeDelta for size
panelRect.anchorMin = new Vector2(0.5f, 0.5f);
panelRect.anchorMax = new Vector2(0.5f, 0.5f);

// WRONG: Scaling child to compensate for parent
panelRect.localScale = new Vector3(1000f, 1000f, 1000f); // ✗ WRONG!
```

**Why this is critical**:
- Unity MCP may auto-scale children to compensate for parent scale, causing issues
- Scaling children breaks layout calculations and makes UI unpredictable
- Child scale should inherit from parent, not compensate for it
- Use RectTransform properties (sizeDelta, anchors) to control size, NOT scale

**When creating UI hierarchy via Unity MCP**:
```javascript
// When creating child elements, ALWAYS explicitly set localScale to [1, 1, 1]
const panel = await manage_gameobject({
  action: "create",
  name: "ButtonPanel",
  parent: "MenuUI",
  component_properties: {
    "RectTransform": {
      "localScale": [1, 1, 1],        // ✓ CRITICAL: Explicitly set to 1
      "sizeDelta": [1000, 600],       // ✓ Control size with sizeDelta
      "anchorMin": [0.5, 0.5],        // ✓ Use anchors for positioning
      "anchorMax": [0.5, 0.5]
    },
    "Image": {
      "color": [0.1, 0.1, 0.1, 0.95]
    }
  }
});

// VALIDATE immediately after creation
const components = await manage_gameobject({
  action: "get_components",
  target: "ButtonPanel",
  search_method: "by_name"
});

const rectTransform = components.data.find(c => c.typeName === "UnityEngine.RectTransform");
if (rectTransform.properties.localScale.x !== 1.0) {
  // FIX IT - scale should be 1.0!
  await manage_gameobject({
    action: "modify",
    target: "ButtonPanel",
    search_method: "by_name",
    component_properties: {
      "RectTransform": {"localScale": [1, 1, 1]}
    }
  });
}
```

**Summary**:
- **Canvas**: localScale = [0.001, 0.001, 0.001]
- **All children (panels, buttons, text, etc.)**: localScale = [1, 1, 1]
- **Size control**: Use RectTransform.sizeDelta, NOT scale
- **Always validate**: Check localScale after creating child elements

## VR UI Interaction Setup

**WHEN TO ADD VR INTERACTION**: Only add interaction components when your Canvas has interactive elements (buttons, dropdowns, sliders, toggles, input fields). If your Canvas is display-only (HUD, labels, score displays), interaction components are NOT needed.

### When VR Interaction is REQUIRED

Add VR interaction components when your Canvas contains ANY of these:

✅ **Buttons** - Any clickable UI elements
✅ **Dropdowns** - Selection menus
✅ **Sliders** - Value adjustment controls
✅ **Toggles/Checkboxes** - On/off switches
✅ **Input Fields** - Text entry (with virtual keyboard)
✅ **Scrollable areas** - ScrollRect components
✅ **Draggable elements** - Any UI requiring pointer interaction

**Examples needing interaction**:
- Main menu with "Start", "Settings", "Quit" buttons
- Settings panel with sliders, toggles, dropdowns
- Inventory system with clickable items
- Virtual keyboard
- Radial menus

### When VR Interaction is NOT Needed

Do NOT add interaction components for display-only UI:

❌ **Pure displays** - Score, health, timer (no user input)
❌ **Labels** - Static text and images
❌ **Status indicators** - Progress bars that users don't interact with
❌ **Notifications** - Temporary messages
❌ **Tooltips** - Hover text (displayed by code, not clicked)

**Examples NOT needing interaction**:
- Gameplay HUD showing score, health, ammo
- Timer display
- Instructional text
- Non-interactive cutscene subtitles
- Damage indicators
- Waypoint markers

### Decision Tree

```
Does your Canvas have buttons, dropdowns, sliders, toggles, or input fields?
├─ YES → Add VR interaction (meta_add_canvas_interaction_ray)
│         Without this, interactive elements won't work in VR!
│
└─ NO  → Skip VR interaction components
          Display-only UI doesn't need interaction overhead
```

### Quick Setup with Unity MCP

**ONLY use these functions when Canvas has interactive elements**:

#### Ray Interaction (Primary Method)

**Use for most interactive VR UI** - allows users to point at UI with controller rays or hand rays:

```javascript
// Add ray interaction to canvas (REQUIRED for button clicks in VR!)
await mcp__unityMCP__meta_add_canvas_interaction_ray({
  NameOrID: "MyCanvas"  // Canvas GameObject name or instance ID
});
```

**What this adds**:
- `RayInteractable` component - makes canvas respond to ray pointers
- `PointableCanvas` component - Meta Quest specific pointer tracking
- `ISDK_RayCanvasInteraction` GameObject - interaction surface configuration
- `Pointable Canvas Module` - global interaction manager (added to scene once)

**When to use**:
- Menu systems
- Settings panels
- Any UI farther than arm's reach
- Hover tooltips
- Dropdown menus
- **DEFAULT CHOICE - use this for most VR UIs**

#### Poke Interaction (For Close-Range UI)

**Use for physical touch-style interaction**:

```javascript
// Add poke interaction to canvas (for direct hand touch)
await mcp__unityMCP__meta_add_canvas_interaction_poke({
  NameOrID: "MyCanvas"
});
```

**What this adds**:
- `PokeInteractable` component - responds to finger/hand pokes
- `PointableCanvas` component - pointer tracking
- Close-range collision detection for hand tracking

**When to use**:
- UI attached to objects (diegetic UI)
- Control panels on surfaces
- Virtual keyboards
- Touch-sensitive buttons
- **ONLY use when Canvas is within arm's reach (< 0.8m)**

#### Both Ray and Poke (Advanced)

For maximum flexibility, add BOTH interaction types:

```javascript
// Add ray interaction first
await mcp__unityMCP__meta_add_canvas_interaction_ray({
  NameOrID: "MyCanvas"
});

// Then add poke interaction
await mcp__unityMCP__meta_add_canvas_interaction_poke({
  NameOrID: "MyCanvas"
});
```

**When to use**:
- Hybrid UIs (users can point OR touch)
- Adaptive interaction distances
- Advanced VR experiences

### Complete Workflow for Interactive VR UI

**ONLY use this workflow when creating UI with buttons, dropdowns, sliders, or other interactive elements**:

```javascript
// Step 1: Create Canvas
const canvas = await manage_gameobject({
  action: "create",
  name: "MenuUI",
  components_to_add: ["Canvas"],
  component_properties: {
    "Canvas": {"renderMode": 2},  // World Space
    "RectTransform": {
      "localScale": [0.001, 0.001, 0.001],
      "sizeDelta": [1920, 1080],
      "localPosition": [0, 2, 3]  // 3m in front of player
    }
  }
});

// Step 2: Create buttons, panels, etc.
const startButton = await manage_gameobject({
  action: "create",
  name: "StartButton",
  parent: "MenuUI",
  primitive_type: "Button",  // Creates Button with Image
  component_properties: {
    "RectTransform": {
      "localScale": [1, 1, 1],  // ALWAYS 1 for children!
      "sizeDelta": [400, 150],
      "anchoredPosition": [0, 0]
    },
    "Image": {
      "color": [0.2, 0.6, 1.0, 1.0]  // Blue button
    }
  }
});

// Step 3: CRITICAL - Add VR interaction to Canvas (ONLY because we have buttons!)
await mcp__unityMCP__meta_add_canvas_interaction_ray({
  NameOrID: "MenuUI"
});

// Step 4: Validate interaction components were added
const canvasComponents = await manage_gameobject({
  action: "get_components",
  target: "MenuUI",
  search_method: "by_name",
  include_non_public_serialized: true
});

// Check for RayInteractable or PointableCanvas
const hasInteraction = canvasComponents.data.some(c =>
  c.typeName === "Oculus.Interaction.PointableCanvas" ||
  c.typeName === "Oculus.Interaction.RayInteractable"
);

if (!hasInteraction) {
  // ERROR - interaction not set up! Buttons won't work in VR!
  throw new Error("VR interaction not configured on canvas");
}

// Step 5: Configure button OnClick events
// (Button events work automatically once canvas has interaction components)
```

### Workflow for Display-Only UI (HUD, Score, etc.)

**For non-interactive displays, SKIP the VR interaction setup**:

```javascript
// Step 1: Create Canvas
const hudCanvas = await manage_gameobject({
  action: "create",
  name: "GameplayHUD",
  components_to_add: ["Canvas"],
  component_properties: {
    "Canvas": {"renderMode": 2},  // World Space
    "RectTransform": {
      "localScale": [0.001, 0.001, 0.001],
      "sizeDelta": [1920, 1080],
      "localPosition": [0, 2, 3]
    }
  }
});

// Step 2: Create text displays
const scoreText = await manage_gameobject({
  action: "create",
  name: "ScoreText",
  parent: "GameplayHUD",
  components_to_add: ["TextMeshProUGUI"],
  component_properties: {
    "TextMeshProUGUI": {
      "fontSize": 64,
      "text": "Score: 0",
      "alignment": 514  // Center
    }
  }
});

// Step 3: NO VR interaction needed - this is display-only!
// Skip meta_add_canvas_interaction_ray() - it's not needed for text displays

// Canvas is complete - no validation of interaction components needed
```

### Interactive UI Elements Configuration

#### Buttons

**Minimum size for VR buttons** (at 0.001 canvas scale):

```javascript
// Standard button
{
  "RectTransform": {
    "sizeDelta": [300, 120]  // 30cm × 12cm (comfortable)
  }
}

// Large primary button
{
  "RectTransform": {
    "sizeDelta": [400, 150]  // 40cm × 15cm
  }
}

// Small secondary button
{
  "RectTransform": {
    "sizeDelta": [250, 100]  // 25cm × 10cm (MINIMUM for reliable interaction)
  }
}
```

**Button spacing** (prevent mis-clicks):

```javascript
// Vertical layout with proper spacing
{
  "VerticalLayoutGroup": {
    "spacing": 50,  // 5cm between buttons (MINIMUM)
    "padding": {"left": 80, "right": 80, "top": 100, "bottom": 100}
  }
}
```

**Button colors for VR** (high visibility):

```javascript
// Normal state
normalColor: [0.2, 0.6, 1.0, 1.0]  // Bright blue

// Highlighted state (when pointing at it)
highlightedColor: [0.3, 0.7, 1.0, 1.0]  // Lighter blue

// Pressed state (when clicking)
pressedColor: [0.1, 0.4, 0.8, 1.0]  // Darker blue

// Disabled state
disabledColor: [0.4, 0.4, 0.4, 0.5]  // Gray with transparency
```

#### Dropdowns

**Setup for VR dropdowns**:

```javascript
// Dropdown requires LARGER touch target
{
  "RectTransform": {
    "sizeDelta": [500, 140]  // Wider than buttons
  }
}

// Dropdown list items - MUST be readable
{
  "TextMeshProUGUI": {
    "fontSize": 48  // Larger than normal text
  },
  "RectTransform": {
    "sizeDelta": [500, 100]  // Each item 10cm tall
  }
}
```

**After adding dropdown**:
- Ray interaction handles dropdown expansion automatically
- No special configuration needed once canvas has `PointableCanvas`

#### Sliders

**VR-friendly sliders**:

```javascript
// Slider configuration
{
  "RectTransform": {
    "sizeDelta": [600, 80]  // Long and tall enough to see
  },
  "Slider": {
    "minValue": 0,
    "maxValue": 100,
    "wholeNumbers": false,
    "direction": 0  // Left to right
  }
}

// Slider handle - LARGER for VR
{
  "RectTransform": {
    "sizeDelta": [60, 60]  // 6cm × 6cm handle (easy to grab with ray)
  },
  "Image": {
    "color": [1.0, 1.0, 1.0, 1.0]  // White handle
  }
}

// Slider background - HIGH CONTRAST
{
  "Image": {
    "color": [0.2, 0.2, 0.2, 0.8]  // Dark background
  }
}
```

#### Toggles/Checkboxes

**VR-friendly toggles**:

```javascript
// Toggle size
{
  "RectTransform": {
    "sizeDelta": [120, 120]  // 12cm × 12cm checkbox (LARGE!)
  }
}

// Checkmark - BOLD and VISIBLE
{
  "Image": {
    "color": [0.0, 1.0, 0.0, 1.0]  // Bright green checkmark
  },
  "RectTransform": {
    "sizeDelta": [80, 80]  // Fill most of the box
  }
}

// Label text - CLOSE to toggle
{
  "TextMeshProUGUI": {
    "fontSize": 52
  },
  "RectTransform": {
    "anchoredPosition": [150, 0]  // 15cm to the right of checkbox
  }
}
```

#### Input Fields

**VR input fields** (requires virtual keyboard):

```javascript
// Input field configuration
{
  "RectTransform": {
    "sizeDelta": [800, 140]  // Wide and tall
  },
  "Image": {
    "color": [0.15, 0.15, 0.15, 0.95]  // Dark background
  }
}

// Placeholder text
{
  "TextMeshProUGUI": {
    "fontSize": 48,
    "color": [0.5, 0.5, 0.5, 1.0],  // Gray placeholder
    "text": "Enter text..."
  }
}

// Input text
{
  "TextMeshProUGUI": {
    "fontSize": 52,
    "color": [1.0, 1.0, 1.0, 1.0]  // White text
  }
}
```

**Note**: Input fields in VR typically require:
- Virtual keyboard (not included in Meta Quest UI by default)
- Voice input alternative
- Or use system keyboard with OVRVirtualKeyboard component

### Validation Checklist for Interactive UI

**AFTER adding VR interaction components, verify**:

```javascript
// Check canvas has interaction components
const components = await manage_gameobject({
  action: "get_components",
  target: "MenuUI",
  search_method: "by_name"
});

✓ Has PointableCanvas component
✓ Has RayInteractable OR PokeInteractable component
✓ GraphicRaycaster is present (added automatically with Canvas)
✓ Canvas renderMode === 2 (World Space)
✓ Canvas has correct scale (0.001, 0.001, 0.001)
```

**Check that Pointable Canvas Module exists in scene**:
```javascript
// This is created automatically by meta_add_canvas_interaction_ray
// Should appear as root GameObject in scene
const module = await manage_gameobject({
  action: "find",
  search_term: "Pointable Canvas Module",
  search_method: "by_name"
});

if (!module.success) {
  // ERROR - global interaction manager missing!
}
```

**Test button interaction** (in Play mode):
- Button should highlight when pointing at it
- Button should trigger OnClick when selecting (trigger pull)
- Visual feedback (color change) should be visible

### Common Issues and Solutions

#### Issue: Buttons visible but not clickable in VR

**CAUSE**: Missing VR interaction components on Canvas

**SYMPTOMS**:
- Buttons appear correctly
- Can see UI in VR
- Controller ray doesn't highlight buttons
- Trigger pull does nothing

**SOLUTION**:
```javascript
// Add ray interaction to canvas
await mcp__unityMCP__meta_add_canvas_interaction_ray({
  NameOrID: "MyCanvas"
});

// Verify it was added
const components = await manage_gameobject({
  action: "get_components",
  target: "MyCanvas",
  search_method: "by_name"
});

// Should now have PointableCanvas component
```

#### Issue: Buttons too small to click reliably

**CAUSE**: Button sizeDelta too small for VR interaction

**MINIMUM SIZES**:
- Buttons: 250 × 100 units (25cm × 10cm)
- Dropdowns: 500 × 140 units
- Sliders: 600 × 80 units
- Toggles: 120 × 120 units

**SOLUTION**:
```javascript
await manage_gameobject({
  action: "modify",
  target: "MyButton",
  search_method: "by_name",
  component_properties: {
    "RectTransform": {
      "sizeDelta": [300, 120]  // Increase to comfortable size
    }
  }
});
```

#### Issue: Buttons too close together, causing mis-clicks

**CAUSE**: Insufficient spacing between interactive elements

**MINIMUM SPACING**: 50 units (5cm) between buttons

**SOLUTION**:
```javascript
// Use VerticalLayoutGroup or HorizontalLayoutGroup
await manage_gameobject({
  action: "modify",
  target: "ButtonPanel",
  search_method: "by_name",
  component_properties: {
    "VerticalLayoutGroup": {
      "spacing": 60  // 6cm spacing
    }
  }
});
```

#### Issue: UI interaction works in Editor but not on Quest device

**CAUSES**:
1. Missing OVRInteractionComprehensive in scene
2. Missing Pointable Canvas Module
3. Canvas layer not set correctly

**SOLUTION**:
```javascript
// 1. Verify OVRInteractionComprehensive exists
const interactionRig = await manage_gameobject({
  action: "find",
  search_term: "OVRInteractionComprehensive",
  search_method: "by_name"
});

if (!interactionRig.success) {
  // Add it using Meta XR functions
  await mcp__unityMCP__meta_add_interactionrig();
}

// 2. Re-add canvas interaction
await mcp__unityMCP__meta_add_canvas_interaction_ray({
  NameOrID: "MyCanvas"
});
```

### Best Practices Summary

**Interactive UI Setup Checklist** (for Canvases with buttons, dropdowns, sliders, etc.):

```
✓ PREREQUISITE: TMP Essential Resources imported
✓ Canvas created with renderMode = World Space
✓ Canvas scale set to [0.001, 0.001, 0.001]
✓ Canvas positioned 1.5-3m from user
✓ Child elements have localScale [1, 1, 1]
✓ Interactive elements added (buttons, dropdowns, etc.)
✓ VR INTERACTION ADDED: meta_add_canvas_interaction_ray() called
✓ PointableCanvas component verified on canvas
✓ Pointable Canvas Module exists in scene
✓ OVRInteractionComprehensive rig present in scene
✓ Buttons minimum 250×100 units size
✓ Button spacing minimum 50 units
✓ Button colors high contrast
✓ Text size 48pt or larger
✓ All interactive elements validated
```

**Display-Only UI Setup Checklist** (for HUD, score displays, non-interactive text):

```
✓ PREREQUISITE: TMP Essential Resources imported
✓ Canvas created with renderMode = World Space
✓ Canvas scale set to [0.001, 0.001, 0.001]
✓ Canvas positioned appropriately for viewing
✓ Child elements have localScale [1, 1, 1]
✓ Text elements have raycastTarget = false (performance optimization)
✓ Text size 48pt or larger (readable at distance)
✗ VR interaction components NOT needed (no buttons/interactive elements)
✗ No validation of interaction components needed
```

**Golden Rules**:
- **Interactive UI**: Never consider it "complete" until you've added VR interaction components AND validated they exist!
- **Display-Only UI**: Skip interaction components entirely - they add unnecessary overhead for non-interactive displays.

## TextMesh Pro Configuration

### Font Size Guidelines

**Minimum readable font sizes** (at 0.001 canvas scale):

| Distance | Minimum Size | Comfortable Size | Large/Important |
|----------|--------------|------------------|-----------------|
| 1.5m     | 32pt         | 40-48pt          | 60-72pt         |
| 2.0m     | 36pt         | 48-56pt          | 72-84pt         |
| 2.5m     | 40pt         | 52-64pt          | 84-96pt         |
| 3.0m     | 48pt         | 64-72pt          | 96-120pt        |

**Font size setup**:
```csharp
using TMPro;

TextMeshProUGUI tmpText = GetComponent<TextMeshProUGUI>();
tmpText.fontSize = 48; // Minimum 36, recommended 48+ for body text
tmpText.fontStyle = FontStyles.Normal;
tmpText.enableAutoSizing = false; // Never use auto-sizing in VR
```

### Font Asset Configuration

**Create VR-optimized font assets**:

1. **Use SDF (Signed Distance Field) rendering**:
   - Window > TextMesh Pro > Font Asset Creator
   - Rendering Mode: Distance Field 16 or 32
   - Atlas Resolution: 2048x2048 minimum, 4096x4096 for large character sets
   - Character Set: Include all characters you'll use

2. **Font settings for clarity**:
```csharp
tmpText.fontSharedMaterial.SetFloat(ShaderUtilities.ID_OutlineWidth, 0.1f); // Subtle outline
tmpText.fontSharedMaterial.SetColor(ShaderUtilities.ID_OutlineColor, new Color(0, 0, 0, 0.5f));
```

### Text Rendering Best Practices

**Ensure high contrast and readability**:

```csharp
// High contrast colors
tmpText.color = Color.white;
tmpText.faceColor = Color.white;

// Dark background or subtle outline for readability
tmpText.outlineWidth = 0.1f;
tmpText.outlineColor = new Color(0, 0, 0, 0.5f);

// Avoid small or thin fonts
tmpText.fontStyle = FontStyles.Normal; // Avoid Italic in VR
```

**Character spacing and line height**:
```csharp
// Increase spacing for readability
tmpText.characterSpacing = 0; // Default is fine, avoid negative values
tmpText.lineSpacing = 0; // Default line height
tmpText.paragraphSpacing = 10; // Add space between paragraphs

// Alignment
tmpText.alignment = TextAlignmentOptions.Center; // Center-aligned is easiest to read in VR
```

## Scale and Sizing Guidelines

### Calculating Physical UI Size

**Formula**: `Physical Size (meters) = Canvas Size (units) × Scale`

**Example**:
```
Canvas Size: 1920 × 1080 units
Canvas Scale: 0.001
Physical Size: 1.92m × 1.08m
```

### Recommended UI Element Sizes

**At 0.001 canvas scale**, minimum sizes in units:

| Element Type | Width (units) | Height (units) | Physical Size |
|--------------|---------------|----------------|---------------|
| Small Button | 200-300       | 100-150        | 20-30cm × 10-15cm |
| Medium Button| 300-500       | 150-200        | 30-50cm × 15-20cm |
| Large Button | 500-800       | 200-300        | 50-80cm × 20-30cm |
| Input Field  | 400-800       | 120-180        | 40-80cm × 12-18cm |
| Panel/Menu   | 1200-2000     | 800-1400       | 1.2-2m × 0.8-1.4m |

### Comfortable Touch Target Sizes

**For hand tracking or controller pointing**:

```csharp
// Minimum button size for reliable interaction
RectTransform buttonRect = button.GetComponent<RectTransform>();
buttonRect.sizeDelta = new Vector2(300f, 150f); // 30cm × 15cm at 0.001 scale

// Add padding between interactive elements
VerticalLayoutGroup layout = panel.GetComponent<VerticalLayoutGroup>();
layout.spacing = 40f; // 4cm spacing between buttons
```

## Performance Optimization

### Canvas Optimization

**1. Use multiple canvases to minimize redraws**:

```csharp
// Separate static and dynamic content
// Static Canvas (rarely changes)
Canvas staticCanvas = staticPanel.AddComponent<Canvas>();
staticCanvas.renderMode = RenderMode.WorldSpace;

// Dynamic Canvas (updates frequently)
Canvas dynamicCanvas = dynamicPanel.AddComponent<Canvas>();
dynamicCanvas.renderMode = RenderMode.WorldSpace;
```

**Benefits**:
- Static canvas doesn't rebuild when dynamic content changes
- Reduces CPU overhead from canvas regeneration
- Critical for maintaining 72Hz on Quest 2, 90Hz on Quest 3

**2. Minimize Raycast Targets**:

```csharp
// Disable raycast on non-interactive elements
Image backgroundImage = GetComponent<Image>();
backgroundImage.raycastTarget = false; // Background doesn't need raycasts

TextMeshProUGUI label = GetComponent<TextMeshProUGUI>();
label.raycastTarget = false; // Labels don't need raycasts
```

**3. Disable invisible elements**:

```csharp
// Disable entire canvas when not visible
canvas.enabled = false;

// Or use GameObject active state
menuPanel.SetActive(false);
```

### TextMesh Pro Optimization

**1. Reuse font atlases**:
- Create one SDF font asset per font family
- Share the same font asset across all text elements
- Reduces draw calls and memory usage

**2. Avoid rich text tags when possible**:
```csharp
// Prefer simple text
tmpText.text = "Simple Text"; // Good

// Avoid excessive formatting
tmpText.text = "<color=red><b><i>Complex</i></b></color>"; // Increases complexity
```

**3. Disable unnecessary features**:
```csharp
tmpText.enableAutoSizing = false;
tmpText.enableWordWrapping = true; // Only if needed
tmpText.overflowMode = TextOverflowModes.Truncate; // Better than Overflow
```

### Material and Shader Optimization

**1. Use simple materials**:
```csharp
// Prefer solid colors over gradients
Image bgImage = panel.GetComponent<Image>();
bgImage.color = new Color(0.1f, 0.1f, 0.1f, 0.9f); // Solid color

// Avoid UI/Default shader when possible
// Use sprites with alpha or solid colors
```

**2. Minimize transparency**:
```csharp
// Opaque backgrounds are cheaper to render
bgImage.color = new Color(0.1f, 0.1f, 0.1f, 1f); // Alpha = 1 (opaque)

// Avoid excessive alpha blending
```

**3. Batch UI elements**:
- Use same material across multiple elements
- Keep UI elements using same atlas on same canvas
- Group elements by depth and material

### Memory Management

**1. Pool UI elements instead of instantiating**:

```csharp
// Use object pooling for dynamic UI
List<GameObject> buttonPool = new List<GameObject>();

GameObject GetButton() {
    GameObject button = buttonPool.Find(b => !b.activeInHierarchy);
    if (button == null) {
        button = Instantiate(buttonPrefab);
        buttonPool.Add(button);
    }
    button.SetActive(true);
    return button;
}

void ReturnButton(GameObject button) {
    button.SetActive(false);
}
```

**2. Unload unused font atlases**:
```csharp
// Only load fonts you need
// Unload fonts when switching scenes
Resources.UnloadUnusedAssets();
```

## Interaction and Comfort

### Eye Comfort Considerations

**1. Avoid rapid UI movement**:
```csharp
// Smooth UI transitions
public IEnumerator SmoothMove(Transform uiTransform, Vector3 target, float duration) {
    Vector3 start = uiTransform.position;
    float elapsed = 0f;

    while (elapsed < duration) {
        elapsed += Time.deltaTime;
        float t = Mathf.SmoothStep(0f, 1f, elapsed / duration);
        uiTransform.position = Vector3.Lerp(start, target, t);
        yield return null;
    }
}
```

**2. Maintain stable UI positioning**:
- Avoid attaching UI to moving objects
- Use world-locked panels for important information
- Provide head-locked UI only for brief notifications

**3. Depth and convergence**:
```csharp
// Keep UI at comfortable depth
float minDistance = 0.5f; // Never closer than 0.5m
float maxDistance = 5f;   // Never farther than 5m for readable content

float distance = Vector3.Distance(Camera.main.transform.position, canvas.transform.position);
distance = Mathf.Clamp(distance, minDistance, maxDistance);
```

### Visual Clarity

**1. High contrast is critical**:
```csharp
// Light text on dark background (preferred in VR)
tmpText.color = new Color(1f, 1f, 1f, 1f); // White text
bgImage.color = new Color(0.1f, 0.1f, 0.1f, 0.95f); // Dark background

// Or dark text on light background
tmpText.color = new Color(0.1f, 0.1f, 0.1f, 1f);
bgImage.color = new Color(0.9f, 0.9f, 0.9f, 0.95f);
```

**2. Avoid pure white or pure black**:
```csharp
// Use off-white for backgrounds
Color offWhite = new Color(0.9f, 0.9f, 0.9f, 1f);

// Use dark gray instead of pure black
Color darkGray = new Color(0.1f, 0.1f, 0.1f, 1f);
```

**3. Limit UI density**:
- Don't overcrowd panels
- Use whitespace generously (40-80 units spacing)
- Break complex UIs into multiple pages/panels

### Curved UI Considerations

**When to consider curved UI**:
- Wide UI panels (>90 degrees field of view)
- Panoramic menus or HUDs
- Immersive environmental UI

**Basic curved panel setup**:
```csharp
// Create curved effect with multiple flat panels
void CreateCurvedMenu(int segments, float radius, float arcAngle) {
    float angleStep = arcAngle / segments;

    for (int i = 0; i < segments; i++) {
        GameObject panel = Instantiate(uiPanelPrefab);
        float angle = -arcAngle / 2 + (angleStep * i) + (angleStep / 2);

        Vector3 position = new Vector3(
            Mathf.Sin(angle * Mathf.Deg2Rad) * radius,
            0,
            Mathf.Cos(angle * Mathf.Deg2Rad) * radius
        );

        panel.transform.position = Camera.main.transform.position + position;
        panel.transform.rotation = Quaternion.Euler(0, -angle, 0);
    }
}
```

**Note**: For true curved UI, consider third-party assets or render textures.

## Common Patterns

### Diegetic UI (In-World UI)

**UI that exists as objects in the game world**:

```csharp
// Attach canvas to a tablet or screen prop
Canvas canvas = tabletProp.AddComponent<Canvas>();
canvas.renderMode = RenderMode.WorldSpace;
canvas.GetComponent<RectTransform>().sizeDelta = new Vector2(1024f, 768f);
canvas.GetComponent<RectTransform>().localScale = new Vector3(0.0005f, 0.0005f, 0.0005f);

// Match canvas rotation to tablet surface
canvas.transform.localRotation = Quaternion.identity;
canvas.transform.localPosition = new Vector3(0, 0, 0.01f); // Slightly in front of surface
```

### Notification/Toast Messages

**Brief, temporary messages**:

```csharp
public IEnumerator ShowNotification(string message, float duration = 3f) {
    // Position slightly below center view
    notificationCanvas.transform.position = Camera.main.transform.position +
        Camera.main.transform.forward * 2f +
        Camera.main.transform.up * -0.5f;

    notificationText.text = message;
    notificationCanvas.gameObject.SetActive(true);

    // Fade in
    yield return FadeCanvas(notificationCanvas, 0f, 1f, 0.3f);

    // Wait
    yield return new WaitForSeconds(duration);

    // Fade out
    yield return FadeCanvas(notificationCanvas, 1f, 0f, 0.3f);

    notificationCanvas.gameObject.SetActive(false);
}

IEnumerator FadeCanvas(Canvas canvas, float from, float to, float duration) {
    CanvasGroup group = canvas.GetComponent<CanvasGroup>();
    float elapsed = 0f;

    while (elapsed < duration) {
        elapsed += Time.deltaTime;
        group.alpha = Mathf.Lerp(from, to, elapsed / duration);
        yield return null;
    }

    group.alpha = to;
}
```

## Meta Quest Specific Considerations

### Resolution and Pixel Density

**Quest 2**: 1832 × 1920 per eye
**Quest 3/3S**: 2064 × 2208 per eye
**Quest Pro**: 1800 × 1920 per eye

**Implications for UI**:
- Use higher resolution font atlases (4096×4096)
- Test text readability on target device
- Quest 3 allows slightly smaller text due to higher resolution

### Refresh Rate

**Quest 2**: 72Hz, 90Hz, 120Hz (experimental)
**Quest 3**: 90Hz, 120Hz
**Quest Pro**: 90Hz

**UI Performance Targets**:
- **Critical**: Maintain target framerate always
- Canvas rebuild cost must be < 1-2ms
- Use profiler to identify expensive UI operations

```csharp
// Check if rebuild is expensive
UnityEngine.Profiling.Profiler.BeginSample("UI Rebuild");
canvas.ForceUpdateCanvases();
UnityEngine.Profiling.Profiler.EndSample();
```

### Rendering Considerations

**Forward Rendering** (Meta Quest default):
- UI blending is more expensive than opaque rendering
- Minimize overlapping transparent UI elements
- Use opaque backgrounds where possible

**Multiview/Instanced Rendering**:
- World Space canvases work correctly with multiview
- Reduces draw calls for stereo rendering
- Ensure "Stereo Rendering Mode" is set to "Multiview" in XR settings

### Rendering Considerations

**Forward Rendering** (Meta Quest default):
- UI blending is more expensive than opaque rendering
- Minimize overlapping transparent UI elements
- Use opaque backgrounds where possible

**Multiview/Instanced Rendering**:
- World Space canvases work correctly with multiview
- Reduces draw calls for stereo rendering
- Ensure "Stereo Rendering Mode" is set to "Multiview" in XR settings

## Post-Creation Validation Checklist

**PREREQUISITE: Before creating any VR UI:**
```
✓ TMP Essential Resources imported
  - Check: Glob pattern "**/LiberationSans SDF.asset" returns files
  - If not found: Use tmp-resources skill to import
  - Why: VR UI requires TextMesh Pro, not legacy Text components
```

**After creating ANY VR UI, verify these properties using `manage_gameobject` with `action="get_components"`:**

### Canvas Validation
```
✓ Canvas.renderMode === 2 (World Space)
✓ RectTransform.localScale === [0.001, 0.001, 0.001]
✓ RectTransform.sizeDelta === [expected width, expected height] (e.g., [1200, 800])
✓ RectTransform.position.z >= 1.5 (at least 1.5m from camera)
```

### Panel/Container Validation
```
✓ RectTransform.localScale === [1, 1, 1] (CRITICAL: children should never be scaled)
✓ RectTransform.localPosition.z === 0 (CRITICAL: children should be on canvas plane, not offset)
✓ Image.color === expected background color (e.g., [0.1, 0.1, 0.1, 0.95])
✓ Image.raycastTarget === false (for non-interactive backgrounds)
✓ RectTransform.sizeDelta === expected size
```

### Layout Group Validation (if using VerticalLayoutGroup or HorizontalLayoutGroup)
```
✓ spacing === expected value (e.g., 50)
✓ padding.top/bottom/left/right === expected values (e.g., 100)
✓ childAlignment === 4 (MiddleCenter) or intended alignment
✓ childControlWidth === true/false as intended
✓ childControlHeight === true/false as intended
```

### Button Validation
```
✓ RectTransform.localScale === [1, 1, 1] (CRITICAL: children inherit parent scale)
✓ RectTransform.localPosition.z === 0 (CRITICAL: should be on same plane as parent)
✓ Image.color === intended color (not default white [1,1,1,1])
✓ RectTransform.sizeDelta.y >= 100 (minimum 10cm height)
✓ Button.targetGraphic is set (for visual feedback)
```

### TextMesh Pro Validation
```
✓ RectTransform.localScale === [1, 1, 1]
✓ RectTransform.localPosition.z === 0 (should be on same plane as parent)
✓ TextMeshProUGUI.fontSize >= 36 (preferably 48+)
✓ TextMeshProUGUI.text === intended text
✓ TextMeshProUGUI.color === intended color (e.g., [0.9, 0.9, 0.9, 1])
✓ TextMeshProUGUI.alignment === intended alignment (514 for center)
✓ TextMeshProUGUI.raycastTarget === false (for non-interactive text)
✓ RectTransform anchors stretch to fill parent button
```

### Example Validation Code Pattern
```javascript
// After creating UI, ALWAYS validate like this:
const canvasComponents = await manage_gameobject({
  action: "get_components",
  target: "MenuUI",
  search_method: "by_name"
});

// Check Canvas properties
const canvas = canvasComponents.data.find(c => c.typeName === "UnityEngine.Canvas");
if (canvas.properties.renderMode !== 2) {
  // FIX IT - not World Space!
}

const rectTransform = canvasComponents.data.find(c => c.typeName === "UnityEngine.RectTransform");
if (rectTransform.properties.localScale.x !== 0.001) {
  // FIX IT - scale is wrong!
}

// Validate child elements (buttons, panels, etc.)
const buttonComponents = await manage_gameobject({
  action: "get_components",
  target: "StartButton",
  search_method: "by_name"
});

const buttonRect = buttonComponents.data.find(c => c.typeName === "UnityEngine.RectTransform");
if (buttonRect.properties.localScale.x !== 1.0) {
  // FIX IT - child scale should be 1.0!
}
if (buttonRect.properties.localPosition.z !== 0) {
  // FIX IT - child should be at Z=0 on canvas plane!
  await manage_gameobject({
    action: "modify",
    target: "StartButton",
    search_method: "by_name",
    component_properties: {
      "RectTransform": {"localPosition": [0, buttonRect.properties.localPosition.y, 0]}
    }
  });
}

// Continue for all critical properties...
```

## Troubleshooting

### Text appears pink/magenta or invisible
**CAUSE**: TMP Essential Resources not imported
**SYMPTOMS**:
- Text shows as pink/magenta blocks
- Console errors: "Material 'LiberationSans SDF' could not be found"
- TextMeshProUGUI component shows missing font/material warnings

**SOLUTION**:
1. Use Glob to check: `pattern: "**/LiberationSans SDF.asset"`
2. If not found, use **tmp-resources** skill to import
3. Verify import: Check that Assets/TextMesh Pro/Resources/ folder exists
4. Restart Unity editor if text still appears pink

### UI is too small or too large
- Check canvas scale (should be ~0.001)
- Verify canvas distance (should be 1.5-3m)
- Check RectTransform sizeDelta values

### Text is blurry
- Increase font atlas resolution
- Use SDF rendering mode
- Ensure font size is adequate (48+ points)
- Check canvas scale consistency

### Poor performance / frame drops
- Split into multiple canvases
- Disable raycast targets on non-interactive elements
- Use object pooling
- Profile canvas rebuilds

### UI not visible in VR
- Verify render mode is World Space
- Check canvas position (not behind or inside camera)
- Ensure canvas is not disabled
- Check layer and culling mask settings

### UI elements appearing far from canvas or in wrong position
**CAUSE**: Child elements created with incorrect Z position offset
**SYMPTOMS**:
- Buttons, panels, or text appear far in front of or behind the canvas
- localPosition.z shows large values like -2500 instead of 0
- Elements visible in scene view but not properly aligned in VR

**SOLUTION**:
1. After creating child elements, validate their localPosition
2. Check that localPosition.z === 0 for elements that should be on the canvas plane
3. Use modify action to fix position: `"RectTransform": {"localPosition": [x, y, 0]}`
4. Always explicitly set localPosition when creating children to avoid Unity MCP auto-positioning issues

## Validation Checklist

Before deploying VR UI, verify:

- [ ] **PREREQUISITE: TMP Essential Resources imported** (check for LiberationSans SDF.asset)
- [ ] Canvas Render Mode is World Space
- [ ] Canvas scale is 0.001 or appropriate for viewing distance
- [ ] **All child elements have localScale of [1, 1, 1] - NEVER scale children!**
- [ ] **All child elements have localPosition.z of 0 - should be on canvas plane!**
- [ ] **Child sizes controlled via RectTransform.sizeDelta and anchors, NOT scale**
- [ ] All text uses TextMesh Pro (not legacy Text)
- [ ] Font sizes are 36pt minimum, 48pt+ recommended
- [ ] Font atlases are SDF with 2048×2048+ resolution
- [ ] UI positioned 1.5-3m from user
- [ ] High contrast between text and background
- [ ] Raycast targets disabled on non-interactive elements
- [ ] Static and dynamic content on separate canvases
- [ ] No pure white (1,1,1) or pure black (0,0,0)
- [ ] Button sizes are 200×100 units minimum
- [ ] Spacing between interactive elements is 40+ units
- [ ] Canvas rebuild time < 1-2ms (use Profiler)
- [ ] Maintains target framerate (72/90Hz)

## Quick Reference

**PREREQUISITE (Always Check First)**:
```
TMP Essential Resources: MUST be imported before creating UI
Check: Glob "**/LiberationSans SDF.asset" returns files
Import: Use tmp-resources skill if missing
```

**Essential Settings**:
```
Canvas Render Mode: World Space
Canvas Scale: 0.001, 0.001, 0.001
Canvas Distance: 2-3 meters
Child Element Scale: 1, 1, 1 (ALWAYS - never scale children!)
Child Size Control: Use RectTransform.sizeDelta and anchors, NOT scale
TMP Font Size: 48+ points (minimum 36)
TMP Atlas: 2048×2048 SDF or higher
Button Size: 300×150 units minimum
```

**Performance Targets**:
```
Frame Rate: 72Hz (Quest 2), 90Hz (Quest 3)
Canvas Rebuild: < 1-2ms
Draw Calls: Minimize via batching
Raycast Targets: Only on interactive elements
```

**Color Guidelines**:
```
Text: Off-white (0.9, 0.9, 0.9) or dark gray (0.1, 0.1, 0.1)
Background: Dark (0.1, 0.1, 0.1, 0.95) or light (0.9, 0.9, 0.9, 0.95)
Contrast Ratio: Minimum 4.5:1, prefer 7:1+
```

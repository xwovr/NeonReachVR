---
name: tmp-resources
description: Import and configure TextMesh Pro Essential Resources, Examples & Extras, and font assets in Unity. Use when setting up TextMesh Pro, creating UI with TMP, encountering missing TMP materials or fonts, or when TMP text appears pink/magenta. Covers TMP package import, resource installation, font asset creation, and troubleshooting common TMP setup issues.
---

# TextMesh Pro Resources Import

This skill provides comprehensive guidance for importing and setting up TextMesh Pro (TMP) resources in Unity projects, including Essential Resources, Examples & Extras, and custom font assets.

## Quick Start

**First-time TMP setup checklist**:
1. Install TextMesh Pro package (usually pre-installed in Unity 2018.1+)
2. Import TMP Essential Resources: Execute menu `Window/TextMeshPro/Import TMP Essential Resources`, then **manually click Import** in the Unity dialog
3. (Optional) Import Examples & Extras: Execute menu `Window/TextMeshPro/Import TMP Examples and Extras`, then **manually click Import** in the Unity dialog
4. Create font assets: `Window/TextMeshPro/Font Asset Creator`
5. Verify default materials exist in `Assets/TextMesh Pro/Resources/`

## When to Import TMP Resources

### TMP Essential Resources (REQUIRED)

**Import immediately when**:
- Creating your first TMP text element in a new project
- TMP text appears **pink/magenta** (missing material shader)
- Console shows errors: `"Material 'LiberationSans SDF' could not be found"`
- Creating UI with TextMeshProUGUI components
- Working with any TMP text in scenes

**What Essential Resources includes**:
- Default SDF font: **LiberationSans SDF**
- Essential shaders and materials
- Default sprite assets
- Core TMP resources folder structure

**Path after import**: `Assets/TextMesh Pro/Resources/`

### TMP Examples & Extras (OPTIONAL)

**Import when**:
- Learning TMP features for the first time
- Need reference examples for advanced TMP features
- Want sample scenes showing TMP capabilities
- Need example materials and prefabs

**What Examples & Extras includes**:
- 12+ example scenes demonstrating TMP features
- Sample fonts and font assets
- Example materials (outline, glow, etc.)
- Prefabs showing common TMP setups
- Sprite assets and example textures

**Path after import**: `Assets/TextMesh Pro/Examples & Extras/`

**Note**: Examples & Extras are NOT required for production. You can safely exclude this folder from builds.

## How to Import TMP Resources

### Method 1: Via Unity Menu (Recommended)

**IMPORTANT**: The import menu items open the Import Unity Package dialog window in the Unity Editor. This is a **manual step** that requires user action - the package will NOT import automatically.

**Import Essential Resources**:
```
1. Execute menu item: Window/TextMeshPro/Import TMP Essential Resources
   (Note: Forward slashes in path, not angle brackets)
2. Unity Editor will open "Import Unity Package" dialog window
3. **USER MUST**: Click "Import" button in the dialog window
4. Wait for import to complete (3-5 seconds)
5. Verify folder created: Assets/TextMesh Pro/Resources/
```

**Import Examples & Extras**:
```
1. Execute menu item: Window/TextMeshPro/Import TMP Examples and Extras
   (Note: Forward slashes in path, not angle brackets)
2. Unity Editor will open "Import Unity Package" dialog window
3. **USER MUST**: Click "Import" button in the dialog window
4. Wait for import to complete (10-15 seconds)
5. Verify folder created: Assets/TextMesh Pro/Examples & Extras/
```

**CRITICAL WORKFLOW**: When using Unity MCP to trigger import:
```
1. Call manage_menu_item with MenuPath: "Window/TextMeshPro/Import TMP Essential Resources"
2. STOP and notify user: "Import Unity Package dialog has opened in Unity Editor"
3. WAIT for user to confirm: "Please click Import in the dialog, then let me know when done"
4. DO NOT proceed until user confirms import is complete
5. After confirmation, verify import with Glob or list_resources
```

### Method 2: Automatic Import on First Use

When you create your first TMP object, Unity will prompt:

```
"This component requires the TMP Essential Resources.
Would you like to import them?"

[Import] [Cancel]
```

Click **"Import"** to automatically import essential resources.

### Method 3: Via Package Manager (Package Samples)

```
1. Window > Package Manager
2. Find "TextMesh Pro" in the list
3. Select TextMesh Pro
4. Under "Samples" section, click "Import" next to:
   - "TMP Essential Resources"
   - "TMP Examples & Extras"
```

## What Happens If Resources Aren't Imported

### Visual Symptoms

**Pink/Magenta text**:
```
Cause: Missing default TMP shader or material
Solution: Import TMP Essential Resources
```

**Invisible text**:
```
Cause: Missing font asset or material
Solution: Import Essential Resources, verify font asset assigned
```

**White boxes instead of text**:
```
Cause: Font atlas not generated or corrupted
Solution: Regenerate font asset via Font Asset Creator
```

### Console Errors

**Common error messages**:

```
Material 'LiberationSans SDF' could not be found.
→ Solution: Import TMP Essential Resources
```

```
The Font Atlas texture '[FontName] Atlas' cannot be found.
→ Solution: Regenerate font asset atlas
```

```
Unable to load TMP Settings. Please import the TMP Essential Resources.
→ Solution: Execute Window/TextMeshPro/Import TMP Essential Resources, then click Import in the Unity dialog
```

### Missing Components

Without Essential Resources:
- ❌ No default fonts available
- ❌ TMP Settings asset missing
- ❌ Default shaders not available
- ❌ Sprite assets unavailable
- ❌ Style sheets missing

With Essential Resources:
- ✅ LiberationSans SDF font ready to use
- ✅ TMP Settings configured
- ✅ All default shaders available
- ✅ Default sprite asset available
- ✅ Default style sheet available

## Creating Font Assets for UI

### When to Create Custom Font Assets

**Create custom font assets when**:
- You need to use a specific font (brand fonts, custom typefaces)
- Default LiberationSans doesn't match your design
- You need special characters not in the default font
- Working with non-Latin scripts (Arabic, Chinese, Japanese, etc.)
- Optimizing for VR (need specific character sets)

### Font Asset Creator Workflow

**Step 1: Prepare font file**
```
1. Obtain .ttf or .otf font file
2. Place in Assets/Fonts/ folder (or any Assets subfolder)
3. Select the font file in Project window
4. Verify it appears in Font Asset Creator
```

**Step 2: Open Font Asset Creator**
```
Window > TextMesh Pro > Font Asset Creator
```

**Step 3: Configure atlas settings**

**For UI text (recommended settings)**:
```
Source Font File: [Select your .ttf/.otf]
Font Size: Auto Sizing
Packing Method: Optimum
Atlas Resolution: 2048 x 2048 (or 4096 x 4096 for large character sets)
Character Set: ASCII (or custom character set)
Render Mode: Distance Field 16 (or Distance Field 32 for VR)
Get Kerning Pairs: ✓ (checked)
```

**Settings breakdown**:

| Setting | Recommended | Notes |
|---------|------------|-------|
| Font Size | Auto Sizing | Maximizes atlas usage |
| Packing Method | Optimum | Better packing, slower generation |
| Atlas Resolution | 2048×2048 | Standard for most fonts |
| | 4096×4096 | For large character sets or VR |
| | 1024×1024 | For minimal character sets only |
| Character Set | ASCII | English, numbers, common symbols |
| | Extended ASCII | Includes accented characters |
| | Unicode Range | For specific Unicode blocks |
| | Characters from File | Import character list from .txt |
| | Custom Characters | Paste specific characters needed |
| Render Mode | Distance Field 16 | Standard quality |
| | Distance Field 32 | Higher quality for VR/close-up text |
| | Raster | Not recommended (pixelated scaling) |

**Step 4: Generate font asset**
```
1. Click "Generate Font Atlas" button
2. Wait for generation (2-30 seconds depending on settings)
3. Preview the atlas texture in the window
4. Click "Save" or "Save as..."
5. Choose location: Assets/Fonts/ or Assets/TextMesh Pro/Fonts/
6. Name the asset: [FontName] SDF
```

**Step 5: Verify font asset**
```
1. Locate saved font asset in Project window
2. Check atlas texture is embedded
3. Assign to TMP text component:
   - Select TMP text GameObject
   - In Inspector, under "Font Asset", drag your new font asset
   - Text should update to use new font
```

### Character Set Selection

**ASCII (default)**:
```
Characters: A-Z, a-z, 0-9, basic punctuation
Size: ~100 characters
Atlas: 512×512 to 1024×1024
Use for: English-only text
```

**Extended ASCII**:
```
Characters: ASCII + accented characters (é, ñ, ü, etc.)
Size: ~256 characters
Atlas: 1024×1024
Use for: European languages
```

**Custom Characters**:
```
Example for game UI:
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?-:;'"

Use for: Minimal character set, optimized memory
```

**Unicode Range** (for non-Latin scripts):
```
Chinese (Simplified): U+4E00-9FFF
Japanese Hiragana: U+3040-309F
Japanese Katakana: U+30A0-30FF
Arabic: U+0600-06FF
Cyrillic: U+0400-04FF

Use for: Non-English languages
```

### VR-Specific Font Assets

**Recommended settings for Meta Quest VR UI**:
```
Atlas Resolution: 4096 x 4096
Render Mode: Distance Field 32
Font Size: Auto Sizing
Character Set: ASCII or Custom (minimal character set)
Padding: 5-7 (default)
```

**Why higher quality for VR**:
- Users can move close to text
- Need sharp rendering at various distances
- Higher pixel density displays (Quest 3)
- Avoid aliasing and artifacts

## Troubleshooting TMP Import Issues

### Issue: "Import TMP Essential Resources" option is grayed out

**Causes**:
- Resources already imported
- TMP package not installed

**Solutions**:
```
1. Check if folder exists: Assets/TextMesh Pro/Resources/
   → If exists, resources are already imported

2. Verify TMP package installed:
   Window > Package Manager > TextMesh Pro
   → Should show "Installed" or version number

3. If package missing:
   Package Manager > Unity Registry > TextMesh Pro > Install
```

### Issue: Font Asset Creator shows no fonts

**Causes**:
- No .ttf or .otf files in project
- Font files not recognized by Unity

**Solutions**:
```
1. Import a .ttf or .otf font file into Assets/
2. Select the font in Project window
3. Refresh Font Asset Creator window
4. Font should appear in "Source Font File" dropdown
```

### Issue: Generated font atlas is blank or corrupted

**Causes**:
- Font file corrupted
- Atlas resolution too small
- Character set too large for atlas

**Solutions**:
```
1. Increase Atlas Resolution:
   2048×2048 → 4096×4096

2. Reduce character set:
   Full Unicode → ASCII only

3. Try different font file:
   Some fonts don't generate SDF correctly

4. Regenerate font asset:
   Select font asset > Inspector > "Generate Font Atlas" button
```

### Issue: Text appears pink/magenta after importing resources

**Causes**:
- TMP Settings not configured correctly
- Shader compilation issue
- Material missing shader reference

**Solutions**:
```
1. Reimport TMP Essential Resources:
   Execute Window/TextMeshPro/Import TMP Essential Resources
   → Click Import in dialog, check "Replace existing files" if available

2. Force shader recompilation:
   Edit > Preferences > GI Cache > Clear Cache
   Assets > Reimport All

3. Verify TMP Settings:
   Edit > Project Settings > TextMesh Pro > Settings
   → Should show default font and material

4. Check material shader:
   Select TMP text > Inspector > Material
   → Shader should be "TextMeshPro/Distance Field"
```

### Issue: Missing characters showing as squares

**Causes**:
- Font asset doesn't include those characters
- Font atlas not generated with needed characters

**Solutions**:
```
1. Regenerate font asset with missing characters:
   - Open Font Asset Creator
   - Select your font asset
   - Add missing characters to character set
   - Click "Generate Font Atlas"
   - Save

2. Use fallback font:
   - Select TMP text component
   - Under "Font Asset" > "Fallback Font Assets"
   - Add LiberationSans SDF or other font with needed characters

3. For dynamic characters:
   - Enable "Dynamic Font Assets" (not recommended for VR)
   - Or create larger atlas with all possible characters
```

### Issue: Font looks blurry in VR

**Causes**:
- Atlas resolution too low
- Distance Field quality too low
- Font size too small

**Solutions**:
```
1. Regenerate with higher quality:
   Atlas Resolution: 4096×4096
   Render Mode: Distance Field 32

2. Increase font size in TMP component:
   Font Size: 48+ (for VR)

3. Ensure proper canvas scale:
   Canvas Scale: 0.001 (see meta-quest-ui skill)
```

## Best Practices for TMP Setup

### New Project Setup Workflow

**Step-by-step setup for new Unity VR project**:

```
1. Create new Unity project (or open existing)

2. Install TextMesh Pro package (if not already):
   Window > Package Manager > TextMesh Pro > Install

3. Import TMP Essential Resources:
   a. Execute menu: Window/TextMeshPro/Import TMP Essential Resources
   b. Click Import button in Unity's Import Package dialog
   c. Wait for import to complete

4. (Optional) Import Examples & Extras for learning:
   a. Execute menu: Window/TextMeshPro/Import TMP Examples and Extras
   b. Click Import button in Unity's Import Package dialog
   c. Wait for import to complete

5. Create custom font assets:
   - Import your .ttf fonts to Assets/Fonts/
   - Window/TextMeshPro/Font Asset Creator
   - Generate font assets (see "Creating Font Assets" section)

6. Configure TMP Settings (optional):
   Edit > Project Settings > TextMesh Pro > Settings
   - Set default font asset
   - Configure default material
   - Set default sprite asset

7. Create TMP text:
   GameObject > UI > Text - TextMeshPro
   - Assign custom font asset
   - Configure size, color, alignment

8. (For VR) Configure Canvas:
   - See meta-quest-ui skill for complete VR UI setup
```

### Font Asset Organization

**Recommended folder structure**:
```
Assets/
├── Fonts/
│   ├── SourceFonts/
│   │   ├── MyFont-Regular.ttf
│   │   ├── MyFont-Bold.ttf
│   │   └── MyFont-Italic.ttf
│   └── TMP FontAssets/
│       ├── MyFont-Regular SDF.asset
│       ├── MyFont-Bold SDF.asset
│       └── MyFont-Italic SDF.asset
└── TextMesh Pro/
    ├── Resources/ (Essential Resources)
    └── Examples & Extras/ (Optional, exclude from build)
```

### Font Asset Naming Convention

**Recommended naming**:
```
[FontName]-[Weight/Style] SDF

Examples:
- Roboto-Regular SDF
- Roboto-Bold SDF
- OpenSans-Light SDF
- Arial-Italic SDF
```

### Performance Considerations

**Atlas size vs. memory**:
```
512×512   = 0.5 MB  → Minimal character sets only
1024×1024 = 2 MB    → ASCII + some extras
2048×2048 = 8 MB    → Full ASCII + extended characters
4096×4096 = 32 MB   → Large character sets or VR
```

**Best practices**:
- Use smallest atlas that contains all needed characters
- Create separate font assets for different character sets (UI vs. subtitles)
- Don't include unused characters in atlas
- Reuse font assets across scenes
- Use fallback fonts instead of giant atlases

### Build Optimization

**Exclude Examples & Extras from build**:

```
1. Select folder: Assets/TextMesh Pro/Examples & Extras/
2. Inspector > Asset Labels > Add "EditorOnly" label

OR

1. Add to .gitignore:
   Assets/TextMesh Pro/Examples & Extras/

OR

1. Delete before building:
   Delete folder: Assets/TextMesh Pro/Examples & Extras/
   (Can reimport later if needed)
```

**Strip unused font assets**:
```
1. Audit font assets in use:
   - Search project for TMP components
   - Note which font assets are assigned

2. Delete unused font assets:
   - Remove font assets not referenced in scenes or prefabs
   - Unity will exclude from build automatically
```

## Quick Reference

### Essential Import Steps
```
1. Execute: Window/TextMeshPro/Import TMP Essential Resources
2. User must click Import button in Unity dialog that appears
3. Create font assets: Window/TextMeshPro/Font Asset Creator
4. Assign font assets to TMP text components
```

### Font Asset Creator Settings (VR Optimized)
```
Atlas Resolution: 4096×4096
Render Mode: Distance Field 32
Character Set: ASCII or Custom
Packing Method: Optimum
Get Kerning Pairs: ✓
```

### Common Paths
```
Essential Resources: Assets/TextMesh Pro/Resources/
Examples & Extras: Assets/TextMesh Pro/Examples & Extras/
Default Font: Assets/TextMesh Pro/Resources/Fonts & Materials/LiberationSans SDF.asset
TMP Settings: Edit > Project Settings > TextMesh Pro > Settings
```

### Troubleshooting Quick Fixes
```
Pink text → Import TMP Essential Resources
Blank atlas → Increase atlas resolution
Missing chars → Regenerate font with broader character set
Blurry in VR → Use Distance Field 32, 4096×4096 atlas
```

## Integration with meta-quest-ui Skill

This skill focuses on **importing and setting up TMP resources**. For complete VR UI configuration including canvas setup, scaling, and performance optimization, use the **meta-quest-ui** skill.

**Workflow**:
1. Use **tmp-resources** skill to import TMP and create font assets
2. Use **meta-quest-ui** skill to configure Canvas and TMP text for VR

**Example**:
```
1. Import TMP Essential Resources (this skill)
2. Create VR-optimized font asset at 4096×4096 (this skill)
3. Create World Space Canvas at 0.001 scale (meta-quest-ui skill)
4. Add TMP text with 48pt font size (meta-quest-ui skill)
5. Position Canvas 2m from user (meta-quest-ui skill)
```

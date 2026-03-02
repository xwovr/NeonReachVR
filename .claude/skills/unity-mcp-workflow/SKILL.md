---
name: unity-mcp-workflow
description: Follow Unity MCP best practices when working with Unity scripts, scenes, and editor operations. Use whenever modifying Unity scripts, creating GameObjects, changing scenes, or making editor changes. Ensures proper compilation checks, console verification, and visual validation through screenshots.
---

# Unity MCP Workflow

This Skill enforces essential best practices when working with Unity through the MCP server to prevent errors, ensure proper compilation, and verify changes visually.

## When to use this Skill

ALWAYS follow these rules when:
- Creating or modifying C# scripts in Unity
- Making changes to GameObjects or scenes
- Performing major editor operations
- Debugging Unity issues

## Core Rules

### Rule 1: Wait for Compilation After Script Changes

**After creating or modifying any C# script, ALWAYS:**

1. **Wait for Unity to compile** - Unity needs time to process script changes
2. **Check the console for compilation errors** using `read_console`:

```
manage_script → read_console (check for errors)
```

**Why this matters:**
- Script changes don't take effect until compilation completes
- Compilation errors will break subsequent operations
- Silent failures can cascade into confusing bugs

**Example workflow:**
```markdown
1. Create or edit script with manage_script
2. Call read_console with Types: ["Error"]
3. If errors exist: Fix them and repeat
4. If no errors: Proceed with next operation
```

### Rule 2: Use Screenshots to Verify Visual Results

**After making scene changes, ALWAYS capture a screenshot:**

Use `manage_scene` with `capture_game_view` to verify:
- Object placement and positioning
- Visual appearance and materials
- UI layout and scale
- Scene hierarchy changes

**Example:**
```markdown
1. Create GameObject or modify scene
2. Call manage_scene → capture_game_view
3. Verify the visual result matches expectations
4. If incorrect: Adjust and re-verify
```

**Why this matters:**
- Confirms changes applied correctly in the scene
- Catches visual bugs early (wrong position, scale, rotation)
- Validates UI setup for VR/AR applications
- Provides visual confirmation to user

### Rule 3: Check Console After Major Changes

**After major operations, ALWAYS check the console:**

Major operations include:
- Importing external models (FBX, textures)
- Adding components to GameObjects
- Creating or loading scenes
- Installing packages or assets
- Modifying project settings

**Use read_console to check for:**
- Errors (Type: "Error")
- Warnings (Type: "Warning")
- Import issues
- Missing dependencies

**Example:**
```markdown
1. Import FBX model with import_external_model
2. Call read_console with Types: ["Error", "Warning"]
3. Review output for issues
4. Resolve any warnings or errors
```

### Rule 4: Check Editor State Before Major Changes

**Before making significant changes, verify editor state:**

Use `manage_editor` with Action: "GetState" to check:
- Is the editor in Play mode? (Stop it first)
- What scene is active?
- What objects are selected?
- Is a prefab being edited?

**Example workflow:**
```markdown
1. Call manage_editor → GetState
2. If in Play mode: Stop playback first
3. If wrong scene active: Load correct scene
4. Proceed with changes
```

**Why this matters:**
- Changes in Play mode are lost when stopping
- Wrong scene edits can corrupt data
- Prefab editing mode has different rules
- Prevents accidental modifications

## Complete Workflow Example

Here's a complete workflow following all rules:

```markdown
Task: Create a new MonoBehaviour script and attach it to a GameObject

1. Check editor state first:
   manage_editor → GetState

2. Create the script:
   manage_script → create (name: "PlayerController", type: "MonoBehaviour")

3. Wait and check console:
   read_console → Types: ["Error"]
   (If errors: fix script and repeat)

4. Verify no errors, then attach to GameObject:
   manage_gameobject → add_component (target: "Player", component: "PlayerController")

5. Check console again:
   read_console → Types: ["Error", "Warning"]

6. Capture screenshot to verify:
   manage_scene → capture_game_view

7. Confirm visual result with user
```

## Best Practices

### Do:
- ✅ Always check console after script operations
- ✅ Wait for compilation before proceeding
- ✅ Use screenshots to validate visual changes
- ✅ Check editor state before major modifications
- ✅ Read console with specific Types filter (Error, Warning)
- ✅ Stop Play mode before making scene changes

### Don't:
- ❌ Skip console checks "to save time"
- ❌ Make multiple script changes without compilation checks
- ❌ Assume visual changes worked without screenshot verification
- ❌ Edit scenes while in Play mode
- ❌ Ignore warnings (they often indicate real issues)
- ❌ Chain operations without intermediate verification

## Common Pitfalls

**Pitfall 1: Script created but not compiled**
```
❌ create_script → add_component → ERROR (script not found)
✅ create_script → read_console → add_component
```

**Pitfall 2: Play mode edits lost**
```
❌ modify_gameobject while in Play mode → changes lost when stopped
✅ manage_editor GetState → Stop if playing → modify_gameobject
```

**Pitfall 3: Visual bugs not caught**
```
❌ import_external_model → assume it worked
✅ import_external_model → capture_game_view → verify placement
```

**Pitfall 4: Cascading errors**
```
❌ script error → add component → scene error → more errors
✅ script error → read_console → FIX error → verify → proceed
```

## Error Recovery

When compilation errors occur:

1. **Read the full error message:**
   ```
   read_console → Types: ["Error"], Format: "Detailed"
   ```

2. **Identify the file and line number**

3. **Fix the script:**
   ```
   read_resource → identify issue → apply_text_edits or manage_script
   ```

4. **Verify the fix:**
   ```
   read_console → Types: ["Error"]
   ```

5. **Only proceed when clean:**
   - No errors = safe to continue
   - Warnings = investigate before proceeding

## Quick Reference

| After this operation... | Always do this... |
|------------------------|-------------------|
| `create_script` | `read_console` (check errors) |
| `manage_script` (update) | `read_console` (check errors) |
| `import_external_model` | `read_console` + `capture_game_view` |
| `manage_gameobject` (create/modify) | `capture_game_view` |
| `manage_scene` (load/create) | `manage_editor GetState` + `capture_game_view` |
| `add_component` | `read_console` (check warnings) |
| Major changes | `read_console` + `capture_game_view` |

## Integration with Other Skills

This workflow skill complements:
- **unity-placement**: After placing objects, capture screenshot to verify
- **unity-fbx-import**: After import, check console and capture screenshot
- **meta-quest-ui**: After UI setup, verify with screenshot
- **tmp-resources**: After TMP import, check console for errors

## Summary

Following these four rules ensures reliable Unity MCP operations:

1. **Script changes** → Wait for compilation + Check console
2. **Scene changes** → Capture screenshot for verification
3. **Major operations** → Check console for errors/warnings
4. **Before changes** → Check editor state

**Remember:** Taking 5 seconds to check console/screenshot saves minutes of debugging mysterious issues.

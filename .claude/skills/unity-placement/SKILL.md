---
name: unity-placement
description: Ensures proper object placement in Unity using bounding boxes when objects are added, placed, moved, or positioned relative to other objects. Use when placing GameObjects, instantiating prefabs, moving objects relative to others, or positioning scene objects. Automatically calculates positions using Renderer and Collider bounds.
---

# Unity Object Placement with Bounding Boxes

This skill ensures that when placing, moving, or positioning Unity GameObjects relative to other objects, proper bounding box calculations are used to prevent overlaps and ensure accurate placement.

## When to use this skill

Use this skill automatically whenever:
- Placing an object relative to another (on top of, beside, above, below, in front of, behind)
- Moving objects to specific positions near other objects
- Instantiating prefabs in relation to existing scene objects
- Positioning imported models relative to scene objects
- Any spatial relationship between GameObjects is specified

## Automatic Triggers (invoke WITHOUT user asking)

**IMPORTANT**: Proactively invoke this skill immediately when you detect ANY of these patterns:

### Placement Language Triggers
- User says **"place X on Y"** or **"put X on Y"**
- User says **"place X next to Y"** or **"put X beside Y"**
- User says **"place X to the left/right of Y"**
- User says **"place X in front of/behind Y"**
- User says **"place X above/below Y"**
- User says **"position X near/around Y"**
- User says **"arrange X on/around Y"**
- User requests **"X meters/units to the left/right/front/back of Y"**

### Multi-Object Scenarios
- **Before ANY** GameObject position modification involving multiple objects and spatial relationships
- When importing models that will be positioned relative to existing objects
- When arranging/organizing multiple objects in a scene
- When setting up object hierarchies with spatial relationships

### Distance-Based Placement
- User specifies distances: "2 meters to the left", "0.5 units above", etc.
- Combine specified distance with bounding box calculations
- Example: "1 meter to the right" = `refMax.x + 1.0 + targetExtents.x`

## Example Scenarios

### ✅ Auto-Invoke Skill (Do These Immediately)

**Example 1**: "Place all objects on the tables"
- **Action**: Invoke unity-placement skill immediately
- **Why**: Multiple objects being placed relative to tables
- **Don't**: Manually set Y coordinates without bounds

**Example 2**: "Put the mug on the table"
- **Action**: Invoke unity-placement skill
- **Why**: Single object placement with "on" relationship
- **Don't**: Guess the table height

**Example 3**: "Place the lamp next to the clock"
- **Action**: Invoke unity-placement skill
- **Why**: "next to" indicates horizontal spatial relationship
- **Process**: Get both bounds, place lamp beside clock using `refMax.x + targetExtents.x`

**Example 4**: "Position the book 0.5 meters to the left of the pen"
- **Action**: Invoke unity-placement skill
- **Why**: Distance-based placement with spatial relationship
- **Process**: Get bounds, calculate: `penMin.x - 0.5 - bookExtents.x`

**Example 5**: "Put the sphere 2 units above the cube"
- **Action**: Invoke unity-placement skill
- **Why**: Vertical spacing with specified distance
- **Process**: Get bounds, calculate: `cubeMax.y + 2.0 + sphereExtents.y`

**Example 6**: "Arrange all decorations around the room"
- **Action**: Invoke unity-placement skill
- **Why**: Multiple object positioning with spatial relationships
- **Don't**: Use arbitrary coordinates

**Example 7**: "Place the chair in front of the desk"
- **Action**: Invoke unity-placement skill
- **Why**: Forward/back spatial relationship
- **Process**: Get bounds, calculate: `deskMax.z + chairExtents.z`

### ❌ Don't Invoke Skill (Direct Operations)

**Example 1**: "Move object to [5, 10, 3]"
- **Why**: Direct coordinates provided, no relative positioning

**Example 2**: "Set the cube's position to (0, 0, 0)"
- **Why**: Absolute position, no reference object

**Example 3**: "Translate the object by (1, 0, 0)"
- **Why**: Direct transform operation, not relative placement

## Core principle

**ALWAYS get bounding box information before calculating positions.**

Never assume object sizes - always retrieve actual bounds from Renderer or Collider components.

## Instructions

### Step 1: Identify the objects involved

When the user requests object placement:
1. Identify the **target object** (the one being placed/moved)
2. Identify the **reference object** (the one it's being placed relative to)
3. Note the desired **spatial relationship** (on, beside, above, etc.)

### Step 2: Get bounding box information

For BOTH objects, retrieve bounds using `manage_gameobject`:

```json
{
  "action": "get_components",
  "target": "ObjectName",
  "search_method": "by_name",
  "include_non_public_serialized": true
}
```

**Extract bounds from the component data:**
- Look for `MeshRenderer` component → `bounds` property → `center` and `size`
- If no MeshRenderer, look for `Collider` components (BoxCollider, SphereCollider, etc.) → `bounds`
- Store both `center` (local offset) and `size` (dimensions in world units)

**Important**: Bounds are in local space. Account for the object's current position when calculating.

### Step 3: Calculate world bounds

For each object, calculate world-space bounds:

```
worldCenter = position + bounds.center
worldMin = worldCenter - (bounds.size / 2)
worldMax = worldCenter + (bounds.size / 2)
```

Store these values:
- `worldCenter`: [x, y, z]
- `size`: [width, height, depth]
- `extents`: [width/2, height/2, depth/2]

### Step 4: Calculate placement position

Based on the spatial relationship, calculate the target position:

**On top of** (object A on top of object B):
```
targetY = B.worldMax.y + A.extents.y
targetX = B.worldCenter.x
targetZ = B.worldCenter.z
newPosition = [targetX, targetY, targetZ]
```

**Beside** (object A beside object B, +X direction):
```
targetX = B.worldMax.x + A.extents.x
targetY = B.worldCenter.y
targetZ = B.worldCenter.z
newPosition = [targetX, targetY, targetZ]
```

**In front of** (object A in front of object B, +Z direction):
```
targetX = B.worldCenter.x
targetY = B.worldCenter.y
targetZ = B.worldMax.z + A.extents.z
newPosition = [targetX, targetY, targetZ]
```

**Above** (floating above, with gap):
```
gap = 0.5  // or specified distance
targetY = B.worldMax.y + gap + A.extents.y
targetX = B.worldCenter.x
targetZ = B.worldCenter.z
newPosition = [targetX, targetY, targetZ]
```

**Next to / Beside with distance** (object A next to object B, with specified gap):
```
gap = user_specified_distance  // e.g., 0.5 meters
// Right side (+X):
targetX = B.worldMax.x + gap + A.extents.x
// Left side (-X):
targetX = B.worldMin.x - gap - A.extents.x
targetY = B.worldCenter.y  // or B.worldMin.y + A.extents.y for ground level
targetZ = B.worldCenter.z
newPosition = [targetX, targetY, targetZ]
```

**X meters/units to the left/right/front/back**:
```
// "2 meters to the right of B"
targetX = B.worldMax.x + 2.0 + A.extents.x
targetY = B.worldCenter.y
targetZ = B.worldCenter.z

// "1.5 units to the left of B"
targetX = B.worldMin.x - 1.5 - A.extents.x
targetY = B.worldCenter.y
targetZ = B.worldCenter.z

// "0.5 meters in front of B"
targetX = B.worldCenter.x
targetY = B.worldCenter.y
targetZ = B.worldMax.z + 0.5 + A.extents.z

// "1 unit behind B"
targetX = B.worldCenter.x
targetY = B.worldCenter.y
targetZ = B.worldMin.z - 1.0 - A.extents.z
```

### Step 5: Apply the position

Use `manage_gameobject` to set the calculated position:

```json
{
  "action": "modify",
  "target": "TargetObject",
  "search_method": "by_name",
  "position": [x, y, z]
}
```

### Step 6: Verify placement

After placement, inform the user:
- The calculated position
- The bounds that were used
- Any adjustments made
- Suggest they check the Scene view

## Common placement patterns

### On top (stacking)
- Use reference object's top surface (worldMax.y)
- Add target object's half-height (extents.y)
- Align centers horizontally (X, Z match)

### Beside (horizontal adjacency)
- Use reference object's side surface (worldMax.x or worldMin.x)
- Add target object's half-width (extents.x)
- Align centers vertically (Y matches) and depth-wise (Z matches)

### In front / Behind
- Use reference object's front/back surface (worldMax.z or worldMin.z)
- Add target object's half-depth (extents.z)
- Align centers (X, Y match)

### At specific offset
- Start with reference object's center
- Add custom offset
- Still account for target object's extents to ensure proper grounding

## Best practices

1. **Always get fresh bounds**: Don't cache bounds - always retrieve before placement
2. **Account for scale**: Bounds already include object scale
3. **Consider rotation**: For rotated objects, bounds are axis-aligned bounding boxes (AABB)
4. **Handle missing renderers**: If no Renderer, check for Colliders; if neither, warn the user
5. **Explain calculations**: Show your work - tell the user what bounds were found and how position was calculated
6. **Use world positions**: All `manage_gameobject` position parameters are local positions, so calculate accordingly
7. **Handle prefabs**: When instantiating prefabs, get their bounds after instantiation

## Handling edge cases

### Object has no Renderer or Collider
- Warn the user that bounds cannot be determined
- Suggest adding a Collider or ask for manual dimensions
- Fall back to assuming zero size at object's pivot

### Multiple Renderers (parent with children)
- Use the parent's Renderer if available
- If parent has no Renderer, calculate combined bounds from children
- Note this to the user

### Irregular shapes
- Bounds are axis-aligned boxes (AABB)
- They may be larger than the visible mesh
- Note this might create gaps for rotated or irregular objects

### Very small or very large objects
- Verify bounds seem reasonable (size > 0)
- Warn if extents are extremely small (< 0.01) or large (> 100)

## Example workflow

User: "Place the Cube on top of the Sphere"

1. Get Sphere's components and extract bounds:
   - Size: [2, 2, 2], Position: [0, 1, 0]
   - World center: [0, 1, 0], Extents: [1, 1, 1]
   - World max Y: 2

2. Get Cube's components and extract bounds:
   - Size: [1, 1, 1], Current position: [5, 0, 0]
   - Extents: [0.5, 0.5, 0.5]

3. Calculate new position:
   - Target Y: 2 (Sphere top) + 0.5 (Cube half-height) = 2.5
   - Target X: 0 (Sphere center X)
   - Target Z: 0 (Sphere center Z)
   - New position: [0, 2.5, 0]

4. Apply position to Cube

5. Report: "Placed Cube on top of Sphere at position [0, 2.5, 0]. The Cube (size 1×1×1) sits on the Sphere's top surface (Y=2)."

## Quick reference

### Coordinate axes in Unity
- X: Right (+) / Left (-)
- Y: Up (+) / Down (-)
- Z: Forward (+) / Back (-)

### Common bounds properties
- `bounds.center`: Local offset from object pivot
- `bounds.size`: Full dimensions [width, height, depth]
- `bounds.extents`: Half dimensions (size / 2)
- `bounds.min`: Minimum corner (local)
- `bounds.max`: Maximum corner (local)

### Placement formulas
- **On top**: `refMax.y + targetExtents.y`
- **Below**: `refMin.y - targetExtents.y`
- **Right of**: `refMax.x + targetExtents.x`
- **Left of**: `refMin.x - targetExtents.x`
- **In front**: `refMax.z + targetExtents.z`
- **Behind**: `refMin.z - targetExtents.z`

### Distance-based placement formulas
- **X units to the right**: `refMax.x + distance + targetExtents.x`
- **X units to the left**: `refMin.x - distance - targetExtents.x`
- **X units in front**: `refMax.z + distance + targetExtents.z`
- **X units behind**: `refMin.z - distance - targetExtents.z`
- **X units above**: `refMax.y + distance + targetExtents.y`
- **X units below**: `refMin.y - distance - targetExtents.y`
- **Next to with gap**: `refMax.x + gap + targetExtents.x` (or use refMin.x for left side)

## Remember

The goal is to make object placement intuitive and accurate. Always:
1. ✅ Get actual bounds from components
2. ✅ Calculate world-space positions
3. ✅ Account for object extents (half-sizes)
4. ✅ Explain your calculations to the user
5. ❌ Never guess object sizes
6. ❌ Never place objects at arbitrary positions without bounds

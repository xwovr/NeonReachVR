using UnityEngine;

/// <summary>
/// Procedurally generates a flat ring (annulus) mesh.
/// Outer radius, inner radius, and segment count are all adjustable from the Inspector.
/// The mesh rebuilds immediately whenever a value changes in the editor.
/// </summary>
[ExecuteAlways]
[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class RingMeshGenerator : MonoBehaviour
{
    [Header("Ring Shape")]
    [SerializeField, Min(0.01f)] private float _outerRadius = 0.5f;
    [SerializeField, Min(0.01f)] private float _innerRadius = 0.35f;
    [SerializeField, Min(0.001f)] private float _depth = 0.1f;
    [SerializeField, Range(3, 128)] private int _segments = 32;

    private MeshFilter _meshFilter;

    private void Awake() => Rebuild();

    private void OnValidate()
    {
        _innerRadius = Mathf.Clamp(_innerRadius, 0.01f, _outerRadius - 0.01f);
#if UNITY_EDITOR
        UnityEditor.EditorApplication.delayCall += () => { if (this != null) Rebuild(); };
#endif
    }

private void Rebuild()
    {
        if (_meshFilter == null) _meshFilter = GetComponent<MeshFilter>();
        if (_meshFilter == null) return;

        var mesh = _meshFilter.sharedMesh;
        if (mesh == null || mesh.name != "ProceduralRing")
        {
            mesh = new Mesh { name = "ProceduralRing" };
            _meshFilter.sharedMesh = mesh;
        }
        else
        {
            mesh.Clear();
        }

        float half = _depth * 0.5f;
        int ring = _segments + 1;

        int totalVerts = 8 * ring;
        var verts = new Vector3[totalVerts];
        var norms = new Vector3[totalVerts];
        var uvs   = new Vector2[totalVerts];

        for (int i = 0; i <= _segments; i++)
        {
            float angle = i / (float)_segments * Mathf.PI * 2f;
            float co = Mathf.Cos(angle);
            float si = Mathf.Sin(angle);
            float u  = i / (float)_segments;
            Vector3 radialOut = new Vector3(co, si, 0f);

            // Front face (z = +half, normal +Z)
            verts[i]        = new Vector3(co * _outerRadius, si * _outerRadius, +half);
            verts[i + ring] = new Vector3(co * _innerRadius, si * _innerRadius, +half);
            norms[i] = norms[i + ring] = Vector3.forward;
            uvs[i]        = new Vector2(u, 1f);
            uvs[i + ring] = new Vector2(u, 0f);

            // Back face (z = -half, normal -Z)
            verts[i + 2*ring] = new Vector3(co * _outerRadius, si * _outerRadius, -half);
            verts[i + 3*ring] = new Vector3(co * _innerRadius, si * _innerRadius, -half);
            norms[i + 2*ring] = norms[i + 3*ring] = Vector3.back;
            uvs[i + 2*ring]   = new Vector2(u, 1f);
            uvs[i + 3*ring]   = new Vector2(u, 0f);

            // Outer wall (normal = radialOut)
            verts[i + 4*ring] = new Vector3(co * _outerRadius, si * _outerRadius, +half);
            verts[i + 5*ring] = new Vector3(co * _outerRadius, si * _outerRadius, -half);
            norms[i + 4*ring] = norms[i + 5*ring] = radialOut;
            uvs[i + 4*ring]   = new Vector2(u, 1f);
            uvs[i + 5*ring]   = new Vector2(u, 0f);

            // Inner wall (normal = -radialOut, faces the hole)
            verts[i + 6*ring] = new Vector3(co * _innerRadius, si * _innerRadius, +half);
            verts[i + 7*ring] = new Vector3(co * _innerRadius, si * _innerRadius, -half);
            norms[i + 6*ring] = norms[i + 7*ring] = -radialOut;
            uvs[i + 6*ring]   = new Vector2(u, 1f);
            uvs[i + 7*ring]   = new Vector2(u, 0f);
        }

        var tris = new int[_segments * 24];
        int ti = 0;

        for (int i = 0; i < _segments; i++)
        {
            // Front face (normal +Z)
            int fo0=i, fo1=i+1, fi0=i+ring, fi1=i+ring+1;
            tris[ti++]=fo0; tris[ti++]=fo1; tris[ti++]=fi1;
            tris[ti++]=fo0; tris[ti++]=fi1; tris[ti++]=fi0;

            // Back face (normal -Z, reversed winding)
            int bo0=i+2*ring, bo1=i+2*ring+1, bi0=i+3*ring, bi1=i+3*ring+1;
            tris[ti++]=bo0; tris[ti++]=bi1; tris[ti++]=bo1;
            tris[ti++]=bo0; tris[ti++]=bi0; tris[ti++]=bi1;

            // Outer wall (normal outward)
            int owf0=i+4*ring, owf1=i+4*ring+1, owb0=i+5*ring, owb1=i+5*ring+1;
            tris[ti++]=owf0; tris[ti++]=owb0; tris[ti++]=owb1;
            tris[ti++]=owf0; tris[ti++]=owb1; tris[ti++]=owf1;

            // Inner wall (normal inward, reversed winding)
            int iwf0=i+6*ring, iwf1=i+6*ring+1, iwb0=i+7*ring, iwb1=i+7*ring+1;
            tris[ti++]=iwf0; tris[ti++]=iwb1; tris[ti++]=iwb0;
            tris[ti++]=iwf0; tris[ti++]=iwf1; tris[ti++]=iwb1;
        }

        mesh.vertices  = verts;
        mesh.normals   = norms;
        mesh.uv        = uvs;
        mesh.triangles = tris;
        mesh.RecalculateBounds();
    }
}

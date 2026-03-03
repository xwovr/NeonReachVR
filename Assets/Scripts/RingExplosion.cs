using UnityEngine;

public class RingExplosion : MonoBehaviour
{
    [SerializeField] private int   _cubeCount      = 14;
    [SerializeField] [Range(1f, 50f)] private float _explosionForce = 6f;
    [SerializeField] private float _cubeSize       = 0.035f;
    [SerializeField] private float _lifetime       = 2f;
    [SerializeField] private Material _cubeMaterial;

    /// <summary>Spawns cube fragments and blasts them outward.</summary>
    public void Explode(Vector3 worldPosition)
    {
        for (int i = 0; i < _cubeCount; i++)
        {
            var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.transform.position   = worldPosition + Random.insideUnitSphere * 0.08f;
            cube.transform.rotation   = Random.rotation;
            cube.transform.localScale = Vector3.one * _cubeSize;

            if (_cubeMaterial != null)
                cube.GetComponent<Renderer>().sharedMaterial = _cubeMaterial;

            // Remove collider so cubes don't trigger score zones
            Destroy(cube.GetComponent<Collider>());

            var rb = cube.AddComponent<Rigidbody>();
            rb.useGravity     = true;
            rb.linearDamping  = 0.5f;
            rb.angularDamping = 0.2f;
            rb.AddForce(Random.onUnitSphere * _explosionForce, ForceMode.Impulse);
            rb.AddTorque(Random.insideUnitSphere * _explosionForce * 2f, ForceMode.Impulse);

            Destroy(cube, _lifetime);
        }
    }
}

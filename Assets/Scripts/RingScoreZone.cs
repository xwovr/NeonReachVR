using UnityEngine;

/// <summary>
/// Detects a ball passing through the ring hole using a circular radius check.
///
/// The BoxCollider acts as a broad-phase proximity sensor.
/// OnTriggerEnter then verifies the ball centre is within the circular
/// hole (not just the square bounding box) before registering a score.
/// </summary>
[RequireComponent(typeof(BoxCollider))]
public class RingScoreZone : MonoBehaviour
{
    [Tooltip("Inner radius of the ring hole. Match this to RingMeshGenerator._innerRadius.")]
    [SerializeField] private float _holeRadius = 0.35f;

    private RingBehavior _ring;

    private void Awake() => _ring = GetComponentInParent<RingBehavior>();

    private void OnTriggerEnter(Collider other)
    {
        if (!other.CompareTag("Ball")) return;
        if (IsInsideHole(other.transform.position))
            _ring?.RegisterScore();
    }

    // Projects the ball position onto the ring's local XY plane and checks
    // whether it falls inside the circular hole (not a square).
    private bool IsInsideHole(Vector3 worldPos)
    {
        Vector3 local = transform.InverseTransformPoint(worldPos);
        return new Vector2(local.x, local.y).magnitude <= _holeRadius;
    }
}

using UnityEngine;

[RequireComponent(typeof(BoxCollider))]
public class RingScoreZone : MonoBehaviour
{
    private RingBehavior _ring;
    private void Awake() => _ring = GetComponentInParent<RingBehavior>();

    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Ball"))
            _ring?.RegisterScore();
    }
}

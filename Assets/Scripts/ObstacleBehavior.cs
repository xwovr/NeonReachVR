using UnityEngine;

/// <summary>
/// Moves an obstacle toward the player. Decrements health if the player is hit.
/// Balls are ignored — only "Player"-tagged colliders trigger a health penalty.
/// </summary>
[RequireComponent(typeof(Rigidbody))]
public class ObstacleBehavior : MonoBehaviour
{
    [HideInInspector] public float MoveSpeed      = 2f;
    [HideInInspector] public float MissZThreshold = -2f;

    private bool      _done;
    private Rigidbody _rb;

    private void Awake() => _rb = GetComponent<Rigidbody>();

    private void OnEnable()
    {
        if (GameManager.Instance != null)
            GameManager.Instance.OnGameOver += OnGameOver;
    }

    private void OnDisable()
    {
        if (GameManager.Instance != null)
            GameManager.Instance.OnGameOver -= OnGameOver;
    }

    private void Update()
    {
        if (_done) return;

        Vector3 next = transform.position + Vector3.back * MoveSpeed * Time.deltaTime;
        if (_rb != null) _rb.MovePosition(next);
        else             transform.position = next;

        if (transform.position.z < MissZThreshold)
        {
            _done = true;
            Destroy(gameObject);
        }
    }

    private void OnTriggerEnter(Collider other)
    {
        if (_done || !other.CompareTag("Player")) return;
        _done = true;
        GameManager.Instance?.RegisterMissedRing();
        Destroy(gameObject);
    }

    private void OnGameOver(int _s, int _m) => Destroy(gameObject);
}

using UnityEngine;

public class RingBehavior : MonoBehaviour
{
    [HideInInspector] public float MoveSpeed        = 2f;
    [HideInInspector] public float MissZThreshold   = -0.5f;
    [HideInInspector] public bool  IsWeaving        = false;
    [HideInInspector] public float LateralAmplitude = 0.9f;
    [HideInInspector] public float LateralFrequency = 0.25f;
    [HideInInspector] public int   PointValue       = 1;
    [HideInInspector] public bool  IsRotating       = false;
    [HideInInspector] public float RotationSpeed    = 45f;

    private bool          _done;
    private Rigidbody     _rb;
    private RingExplosion _explosion;
    private float         _elapsedTime;
    private float         _startX;

    private void Awake()
    {
        _explosion = GetComponent<RingExplosion>();
        _rb = GetComponent<Rigidbody>();
    }

    private void Start() => _startX = transform.position.x;

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
        _elapsedTime += Time.deltaTime;

        Vector3 next = transform.position + Vector3.back * MoveSpeed * Time.deltaTime;
        if (IsWeaving)
            next.x = _startX + Mathf.Sin(_elapsedTime * LateralFrequency * Mathf.PI * 2f) * LateralAmplitude;

        if (_rb != null)
        {
            _rb.MovePosition(next);
            if (IsRotating)
                _rb.MoveRotation(_rb.rotation * Quaternion.Euler(0f, RotationSpeed * Time.deltaTime, 0f));
        }
        else
        {
            transform.position = next;
            if (IsRotating)
                transform.Rotate(0f, RotationSpeed * Time.deltaTime, 0f, Space.World);
        }

        if (transform.position.z < MissZThreshold)
        {
            _done = true;
            GameManager.Instance?.RegisterMissedRing();
            Destroy(gameObject);
        }
    }

    public void RegisterScore()
    {
        if (_done) return;
        _done = true;
        _explosion?.Explode(transform.position);
        GameManager.Instance?.AddScore(PointValue);
        Destroy(gameObject);
    }

    private void OnGameOver(int _s, int _m) => Destroy(gameObject);
}

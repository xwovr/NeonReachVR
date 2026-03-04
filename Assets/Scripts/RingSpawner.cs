using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RingSpawner : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private GameObject  _ringPrefab;
    [SerializeField] private Transform[] _spawnPoints;

    [Header("Weaving Ring")]
    [SerializeField] private GameObject _weavingRingPrefab;
    [Tooltip("Number of normal rings that spawn before one weaving ring appears.")]
    [SerializeField] private int   _waveSize         = 18;
    [SerializeField] private float _lateralAmplitude = 0.9f;
    [Tooltip("Oscillations per second (0.25 = one full sweep every 4 s).")]
    [SerializeField] private float _lateralFrequency = 0.25f;

    [Header("Rotating Ring")]
    [SerializeField] private GameObject _rotatingRingPrefab;
    [Tooltip("Chance (0-1) that any normal ring spawn is replaced by a RotatingRing.")]
    [SerializeField] [Range(0f, 1f)] private float _rotatingRingChance = 0.2f;
    [SerializeField] private float _rotationSpeed = 45f;

    [Header("Difficulty")]
    [SerializeField] private float _baseSpeed          = 1.5f;
    [SerializeField] private float _maxSpeed           = 5.5f;
    [SerializeField] private float _baseSpawnInterval  = 2.5f;
    [SerializeField] private float _minSpawnInterval   = 0.6f;
    [SerializeField] private float _rampDuration       = 90f;
    [SerializeField] private float _missZThreshold     = -0.5f;

    private float _gameTimer;
    private bool  _spawning;
    private int   _lastIndex = -1;
    private int   _spawnedInWave;

    private readonly List<GameObject> _activeRings = new();

    private void Start()
    {
        foreach (var p in FindObjectsByType<PreviewOnly>(FindObjectsSortMode.None))
            Destroy(p.gameObject);

        if (GameManager.Instance != null)
        {
            GameManager.Instance.OnGameOver    += HandleGameOver;
            GameManager.Instance.OnGameRestart += HandleGameRestart;
        }

        _spawning = true;
        StartCoroutine(SpawnLoop());
    }

    private void OnDestroy()
    {
        if (GameManager.Instance != null)
        {
            GameManager.Instance.OnGameOver    -= HandleGameOver;
            GameManager.Instance.OnGameRestart -= HandleGameRestart;
        }
    }

    private void Update()
    {
        if (_spawning) _gameTimer += Time.deltaTime;
    }

    private IEnumerator SpawnLoop()
    {
        while (_spawning)
        {
            SpawnRing();
            _spawnedInWave++;

            if (_spawnedInWave >= _waveSize)
            {
                _spawnedInWave = 0;
                yield return new WaitForSeconds(ComputeInterval());
                SpawnWeavingRing();
            }

            yield return new WaitForSeconds(ComputeInterval());
        }
    }

    private void SpawnRing()
    {
        if (_spawnPoints == null || _spawnPoints.Length == 0) return;
        int idx;
        do { idx = Random.Range(0, _spawnPoints.Length); }
        while (_spawnPoints.Length > 1 && idx == _lastIndex);
        _lastIndex = idx;

        bool spawnRotating = _rotatingRingPrefab != null
                          && Random.value < _rotatingRingChance;
        GameObject prefab = spawnRotating ? _rotatingRingPrefab : _ringPrefab;

        var ring = Instantiate(prefab, _spawnPoints[idx].position,
                               Quaternion.LookRotation(Vector3.back, Vector3.up));
        _activeRings.Add(ring);

        var rb = ring.GetComponent<RingBehavior>();
        if (rb != null)
        {
            rb.MoveSpeed      = ComputeSpeed();
            rb.MissZThreshold = _missZThreshold;
            if (spawnRotating)
            {
                rb.IsRotating    = true;
                rb.RotationSpeed = _rotationSpeed;
                rb.PointValue    = 10;

            }
        }
    }

    private void SpawnWeavingRing()
    {
        if (_weavingRingPrefab == null || _spawnPoints == null || _spawnPoints.Length == 0) return;

        int idx;
        do { idx = Random.Range(0, _spawnPoints.Length); }
        while (_spawnPoints.Length > 1 && idx == _lastIndex);
        _lastIndex = idx;

        var ring = Instantiate(_weavingRingPrefab, _spawnPoints[idx].position,
                               Quaternion.LookRotation(Vector3.back, Vector3.up));
        _activeRings.Add(ring);

        var rb = ring.GetComponent<RingBehavior>();
        if (rb != null)
        {
            rb.MoveSpeed        = ComputeSpeed();
            rb.MissZThreshold   = _missZThreshold;
            rb.IsWeaving        = true;
            rb.LateralAmplitude = _lateralAmplitude;
            rb.LateralFrequency = _lateralFrequency;
            rb.PointValue       = 3;
        }
    }

    private float Smoothstep() { float t = Mathf.Clamp01(_gameTimer / _rampDuration); return t * t * (3f - 2f * t); }
    private float ComputeSpeed()    => Mathf.Lerp(_baseSpeed, _maxSpeed, Smoothstep());
    private float ComputeInterval() => Mathf.Lerp(_baseSpawnInterval, _minSpawnInterval, Smoothstep());

    private void HandleGameOver(int _s, int _m)
    {
        _spawning = false;
        StopAllCoroutines();
        foreach (var r in _activeRings) if (r) Destroy(r);
        _activeRings.Clear();
    }

    private void HandleGameRestart()
    {
        foreach (var r in _activeRings) if (r) Destroy(r);
        _activeRings.Clear();
        _lastIndex     = -1;
        _spawnedInWave = 0;
        _gameTimer     = 0f;
        _spawning      = true;
        StartCoroutine(SpawnLoop());
    }
}

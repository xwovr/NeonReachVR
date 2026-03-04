using System.Collections;
using UnityEngine;

/// <summary>
/// Spawns obstacles at random left/center/right positions.
/// Speed and frequency ramp with the game timer (same curve as RingSpawner).
/// </summary>
public class ObstacleSpawner : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private GameObject _obstaclePrefab;

    [Header("Spawn positions (X)")]
    [SerializeField] private float _leftX   = -1f;
    [SerializeField] private float _centerX =  0f;
    [SerializeField] private float _rightX  =  1f;
    [SerializeField] private float _spawnZ  = 10f;
    [SerializeField] private float _spawnY  =  1.6f;

    [Header("Difficulty")]
    [SerializeField] private float _baseInterval  = 10f;
    [SerializeField] private float _minInterval   =  5f;
    [SerializeField] private float _baseSpeed     =  2f;
    [SerializeField] private float _maxSpeed      =  5f;
    [SerializeField] private float _rampDuration  = 90f;
    [SerializeField] private float _missZThreshold = -2f;

    private float _gameTimer;
    private bool  _spawning;
    private int   _lastXIndex = -1;

    private void Start()
    {
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

    private void Update() { if (_spawning) _gameTimer += Time.deltaTime; }

    private IEnumerator SpawnLoop()
    {
        yield return new WaitForSeconds(8f);   // let a few rings arrive first
        while (_spawning)
        {
            SpawnObstacle();
            yield return new WaitForSeconds(ComputeInterval());
        }
    }

    private void SpawnObstacle()
    {
        if (_obstaclePrefab == null) return;

        float[] xs = { _leftX, _centerX, _rightX };
        int idx;
        do { idx = Random.Range(0, xs.Length); }
        while (xs.Length > 1 && idx == _lastXIndex);
        _lastXIndex = idx;

        var pos = new Vector3(xs[idx], _spawnY, _spawnZ);
        var obj = Instantiate(_obstaclePrefab, pos, Quaternion.identity);
        var ob  = obj.GetComponent<ObstacleBehavior>();
        if (ob != null)
        {
            ob.MoveSpeed      = ComputeSpeed();
            ob.MissZThreshold = _missZThreshold;
        }
    }

    private float Smoothstep()
    {
        float t = Mathf.Clamp01(_gameTimer / _rampDuration);
        return t * t * (3f - 2f * t);
    }

    private float ComputeSpeed()    => Mathf.Lerp(_baseSpeed,    _maxSpeed,   Smoothstep());
    private float ComputeInterval() => Mathf.Lerp(_baseInterval, _minInterval, Smoothstep());

    private void HandleGameOver(int _s, int _m)
    {
        _spawning = false;
        StopAllCoroutines();
    }

    private void HandleGameRestart()
    {
        _gameTimer = 0f;
        _spawning  = true;
        StartCoroutine(SpawnLoop());
    }
}

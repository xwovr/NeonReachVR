using UnityEngine;

public class RingBehavior : MonoBehaviour
{
    [HideInInspector] public float MoveSpeed      = 2f;
    [HideInInspector] public float MissZThreshold = -0.5f;

    private bool _done;

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
        transform.position += Vector3.back * MoveSpeed * Time.deltaTime;
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
        GameManager.Instance?.AddScore();
        Destroy(gameObject);
    }

    private void OnGameOver(int _s, int _m) => Destroy(gameObject);
}

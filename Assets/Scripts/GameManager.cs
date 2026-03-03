using System;
using UnityEngine;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [SerializeField] private int _maxMissedRings = 10;

    public int  Score          { get; private set; }
    public int  MissedRings    { get; private set; }
    public bool IsGameOver     { get; private set; }
    public int  MaxMissedRings => _maxMissedRings;

    public event Action<int>      OnScoreChanged;   // new score
    public event Action<int, int> OnMissedChanged;  // (missedCount, maxMissed)
    public event Action<int, int> OnGameOver;       // (finalScore, missedCount)

    private void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
    }

    public void AddScore()
    {
        if (IsGameOver) return;
        Score++;
        OnScoreChanged?.Invoke(Score);
    }

    public void RegisterMissedRing()
    {
        if (IsGameOver) return;
        MissedRings++;
        OnMissedChanged?.Invoke(MissedRings, _maxMissedRings);
        if (MissedRings >= _maxMissedRings)
        {
            IsGameOver = true;
            OnGameOver?.Invoke(Score, MissedRings);
        }
    }
}

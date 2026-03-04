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
    public int  HighScore      { get; private set; }

    private const string HighScoreKey = "HighScore";

    public event Action<int>      OnScoreChanged;      // new score
    public event Action<int, int> OnMissedChanged;     // (missedCount, maxMissed)
    public event Action<int, int> OnGameOver;          // (finalScore, missedCount)
    public event Action           OnGameRestart;
    public event Action<int>      OnHighScoreChanged;  // new high score

    private void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
        HighScore = PlayerPrefs.GetInt(HighScoreKey, 0);
    }

public void AddScore(int points = 1)
    {
        if (IsGameOver) return;
        Score += points;
        OnScoreChanged?.Invoke(Score);
        if (Score > HighScore)
        {
            HighScore = Score;
            PlayerPrefs.SetInt(HighScoreKey, HighScore);
            PlayerPrefs.Save();
            OnHighScoreChanged?.Invoke(HighScore);
        }
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

    public void Restart()
    {
        Score       = 0;
        MissedRings = 0;
        IsGameOver  = false;
        OnScoreChanged?.Invoke(Score);
        OnMissedChanged?.Invoke(MissedRings, _maxMissedRings);
        OnGameRestart?.Invoke();
    }
}

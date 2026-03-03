using System.Collections;
using TMPro;
using UnityEngine;

public class GameUI : MonoBehaviour
{
    [Header("HUD — always visible")]
    [SerializeField] private TextMeshProUGUI _scoreText;
    [SerializeField] private TextMeshProUGUI _missedLiveText;

    [Header("Game Over Panel (initially inactive)")]
    [SerializeField] private GameObject      _gameOverPanel;
    [SerializeField] private TextMeshProUGUI _gameOverText;

    private Transform _playerEye;
    private Coroutine _countdownCoroutine;

    private void Start()
    {
        _gameOverPanel.SetActive(false);

        int max = GameManager.Instance?.MaxMissedRings ?? 10;
        RefreshScore(0);
        RefreshMissed(0, max);

        var rig = FindFirstObjectByType<OVRCameraRig>();
        if (rig) _playerEye = rig.centerEyeAnchor;

        if (GameManager.Instance != null)
        {
            GameManager.Instance.OnScoreChanged  += RefreshScore;
            GameManager.Instance.OnMissedChanged += RefreshMissed;
            GameManager.Instance.OnGameOver      += ShowGameOver;
            GameManager.Instance.OnGameRestart   += HideGameOver;
        }
    }

    private void OnDestroy()
    {
        if (GameManager.Instance != null)
        {
            GameManager.Instance.OnScoreChanged  -= RefreshScore;
            GameManager.Instance.OnMissedChanged -= RefreshMissed;
            GameManager.Instance.OnGameOver      -= ShowGameOver;
            GameManager.Instance.OnGameRestart   -= HideGameOver;
        }
    }

    private void LateUpdate()
    {
        if (_playerEye == null) return;
        Vector3 dir = _playerEye.position - transform.position;
        if (dir.sqrMagnitude > 0.001f)
            transform.rotation = Quaternion.LookRotation(-dir, Vector3.up);
    }

    private void RefreshScore(int score)
        => _scoreText.text = $"SCORE\n<size=52>{score}</size>";

    private void RefreshMissed(int missed, int max)
        => _missedLiveText.text = $"MISSED  <color=#FF8C42>{missed}</color> / {max}";

    private void ShowGameOver(int finalScore, int missedCount)
    {
        _gameOverPanel.SetActive(true);
        if (_countdownCoroutine != null) StopCoroutine(_countdownCoroutine);
        _countdownCoroutine = StartCoroutine(GameOverCountdown(finalScore, missedCount));
    }

    private IEnumerator GameOverCountdown(int finalScore, int missedCount)
    {
        for (int t = 10; t > 0; t--)
        {
            _gameOverText.text = $"GAME OVER\n<size=26>Score: {finalScore}  |  Missed: {missedCount} / 10\nRestarting in {t}...</size>";
            yield return new WaitForSeconds(1f);
        }
        _countdownCoroutine = null;
        GameManager.Instance?.Restart();
    }

    private void HideGameOver()
    {
        if (_countdownCoroutine != null)
        {
            StopCoroutine(_countdownCoroutine);
            _countdownCoroutine = null;
        }
        _gameOverPanel.SetActive(false);
    }
}

using UnityEngine;

public class AudioManager : MonoBehaviour
{
    public static AudioManager Instance { get; private set; }

    [Header("Music")]
    [SerializeField] private AudioClip _backgroundMusic;
    [SerializeField] [Range(0f, 1f)] private float _musicVolume = 0.4f;

    [Header("SFX")]
    [SerializeField] private AudioClip _ringHitSFX;
    [SerializeField] private AudioClip _ballLaunchSFX;
    [SerializeField] private AudioClip _missSFX;
    [SerializeField] [Range(0f, 1f)] private float _sfxVolume   = 1f;

    private AudioSource _musicSource;
    private AudioSource _sfxSource;

    private void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;

        // Music source — looping, 2D
        _musicSource             = gameObject.AddComponent<AudioSource>();
        _musicSource.clip        = _backgroundMusic;
        _musicSource.loop        = true;
        _musicSource.volume      = _musicVolume;
        _musicSource.spatialBlend = 0f;
        _musicSource.playOnAwake = false;

        // SFX source — one-shot, 2D
        _sfxSource               = gameObject.AddComponent<AudioSource>();
        _sfxSource.spatialBlend  = 0f;
        _sfxSource.playOnAwake   = false;
    }

    private void Start()
    {
        if (_backgroundMusic != null)
            _musicSource.Play();

        if (GameManager.Instance != null)
        {
            GameManager.Instance.OnScoreChanged  += OnScoreChanged;
            GameManager.Instance.OnMissedChanged += OnMissedChanged;
        }
    }

    private void OnDestroy()
    {
        if (GameManager.Instance != null)
        {
            GameManager.Instance.OnScoreChanged  -= OnScoreChanged;
            GameManager.Instance.OnMissedChanged -= OnMissedChanged;
        }
    }

    public void PlayLaunchSFX()
    {
        if (_ballLaunchSFX != null)
            _sfxSource.PlayOneShot(_ballLaunchSFX, _sfxVolume);
    }

    private void OnMissedChanged(int missed, int max)
    {
        if (_missSFX != null)
            _sfxSource.PlayOneShot(_missSFX, _sfxVolume);
    }

    private void OnScoreChanged(int _)
    {
        if (_ringHitSFX != null)
            _sfxSource.PlayOneShot(_ringHitSFX, _sfxVolume);
    }
}

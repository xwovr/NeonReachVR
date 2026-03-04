using System.Collections;
using UnityEngine;

/// <summary>
/// Animates _GridSize and _GridColor on all child Renderers of the Enclosure
/// whenever the player misses a ring. Uses MaterialPropertyBlock so the
/// shared material asset is never modified.
/// </summary>
public class GridAnimator : MonoBehaviour
{
    [Tooltip("Grid size to flash down to on each miss.")]
    [SerializeField] private float _minGridSize    = 0.25f;
    [Tooltip("Color to flash to on each miss.")]
    [SerializeField] private Color _missColor      = Color.red;
    [Tooltip("How fast the grid shrinks / color shifts to the miss state (seconds).")]
    [SerializeField] private float _shrinkDuration = 0.2f;
    [Tooltip("How fast the grid grows / color returns to baseline (seconds).")]
    [SerializeField] private float _growDuration   = 0.55f;

    private Renderer[]            _renderers;
    private MaterialPropertyBlock _block;

    private float _baseGridSize;
    private Color _baseGridColor;
    private float _currentGridSize;
    private Color _currentGridColor;
    private Coroutine _anim;

    private static readonly int GridSizeID  = Shader.PropertyToID("_GridSize");
    private static readonly int GridColorID = Shader.PropertyToID("_GridColor");

    private void Awake()
    {
        _renderers = GetComponentsInChildren<Renderer>();
        _block     = new MaterialPropertyBlock();

        if (_renderers.Length > 0)
        {
            var mat          = _renderers[0].sharedMaterial;
            _baseGridSize    = mat.GetFloat(GridSizeID);
            _baseGridColor   = mat.GetColor(GridColorID);
        }

        _currentGridSize  = _baseGridSize;
        _currentGridColor = _baseGridColor;
    }

    private void Start()
    {
        if (GameManager.Instance != null)
            GameManager.Instance.OnMissedChanged += OnMissed;
    }

    private void OnDestroy()
    {
        if (GameManager.Instance != null)
            GameManager.Instance.OnMissedChanged -= OnMissed;
    }

    private void OnMissed(int missed, int max)
    {
        if (_anim != null) StopCoroutine(_anim);
        _anim = StartCoroutine(AnimateMiss());
    }

    private IEnumerator AnimateMiss()
    {
        yield return Tween(_currentGridSize, _minGridSize,
                           _currentGridColor, _missColor,
                           _shrinkDuration);

        yield return Tween(_minGridSize, _baseGridSize,
                           _missColor, _baseGridColor,
                           _growDuration);
    }

    private IEnumerator Tween(float sizeFrom, float sizeTo,
                              Color colorFrom, Color colorTo,
                              float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.SmoothStep(0f, 1f, elapsed / duration);
            _currentGridSize  = Mathf.Lerp(sizeFrom, sizeTo, t);
            _currentGridColor = Color.Lerp(colorFrom, colorTo, t);
            Apply(_currentGridSize, _currentGridColor);
            yield return null;
        }
        _currentGridSize  = sizeTo;
        _currentGridColor = colorTo;
        Apply(sizeTo, colorTo);
    }

    private void Apply(float size, Color color)
    {
        _block.SetFloat(GridSizeID,  size);
        _block.SetColor(GridColorID, color);
        foreach (var r in _renderers)
            r.SetPropertyBlock(_block);
    }
}

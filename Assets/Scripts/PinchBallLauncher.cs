using UnityEngine;
using Oculus.Interaction.Input;

/// <summary>
/// Pinch to hold a ball. Swing your hand from the pinch origin — a line renderer
/// traces that swing vector, and the ball launches in the direction of that line
/// when you release. A ribbon trail follows the ball (shows the swing gesture while
/// held, then the throw arc after release).
/// Add one instance per hand (set Handedness to Left or Right).
/// </summary>
public class PinchBallLauncher : MonoBehaviour
{
    [Header("Hand")]
    [Tooltip("Which hand this launcher belongs to.")]
    [SerializeField] private Handedness _handedness = Handedness.Left;

    [Header("Ball")]
    [SerializeField] private GameObject _ballPrefab;
    [SerializeField] private float      _ballScale = 0.04f;
    [SerializeField] private Material   _ballTrailMaterial; // assign BallTrail.mat

    [Header("Launch")]
    [SerializeField] private float _launchMultiplier    = 20f;
    [SerializeField] private float _maxPullDistance     = 0.35f;
    [Tooltip("Pinch strength required to START holding a ball.")]
    [SerializeField] [Range(0f, 1f)] private float _pinchThreshold        = 0.85f;
    [Tooltip("Pinch strength must drop BELOW this to release.")]
    [SerializeField] [Range(0f, 1f)] private float _pinchReleaseThreshold = 0.5f;

    [Header("Aim Line")]
    [SerializeField] private LineRenderer _aimLine; // assign the LineRenderer on this GameObject

    // Runtime refs (auto-found in Start)
    private IHand     _hand;
    private Transform _centerEyeAnchor;

    // State
    private GameObject   _activeBall;
    private Material     _activeMaterial;
    private TrailRenderer _activeTrail;
    private Vector3      _pinchOrigin;
    private Vector3      _aimDirection;
    private bool         _wasPinching;

    // -----------------------------------------------------------------------
    private void Start()
    {
        // Prefer the Hand on the parent (launcher is a child of LeftInteractions / RightInteractions)
        _hand = GetComponentInParent<IHand>();

        // Fallback: search the whole scene filtered by handedness
        if (_hand == null)
        {
            foreach (var h in FindObjectsByType<Hand>(FindObjectsSortMode.None))
            {
                if (h.Handedness == _handedness) { _hand = h as IHand; break; }
            }
        }

        var rig = FindFirstObjectByType<OVRCameraRig>();
        if (rig != null) _centerEyeAnchor = rig.centerEyeAnchor;

        if (_hand == null)
            Debug.LogWarning($"[PinchBallLauncher] No ISDK Hand found for handedness: {_handedness}");

        if (_aimLine == null)
            Debug.LogWarning($"[PinchBallLauncher] _aimLine (LineRenderer) is not assigned on {gameObject.name}!");
        else
            _aimLine.enabled = false;
    }

    // -----------------------------------------------------------------------
    private void Update()
    {
        if (_hand == null) return;

        // Reset stale state when tracking is lost mid-pinch
        if (!_hand.IsConnected || !_hand.IsTrackedDataValid)
        {
            if (_wasPinching)
            {
                if (_activeBall != null) { Destroy(_activeBall); _activeBall = null; _activeMaterial = null; _activeTrail = null; }
                if (_aimLine != null) _aimLine.enabled = false;
                _wasPinching = false;
            }
            return;
        }

        float pinchStrength = _hand.GetFingerPinchStrength(HandFinger.Index);

        // Hysteresis: once pinching, sustain until strength drops below release threshold
        bool isPinching = _wasPinching
            ? pinchStrength >= _pinchReleaseThreshold
            : pinchStrength >= _pinchThreshold;

        Vector3 pinchPos = GetPinchPosition();

        if (isPinching && !_wasPinching)
            OnPinchStart(pinchPos);
        else if (isPinching)
            OnPinchHold(pinchPos);
        else if (_wasPinching)
            OnPinchRelease(pinchPos);

        _wasPinching = isPinching;
    }

    // -----------------------------------------------------------------------
    private void OnPinchStart(Vector3 pinchPos)
    {
        if (_activeBall != null) Destroy(_activeBall);

        _pinchOrigin  = pinchPos;

        // Default aim = eye → pinch point; updated each frame in OnPinchHold
        _aimDirection = _centerEyeAnchor != null
            ? (pinchPos - _centerEyeAnchor.position).normalized
            : transform.forward;

        _activeBall = SpawnBall(pinchPos);
        SetChargeColor(0f);

        // Show aim line (zero-length at start — grows as hand moves)
        _aimLine.SetPosition(0, _pinchOrigin);
        _aimLine.SetPosition(1, _pinchOrigin);
        _aimLine.enabled = true;
    }

    private void OnPinchHold(Vector3 pinchPos)
    {
        if (_activeBall == null) return;

        // Line: from pulled-back hand → pinch origin (arrow points in launch direction)
        _aimLine.SetPosition(0, pinchPos);
        _aimLine.SetPosition(1, _pinchOrigin);

        // Aim = opposite of pull direction (slingshot: pull back → launch forward)
        Vector3 delta = pinchPos - _pinchOrigin;
        if (delta.sqrMagnitude > 0.0001f)
            _aimDirection = -delta.normalized;

        // Ball stays at hand position — trail traces the swing gesture
        _activeBall.transform.position = pinchPos;

        float t = ComputeCharge(pinchPos) / _maxPullDistance;
        _activeBall.transform.localScale = Vector3.one * Mathf.Lerp(_ballScale, _ballScale * 2f, t);
        SetChargeColor(t);
    }

    private void OnPinchRelease(Vector3 pinchPos)
    {
        if (_activeBall == null) return;

        _aimLine.enabled = false;

        float charge = ComputeCharge(pinchPos);
        var rb = _activeBall.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
            rb.isKinematic    = false;
            rb.useGravity     = true;
            rb.linearVelocity = _aimDirection * (charge * _launchMultiplier);
        }

        // Start the trail now that the ball is in flight
        if (_activeTrail != null) _activeTrail.emitting = true;

        Destroy(_activeBall, 5f);
        _activeBall     = null;
        _activeMaterial = null;
        _activeTrail    = null;
    }

    // -----------------------------------------------------------------------
    /// <summary>Charge = distance moved from pinch origin, clamped to max.</summary>
    private float ComputeCharge(Vector3 currentPos)
        => Mathf.Clamp((currentPos - _pinchOrigin).magnitude, 0f, _maxPullDistance);

    /// <summary>Returns the midpoint of thumb tip and index tip in world space.</summary>
    private Vector3 GetPinchPosition()
    {
        if (_hand.GetJointPose(HandJointId.HandThumbTip, out Pose thumbPose) &&
            _hand.GetJointPose(HandJointId.HandIndexTip, out Pose indexPose))
            return (thumbPose.position + indexPose.position) * 0.5f;

        if (_hand.GetPointerPose(out Pose pointerPose))
            return pointerPose.position;

        return transform.position;
    }

    private GameObject SpawnBall(Vector3 position)
    {
        if (_ballPrefab == null)
        {
            Debug.LogError("[PinchBallLauncher] _ballPrefab is not assigned!");
            return null;
        }

        var ball = Instantiate(_ballPrefab, position, Quaternion.identity);
        ball.transform.localScale = Vector3.one * _ballScale;

        // Per-instance material for charge colour tinting
        var rend = ball.GetComponent<Renderer>();
        if (rend != null)
            _activeMaterial = rend.material;

        // Start kinematic — physics enabled on release
        var rb = ball.GetComponent<Rigidbody>();
        if (rb != null) { rb.isKinematic = true; rb.useGravity = false; }

        _activeTrail = ball.GetComponent<TrailRenderer>();
        ConfigureTrail(_activeTrail);

        return ball;
    }

    private void ConfigureTrail(TrailRenderer trail)
    {
        if (trail == null) return;

        trail.emitting          = false;   // trail only starts after launch
        trail.time              = 0.55f;
        trail.startWidth        = 0.055f;  // wide ribbon matching reference images
        trail.endWidth          = 0.004f;  // tapers to thin at the tail
        trail.minVertexDistance = 0.004f;
        trail.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        trail.receiveShadows    = false;

        if (_ballTrailMaterial != null)
            trail.material = _ballTrailMaterial;

        // Bright yellow → orange → red-orange, fading to transparent at tail
        var gradient = new Gradient();
        gradient.SetKeys(
            new GradientColorKey[]
            {
                new GradientColorKey(new Color(1.0f, 0.95f, 0.25f), 0.00f), // bright yellow (ball end)
                new GradientColorKey(new Color(1.0f, 0.55f, 0.05f), 0.45f), // orange mid
                new GradientColorKey(new Color(1.0f, 0.15f, 0.00f), 1.00f), // red-orange tail
            },
            new GradientAlphaKey[]
            {
                new GradientAlphaKey(1.0f, 0.00f),
                new GradientAlphaKey(0.7f, 0.45f),
                new GradientAlphaKey(0.0f, 1.00f),
            }
        );
        trail.colorGradient = gradient;
    }

    /// <summary>Lerps CoreColor and RimColor from red (t=0) to green (t=1).</summary>
    private void SetChargeColor(float t)
    {
        if (_activeMaterial == null) return;
        Color c = Color.Lerp(Color.red, Color.green, t);
        _activeMaterial.SetColor("_CoreColor", c);
        _activeMaterial.SetColor("_RimColor",  c);
    }
}

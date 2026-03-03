using UnityEngine;
using Oculus.Interaction.Input;

/// <summary>
/// Detects a thumb-index pinch via ISDK Hand tracking, spawns a ball at the
/// pinch point, and keeps it attached while the user holds the pinch.
/// Pulling back (opposite the aim direction) charges launch power.
/// Releasing the pinch launches the ball; it auto-destroys after 5 seconds.
/// Add one instance per hand (set Handedness to Left or Right).
/// </summary>
public class PinchBallLauncher : MonoBehaviour
{
    [Header("Hand")]
    [Tooltip("Which hand this launcher belongs to. Used to auto-find the ISDK Hand component.")]
    [SerializeField] private Handedness _handedness = Handedness.Left;

    [Header("Ball")]
    [SerializeField] private GameObject _ballPrefab;
    [SerializeField] private float _ballScale = 0.04f;

    [Header("Launch")]
    [SerializeField] private float _launchMultiplier = 20f;
    [SerializeField] private float _maxPullDistance = 0.35f;
    [Tooltip("Pinch strength required to START holding a ball.")]
    [SerializeField] [Range(0f, 1f)] private float _pinchThreshold = 0.85f;
    [Tooltip("Pinch strength must drop BELOW this to release. Lower than _pinchThreshold to prevent jitter.")]
    [SerializeField] [Range(0f, 1f)] private float _pinchReleaseThreshold = 0.5f;

    [Header("Aiming")]
    [Tooltip("How much wrist rotation steers the aim. 1 = 1:1, 0.5 = half sensitivity.")]
    [SerializeField] [Range(0.1f, 2f)] private float _aimSensitivity = 1f;

    // Runtime refs (auto-found in Start)
    private IHand _hand;
    private Transform _centerEyeAnchor;

    // State
    private GameObject _activeBall;
    private Material   _activeMaterial;
    private Vector3    _pinchOrigin;
    private Vector3    _aimDirection;
    private Vector3    _initialAimDirection;      // locked at pinch-start
    private Quaternion _wristRotationAtPinchStart; // locked at pinch-start
    private Vector3    _chargeAxis;               // locked at pinch-start
    private bool _wasPinching;

private void Start()
    {
        // Prefer the Hand on the parent hierarchy — launcher is a child of LeftInteractions / RightInteractions
        _hand = GetComponentInParent<IHand>();

        // Fallback: search the whole scene filtered by handedness
        if (_hand == null)
        {
            foreach (var h in FindObjectsByType<Hand>(FindObjectsSortMode.None))
            {
                if (h.Handedness == _handedness)
                {
                    _hand = h as IHand;
                    break;
                }
            }
        }

        // Auto-find center eye anchor from OVRCameraRig
        var rig = FindFirstObjectByType<OVRCameraRig>();
        if (rig != null)
            _centerEyeAnchor = rig.centerEyeAnchor;

        if (_hand == null)
            Debug.LogWarning($"[PinchBallLauncher] No ISDK Hand found for handedness: {_handedness}");
    }

private void Update()
    {
        if (_hand == null) return;

        // Reset stale state when tracking is lost mid-pinch
        if (!_hand.IsConnected || !_hand.IsTrackedDataValid)
        {
            if (_wasPinching)
            {
                if (_activeBall != null) { Destroy(_activeBall); _activeBall = null; _activeMaterial = null; }
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

private void OnPinchStart(Vector3 pinchPos)
    {
        if (_activeBall != null)
            Destroy(_activeBall);

        _pinchOrigin = pinchPos;
        _initialAimDirection = _centerEyeAnchor != null
            ? (pinchPos - _centerEyeAnchor.position).normalized
            : transform.forward;

        _aimDirection = _initialAimDirection;
        _chargeAxis   = _initialAimDirection; // charge axis stays locked so pull-back feels consistent

        // Record wrist rotation as the rotation reference point
        _wristRotationAtPinchStart = _hand.GetJointPose(HandJointId.HandWristRoot, out Pose wristStart)
            ? wristStart.rotation
            : Quaternion.identity;

        _activeBall = SpawnBall(pinchPos);
        SetChargeColor(0f);
    }

private void OnPinchHold(Vector3 pinchPos)
    {
        if (_activeBall == null) return;

        // Rotate aim by however much the wrist has rotated since pinch-start
        if (_hand.GetJointPose(HandJointId.HandWristRoot, out Pose wristCurrent))
        {
            Quaternion delta = wristCurrent.rotation * Quaternion.Inverse(_wristRotationAtPinchStart);
            Quaternion scaledDelta = Quaternion.Slerp(Quaternion.identity, delta, _aimSensitivity);
            _aimDirection = (scaledDelta * _initialAimDirection).normalized;
        }

        _activeBall.transform.position = pinchPos;

        float t = ComputeCharge(pinchPos) / _maxPullDistance;
        _activeBall.transform.localScale = Vector3.one * Mathf.Lerp(_ballScale, _ballScale * 2f, t);
        SetChargeColor(t);
    }

private void OnPinchRelease(Vector3 pinchPos)
    {
        if (_activeBall == null) return;

        float charge = ComputeCharge(pinchPos);
        var rb = _activeBall.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.isKinematic = false;
            rb.useGravity = true;
            rb.linearVelocity = _aimDirection * (charge * _launchMultiplier);
        }

        Destroy(_activeBall, 5f);
        _activeBall   = null;
        _activeMaterial = null;
    }

    /// <summary>Charge = how far the hand has pulled back along the locked charge axis.</summary>
    private float ComputeCharge(Vector3 currentPos)
    {
        float pullBack = Vector3.Dot(_pinchOrigin - currentPos, _chargeAxis);
        return Mathf.Clamp(pullBack, 0f, _maxPullDistance);
    }

    /// <summary>Returns the midpoint of the thumb tip and index tip in world space.</summary>
    private Vector3 GetPinchPosition()
    {
        if (_hand.GetJointPose(HandJointId.HandThumbTip, out Pose thumbPose) &&
            _hand.GetJointPose(HandJointId.HandIndexTip, out Pose indexPose))
            return (thumbPose.position + indexPose.position) * 0.5f;

        // Fallback to pointer pose (the hand's aim ray origin)
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

        // Grab the shared material instance so we can tint it per-ball
        var rend = ball.GetComponent<Renderer>();
        if (rend != null)
            _activeMaterial = rend.material; // .material creates a per-instance copy

        // Start kinematic — physics enabled on release
        var rb = ball.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.isKinematic = true;
            rb.useGravity  = false;
        }

        return ball;
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

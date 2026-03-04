using UnityEngine;

/// <summary>
/// Follows the VR headset position so obstacles can detect player hits.
/// Attach to a GameObject with a BoxCollider tagged "Player".
/// </summary>
[RequireComponent(typeof(Rigidbody))]
[RequireComponent(typeof(BoxCollider))]
public class PlayerBody : MonoBehaviour
{
    private Transform _head;

    private void Start()
    {
        var rig = FindFirstObjectByType<OVRCameraRig>();
        if (rig != null) _head = rig.centerEyeAnchor;

        var rb        = GetComponent<Rigidbody>();
        rb.isKinematic = true;
        rb.useGravity  = false;
    }

    private void LateUpdate()
    {
        if (_head != null)
            transform.position = _head.position;
    }
}

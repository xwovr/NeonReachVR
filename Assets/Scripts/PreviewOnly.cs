using UnityEngine;
public class PreviewOnly : MonoBehaviour
{
    private void Awake() => Destroy(gameObject);
}

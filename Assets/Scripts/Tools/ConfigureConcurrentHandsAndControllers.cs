using UnityEngine;

public class ConfigureConcurrentHandsAndControllers : MonoBehaviour
{
    private void OnEnable()
    {
        if (OVRPlugin.SetSimultaneousHandsAndControllersEnabled(true))
        {
            Debug.Log("Concurrent hands and controllers mode succesfully set.");
        }
        else
        {
            Debug.LogWarning("Concurrent Hands and controllers not supported.");
        }
    }

    private void OnDisable()
    {
        if (OVRPlugin.SetSimultaneousHandsAndControllersEnabled(false))
        {
            Debug.Log("Concurrent hands and controllers mode succesfully unset.");
        }
        else
        {
            Debug.LogWarning("Concurrent Hands and controllers not supported.");
        }
    }

}

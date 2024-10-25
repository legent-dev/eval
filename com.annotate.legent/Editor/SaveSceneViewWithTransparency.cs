using UnityEditor;
using UnityEngine;
using System.IO;

public class SaveSceneViewWithTransparency : ScriptableObject
{
    [MenuItem("Custom/Save Scene View with Transparency")]
    static void SaveSceneView()
    {
        // Get the active SceneView or create a new one if none is open
        SceneView sceneView = SceneView.lastActiveSceneView;
        if (sceneView == null)
        {
            EditorUtility.DisplayDialog("Error", "No active Scene View found!", "OK");
            return;
        }

        // Set up the camera to render with a transparent background
        Camera sceneCamera = sceneView.camera;
        Color originalBackground = sceneCamera.backgroundColor;
        CameraClearFlags originalClearFlags = sceneCamera.clearFlags;
        sceneCamera.clearFlags = CameraClearFlags.SolidColor;
        sceneCamera.backgroundColor = Color.white;

        // Create a RenderTexture with alpha to capture transparent background
        RenderTexture activeRenderTexture = RenderTexture.active;
        RenderTexture sceneRT = new RenderTexture(sceneCamera.pixelWidth, sceneCamera.pixelHeight, 24);
        sceneRT.antiAliasing = 8;
        //// sceneRT.alpha = RenderTextureReadWrite.Linear;
        sceneCamera.targetTexture = sceneRT;

        // Render the scene to the texture
        Texture2D image = new Texture2D(sceneCamera.pixelWidth, sceneCamera.pixelHeight, TextureFormat.ARGB32, false);
        sceneCamera.Render();
        RenderTexture.active = sceneRT;
        image.ReadPixels(new Rect(0, 0, sceneCamera.pixelWidth, sceneCamera.pixelHeight), 0, 0);
        image.Apply();

        // Reset the camera settings and the active render texture
        sceneCamera.targetTexture = null;
        RenderTexture.active = activeRenderTexture;
        sceneCamera.clearFlags = originalClearFlags;
        sceneCamera.backgroundColor = originalBackground;
        DestroyImmediate(sceneRT);

        // Encode the texture into PNG
        byte[] bytes = image.EncodeToPNG();
        DestroyImmediate(image);

        // Save the PNG file
        string path = EditorUtility.SaveFilePanel("Save Scene View as PNG", "", "SceneViewTransparent.png", "png");
        if (!string.IsNullOrEmpty(path))
        {
            File.WriteAllBytes(path, bytes);
            Debug.Log("Saved Scene View with Transparency to " + path);
        }
    }
}
using System;
using Annotate.Unity.AI.Navigation.Samples.Editor;
using UnityEditor.SceneManagement;
using UnityEditor;
using UnityEngine;

namespace Annotate.Unity.AI.Navigation.Samples
{
    /// <summary>
    /// The Navigation samples use a couple of custom agent types.
    /// This class calls the NavigationSampleProjectSettingsGenerator to ensure that these agent types do exist within your Unity project.
    /// It is in no way necessary for using the Navigation package and is only used for the correct functioning of the samples.
    /// </summary>
    public class NavigationSampleInitializer : MonoBehaviour
    {
        [SerializeField]
        public static NavigationSampleSettingsState settingsState;

        [MenuItem("Custom/AINavigation/Create Agent Settings")]
        public static void CreateAgent()
        {
            settingsState = ScriptableObject.CreateInstance<NavigationSampleSettingsState>();
            settingsState.generated = true;
            NavigationSampleProjectSettingsGenerator.GenerateAllProjectSettings(settingsState);
        }
    }
}
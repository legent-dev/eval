using UnityEditor;
using UnityEngine;
using System.IO;
namespace Annotator
{
    [SerializeField]
    public class TaskInstanceSceneInfo
    {
        public string scene_name;
        public string scene_path;
    }
    public class JsonProcessor : MonoBehaviour
    {
        // 在Project视图中添加右键菜单项
        [MenuItem("Assets/打开标注场景和任务继续编辑", true)] // 这个true表示验证函数
        private static bool ValidateProcessJsonFile()
        {
            // 获取当前选中的文件路径
            string path = AssetDatabase.GetAssetPath(Selection.activeObject);
            // 检查文件后缀是否为 .json
            return Path.GetExtension(path).Equals(".json");
        }

        public static string GetGlbFilePath(string sceneName)
        {
            string sceneFullPath = "";
            string[] files = Directory.GetFiles(Application.dataPath, sceneName + ".glb", SearchOption.AllDirectories);
            if (files.Length > 0)
            {
                sceneFullPath = files[0].Replace("\\", "/");
            }
            return sceneFullPath;
        }

        // 菜单项点击时的处理函数
        [MenuItem("Assets/打开标注场景和任务继续编辑")]
        private static void ProcessJsonFile()
        {
            // 获取当前选中的文件路径
            string path = AssetDatabase.GetAssetPath(Selection.activeObject);

            // 读取JSON文件内容
            string jsonContent = File.ReadAllText(path);

            TaskInstanceSceneInfo sceneInfo = JsonUtility.FromJson<TaskInstanceSceneInfo>(jsonContent);
            Debug.Log(sceneInfo.scene_path);
            // 如果路径中有该文件，打开该fbx文件
            if (sceneInfo.scene_path != null)
            {
                Debug.Log("scene_path =" + sceneInfo.scene_path);
                string sceneFullPath = sceneInfo.scene_path;


                string sceneName = sceneInfo.scene_name;
                bool isExist = false;
                if (File.Exists(sceneFullPath)) isExist = true;
                else{
                    sceneFullPath = GetGlbFilePath(sceneName);
                    if (sceneFullPath != "") {
                        isExist = true;
                    }
                }
                
                if (isExist){
                    // 清空场景里所有物体，包括disable掉的
                    GameObject[] allObjects = GameObject.FindObjectsOfType<GameObject>();
                    foreach (GameObject obj in allObjects)
                    {
                        GameObject.DestroyImmediate(obj);
                    }
                    string scenePathInProject = sceneFullPath.Substring(sceneFullPath.IndexOf("Assets/"));
                    if (scenePathInProject != sceneFullPath)
                    {
                        // 用AssetDatabase实例化一个该glb文件，添加到场景中
                        GameObject sceneObject = AssetDatabase.LoadAssetAtPath<GameObject>(scenePathInProject);
                        if (sceneObject != null)
                        {
                            GameObject sceneGlb = GameObject.Instantiate(sceneObject);
                            sceneGlb.name = sceneName;
                            TaskLoader taskLoader = sceneGlb.AddComponent<TaskLoader>();
                            sceneGlb.AddComponent<TaskInstance>();
                            taskLoader.textFile = AssetDatabase.LoadAssetAtPath<TextAsset>(path);
                            taskLoader.LoadTask();
                        }
                    }
                }
                else
                {
                    Debug.Log("场景文件不存在");
                }
            }


        }
    }
}
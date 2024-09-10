
using UnityEngine;
using NaughtyAttributes;
namespace Annotator
{
    public class TaskLoader: MonoBehaviour{
        
        [Label("要加载的文件")]
        public TextAsset textFile;

        [Button("加载任务")]
        public void LoadTask(){
            if(gameObject.GetComponent<TaskInstance>() == null){
                gameObject.AddComponent<TaskInstance>();
            }
            TaskInstance taskInstance = gameObject.GetComponent<TaskInstance>();
            // taskInstance.OnValidate();
            taskInstance.Load(textFile.text);
            taskInstance.Refresh();
        }
    }

}
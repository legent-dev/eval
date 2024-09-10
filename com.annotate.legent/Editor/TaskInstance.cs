using System.Collections;
using System.Collections.Generic;
using Codice.Client.Commands;
using UnityEngine;
using UnityEditor;
using NaughtyAttributes;
using NaughtyAttributes.Editor;
using System.IO;
using System;
using UnityEngine.SceneManagement;

namespace Annotator
{
    [System.Serializable]

    public class Option
    {
        //[HideInInspector]
        // https://www.youtube.com/shorts/KFoyIUjrZ8A
        // 这是显示在Inspector中的元素名称
        //public string name="选项";

        [Label("选项类型"), AllowNesting]
        // 用AllowNesting才会显示嵌套
        // https://github.com/dbrizov/NaughtyAttributes/issues/91
        [Dropdown("optionTypes")]
        [OnValueChanged("OnOptionChanged")]
        public string option_type = "Answer-回答";
        // private List<string> optionTypes { get { return new List<string>() { "Answer", "PickUp", "PlaceTo", "OpenDrawer", "OpenDoor", "CloseDrawer", "CloseDoor" }; } }
        private List<string> optionTypes { get { return new List<string>() { "Answer-回答", "PickUp-拿起", "PlaceTo-放到", "OpenDrawer-开抽屉", "OpenDoor-开门", "CloseDrawer-关抽屉", "CloseDoor-关门" }; } }

        bool NeedObject(){
            return option_type != "Answer-回答";
        }
        public void OnOptionChanged()
        {
            Dictionary<string, string> saved2option = new Dictionary<string, string>(){
                {"Answer", "Answer-回答"},
                {"PickUp", "PickUp-拿起"},
                {"PlaceTo", "PlaceTo-放到"},
                {"OpenDrawer", "OpenDrawer-开抽屉"},
                {"CloseDrawer", "CloseDrawer-关抽屉"},
                {"OpenDoor", "OpenDoor-开门"},
                {"CloseDoor", "CloseDoor-关门"}
            };
            if(saved2option.ContainsKey(option_type)){
                option_type = saved2option[option_type];
            }
            Debug.Log("OnOptionChanged "+option_type);
            bool needObject = option_type != "Answer-回答";
            if (needObject)
            {
                if(option_text == null || option_text == ""){
                    string t = option_type.Split('-')[0];
                    if(t == "PickUp") option_text = "pick up the ";
                    else if(t == "PlaceTo") option_text = "place to the ";
                    else if(t == "OpenDrawer") option_text = "open the drawer of the";
                    else if(t == "CloseDrawer") option_text = "close the drawer of the";
                    else if(t == "OpenDoor") option_text = "open the door of the";
                    else if(t == "CloseDoor") option_text = "close the door of the";
                }
                if (gameObjects == null || gameObjects.list == null || gameObjects.list.Count == 0)
                {
                    gameObjects = new NestedArray<GameObject>();
                    gameObjects.list = new List<GameObject>();
                    gameObjects.list.Add(null);
                }
            }
        }


        [Label("选项文本"), AllowNesting]
        public string option_text;



        [Label("可操作对象"), AllowNesting, ShowIf("NeedObject")]
        //[HideNestedArray]
        // List<GameObject>不行，只有自己单独写一个类NestedArray进行嵌套
        public NestedArray<GameObject> gameObjects;

        [HideInInspector]
        public List<string> objects;


    }

    [System.Serializable]
    public class Predicate
    {

        [Label("判定类型"), AllowNesting]
        [Dropdown("predicateTypes")]
        [OnValueChanged("OnPredicateChanged")]
        public string predicate_type;


        [Label("正确回答"), AllowNesting, ShowIf("Need0Param")]
        public string right_answer_content;

        [Label("参数一"), AllowNesting, ShowIf("Need1Param")]
        //[NonSerialized]
        public GameObject targetObject;
        [HideInInspector]
        public string predicate_object;

        [Label("参数二"), AllowNesting, ShowIf("Need2Param")]
        //[NonSerialized]
        public GameObject targetPlace;
        [HideInInspector]
        public string predicate_place;

        bool Need0Param(){
            return predicate_type == "choose";
        }
        bool Need1Param(){
            bool need = predicate_type!="choose";
            if(!need) targetObject = null;
            return need;
        }
        bool Need2Param(){
            bool need = predicate_type != "choose" && !predicate_type.StartsWith("agent") && !predicate_type.StartsWith("grab");
            if(!need) targetPlace = null;
            return need;
        }


        private List<string> predicateTypes { get { return new List<string>() { "choose", "agent_at", "agent_near", "at", "near", "not_at", "agent_pass", "grab", "closer", "further"}; } }
        //  "in", "on", "near", "not in", "not on"

        public void OnPredicateChanged()
        {
            
            // needObject = option_type != "Answer";
            // if (needObject)
            // {
            //     if (gameObjects == null)
            //     {
            //         gameObjects = new NestedArray<GameObject>();
            //         gameObjects.list = new GameObject[0];
            //     }
            // }
        }

    }

    [System.Serializable]
    public class NestedArray<T>
    {
        public List<T> list;
    }

    [Serializable]
    public class SpecialPoint
    {
        public string name;
        public List<float> position;
        public string type; // "navigation" "navigation-target" "special"
    }

    [Serializable]
    [RequireComponent(typeof(TaskLoader))]
    public class TaskInstance : MonoBehaviour
    {
        [Label("场景"), ReadOnly]
        public string scene_name;
        [HideInInspector]
        public string scene_path;

        [HideInInspector]
        public List<float> scene_scale;
        [HideInInspector]
        public List<float> scene_position;

        [NonSerialized]
        GameObject _agent;
        GameObject agent{
            get{
                if(_agent == null){
                    if(GameObject.Find("Agent")==null) {
                        GameObject capsule = GameObject.CreatePrimitive(PrimitiveType.Cube);
                        capsule.transform.localScale = new Vector3(0.3f, 3f, 0.3f);
                        capsule.name = "Agent";
                        // Remove(capsule.GetComponent<Collider>());
                        capsule.transform.position = Vector3.zero; //Utils.GetBounds(gameObject).center;
                        capsule.transform.position = new Vector3(capsule.transform.position.x, 0, capsule.transform.position.z);
                        // add a capsule
                    }
                    _agent = GameObject.Find("Agent");
                }
                else {
                }


                return _agent;
            }
            set{
                _agent = value;
            }
        }

        [HideInInspector]
        public List<float> agent_position;
        [HideInInspector]
        public List<float> agent_rotation;

        [Label("地板")]
        public List<GameObject> floorObjects;
        [HideInInspector]
        public List<string> floor_objects;

        [Label("删除物体")]
        [OnValueChanged("OnRemoveObjects")]
        public List<GameObject> removedObjects;
        [HideInInspector]
        public List<string> removed_objects;
        public void OnRemoveObjects()
        {
            foreach (GameObject obj in removedObjects)
            {
                obj.SetActive(false);
            }
        }

        // show task_template as "任务文本" in spector
        [Label("任务模板")]
        [OnValueChanged("Refresh")]
        //[ValidateInput("TemplateExist", "请选择任务模板中存在的任务")]
        public string task_template="";
        public void Refresh()
        {
            Debug.Log("OnTemplateChanged");
            // 这里可以直接设置好选项和判定函数
            OnOptionsChanged();
        }
        public bool TemplateExist(string template){
            return TaskTemplates.task_templates.Contains(template);
        }


        [Label("任务文本")]
        public string task_text;

        [Label("行动选项")]
        [OnValueChanged("OnOptionsChanged")]
        public List<Option> options;

        private void OnOptionsChanged()
        {
            foreach (Option option in options)
            {
                option.OnOptionChanged();
            }
        }

        //[System.NonSerialized]
        [Label("判定条件")]
        public List<Predicate> predicates;

        
        [HideInInspector]
        public List<SpecialPoint> special_points;

        public void InitVariables(){
            floorObjects = new List<GameObject>();
            floorObjects.Add(null);
            removedObjects = new List<GameObject>();
            
            if(GameObject.Find("FPSController")!=null){ //AI2THOR的机器人
                GameObject obj = GameObject.Find("FPSController");
                removedObjects.Add(obj);
                obj.SetActive(false);
            }

        }
        // [Button("初始化场景变量")]

        private bool onValidateUseDestroy = false;
        public void Remove(GameObject obj)
        {
            onValidateUseDestroy = false;
            try{

            if(onValidateUseDestroy) Destroy(obj);
            else DestroyImmediate(obj);
            }
            catch(Exception e){
                Debug.Log("Remove Error");
                Debug.LogError(e);
            }
        }
        public void Remove(Collider obj)
        {
            onValidateUseDestroy = false;
            if(onValidateUseDestroy) Destroy(obj);
            else DestroyImmediate(obj);
        }
        public void InitScene()
        {
            Debug.Log("InitScene");
            NavigationGraph CreateNavMesh(){
                {
                    if(GameObject.Find("NavPoints")==null){
                        new GameObject("NavPoints");
                    }
                    GameObject obj = GameObject.Find("NavPoints");
                    obj.AddComponent<NavigationGraph>();
                    obj.transform.position = new Vector3(0, 0, 0);
                    obj.transform.localScale = new Vector3(1, 1, 1);
                }
                {
                    if(GameObject.Find("TargetPoints")==null){
                        new GameObject("TargetPoints");
                    }
                    GameObject obj = GameObject.Find("TargetPoints");
                    obj.transform.position = new Vector3(0, 0, 0);
                    obj.transform.localScale = new Vector3(1, 1, 1);
                }
                NavigationGraph graph = GameObject.Find("NavPoints").gameObject.GetComponent<NavigationGraph>();
                graph.infoList = this;
                agent.SetActive(false);
                graph.CreateNavMesh();
                agent.SetActive(true);
                return graph;
            }
            // 获取所有子物体的Transform组件
            Transform[] allChildren = gameObject.GetComponentsInChildren<Transform>();

            // 遍历所有子物体
            foreach (Transform child in allChildren)
            {
                // 跳过父物体本身
                if (child == gameObject.transform) continue;

                // 添加MeshCollider组件，如果没有的话
                MeshCollider meshCollider = child.gameObject.GetComponent<MeshCollider>();
                if (meshCollider == null)
                {
                    meshCollider = child.gameObject.AddComponent<MeshCollider>();
                }

                // // 添加Rigidbody组件，如果没有的话
                // Rigidbody rb = child.gameObject.GetComponent<Rigidbody>();
                // if (rb == null)
                // {
                //     rb = child.gameObject.AddComponent<Rigidbody>();
                // }

                // // 设置Rigidbody为kinematic
                // rb.isKinematic = true;
            }

            agent = null;
            agent = agent;

            Annotate.Unity.AI.Navigation.Samples.NavigationSampleInitializer.CreateAgent();
            CreateNavMesh();
        }

        private void DestroyNavPoints(){
            if(GameObject.Find("NavPoints")!=null)
                Remove(GameObject.Find("NavPoints"));
            if(GameObject.Find("TargetPoints")!=null)
                Remove(GameObject.Find("TargetPoints"));
        }
        [Button("生成导航点")]
        private void CreateNavPoints()
        {
            DestroyNavPoints();
            InitScene();
            NavigationGraph graph = GameObject.Find("NavPoints").GetComponent<NavigationGraph>();
            graph.AddNavigationPointsForInterest();
        }

        private List<GameObject> GetSpecialPoints(){
            List<GameObject> specials = new List<GameObject>();
            GameObject[] gos = SceneManager.GetActiveScene().GetRootGameObjects();
            foreach(GameObject go in gos){
                Transform child = go.transform;
                if(!child.name.StartsWith("SpecialPoint")) continue;
                specials.Add(child.gameObject);
            }
            return specials;
        }

        private string GetPath(Transform transform){
            if(transform.parent == null){
                return transform.name;
            }
            return GetPath(transform.parent) + "/" + transform.name;
        }
        
        private Transform LoadPath(string path){
            if(path.StartsWith("NavigationPoint")||path.StartsWith("SpecialPoint")){
                return GameObject.Find(path).transform;
            }
            string[] names = path.Split('/');
            GameObject obj = GameObject.Find(names[0]);
            for(int i = 1; i < names.Length; i++){
                obj = obj.transform.Find(names[i]).gameObject;
            }
            return obj.transform;
        }
        
        [ResizableTextArea]
        [Label("标注文件保存信息")]
        public string savePath;

        [Button("保存为任务文件")]
        private void Save(){
            scene_name = gameObject.name;
            // Get the full prefab path of the nearest instance root of the object
            scene_path = PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(gameObject);
            scene_path = scene_path.Replace(Application.dataPath, "Assets");
            scene_path = Path.GetFullPath(scene_path);
            scene_path = scene_path.Replace("\\", "/");
            scene_scale = new List<float>(){
                gameObject.transform.localScale.x,
                gameObject.transform.localScale.y,
                gameObject.transform.localScale.z
            };
            scene_position = new List<float>(){
                gameObject.transform.position.x,
                gameObject.transform.position.y,
                gameObject.transform.position.z
            };

            agent_position = new List<float>(){
                agent.transform.position.x,
                agent.transform.position.y,
                agent.transform.position.z
            };
            agent_rotation = new List<float>(){
                agent.transform.rotation.eulerAngles.x,
                agent.transform.rotation.eulerAngles.y,
                agent.transform.rotation.eulerAngles.z
            };


            // 地板改成floor的路径
            floor_objects = new List<string>();
            foreach(GameObject floor in floorObjects){
                floor_objects.Add(GetPath(floor.transform));
            }
            // 删除物体改成物体的路径
            removed_objects = new List<string>();
            foreach(GameObject obj in removedObjects){
                removed_objects.Add(GetPath(obj.transform));
            }
            
            HashSet<string> specialPointNames = new HashSet<string>();
            // 把导航点的都转成位置
            special_points = new List<SpecialPoint>();
            foreach(Transform child in GameObject.Find("NavPoints").transform){
                if(specialPointNames.Contains(child.name)) {
                    Error("重复的导航点名字：" + child.name);
                    return;
                }
                specialPointNames.Add(child.name);

                special_points.Add(new SpecialPoint(){
                    name = child.name,
                    position = new List<float>(){
                        child.position.x,
                        child.position.y,
                        child.position.z
                    },
                    type = "navigation"
                });
            }
            foreach(Transform child in GameObject.Find("TargetPoints").transform){
                if(specialPointNames.Contains(child.name)) {
                    Error("重复的导航点名字：" + child.name);
                    return;
                }
                specialPointNames.Add(child.name);
                special_points.Add(new SpecialPoint(){
                    name = child.name,
                    position = new List<float>(){
                        child.position.x,
                        child.position.y,
                        child.position.z
                    },
                    type = "navigation-target"
                });
            }
            // 把特殊点的都转成位置
            foreach(GameObject _child in GetSpecialPoints()){
                Transform child = _child.transform;
                if(specialPointNames.Contains(child.name)) {
                    Error("重复的特殊点名字：" + child.name);
                    return;
                }
                specialPointNames.Add(child.name);
                special_points.Add(new SpecialPoint(){
                    name = child.name,
                    position = new List<float>(){
                        child.position.x,
                        child.position.y,
                        child.position.z
                    },
                    type = "special"
                });
            }


            // 把可操作物体改一改
            for(int i = 0; i < options.Count; i++){
                options[i].option_type = options[i].option_type.Split('-')[0];
                options[i].objects = new List<string>();
                if(options[i].option_type!="Answer"){
                    for(int j = 0; j < options[i].gameObjects.list.Count; j++){
                        if(options[i].gameObjects.list[j] == null){
                            Error("选项"+options[i].option_type+" " + options[i].option_text + "的物体为空");
                            return;
                        }
                        options[i].objects.Add(GetPath(options[i].gameObjects.list[j].transform));
                    }
                }
            }

            // 把判定函数的物体改一改
            for(int i = 0; i < predicates.Count; i++){
                if(predicates[i].targetObject != null){
                    predicates[i].predicate_object = GetPath(predicates[i].targetObject.transform);
                }
                if(predicates[i].targetPlace != null){
                    predicates[i].predicate_place = predicates[i].targetPlace.name;
                }
            }

            

            message = "";
            //get current time second
            string time = Utils.GetTimeString(true);
            string file_name = $"task-{time}-{gameObject.name}-{task_text.Replace(" ","_").Replace(".","_").Replace("?","_").Replace("!","_").Replace(":","_").Replace(";","_")}.json";
            savePath = Path.Combine(Application.dataPath, "Tasks", file_name);
            Utils.WriteFile(Path.Combine(Application.dataPath, "Tasks"), file_name, JsonUtility.ToJson(this, true));
            savePath = Path.GetFullPath(savePath);
            savePath = savePath.Replace("\\", "/");
            savePath = $"（请勿修改此文本）文件被保存在\n{savePath}\n用下列命令打开此任务：\npython run_eval.py --agent human --max_steps 30 --max_images 25 --port 50051 --sync --run_one_task_instance {savePath}\n\n";
            Refresh();
        }

        
        [ValidateInput("IsEmpty", "出错了！")]
        [HideIf("IsEmpty")]
        [Label("出错信息")]
        [ReadOnly]
	    public string message="";
        public bool IsEmpty(){
            return message == "";
        }
        public void Error(string str){
            Debug.LogError(str);
            message = str;
        }

        public void Load(string text){
            string json = text;
            if(json == null){
                message = "文件不存在";
                return;
            }
            Debug.Log(json);
            // Monobeheviour不能直接用JsonUtility.FromJson序列化
            // https://gamedev.stackexchange.com/questions/186780/how-do-you-de-serialize-a-monobehaviour-class
            // TaskInstance task = JsonUtility.FromJson<TaskInstance>(json);
            JsonUtility.FromJsonOverwrite(json, this);
            transform.position = new Vector3(scene_position[0], scene_position[1], scene_position[2]);
            transform.localScale = new Vector3(scene_scale[0], scene_scale[1], scene_scale[2]);
            
            agent.transform.position = new Vector3(agent_position[0], agent_position[1], agent_position[2]);
            agent.transform.rotation = Quaternion.Euler(agent_rotation[0], agent_rotation[1], agent_rotation[2]);

            removedObjects = new List<GameObject>();
            foreach(string path in removed_objects){
                removedObjects.Add(LoadPath(path).gameObject);
            }
            floorObjects = new List<GameObject>();
            foreach(string path in floor_objects){
                Debug.Log("LoadPath "+path);
                floorObjects.Add(LoadPath(path).gameObject);
            }
            DestroyNavPoints();
            InitScene();

            // 把导航点和特殊点都转成物体
            foreach(GameObject go in GetSpecialPoints()){
                Remove(go);
            }


            foreach(SpecialPoint point in special_points){;
                if(point.type == "navigation"){
                    GameObject obj = new GameObject(point.name);
                    obj.transform.position = new Vector3(point.position[0], point.position[1], point.position[2]);
                    obj.transform.parent = GameObject.Find("NavPoints").transform;
                    bool forInterest = false;
                    Utils.DrawSphere(obj.transform.position, 0.1f, forInterest? Color.green:Color.cyan, obj, "sphere", obj);
                }
                else if(point.type == "navigation-target"){
                    GameObject obj = new GameObject(point.name);
                    obj.transform.position = new Vector3(point.position[0], point.position[1], point.position[2]);
                    obj.transform.parent = GameObject.Find("TargetPoints").transform;
                    Utils.DrawSphere(obj.transform.position, 0.1f, Color.red, obj, "sphere", obj);
                }
                else {
                    GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                    obj.transform.position = new Vector3(point.position[0], point.position[1], point.position[2]);
                    obj.transform.localScale = new Vector3(0.1f, 0.1f, 0.1f);
                    obj.name = point.name;
                }
            }

            foreach(Option option in options){
                option.gameObjects = new NestedArray<GameObject>();
                option.gameObjects.list = new List<GameObject>();
                foreach(string name in option.objects){
                    GameObject obj=LoadPath(name).gameObject;
                    if(obj == null){
                        Error("找不到物体：" + name);
                        return;
                    }
                    option.gameObjects.list.Add(obj);
                }
            }
            foreach(Predicate predicate in predicates){
                if(predicate.predicate_object != null){
                    predicate.targetObject = LoadPath(predicate.predicate_object).gameObject;
                }
                if(predicate.predicate_place != null){
                    predicate.targetPlace = LoadPath(predicate.predicate_place).gameObject;
                }
            }
        }
        public void OnValidate(){
            // On Validate不能destory也不能destory immediately
            // https://discussions.unity.com/t/in-onvalidate-since-using-destroy-and-destroyimmediate-can-result-in-errors/924876/6
            Debug.Log("OnValidate");
            if(floorObjects == null) {
                InitVariables();
            }
            if(floorObjects.Count == 0 || floorObjects[0] == null){
                InitScene();
            }
        }
    }


}
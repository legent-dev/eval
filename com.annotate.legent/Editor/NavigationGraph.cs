using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.AI;
using Unity.AI.Navigation;
using System.Threading.Tasks;

namespace Annotator
{
    public enum OptionType { TurnLeft, TurnRight, MoveForward, Grab, Put, Answer, LookUpward, LookDownward }


    public enum NodeType { Navigable, Interest }
    public class NavigationNode
    {
        public Vector3 position;
        public NodeType type;
        public List<NavigationNode> neighbors;

    }

    [ExecuteInEditMode] // 让OnTransformChildrenChanged一直执行
    public class NavigationGraph : MonoBehaviour
    {
        // 既是sample distance，又是可抓取distance
        public static float SAMPLE_DISTANCE = 2f; // 一个insterest point是否需要被连接到一个完全无关的navigation point上，如果在可抓取距离内，可以加上，例如从桌子的两个方向上过来都可以抓。否则不要了。
        public GameObject playmateArmature;
        public List<GameObject> navigationPoints;
        public List<GameObject> interestPoints;
        public List<NavigationNode> nodes;
        public int currentNode;
        public int faceNode; // 面向哪个邻居node（在neighbor数组的index）
        public List<Option> options;
        public List<Option> manipulations;
        public bool isCreating = false;
        public TaskInstance infoList;
        public float CONNECT_DISTANCE=3.5f;
        public static float MIN_NEIGHBOR_DISTANCE=1.5f;
        public void CreateNavMesh()
        {
            // SetLayerRecursively(createdScene, NAV_MESH_LAYER);

            // 新建NavMesh
            GameObject navMeshSurfaceGameObject = gameObject;
            NavMeshSurface navMeshSurface = navMeshSurfaceGameObject.AddComponent<NavMeshSurface>();
            navMeshSurface.agentTypeID = 3;
            navMeshSurface.layerMask = NavMesh.AllAreas; // Use NavMesh.AllAreas to include all layers.

            // 设置layerMask忽略掉一些mesh
            LayerMask excludedLayers = LayerMask.GetMask("NonNavMesh") | LayerMask.GetMask("PlaymateArmature") | LayerMask.GetMask("PlayerArmature") | LayerMask.GetMask("Doorway"); // TODO: 整理一下所有layer
            //navMeshSurface.defaultArea = 0; // Set the default area type
            LayerMask includedLayers = ~excludedLayers;
            navMeshSurface.layerMask = includedLayers;

            // Build the NavMesh at runtime.
            navMeshSurface.BuildNavMesh();

            // // TODO: 改成一个自适应的合理位置？ 之前这句忘删了，怪不得不行，playmateArmature.transform.localPosition = new Vector3(-0.48f, 0.08f, -1.60f);
            // // TODO: Failed to create agent because it is not close enough to the NavMesh
            // // 新建NavMeshAgent
            // NavMeshAgent navMeshAgent = playmateArmature.AddComponent<NavMeshAgent>();
            // navMeshAgent.agentTypeID = 1;
            // navMeshAgent.speed = 1;
            // navMeshAgent.updatePosition = false; // 禁用navMeshAgent的移动，用CharacterController来移动
            // navMeshAgent.updateRotation = false;

            // // 文档 Library\PackageCache\com.unity.ai.navigation@1.1.4\Documentation~\NavMeshAgent.md
            // //
            // navMeshAgent.autoRepath = false; // 到不了的时候到一个可达的最近点，不然会一直pathPending【TODO：好像没有用啊！】

            // playmateArmature.GetComponent<BasePersonController>().navMeshAgent = navMeshAgent;
            // // CharacterController和NavMeshAgent的控制会冲突，disable掉CharacterController，NavMeshAgent才会动
            // // 或者直接用CharacterController控制运动


        }


        public void GetInterestPoints()
        {

        }
        public void AddNavigationPointsForInterest()
        {
            isCreating = true;
            navigationPoints = new List<GameObject>(); // TODO: 可以使用预定义的navigationPoints（例如python端传入），不是重新实时生成
            interestPoints = new List<GameObject>();
            // const float MIN_NEIGHBOR_DISTANCE = 1.5f;
            Transform navPoints = gameObject.transform;
            Transform targetPoints = GameObject.Find("TargetPoints").transform;
            if (!GameObject.Find("DrawScratch")) new GameObject("DrawScratch");

            bool AddNavPoint(Vector3 position, bool forInterest)
            {
                // https://docs.unity3d.com/ScriptReference/AI.NavMesh.SamplePosition.html
                NavMeshHit hit;
                if (NavMesh.SamplePosition(position, out hit, NavigationGraph.SAMPLE_DISTANCE, NavMesh.AllAreas))
                {
                    if (hit.position.y > 1) return false; // 太高了，可能是屋顶
                    Vector3 hit_position = hit.position;
                    Vector3 dir = hit_position - position;
                    dir = new Vector3(dir.x, 0, dir.z);
                    // 让导航点不要都在边缘，往中间去一点，因为大多时候确实导航点都是在边缘的。
                    if (dir.magnitude > 0.1f)
                    { // 原位置离成功采样位置很远，表示在边缘
                        // 如果往里走0.2还是在navmesh上，就用这个位置
                        if (NavMesh.SamplePosition(hit_position + dir.normalized * 0.1f, out hit, 0, NavMesh.AllAreas))
                        {
                            if (NavMesh.SamplePosition(hit_position + dir.normalized * 0.2f, out hit, 0, NavMesh.AllAreas))
                            {
                                if (MIN_NEIGHBOR_DISTANCE>=1.5f&&NavMesh.SamplePosition(hit_position + dir.normalized * 0.4f, out hit, 0, NavMesh.AllAreas))
                                {
                                    
                                    if (NavMesh.SamplePosition(hit_position + dir.normalized * 0.5f, out hit, 0, NavMesh.AllAreas)&&NavMesh.SamplePosition(hit_position + dir.normalized * 0.6f, out hit, 0, NavMesh.AllAreas))
                                    {
                                        // 对于interest点，不要走太远
                                        if (!forInterest && NavMesh.SamplePosition(hit_position + dir.normalized * 0.7f, out hit, 0, NavMesh.AllAreas) && NavMesh.SamplePosition(hit_position + dir.normalized * 0.8f, out hit, 0, NavMesh.AllAreas))
                                        {
                                            // 如果往里走0.8还是在navmesh上，就用往里走0.4m
                                            if (!forInterest && NavMesh.SamplePosition(hit_position + dir.normalized * 0.9f, out hit, 0, NavMesh.AllAreas) && NavMesh.SamplePosition(hit_position + dir.normalized * 1.0f, out hit, 0, NavMesh.AllAreas))
                                            {
                                                // if(!forInterest && NavMesh.SamplePosition(hit_position + dir.normalized * 1.2f, out hit, 0, NavMesh.AllAreas)){
                                                //     hit_position  += dir.normalized * 0.6f;
                                                // }
                                                // else hit_position  += dir.normalized * 0.5f;
                                                hit_position  += dir.normalized * 0.5f;
                                            }
                                            else hit_position += dir.normalized * 0.4f;
                                        }
                                        else hit_position += dir.normalized * 0.3f;
                                    }
                                    else hit_position += dir.normalized * 0.2f;
                                }
                                else hit_position += dir.normalized * 0.2f;
                            }
                            else hit_position += dir.normalized * 0.1f;
                        }
                    }

                    bool hasNeighbor = false;
                    foreach (GameObject nav in navigationPoints)
                    {
                        // 感兴趣点，加navPoint宽容度高（也不是一定要加，不然两个点重合了会报错）
                        float nearJudgeDistance = forInterest ? 0.3f : MIN_NEIGHBOR_DISTANCE;
                        if (Vector3.Distance(nav.transform.position, hit_position) < nearJudgeDistance)
                        {
                            hasNeighbor = true;
                            break;
                        }
                    }
                    if (!hasNeighbor)
                    {
                        string name = "NavigationPoint" + navigationPoints.Count;
                        GameObject navPoint = new GameObject(name);
                        navPoint.transform.position = hit_position;

                        navPoint.transform.parent = navPoints;
                        navigationPoints.Add(navPoint);
                        Utils.DrawSphere(hit_position, 0.1f, forInterest ? Color.green : Color.cyan, navPoint, "sphere", navPoint); //.layer = LayerMask.NameToLayer("SceneEditor");
                        //Utils.DrawLine(hit.position,new Vector3(position.x, hit.position.y, position.z), Color.yellow);
                        return true;
                    }
                }
                return false;
            }


            infoList.message = "";
            // 根据options和predicates看看再加上哪些感兴趣的物体
            HashSet<GameObject> allInterest = new HashSet<GameObject>();
            if(infoList.options != null)
            foreach (Option option in infoList.options)
            {
                foreach (GameObject obj in option.gameObjects.list)
                {
                    if (option.option_type == "Answer-回答" || option.option_type == "SpecialAction-特殊动作") continue;
                    else if (obj == null) infoList.Error($"选项{option.option_type} {option.option_text} 的可操作对象为空！");
                    else
                    {
                        allInterest.Add(obj);
                    }

                }
            }
            // foreach(Predicate predicate in infoList.predicates){
            //     allInterest.Add(predicate.targetObject);
            //     allInterest.Add(predicate.targetPlace);
            // }

            foreach (GameObject obj in allInterest)
            {
                Vector3 position = Utils.VecXZ(Utils.GetBounds(obj).center);
                bool success = AddNavPoint(position, true);
                if (success)
                {
                    // GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    // cube.transform.position = position;
                    // cube.transform.parent = navPoints;
                    string name = "NavigationPoint" + interestPoints.Count + "-Target";
                    GameObject navPoint = new GameObject(name);
                    navPoint.transform.position = Utils.GetBounds(obj).center;
                    navPoint.transform.parent = targetPoints;

                    Debug.Log("NavPoint" + navPoint);
                    interestPoints.Add(navPoint);


                    Utils.DrawSphere(navPoint.transform.position, 0.11f, Color.red, navPoint, "sphere", navPoint);
                    //navigationPointToInterestPoint.Add(navigationPoints[navigationPoints.Count-1], navPoint);
                    // Debug.Log("Add interest point"+obj+" "+obj.transform.Find("MeshCenter").gameObject);
                    // interestPoints.Add(obj.transform.Find("MeshCenter").gameObject);
                    // navigationPointToInterestPoint.Add(navigationPoints[navigationPoints.Count-1], obj.transform.Find("MeshCenter").gameObject);
                }
                if (!success)
                {
                    Utils.DrawSphere(position, 0.1f, Color.red, null, "sphere", null); //.layer = LayerMask.NameToLayer("SceneEditor");
                    if (!NavMesh.SamplePosition(position, out _, NavigationGraph.SAMPLE_DISTANCE, NavMesh.AllAreas))
                        Debug.LogError("Could not find a navigation point for the object " + obj);
                }
            }

            // 根据options看看再加上哪些感兴趣的物体
            // for(int i=0;i<infoList.options.Count;i++){
            //     foreach(int objectID in infoList.options[i].object_ids){
            //         infoList.instances[objectID].of_interest = true;
            //     }
            // }

            // 把感兴趣的物体生成必要的导航点
            // for(int i=0;i<infoList.instances.Count;i++){
            //     if(infoList.instances[i].of_interest){
            //         Vector3 position = Utils.VecXZ(assetsLoader.sceneObjects.objects[i].position);
            //         bool success = AddNavPoint(position, true);
            //         if(success) interestPoints.Add(assetsLoader.sceneObjects.objects[i].gameObject.transform.Find("MeshCenter").gameObject);
            //         if(!success){
            //             if (!NavMesh.SamplePosition(position, out _, NavigationGraph.SAMPLE_DISTANCE, NavMesh.AllAreas))
            //                 Debug.LogError("Could not find a navigation point for the object "+infoList.instances[i].prefab);
            //         }
            //     }
            // }
            // 加入其他物体的导航点
            // for(int i=0;i<infoList.instances.Count;i++) {
            //     if(infoList.instances[i].of_interest) continue;

            //     bool isFloor = infoList.instances[i].prefab.StartsWith("LowPolyInterior") && infoList.instances[i].prefab.Contains("Floor");

            //     if(isFloor) {
            //         bool success = AddNavPoint(Utils.VecXZ(assetsLoader.sceneObjects.objects[i].position), false);
            //         if(success) interestPoints.Add(null);
            //     }
            //     else{
            //         bool success = AddNavPoint(Utils.VecXZ(assetsLoader.sceneObjects.objects[i].position), false);
            //         if(success) interestPoints.Add(null); // NOTE: 不然加了会导致interestPoints和navigationPoints重合，造成错误
            //     }
            // }

            // 加入均匀洒落的补充导航点
            const float UNIT_DISTANCE = 0.5f;
            // Find TaskInstance Component in the whole scene
            TaskInstance[] taskInstances = FindObjectsOfType<TaskInstance>();
            if (taskInstances.Length == 0)
            {
                Debug.LogError("No TaskInstance found in the scene");
                return;
            }
            else if (taskInstances.Length > 1)
            {
                Debug.LogError("More than one TaskInstance found in the scene");
                return;
            }
            TaskInstance taskInstance = taskInstances[0];
            Bounds bounds = Utils.GetBounds(taskInstance.gameObject);
            Vector3 floor_position = bounds.center - new Vector3(0, bounds.size.y / 2, 0);
            Vector3 floor_size = bounds.size;
            for (float x = floor_position[0] - floor_size[0] / 2 + UNIT_DISTANCE/2; x < floor_position[0] + floor_size[0] / 2; x += UNIT_DISTANCE)
            {
                for (float z = floor_position[2] - floor_size[2] / 2 + UNIT_DISTANCE/2; z < floor_position[2] + floor_size[2] / 2; z += UNIT_DISTANCE)
                {
                    bool success = AddNavPoint(new Vector3(x, 0, z), false);
                    // if(success) interestPoints.Add(null);
                }
            }

            BuildNavigationGraph();
            // ResetAgentToNearest();
            isCreating = false;
        }

        public void BuildNavigationGraph()
        {
            // List<GameObject> navigationPoints;
            // List<GameObject> interestPoints;
            Utils.ClearScratch();
            if (interestPoints == null)
            {
                return;
                Debug.Log("interestPoints is null");
                return;
                interestPoints = new List<GameObject>();
                for (int i = 0; i < navigationPoints.Count; i++)
                {
                    interestPoints.Add(null);
                }
            }
            // https://docs.unity3d.com/ScriptReference/AI.NavMeshTriangulation.html
            // NavMeshTriangulation

            // NavMesh.Raycast 可以判断两点间是否有障碍物（是否两点连线会有在navmesh外的部分）


            //const float CONNECT_DISTANCE = 2.5f;
            //const float CONNECT_DISTANCE = 3.5f;
            nodes = new List<NavigationNode>();
            GameObject targetPoints = GameObject.Find("TargetPoints");
            for (int i = 0; i < navigationPoints.Count; i++)
            {
                GameObject point = navigationPoints[i];
                NavigationNode node = new NavigationNode
                {
                    position = Utils.VecXZ(point.transform.position) + new Vector3(0, 0.1f, 0),
                    type = NodeType.Navigable,
                    neighbors = new List<NavigationNode>()
                };
                nodes.Add(node);
                // 连接自己的interest
                if (targetPoints.transform.Find(point.name + "-Target") != null)
                    point = targetPoints.transform.Find(point.name + "-Target").gameObject;
                else point = null;
                // point = interestPoints[i];
                if (point != null)
                {
                    // 造孽，这句让navigationPoint乱套了
                    //Utils.DrawSphere(point.transform.position, 0.1f, Color.red, null, "sphere", point); //.layer = LayerMask.NameToLayer("SceneEditor");
                    NavigationNode interest = new NavigationNode
                    {
                        position = new Vector3(point.transform.position.x, 0.1f, point.transform.position.z),
                        type = NodeType.Interest,
                        neighbors = new List<NavigationNode>()
                    };
                    node.neighbors.Add(interest);
                    nodes.Add(interest);
                }
            }

            // for (int i=0;i<interestPoints.Count;i++ )
            // {
            //     GameObject point = interestPoints[i];
            //     NavigationNode node = new NavigationNode
            //     {
            //         position = point.transform.position,
            //         type = NodeType.Interest,
            //         neighbors = new List<NavigationNode>()
            //     };
            //     nodes.Add(node);
            // }
            for (int i = 0; i < nodes.Count; i++)
            {
                NavigationNode thisNode = nodes[i];
                bool TooDenseAfterAdd(NavigationNode newNode)
                {
                    // 不要让夹角过于密集
                    bool tooDense = false;
                    foreach (NavigationNode neighbor in thisNode.neighbors)
                    {
                        if (Vector3.Angle(neighbor.position - thisNode.position, newNode.position - thisNode.position) < 60)
                        {
                            tooDense = true;
                            break;
                        }
                    }
                    return tooDense;
                }
                // 连接其他navigable
                if (thisNode.type == NodeType.Interest) continue;

                // 按距离连接，由近及远连接
                List<(float, int)> distance_index = new List<(float, int)>();
                for (int j = 0; j < nodes.Count; j++)
                {
                    if (i == j) continue;
                    if (nodes[j].type == NodeType.Interest) continue;
                    if (thisNode.neighbors.Contains(nodes[j])) continue;
                    NavMeshHit hit;
                    bool blocked = NavMesh.Raycast(thisNode.position, nodes[j].position, out hit, NavMesh.AllAreas);
                    if (Vector3.Distance(thisNode.position, nodes[j].position) < CONNECT_DISTANCE + 0.01f && !blocked)
                    {
                        distance_index.Add((Vector3.Distance(thisNode.position, nodes[j].position), j));
                    }
                }
                distance_index.Sort((a, b) => a.Item1.CompareTo(b.Item1));
                foreach((float, int) item in distance_index)
                {
                    int j = item.Item2;
                // for (int j = 0; j < nodes.Count; j++)
                // {
                    if (i == j) continue;
                    if (thisNode.neighbors.Contains(nodes[j])) continue;
                    NavMeshHit hit;
                    bool blocked = NavMesh.Raycast(thisNode.position, nodes[j].position, out hit, NavMesh.AllAreas);
                    if (nodes[j].type == NodeType.Navigable && Vector3.Distance(thisNode.position, nodes[j].position) < CONNECT_DISTANCE + 0.01f && !blocked)
                    {
                        //if(nodes[j].neighbors.Contains(nodes[i])) continue;
                        if (!TooDenseAfterAdd(nodes[j]))
                        {
                            thisNode.neighbors.Add(nodes[j]);
                            nodes[j].neighbors.Add(thisNode);
                        }
                    }
                }

                // 连接其他interest
                for (int j = 0; j < nodes.Count; j++)
                {
                    if (nodes[j].type == NodeType.Interest && Vector3.Distance(thisNode.position, nodes[j].position) < SAMPLE_DISTANCE + 0.01f)
                    {
                        if (!TooDenseAfterAdd(nodes[j])) thisNode.neighbors.Add(nodes[j]);
                    }
                }

            }

            // 加入interest
            // NOTE:需要在navigable互相连完之后再做，不然会出现A点有了4个朝向之后，B点由于只能和A点相连，又去连接A点了，导致A点有了5个朝向
            for (int i = 0; i < nodes.Count; i++){
                
                NavigationNode thisNode = nodes[i];
                if (thisNode.type == NodeType.Interest) continue;

                // 给只有一个neighbor的点加上一个新的interest
                if (thisNode.neighbors.Count == 1)
                {
                    // Debug.LogError("Add new interest");
                    NavigationNode interest = new NavigationNode
                    {
                        position = thisNode.position - (thisNode.neighbors[0].position - thisNode.position).normalized * 0.3f,
                        type = NodeType.Interest,
                        neighbors = new List<NavigationNode>()
                    };
                    thisNode.neighbors.Add(interest);
                    nodes.Add(interest);
                }

                // 给特别空的部分加入新的interest
                List<Vector3> rayDirections = new List<Vector3>();
                for (int j = 0; j < thisNode.neighbors.Count; j++) rayDirections.Add(thisNode.neighbors[j].position - thisNode.position);
                rayDirections.Sort((a, b) => Vector3.SignedAngle(Vector3.forward, a, Vector3.up).CompareTo(Vector3.SignedAngle(Vector3.forward, b, Vector3.up))); // -180到180
                for (int j = 0; j < rayDirections.Count; j++)
                {
                    Vector3 currentRay = rayDirections[j];
                    Vector3 nextRay = rayDirections[(j + 1) % rayDirections.Count];
                    // if(j==0)Utils.DrawLine(thisNode.position, thisNode.position + currentRay.normalized*0.3f, Color.red);
                    // if(j==1)Utils.DrawLine(thisNode.position, thisNode.position + currentRay.normalized*0.3f, Color.green);
                    // if(j==2)Utils.DrawLine(thisNode.position, thisNode.position + currentRay.normalized*0.3f, Color.blue);
                    // float angleBetween = Vector3.Angle(currentRay, nextRay);
                    float angleBetween = Vector3.SignedAngle(currentRay, nextRay, Vector3.up);
                    if (angleBetween < 0) angleBetween += 360; // 确保角度为正

                    const float gapThresholdDegrees = 150.0f; // 设置缝隙阈值为60度
                    if (angleBetween >= gapThresholdDegrees)
                    {
                        // 旋转出需要的新方向
                        Vector3 newDirection = Quaternion.AngleAxis(angleBetween / 2, Vector3.up) * currentRay;
                        // Vector3 newDirection = Vector3.Slerp(currentRay, nextRay, 0.5f).normalized;
                        // rayDirections.Add(newDirection);
                        NavigationNode interest = new NavigationNode
                        {
                            position = thisNode.position + newDirection.normalized * 0.3f,
                            type = NodeType.Interest,
                            neighbors = new List<NavigationNode>()
                        };

                        //Utils.DrawLine(thisNode.position, thisNode.position + newDirection.normalized*0.3f, Color.yellow);
                        thisNode.neighbors.Add(interest);
                        nodes.Add(interest);
                    }
                }
            }

            for (int i = 0; i < nodes.Count; i++)
            {
                for (int j = 0; j < nodes[i].neighbors.Count; j++)
                {
                    Vector3 dir = nodes[i].neighbors[j].position - nodes[i].position;
                    if (nodes[i].type == NodeType.Navigable && nodes[i].neighbors[j].type == NodeType.Navigable)
                        Utils.DrawLine(nodes[i].position, nodes[i].position + dir, Color.green); // .layer = LayerMask.NameToLayer("SceneEditor");;
                    else
                        Utils.DrawLine(nodes[i].position, nodes[i].position + dir.normalized * 0.5f, Color.yellow); // .layer = LayerMask.NameToLayer("SceneEditor");;
                }
            }
        }
        private NavigationNode CurrentNode()
        {
            return nodes[currentNode];
        }
        private NavigationNode FaceNode()
        {
            return nodes[currentNode].neighbors[faceNode];
        }

        private bool isLookingUpward = false;

        public void ResetAgentToNearest()
        {
            // 找到最近的node
            float minDistance = float.MaxValue;
            int nearestNode = -1;
            for (int i = 0; i < nodes.Count; i++)
            {
                NavigationNode node = nodes[i];
                if (node.type != NodeType.Navigable) continue;
                float distance = Vector3.Distance(node.position, playmateArmature.transform.position);
                if (distance < minDistance)
                {
                    minDistance = distance;
                    nearestNode = i;
                }
            }
            currentNode = nearestNode;

            // 在node中找到和foward方向最接近的neighbor
            float minAngle = float.MaxValue;
            int nearestNeighbor = -1;
            for (int i = 0; i < CurrentNode().neighbors.Count; i++)
            {
                float angle = Vector3.Angle(CurrentNode().neighbors[i].position - CurrentNode().position, playmateArmature.transform.forward);
                if (angle < minAngle)
                {
                    minAngle = angle;
                    nearestNeighbor = i;
                }
            }
            faceNode = nearestNeighbor;

            // playmateArmature.transform.position = CurrentNode().position;
            // playmateArmature.transform.forward = FaceNode().position - CurrentNode().position;

            // playmateArmature.GetComponent<BasePersonController>().SetCameraPitch(45);
            isLookingUpward = false;
        }
        public void OnKeyboard()
        {

        }

        public void RefreshNavigationPoints()
        {
            navigationPoints = new List<GameObject>();
            interestPoints = new List<GameObject>();
            foreach (Transform child in transform)
            {
                navigationPoints.Add(child.gameObject);
            }
            foreach (Transform child in GameObject.Find("TargetPoints").transform)
            {
                bool valid = false;
                foreach (Transform nav in GameObject.Find("NavPoints").transform)
                {
                    if (nav.name == child.name.Replace("-Target", ""))
                    {
                        valid = true;
                    }
                }
                if (!valid) DestroyImmediate(child.gameObject);
                else interestPoints.Add(child.gameObject);
            }
        }
        public void Update()
        {
            bool changed = false;
            foreach (Transform child in transform)
            {
                if (child.hasChanged)
                {
                    changed = true;
                    break;
                }
            }
            if (changed)
            {
                RefreshNavigationPoints();
                BuildNavigationGraph();
            }
        }

        public void OnTransformChildrenChanged()
        {
            if (isCreating) return;
            Debug.Log("OnTransformChildrenChanged");
            RefreshNavigationPoints();
            BuildNavigationGraph();
        }
    }
}

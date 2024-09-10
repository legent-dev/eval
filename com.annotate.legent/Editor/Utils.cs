using UnityEditor;
using UnityEngine;
using System.Text.RegularExpressions;
using System.Linq;
using System;
using System.Collections.Generic;
using System.IO;

namespace Annotator
{

    public class Utils : MonoBehaviour
    {
        public static string Normalize(string name)
        {
            return Regex.Replace(name.ToLower().Replace('_', ' '), @"\s+", "");
        }
        // Function to find the object by name in children and descendants
        public static GameObject FindObjectInDescendants(Transform parent, string name, bool fuzzy = false)
        {
            if (fuzzy) name = Normalize(name);
            foreach (Transform child in parent)
            {
                if (child.name == name)
                {
                    return child.gameObject;
                }
                if (fuzzy)
                {
                    if (Normalize(child.name).Contains(name))
                    {
                        return child.gameObject;
                    }
                }

                GameObject result = FindObjectInDescendants(child, name, fuzzy);
                if (result != null)
                {
                    return result;
                }
            }

            return null;
        }

        public static void Pause()
        {
#if UNITY_EDITOR
            EditorApplication.isPaused = true;
#endif
        }


        public static string GetTimeString(bool includeSeconds = false)
        {
            DateTime now = DateTime.Now;
            string formattedNow = now.ToString("yyyyMMddHHmm");
            if (includeSeconds) formattedNow += now.ToString("ss");
            return formattedNow;
        }

        public static void LogTime(string tag = "")
        {
            Debug.Log($"Time since Startup {tag}: {Time.realtimeSinceStartup}s");
        }

#if UNITY_WEBGL && !UNITY_EDITOR
        //[DllImport("__Internal")]
        //private static extern void PrintStackTrace();
        public static void WebGLCallTrace() {
            //PrintStackTrace();
        }
#else
        public static void WebGLCallTrace() {
        }
#endif

        public static void WriteFile(string directoryPath, string filename, string content)
        {
            if (!Directory.Exists(directoryPath))
            {
                Directory.CreateDirectory(directoryPath);
            }
            string filePath = Path.Combine(directoryPath, filename);
            using (StreamWriter writer = new StreamWriter(filePath))
            {
                writer.WriteLine(content);
            }
        }

        public static string ReadFile(string directoryPath, string filename)
        {
            string filePath = Path.Combine(directoryPath, filename);
            if (!File.Exists(filePath))
            {
                return null;
            }
            using (StreamReader reader = new StreamReader(filePath))
            {
                return reader.ReadToEnd();
            }
        }


        public static Vector3 ToVector3(float[] floatList)
        {
            return new Vector3(floatList[0], floatList[1], floatList[2]);
        }

        public static Vector3 ToVector3(List<float> floatList)
        {
            return new Vector3(floatList[0], floatList[1], floatList[2]);
        }

        public static float DistanceXZ(Vector3 v1, Vector3 v2)
        {
            Vector3 v1xz = new Vector3(v1.x, 0, v1.z);
            Vector3 v2xz = new Vector3(v2.x, 0, v2.z);
            return Vector3.Distance(v1xz, v2xz);
        }
        public static Vector3 VecXZ(Vector3 v)
        {
            Vector3 v1 = new Vector3(v.x, 0, v.z);
            return v1;
        }

        public static float ComputeSignedAngle2D(Vector2 vSource, Vector2 vTarget)
        {
            Vector2 v1 = vTarget;
            Vector2 v2 = vSource;
            // v1 目标方向，v2 playmate的方向
            v1.Normalize();
            v2.Normalize();
            double dot_product = v1[0] * v2[0] + v1[1] * v2[1];// 计算向量的点积 
            double cross_product = v1[0] * v2[1] - v1[1] * v2[0]; // 计算向量的叉积 
            double angle = Math.Atan2(cross_product, dot_product);// 计算带符号夹角（弧度） 
            double degree = angle / Math.PI * 180; //需要右转的角度
            return (float)degree;
        }

        public static float ComputeSignedAngle3D(Vector3 v1, Vector3 v2)
        {
            v1.Normalize();
            v2.Normalize();
            // Calculate the angle between the vectors
            float angle = Vector3.Angle(v1, v2);
            // Calculate the cross product of the vectors
            Vector3 cross = Vector3.Cross(v1, v2);
            // Calculate the dot product of the cross product and the reference up vector
            //float dot = Vector3.Dot(cross, Vector3.up);
            //float dot = Vector3.Dot(cross, Vector3.down); // BUG fix：应该用right, left，而不是up, down，否则一会正一会负
            // Adjust the sign of the angle based on the dot product
            //if (dot < 0f) angle = -angle;
            if (v1.y > v2.y)
            { //要向上转
                angle = -angle;
            }
            return angle;
        }

        public static float ComputeAngleToYAxis(Vector3 v)
        {
            v.Normalize();
            float angle = Mathf.Acos(v.y / 1.0f); // 计算与y轴的夹角（在Unity中，向量的y分量代表上方向）
            float degree = angle * Mathf.Rad2Deg; // 将弧度转换为度
            return degree;
        }
        public static float ComputeAngleToYAxisDiff(Vector3 vSource, Vector3 vTarget)
        {
            return ComputeAngleToYAxis(vTarget) - ComputeAngleToYAxis(vSource);
        }


        public static List<float> ToList(Vector3 v)
        {
            return new List<float> { v.x, v.y, v.z };
        }
        // 想要把child旋转到target的位置，但是通过旋转parent来实现。返回parent应当旋转到的位置
        public static Quaternion RotateByParent(Quaternion parent, Quaternion child, Quaternion childTarget)
        {
            Quaternion offset = childTarget * Quaternion.Inverse(child);
            return offset * parent;
        }
        // 想要把child放置到target的位置，但是通过移动parent来实现。返回parent应当移动到的位置
        public static Vector3 PositionByParent(Vector3 parent, Vector3 child, Vector3 childTarget)
        {
            Vector3 offset = childTarget - child;
            return parent + offset;
        }

        // 检查后代中是否存在某种组件
        public static bool CheckForComponentInChildren<T>(Transform obj) where T : Component
        {
            // 检查当前 GameObject 是否有指定类型的组件
            if (obj.GetComponent<T>() != null)
            {
                return true;
            }

            // 递归检查所有子对象
            foreach (Transform child in obj.transform)
            {
                if (CheckForComponentInChildren<T>(child))
                {
                    return true;
                }
            }

            return false;
        }

        public static GameObject player;
        public static GameObject agent;

        public static void ClearScratch()
        {
            GameObject.DestroyImmediate(GameObject.Find("DrawScratch"));
            GameObject parent = new GameObject("DrawScratch");
        }

        public static void EnablePlayersInEditor()
        {
            player.SetActive(true);
            agent.SetActive(true);
        }
        public static void DisablePlayersInEditor()
        {
            player = GameObject.Find("Player");
            agent = GameObject.Find("Agent");
            player.SetActive(false);
            agent.SetActive(false);
        }
        public static GameObject DrawSphere(Vector3 position, float scale = 0.05f, Color? color=null, GameObject parent = null, string name = "TEMP VIS", GameObject sphere=null)
        {
            if(sphere == null) sphere = new GameObject(name);
            if (parent == null) parent = GameObject.Find("DrawScratch");
            if (parent != null) sphere.transform.parent = parent.transform;

            // 设置球的Mesh
            MeshFilter meshFilter = sphere.AddComponent<MeshFilter>();
            meshFilter.mesh = Resources.GetBuiltinResource<Mesh>("New-Sphere.fbx");


            // 设置球体的颜色
            MeshRenderer renderer = sphere.AddComponent<MeshRenderer>();
            renderer.material = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
            if(color!=null) renderer.sharedMaterial.color = (Color)color;
            else renderer.sharedMaterial.color = Color.magenta; // 粉色

            sphere.transform.position = position;
            sphere.transform.localScale = new Vector3(scale, scale, scale);
            return sphere;
        }
        public static GameObject DrawSphere(Vector3 position, float scale = 0.05f, string colorStr = "magenta", GameObject parent = null, string name = "TEMP VIS")
        {
            Color color = Color.magenta;
            if (colorStr == "cyan") color = Color.cyan; // 蓝色
            else if (colorStr == "green") color = Color.green; // 蓝色
            else if (colorStr == "yellow") color = Color.yellow; // 蓝色
            return DrawSphere(position, scale, color, parent, name);

        }

        public static GameObject DrawBounds(Vector3 center, Vector3 size, Color color, GameObject parent = null, string name = "TEMP VIS")
        {
            GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            Destroy(cube.GetComponent<BoxCollider>());
            cube.name = name;
            if (parent == null) parent = GameObject.Find("DrawScratch");
            if (parent != null) cube.transform.parent = parent.transform;

            cube.transform.position = center;
            cube.transform.localScale = size;
            cube.GetComponent<Renderer>().material.color = color;
            // 材质变透明
            Material transparentMaterial = new Material(Resources.Load<Material>("Transparent"));
            transparentMaterial.color = new Color(color.r, color.g, color.b, 0.5f); // Set color to white with half transparency
            cube.GetComponent<Renderer>().material = transparentMaterial;

            return cube;
        }

        public static void ClearLines()
        {
            foreach (Transform child in GameObject.Find("DrawScratch").transform)
            {
                GameObject.Destroy(child.gameObject);
            }
        }
        public static GameObject DrawLine(Vector3 lineStart, Vector3 lineEnd)
        {
            return DrawLine(lineStart, lineEnd, Color.red);
        }

        public static Material lineMat =null;
        public static GameObject DrawLine(Vector3 lineStart, Vector3 lineEnd, Color color, float width=0.01f, string name="RAY LINE")
        {
            GameObject obj = new GameObject(name);
            obj.transform.parent = GameObject.Find("DrawScratch").transform;
            LineRenderer lineRenderer = obj.AddComponent<LineRenderer>();

            // Set the width of the Line Renderer
            lineRenderer.startWidth = width;
            lineRenderer.endWidth = width;

            // Set the number of vertex counts
            lineRenderer.positionCount = 2;

            // Set the Line Renderer's material
            if(lineMat==null)lineMat = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            // if(lineMat==null)lineMat = Resources.Load<Material>("ParticlesUnlit"); // TODO: 换成URP的材质Shader.Find("Universal .../Particles/Standard Unlit"
            lineRenderer.material = new Material(lineMat);
            //lineRenderer.material = new Material(Shader.Find("Particles/Standard Unlit"));

            // Set the color of the Line Renderer
            lineRenderer.startColor = color;
            lineRenderer.endColor = color;

            // Set the position of both two points of the line
            lineRenderer.SetPosition(0, lineStart);
            lineRenderer.SetPosition(1, lineEnd);
            return obj;
        }


        public static void DrawPlane((float, float, float, float, float) y_xz)
        {
            (float y, float xmin, float zmin, float xmax, float zmax) = y_xz;

            // 创建一个Plane对象
            GameObject plane = GameObject.CreatePrimitive(PrimitiveType.Plane);
            plane.name = "TEMP VIS plane";
            GameObject parent = GameObject.Find("DrawScratch");
            if (parent != null) plane.transform.parent = parent.transform;

            // 计算平面的中心点
            float centerX = (xmin + xmax) / 2f;
            float centerZ = (zmin + zmax) / 2f;

            // 设置平面的位置
            plane.transform.position = new Vector3(centerX, y, centerZ);

            // 计算平面需要缩放的倍数
            float scaleX = Mathf.Abs(xmax - xmin) / 10.0f; // Unity默认的Plane宽度是10个单位
            float scaleZ = Mathf.Abs(zmax - zmin) / 10.0f; // Unity默认的Plane长度是10个单位

            // 设置平面的缩放
            plane.transform.localScale = new Vector3(scaleX, 1, scaleZ);
        }


        // 获取一个物体的包围盒，考虑所有子物体
        // https://stackoverflow.com/questions/57711849/meshrenderer-has-wrong-bounds-when-rotated
        // renderer.bounds（不保证紧包围）和collider.bounds是世界坐标，mesh.bounds是局部坐标
        public static Bounds GetBounds(GameObject obj) // 世界坐标
        {
            Collider[] colliders = obj.GetComponentsInChildren<Collider>();
            if (colliders.Length == 0) return new Bounds();

            Bounds bounds = colliders[0].bounds;
            for (int i = 1; i < colliders.Length; i++)
            {
                bounds.Encapsulate(colliders[i].bounds);
            }
            return bounds;
        }
        public static Bounds GetRendererBounds(GameObject obj) // 世界坐标
        {
            // 如果用collider的GetBounds，EMAbench的物体会有问题，可能是导入的时候没有collider，位置会不对，只能用Renderer
            //Renderer[] renderers = obj.GetComponentsInChildren<Renderer>(); // TODO: 如果这个renderer是一个粒子特效呢？
            Renderer[] renderers = obj.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0) return new Bounds();

            Bounds bounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++)
            {
                bounds.Encapsulate(renderers[i].bounds);
            }
            return bounds;
        }

        public static void MoveMeshToAvoidCollision(GameObject obj, int obstaclesLayer)
        {
            // 没用
            Bounds bounds = GetBounds(obj);
            Collider[] cs = Physics.OverlapBox(bounds.center, bounds.extents, Quaternion.identity, obstaclesLayer);
            if(cs.Length > 0){
                Collider[] colliders = obj.GetComponentsInChildren<Collider>();
                foreach(Collider collider in colliders){
                    foreach(Collider c in cs){
                        Vector3 direction;
                        float distance;
                        
                        // 计算与每个Collider的穿透
                        if (Physics.ComputePenetration(
                            collider,
                            collider.transform.position,
                            collider.transform.rotation,
                            c,
                            c.transform.position,
                            c.transform.rotation,
                            out direction,
                            out distance))
                        {
                            // 根据穿透方向和距离调整位置
                            obj.transform.position += direction * distance;
                        }
                        
                    }
                }
            }
        }
        public static Vector3 MoveBoxToAvoidCollision(Vector3 center, Vector3 extents, int obstaclesLayer, float extend = 0.02f)
        {
            GameObject colliderObject = new GameObject("TempBoxCollider");
            BoxCollider boxCollider = colliderObject.AddComponent<BoxCollider>();

            boxCollider.transform.position = center;
            boxCollider.size = (extents+ extend*Vector3.one) * 2;
            Vector3 deltaMove = MoveBoxToAvoidCollision(boxCollider, obstaclesLayer);
            colliderObject.SetActive(false);
            Destroy(colliderObject);
            return deltaMove;
        }
        public static Vector3 MoveBoxToAvoidCollision(BoxCollider boxCollider, int obstaclesLayer)
        {
            Collider[] cs = Physics.OverlapBox(boxCollider.transform.position, boxCollider.size / 2, boxCollider.transform.rotation, obstaclesLayer);

            Vector3 deltaMove = Vector3.zero;
            foreach(Collider c in cs){
                Vector3 direction;
                float distance;
                
                // 计算与每个Collider的穿透
                if (Physics.ComputePenetration(
                    boxCollider,
                    boxCollider.transform.position,
                    boxCollider.transform.rotation,
                    c,
                    c.transform.position,
                    c.transform.rotation,
                    out direction,
                    out distance))
                {
                    if(Physics.Raycast(boxCollider.transform.position, direction, distance, obstaclesLayer)){
                        Debug.Log("Penetration wrong");
                        continue;
                        // Penetration出错了，比如穿到抽屉下面了，这时候用Raycast决定往哪里移动
                        // 计算左右应该怎么移动
                        // TODO: 如果左边rayCast有问题，且右边没有问题，那么往右边移动
                        // Physics.Raycast(boxCollider.transform.position, direction, distance, obstaclesLayer)
                        
                    }
                    // 根据穿透方向和距离调整位置
                    boxCollider.transform.position += direction * distance;
                    deltaMove += direction * distance;
                }
            }
            return deltaMove;
        }

        public static Vector3 GetCenterWorld(GameObject obj)
        {
            return GetBounds(obj).center;
        }

        public static string CreateWriteDirectory(string parentDirectory, string directoryName)
        {

            // 从Editor的Assets文件夹或者可执行文件的Data文件夹开始找
            string path = Application.dataPath;

            // 找到parentDirectory(例如.legent)文件夹为止
            while (!Directory.Exists(Path.Combine(path, parentDirectory)) && path != Path.GetPathRoot(path))
            {
                path = Directory.GetParent(path).FullName;
            }

            string filePath = Application.dataPath;


            string legentPath = Path.Combine(path, parentDirectory);
            if (Directory.Exists(legentPath))
            {
                string directoryPath = Path.Combine(legentPath, directoryName);
                if (!Directory.Exists(directoryPath))
                {
                    Directory.CreateDirectory(directoryPath);
                }
                filePath = directoryPath;
            }
            return filePath;
        }


        // Tranform.LookAt的Y轴精确对齐，Z轴尽量对齐版本（Tranform.LookAt是Z轴精确对齐）
        // Tranform.LookAt实现原理：先把z轴和第一个参数对齐，再调整旋转，使对象的上方 (y 轴) 尽可能接近你指定的第二个参数
        public static void YLookAt(Transform t, Vector3 targetDirectionY, Vector3 targetDirectionZ)
        {
            targetDirectionY.Normalize();
            targetDirectionZ.Normalize();

            // 计算使Y轴对齐的初始旋转
            Quaternion rotation = Quaternion.FromToRotation(t.up, targetDirectionY);

            // 应用初始旋转
            t.rotation = rotation * t.rotation;

            // 现在调整Z轴与targetDirectionZ对齐
            Vector3 currentZDirection = t.forward; // 当前Z轴方向
            Vector3 newZDirection = Vector3.ProjectOnPlane(targetDirectionZ, t.up); // 在Y轴平面投影的新Z方向

            Quaternion zRotation = Quaternion.FromToRotation(currentZDirection, newZDirection);

            // 应用最终旋转
            t.rotation = zRotation * t.rotation;
        }

        public static (List<Vector3>, List<MeshFilter>) GetVertices(GameObject obj, bool useLocal)
        {
            List<Vector3> vertices = new List<Vector3>();
            List<MeshFilter> meshes = new List<MeshFilter>();
            MeshFilter[] meshFilters = obj.GetComponentsInChildren<MeshFilter>();
            if (meshFilters.Length == 0) return (vertices, meshes);
            for (int i = 0; i < meshFilters.Length; i++)
            {
                Mesh mesh = meshFilters[i].mesh;
                for (int j = 0; j < mesh.vertexCount; j++)
                {
                    Vector3 worldVertex = meshFilters[i].transform.TransformPoint(mesh.vertices[j]);
                    if (useLocal)
                    {
                        vertices.Add(obj.transform.InverseTransformPoint(worldVertex));
                    }
                    else vertices.Add(worldVertex);
                    meshes.Add(meshFilters[i]);
                }
            }
            return (vertices, meshes);
        }

        public static (List<Vector3>, List<MeshFilter>) SampleVertices(GameObject obj, bool useLocal)
        {
            List<Vector3> vertices = new List<Vector3>();
            List<MeshFilter> meshes = new List<MeshFilter>();
            MeshFilter[] meshFilters = obj.GetComponentsInChildren<MeshFilter>();
            if (meshFilters.Length == 0) return (vertices, meshes);
            for (int i = 0; i < meshFilters.Length; i++)
            {
                Mesh mesh = meshFilters[i].mesh;
                System.Random rnd = new System.Random();
                int samples = 128;
                var randomNumbers = Enumerable.Range(0, mesh.vertexCount).OrderBy(x => rnd.Next()).Take(Math.Min(mesh.vertexCount, samples)).ToList();
                //Debug.Log($"{mesh.vertexCount}, {samples}, {randomNumbers.Count}" );
                //Debug.Log("List"+randomNumbers.OrderBy(x => x).ToList());
                // foreach (int num in randomNumbers.OrderBy(x => x).ToList())
                // {
                //     Debug.Log(num);
                // }
                foreach (int j in randomNumbers)
                {
                    Vector3 worldVertex = meshFilters[i].transform.TransformPoint(mesh.vertices[j]);
                    if (useLocal)
                    {
                        vertices.Add(obj.transform.InverseTransformPoint(worldVertex));
                    }
                    else vertices.Add(worldVertex);
                    meshes.Add(meshFilters[i]);
                }
            }
            return (vertices, meshes);
        }

        public static float ObjectInViewRatio(GameObject targetObject, Camera cam)
        {
            // TODO

            // 物体的包围盒的8个顶点投射到相机的视口坐标，再计算包围盒

            // 计算这个包围盒和相机视野的交集

            return 1;
        }

        // 判定一个物体是否在一个相机的视野范围内 VisibilityAndOcclusionCheck
        // ignoreWhenCasting用来忽略自身，例如不要打到机器人的eyeRight上
        public static (bool, string) ObjectInView(GameObject ignoreWhenCasting, GameObject targetObject, Camera cam, bool useMeshCenter, bool ignoreOcclusion = false)
        {
            // 转换为视口坐标
            Vector3 position = targetObject.transform.position;
            if (useMeshCenter) position = targetObject.transform.Find("MeshCenter").position;
            Vector3 viewportPos = cam.WorldToViewportPoint(position);

            // 检查是否在视野范围内
            // z>0表示在相机前方，x,y表示在视野矩形内
            bool isInView = viewportPos.z > 0 && viewportPos.x > 0 && viewportPos.x < 1 && viewportPos.y > 0 && viewportPos.y < 1;

            if (isInView)
            {
                if (ignoreOcclusion) return (true, "");
                // 发射射线检测遮挡
                Vector3 direction = position - cam.transform.position;
                RaycastHit hit;
                if (Physics.Raycast(cam.transform.position, direction.normalized, out hit, direction.magnitude, ~LayerMask.GetMask(ignoreWhenCasting.name)))

                // if (Physics.Raycast(cam.transform.position, direction.normalized, out hit, direction.magnitude))
                {
                    if (hit.transform == targetObject.transform) return (true, ""); // 对象在视野范围内且未被遮挡
                    else return (false, hit.transform.name); // 对象被其他物体遮挡
                }
                else return (true, ""); // 没有碰撞发生，也意味着没有遮挡
            }
            else return (false, "not in view"); // 不在视野范围内
        }

        // 给相机拍一张照片, 存到file里
        // TODO: 弄成项目的工具函数，其他所有的capturescreenshot都用这个。
        public static List<Color> CaptureScreenshot(GameObject camera, string filename, int width, int height, float verticalFOV, bool returnUniqueColors = false, Dictionary<Color, int> allowedColors = null, bool useAlpha=false)
        {
            Camera captureCamera = camera.GetComponent<Camera>();

            // 设置参数，camera的参数是视野和宽高比（用宽和高计算出来）。图像的参数是分辨率（宽和高）
            captureCamera.aspect = (float)width / height;
            captureCamera.fieldOfView = verticalFOV;

            // Create a RenderTexture with the desired width and height
            RenderTexture rt = new RenderTexture(width, height, useAlpha? 32: 24);

            // Set the target texture of the camera to the RenderTexture
            captureCamera.targetTexture = rt;
            captureCamera.Render();

            // Activate the RenderTexture so we can read its contents
            RenderTexture.active = rt;

            // Create a new Texture2D and read the RenderTexture data into it
            Texture2D screenshot = new Texture2D(width, height, useAlpha? TextureFormat.ARGB32: TextureFormat.RGB24, false);
            screenshot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            screenshot.Apply();

            List<Color> colors = null;

            void CheckInvalidColor()
            {
                Color[] pixels = screenshot.GetPixels();
                for (int i = 0; i < pixels.Length; i++)
                {
                    Color color = pixels[i];
                    if (allowedColors != null && !allowedColors.ContainsKey(color))
                    {
                        int x = i % width; // Calculate x position
                        int y = i / width; // Calculate y position
                        Vector2 screenPos = new Vector2(x / width, y / height);

                        // 使用Camera.ScreenPointToRay将屏幕坐标转换为射线
                        Ray ray = captureCamera.ViewportPointToRay(screenPos);
                        // 进行射线投射，查看射线与哪些物体相交
                        RaycastHit hit;
                        if (Physics.Raycast(ray, out hit))
                        {
                            Debug.Log("Hit object: " + hit.collider.gameObject.name);
                            GameObject obj = new GameObject("wrong obj");
                            obj.transform.parent = hit.collider.gameObject.transform;
                        }
                        else
                        {
                            Debug.Log("No hit");
                        }

                        Debug.LogError("Color not allowed: " + color);
                        break;
                    }
                }
            }
            if (returnUniqueColors) colors = GetUniqueColors(screenshot);

            // Clean up resources
            captureCamera.targetTexture = null;
            RenderTexture.active = null;
            Destroy(rt);

            if (filename != null && filename != "")
            {
                // Save the screenshot as a PNG file
                byte[] bytes = screenshot.EncodeToPNG();
                Debug.Log("Saving screenshot to " + filename);
                System.IO.File.WriteAllBytes(filename, bytes);
                Debug.Log("Screenshot saved as " + filename);
            }

            return colors;
        }

        public static List<Color> GetUniqueColors(Texture2D texture)
        {
            Color[] pixels = texture.GetPixels();
            HashSet<Color> uniqueColors = new HashSet<Color>();
            foreach (Color pixel in pixels)
            {
                uniqueColors.Add(pixel);
            }
            return uniqueColors.ToList();
        }

        public static void CaptureScreenshot(GameObject camera, string filename)
        {
            CaptureScreenshot(camera, filename, 4096, 4096, 60);
        }

        public static GameObject GetRootObject(GameObject obj)
        {   // 找到物体（因为有可能是物体的子物体，例如开关按钮）的最上层对象
            Transform current = obj.transform;
            while (current != null)
            {
                if (current.Find("MeshCenter") != null) // 检查是否有名为"meshCenter"的子对象
                {
                    return current.gameObject;
                }
                current = current.parent;
            }
            return null;
        }

        public static GameObject GetRootArmatureObject(GameObject obj)
        {   // 找到物体（因为有可能是物体的子物体，例如开关按钮）的最上层对象
            Transform current = obj.transform;
            while (current != null)
            {
                if (current.name == "PlayerArmature" || current.name == "PlaymateArmature") // 检查是否有名为"meshCenter"的子对象
                {
                    return current.gameObject;
                }
                current = current.parent;
            }
            return null;
        }

        public static void SetKinematic(GameObject obj, bool isKinematic)
        {
            Rigidbody rb = obj.GetComponent<Rigidbody>();
            if (rb != null)
            {
                MeshCollider meshCollider = obj.GetComponent<MeshCollider>();
                if (meshCollider != null) meshCollider.convex = !isKinematic;
                rb.isKinematic = isKinematic;
                if(!isKinematic){
                    rb.velocity = Vector3.zero;
                    rb.angularVelocity = Vector3.zero;
                }
            }

            foreach (Transform child in obj.transform)
            {
                SetKinematic(child.gameObject, isKinematic);
            }
        }

        public static Vector3 ClampVector3(Vector3 v, float extend)
        {
            return new Vector3(
                Mathf.Clamp(v.x, -extend, extend),
                Mathf.Clamp(v.y, -extend, extend),
                Mathf.Clamp(v.z, -extend, extend)
            );
        }

        public static void SetLayer(GameObject obj, string layerName)
        {
            obj.layer = LayerMask.NameToLayer(layerName);
            foreach (Transform child in obj.transform)
            {
                SetLayer(child.gameObject, layerName);
            }
        }

        public static Material CreateEnabledURPMaterial()
        {
            //return Resources.Load<Material>("FloorMaterial");
#if UNITY_URP
            Material material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
#else
            Material material = new Material(Shader.Find("HDRP/Lit"));
#endif

            // https://forum.unity.com/threads/get-list-of-shader-supported-keywords.1042093/
            // Shader myShader = material.shader; // Or however you get the shader in question.
            // string[] allViableLocalKeywords = myShader.keywordSpace.keywordNames;

            // Debug.Log(string.Join(", ", allViableLocalKeywords));
            // foreach (string keyword in allViableLocalKeywords)
            // {
            //     if(keyword=="INSTANCING_ON")continue;
            //     if(keyword.Contains("LIGHTMAP"))continue;
            //     material.EnableKeyword(keyword);
            // }

            // STEREO_INSTANCING_ON, UNITY_SINGLE_PASS_STEREO, STEREO_MULTIVIEW_ON, STEREO_CUBEMAP_RENDER_ON,
            // _MAIN_LIGHT_SHADOWS, _MAIN_LIGHT_SHADOWS_CASCADE, _MAIN_LIGHT_SHADOWS_SCREEN, _ADDITIONAL_LIGHTS_VERTEX,
            // _ADDITIONAL_LIGHTS, EVALUATE_SH_MIXED, EVALUATE_SH_VERTEX, _LIGHT_LAYERS, _FORWARD_PLUS,
            // _FOVEATED_RENDERING_NON_UNIFORM_RASTER, LIGHTMAP_SHADOW_MIXING, SHADOWS_SHADOWMASK, DIRLIGHTMAP_COMBINED,
            // LIGHTMAP_ON, DYNAMICLIGHTMAP_ON, DOTS_INSTANCING_ON, FOG_LINEAR, FOG_EXP, FOG_EXP2, INSTANCING_ON,
            // _NORMALMAP, _PARALLAXMAP, _RECEIVE_SHADOWS_OFF, _DETAIL_MULX2, _DETAIL_SCALED, _ADDITIONAL_LIGHT_SHADOWS,
            // _REFLECTION_PROBE_BLENDING, _REFLECTION_PROBE_BOX_PROJECTION, _SHADOWS_SOFT, _SHADOWS_SOFT_LOW,
            // _SHADOWS_SOFT_MEDIUM, _SHADOWS_SOFT_HIGH, _SCREEN_SPACE_OCCLUSION, _DBUFFER_MRT1, _DBUFFER_MRT2,
            // _DBUFFER_MRT3, _LIGHT_COOKIES, _WRITE_RENDERING_LAYERS, LOD_FADE_CROSSFADE, DEBUG_DISPLAY,
            // _SURFACE_TYPE_TRANSPARENT, _ALPHATEST_ON, _ALPHAPREMULTIPLY_ON, _ALPHAMODULATE_ON, _EMISSION,
            // _METALLICSPECGLOSSMAP, _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A, _OCCLUSIONMAP, _SPECULARHIGHLIGHTS_OFF,
            // _ENVIRONMENTREFLECTIONS_OFF, _SPECULAR_SETUP, _CASTING_PUNCTUAL_LIGHT_SHADOW, _RENDER_PASS_ENABLED,
            // _GBUFFER_NORMALS_OCT, EDITOR_VISUALIZATION, _SPECGLOSSMAP;
            // material.EnableKeyword("_NORMALMAP");
            // material.EnableKeyword("_PARALLAXMAP");
            // material.EnableKeyword("_METALLICSPECGLOSSMAP");
            // material.EnableKeyword("_OCCLUSIONMAP");
            // material.EnableKeyword("_SPECGLOSSMAP");

            // // material.EnableKeyword("_EMISSION");
            // material.EnableKeyword("_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A");
            // material.EnableKeyword("_ALPHATEST_ON");

            // material.EnableKeyword("_DETAIL_MULX2");
            // material.EnableKeyword("_DETAIL_SCALED");
            return material;
        }

        public static void DisableTextureMipmap(GameObject gameObject)
        {
            // https://forum.unity.com/threads/easy-way-to-make-texture-isreadable-true-by-script.1141915/
            Texture2D duplicateTexture(Texture2D source)
            {
                RenderTexture renderTex = RenderTexture.GetTemporary(
                            source.width,
                            source.height,
                            0,
                            RenderTextureFormat.Default,
                            RenderTextureReadWrite.sRGB);
                //RenderTextureReadWrite.Linear); // 这个颜色会变深

                Graphics.Blit(source, renderTex);
                RenderTexture previous = RenderTexture.active;
                RenderTexture.active = renderTex;
                Texture2D readableText = new Texture2D(source.width, source.height, TextureFormat.RGB24, false);
                readableText.ReadPixels(new Rect(0, 0, renderTex.width, renderTex.height), 0, 0);
                readableText.Apply();
                RenderTexture.active = previous;
                RenderTexture.ReleaseTemporary(renderTex);
                return readableText;
            }

            // mipmap会导致卡通猫身上有裂缝
            Renderer[] renderers = gameObject.GetComponentsInChildren<Renderer>();
            foreach (Renderer renderer in renderers)
            {
                Material[] materials = renderer.materials;
                foreach (Material material in materials)
                {
                    Texture texture;
                    List<string> propertyNames = new List<string> { "_MainTex", "_baseColorTexture" };
                    foreach (string propertyName in propertyNames)
                    {
                        if (material.HasProperty(propertyName))
                        {
                            texture = material.GetTexture(propertyName);
                            if (texture != null)
                            {
                                Texture2D newTexture = duplicateTexture((Texture2D)texture);
                                material.SetTexture(propertyName, newTexture);
                            }
                        }
                    }
                }
            }
        }

    }

    public class MyLogHandler : ILogHandler {
        private ILogHandler defaultLogHandler = Debug.unityLogger.logHandler;
    
        public void LogFormat(LogType logType, UnityEngine.Object context, string format, params object[] args) {
            // You can filter messages here by logType
            if (logType == LogType.Error) return; // Suppress all error messages
            
            defaultLogHandler.LogFormat(logType, context, format, args);
        }
    
        public void LogException(Exception exception, UnityEngine.Object context) {
            // Suppress exceptions or handle them differently
        }
    }

}
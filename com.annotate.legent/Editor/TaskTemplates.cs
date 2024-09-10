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
    public class TaskTemplates
    {
        public static HashSet<string> task_templates = new HashSet<string>(){
            "Put the apple into the fridge.",
        };
    }

}
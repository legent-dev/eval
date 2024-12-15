from legent import load_json

settings =load_json("F:/codes/github-LEGENT/eval/task_settings.json")
for setting in settings:
    print(setting["task_raw"]["task"])
#print(settings)
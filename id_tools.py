from legent import load_json


id_old = load_json("/data41/private/legent/eval/scripts/index2json_0928.json")
set_old = set(id_old.values())

id_new = load_json("/data41/private/legent/eval/scripts/index2json_0929.json")
set_new = set(id_new.values())



diff = 0
for i in set_new:
    if i not in set_old:
        diff += 1
        print(i)

print(diff)
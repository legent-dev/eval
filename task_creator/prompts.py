# Given a desciption of a skill and some example tasks, generate more tasks
SEED_GENERATE_PROMPT = """You are a smart household activity designer. You are to generate task templates that serve as reference by providing a structured format that can be replicated and customized. Given the examples, please brainstorm {num_examples} more task templates that realistically assess the agent's "{ability}" ability.

**Examples:**
{existing_examples}

**Requirements:**
1. Use varied language and creativity to enhance overal diversity of the templates instead of limiting your template to the example given. 
2. Limit the actions to complete the tasks to a set of basic actions {{'move around', 'grab', 'put on', 'put in', 'open', 'close'}} and excluing any other actions. 
3. Design the template with a clear, single solution to avoid ambiguity or multiple solutions.  

Directly return the new templates as a list of strings, starting with '['."""


QUESTION_GENERATE_PROMPT = """You are a smart household task designer. You are to brainstorm a task suitable in the house. The task should realistically assess the agent's "{ability}" ability. The task is a {task_type} task. The objects in the house are listed below.

**Template:**
{example_questions}

**Spatial Relations:**   
{spatial_relations}

**Requirements:**
1. The task should **strictly** follow the structure and design of the template and only replace the items. The template appears simple but subtly involves coherent multiple steps of reasoning or execution.
2. The task should **only** be accomplished by a sequence of simple actions. There are only three kinds of actions: (1) walking around (2) grabing one small object at a time (**lamp and chair are not graspable object**); (3) opening or closing the door of one large object. No any other actions should be involved. These actions should not be explicitly told to do but should be figuired out by the agent itself.
3. The task should only involve the listed objects and adhere to commonsense. Do not make the task weird.
4. There should be only one solution that reasonably and properly address the task.
5. Both the task and the solution should only be designed by reading the information from the spatial relations.
6. Do not tell the agent where to go to find an item.
7. Do not use left or right when describing relations.

**Instructions:**   
Generate one task to test exactly the "{ability}" ability, and then tell the deterministic solution of the task. Use the JSON format: {{"task": "", "solution":""}}. Now directly return the output starting with '{{'.
"""


QA_OPTION_GENERATE_PROMPT = """You are in a home environment. You are to complete the entire JSON structure of a given task by providing the options and correct answer of the question. You should strictly follow the the same JSON format as the example provided. 

**Example:**
{example}

**Task:**
{question}

**Potential Solution:**
{solution}

**List of Objects in Environment:**   
{object_description}

**Requirements:**
- The "task" must be an exact copy of the given task.
- The "options" must be **short** and clear to avoid ambiguity, overlap or multiple solutions. Add smart distractors to confuse the agent.
- The "object_id" means all objects involved in this task only as shown in the task and options.
- The "answer" is the correct answer from the options which fully and accurately adresses the question.
- The "answer" must be provided as the corresponding option number (e.g., 0, 1, 2, 3, 4). 
- The potential solution is only for reference. You should give your own correct answer.
"""


ACTION_OPTION_GENERATE_PROMPT = """You are in a home environment. You are to complete the entire JSON structure of a given task by providing the options of actions and correct solution of the task. You should strictly follow the the same JSON format as the example provided. 

**Example:**
{example}

**Task:**
{question}

**Description of Solution:**
{solution}

**List of Objects in Environment:**   
{object_description}

**Requirements:**
- The "task" must be an exact copy of the given task.
- The "object_id" means all objects involved in this task only as shown in the task and options.
- The "predicates" serve as judgment functions to determine "action" task completion. Use appropriate predicates, e.g., "grab 17" indicates the task is successful if the agent is holding item 17. Multiple predicates represent sequential sub-goals that must be achieved before the completion of the entire task.
- All "predicates" should be composed of "condition + object indexes," where conditions can only be chosen from the following set: {{'near', 'closer', 'further', 'not on', 'on', 'not in', 'in', 'grab', 'swap', 'open', 'closed', 'near_human'}}. For example, "in 17 23" means that object 17 is inside object 23, "near 35" indicates the robot is near object 35, and "near 12 24" means object 12 is near object 24.
- The "options" should **only** be limited to the following basic actions: {{'grab', 'put on', 'put in', 'open', 'close'}}. Do not include any other actions or combinations of actions. If the task does not involve any action within this list, the options should be empty [].
- Add at least two smart distractors to confuse the agent.
"""


HOUSEHOLD_NOUNS = [
    "broom", "dustpan", "vacuum", "bucket", "sponge", "cloth", "duster", "rag", "mop", "cleaner",
    "spray", "brush", "wiper", "shovel", "pail", "gloves", "towel", "soap", "detergent", "squeegee",
    "sponges", "scrubbers", "cleanser", "sponge", "toilet", "sink", "counter", "stove", "oven",
    "microwave", "dishwasher", "refrigerator", "freezer", "washer", "dryer", "iron", "ironing board", "laundry basket",
    "garbage can", "recycling bin", "compost bin", "disposal", "cleaning solution", "bleach", "vinegar", "baking soda",
    "plunger", "toilet brush", "air freshener", "deodorizer", "mop bucket", "dust cloth", "vacuum cleaner", "floor mat",
    "soap dispenser", "toilet paper", "paper towel", "hand sanitizer", "bleach", "window cleaner", "carpet", "rug",
    "floor", "tile", "wood", "laminate", "linoleum", "curtain", "blinds", "shade", "shower", "bathtub",
    "toothbrush holder", "soap dish", "tissue box", "laundry detergent", "fabric softener", "stain remover", "dish soap",
    "dish rack", "kitchen sponge", "scouring pad", "scrub brush", "dish towel", "pot", "pan", "baking sheet", "roasting pan",
    "microwave plate", "ice tray", "can opener", "peeler", "grater", "zester", "measuring cup", "measuring spoon",
    "timer", "thermometer", "pot holder", "oven mitt", "mixing bowl", "whisk", "spatula", "tongs", "ladle",
    "strainer", "colander", "pot rack", "pantry", "cabinet", "drawer", "shelf", "countertop", "island",
    "kitchen counter", "breakfast bar", "stool", "table", "chair", "barstool", "kitchen towel", "dish towel",
    "dishwasher detergent", "kitchen sink", "sink mat", "garbage disposal", "countertop cleaner", "stainless steel cleaner",
    "wood polish", "glass cleaner", "oven cleaner", "floor polish", "carpet cleaner", "drain cleaner", "air purifier",
    "humidifier", "dehumidifier", "fan", "heater", "air conditioner", "thermostat", "fire extinguisher", "first aid kit",
    "toolbox", "screwdriver", "hammer", "nails", "screws", "drill", "tape measure", "level", "wrench", "pliers",
    "ladder", "extension cord", "battery", "light bulb", "lamp", "chandelier", "ceiling fan", "smoke detector",
    "carbon monoxide detector", "doorbell", "lock", "key", "window", "door", "handle", "hinge", "lock", "doorknob",
    "bell", "mailbox", "doormat", "welcome mat", "umbrella stand", "coat rack", "shoe rack", "jacket", "scarf", "gloves",
    "hat", "boot", "umbrella", "raincoat", "backpack", "suitcase", "laundry room", "mudroom", "pantry shelf",
    "dish soap dispenser", "laundry detergent dispenser", "clothespin", "laundry line", "dryer sheet", "fabric spray",
    "shoe polish", "leather cleaner", "wooden spoon", "metal spoon", "plastic spoon", "ceramic plate", "glass plate",
    "plastic plate", "stainless steel plate", "ceramic bowl", "glass bowl", "plastic bowl", "stainless steel bowl",
    "cup", "mug", "glass", "tumbler", "wine glass", "beer mug", "coaster", "placemat", "napkin", "napkin holder",
    "salt shaker", "pepper grinder", "sugar bowl", "creamer", "butter dish", "breadbox", "spice rack", "tea kettle",
    "coffee maker", "blender", "toaster", "coffee grinder", "microwave oven", "slow cooker", "pressure cooker",
    "rice cooker", "electric skillet", "griddle", "wok", "baking dish", "cake pan", "pie dish", "cookie sheet",
    "bread pan", "pizza pan", "roasting rack", "meat thermometer", "oven thermometer", "pot rack", "utensil holder",
    "kitchen organizer", "spice jar", "tea bag holder", "toothpick", "toothpick holder", "ice bucket", "wine opener",
    "bottle opener", "canister", "food container", "storage jar", "vacuum sealer", "food wrap", "foil", "wax paper",
    "paper bag", "plastic bag", "canvas bag", "shopping bag", "reusable bag", "trash bag", "recycling bag", "compost bag",
    "cleaning caddy", "cleaning bucket", "squeegee", "floor brush", "hand brush", "dust mop", "dry mop", "wet mop",
    "steam mop", "broom and dustpan", "window squeegee", "carpet sweeper", "robot vacuum", "air freshener",
    "essential oil", "aromatherapy diffuser", "candles", "matches", "fireplace", "fireplace screen", "chimney brush",
    "shovel", "rake", "hoe", "garden trowel", "pruning shears", "garden fork", "watering can", "plant pot", "flower bed",
    "compost bin", "potted plant", "flower pot", "garden hose", "spade", "hedge trimmer", "lawn mower", "garden gloves",
    "weed killer", "pesticide", "plant food", "mulch", "garden shovel", "topsoil", "landscaping fabric", "garden tools",
    "fertilizer", "grass seed", "plant tray", "seedling", "watering nozzle", "soil tester", "sprinkler system",
    "garden gnome", "bird feeder", "bird bath", "fence", "trellis", "arbor", "garden path", "outdoor chair", "patio table",
    "deck", "balcony", "porch", "outdoor rug", "doormat", "welcome sign", "grill", "outdoor heater", "patio umbrella",
    "sun lounger", "outdoor cushions", "garden furniture", "patio light", "lantern", "fire pit", "outdoor rug",
    "picnic table", "barbecue", "chiminea", "outdoor storage", "planter box", "garden shed", "tool shed"
]



HOUSEHOLD_VERBS = [
    "vacuum", "sweep", "dust", "mop", "organize", "rearrange", "clean", "sanitize", "arrange", "sort",
    "shovel", "water", "fertilize", "prune", "polish", "scrub", "wipe", "wash", "scrape", "dry",
    "squeegee", "rotate", "adjust", "move", "realign", "stack", "straighten", "tidy", "clear", "dispose",
    "recycle", "arrange", "disinfect", "neaten", "sweep", "collect", "dispose", "clear", "hang", "remove",
    "replace", "retrieve", "locate", "find", "replace", "organize", "restock", "unclutter", "pick", "arrange",
    "fold", "wrap", "put", "arrange", "sort", "gather", "catalog", "check", "inspect", "rearrange",
    "lay", "stretch", "fold", "hang", "stretch", "fasten", "unfasten", "toggle", "assemble", "disassemble",
    "mount", "align", "calibrate", "sync", "recharge", "load", "unload", "prepare", "set", "clear",
    "adjust", "update", "organize", "refill", "refurbish", "decorate", "restore", "cleanse", "revise", "inspect",
    "handle", "manage", "fetch", "bring", "collect", "carry", "pass", "deliver", "store", "hold",
    "sift", "unpack", "pack", "fold", "unfold", "shrink", "expand", "secure", "release", "detach",
    "attach", "fold", "drain", "pour", "measure", "stir", "blend", "whisk", "shake", "chop",
    "slice", "grate", "peel", "crush", "grind", "churn", "knead", "separate", "combine", "marinate",
    "boil", "roast", "bake", "toast", "grill", "steam", "simmer", "heat", "cool", "defrost",
    "deodorize", "air", "freshen", "sanitize", "disinfect", "ventilate", "examine", "evaluate", "review", "check",
    "adjust", "operate", "service", "test", "renew", "refresh", "rearrange", "stabilize", "inspect", "polish",
    "unbox", "sort", "catalog", "rearrange", "organize", "sweep", "mop", "scrub", "dry", "sanitize",
    "de-clutter", "empty", "fill", "replace", "refill", "pack", "unpack", "wrap", "unwrap", "cleanse",
    "open", "close", "lock", "unlock", "seal", "unseal", "toggle", "slide", "push", "pull",
    "turn", "rotate", "shift", "move", "align", "adjust", "fasten", "unfasten", "secure", "release",
    "slide", "open", "shut", "lock", "unlock", "crack", "seal", "unseal", "toggle", "flip",
    "rotate", "turn", "change", "update", "install", "remove", "attach", "detach", "set", "reset",
    "operate", "test", "service", "calibrate", "configure", "sync", "maintain", "upgrade", "adjust", "clean",
    "clean", "replenish", "restore", "fix", "adjust", "upgrade", "replace", "renovate", "remodel", "restore",
    "refresh", "redecorate", "repaint", "fix", "touch-up", "maintain", "organize", "stow", "stack", "store",
    "arrange", "clear", "empty", "fill", "sort", "organize", "dispose", "recycle", "remove", "replace",
    "retrieve", "gather", "collect", "replenish", "refill", "pack", "unpack", "store", "organize", "catalog",
    "arrange", "sort", "classify", "clean", "sanitize", "disinfect", "freshen", "air", "deodorize", "ventilate",
    "refresh", "check", "inspect", "review", "cleanse", "polish", "shine", "dust", "wipe", "scrub",
    "sanitize", "disinfect", "deodorize", "refresh", "clean", "dry", "rinse", "wash", "vacuum", "sweep"
]


VERB_GENERATE_PROMPT = """
Brainstorm 500 verbs related to household activities. 1. The activities should be accomplished with three kinds of basic actions:(1) walking around (2) grabing one small object at a time (**lamp and chair are not graspable object**); (3) opening or closing the door of one large object. No any other actions should be involved. 2. The verbs should be as diversified as possible, like rinse off, retrieve, decorate... Now list your verbs as a Python list.
"""
# EmbodiedEval: Evaluate Multimodal LLMs as Embodied Agents

**EmbodiedEval** is a comprehensive and interactive benchmark designed to evaluate the capabilities of MLLMs in embodied tasks.

## Installation

#### Simulation Prerequisite

EmbodiedEval includes a 3D simulator for realtime simulation. You have two options to run the simulator:

(1) Run the simulator on your personal computer with a display (Windows/MacOS/Linux). No additional configuration is required. The subsequent installation and data download (approximately 20GB of space) will take place on your computer.

(2) Run the simulator on a Linux server, which requires sudo access, up-to-date NVIDIA drivers, and running outside a Docker container. Additional configurations are required as follows:
<details>
  <summary>Click to expand/collapse</summary>
Install Xorg:

```
sudo apt install -y gcc make pkg-config xorg
```

Generate .conf file:

```
sudo nvidia-xconfig --no-xinerama --probe-all-gpus --use-display-device=none
sudo cp /etc/X11/xorg.conf /etc/X11/xorg-0.conf
```

Edit /etc/X11/xorg-0.conf:

* Remove "ServerLayout" and "Screen" section.
* Set `BoardName` and `BusID` of "Device" section to the corresponding `Name` and `PCI BusID` of a GPU displayed by the `nvidia-xconfig --query-gpu-info` command. For example:
    ```
    Section "Device"
        Identifier     "Device0"
        Driver         "nvidia"
        VendorName     "NVIDIA Corporation"
        BusID          "PCI:164:0:0"
        BoardName      "NVIDIA GeForce RTX 3090"
    EndSection
    ```

Run Xorg:

```
sudo nohup Xorg :0 -config /etc/X11/xorg-0.conf &
```

Set the display (Remember to run the following command in every new terminal session before running the evaluation code):

```
export DISPLAY=:0
```
</details>

(3) TODO
```
ssh -N -L 50051:localhost:50051 host
legent launch
```

#### Install Dependencies

```bash
conda create -n embodiedeval python=3.10
conda activate embodiedeval
pip install -r requirements.txt
```

#### Download Dataset

```bash
python download.py
```


## Evaluation

#### Random Baseline

```bash
python run_eval.py --agent random --port 50051 --test_case_start=0 --test_case_end=328 --all
```

#### Human Baseline

```bash
python run_eval.py --agent human --port 50051 --test_case_start=0 --test_case_end=328 --all
```

In this mode, you can manually interact with the environment.
<details>
 <summary> How to play</summary>

Use the keyboard to press the corresponding number to choose an option;

Pressing W/A/D will map to the forward/turn left/turn right options in the menu;

Pressing Enter opens or closes the chat window, and you can enter option numbers greater than 9;

Pressing T will hide/show the options panel.
</details>

#### Creating a New Agent

`agent.py`  `AgentBase`.

`run_eval.py`



## Compute Metrics
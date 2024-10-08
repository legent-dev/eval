# EmbodiedEval

## 环境配置

#### 配环境

```bash
conda create -n legent python=3.10
conda activate legent
git clone https://github.com/thunlp/LEGENT.git
cd LEGENT
pip install -e .
legent download --dev --thu
```

```bash
cd ..
git clone git@github.com:legent-dev/eval.git
```

#### 下载场景文件

```bash
python download.py
```

场景文件会下载到EmbodiedEvalData/scenes文件夹，共24G。

#### 服务器渲染环境（有显示器的机器不需要）

以下两种方式二选一，有条件选gpu渲染

CPU渲染：

```bash
sudo apt install -y xorg-dev xvfb
```

GPU渲染：

```bash
sudo apt install -y gcc make pkg-config xorg
sudo nvidia-xconfig --no-xinerama --probe-all-gpus --use-display-device=none
<<<<<<< HEAD
sudo cp /etc/X11/xorg.conf /etc/X11/xorg-0.conf
=======
export DISPLAY=:7
>>>>>>> a7480c4d978f55d81a87dc2d3a601107be63f64a
```
编辑/etc/X11/xorg-0.conf,删掉ServerLayout和Screen Section

nvidia-xconfig --query-gpu-info查看busid和board id, 然后选一个gpu将其信息跳到Section "Device"
```
    BusID          "PCI:62:0:0"
	BoardName      "NVIDIA GeForce RTX 3090"
```
新建一个screen，运行Xorg :7 -config /etc/X11/xorg-0.conf

## 评测

#### Random Baseline

能运行这个就表示环境没有问题了。

```bash
python run_eval.py --agent random --max_steps 24 --max_images 25 --port 50051 --test_case_start=0 --all
```

#### 人类评测

```bash
python run_eval.py --agent human --max_steps 24 --max_images 25 --port 50051 --test_case_start=0 --all
```

#### gpt4o评测

```bash
python run_eval.py --agent gpt-4o --max_steps 24 --max_images 25 --port 50051 --test_case_start=0 --all
```

#### 评测其他模型

`agent.py` 里继承 `AgentBase` 实现你的Agent.

`run_eval.py`改成你的Agent.

#### 并行评测(TODO)

```python run_eval_multiprocess.py```


```
ssh -N -L 50051:localhost:50051 H100
legent launch
```
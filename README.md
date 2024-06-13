# eval

#### 配环境

```
conda create -n legent python=3.10
conda activate legent
git clone https://github.com/thunlp/LEGENT.git
cd LEGENT
pip install -e .
legent download --dev --thu
```

```
cd ..
git clone git@github.com:legent-dev/eval.git
```

#### 评测

`python download.py` 下载 `eval_folder_xxx.zip` 并解压，目前最新版是eval_folder_20240614_0251。

**查看eval.py里的TODO** `eval.py`的`eval_folder`路径改为对应路径；实现`YourAgentSimple`里的两个方法，并将`AgentGemini`改成你的Agent。

`python eval.py`，运行结果保存在eval_folder_xxx/results下。
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

`python download.py` 下载 `eval_folder_xxx.zip` 并解压，目前最新版是eval_folder_20240614_0251，`eval.py`的`eval_folder`路径改为对应路径.

`python run_eval.py --agent gpt-4o`，查看是否运行成功，运行结果保存在eval_folder_xxx/results下.

#### 并行评测

```python run_eval_multiprocess.py```

#### 评测其他模型

`agent.py` 里继承 `AgentBase` 实现你的Agent.

`run_eval.py`改成你的Agent.
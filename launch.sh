#!/bin/bash

# 定义本地端口
LOCAL_PORT=50051
# LOCAL_PORT=50052
# LOCAL_PORT=50053

REMOTE_HOST=H100

# 查找并杀掉现有的tunnel
lsof -ti :$LOCAL_PORT | xargs -r kill

# 启动新的SSH tunnel，后台运行
ssh -fN -L $LOCAL_PORT:localhost:$LOCAL_PORT $REMOTE_HOST

# 执行DISPLAY命令
DISPLAY=:7 $(python -c "from legent.environment.env_utils import validate_environment_path, get_default_env_path;print(validate_environment_path(get_default_env_path()))") \
    --width 640 --height 480 --port $LOCAL_PORT

# . launch.sh
# DISPLAY=:7 $(python -c "from legent.environment.env_utils import validate_environment_path, get_default_env_path;print(validate_environment_path(get_default_env_path()))") \
#     --width 640 --height 480 --port 50051
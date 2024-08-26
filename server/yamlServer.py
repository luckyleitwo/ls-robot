import yaml

# 读取 YAML 文件
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

import sys
import os
import toml


def load_config(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Конфигурационный файл не найден: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return toml.load(f)

def validate_config(config)
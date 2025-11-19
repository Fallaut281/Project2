import sys
import os
import toml


def load_config(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Конфигурационный файл не найден: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return toml.load(f)


def validate_config(config):
    errors = []

    #1. Имя анализируемого пакета
    if 'package_name' not in config:
        errors.append("Отсутствует обязательный параметр: package_name")
    elif not isinstance(config['package_name'], str) or not config['package_name'].strip():
        errors.append("package_name должен быть непустой строкой")

    #2. URL или путь к репозиторию
    if 'repository_url' not in config:
        errors.append("Отсутствует обязательный параметр: repository_url")
    elif not isinstance(config['repository_url'], str) or not config['repository_url'].strip():
        errors.append("repository_url должен быть непустой строкой")

    #3. Режим работы
    allowed_modes = {'online', 'offline'}
    if 'mode' not in config:
        errors.append("Отсутствует обязательный параметр: mode")
    elif not isinstance(config['mode'], str) or config['mode'].lower() not in allowed_modes:
        errors.append(f"mode должен быть одним из {allowed_modes}")

    #4. Версия пакета
    if 'package_version' not in config:
        errors.append("Отсутствует обязательный параметр: package_version")
    elif not isinstance(config['package_version'], str) or not config['package_version'].strip():
        errors.append("package_version должен быть непустой строкой")

    #5. Максимальная глубина
    if 'max_depth' not in config:
        errors.append("Отсутствует обязательный параметр: max_depth")
    elif not isinstance(config['max_depth'], int) or config['max_depth'] < 0:
        errors.append("max_depth должен быть неотрецательным целым числом")

    #6. Подстрока для фильтрации
    if 'filter_substring'in config and not isinstance(config['filter_substring'], str):
        errors.append("filter_substring должен быть строкой")

    return errors

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_config.toml>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except toml.TomlDecodeError as e:
        print(f"Error: Invalid TOML syntax in {config_path}: {e}", file=sys.stderr)
        sys.exit(1)

    errors = validate_config(config)
    if errors:
        print("Configuration validation failed:", file=sys.stderr)
        for err in errors:
            print(f"-{err}", file=sys.stderr)
        sys.exit(1)

    print(f"package_name = {config['package_name']!r}")
    print(f"repository_url = {config['repository_url']!r}")
    print(f"mode = {config['mode']!r}")
    print(f"package_version = {config['package_version']!r}")
    print(f"max_depth = {config['max_depth']!r}")
    print(f"filter_substring = {config.get('filter_substring', None)!r}")


if __name__ == "__main__":
    main()


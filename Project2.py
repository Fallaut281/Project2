import sys
import os
import toml


def load_config(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Конфигурационный файл не найден: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return toml.load(f)


def parse_packages_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    packages = []
    entries = content.split('\n---\n')

    for entry in entries:
        lines = [line.strip() for line in entry.splitlines() if line.strip()]
        pkg = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                pkg[key] = value
        if 'package' in pkg:
            packages.append(pkg)

    return packages


def find_package(packages, name, version):
    for pkg in packages:
        if pkg.get('package') == name and pkg.get('version') == version:
            return pkg
    return None


def extract_dependencies(pkg):
    deps_line = pkg.get('depends', '')
    if not deps_line:
        return []

    deps = [dep.strip() for dep in deps_line.split(',')]
    deps = [dep for dep in deps if dep]
    return deps


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

    repo_path = config['repository_url']
    pkg_name = config['package_name']
    pkg_version = config['package_version']

    packages_file_path = os.path.join(repo_path, 'Packages')

    if not os.path.isfile(packages_file_path):
        print(f"Error: Packages file not found at {packages_file_path}", file=sys.stderr)
        sys.exit(1)

    packages = parse_packages_file(packages_file_path)
    pkg = find_package(packages, pkg_name, pkg_version)

    if not pkg:
        print(f"Error: Package {pkg_name}={pkg_version} not found in repository.", file=sys.stderr)
        sys.exit(1)

    dependencies = extract_dependencies(pkg)

    print("Direct dependencies")
    for dep in dependencies:
        print(dep)


if __name__ == "__main__":
    main()


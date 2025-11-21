import sys
import os
import toml
from collections import deque

# Загружает конфигурационный файл TOML и возвращает его содержимое как словарь
def load_config(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Конфигурационный файл не найден: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return toml.load(f)

# Парсит файл Packages (в формате Ubuntu) и возвращает список пакетов
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

# Ищет пакет с заданным именем и версией в списке пакетов
def find_package(packages, name, version):
    for pkg in packages:
        if pkg.get('package') == name and pkg.get('version') == version:
            return pkg
    return None

# Извлекает зависимости из поля 'depends' пакета и возвращает их список
def extract_dependencies(pkg):
    deps_line = pkg.get('depends', '')
    if not deps_line:
        return []

    deps = [dep.strip() for dep in deps_line.split(',')]
    deps = [dep for dep in deps if dep]
    return deps

# Парсит тестовый файл с описанием графа (например, A -> B, C) и возвращает словарь
def parse_test_graph(filepath):
    graph = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '->' in line:
                node, deps_str = line.split('->', 1)
                node = node.strip()
                deps = [d.strip() for d in deps_str.split(',')]
                deps = [d for d in deps if d]
                graph[node] = deps
    return graph

# Строит граф зависимостей с помощью BFS, учитывая глубину и фильтрацию
def build_dependency_graph_bfs(start_package, max_depth, get_deps_func, filter_substring=None):
    graph = {}
    visited = set()
    queue = deque([(start_package, 0)])

    while queue:
        current_pkg, depth = queue.popleft()

        if depth > max_depth:
            continue

        if filter_substring and filter_substring in current_pkg:
            continue

        if current_pkg in visited:
            continue

        visited.add(current_pkg)

        deps = get_deps_func(current_pkg)
        graph[current_pkg] = deps

        if depth < max_depth:
            for dep in deps:
                if dep not in visited:
                    queue.append((dep, depth + 1))

    return graph

# Выполняет топологическую сортировку графа и возвращает порядок установки пакетов
def topological_sort(graph):
    in_degree = {}
    reverse_graph = {}

    for node in graph:
        in_degree[node] = 0
        reverse_graph[node] = []

    for node, deps in graph.items():
        for dep in deps:
            if dep not in reverse_graph:
                reverse_graph[dep] = []
                in_degree[dep] = 0
            reverse_graph[dep].append(node)
            in_degree[node] = in_degree.get(node, 0) + 1

    queue = deque()
    for node, deg in in_degree.items():
        if deg == 0:
            queue.append(node)

    result = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in reverse_graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(in_degree):
        return None, "Граф имеет цикл, топологическая сортировка невозможна"

    return result, None

# Проверяет, все ли обязательные параметры в конфиге указаны правильно
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

# Главная функция: загружает конфиг, строит граф, выводит зависимости и порядок установки
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
    max_depth = config['max_depth']
    filter_substring = config.get('filter_substring', None)

    mode = config['mode']

    if mode == 'test':
        graph_data = parse_test_graph(repo_path)
        def get_deps_func(name):
            return graph_data.get(name, [])

        graph = build_dependency_graph_bfs(pkg_name, max_depth, get_deps_func, filter_substring)
    else:
        packages_file_path = os.path.join(repo_path, 'Packages')
        if not os.path.isfile(packages_file_path):
            print(f"Error: Packages file not found at {packages_file_path}", file=sys.stderr)
            sys.exit(1)

        packages = parse_packages_file(packages_file_path)

        pkg_deps_map = {}
        for pkg in packages:
            name = pkg['package']
            deps = extract_dependencies(pkg)
            pkg_deps_map[name] = deps

        def get_deps_func(name):
            return pkg_deps_map.get(name, [])

        graph = build_dependency_graph_bfs(pkg_name, max_depth, get_deps_func, filter_substring)

    print("Dependency graph:")
    for pkg, deps in graph.items():
        print(f"{pkg} -> {', '.join(deps) if deps else '(no deps)'}")

    #4
    order, error = topological_sort(graph)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print("Порядок установки (топологическая сортировка):")
    for i, pkg in enumerate(order, 1):
        print(f"{i}. {pkg}")

    print("\nПримечание: Реальные менеджеры пакетов (например, apt) могут по-другому разрешать зависимости из-за:")
    print("- Ограничений по версиям (например, 'lib>=1.2')")
    print("- Виртуальных пакетов и альтернатив")
    print("- Предустановленных системных пакетов")
    print("- Правил разрешения конфликтов и политик установки")
    print("Наша простая модель не учитывает эти сложности.")


if __name__ == "__main__":
    main()
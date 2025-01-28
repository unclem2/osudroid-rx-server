import os
import importlib
import logging
import coloredlogs

coloredlogs.install(level=logging.INFO, format="[%(levelname)s] %(message)s")


def load_blueprints():
    modules = []
    base_dir = os.path.basename(os.path.dirname(__file__))
    for root, _, files in os.walk(os.path.dirname(__file__)):
        for file in files:
            if file == "__init__.py" or not file.endswith(".py"):
                continue

            path = f"{os.path.relpath(root)}.{file[:-3]}"
            import_path = path.replace("/", ".")
            filename = file[:-3]

            # Преобразуем имя, если это нужно

            try:
                module = importlib.import_module(import_path)
                if not hasattr(module, "bp"):
                    continue

                blueprint = module.bp
                # Формируем префикс, включая полный путь до файла
                path = os.path.relpath(root, start=os.path.dirname(__file__)).replace(
                    os.sep, "/"
                )
                path = path.replace("cho", "api").replace(".", "")
                blueprint.prefix = f"/{path}/{filename}"

                # Если модуль имеет атрибуты для настройки пути
                if hasattr(module, "php_file"):
                    blueprint.prefix += ".php"
                if hasattr(module, "forced_route"):
                    blueprint.prefix = module.forced_route

                logging.info(
                    f"✔ Loaded: {path.replace('.', '/')} → Route: {blueprint.prefix}"
                )
                modules.append(blueprint)
            except Exception as e:
                logging.error(f"✘ Failed to load: {import_path}")
                logging.error(f"  Reason: {e}")
    return modules

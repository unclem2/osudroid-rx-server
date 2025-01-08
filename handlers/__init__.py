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
            current_dir = os.path.basename(root)
            filename = file[:-3]

            if filename == "cho":
                filename = "api"
            if current_dir == "cho":
                current_dir = "api"
            if current_dir == filename:
                current_dir = ""

            try:
                module = importlib.import_module(import_path)
                if not hasattr(module, "bp"):
                    continue

                blueprint = module.bp
                blueprint.prefix = (
                    f"/{current_dir}/{filename}"
                    if current_dir != base_dir
                    else f"/{filename}/"
                )

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

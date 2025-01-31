import os
import importlib
import logging
import coloredlogs

coloredlogs.install(level=logging.INFO, format="[%(levelname)s] %(message)s")


def load_blueprints():
    modules = []
    base_dir = os.path.basename(os.path.dirname(__file__))
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == "__init__.py" or not file.endswith(".py"):
                continue

            path = os.path.join(root, file)[:-3]
            import_path = path.replace("/", ".")

        
            try:
                module = importlib.import_module(import_path)
                if not hasattr(module, "bp"):
                    continue

                blueprint = module.bp

                blueprint.prefix = path.replace(base_dir, "").replace("cho", "api")
                if hasattr(module, "php_file"):
                    blueprint.prefix += ".php"
                if hasattr(module, "forced_route"):
                    blueprint.prefix = module.forced_route

                logging.info(
                    f"✔ Loaded: {blueprint.prefix} → Route: {blueprint.prefix}"
                )
                modules.append(blueprint)
            except Exception as e:
                logging.error(f"✘ Failed to load: {import_path}")
                logging.error(f"  Reason: {e}")
    return modules

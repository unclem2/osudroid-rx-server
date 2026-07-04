import os
import importlib
import logging
import coloredlogs

coloredlogs.install(level=logging.INFO, format="[%(levelname)s] %(message)s")


def load_routers():
    modules = []
    base_dir = os.path.basename(os.path.dirname(__file__))
    hide_prefixes = ("multi", "cho", "user")
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == "__init__.py" or not file.endswith(".py"):
                continue

            path = os.path.join(root, file)[:-3]
            import_path = path.replace("/", ".")

            try:
                module = importlib.import_module(import_path)
                if not hasattr(module, "router"):
                    continue

                router = module.router
                prefix = path.replace(base_dir, "").replace("cho", "api")
                if hasattr(module, "php_file"):
                    prefix += ".php"
                if hasattr(module, "forced_route"):
                    prefix = module.forced_route

                if any(h in root for h in hide_prefixes):
                    for route in router.routes:
                        if hasattr(route, "include_in_schema"):
                            route.include_in_schema = False

                logging.info(
                    f"✔ Loaded: {prefix} → Route: {prefix}"
                )
                modules.append((router, prefix))
            except Exception as e:
                logging.error(f"✘ Failed to load: {import_path}")
                logging.error(f"  Reason: {e}")
    return modules

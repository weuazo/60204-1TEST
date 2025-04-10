import os
import importlib.util

class PluginLoader:
    """
    A class to dynamically load plugins from the plugins directory.

    Attributes:
        plugins_dir (str): The directory where plugins are stored.
        plugins (dict): A dictionary of loaded plugins.
    """

    def __init__(self, plugins_dir="plugins"):
        """
        Initialize the PluginLoader.

        Args:
            plugins_dir (str): The directory where plugins are stored. Defaults to "plugins".
        """
        self.plugins_dir = plugins_dir
        self.plugins = {}

    def load_plugins(self):
        """
        Load all plugins from the plugins directory.

        This method scans the plugins directory for Python files and attempts to load them as modules.
        """
        if not os.path.exists(self.plugins_dir):
            print(f"Plugins directory '{self.plugins_dir}' does not exist.")
            return

        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                plugin_name = filename[:-3]
                plugin_path = os.path.join(self.plugins_dir, filename)
                self._load_plugin(plugin_name, plugin_path)

    def _load_plugin(self, plugin_name, plugin_path):
        """
        Load a single plugin by name and path.

        Args:
            plugin_name (str): The name of the plugin.
            plugin_path (str): The file path to the plugin.
        """
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.plugins[plugin_name] = module
            print(f"Loaded plugin: {plugin_name}")
        except Exception as e:
            print(f"Failed to load plugin '{plugin_name}': {e}")

    def get_plugin(self, plugin_name):
        """
        Retrieve a loaded plugin by name.

        Args:
            plugin_name (str): The name of the plugin to retrieve.

        Returns:
            module: The loaded plugin module, or None if not found.
        """
        return self.plugins.get(plugin_name)

# Example usage
if __name__ == "__main__":
    loader = PluginLoader()
    loader.load_plugins()
    print("Available plugins:", loader.plugins.keys())
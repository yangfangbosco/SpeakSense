"""
Configuration Loader for SpeakSense
Loads and validates configuration from YAML file
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Singleton configuration loader"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load_config()

    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if config_path is None:
            # Default to config/config.yaml relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.yaml"

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key (e.g., 'asr.model_name')"""
        if self._config is None:
            self.load_config()

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        if self._config is None:
            self.load_config()

        return self._config.get(section, {})

    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration"""
        if self._config is None:
            self.load_config()
        return self._config


# Global config instance
config = ConfigLoader()

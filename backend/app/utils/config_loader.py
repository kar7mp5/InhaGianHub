import yaml
import os

def load_facility_config() -> dict:
    """
    Load facility URLs from config.yaml located in the same directory.

    Returns:
        dict: Dictionary of facility names and their URLs.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config.yaml")

    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config.get("facilities", {})

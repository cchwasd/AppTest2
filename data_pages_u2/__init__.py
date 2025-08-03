from types import SimpleNamespace

def process_page_class(page_class):
    """Process the page class to convert its attributes into dictionaries."""
    for attr_name, attr_value in vars(page_class).items():
        if isinstance(attr_value, type) and hasattr(attr_value, '__dict__'):
            # Convert inner class attributes to a dictionary
            processed_attrs = {
                k: v for k, v in vars(attr_value).items() if not k.startswith("__")
            }
            setattr(page_class, attr_name, SimpleNamespace(**processed_attrs))
    return page_class

# Import and process SettingsPage
from .settings_page import SettingsPage
SettingsPage = process_page_class(SettingsPage)

print(f"{vars(SettingsPage)=}")



try:
    from core import rz
except ImportError:
    import importlib.util
    import os
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location("SimpleSyntax", os.path.join(root, "__init__.py"), submodule_search_locations=[root])
    module = importlib.util.module_from_spec(spec)
    sys.modules["SimpleSyntax"] = module
    spec.loader.exec_module(module)
    rz = module.rz

__all__ = ["rz"]

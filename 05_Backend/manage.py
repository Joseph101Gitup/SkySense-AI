#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

def main():
    """Run administrative tasks."""
    # Ensure project root and 03_AI_Model are accessible
    backend_dir = Path(__file__).resolve().parent
    repo_root = backend_dir.parent
    ai_model_dir = repo_root / "03_AI_Model"
    
    for p in [str(backend_dir), str(ai_model_dir)]:
        if p not in sys.path:
            sys.path.insert(0, p)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skysense.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

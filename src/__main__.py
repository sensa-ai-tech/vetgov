"""Module entry point.

Allows `python -m src` to delegate to the CLI's main function.
This fixes pipeline reliability issues across different Python environments
where `python -m src.cli` might fail without an explicit module entrypoint.
"""
from src.cli import main

if __name__ == "__main__":
    main()

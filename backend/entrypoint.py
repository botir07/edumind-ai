#!/usr/bin/env python3
"""Placeholder backend entrypoint for container (runs migrations + uvicorn)."""
import subprocess
import sys


def main():
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    subprocess.run(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        check=True,
    )


if __name__ == "__main__":
    main()

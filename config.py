import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "database", "h2s_wristband.db"),
)

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "local-development-only-change-before-deploy",
)
import os

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
EXECUTION_MODE = "Local Deterministic Mode"


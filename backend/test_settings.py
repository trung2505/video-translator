import os
import sys

print("CWD:", os.getcwd())
print(".env exists:", os.path.exists(".env"))

if os.path.exists(".env"):
    with open(".env") as f:
        print("First line of .env:", f.readline().strip())

print("\n---\n")

try:
    from app.core.config import Settings
    s = Settings()
    print("✓ Settings created")
    print("DATABASE_URL:", s.DATABASE_URL)
    print("REDIS_URL:", s.REDIS_URL)
except Exception as e:
    import traceback
    print("Error:", type(e).__name__)
    print(traceback.format_exc())

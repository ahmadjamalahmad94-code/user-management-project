# Auto-split from app/legacy.py lines 11011-11015. Loaded by app.legacy.
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

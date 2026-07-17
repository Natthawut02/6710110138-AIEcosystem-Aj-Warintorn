import sys
import os

# Add the backend/ directory to the system path to allow importing core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

def main():
    print("=" * 55)
    print("  Backend Settings Configuration Verification")
    print("=" * 55)
    try:
        config_dict = settings.model_dump()
        for key, val in config_dict.items():
            # Check if it's sensitive and print it clearly
            if "PASSWORD" in key or "KEY" in key:
                print(f" {key:<25} : {val} (Sensitive)")
            else:
                print(f" {key:<25} : {val}")
        print("=" * 55)
        print(" SUCCESS: Configuration loaded successfully from environment!")
        print("=" * 55)
    except Exception as e:
        print(f" ERROR: Failed to load configuration: {e}")
        print("=" * 55)
        sys.exit(1)

if __name__ == "__main__":
    main()

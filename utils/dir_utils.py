# ==========================================
# IMPORTS
# ==========================================
import os
import shutil

# ==========================================
# FUNCTIONS
# ==========================================
def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return True
    return False

def clear_directory(path):
    if os.path.exists(path):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        return True
    return False

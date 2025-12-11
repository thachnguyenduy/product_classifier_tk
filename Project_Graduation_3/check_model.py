#!/usr/bin/env python3
# ============================================
# QUICK MODEL PATH CHECKER
# ============================================

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

print("=" * 60)
print("  MODEL PATH CHECKER")
print("=" * 60)

print(f"\n[Config] MODEL_PATH: {config.MODEL_PATH}")
print(f"[Config] MODEL_PARAM: {config.MODEL_PARAM}")
print(f"[Config] MODEL_BIN: {config.MODEL_BIN}")

# Check if model directory exists
model_dir = config.MODEL_PATH
print(f"\n[Check] Model directory: {model_dir}")

if os.path.exists(model_dir):
    print(f"  ✅ Directory exists")
    
    # List contents
    print(f"\n[Contents]")
    for item in os.listdir(model_dir):
        item_path = os.path.join(model_dir, item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path) / 1024  # KB
            print(f"  - {item} ({size:.1f} KB)")
        else:
            print(f"  - {item}/ (directory)")
    
    # Check param file
    param_path = os.path.join(model_dir, config.MODEL_PARAM)
    print(f"\n[Check] Param file: {config.MODEL_PARAM}")
    if os.path.exists(param_path):
        size = os.path.getsize(param_path) / 1024
        print(f"  ✅ Found ({size:.1f} KB)")
    else:
        print(f"  ❌ NOT FOUND!")
        print(f"  Expected: {param_path}")
    
    # Check bin file
    bin_path = os.path.join(model_dir, config.MODEL_BIN)
    print(f"\n[Check] Bin file: {config.MODEL_BIN}")
    if os.path.exists(bin_path):
        size = os.path.getsize(bin_path) / 1024 / 1024  # MB
        print(f"  ✅ Found ({size:.1f} MB)")
    else:
        print(f"  ❌ NOT FOUND!")
        print(f"  Expected: {bin_path}")
    
    # Final verdict
    print(f"\n" + "=" * 60)
    if os.path.exists(param_path) and os.path.exists(bin_path):
        print("  ✅ MODEL FILES READY!")
        print("=" * 60)
        print("\n✅ Model path is CORRECT!")
        print("✅ You can run the system now!")
        sys.exit(0)
    else:
        print("  ❌ MODEL FILES MISSING!")
        print("=" * 60)
        print("\n❌ Model files not found at expected locations.")
        print("\nPlease check:")
        print("  1. Model files are in the correct directory")
        print("  2. File names match config.py settings")
        sys.exit(1)
else:
    print(f"  ❌ Directory does NOT exist!")
    print(f"\n❌ Model directory not found: {model_dir}")
    print("\nPlease check:")
    print("  1. Model folder exists")
    print("  2. MODEL_PATH in config.py is correct")
    sys.exit(1)


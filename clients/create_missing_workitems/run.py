#!/usr/bin/env python3
"""
Run script for Create Missing Workitems client
Simply run: python run.py
Or double-click this file (if .py is associated with Python)
"""
import sys
import os
import subprocess

def main():
    """Run CreateMissingWorkItems with recommended parameters."""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 80)
    print("Create Missing WorkItems Client")
    print("=" * 80)
    print("Using: ../../data/create_missing_workitems_sample.csv")
    print("Parameters: --step-delay 2.0 --max-retries 2 --verbose")
    print("=" * 80)
    print()
    
    # Run with recommended parameters
    cmd = [
        sys.executable,  # Use current Python interpreter
        "CreateMissingWorkItems.py",
        "--step-delay", "2.0",
        "--max-retries", "2",
        "--verbose"
    ]
    
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError running script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")  # Pause so window doesn't close immediately

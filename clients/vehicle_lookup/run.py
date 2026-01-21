#!/usr/bin/env python3
"""
Run script for Vehicle Lookup client
Simply run: python run.py
Or double-click this file (if .py is associated with Python)
"""
import sys
import os
import subprocess

def main():
    """Run VehicleLookup with default parameters."""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 80)
    print("Vehicle Lookup Client")
    print("=" * 80)
    print("Input:  ../../data/vehicle_lookup_sample.csv")
    print("Output: VehicleLookup_results.csv")
    print("=" * 80)
    print()
    
    # Run main script
    cmd = [
        sys.executable,  # Use current Python interpreter
        "main.py"
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

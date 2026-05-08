#!/usr/bin/env python3
"""
Simple test script to validate the multi-agent research assistant structure
without requiring all dependencies to be installed.
"""

import os
import sys
import json
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        "main.py",
        "controller.py",
        "requirements.txt",
        "README.md",
        ".env.example",
        "agents/searchAgent.py",
        "agents/summarizeAgent.py",
        "agents/factCheckAgent.py",
        "agents/reportAgent.py",
        "services/geminiService.py",
        "services/storageService.py",
        "routes/researchRoutes.py",
        "utils/jsonDB.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def test_data_structure():
    """Test that data directories exist"""
    data_dirs = [
        "data",
        "data/users",
        "data/projects",
        "data/reports",
        "data/cache"
    ]

    missing_dirs = []
    for dir_path in data_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    else:
        print("✅ All data directories exist")
        return True

def test_json_structure():
    """Test JSON file creation and reading"""
    test_data = {
        "test": "value",
        "timestamp": "2026-05-08"
    }

    # Test writing
    test_file = Path("data/test.json")
    try:
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        print("✅ JSON writing works")
    except Exception as e:
        print(f"❌ JSON writing failed: {e}")
        return False

    # Test reading
    try:
        with open(test_file, 'r') as f:
            read_data = json.load(f)
        if read_data == test_data:
            print("✅ JSON reading works")
        else:
            print("❌ JSON data mismatch")
            return False
    except Exception as e:
        print(f"❌ JSON reading failed: {e}")
        return False

    # Clean up
    test_file.unlink()
    return True

def main():
    print("🔍 Testing Multi-Agent Research Assistant Structure")
    print("=" * 50)

    tests = [
        test_file_structure,
        test_data_structure,
        test_json_structure
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All structural tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up environment: cp .env.example .env")
        print("3. Add your GEMINI_API_KEY to .env")
        print("4. Run the app: python main.py")
    else:
        print("❌ Some tests failed. Please check the structure.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Modern build script for BillBox preprocessing Python extension
Uses setuptools directly without deprecated distutils
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """Check if required build dependencies are available"""
    required_packages = ['setuptools', 'wheel', 'pybind11', 'numpy']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is available")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} is missing")
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def clean_build():
    """Clean previous build artifacts"""
    build_dirs = ['build', 'dist', '*.egg-info']
    so_files = list(Path('.').glob('*.so'))
    
    for pattern in build_dirs:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                print(f"Removing directory: {path}")
                shutil.rmtree(path, ignore_errors=True)
            elif path.is_file():
                print(f"Removing file: {path}")
                path.unlink(missing_ok=True)
    
    for so_file in so_files:
        print(f"Removing shared library: {so_file}")
        so_file.unlink(missing_ok=True)

def build_extension():
    """Build the C++ extension using modern setuptools"""
    
    # Method 1: Try pip install (modern approach)
    print("Method 1: Building with pip install...")
    try:
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "--no-build-isolation",  # Use current environment
            "--editable", ".",        # Install in development mode
            "--verbose"               # Show build output
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Build successful with pip!")
            return True
        else:
            print("✗ Pip build failed, trying alternative method...")
            print("Pip error:", result.stderr[-500:])  # Show last 500 chars
    except Exception as e:
        print(f"✗ Pip build error: {e}")
    
    # Method 2: Try setup.py build_ext (fallback)
    print("\nMethod 2: Building with setup.py...")
    try:
        cmd = [sys.executable, "setup.py", "build_ext", "--inplace"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Build successful with setup.py!")
            print(result.stdout)
            return True
        else:
            print("✗ Setup.py build also failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Setup.py build error: {e}")
        return False

def verify_build():
    """Verify that the extension was built correctly"""
    try:
        import billbox_preprocessing
        print("✓ Module import successful!")
        
        # Test basic functionality
        config = billbox_preprocessing.create_invoice_config()
        print(f"✓ Configuration created: deskewing={config.enable_deskewing}")
        
        return True
    except ImportError as e:
        print(f"✗ Module import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Module test failed: {e}")
        return False

def check_source_files():
    """Check if all required source files exist"""
    required_files = [
        "src/python_bindings.cpp",
        "../preprocessing/src/image.cpp",
        "../preprocessing/src/grayscale.cpp",
        "../preprocessing/src/resize.cpp",
        "../preprocessing/src/contrast.cpp",
        "../preprocessing/src/filter.cpp",
        "../preprocessing/src/threshold.cpp",
        "../preprocessing/src/deskew.cpp",
        "../preprocessing/src/pipeline.cpp",
    ]
    
    required_headers = [
        "../preprocessing/include/image.h",
        "../preprocessing/include/pipeline.h",
        "../preprocessing/external/stb_image.h",
        "../preprocessing/external/stb_image_write.h",
    ]
    
    missing_files = []
    
    print("Checking source files...")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing_files.append(file_path)
    
    print("\nChecking header files...")
    for file_path in required_headers:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\nMissing files: {len(missing_files)}")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("✓ All source files found")
    return True

def main():
    """Main build process"""
    print("BillBox Preprocessing - Modern Build Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/python_bindings.cpp").exists():
        print("✗ Error: python_bindings.cpp not found!")
        print("Please run this script from the services/ocr directory")
        print("Current directory:", Path.cwd())
        return 1
    
    # Check if setup.py exists
    if not Path("setup.py").exists():
        print("✗ Error: setup.py not found!")
        print("Please ensure setup.py is in the current directory")
        return 1
    
    # Check all source files
    if not check_source_files():
        print("\n✗ Missing required source files!")
        print("Please ensure the preprocessing service is in ../preprocessing/")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Clean previous builds
    clean_build()
    
    # Build extension
    if not build_extension():
        print("\nBuild failed. Try alternative approaches:")
        print("1. pip install --upgrade setuptools wheel")
        print("2. python setup.py build_ext --inplace")
        print("3. Check that all C++ source files exist")
        return 1
    
    # Verify build
    if not verify_build():
        print("\nBuild completed but module verification failed")
        return 1
    
    print("\n" + "=" * 50)
    print("✓ Build completed successfully!")
    print("\nYou can now use the module:")
    print("  python billbox_ocr.py")
    print("  python test_python_bindings.py")
    
    # Show file locations
    print("\nFiles structure:")
    print("  services/ocr/")
    print("    ├── billbox_ocr.py (main OCR service)")
    print("    ├── test_python_bindings.py (test script)")
    print("    ├── src/python_bindings.cpp (C++ bindings)")
    print("    └── billbox_preprocessing.*.so (built extension)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
import os
import sys
from pathlib import Path
from setuptools import setup, Extension
import pybind11

# Modern approach using setuptools Extension instead of pybind11.setup_helpers
# This avoids the deprecated distutils dependency

def get_pybind_include():
    """Get pybind11 include directory"""
    return pybind11.get_include()

def get_extension():
    """Create the extension module configuration"""
    
    # Source files with correct paths
    sources = [
        "cpp/python_bindings.cpp",
        "../preprocessing/src/image.cpp",
        "../preprocessing/src/grayscale.cpp", 
        "../preprocessing/src/resize.cpp",
        "../preprocessing/src/contrast.cpp",
        "../preprocessing/src/filter.cpp",
        "../preprocessing/src/threshold.cpp",
        "../preprocessing/src/deskew.cpp",
        "../preprocessing/src/pipeline.cpp",
    ]
    
    # Include directories
    include_dirs = [
        "../preprocessing/include",
        "../preprocessing/external",
        get_pybind_include(),
    ]
    
    # Compiler flags
    extra_compile_args = [
        "-std=c++17",
        "-fvisibility=hidden",
    ]
    
    # Platform-specific flags
    if sys.platform == "darwin":  # macOS
        extra_compile_args.extend([
            "-mmacosx-version-min=10.15",
            "-stdlib=libc++",
        ])
    elif sys.platform.startswith("linux"):  # Linux
        extra_compile_args.extend([
            "-fPIC",
        ])
    
    # Define macros
    define_macros = [
        ("STB_IMAGE_IMPLEMENTATION", None),
        ("STB_IMAGE_WRITE_IMPLEMENTATION", None),
        ("VERSION_INFO", '"dev"'),
    ]
    
    # Create extension
    ext = Extension(
        "billbox_preprocessing",
        sources=sources,
        include_dirs=include_dirs,
        define_macros=define_macros,
        extra_compile_args=extra_compile_args,
        language="c++",
    )
    
    return ext

# Read long description from README
long_description = ""
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="billbox_preprocessing",
    version="1.0.0",
    author="BillBox Team",
    author_email="",
    description="C++ image preprocessing pipeline for OCR preparation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/billbox",
    ext_modules=[get_extension()],
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
    ],
    extras_require={
        "ocr": [
            "opencv-python>=4.5.0",
            "pytesseract>=0.3.8",
            "Pillow>=8.0.0",
        ],
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: C++",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="image-processing ocr preprocessing computer-vision",
    project_urls={
        "Bug Reports": "https://github.com/your-username/billbox/issues",
        "Source": "https://github.com/your-username/billbox",
        "Documentation": "https://github.com/your-username/billbox/blob/main/services/ocr/README.md",
    },
)
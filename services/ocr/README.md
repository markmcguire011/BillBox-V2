# BillBox OCR Service

This service provides OCR (Optical Character Recognition) capabilities for the BillBox invoice processing system, integrating C++ image preprocessing with Python OCR libraries.

## Quick Start

```bash
# 1. Install system dependencies (macOS)
brew install tesseract

# 2. Setup and build (automated)
cd services/ocr
./install.sh

# 3. Test installation
python billbox_ocr.py
```

**Alternative Quick Start:**
```bash
# Manual setup
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python build.py
```

For **Python 3.13+** users experiencing distutils errors, our modern build system automatically handles compatibility issues.

## Architecture

- **C++ Preprocessing**: High-performance image preprocessing pipeline (grayscale, deskewing, contrast enhancement, thresholding)
- **Python OCR**: pytesseract integration for text extraction
- **Pipeline Integration**: Seamless connection between preprocessing and OCR
- **Modern Packaging**: Compatible with Python 3.8-3.13, avoids deprecated distutils

## File Structure

```
services/ocr/
├── billbox_ocr.py              # Main OCR service module
├── test_python_bindings.py     # Test and demonstration script
├── build.py                    # Modern build script (avoids distutils)
├── install.sh                  # Automated installation script
├── setup.py                    # Python extension configuration
├── pyproject.toml              # Modern Python packaging configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── src/
│   └── python_bindings.cpp     # C++ Python bindings
└── venv/                       # Virtual environment (created during setup)

# Dependencies (C++ source code)
../preprocessing/
├── src/                        # C++ implementation files
│   ├── image.cpp               # Image I/O and structure
│   ├── pipeline.cpp            # Main preprocessing pipeline
│   ├── grayscale.cpp           # Grayscale conversion
│   ├── deskew.cpp              # Document deskewing
│   ├── threshold.cpp           # Image thresholding
│   └── ...                     # Other preprocessing modules
├── include/                    # C++ header files
│   ├── image.h
│   ├── pipeline.h
│   └── ...
└── external/                   # Third-party headers
    ├── stb_image.h             # Image loading
    └── stb_image_write.h       # Image saving
```

## Setup

### 1. System Requirements

- **Python**: 3.8 or higher (3.13+ recommended)
- **C++ Compiler**: Supporting C++17 standard
- **Tesseract OCR**: For text extraction

### 2. Install System Dependencies

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
sudo apt-get install build-essential python3-dev

# CentOS/RHEL
sudo yum install tesseract tesseract-langpack-eng
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

### 3. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel
```

### 4. Build C++ Python Extension

We provide multiple build methods to ensure compatibility with modern Python versions:

#### Method 1: Automated Installation Script (Recommended)

```bash
# One-command setup (handles everything)
./install.sh
```

#### Method 2: Using the Modern Build Script

```bash
# Install dependencies and build
pip install -r requirements.txt
python build.py
```

#### Method 3: Using pip (Modern Python Packaging)

```bash
# Install in development mode
pip install -e .

# Or install with OCR dependencies
pip install -e ".[ocr]"
```

#### Method 4: Using pyproject.toml (Standards-Based)

```bash
# Build and install using modern Python packaging
pip install --upgrade build
python -m build
pip install dist/*.whl
```

#### Method 5: Traditional setup.py (Fallback)

```bash
# Traditional method (if others fail)
python setup.py build_ext --inplace
```

### 5. Verify Installation

```bash
# Test the C++ module
python -c "import billbox_preprocessing; print('✓ C++ module loaded')"

# Test complete functionality and preprocessing pipeline
python test_python_bindings.py

# Test OCR service with invoice processing
python billbox_ocr.py
```

## Usage

### Basic OCR

```python
import cv2
from billbox_ocr import BillBoxOCR

# Initialize OCR service
ocr = BillBoxOCR(pipeline_type='invoice')

# Load image
image = cv2.imread('path/to/invoice.png')

# Extract text
result = ocr.extract_text(image)

if result.success:
    print(f"Extracted text: {result.text}")
    print(f"Confidence: {result.confidence}%")
    print(f"Skew angle: {result.preprocessing_stats['skew_angle']}°")
else:
    print(f"OCR failed: {result.error_message}")
```

### Invoice Data Extraction

```python
# Extract structured invoice data
invoice_data = ocr.extract_invoice_data(image)
print(f"Confidence: {invoice_data['confidence']}%")
print(f"Lines of text: {len(invoice_data['lines'])}")
```

### Batch Processing

```python
# Process multiple images
image_paths = ['invoice1.png', 'invoice2.jpg', 'invoice3.pdf']
results = ocr.process_batch(image_paths, output_dir='results')

for result in results:
    if result['success']:
        print(f"✓ {result['image_path']}: {result['confidence']}% confidence")
    else:
        print(f"✗ {result['image_path']}: {result['error']}")
```

### Pipeline Configuration

```python
# Use different preprocessing pipelines
ocr_invoice = BillBoxOCR(pipeline_type='invoice')     # Optimized for invoices
ocr_document = BillBoxOCR(pipeline_type='document')   # General documents
ocr_custom = BillBoxOCR(pipeline_type='custom')       # Custom settings
```

## C++ Preprocessing Pipeline

The preprocessing pipeline performs the following steps:

1. **Grayscale Conversion**: Luminance-based conversion for better text recognition
2. **Deskewing**: Automatic skew detection and correction using projection profile analysis
3. **Noise Reduction**: Optional median filtering for noisy images
4. **Contrast Enhancement**: Percentile normalization or histogram equalization
5. **Resizing**: Optional scaling for standardization
6. **Thresholding**: Otsu's method for binary image conversion

### Pipeline Configurations

- **Invoice Pipeline**: Optimized for invoice processing
  - Aggressive deskewing (±30°)
  - Strong contrast enhancement
  - Otsu thresholding
  - No noise reduction (preserves text quality)

- **Document Pipeline**: General document processing
  - Standard deskewing (±45°)
  - Moderate contrast enhancement
  - Light noise reduction
  - Adaptive thresholding options

## API Reference

### BillBoxOCR Class

#### Constructor
```python
BillBoxOCR(tesseract_config='--oem 3 --psm 6', 
           preprocessing_enabled=True, 
           pipeline_type='invoice')
```

#### Methods

- `extract_text(image) -> OCRResult`: Extract text from image
- `extract_invoice_data(image) -> Dict`: Extract structured invoice data
- `process_batch(image_paths, output_dir) -> List[Dict]`: Process multiple images
- `preprocess_image(image) -> Tuple[np.ndarray, Dict]`: Preprocess image only

### OCRResult Class

```python
@dataclass
class OCRResult:
    text: str                    # Extracted text
    confidence: float            # Average confidence score
    word_boxes: List[Dict]       # Word-level bounding boxes
    preprocessing_stats: Dict    # Preprocessing metadata
    success: bool               # Success flag
    error_message: str          # Error message if failed
```

## Performance

The C++ preprocessing pipeline provides significant performance improvements:

- **Speed**: 10-50x faster than equivalent Python image processing
- **Memory**: Lower memory usage for large images
- **Quality**: Optimized algorithms for document images

## Troubleshooting

### Modern Python Build Issues

#### Python 3.13+ and Distutils Deprecation

If you encounter `ModuleNotFoundError: No module named 'distutils'`:

```bash
# Use our modern build system (avoids distutils)
python build.py

# Or upgrade to modern packaging tools
pip install --upgrade setuptools>=61.0 wheel>=0.37.0

# Use pip instead of setup.py directly
pip install -e .
```

#### C++ Compilation Issues

```bash
# Ensure development tools are installed
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# For C++17 compatibility issues
export MACOSX_DEPLOYMENT_TARGET=10.15  # macOS
export CXXFLAGS="-std=c++17"           # Linux

# If filesystem errors occur (older systems)
export CXXFLAGS="-std=c++17 -DFILESYSTEM_EXPERIMENTAL"
```

#### pybind11 Build Failures

```bash
# Update pybind11 to latest version
pip install --upgrade "pybind11>=2.10.0"

# Use alternative build with verbose output
python setup.py build_ext --inplace --verbose

# Check compiler compatibility
python -c "import pybind11; print(pybind11.__version__)"
```

### Tesseract Issues

```bash
# Verify tesseract installation
tesseract --version

# Install additional language packs
# macOS
brew install tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr-all

# CentOS/RHEL
sudo yum install tesseract-langpack-*

# Test tesseract directly
echo "Hello World" | tesseract stdin stdout
```

### Module Import Issues

```bash
# Check if extension was built
ls -la *.so *.pyd  # .so on Unix, .pyd on Windows

# Verify Python environment
python -c "import sys; print('Python:', sys.version)"
python -c "import numpy; print('NumPy:', numpy.__version__)"

# Test C++ module import
python -c "
try:
    import billbox_preprocessing as bp
    print('✓ C++ module imported successfully')
    config = bp.create_invoice_config()
    print('✓ Basic functionality works')
except Exception as e:
    print('✗ Import failed:', e)
"
```

### Platform-Specific Issues

#### macOS Issues

```bash
# If you get "clang: error: unsupported option"
export MACOSX_DEPLOYMENT_TARGET=10.15
export CC=clang
export CXX=clang++

# For M1/M2 Macs with architecture issues
pip install --no-cache-dir --force-reinstall .
```

#### Windows Issues

```bash
# Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/

# Use conda for easier dependency management
conda install -c conda-forge pybind11 numpy opencv pytesseract

# Alternative: Use pre-compiled wheels
pip install --only-binary=all -r requirements.txt
```

#### Linux Issues

```bash
# For older Linux distributions
sudo apt-get install python3.8-dev  # Or your Python version
export CXXFLAGS="-std=c++17 -fPIC"

# If getting "No module named '_ctypes'"
sudo apt-get install libffi-dev

# For CentOS/RHEL 7 (older GCC)
sudo yum install centos-release-scl
sudo yum install devtoolset-8-gcc-c++
scl enable devtoolset-8 bash
```

### Performance Issues

```bash
# If OCR is slow, check tesseract config
python -c "
import pytesseract
print('Tesseract config examples:')
print('Fast: --oem 3 --psm 6')
print('Accurate: --oem 1 --psm 3')
print('Custom: --oem 3 --psm 6 -c tessedit_char_whitelist=0123456789')
"

# Monitor preprocessing performance
python -c "
import time
import billbox_preprocessing as bp
import numpy as np

# Create test image
img = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)

start = time.time()
result = bp.process_invoice_pipeline(img)
end = time.time()

print(f'Preprocessing time: {end-start:.3f}s')
print(f'Success: {result.success}')
"
```

### Getting Help

If you continue to have issues:

1. **Check our build script output**: `python build.py` provides detailed diagnostics
2. **Verify system requirements**: Ensure Python 3.8+, C++17 compiler, and Tesseract are properly installed
3. **Try different build methods**: Use the method that works best for your system
4. **Check dependencies**: Ensure all requirements.txt packages are installed
5. **Use verbose builds**: Add `--verbose` flags to see detailed error messages

## Integration with BillBox System

This OCR service is designed to integrate with the broader BillBox invoice processing system:

1. **Preprocessing Service**: Uses C++ pipeline for optimal image preparation
2. **OCR Service**: Extracts text and structured data
3. **Data Processing**: Feeds into invoice parsing and analysis pipeline
4. **API Integration**: Can be wrapped in REST API for microservice architecture

## Future Enhancements

- Deep learning-based text detection and recognition
- Handwriting recognition for handwritten invoices
- Table extraction and structure recognition
- Multi-language support optimization
- Real-time processing capabilities
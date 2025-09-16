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
- **Python OCR**: pytesseract integration with OpenCV preprocessing as primary method
- **Data Extraction**: Regex-based extraction of amounts, due dates, and vendor information
- **Unified Pipeline**: Complete invoice processing from image to API-ready data
- **Modern Packaging**: Compatible with Python 3.8-3.13, avoids deprecated distutils

## File Structure

```
services/ocr/
├── demo_pipeline.py            # Pipeline demonstration script
├── build.py                    # Modern build script (avoids distutils)
├── install.sh                  # Automated installation script
├── setup.py                    # Python extension configuration
├── pyproject.toml              # Modern Python packaging configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── src/
│   ├── pipeline.py             # Main invoice processing pipeline
│   ├── ocr_engine.py           # OCR engine with OpenCV/C++ preprocessing
│   └── extractor.py            # Data extraction (amount, due date, vendor)
├── tests/
│   ├── test_pipeline.py        # Pipeline integration tests
│   ├── test_ocr_engine.py      # OCR engine tests
│   └── test_extractor.py       # Data extraction tests
├── cpp/
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

### Quick Invoice Processing

```python
from src.pipeline import process_invoice_file

# Process a single invoice file (returns API-ready data)
result = process_invoice_file('path/to/invoice.png')

if result['success']:
    print(f"Amount: ${result['data']['amount']}")
    print(f"Due Date: {result['data']['due_date']}")
    print(f"Vendor: {result['data']['vendor']}")
    print(f"OCR Confidence: {result['metadata']['ocr_confidence']:.1f}%")
else:
    print(f"Error: {result['error']}")
```

### Complete Pipeline Usage

```python
from src.pipeline import InvoiceProcessor, create_invoice_processor
import cv2

# Create custom processor
processor = create_invoice_processor(
    require_amount=True,
    require_due_date=True,
    min_ocr_confidence=50.0
)

# Load and process image
image = cv2.imread('path/to/invoice.png')
result = processor.process_image(image, 'my_invoice')

# Get API-ready data
api_data = processor.get_api_ready_data(result)
print(api_data)
```

### OCR Engine Only

```python
from src.ocr_engine import OCREngine, OCRConfig

# Initialize OCR engine
config = OCRConfig(
    tesseract_config='--oem 3 --psm 6',
    pipeline_type='invoice',
    enable_preprocessing=True
)
ocr = OCREngine(config)

# Extract text only
result = ocr.extract_text(image)
if result.success:
    print(f"Text: {result.text}")
    print(f"Confidence: {result.confidence}%")
    print(f"Preprocessing: {result.preprocessing_stats}")
```

### Data Extraction Only

```python
from src.extractor import InvoiceExtractor

# Extract structured data from text
extractor = InvoiceExtractor()
extracted = extractor.extract("ACME Corp Invoice Total: $1,234.56 Due: 2024-02-15")

print(f"Amount: {extracted.amount}")
print(f"Due Date: {extracted.due_date}")
print(f"Vendor: {extracted.vendor}")
print(f"Confidence: {extracted.confidence_scores}")
```

### Batch Processing

```python
# Process multiple invoices
image_paths = ['invoice1.png', 'invoice2.jpg', 'invoice3.png']
results = processor.process_batch(image_paths)

for result in results:
    if result.processing_success:
        print(f"✓ Amount: ${result.amount}, Due: {result.due_date}")
    else:
        print(f"✗ Error: {result.error_message}")
```

### Pre-configured Processors

```python
from src.pipeline import DEFAULT_PROCESSOR, STRICT_PROCESSOR, LENIENT_PROCESSOR

# Default: requires amount only
result = DEFAULT_PROCESSOR.process_image(image)

# Strict: requires amount + due date, high confidence
result = STRICT_PROCESSOR.process_image(image)

# Lenient: no requirements, low confidence threshold
result = LENIENT_PROCESSOR.process_image(image)
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

### Pipeline Classes

#### InvoiceProcessor
Main pipeline orchestrator that combines OCR and data extraction.

```python
from src.pipeline import InvoiceProcessor, PipelineConfig

processor = InvoiceProcessor(config)
result = processor.process_image(image_data, source_info)
api_data = processor.get_api_ready_data(result)
```

**Methods:**
- `process_image(image_data, source_info) -> InvoiceData`
- `process_batch(image_sources) -> List[InvoiceData]`
- `get_api_ready_data(invoice_data) -> Dict`

#### OCREngine
Handles text extraction with preprocessing.

```python
from src.ocr_engine import OCREngine, OCRConfig

engine = OCREngine(config)
result = engine.extract_text(image)
```

**Methods:**
- `extract_text(image) -> OCRResult`
- `process_image_file(image_path) -> OCRResult`
- `batch_process(image_paths) -> List[OCRResult]`

#### InvoiceExtractor
Extracts structured data from text.

```python
from src.extractor import InvoiceExtractor

extractor = InvoiceExtractor()
data = extractor.extract(text)
```

**Methods:**
- `extract(text) -> ExtractedData`
- `extract_batch(texts) -> List[ExtractedData]`

### Data Classes

#### InvoiceData
Final processed invoice data ready for API consumption.

```python
@dataclass
class InvoiceData:
    amount: Optional[Decimal]           # Extracted amount
    due_date: Optional[datetime]        # Extracted due date
    vendor: Optional[str]               # Extracted vendor name
    ocr_text: str                       # Full OCR text
    ocr_confidence: float               # OCR confidence score
    extraction_confidence: Dict[str, float]  # Per-field confidence
    extraction_notes: List[str]         # Processing notes
    processing_success: bool            # Overall success flag
    processing_time_ms: float           # Processing time
    error_message: Optional[str]        # Error details
```

#### API Response Format
The `get_api_ready_data()` method returns data in this format:

```python
{
    'success': bool,                    # Processing success
    'data': {
        'amount': float,                # Dollar amount (or null)
        'due_date': str,                # ISO format date (or null)
        'vendor': str,                  # Vendor name (or null)
        'currency': str                 # Currency code (default: 'USD')
    },
    'metadata': {
        'ocr_confidence': float,        # OCR confidence percentage
        'extraction_confidence': {      # Per-field confidence scores
            'amount': float,
            'due_date': float,
            'vendor': float,
            'overall': float
        },
        'processing_time_ms': float,    # Total processing time
        'text_length': int,             # Length of extracted text
        'extraction_notes': List[str]   # Processing notes
    },
    'error': str                        # Error message (null if success)
}
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
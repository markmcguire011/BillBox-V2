#!/usr/bin/env python3
"""
Test script for BillBox preprocessing Python bindings
This demonstrates how to use the C++ pipeline with Python and pytesseract
"""

import numpy as np
import cv2
import sys
import os

try:
    import billbox_preprocessing as bp
    print("✓ Successfully imported billbox_preprocessing")
except ImportError as e:
    print(f"✗ Failed to import billbox_preprocessing: {e}")
    print("Make sure to build and install the Python module first:")
    print("  pip install pybind11")
    print("  python setup.py build_ext --inplace")
    sys.exit(1)

try:
    import pytesseract
    print("✓ pytesseract is available")
except ImportError:
    print("⚠ pytesseract not found - OCR testing will be skipped")
    print("Install with: pip install pytesseract")
    pytesseract = None

def load_test_image():
    """Load a test image"""
    # Try to load the example invoice (relative path from tests directory)
    test_image_paths = [
        "../../preprocessing/examples/Invoice Example 2.png",
        "../../preprocessing/examples/Invoice Example 1.png",
        "../../preprocessing/examples/Invoice Example 3.png",
    ]
    
    for test_image_path in test_image_paths:
        if os.path.exists(test_image_path):
            print(f"Loading test image: {test_image_path}")
            image = cv2.imread(test_image_path)
            if image is not None:
                # Convert BGR to RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                return image
    
    # Create a synthetic test image if no example is found
    print("Creating synthetic test image...")
    image = np.ones((400, 600, 3), dtype=np.uint8) * 255  # White background
    
    # Add some text-like patterns (black rectangles)
    image[50:70, 50:200] = 0    # Header line
    image[100:120, 50:150] = 0  # Text line 1
    image[130:150, 50:180] = 0  # Text line 2
    image[160:180, 50:120] = 0  # Text line 3
    image[210:230, 50:250] = 0  # Text line 4
    
    # Add some skew by rotating slightly
    center = (image.shape[1]//2, image.shape[0]//2)
    rotation_matrix = cv2.getRotationMatrix2D(center, 3, 1.0)  # 3 degree rotation
    image = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]), 
                          borderValue=(255, 255, 255))
    
    return image

def test_basic_functionality():
    """Test basic module functionality"""
    print("\n=== Testing Basic Functionality ===")
    
    # Test config creation
    config = bp.create_invoice_config()
    print(f"✓ Created invoice config: deskewing={config.enable_deskewing}, thresholding={config.enable_thresholding}")
    
    # Test custom config
    custom_config = bp.PipelineConfig()
    custom_config.enable_deskewing = True
    custom_config.enable_thresholding = True
    custom_config.save_intermediate_steps = True
    print("✓ Created custom config")
    
    return config, custom_config

def test_image_processing(image):
    """Test image processing functions"""
    print("\n=== Testing Image Processing ===")
    
    print(f"Input image shape: {image.shape}")
    
    # Test individual functions
    try:
        grayscale = bp.to_grayscale_luminance(image)
        print(f"✓ Grayscale conversion: {grayscale.shape}")
        
        # Estimate skew angle
        skew_angle = bp.estimate_skew_angle_projection(image)
        print(f"✓ Estimated skew angle: {skew_angle:.2f} degrees")
        
        # Test thresholding on grayscale
        if len(grayscale.shape) == 3 and grayscale.shape[2] == 1:
            # Remove channel dimension for thresholding
            gray_2d = grayscale.squeeze()
            gray_3d = np.expand_dims(gray_2d, axis=2)
            binary = bp.threshold_otsu(gray_3d)
            print(f"✓ Otsu thresholding: {binary.shape}")

        # Save intermediate image
        os.makedirs("../output", exist_ok=True)
        cv2.imwrite("../output/intermediate.png", binary)
        
        return True
    except Exception as e:
        print(f"✗ Error in individual processing: {e}")
        return False

def test_pipeline_processing(image, config):
    """Test the full pipeline"""
    print("\n=== Testing Pipeline Processing ===")
    
    try:
        # Test invoice pipeline
        result = bp.process_invoice_pipeline(image)
        
        if result.success:
            final_image = result.get_final_numpy()
            print(f"✓ Invoice pipeline succeeded")
            print(f"  Final image shape: {final_image.shape}")
            print(f"  Detected skew angle: {result.detected_skew_angle:.2f} degrees")
            print(f"  Otsu threshold: {result.otsu_threshold}")
            print(f"  Steps completed: {len(result.step_names)}")
            
            return final_image, result
        else:
            print(f"✗ Pipeline failed: {result.error_message}")
            return None, None
            
    except Exception as e:
        print(f"✗ Error in pipeline: {e}")
        return None, None

def test_ocr_integration(original_image, processed_image):
    """Test OCR with pytesseract"""
    if pytesseract is None:
        print("\n=== Skipping OCR Test (pytesseract not available) ===")
        return
    
    print("\n=== Testing OCR Integration ===")
    
    try:
        # Convert images for pytesseract (expects PIL format or file path)
        # Convert to PIL format via cv2
        
        # Original image OCR
        original_bgr = cv2.cvtColor(original_image, cv2.COLOR_RGB2BGR)
        original_text = pytesseract.image_to_string(original_bgr)
        
        # Processed image OCR
        if len(processed_image.shape) == 3:
            if processed_image.shape[2] == 1:
                # Grayscale
                processed_for_ocr = processed_image.squeeze()
            else:
                # Convert to grayscale
                processed_for_ocr = cv2.cvtColor(processed_image, cv2.COLOR_RGB2GRAY)
        else:
            processed_for_ocr = processed_image
            
        processed_text = pytesseract.image_to_string(processed_for_ocr)
        
        print("✓ OCR completed")
        print(f"Original text length: {len(original_text.strip())} characters")
        print(f"Processed text length: {len(processed_text.strip())} characters")
        
        if len(processed_text.strip()) > 0:
            print("Sample processed text:")
            print(processed_text[:200] + "..." if len(processed_text) > 200 else processed_text)
        
    except Exception as e:
        print(f"✗ OCR test failed: {e}")

def save_results(original_image, processed_image, result):
    """Save test results"""
    print("\n=== Saving Results ===")
    
    try:
        os.makedirs("../output", exist_ok=True)
        
        # Save original
        cv2.imwrite("../output/original.png", 
                   cv2.cvtColor(original_image, cv2.COLOR_RGB2BGR))
        
        # Save processed
        if len(processed_image.shape) == 3 and processed_image.shape[2] == 1:
            # Single channel
            cv2.imwrite("../output/processed.png", processed_image.squeeze())
        else:
            cv2.imwrite("../output/processed.png", 
                       cv2.cvtColor(processed_image, cv2.COLOR_RGB2BGR))
        
        # Save intermediate steps if available
        if result and result.intermediate_steps:
            for i, step_name in enumerate(result.step_names):
                step_image = result.get_intermediate_numpy(i)
                if len(step_image.shape) == 3 and step_image.shape[2] == 1:
                    step_image = step_image.squeeze()
                cv2.imwrite(f"../output/{step_name}.png", step_image)
        
        print("✓ Results saved to ../output/")
        
    except Exception as e:
        print(f"✗ Failed to save results: {e}")

def main():
    """Main test function"""
    print("BillBox Preprocessing Python Bindings Test")
    print("=" * 50)
    
    # Load test image
    image = load_test_image()
    if image is None:
        print("✗ Failed to load test image")
        return 1
    
    # Test basic functionality
    config, custom_config = test_basic_functionality()
    
    # Test individual processing functions
    if not test_image_processing(image):
        return 1
    
    # Test pipeline
    processed_image, result = test_pipeline_processing(image, config)
    if processed_image is None:
        return 1
    
    # Test OCR integration
    test_ocr_integration(image, processed_image)
    
    # Save results
    save_results(image, processed_image, result)
    
    print("\n" + "=" * 50)
    print("✓ All tests completed successfully!")
    print("\nUsage example in your Python code:")
    print("""
import billbox_preprocessing as bp
import cv2

# Load image
image = cv2.imread('path/to/invoice.png')
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Process for OCR
result = bp.process_invoice_pipeline(image)

if result.success:
    # Get processed image as numpy array
    processed = result.get_final_numpy()
    
    # Use with pytesseract
    import pytesseract
    text = pytesseract.image_to_string(processed)
    print(text)
""")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
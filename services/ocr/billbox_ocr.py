#!/usr/bin/env python3
"""
BillBox OCR Service - Main OCR processing module
Integrates C++ preprocessing pipeline with pytesseract OCR
"""

import numpy as np
import cv2
import pytesseract
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    import billbox_preprocessing as bp
    PREPROCESSING_AVAILABLE = True
except ImportError:
    PREPROCESSING_AVAILABLE = False
    print("Warning: billbox_preprocessing module not found. Install with: python setup.py build_ext --inplace")

@dataclass
class OCRResult:
    """Container for OCR results"""
    text: str
    confidence: float
    word_boxes: List[Dict]
    preprocessing_stats: Dict
    success: bool
    error_message: str = ""

class BillBoxOCR:
    """Main OCR class that combines preprocessing and OCR"""
    
    def __init__(self, 
                 tesseract_config: str = '--oem 3 --psm 6',
                 preprocessing_enabled: bool = True,
                 pipeline_type: str = 'invoice'):
        """
        Initialize OCR service
        
        Args:
            tesseract_config: Tesseract configuration string
            preprocessing_enabled: Whether to use C++ preprocessing
            pipeline_type: 'invoice', 'document', or 'custom'
        """
        self.tesseract_config = tesseract_config
        self.preprocessing_enabled = preprocessing_enabled and PREPROCESSING_AVAILABLE
        self.pipeline_type = pipeline_type
        
        if not self.preprocessing_enabled:
            print("Warning: Preprocessing disabled or unavailable")
    
    def preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Preprocess image using C++ pipeline
        
        Args:
            image: Input image as numpy array (BGR format from cv2)
            
        Returns:
            Tuple of (processed_image, stats)
        """
        if not self.preprocessing_enabled:
            # Basic preprocessing with OpenCV if C++ module unavailable
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return gray, {"method": "opencv_basic", "skew_angle": 0.0}
        
        # Convert BGR to RGB for our C++ module
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        try:
            if self.pipeline_type == 'invoice':
                result = bp.process_invoice_pipeline(rgb_image)
            elif self.pipeline_type == 'document':
                result = bp.process_document_pipeline(rgb_image)
            else:
                # Custom pipeline with default settings
                config = bp.PipelineConfig()
                result = bp.process_for_ocr(rgb_image, config)
            
            if result.success:
                processed_image = result.get_final_numpy()
                stats = {
                    "method": "cpp_pipeline",
                    "pipeline_type": self.pipeline_type,
                    "skew_angle": result.detected_skew_angle,
                    "otsu_threshold": result.otsu_threshold,
                    "steps_completed": result.step_names
                }
                
                # Convert single channel to grayscale if needed
                if len(processed_image.shape) == 3 and processed_image.shape[2] == 1:
                    processed_image = processed_image.squeeze()
                
                return processed_image, stats
            else:
                raise Exception(f"Preprocessing failed: {result.error_message}")
                
        except Exception as e:
            print(f"Preprocessing error: {e}")
            # Fallback to basic OpenCV preprocessing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return gray, {"method": "opencv_fallback", "error": str(e)}
    
    def extract_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract text from image using preprocessing + OCR
        
        Args:
            image: Input image as numpy array
            
        Returns:
            OCRResult object with text and metadata
        """
        try:
            # Preprocess image
            processed_image, preprocessing_stats = self.preprocess_image(image)
            
            # Run OCR
            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract word boxes
            word_boxes = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    word_boxes.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'bbox': (data['left'][i], data['top'][i], 
                                data['width'][i], data['height'][i])
                    })
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                word_boxes=word_boxes,
                preprocessing_stats=preprocessing_stats,
                success=True
            )
            
        except Exception as e:
            return OCRResult(
                text="",
                confidence=0.0,
                word_boxes=[],
                preprocessing_stats={},
                success=False,
                error_message=str(e)
            )
    
    def extract_invoice_data(self, image: np.ndarray) -> Dict:
        """
        Extract structured data from invoice image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary with extracted invoice fields
        """
        ocr_result = self.extract_text(image)
        
        if not ocr_result.success:
            return {"error": ocr_result.error_message}
        
        # Basic invoice data extraction (can be enhanced with regex patterns)
        lines = [line.strip() for line in ocr_result.text.split('\n') if line.strip()]
        
        invoice_data = {
            "raw_text": ocr_result.text,
            "confidence": ocr_result.confidence,
            "preprocessing_stats": ocr_result.preprocessing_stats,
            "lines": lines,
            "word_count": len(ocr_result.word_boxes),
            # Add more structured extraction here
        }
        
        return invoice_data
    
    def process_batch(self, image_paths: List[str], output_dir: str = "ocr_results") -> List[Dict]:
        """
        Process multiple images
        
        Args:
            image_paths: List of image file paths
            output_dir: Directory to save results
            
        Returns:
            List of results for each image
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, image_path in enumerate(image_paths):
            try:
                # Load image
                image = cv2.imread(image_path)
                if image is None:
                    raise Exception(f"Could not load image: {image_path}")
                
                # Extract text
                result = self.extract_text(image)
                
                # Save results
                filename = os.path.splitext(os.path.basename(image_path))[0]
                
                # Save text
                with open(os.path.join(output_dir, f"{filename}_text.txt"), 'w') as f:
                    f.write(result.text)
                
                # Save processed image if preprocessing was used
                if result.preprocessing_stats.get("method") == "cpp_pipeline":
                    processed_image, _ = self.preprocess_image(image)
                    cv2.imwrite(os.path.join(output_dir, f"{filename}_processed.png"), processed_image)
                
                results.append({
                    "image_path": image_path,
                    "text": result.text,
                    "confidence": result.confidence,
                    "preprocessing_stats": result.preprocessing_stats,
                    "success": result.success,
                    "error": result.error_message if not result.success else None
                })
                
                print(f"Processed {i+1}/{len(image_paths)}: {filename}")
                
            except Exception as e:
                results.append({
                    "image_path": image_path,
                    "text": "",
                    "confidence": 0.0,
                    "preprocessing_stats": {},
                    "success": False,
                    "error": str(e)
                })
                print(f"Error processing {image_path}: {e}")
        
        return results

def main():
    """Demo/test function"""
    print("BillBox OCR Service")
    print("=" * 50)
    
    # Initialize OCR service
    ocr = BillBoxOCR(pipeline_type='invoice')
    
    # Check if sample images exist
    sample_image_path = "../preprocessing/examples/Invoice Example 2.png"
    
    if os.path.exists(sample_image_path):
        print(f"Testing with: {sample_image_path}")
        
        # Load and process image
        image = cv2.imread(sample_image_path)
        result = ocr.extract_text(image)
        
        if result.success:
            print(f"\n✓ OCR completed successfully!")
            print(f"Confidence: {result.confidence:.1f}%")
            print(f"Word count: {len(result.word_boxes)}")
            print(f"Preprocessing: {result.preprocessing_stats.get('method', 'unknown')}")
            
            if 'skew_angle' in result.preprocessing_stats:
                print(f"Detected skew: {result.preprocessing_stats['skew_angle']:.2f}°")
            
            print("\nExtracted text preview:")
            print("-" * 30)
            preview = result.text[:500] + "..." if len(result.text) > 500 else result.text
            print(preview)
            
        else:
            print(f"✗ OCR failed: {result.error_message}")
    
    else:
        print(f"Sample image not found: {sample_image_path}")
        print("Place an invoice image in the preprocessing/examples/ folder to test")

if __name__ == "__main__":
    main()
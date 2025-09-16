#!/usr/bin/env python3
"""
Test suite for OCR Engine
Comprehensive tests to verify OCR functionality and ensure future compatibility
"""

import os
import sys
import cv2
import numpy as np
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from ocr_engine import (
        OCREngine, OCRConfig, OCRResult,
        create_ocr_engine,
        INVOICE_OCR_CONFIG, DOCUMENT_OCR_CONFIG, FAST_OCR_CONFIG
    )
    print("✓ Successfully imported OCR engine")
except ImportError as e:
    print(f"✗ Failed to import OCR engine: {e}")
    sys.exit(1)

try:
    import pytesseract
    # Test if tesseract is working
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
    print("✓ Tesseract OCR is available")
except Exception as e:
    TESSERACT_AVAILABLE = False
    print(f"⚠ Tesseract not available: {e}")


class TestOCREngine(unittest.TestCase):
    """Test cases for OCR Engine functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_images = {}
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test images
        self.test_images['simple_text'] = self._create_simple_text_image()
        self.test_images['invoice_like'] = self._create_invoice_like_image()
        self.test_images['noisy'] = self._create_noisy_image()
        self.test_images['skewed'] = self._create_skewed_image()
        
        # Save test images to temporary files
        self.test_files = {}
        for name, image in self.test_images.items():
            file_path = os.path.join(self.temp_dir, f"{name}.png")
            cv2.imwrite(file_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            self.test_files[name] = file_path
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_simple_text_image(self) -> np.ndarray:
        """Create a simple image with clear text"""
        image = np.ones((200, 600, 3), dtype=np.uint8) * 255  # White background
        
        # Add simple text-like rectangles
        cv2.rectangle(image, (50, 50), (250, 80), (0, 0, 0), -1)  # "INVOICE"
        cv2.rectangle(image, (50, 100), (180, 120), (0, 0, 0), -1)  # "Date:"
        cv2.rectangle(image, (200, 100), (320, 120), (0, 0, 0), -1)  # "2024-01-15"
        cv2.rectangle(image, (50, 140), (200, 160), (0, 0, 0), -1)  # "Amount:"
        cv2.rectangle(image, (220, 140), (300, 160), (0, 0, 0), -1)  # "$123.45"
        
        return image
    
    def _create_invoice_like_image(self) -> np.ndarray:
        """Create an invoice-like image with more complex layout"""
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255  # White background
        
        # Header
        cv2.rectangle(image, (50, 30), (300, 60), (0, 0, 0), -1)
        
        # Date and invoice number
        cv2.rectangle(image, (50, 80), (120, 100), (0, 0, 0), -1)
        cv2.rectangle(image, (130, 80), (250, 100), (0, 0, 0), -1)
        
        # Customer info
        cv2.rectangle(image, (50, 120), (180, 140), (0, 0, 0), -1)
        cv2.rectangle(image, (50, 150), (200, 170), (0, 0, 0), -1)
        cv2.rectangle(image, (50, 180), (180, 200), (0, 0, 0), -1)
        
        # Items table
        for i in range(3):
            y = 220 + i * 30
            cv2.rectangle(image, (50, y), (150, y + 20), (0, 0, 0), -1)  # Item
            cv2.rectangle(image, (200, y), (250, y + 20), (0, 0, 0), -1)  # Qty
            cv2.rectangle(image, (300, y), (380, y + 20), (0, 0, 0), -1)  # Price
        
        # Total
        cv2.rectangle(image, (300, 330), (380, 350), (0, 0, 0), -1)
        
        return image
    
    def _create_noisy_image(self) -> np.ndarray:
        """Create an image with noise to test preprocessing"""
        image = self._create_simple_text_image()
        
        # Add random noise
        noise = np.random.randint(0, 50, image.shape, dtype=np.uint8)
        image = cv2.add(image, noise)
        
        # Add some blur
        image = cv2.GaussianBlur(image, (3, 3), 0)
        
        return image
    
    def _create_skewed_image(self) -> np.ndarray:
        """Create a skewed image to test deskewing"""
        image = self._create_simple_text_image()
        
        # Apply rotation
        center = (image.shape[1] // 2, image.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, 5, 1.0)  # 5 degree rotation
        image = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]),
                              borderValue=(255, 255, 255))
        
        return image
    
    @unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract not available")
    def test_basic_ocr_functionality(self):
        """Test basic OCR functionality"""
        config = OCRConfig(enable_preprocessing=False)  # Test without preprocessing first
        engine = OCREngine(config)
        
        result = engine.extract_text(self.test_images['simple_text'])
        
        self.assertIsInstance(result, OCRResult)
        self.assertTrue(result.success, f"OCR failed: {result.error_message}")
        self.assertIsInstance(result.text, str)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 100.0)
    
    @unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract not available")
    def test_ocr_with_preprocessing(self):
        """Test OCR with C++ preprocessing enabled"""
        config = OCRConfig(enable_preprocessing=True, pipeline_type='invoice')
        engine = OCREngine(config)
        
        result = engine.extract_text(self.test_images['invoice_like'])
        
        self.assertTrue(result.success, f"OCR with preprocessing failed: {result.error_message}")
        self.assertIn('preprocessing_method', result.preprocessing_stats)
        
        # Should have some preprocessing stats
        if result.preprocessing_stats.get('preprocessing_method') == 'cpp_pipeline':
            self.assertIn('skew_angle', result.preprocessing_stats)
            self.assertIn('otsu_threshold', result.preprocessing_stats)
    
    @unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract not available")
    def test_word_and_line_boxes(self):
        """Test word and line box extraction"""
        config = OCRConfig(
            include_word_boxes=True,
            include_line_boxes=True,
            confidence_threshold=30.0
        )
        engine = OCREngine(config)
        
        result = engine.extract_text(self.test_images['simple_text'])
        
        self.assertTrue(result.success)
        self.assertIsInstance(result.word_boxes, list)
        self.assertIsInstance(result.line_boxes, list)
        
        # Check word box structure
        if result.word_boxes:
            word_box = result.word_boxes[0]
            required_keys = ['text', 'confidence', 'x', 'y', 'width', 'height']
            for key in required_keys:
                self.assertIn(key, word_box)
        
        # Check line box structure
        if result.line_boxes:
            line_box = result.line_boxes[0]
            required_keys = ['text', 'confidence', 'x', 'y', 'width', 'height']
            for key in required_keys:
                self.assertIn(key, line_box)
    
    @unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract not available")
    def test_file_processing(self):
        """Test processing image files"""
        engine = create_ocr_engine()
        
        result = engine.process_image_file(self.test_files['simple_text'])
        
        self.assertTrue(result.success, f"File processing failed: {result.error_message}")
        self.assertIsInstance(result.text, str)
    
    def test_file_not_found(self):
        """Test handling of non-existent files"""
        engine = create_ocr_engine()
        
        result = engine.process_image_file("non_existent_file.png")
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.error_message.lower())
    
    @unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract not available")
    def test_batch_processing(self):
        """Test batch processing of multiple images"""
        engine = create_ocr_engine()
        
        image_paths = [
            self.test_files['simple_text'],
            self.test_files['invoice_like']
        ]
        
        results = engine.batch_process(image_paths)
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsInstance(result, OCRResult)
    
    def test_configuration_presets(self):
        """Test predefined configuration presets"""
        # Test that configurations can be created
        configs = [INVOICE_OCR_CONFIG, DOCUMENT_OCR_CONFIG, FAST_OCR_CONFIG]
        
        for config in configs:
            self.assertIsInstance(config, OCRConfig)
            engine = OCREngine(config)
            self.assertIsInstance(engine, OCREngine)
    
    def test_preprocessing_fallback(self):
        """Test that OCR works even if C++ preprocessing is unavailable"""
        # Mock the billbox_preprocessing module as unavailable
        with patch.dict('sys.modules', {'billbox_preprocessing': None}):
            with patch('ocr_engine.PREPROCESSING_AVAILABLE', False):
                config = OCRConfig(enable_preprocessing=True)
                engine = OCREngine(config)
                
                # Should fall back to OpenCV preprocessing
                processed, stats = engine.preprocess_image(self.test_images['simple_text'])
                
                self.assertIsInstance(processed, np.ndarray)
                self.assertIn('preprocessing_method', stats)
                self.assertEqual(stats['preprocessing_method'], 'opencv_fallback')
    
    @unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract not available")
    def test_confidence_filtering(self):
        """Test confidence threshold filtering"""
        config = OCRConfig(
            include_word_boxes=True,
            confidence_threshold=80.0  # High threshold
        )
        engine = OCREngine(config)
        
        result = engine.extract_text(self.test_images['noisy'])  # Noisy image should have lower confidence
        
        self.assertTrue(result.success)
        # All returned words should meet confidence threshold
        for word_box in result.word_boxes:
            self.assertGreaterEqual(word_box['confidence'], 80.0)
    
    def test_different_pipeline_types(self):
        """Test different preprocessing pipeline types"""
        pipeline_types = ['invoice', 'document', 'custom']
        
        for pipeline_type in pipeline_types:
            config = OCRConfig(pipeline_type=pipeline_type)
            engine = OCREngine(config)
            
            # Should create engine without errors
            self.assertIsInstance(engine, OCREngine)
            self.assertEqual(engine.config.pipeline_type, pipeline_type)
    
    def test_invalid_image_handling(self):
        """Test handling of invalid images"""
        engine = create_ocr_engine()
        
        # Test with invalid image data
        invalid_image = np.array([])
        result = engine.extract_text(invalid_image)
        
        self.assertFalse(result.success)
        self.assertIn("error", result.error_message.lower())


class TestOCREngineIntegration(unittest.TestCase):
    """Integration tests for OCR Engine with real scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_realistic_invoice(self) -> np.ndarray:
        """Create a more realistic invoice image with text-like patterns"""
        image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        
        # Company header
        cv2.putText(image, "ACME CORPORATION", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "123 Business Street", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "City, State 12345", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Invoice details
        cv2.putText(image, "INVOICE", (600, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.putText(image, "Invoice #: 2024-001", (500, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Date: 2024-01-15", (500, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Customer info
        cv2.putText(image, "Bill To:", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "John Doe", (50, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "456 Customer Ave", (50, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Items
        cv2.putText(image, "Description", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Qty", (400, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Price", (500, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Total", (600, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        cv2.putText(image, "Web Development Services", (50, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(image, "1", (400, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(image, "$1000.00", (500, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(image, "$1000.00", (600, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Total
        cv2.putText(image, "TOTAL: $1000.00", (500, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        return image
    
    @unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract not available")
    def test_realistic_invoice_processing(self):
        """Test processing of a realistic invoice"""
        invoice_image = self._create_realistic_invoice()
        
        # Test with invoice-optimized configuration
        engine = OCREngine(INVOICE_OCR_CONFIG)
        result = engine.extract_text(invoice_image)
        
        self.assertTrue(result.success, f"Realistic invoice OCR failed: {result.error_message}")
        
        # Check that we extracted some meaningful text
        text_lower = result.text.lower()
        expected_terms = ['invoice', 'total', 'date']
        found_terms = [term for term in expected_terms if term in text_lower]
        
        # Should find at least some expected invoice terms
        self.assertGreater(len(found_terms), 0, f"Expected invoice terms not found in: {result.text}")
    
    @unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract not available")
    def test_preprocessing_impact(self):
        """Test the impact of preprocessing on OCR accuracy"""
        invoice_image = self._create_realistic_invoice()
        
        # Add some noise and skew to make preprocessing more valuable
        noisy_image = cv2.add(invoice_image, np.random.randint(0, 30, invoice_image.shape, dtype=np.uint8))
        center = (noisy_image.shape[1] // 2, noisy_image.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, 3, 1.0)
        skewed_image = cv2.warpAffine(noisy_image, rotation_matrix, 
                                     (noisy_image.shape[1], noisy_image.shape[0]),
                                     borderValue=(255, 255, 255))
        
        # Test without preprocessing
        config_no_prep = OCRConfig(enable_preprocessing=False)
        engine_no_prep = OCREngine(config_no_prep)
        result_no_prep = engine_no_prep.extract_text(skewed_image)
        
        # Test with preprocessing
        config_with_prep = OCRConfig(enable_preprocessing=True, pipeline_type='invoice')
        engine_with_prep = OCREngine(config_with_prep)
        result_with_prep = engine_with_prep.extract_text(skewed_image)
        
        # Both should succeed, but preprocessing might improve confidence or text quality
        self.assertTrue(result_no_prep.success)
        self.assertTrue(result_with_prep.success)
        
        # Log results for manual inspection
        print(f"\nWithout preprocessing - Confidence: {result_no_prep.confidence:.1f}%, Text length: {len(result_no_prep.text)}")
        print(f"With preprocessing - Confidence: {result_with_prep.confidence:.1f}%, Text length: {len(result_with_prep.text)}")


def create_demo_output():
    """Create demonstration output showing OCR capabilities"""
    if not TESSERACT_AVAILABLE:
        print("Tesseract not available - skipping demo")
        return
    
    print("\n" + "="*60)
    print("OCR ENGINE DEMONSTRATION")
    print("="*60)
    
    # Create test image
    image = np.ones((300, 500, 3), dtype=np.uint8) * 255
    cv2.putText(image, "SAMPLE INVOICE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(image, "Date: 2024-01-15", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(image, "Amount: $123.45", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(image, "Customer: John Doe", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(image, "Total: $123.45", (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Test different configurations
    configurations = [
        ("Invoice Optimized", INVOICE_OCR_CONFIG),
        ("Document General", DOCUMENT_OCR_CONFIG),
        ("Fast Processing", FAST_OCR_CONFIG)
    ]
    
    for name, config in configurations:
        print(f"\n{name} Configuration:")
        print("-" * 40)
        
        engine = OCREngine(config)
        result = engine.extract_text(image)
        
        if result.success:
            print(f"✓ OCR Success - Confidence: {result.confidence:.1f}%")
            print(f"Extracted text: {repr(result.text[:100])}")
            print(f"Word boxes found: {len(result.word_boxes)}")
            print(f"Line boxes found: {len(result.line_boxes)}")
            print(f"Preprocessing: {result.preprocessing_stats.get('preprocessing_method', 'none')}")
        else:
            print(f"✗ OCR Failed: {result.error_message}")


def main():
    """Main test runner"""
    print("BillBox OCR Engine Test Suite")
    print("=" * 50)
    
    # Run the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestOCREngine))
    suite.addTests(loader.loadTestsFromTestCase(TestOCREngineIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Create demonstration
    create_demo_output()
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'✓ PASSED' if success else '✗ FAILED'}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
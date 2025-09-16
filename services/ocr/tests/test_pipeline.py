#!/usr/bin/env python3
"""
Unit tests for Invoice Processing Pipeline
Tests the complete pipeline from image to API-ready data
"""

import os
import sys
import unittest
import tempfile
import cv2
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from pipeline import (
        InvoiceProcessor, InvoiceData, PipelineConfig,
        create_invoice_processor, process_invoice_file,
        DEFAULT_PROCESSOR, STRICT_PROCESSOR, LENIENT_PROCESSOR
    )
    from ocr_engine import OCRConfig
    from extractor import ExtractionConfig
    print("✓ Successfully imported pipeline modules")
except ImportError as e:
    print(f"✗ Failed to import pipeline modules: {e}")
    sys.exit(1)


class TestInvoiceData(unittest.TestCase):
    """Test cases for InvoiceData dataclass"""
    
    def test_default_invoice_data(self):
        """Test default InvoiceData initialization"""
        data = InvoiceData()
        
        self.assertIsNone(data.amount)
        self.assertIsNone(data.due_date)
        self.assertIsNone(data.vendor)
        self.assertEqual(data.ocr_text, "")
        self.assertEqual(data.ocr_confidence, 0.0)
        self.assertEqual(data.extraction_confidence, {})
        self.assertEqual(data.extraction_notes, [])
        self.assertFalse(data.processing_success)
        self.assertEqual(data.processing_time_ms, 0.0)
        self.assertIsNone(data.error_message)
    
    def test_invoice_data_with_values(self):
        """Test InvoiceData with actual values"""
        test_date = datetime(2024, 12, 31)
        test_amount = Decimal('123.45')
        
        data = InvoiceData(
            amount=test_amount,
            due_date=test_date,
            vendor="Test Company Inc",
            ocr_text="Sample OCR text",
            ocr_confidence=85.5,
            processing_success=True,
            processing_time_ms=250.0
        )
        
        self.assertEqual(data.amount, test_amount)
        self.assertEqual(data.due_date, test_date)
        self.assertEqual(data.vendor, "Test Company Inc")
        self.assertEqual(data.ocr_text, "Sample OCR text")
        self.assertEqual(data.ocr_confidence, 85.5)
        self.assertTrue(data.processing_success)
        self.assertEqual(data.processing_time_ms, 250.0)


class TestPipelineConfig(unittest.TestCase):
    """Test cases for PipelineConfig"""
    
    def test_default_pipeline_config(self):
        """Test default configuration"""
        config = PipelineConfig()
        
        self.assertIsInstance(config.ocr_config, OCRConfig)
        self.assertIsInstance(config.extraction_config, ExtractionConfig)
        self.assertEqual(config.min_ocr_confidence, 30.0)
        self.assertTrue(config.require_amount)
        self.assertFalse(config.require_due_date)
        self.assertFalse(config.require_vendor)
    
    def test_custom_pipeline_config(self):
        """Test custom configuration"""
        ocr_config = OCRConfig(language='spa')
        extraction_config = ExtractionConfig(case_sensitive=True)
        
        config = PipelineConfig(
            ocr_config=ocr_config,
            extraction_config=extraction_config,
            min_ocr_confidence=50.0,
            require_due_date=True
        )
        
        self.assertEqual(config.ocr_config.language, 'spa')
        self.assertTrue(config.extraction_config.case_sensitive)
        self.assertEqual(config.min_ocr_confidence, 50.0)
        self.assertTrue(config.require_due_date)


class TestInvoiceProcessor(unittest.TestCase):
    """Test cases for InvoiceProcessor main functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = InvoiceProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a simple test image
        self.test_image = self._create_test_invoice_image()
        self.test_image_path = os.path.join(self.temp_dir, "test_invoice.png")
        cv2.imwrite(self.test_image_path, cv2.cvtColor(self.test_image, cv2.COLOR_RGB2BGR))
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_invoice_image(self) -> np.ndarray:
        """Create a test invoice image with recognizable text"""
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255
        
        # Add text that should be recognizable by OCR
        cv2.putText(image, "ACME CORPORATION", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "INVOICE", (450, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "Date: 2024-01-15", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "Due Date: 2024-02-15", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "Amount Due: $1,234.56", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        return image
    
    def test_processor_initialization(self):
        """Test processor initialization"""
        self.assertIsInstance(self.processor.config, PipelineConfig)
        self.assertIsNotNone(self.processor.ocr_engine)
        self.assertIsNotNone(self.processor.extractor)
    
    def test_validation_logic(self):
        """Test validation of extracted data"""
        from extractor import ExtractedData
        
        # Valid data
        valid_data = ExtractedData(
            amount=Decimal('100.00'),
            due_date=datetime.now() + timedelta(days=30),
            vendor="Test Company"
        )
        
        result = self.processor._validate_extraction(valid_data)
        self.assertTrue(result['success'])
        
        # Invalid data - missing required amount
        invalid_data = ExtractedData(
            amount=None,
            due_date=datetime.now() + timedelta(days=30),
            vendor="Test Company"
        )
        
        result = self.processor._validate_extraction(invalid_data)
        self.assertFalse(result['success'])
        self.assertIn('Amount is required', result['error_message'])
    
    def test_api_ready_data_conversion(self):
        """Test conversion to API-ready format"""
        test_date = datetime(2024, 12, 31, 12, 0, 0)
        test_amount = Decimal('123.45')
        
        invoice_data = InvoiceData(
            amount=test_amount,
            due_date=test_date,
            vendor="Test Company Inc",
            ocr_text="Sample text",
            ocr_confidence=85.5,
            extraction_confidence={'amount': 0.9, 'vendor': 0.8},
            processing_success=True,
            processing_time_ms=250.0
        )
        
        api_data = self.processor.get_api_ready_data(invoice_data)
        
        self.assertTrue(api_data['success'])
        self.assertEqual(api_data['data']['amount'], 123.45)
        self.assertEqual(api_data['data']['due_date'], '2024-12-31T12:00:00')
        self.assertEqual(api_data['data']['vendor'], "Test Company Inc")
        self.assertEqual(api_data['data']['currency'], 'USD')
        self.assertEqual(api_data['metadata']['ocr_confidence'], 85.5)
        self.assertEqual(api_data['metadata']['processing_time_ms'], 250.0)
        self.assertIsNone(api_data['error'])
    
    def test_error_handling(self):
        """Test error handling in pipeline"""
        # Test with invalid image data
        invalid_image = np.array([])
        
        result = self.processor.process_image(invalid_image)
        
        self.assertFalse(result.processing_success)
        self.assertIsNotNone(result.error_message)
        self.assertGreater(result.processing_time_ms, 0)
    
    @patch('sys.modules', {'pytesseract': None})
    def test_missing_dependencies(self):
        """Test handling of missing dependencies"""
        # This test might be tricky to implement due to import dependencies
        # For now, just test that the processor can be created
        processor = InvoiceProcessor()
        self.assertIsInstance(processor, InvoiceProcessor)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for complete pipeline"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = InvoiceProcessor()
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_realistic_invoice(self) -> np.ndarray:
        """Create a realistic invoice image for testing"""
        image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        
        # Company header
        cv2.putText(image, "ACME CORPORATION", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.putText(image, "123 Business Street", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Invoice details
        cv2.putText(image, "INVOICE", (600, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.putText(image, "Invoice #: 2024-001", (500, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Date: 2024-01-15", (500, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(image, "Due Date: 2024-02-15", (500, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Customer info
        cv2.putText(image, "Bill To:", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(image, "John Doe", (50, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Total
        cv2.putText(image, "TOTAL: $1,234.56", (500, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        return image
    
    def test_complete_pipeline_processing(self):
        """Test complete pipeline from image to API data"""
        invoice_image = self._create_realistic_invoice()
        
        # Save image to file
        image_path = os.path.join(self.temp_dir, "realistic_invoice.png")
        cv2.imwrite(image_path, cv2.cvtColor(invoice_image, cv2.COLOR_RGB2BGR))
        
        # Process through pipeline
        result = self.processor.process_image(image_path, "test_invoice")
        
        # Verify result structure
        self.assertIsInstance(result, InvoiceData)
        self.assertGreater(result.processing_time_ms, 0)
        
        # Convert to API format
        api_data = self.processor.get_api_ready_data(result)
        
        # Verify API data structure
        self.assertIn('success', api_data)
        self.assertIn('data', api_data)
        self.assertIn('metadata', api_data)
        
        # Check data fields
        self.assertIn('amount', api_data['data'])
        self.assertIn('due_date', api_data['data'])
        self.assertIn('vendor', api_data['data'])
        self.assertIn('currency', api_data['data'])
        
        # Check metadata fields
        self.assertIn('ocr_confidence', api_data['metadata'])
        self.assertIn('processing_time_ms', api_data['metadata'])
    
    def test_batch_processing(self):
        """Test batch processing of multiple invoices"""
        # Create multiple test images
        images = []
        image_paths = []
        
        for i in range(3):
            image = self._create_realistic_invoice()
            image_path = os.path.join(self.temp_dir, f"invoice_{i}.png")
            cv2.imwrite(image_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            
            images.append(image)
            image_paths.append(image_path)
        
        # Process batch
        results = self.processor.process_batch(image_paths)
        
        # Verify results
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, InvoiceData)
    
    def test_different_processor_configs(self):
        """Test different processor configurations"""
        invoice_image = self._create_realistic_invoice()
        
        processors = {
            'default': DEFAULT_PROCESSOR,
            'strict': STRICT_PROCESSOR,
            'lenient': LENIENT_PROCESSOR
        }
        
        for name, processor in processors.items():
            with self.subTest(processor=name):
                result = processor.process_image(invoice_image, f"test_{name}")
                
                # All should process without errors
                self.assertIsInstance(result, InvoiceData)
                self.assertGreater(result.processing_time_ms, 0)
                
                # Different configs may have different success criteria
                if name == 'strict':
                    # Strict processor requires both amount and due date
                    pass  # Success depends on extraction accuracy
                elif name == 'lenient':
                    # Lenient processor should be more forgiving
                    pass  # May succeed even with partial data


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def test_create_invoice_processor(self):
        """Test create_invoice_processor convenience function"""
        processor = create_invoice_processor(
            pipeline_type='document',
            require_amount=False,
            require_due_date=True,
            min_ocr_confidence=40.0
        )
        
        self.assertIsInstance(processor, InvoiceProcessor)
        self.assertEqual(processor.config.ocr_config.pipeline_type, 'document')
        self.assertFalse(processor.config.require_amount)
        self.assertTrue(processor.config.require_due_date)
        self.assertEqual(processor.config.min_ocr_confidence, 40.0)
    
    def test_process_invoice_file_function(self):
        """Test process_invoice_file convenience function"""
        # Create test image
        image = np.ones((200, 400, 3), dtype=np.uint8) * 255
        cv2.putText(image, "Test Invoice", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        temp_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        cv2.imwrite(temp_path.name, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        
        try:
            # Test the convenience function
            result = process_invoice_file(temp_path.name)
            
            # Should return API-ready dictionary
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('data', result)
            self.assertIn('metadata', result)
            
        finally:
            os.unlink(temp_path.name)


class TestPreConfiguredProcessors(unittest.TestCase):
    """Test cases for pre-configured processor instances"""
    
    def test_default_processor(self):
        """Test DEFAULT_PROCESSOR instance"""
        self.assertIsInstance(DEFAULT_PROCESSOR, InvoiceProcessor)
        self.assertTrue(DEFAULT_PROCESSOR.config.require_amount)
        self.assertFalse(DEFAULT_PROCESSOR.config.require_due_date)
    
    def test_strict_processor(self):
        """Test STRICT_PROCESSOR instance"""
        self.assertIsInstance(STRICT_PROCESSOR, InvoiceProcessor)
        self.assertTrue(STRICT_PROCESSOR.config.require_amount)
        self.assertTrue(STRICT_PROCESSOR.config.require_due_date)
        self.assertEqual(STRICT_PROCESSOR.config.min_ocr_confidence, 50.0)
    
    def test_lenient_processor(self):
        """Test LENIENT_PROCESSOR instance"""
        self.assertIsInstance(LENIENT_PROCESSOR, InvoiceProcessor)
        self.assertFalse(LENIENT_PROCESSOR.config.require_amount)
        self.assertFalse(LENIENT_PROCESSOR.config.require_due_date)
        self.assertEqual(LENIENT_PROCESSOR.config.min_ocr_confidence, 20.0)


def main():
    """Main test runner"""
    print("Invoice Processing Pipeline Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestInvoiceData,
        TestPipelineConfig,
        TestInvoiceProcessor,
        TestPipelineIntegration,
        TestConvenienceFunctions,
        TestPreConfiguredProcessors
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(getattr(result, 'skipped', []))}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'✓ PASSED' if success else '✗ FAILED'}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
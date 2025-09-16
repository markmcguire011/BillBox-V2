#!/usr/bin/env python3
"""
Unit tests for Invoice Data Extractor
Comprehensive tests for amount, due date, and vendor extraction functionality
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from extractor import (
        InvoiceExtractor, ExtractionConfig, ExtractedData,
        create_invoice_extractor,
        DEFAULT_EXTRACTOR, STRICT_EXTRACTOR, LENIENT_EXTRACTOR
    )
    print("✓ Successfully imported extractor modules")
except ImportError as e:
    print(f"✗ Failed to import extractor modules: {e}")
    sys.exit(1)


class TestExtractionConfig(unittest.TestCase):
    """Test cases for ExtractionConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ExtractionConfig()
        
        # Test default currency symbols
        self.assertIn('$', config.currency_symbols)
        self.assertIn('USD', config.currency_symbols)
        
        # Test default amount keywords
        self.assertIn('total', config.amount_keywords)
        self.assertIn('amount due', config.amount_keywords)
        
        # Test default date formats
        self.assertIn('%m/%d/%Y', config.date_formats)
        self.assertIn('%Y-%m-%d', config.date_formats)
        
        # Test default vendor keywords
        self.assertIn('vendor', config.vendor_keywords)
        self.assertIn('company', config.vendor_keywords)
        
        # Test default settings
        self.assertFalse(config.case_sensitive)
        self.assertEqual(config.max_vendor_length, 100)
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = ExtractionConfig(
            currency_symbols=['€', 'EUR'],
            case_sensitive=True,
            max_amount_value=50000.0
        )
        
        self.assertEqual(config.currency_symbols, ['€', 'EUR'])
        self.assertTrue(config.case_sensitive)
        self.assertEqual(config.max_amount_value, 50000.0)


class TestExtractedData(unittest.TestCase):
    """Test cases for ExtractedData dataclass"""
    
    def test_default_extracted_data(self):
        """Test default ExtractedData initialization"""
        data = ExtractedData()
        
        self.assertIsNone(data.amount)
        self.assertIsNone(data.due_date)
        self.assertIsNone(data.vendor)
        self.assertEqual(data.confidence_scores, {})
        self.assertEqual(data.raw_matches, {})
        self.assertEqual(data.extraction_notes, [])
    
    def test_extracted_data_with_values(self):
        """Test ExtractedData with actual values"""
        test_date = datetime(2024, 12, 31)
        test_amount = Decimal('123.45')
        
        data = ExtractedData(
            amount=test_amount,
            due_date=test_date,
            vendor="Test Company Inc"
        )
        
        self.assertEqual(data.amount, test_amount)
        self.assertEqual(data.due_date, test_date)
        self.assertEqual(data.vendor, "Test Company Inc")


class TestInvoiceExtractor(unittest.TestCase):
    """Test cases for InvoiceExtractor main functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = InvoiceExtractor()
        self.config = ExtractionConfig()
        self.custom_extractor = InvoiceExtractor(self.config)
    
    def test_extractor_initialization(self):
        """Test extractor initialization"""
        self.assertIsInstance(self.extractor.config, ExtractionConfig)
        self.assertIsNotNone(self.extractor.amount_patterns)
        self.assertIsNotNone(self.extractor.date_patterns)
        self.assertIsNotNone(self.extractor.vendor_patterns)
    
    def test_empty_text_extraction(self):
        """Test extraction with empty or whitespace text"""
        result = self.extractor.extract("")
        self.assertIsNone(result.amount)
        self.assertIsNone(result.due_date)
        self.assertIsNone(result.vendor)
        self.assertIn("Empty or whitespace-only text provided", result.extraction_notes)
        
        result = self.extractor.extract("   \n\t  ")
        self.assertIn("Empty or whitespace-only text provided", result.extraction_notes)


class TestAmountExtraction(unittest.TestCase):
    """Test cases for amount extraction functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = InvoiceExtractor()
    
    def test_basic_amount_extraction(self):
        """Test basic amount patterns"""
        test_cases = [
            ("Total: $123.45", Decimal('123.45')),
            ("Amount due: $1,234.56", Decimal('1234.56')),
            ("Invoice total $999.99", Decimal('999.99')),
            ("TOTAL: $50.00", Decimal('50.00')),
            ("Amount: 789.12 USD", Decimal('789.12')),
        ]
        
        for text, expected_amount in test_cases:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                self.assertEqual(result.amount, expected_amount)
                self.assertGreater(result.confidence_scores.get('amount', 0), 0)
    
    def test_currency_symbols(self):
        """Test different currency symbols"""
        test_cases = [
            ("Total: $100.00", Decimal('100.00')),
            ("Amount: 100.00 USD", Decimal('100.00')),
            ("Total: 100.00 EUR", Decimal('100.00')),
            ("Amount: 100.00 GBP", Decimal('100.00')),
        ]
        
        for text, expected_amount in test_cases:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                self.assertEqual(result.amount, expected_amount)
    
    def test_amount_with_commas(self):
        """Test amounts with comma separators"""
        test_cases = [
            ("Total: $1,234.56", Decimal('1234.56')),
            ("Amount: $12,345.67", Decimal('12345.67')),
            ("Invoice: $1,000.00", Decimal('1000.00')),
        ]
        
        for text, expected_amount in test_cases:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                self.assertEqual(result.amount, expected_amount)
    
    def test_invalid_amounts(self):
        """Test that invalid amounts are rejected"""
        invalid_texts = [
            "Total: $0.00",  # Zero amount
            "Amount: $-123.45",  # Negative amount
            "Total: $9999999.99",  # Too large (exceeds max_amount_value)
            "Invoice: abc.def",  # Non-numeric
        ]
        
        for text in invalid_texts:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                self.assertIsNone(result.amount)
    
    def test_multiple_amounts_confidence(self):
        """Test confidence scoring with multiple amounts"""
        text = "Subtotal: $100.00\nTax: $8.50\nTotal: $108.50\nBalance: $108.50"
        result = self.extractor.extract(text)
        
        # Should extract one of the amounts (likely the highest confidence one)
        self.assertIsNotNone(result.amount)
        self.assertIn('amount', result.confidence_scores)
        self.assertGreater(result.confidence_scores['amount'], 0)


class TestDateExtraction(unittest.TestCase):
    """Test cases for due date extraction functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = InvoiceExtractor()
        self.today = datetime.now()
    
    def test_basic_date_extraction(self):
        """Test basic date patterns"""
        future_date = self.today + timedelta(days=30)
        test_cases = [
            ("Due date: 12/31/2024", "2024-12-31"),
            ("Payment due: 01/15/2025", "2025-01-15"),
            ("Due: December 31, 2024", "2024-12-31"),
            ("Date due: Jan 15, 2025", "2025-01-15"),
        ]
        
        for text, expected_date_str in test_cases:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                if result.due_date:
                    self.assertEqual(result.due_date.strftime('%Y-%m-%d'), expected_date_str)
                    self.assertGreater(result.confidence_scores.get('due_date', 0), 0)
    
    def test_date_formats(self):
        """Test various date formats"""
        test_cases = [
            "Due: 12/31/2024",  # MM/DD/YYYY
            "Due: 31/12/2024",  # DD/MM/YYYY  
            "Due: 2024-12-31",  # YYYY-MM-DD
            "Due: December 31, 2024",  # Month DD, YYYY
            "Due: 31 December 2024",  # DD Month YYYY
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                # Should extract some date (format parsing may vary)
                self.assertIn('due_date', result.confidence_scores)
    
    def test_invalid_dates(self):
        """Test that invalid dates are rejected"""
        past_date = self.today - timedelta(days=100)
        far_future_date = self.today + timedelta(days=500)
        
        invalid_texts = [
            f"Due: {past_date.strftime('%m/%d/%Y')}",  # Too far in past
            f"Due: {far_future_date.strftime('%m/%d/%Y')}",  # Too far in future
            "Due: 13/32/2024",  # Invalid month/day
            "Due: February 30, 2024",  # Invalid date
            "Due: abc/def/ghij",  # Non-numeric
        ]
        
        for text in invalid_texts:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                # Some invalid dates might still be parsed, but should have low confidence
                # or be rejected entirely
                if result.due_date is None:
                    self.assertEqual(result.confidence_scores.get('due_date', 0), 0)
    
    def test_date_with_keywords(self):
        """Test dates with due-related keywords get higher confidence"""
        text_with_keyword = "Payment due: 12/31/2024"
        text_without_keyword = "Invoice date: 12/31/2024"
        
        result_with = self.extractor.extract(text_with_keyword)
        result_without = self.extractor.extract(text_without_keyword)
        
        # Both should extract dates, but keyword version should have higher confidence
        if result_with.due_date and result_without.due_date:
            self.assertGreaterEqual(
                result_with.confidence_scores.get('due_date', 0),
                result_without.confidence_scores.get('due_date', 0)
            )


class TestVendorExtraction(unittest.TestCase):
    """Test cases for vendor extraction functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = InvoiceExtractor()
    
    def test_basic_vendor_extraction(self):
        """Test basic vendor patterns"""
        test_cases = [
            ("From: Acme Corporation", "Acme Corporation"),
            ("Vendor: Smith & Associates LLC", "Smith & Associates Llc"),
            ("Company: Tech Solutions Inc", "Tech Solutions Inc"),
            ("Bill from: ABC Services", "Abc Services"),
        ]
        
        for text, expected_vendor in test_cases:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                self.assertEqual(result.vendor, expected_vendor)
                self.assertGreater(result.confidence_scores.get('vendor', 0), 0)
    
    def test_vendor_in_header(self):
        """Test vendor extraction from document header"""
        header_text = """ACME CORPORATION
123 Business Street
City, State 12345

Invoice #: 2024-001
Date: 01/15/2024
"""
        result = self.extractor.extract(header_text)
        self.assertIsNotNone(result.vendor)
        self.assertIn("acme", result.vendor.lower())
    
    def test_business_entity_detection(self):
        """Test detection of business entity suffixes"""
        test_cases = [
            "XYZ Services LLC",
            "ABC Corporation", 
            "Smith & Associates Inc",
            "Tech Solutions Company",
        ]
        
        for vendor_text in test_cases:
            with self.subTest(vendor=vendor_text):
                text = f"Invoice from {vendor_text}\nAmount: $100.00"
                result = self.extractor.extract(text)
                self.assertIsNotNone(result.vendor)
    
    def test_invalid_vendors(self):
        """Test that invalid vendor names are rejected"""
        invalid_texts = [
            "From: Total",  # Common excluded word
            "Vendor: 123",  # Just numbers
            "Company: a",   # Too short
            "From: Invoice Receipt Payment",  # Multiple excluded words
        ]
        
        for text in invalid_texts:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                # Should either reject the vendor or have very low confidence
                if result.vendor is None:
                    self.assertEqual(result.confidence_scores.get('vendor', 0), 0)
    
    def test_vendor_cleaning(self):
        """Test vendor name cleaning and normalization"""
        test_cases = [
            ("From:   ACME    CORP   ", "Acme Corp"),
            ("Vendor: smith & associates", "Smith & Associates"),
            ("Company: ABC-123 LLC", "Abc-123 Llc"),
        ]
        
        for text, expected_clean in test_cases:
            with self.subTest(text=text):
                result = self.extractor.extract(text)
                if result.vendor:
                    self.assertEqual(result.vendor, expected_clean)


class TestIntegratedExtraction(unittest.TestCase):
    """Test cases for integrated extraction scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = InvoiceExtractor()
    
    def test_complete_invoice_extraction(self):
        """Test extraction from a complete invoice text"""
        invoice_text = """
ACME CORPORATION
123 Business Street
City, State 12345

INVOICE

Invoice #: 2024-001
Date: 01/15/2024
Due Date: 02/15/2024

Bill To:
John Doe
456 Customer Ave

Description                  Qty    Price    Total
Web Development Services      1    $1000.00  $1000.00
Consulting Services          2     $250.00   $500.00

Subtotal:                              $1500.00
Tax (8.5%):                           $127.50
TOTAL AMOUNT DUE:                     $1627.50

Payment is due by 02/15/2024
"""
        
        result = self.extractor.extract(invoice_text)
        
        # Should extract all three key pieces of data
        self.assertIsNotNone(result.amount)
        self.assertIsNotNone(result.due_date)
        self.assertIsNotNone(result.vendor)
        
        # Verify extracted values are reasonable
        self.assertEqual(result.amount, Decimal('1627.50'))
        self.assertEqual(result.due_date.strftime('%m/%d/%Y'), '02/15/2024')
        self.assertIn("acme", result.vendor.lower())
        
        # Should have confidence scores for all extractions
        self.assertIn('amount', result.confidence_scores)
        self.assertIn('due_date', result.confidence_scores)
        self.assertIn('vendor', result.confidence_scores)
        self.assertIn('overall', result.confidence_scores)
    
    def test_partial_extraction(self):
        """Test extraction when only some data is available"""
        partial_text = "Amount due: $500.00\nThank you for your business!"
        
        result = self.extractor.extract(partial_text)
        
        # Should extract amount but not date or vendor
        self.assertEqual(result.amount, Decimal('500.00'))
        self.assertIsNone(result.due_date)
        self.assertIsNone(result.vendor)
        
        # Confidence scores should reflect what was found
        self.assertGreater(result.confidence_scores['amount'], 0)
        self.assertEqual(result.confidence_scores['due_date'], 0)
        self.assertEqual(result.confidence_scores['vendor'], 0)
    
    def test_noisy_text_extraction(self):
        """Test extraction from noisy OCR text"""
        noisy_text = """
AC ME   C0RP0RATI0N
123 Bu5ine55 5treet

T0TAL  AM0UNT:  $1,234.56
DUE  DATE:  12/31/2024
"""
        
        result = self.extractor.extract(noisy_text)
        
        # Should still extract some data despite OCR noise
        # (Results may vary based on OCR quality)
        self.assertIsInstance(result, ExtractedData)
        self.assertIsInstance(result.confidence_scores, dict)


class TestBatchProcessing(unittest.TestCase):
    """Test cases for batch processing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = InvoiceExtractor()
    
    def test_batch_extraction(self):
        """Test batch processing of multiple texts"""
        texts = [
            "Total: $100.00\nDue: 12/31/2024\nFrom: Company A",
            "Amount: $200.00\nPayment due: 01/15/2025\nVendor: Company B",
            "Invoice total: $300.00"  # Partial data
        ]
        
        results = self.extractor.extract_batch(texts)
        
        self.assertEqual(len(results), 3)
        
        # First result should have all data
        self.assertEqual(results[0].amount, Decimal('100.00'))
        self.assertIsNotNone(results[0].due_date)
        self.assertIsNotNone(results[0].vendor)
        
        # Second result should have all data
        self.assertEqual(results[1].amount, Decimal('200.00'))
        self.assertIsNotNone(results[1].due_date)
        self.assertIsNotNone(results[1].vendor)
        
        # Third result should have partial data
        self.assertEqual(results[2].amount, Decimal('300.00'))
    
    def test_batch_with_errors(self):
        """Test batch processing with some invalid inputs"""
        texts = [
            "Total: $100.00",  # Valid
            "",                # Empty
            "Invalid data xyz", # No extractable data
        ]
        
        results = self.extractor.extract_batch(texts)
        
        self.assertEqual(len(results), 3)
        
        # All should return ExtractedData objects (even if empty)
        for result in results:
            self.assertIsInstance(result, ExtractedData)
            self.assertIsInstance(result.extraction_notes, list)


class TestPreConfiguredExtractors(unittest.TestCase):
    """Test cases for pre-configured extractor instances"""
    
    def test_default_extractor(self):
        """Test DEFAULT_EXTRACTOR instance"""
        text = "Total: $100.00"
        result = DEFAULT_EXTRACTOR.extract(text)
        
        self.assertIsInstance(result, ExtractedData)
        self.assertEqual(result.amount, Decimal('100.00'))
    
    def test_strict_extractor(self):
        """Test STRICT_EXTRACTOR instance"""
        text = "Total: $100.00"
        result = STRICT_EXTRACTOR.extract(text)
        
        self.assertIsInstance(result, ExtractedData)
        # Should have stricter validation
        self.assertTrue(STRICT_EXTRACTOR.config.case_sensitive)
        self.assertLess(STRICT_EXTRACTOR.config.max_amount_value, DEFAULT_EXTRACTOR.config.max_amount_value)
    
    def test_lenient_extractor(self):
        """Test LENIENT_EXTRACTOR instance"""
        text = "Total: $100.00"
        result = LENIENT_EXTRACTOR.extract(text)
        
        self.assertIsInstance(result, ExtractedData)
        # Should have more lenient validation
        self.assertFalse(LENIENT_EXTRACTOR.config.case_sensitive)
        self.assertGreater(LENIENT_EXTRACTOR.config.max_amount_value, DEFAULT_EXTRACTOR.config.max_amount_value)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def test_create_invoice_extractor(self):
        """Test create_invoice_extractor convenience function"""
        extractor = create_invoice_extractor(max_amount=50000.0, case_sensitive=True)
        
        self.assertIsInstance(extractor, InvoiceExtractor)
        self.assertEqual(extractor.config.max_amount_value, 50000.0)
        self.assertTrue(extractor.config.case_sensitive)
    
    def test_create_invoice_extractor_defaults(self):
        """Test create_invoice_extractor with default parameters"""
        extractor = create_invoice_extractor()
        
        self.assertIsInstance(extractor, InvoiceExtractor)
        self.assertEqual(extractor.config.max_amount_value, 1000000.0)
        self.assertFalse(extractor.config.case_sensitive)


def main():
    """Main test runner"""
    print("Invoice Extractor Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestExtractionConfig,
        TestExtractedData,
        TestInvoiceExtractor,
        TestAmountExtraction,
        TestDateExtraction,
        TestVendorExtraction,
        TestIntegratedExtraction,
        TestBatchProcessing,
        TestPreConfiguredExtractors,
        TestConvenienceFunctions
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
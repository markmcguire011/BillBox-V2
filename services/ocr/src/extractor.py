#!/usr/bin/env python3
"""
Data Extractor for BillBox - Invoice Information Extraction
Uses regex patterns and text analysis to extract key invoice data from OCR text
"""

import re
import logging
from typing import Dict, List, Optional, Union, Tuple, Pattern
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import calendar


@dataclass
class ExtractedData:
    """Container for extracted invoice data"""
    amount: Optional[Decimal] = None
    due_date: Optional[datetime] = None
    vendor: Optional[str] = None
    
    # Additional metadata
    confidence_scores: Dict[str, float] = None
    raw_matches: Dict[str, List[str]] = None
    extraction_notes: List[str] = None
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}
        if self.raw_matches is None:
            self.raw_matches = {}
        if self.extraction_notes is None:
            self.extraction_notes = []


@dataclass
class ExtractionConfig:
    """Configuration for data extraction"""
    # Amount extraction settings
    currency_symbols: List[str] = None
    amount_keywords: List[str] = None
    max_amount_value: float = 1000000.0  # Maximum reasonable amount
    
    # Date extraction settings
    date_formats: List[str] = None
    max_days_future: int = 365  # Maximum days in future for due dates
    max_days_past: int = 30     # Maximum days in past for due dates
    
    # Vendor extraction settings
    vendor_keywords: List[str] = None
    exclude_vendor_words: List[str] = None
    max_vendor_length: int = 100
    
    # General settings
    case_sensitive: bool = False
    
    def __post_init__(self):
        if self.currency_symbols is None:
            self.currency_symbols = ['$', 'USD', 'EUR', 'GBP']
        
        if self.amount_keywords is None:
            self.amount_keywords = [
                'total', 'amount', 'due', 'balance', 'sum', 'grand total',
                'amount due', 'total due', 'invoice total', 'final amount',
                'net amount', 'gross amount', 'subtotal'
            ]
        
        if self.date_formats is None:
            self.date_formats = [
                '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d',
                '%m-%d-%Y', '%d-%m-%Y', '%B %d, %Y', '%d %B %Y',
                '%b %d, %Y', '%d %b %Y', '%m/%d/%y', '%d/%m/%y'
            ]
        
        if self.vendor_keywords is None:
            self.vendor_keywords = [
                'from', 'vendor', 'supplier', 'company', 'corporation', 'corp',
                'inc', 'llc', 'ltd', 'limited', 'business', 'services',
                'invoice from', 'bill from', 'billed by'
            ]
        
        if self.exclude_vendor_words is None:
            self.exclude_vendor_words = [
                'customer', 'client', 'bill to', 'ship to', 'invoice',
                'receipt', 'total', 'amount', 'date', 'due', 'tax'
            ]


class InvoiceExtractor:
    """
    Main extractor class for parsing invoice data from OCR text
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """Initialize extractor with configuration"""
        self.config = config or ExtractionConfig()
        self.logger = logging.getLogger(__name__)
        
        # Compile regex patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for better performance"""
        flags = 0 if self.config.case_sensitive else re.IGNORECASE
        
        # Amount patterns
        currency_pattern = '|'.join(re.escape(sym) for sym in self.config.currency_symbols)
        self.amount_patterns = [
            # $123.45, �1,234.56, etc.
            re.compile(rf'({currency_pattern})\s*([0-9,]+\.?[0-9]*)', flags),
            # 123.45 USD, 1,234.56 EUR, etc.
            re.compile(rf'([0-9,]+\.?[0-9]*)\s*({currency_pattern})', flags),
            # Amount: $123.45, Total: 1,234.56, etc.
            re.compile(rf'(?:{"| ".join(self.config.amount_keywords)})\s*:?\s*({currency_pattern})?\s*([0-9,]+\.?[0-9]*)', flags),
            # Standalone decimal numbers (lower confidence)
            re.compile(r'([0-9,]{1,3}(?:,[0-9]{3})*\.?[0-9]{0,2})', flags)
        ]
        
        # Date patterns
        self.date_patterns = [
            # Various date formats with keywords
            re.compile(r'(?:due\s+date|due|payment\s+due|date\s+due)\s*:?\s*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})', flags),
            re.compile(r'(?:due\s+date|due|payment\s+due|date\s+due)\s*:?\s*([a-zA-Z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{2,4})', flags),
            # Standalone date patterns (lower confidence)
            re.compile(r'([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})', flags),
            re.compile(r'([a-zA-Z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{2,4})', flags),
            # ISO format dates
            re.compile(r'([0-9]{4}-[0-9]{1,2}-[0-9]{1,2})', flags)
        ]
        
        # Vendor patterns
        vendor_keywords = '|'.join(self.config.vendor_keywords)
        self.vendor_patterns = [
            # "From: Company Name", "Vendor: Business Inc", etc.
            re.compile(rf'(?:{vendor_keywords})\s*:?\s*([A-Za-z0-9\s&\.,\-\']+?)(?:\n|$|[0-9]{{3,}})', flags),
            # Company name at start of line (first few lines typically)
            re.compile(r'^([A-Z][A-Za-z0-9\s&\.,\-\']{2,50})(?:\n|$)', re.MULTILINE | flags),
            # Lines containing business indicators
            re.compile(r'([A-Za-z\s&\.,\-\']*(?:Inc|LLC|Ltd|Corp|Corporation|Company|Services|Solutions)[A-Za-z\s&\.,\-\']*)', flags)
        ]
    
    def extract(self, text: str) -> ExtractedData:
        """
        Extract key data from OCR text
        
        Args:
            text: Raw OCR text from invoice
            
        Returns:
            ExtractedData with extracted information
        """
        result = ExtractedData()
        
        if not text or not text.strip():
            result.extraction_notes.append("Empty or whitespace-only text provided")
            return result
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Extract each type of data
        result.amount = self._extract_amount(cleaned_text, result)
        result.due_date = self._extract_due_date(cleaned_text, result)
        result.vendor = self._extract_vendor(cleaned_text, result)
        
        # Calculate overall confidence scores
        self._calculate_confidence_scores(result)
        
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better extraction"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s\.,\-\/\$���:()]', ' ', text)
        
        return text.strip()
    
    def _extract_amount(self, text: str, result: ExtractedData) -> Optional[Decimal]:
        """Extract monetary amount from text"""
        amounts_found = []
        
        for i, pattern in enumerate(self.amount_patterns):
            matches = pattern.findall(text)
            
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        # Handle tuple results from regex groups
                        amount_str = ''.join(match).strip()
                    else:
                        amount_str = match.strip()
                    
                    # Clean amount string
                    amount_str = re.sub(r'[^\d\.]', '', amount_str)
                    
                    if amount_str and '.' in amount_str:
                        # Ensure only one decimal point
                        parts = amount_str.split('.')
                        if len(parts) == 2:
                            amount_str = parts[0] + '.' + parts[1]
                        else:
                            continue
                    
                    amount = Decimal(amount_str)
                    
                    # Validate amount range
                    if 0 < amount <= self.config.max_amount_value:
                        confidence = 1.0 - (i * 0.2)  # Higher patterns have higher confidence
                        amounts_found.append((amount, confidence, str(match)))
                        
                except (InvalidOperation, ValueError, TypeError):
                    continue
        
        # Store all matches for debugging
        result.raw_matches['amounts'] = [match[2] for match in amounts_found]
        
        if amounts_found:
            # Sort by confidence and return highest confidence amount
            amounts_found.sort(key=lambda x: x[1], reverse=True)
            best_amount, confidence, raw_match = amounts_found[0]
            
            result.confidence_scores['amount'] = confidence
            result.extraction_notes.append(f"Amount extracted: {best_amount} (confidence: {confidence:.2f})")
            
            return best_amount
        
        result.extraction_notes.append("No valid amount found")
        return None
    
    def _extract_due_date(self, text: str, result: ExtractedData) -> Optional[datetime]:
        """Extract due date from text"""
        dates_found = []
        today = datetime.now()
        
        for i, pattern in enumerate(self.date_patterns):
            matches = pattern.findall(text)
            
            for match in matches:
                date_str = match.strip() if isinstance(match, str) else ' '.join(match).strip()
                
                # Try to parse with different formats
                for date_format in self.config.date_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, date_format)
                        
                        # Validate date range (reasonable due dates)
                        min_date = today - timedelta(days=self.config.max_days_past)
                        max_date = today + timedelta(days=self.config.max_days_future)
                        
                        if min_date <= parsed_date <= max_date:
                            confidence = 1.0 - (i * 0.15)  # Higher pattern index = lower confidence
                            
                            # Boost confidence for dates with "due" keywords
                            if any(keyword in text.lower() for keyword in ['due', 'payment']):
                                confidence += 0.2
                            
                            dates_found.append((parsed_date, confidence, date_str))
                            break
                            
                    except ValueError:
                        continue
        
        # Store all matches for debugging
        result.raw_matches['dates'] = [match[2] for match in dates_found]
        
        if dates_found:
            # Sort by confidence and return highest confidence date
            dates_found.sort(key=lambda x: x[1], reverse=True)
            best_date, confidence, raw_match = dates_found[0]
            
            result.confidence_scores['due_date'] = confidence
            result.extraction_notes.append(f"Due date extracted: {best_date.strftime('%Y-%m-%d')} (confidence: {confidence:.2f})")
            
            return best_date
        
        result.extraction_notes.append("No valid due date found")
        return None
    
    def _extract_vendor(self, text: str, result: ExtractedData) -> Optional[str]:
        """Extract vendor/company name from text"""
        vendors_found = []
        lines = text.split('\n')
        
        for i, pattern in enumerate(self.vendor_patterns):
            matches = pattern.findall(text)
            
            for match in matches:
                vendor_name = match.strip() if isinstance(match, str) else ' '.join(match).strip()
                
                # Clean vendor name
                vendor_name = self._clean_vendor_name(vendor_name)
                
                if self._is_valid_vendor_name(vendor_name):
                    confidence = 1.0 - (i * 0.2)
                    
                    # Boost confidence for vendors found in first few lines
                    if any(vendor_name.lower() in line.lower() for line in lines[:3]):
                        confidence += 0.3
                    
                    vendors_found.append((vendor_name, confidence, match))
        
        # Store all matches for debugging
        result.raw_matches['vendors'] = [match[2] for match in vendors_found]
        
        if vendors_found:
            # Sort by confidence and return highest confidence vendor
            vendors_found.sort(key=lambda x: x[1], reverse=True)
            best_vendor, confidence, raw_match = vendors_found[0]
            
            result.confidence_scores['vendor'] = confidence
            result.extraction_notes.append(f"Vendor extracted: {best_vendor} (confidence: {confidence:.2f})")
            
            return best_vendor
        
        result.extraction_notes.append("No valid vendor found")
        return None
    
    def _clean_vendor_name(self, vendor: str) -> str:
        """Clean and normalize vendor name"""
        # Remove extra whitespace
        vendor = re.sub(r'\s+', ' ', vendor).strip()
        
        # Remove leading/trailing punctuation
        vendor = re.sub(r'^[^\w]+|[^\w]+$', '', vendor)
        
        # Capitalize properly
        vendor = ' '.join(word.capitalize() for word in vendor.split())
        
        return vendor
    
    def _is_valid_vendor_name(self, vendor: str) -> bool:
        """Validate if string is a reasonable vendor name"""
        if not vendor or len(vendor) < 3:
            return False
        
        if len(vendor) > self.config.max_vendor_length:
            return False
        
        # Check if it's mostly letters
        letter_count = sum(1 for c in vendor if c.isalpha())
        if letter_count < len(vendor) * 0.5:
            return False
        
        # Check against exclusion list
        vendor_lower = vendor.lower()
        for exclude_word in self.config.exclude_vendor_words:
            if exclude_word in vendor_lower:
                return False
        
        # Check if it's just numbers or common non-vendor words
        if vendor_lower in ['total', 'amount', 'invoice', 'bill', 'receipt', 'payment']:
            return False
        
        return True
    
    def _calculate_confidence_scores(self, result: ExtractedData) -> None:
        """Calculate overall confidence scores"""
        # Set default confidence for missing data
        if 'amount' not in result.confidence_scores:
            result.confidence_scores['amount'] = 0.0
        if 'due_date' not in result.confidence_scores:
            result.confidence_scores['due_date'] = 0.0
        if 'vendor' not in result.confidence_scores:
            result.confidence_scores['vendor'] = 0.0
        
        # Calculate overall extraction confidence
        total_confidence = sum(result.confidence_scores.values())
        result.confidence_scores['overall'] = total_confidence / 3.0
    
    def extract_batch(self, texts: List[str]) -> List[ExtractedData]:
        """
        Extract data from multiple texts
        
        Args:
            texts: List of OCR text strings
            
        Returns:
            List of ExtractedData objects
        """
        results = []
        for i, text in enumerate(texts):
            try:
                result = self.extract(text)
                result.extraction_notes.append(f"Processed batch item {i}")
                results.append(result)
            except Exception as e:
                error_result = ExtractedData()
                error_result.extraction_notes.append(f"Error processing batch item {i}: {str(e)}")
                results.append(error_result)
                self.logger.error(f"Error extracting from batch item {i}: {e}")
        
        return results


def create_invoice_extractor(
    max_amount: float = 1000000.0,
    case_sensitive: bool = False
) -> InvoiceExtractor:
    """
    Convenience function to create invoice extractor with common settings
    
    Args:
        max_amount: Maximum reasonable amount value
        case_sensitive: Whether pattern matching should be case sensitive
        
    Returns:
        Configured InvoiceExtractor instance
    """
    config = ExtractionConfig(
        max_amount_value=max_amount,
        case_sensitive=case_sensitive
    )
    
    return InvoiceExtractor(config)


# Pre-configured extractors for common use cases
DEFAULT_EXTRACTOR = InvoiceExtractor()

STRICT_EXTRACTOR = InvoiceExtractor(ExtractionConfig(
    max_amount_value=50000.0,
    max_days_future=90,
    case_sensitive=True
))

LENIENT_EXTRACTOR = InvoiceExtractor(ExtractionConfig(
    max_amount_value=5000000.0,
    max_days_future=730,
    case_sensitive=False,
    max_vendor_length=200
))
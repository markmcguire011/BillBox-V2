#!/usr/bin/env python3
"""
BillBox Invoice Processing Pipeline
Combines OCR engine and data extraction to provide a unified interface for processing invoices
"""

import logging
from typing import Dict, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ocr_engine import OCREngine, OCRConfig, OCRResult, create_ocr_engine
from extractor import InvoiceExtractor, ExtractionConfig, ExtractedData, create_invoice_extractor


@dataclass
class InvoiceData:
    """Final invoice data ready for API consumption"""
    # Core extracted data
    amount: Optional[Decimal] = None
    due_date: Optional[datetime] = None
    vendor: Optional[str] = None
    
    # OCR metadata
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    
    # Extraction metadata
    extraction_confidence: Dict[str, float] = None
    extraction_notes: List[str] = None
    
    # Processing metadata
    processing_success: bool = False
    processing_time_ms: float = 0.0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.extraction_confidence is None:
            self.extraction_confidence = {}
        if self.extraction_notes is None:
            self.extraction_notes = []


@dataclass
class PipelineConfig:
    """Configuration for the invoice processing pipeline"""
    # OCR configuration
    ocr_config: OCRConfig = None
    
    # Extraction configuration
    extraction_config: ExtractionConfig = None
    
    # Pipeline settings
    min_ocr_confidence: float = 30.0
    require_amount: bool = True
    require_due_date: bool = False
    require_vendor: bool = False
    
    def __post_init__(self):
        if self.ocr_config is None:
            self.ocr_config = OCRConfig(
                tesseract_config='--oem 3 --psm 6',
                pipeline_type='invoice',
                enable_preprocessing=True,
                include_word_boxes=True,
                include_line_boxes=True
            )
        
        if self.extraction_config is None:
            self.extraction_config = ExtractionConfig()


class InvoiceProcessor:
    """
    Main pipeline class that orchestrates OCR and data extraction
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the invoice processor with configuration"""
        self.config = config or PipelineConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize OCR engine
        self.ocr_engine = OCREngine(self.config.ocr_config)
        
        # Initialize extractor
        self.extractor = InvoiceExtractor(self.config.extraction_config)
        
        self.logger.info("Invoice processor initialized successfully")
    
    def process_image(self, image_data, source_info: str = "unknown") -> InvoiceData:
        """
        Process an image to extract invoice data
        
        Args:
            image_data: Image as numpy array or file path
            source_info: Information about the source (for logging)
            
        Returns:
            InvoiceData with extracted information
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing invoice from {source_info}")
            
            # Step 1: OCR extraction
            if isinstance(image_data, (str, Path)):
                ocr_result = self.ocr_engine.process_image_file(image_data)
            else:
                ocr_result = self.ocr_engine.extract_text(image_data)
            
            if not ocr_result.success:
                return InvoiceData(
                    processing_success=False,
                    error_message=f"OCR failed: {ocr_result.error_message}",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check OCR confidence
            if ocr_result.confidence < self.config.min_ocr_confidence:
                self.logger.warning(f"Low OCR confidence: {ocr_result.confidence:.1f}% (min: {self.config.min_ocr_confidence}%)")
            
            # Step 2: Text extraction
            extracted_data = self.extractor.extract(ocr_result.text)
            
            # Step 3: Validation
            validation_result = self._validate_extraction(extracted_data)
            
            # Step 4: Create final result
            processing_time = (time.time() - start_time) * 1000
            
            result = InvoiceData(
                amount=extracted_data.amount,
                due_date=extracted_data.due_date,
                vendor=extracted_data.vendor,
                ocr_text=ocr_result.text,
                ocr_confidence=ocr_result.confidence,
                extraction_confidence=extracted_data.confidence_scores,
                extraction_notes=extracted_data.extraction_notes,
                processing_success=validation_result['success'],
                processing_time_ms=processing_time,
                error_message=validation_result.get('error_message')
            )
            
            self.logger.info(f"Processing completed in {processing_time:.1f}ms - Success: {result.processing_success}")
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_msg = f"Pipeline processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            return InvoiceData(
                processing_success=False,
                error_message=error_msg,
                processing_time_ms=processing_time
            )
    
    def _validate_extraction(self, extracted_data: ExtractedData) -> Dict:
        """
        Validate extracted data against requirements
        
        Args:
            extracted_data: Data extracted by the extractor
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        # Check required fields
        if self.config.require_amount and extracted_data.amount is None:
            errors.append("Amount is required but not found")
        
        if self.config.require_due_date and extracted_data.due_date is None:
            errors.append("Due date is required but not found")
        
        if self.config.require_vendor and extracted_data.vendor is None:
            errors.append("Vendor is required but not found")
        
        # Validate amount if present
        if extracted_data.amount is not None:
            if extracted_data.amount <= 0:
                errors.append(f"Invalid amount: {extracted_data.amount}")
        
        # Validate due date if present
        if extracted_data.due_date is not None:
            # Check if date is reasonable (not too far in past or future)
            from datetime import timedelta
            today = datetime.now()
            min_date = today - timedelta(days=30)
            max_date = today + timedelta(days=365)
            
            if not (min_date <= extracted_data.due_date <= max_date):
                errors.append(f"Due date outside reasonable range: {extracted_data.due_date}")
        
        success = len(errors) == 0
        result = {'success': success}
        
        if not success:
            result['error_message'] = "; ".join(errors)
        
        return result
    
    def process_batch(self, image_sources: List) -> List[InvoiceData]:
        """
        Process multiple invoices
        
        Args:
            image_sources: List of image data or file paths
            
        Returns:
            List of InvoiceData objects
        """
        results = []
        
        for i, image_source in enumerate(image_sources):
            source_info = f"batch_item_{i}"
            if isinstance(image_source, (str, Path)):
                source_info = str(image_source)
            
            result = self.process_image(image_source, source_info)
            results.append(result)
        
        success_count = sum(1 for r in results if r.processing_success)
        self.logger.info(f"Batch processing completed: {success_count}/{len(results)} successful")
        
        return results
    
    def get_api_ready_data(self, invoice_data: InvoiceData) -> Dict:
        """
        Convert InvoiceData to dictionary format ready for backend API
        
        Args:
            invoice_data: Processed invoice data
            
        Returns:
            Dictionary formatted for API consumption
        """
        return {
            'success': invoice_data.processing_success,
            'data': {
                'amount': float(invoice_data.amount) if invoice_data.amount else None,
                'due_date': invoice_data.due_date.isoformat() if invoice_data.due_date else None,
                'vendor': invoice_data.vendor,
                'currency': 'USD'  # Default currency - could be extracted in future
            },
            'metadata': {
                'ocr_confidence': invoice_data.ocr_confidence,
                'extraction_confidence': invoice_data.extraction_confidence,
                'processing_time_ms': invoice_data.processing_time_ms,
                'text_length': len(invoice_data.ocr_text),
                'extraction_notes': invoice_data.extraction_notes
            },
            'error': invoice_data.error_message if not invoice_data.processing_success else None
        }


def create_invoice_processor(
    pipeline_type: str = 'invoice',
    require_amount: bool = True,
    require_due_date: bool = False,
    min_ocr_confidence: float = 30.0
) -> InvoiceProcessor:
    """
    Convenience function to create invoice processor with common configurations
    
    Args:
        pipeline_type: OCR pipeline type ('invoice', 'document', 'custom')
        require_amount: Whether amount extraction is required
        require_due_date: Whether due date extraction is required
        min_ocr_confidence: Minimum OCR confidence threshold
        
    Returns:
        Configured InvoiceProcessor instance
    """
    ocr_config = OCRConfig(
        tesseract_config='--oem 3 --psm 6',
        pipeline_type=pipeline_type,
        enable_preprocessing=True,
        include_word_boxes=True,
        include_line_boxes=True
    )
    
    extraction_config = ExtractionConfig()
    
    pipeline_config = PipelineConfig(
        ocr_config=ocr_config,
        extraction_config=extraction_config,
        min_ocr_confidence=min_ocr_confidence,
        require_amount=require_amount,
        require_due_date=require_due_date
    )
    
    return InvoiceProcessor(pipeline_config)


# Pre-configured processors for common use cases
DEFAULT_PROCESSOR = create_invoice_processor()

STRICT_PROCESSOR = create_invoice_processor(
    require_amount=True,
    require_due_date=True,
    min_ocr_confidence=50.0
)

LENIENT_PROCESSOR = create_invoice_processor(
    require_amount=False,
    require_due_date=False,
    min_ocr_confidence=20.0
)


def process_invoice_file(file_path: Union[str, Path]) -> Dict:
    """
    Quick utility function to process a single invoice file
    
    Args:
        file_path: Path to invoice image file
        
    Returns:
        API-ready dictionary with extracted data
    """
    processor = DEFAULT_PROCESSOR
    invoice_data = processor.process_image(file_path, str(file_path))
    return processor.get_api_ready_data(invoice_data)


if __name__ == "__main__":
    # Demo usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"Processing invoice: {file_path}")
        
        result = process_invoice_file(file_path)
        
        print("\nResult:")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Amount: ${result['data']['amount']}")
            print(f"Due Date: {result['data']['due_date']}")
            print(f"Vendor: {result['data']['vendor']}")
            print(f"OCR Confidence: {result['metadata']['ocr_confidence']:.1f}%")
        else:
            print(f"Error: {result['error']}")
    else:
        print("Usage: python pipeline.py <invoice_image_path>")
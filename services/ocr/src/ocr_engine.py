#!/usr/bin/env python3
"""
OCR Engine for BillBox - Pytesseract Implementation
Handles text extraction using OpenCV preprocessing (primary) with C++ preprocessing as fallback
Combines robust image preprocessing with Tesseract OCR for optimal text extraction
"""

import cv2
import numpy as np
import pytesseract
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import logging

# Import our C++ preprocessing module
try:
    import billbox_preprocessing as bp
    PREPROCESSING_AVAILABLE = True
except ImportError:
    PREPROCESSING_AVAILABLE = False
    logging.warning("billbox_preprocessing module not available - using OpenCV fallback")


@dataclass
class OCRResult:
    """Result of OCR operation"""
    text: str
    confidence: float
    word_boxes: List[Dict]
    line_boxes: List[Dict]
    preprocessing_stats: Dict
    success: bool
    error_message: Optional[str] = None


@dataclass
class OCRConfig:
    """Configuration for OCR engine"""
    # Tesseract configuration
    tesseract_config: str = '--oem 3 --psm 6'  # LSTM engine, single uniform block
    language: str = 'eng'
    
    # Preprocessing options
    enable_preprocessing: bool = True
    pipeline_type: str = 'invoice'  # 'invoice', 'document', 'custom'
    
    # Output options
    include_word_boxes: bool = True
    include_line_boxes: bool = True
    confidence_threshold: float = 0.0  # Minimum confidence to include text


class OCREngine:
    """
    Main OCR engine class that uses OpenCV preprocessing by default, with C++ preprocessing as fallback
    Combines image preprocessing with Pytesseract OCR for text extraction
    """
    
    def __init__(self, config: Optional[OCRConfig] = None):
        """Initialize OCR engine with configuration"""
        self.config = config or OCRConfig()
        self.logger = logging.getLogger(__name__)
        
        # Verify tesseract installation
        self._verify_tesseract()
        
        # Setup C++ preprocessing as fallback option if available
        if PREPROCESSING_AVAILABLE and self.config.enable_preprocessing:
            self.preprocessing_config = self._create_preprocessing_config()
            self.logger.info("C++ preprocessing available as fallback option")
        else:
            self.preprocessing_config = None
            if self.config.enable_preprocessing:
                self.logger.info("C++ preprocessing not available - using OpenCV primary with minimal fallback")
    
    def _verify_tesseract(self) -> None:
        """Verify that tesseract is properly installed"""
        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract version: {version}")
        except Exception as e:
            raise RuntimeError(f"Tesseract not found or not properly installed: {e}")
    
    def _create_preprocessing_config(self):
        """Create preprocessing configuration based on pipeline type"""
        if not PREPROCESSING_AVAILABLE:
            return None
            
        if self.config.pipeline_type == 'invoice':
            return bp.create_invoice_config()
        elif self.config.pipeline_type == 'document':
            return bp.create_document_config()
        else:
            # Custom config
            config = bp.PipelineConfig()
            config.enable_deskewing = True
            config.enable_thresholding = True
            config.enable_contrast_enhancement = True
            return config
    
    def preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Preprocess image using OpenCV by default, with C++ pipeline as fallback
        
        Args:
            image: Input image as numpy array (RGB or BGR)
            
        Returns:
            Tuple of (processed_image, stats)
        """
        stats = {}
        
        # Primary: Use OpenCV preprocessing
        try:
            processed_image, opencv_stats = self._opencv_preprocessing(image)
            stats.update(opencv_stats)
            stats['preprocessing_method'] = 'opencv_primary'
            return processed_image, stats
            
        except Exception as e:
            self.logger.warning(f"OpenCV preprocessing failed: {e}")
            
            # Fallback: Use C++ preprocessing pipeline if available
            if PREPROCESSING_AVAILABLE and self.preprocessing_config:
                self.logger.info("Falling back to C++ preprocessing pipeline")
                try:
                    if self.config.pipeline_type == 'invoice':
                        result = bp.process_invoice_pipeline(image)
                    elif self.config.pipeline_type == 'document':
                        result = bp.process_document_pipeline(image)
                    else:
                        result = bp.process_custom_pipeline(image, self.preprocessing_config)
                    
                    if result.success:
                        processed_image = result.get_final_numpy()
                        stats = {
                            'skew_angle': result.detected_skew_angle,
                            'otsu_threshold': result.otsu_threshold,
                            'steps_completed': len(result.step_names),
                            'preprocessing_method': 'cpp_fallback'
                        }
                        return processed_image, stats
                    else:
                        self.logger.error(f"C++ preprocessing also failed: {result.error_message}")
                        
                except Exception as cpp_e:
                    self.logger.error(f"C++ preprocessing fallback error: {cpp_e}")
            
            # Final fallback: Basic image normalization
            self.logger.warning("Using minimal preprocessing as last resort")
            processed_image, minimal_stats = self._minimal_preprocessing(image)
            stats.update(minimal_stats)
            stats['preprocessing_method'] = 'minimal_fallback'
            
            return processed_image, stats
    
    def _opencv_preprocessing(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Simple OpenCV-based preprocessing fallback"""
        stats = {}
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Basic contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        # Threshold
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        stats['otsu_threshold'] = _
        stats['skew_angle'] = 0.0  # No skew correction in fallback
        
        return thresh, stats
    
    def _minimal_preprocessing(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Minimal preprocessing as final fallback when everything else fails
        
        Args:
            image: Input image array
            
        Returns:
            Tuple of (processed_image, stats)
        """
        stats = {}
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # Simple threshold (just use a fixed value)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            stats['otsu_threshold'] = 127
            stats['skew_angle'] = 0.0
            stats['fallback_reason'] = 'all_preprocessing_failed'
            
            return thresh, stats
            
        except Exception as e:
            # Last resort - just return the input image converted to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            stats['otsu_threshold'] = 0
            stats['skew_angle'] = 0.0
            stats['fallback_reason'] = 'emergency_fallback'
            stats['error'] = str(e)
            
            return gray, stats
    
    def _prepare_image_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Prepare image for pytesseract by ensuring correct format and data type
        
        Args:
            image: Input image array
            
        Returns:
            Image ready for OCR processing
        """
        # Ensure image is in uint8 format
        if image.dtype != np.uint8:
            if image.dtype == np.float32 or image.dtype == np.float64:
                # Convert from float [0,1] to uint8 [0,255]
                if image.max() <= 1.0:
                    image = (image * 255).astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
            else:
                image = image.astype(np.uint8)
        
        # Handle different image shapes
        if len(image.shape) == 3:
            if image.shape[2] == 1:
                # Single channel with explicit dimension - squeeze it
                image = image.squeeze(axis=2)
            elif image.shape[2] == 3:
                # RGB image - convert to grayscale for better OCR
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            elif image.shape[2] == 4:
                # RGBA image - convert to grayscale
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        elif len(image.shape) == 2:
            # Already grayscale - good to go
            pass
        else:
            raise ValueError(f"Unsupported image shape: {image.shape}")
        
        # Ensure minimum size for OCR
        min_height, min_width = 20, 20
        if image.shape[0] < min_height or image.shape[1] < min_width:
            # Resize to minimum size
            scale_h = min_height / image.shape[0] if image.shape[0] < min_height else 1
            scale_w = min_width / image.shape[1] if image.shape[1] < min_width else 1
            scale = max(scale_h, scale_w)
            
            new_height = int(image.shape[0] * scale)
            new_width = int(image.shape[1] * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return image
    
    def extract_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract text from image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            OCRResult with extracted text and metadata
        """
        try:
            # Validate and normalize input image
            if image.size == 0:
                raise ValueError("Error: Empty image provided")
            
            # Ensure image has proper dimensions
            if len(image.shape) == 1 or min(image.shape[:2]) < 1:
                raise ValueError(f"Invalid image dimensions: {image.shape}")
            
            # Preprocess image
            processed_image, preprocessing_stats = self.preprocess_image(image)
            
            # Ensure processed image is in correct format for pytesseract
            processed_image = self._prepare_image_for_ocr(processed_image)
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(
                processed_image,
                lang=self.config.language,
                config=self.config.tesseract_config
            )
            
            # Get detailed data if requested
            word_boxes = []
            line_boxes = []
            confidence = 0.0
            
            if self.config.include_word_boxes or self.config.include_line_boxes:
                data = pytesseract.image_to_data(
                    processed_image,
                    lang=self.config.language,
                    config=self.config.tesseract_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Extract word boxes and calculate confidence
                confidences = []
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > self.config.confidence_threshold:
                        word_text = data['text'][i].strip()
                        if word_text:  # Non-empty text
                            confidences.append(int(data['conf'][i]))
                            
                            if self.config.include_word_boxes:
                                word_boxes.append({
                                    'text': word_text,
                                    'confidence': int(data['conf'][i]),
                                    'x': int(data['left'][i]),
                                    'y': int(data['top'][i]),
                                    'width': int(data['width'][i]),
                                    'height': int(data['height'][i]),
                                    'page': int(data['page_num'][i]),
                                    'block': int(data['block_num'][i]),
                                    'paragraph': int(data['par_num'][i]),
                                    'line': int(data['line_num'][i]),
                                    'word': int(data['word_num'][i])
                                })
                
                # Calculate average confidence
                confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                # Extract line boxes if requested
                if self.config.include_line_boxes:
                    line_boxes = self._extract_line_boxes(data)
            
            return OCRResult(
                text=text.strip(),
                confidence=confidence,
                word_boxes=word_boxes,
                line_boxes=line_boxes,
                preprocessing_stats=preprocessing_stats,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                word_boxes=[],
                line_boxes=[],
                preprocessing_stats={},
                success=False,
                error_message=str(e)
            )
    
    def _extract_line_boxes(self, data: Dict) -> List[Dict]:
        """Extract line-level bounding boxes from tesseract data"""
        lines = {}
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > self.config.confidence_threshold:
                word_text = data['text'][i].strip()
                if word_text:
                    line_key = (
                        int(data['page_num'][i]),
                        int(data['block_num'][i]),
                        int(data['par_num'][i]),
                        int(data['line_num'][i])
                    )
                    
                    if line_key not in lines:
                        lines[line_key] = {
                            'text': word_text,
                            'confidence': [int(data['conf'][i])],
                            'x': int(data['left'][i]),
                            'y': int(data['top'][i]),
                            'right': int(data['left'][i]) + int(data['width'][i]),
                            'bottom': int(data['top'][i]) + int(data['height'][i]),
                            'page': int(data['page_num'][i]),
                            'block': int(data['block_num'][i]),
                            'paragraph': int(data['par_num'][i]),
                            'line': int(data['line_num'][i])
                        }
                    else:
                        # Extend existing line
                        lines[line_key]['text'] += ' ' + word_text
                        lines[line_key]['confidence'].append(int(data['conf'][i]))
                        lines[line_key]['x'] = min(lines[line_key]['x'], int(data['left'][i]))
                        lines[line_key]['y'] = min(lines[line_key]['y'], int(data['top'][i]))
                        lines[line_key]['right'] = max(
                            lines[line_key]['right'],
                            int(data['left'][i]) + int(data['width'][i])
                        )
                        lines[line_key]['bottom'] = max(
                            lines[line_key]['bottom'],
                            int(data['top'][i]) + int(data['height'][i])
                        )
        
        # Convert to final format
        line_boxes = []
        for line_data in lines.values():
            line_boxes.append({
                'text': line_data['text'],
                'confidence': sum(line_data['confidence']) / len(line_data['confidence']),
                'x': line_data['x'],
                'y': line_data['y'],
                'width': line_data['right'] - line_data['x'],
                'height': line_data['bottom'] - line_data['y'],
                'page': line_data['page'],
                'block': line_data['block'],
                'paragraph': line_data['paragraph'],
                'line': line_data['line']
            })
        
        return line_boxes
    
    def process_image_file(self, image_path: Union[str, Path]) -> OCRResult:
        """
        Process an image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            OCRResult with extracted text and metadata
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            return self.extract_text(image)
            
        except Exception as e:
            return OCRResult(
                text="",
                confidence=0.0,
                word_boxes=[],
                line_boxes=[],
                preprocessing_stats={},
                success=False,
                error_message=f"Failed to process file {image_path}: {e}"
            )
    
    def batch_process(self, image_paths: List[Union[str, Path]]) -> List[OCRResult]:
        """
        Process multiple images
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            List of OCRResult objects
        """
        results = []
        for image_path in image_paths:
            result = self.process_image_file(image_path)
            results.append(result)
            self.logger.info(f"Processed {image_path}: {'✓' if result.success else '✗'}")
        
        return results


def create_ocr_engine(
    tesseract_config: str = '--oem 3 --psm 6',
    enable_preprocessing: bool = True,
    pipeline_type: str = 'invoice'
) -> OCREngine:
    """
    Convenience function to create OCR engine with common configurations
    
    Args:
        tesseract_config: Tesseract configuration string
        enable_preprocessing: Whether to enable preprocessing (OpenCV primary, C++ fallback)
        pipeline_type: Type of preprocessing pipeline ('invoice', 'document', 'custom')
        
    Returns:
        Configured OCREngine instance (uses OpenCV preprocessing by default)
    """
    config = OCRConfig(
        tesseract_config=tesseract_config,
        enable_preprocessing=enable_preprocessing,
        pipeline_type=pipeline_type
    )
    
    return OCREngine(config)


# Common OCR configurations
INVOICE_OCR_CONFIG = OCRConfig(
    tesseract_config='--oem 3 --psm 6',  # Single uniform block
    pipeline_type='invoice',
    include_word_boxes=True,
    include_line_boxes=True
)

DOCUMENT_OCR_CONFIG = OCRConfig(
    tesseract_config='--oem 3 --psm 3',  # Fully automatic page segmentation
    pipeline_type='document',
    include_word_boxes=True,
    include_line_boxes=True
)

FAST_OCR_CONFIG = OCRConfig(
    tesseract_config='--oem 3 --psm 6',  # Fast processing
    pipeline_type='invoice',
    include_word_boxes=False,
    include_line_boxes=False
)
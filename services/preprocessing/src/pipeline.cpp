#include "pipeline.h"
#include "grayscale.h"
#include "deskew.h"
#include "filter.h"
#include "contrast.h"
#include "resize.h"
#include "threshold.h"
#include <iostream>
#include <filesystem>
#include <stdexcept>
#include <algorithm>
#include <cctype>

PipelineResult process_for_ocr(const Image& input_image, const PipelineConfig& config) {
    PipelineResult result{Image(1, 1, 1), {}, {}, 0.0f, 0, false, ""};
    
    try {
        Image current_image = input_image;
        
        if (config.save_intermediate_steps) {
            result.intermediate_steps.push_back(current_image);
            result.step_names.push_back("00_original");
        }
        
        // Step 1: Convert to grayscale
        if (current_image.channels > 1) {
            current_image = to_grayscale_luminance(current_image);
            if (config.save_intermediate_steps) {
                result.intermediate_steps.push_back(current_image);
                result.step_names.push_back("01_grayscale");
            }
        }
        
        // Step 2: Deskewing (critical for OCR accuracy)
        if (config.enable_deskewing) {
            float skew_angle = estimate_skew_angle_projection(current_image, -config.max_skew_angle, config.max_skew_angle);
            result.detected_skew_angle = skew_angle;
            
            // Only deskew if angle is significant (> 0.5 degrees)
            if (std::abs(skew_angle) > 0.5f) {
                current_image = deskew(current_image, skew_angle);
                if (config.save_intermediate_steps) {
                    result.intermediate_steps.push_back(current_image);
                    result.step_names.push_back("02_deskewed");
                }
            }
        }
        
        // Step 3: Noise reduction (before contrast enhancement) --> usually not needed for most invoice formats
        if (config.enable_noise_reduction) {
            current_image = median_filter(current_image, config.median_filter_size);
            if (config.save_intermediate_steps) {
                result.intermediate_steps.push_back(current_image);
                result.step_names.push_back("03_noise_reduced");
            }
        }
        
        // Step 4: Contrast enhancement
        if (config.enable_contrast_enhancement) {
            if (config.use_histogram_equalization) {
                current_image = histogram_equalization(current_image);
            } else {
                current_image = normalize_contrast_percentile(current_image, config.percentile_low, config.percentile_high);
            }
            if (config.save_intermediate_steps) {
                result.intermediate_steps.push_back(current_image);
                result.step_names.push_back("04_contrast_enhanced");
            }
        }
        
        // Step 5: Resizing (if needed for standardization)
        if (config.enable_resizing) {
            if (config.target_width > 0 && config.target_height > 0) {
                current_image = resize_bilinear(current_image, config.target_width, config.target_height);
            } else if (config.target_width > 0) {
                current_image = scale_image_width(current_image, config.target_width);
            } else if (config.target_height > 0) {
                current_image = scale_image_height(current_image, config.target_height);
            } else if (config.scale_factor != 1.0f) {
                current_image = scale_image(current_image, config.scale_factor);
            }
            if (config.save_intermediate_steps) {
                result.intermediate_steps.push_back(current_image);
                result.step_names.push_back("05_resized");
            }
        }
        
        // Step 6: Final thresholding (for binary OCR input)
        if (config.enable_thresholding) {
            if (config.use_adaptive_threshold) {
                current_image = threshold_adaptive_mean(current_image, config.adaptive_block_size, config.adaptive_c);
            } else {
                result.otsu_threshold = calculate_otsu_threshold(current_image);
                current_image = threshold_otsu(current_image);
            }
            if (config.save_intermediate_steps) {
                result.intermediate_steps.push_back(current_image);
                result.step_names.push_back("06_thresholded");
            }
        }
        
        result.final_image = current_image;
        result.success = true;
        
    } catch (const std::exception& e) {
        result.error_message = e.what();
        result.success = false;
    }
    
    return result;
}

PipelineResult process_invoice_pipeline(const Image& input_image) {
    PipelineConfig config = create_invoice_config();
    return process_for_ocr(input_image, config);
}

PipelineResult process_document_pipeline(const Image& input_image) {
    PipelineConfig config = create_document_config();
    return process_for_ocr(input_image, config);
}

PipelineResult process_custom_pipeline(const Image& input_image, const PipelineConfig& config) {
    return process_for_ocr(input_image, config);
}

std::vector<PipelineResult> process_batch(const std::vector<std::string>& image_paths, const PipelineConfig& config) {
    std::vector<PipelineResult> results;
    results.reserve(image_paths.size());
    
    for (const std::string& path : image_paths) {
        try {
            Image img = load_image_rgb(path);
            PipelineResult result = process_for_ocr(img, config);
            results.push_back(std::move(result));
        } catch (const std::exception& e) {
            PipelineResult failed_result{Image(1, 1, 1), {}, {}, 0.0f, 0, false, "Failed to load image: " + path + " - " + e.what()};
            results.push_back(std::move(failed_result));
        }
    }
    
    return results;
}

bool process_directory(const std::string& input_dir, const std::string& output_dir, const PipelineConfig& config) {
    try {
        // Create output directory
        std::filesystem::create_directories(output_dir);
        
        // Find all image files
        std::vector<std::string> image_paths;
        for (const auto& entry : std::filesystem::directory_iterator(input_dir)) {
            if (entry.is_regular_file()) {
                std::string ext = entry.path().extension().string();
                std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
                if (ext == ".png" || ext == ".jpg" || ext == ".jpeg" || ext == ".bmp" || ext == ".tiff") {
                    image_paths.push_back(entry.path().string());
                }
            }
        }
        
        // Process each image
        for (const std::string& input_path : image_paths) {
            try {
                Image img = load_image_rgb(input_path);
                PipelineResult result = process_for_ocr(img, config);
                
                if (result.success) {
                    std::filesystem::path input_file_path(input_path);
                    std::string output_filename = config.output_prefix + "_" + input_file_path.stem().string() + ".png";
                    std::string output_path = (std::filesystem::path(output_dir) / output_filename).string();
                    
                    save_pipeline_result(result, output_path, config);
                    std::cout << "Processed: " << input_file_path.filename().string() << " -> " << output_filename << "\n";
                } else {
                    std::cerr << "Failed to process: " << input_path << " - " << result.error_message << "\n";
                }
            } catch (const std::exception& e) {
                std::cerr << "Error processing: " << input_path << " - " << e.what() << "\n";
            }
        }
        
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Directory processing error: " << e.what() << "\n";
        return false;
    }
}

void save_pipeline_result(const PipelineResult& result, const std::string& output_path, const PipelineConfig& config) {
    if (!result.success) {
        throw std::runtime_error("Cannot save failed pipeline result");
    }
    
    // Save final processed image
    save_image_auto(output_path, result.final_image);
    
    // Save intermediate steps if requested
    if (config.save_intermediate_steps && !result.intermediate_steps.empty()) {
        std::filesystem::path base_path(output_path);
        std::string base_name = base_path.stem().string();
        std::string extension = base_path.extension().string();
        std::string dir_path = base_path.parent_path().string();
        
        for (size_t i = 0; i < result.intermediate_steps.size(); ++i) {
            std::string step_filename = base_name + "_" + result.step_names[i] + extension;
            std::string step_path = (std::filesystem::path(dir_path) / step_filename).string();
            save_image_auto(step_path, result.intermediate_steps[i]);
        }
    }
}

PipelineConfig create_invoice_config() {
    PipelineConfig config;
    
    // Optimized for invoice processing
    config.enable_deskewing = true;
    config.max_skew_angle = 30.0f;  // Invoices rarely skewed more than 30 degrees
    
    config.enable_noise_reduction = false;
    config.median_filter_size = 3;  // Light noise reduction to preserve text quality
    
    config.enable_contrast_enhancement = true;
    config.use_histogram_equalization = false;  // Percentile normalization is better for text
    config.percentile_low = 1.0f;   // Aggressive contrast for better text separation
    config.percentile_high = 99.0f;
    
    config.enable_resizing = false;  // Keep original resolution for OCR accuracy
    
    config.enable_thresholding = true;
    config.use_adaptive_threshold = false;  // Otsu works well for invoices
    
    config.output_prefix = "invoice_processed";
    
    return config;
}

PipelineConfig create_document_config() {
    PipelineConfig config;
    
    // Optimized for general document processing
    config.enable_deskewing = true;
    config.max_skew_angle = 45.0f;
    
    config.enable_noise_reduction = true;
    config.median_filter_size = 3;
    
    config.enable_contrast_enhancement = true;
    config.use_histogram_equalization = false;
    config.percentile_low = 2.0f;
    config.percentile_high = 98.0f;
    
    config.enable_resizing = false;
    
    config.enable_thresholding = true;
    config.use_adaptive_threshold = false;
    
    config.output_prefix = "document_processed";
    
    return config;
}

void print_pipeline_summary(const PipelineResult& result) {
    if (!result.success) {
        std::cout << "Pipeline failed: " << result.error_message << "\n";
        return;
    }
    
    std::cout << "\n=== Pipeline Processing Summary ===\n";
    std::cout << "Status: SUCCESS\n";
    std::cout << "Final image size: " << result.final_image.width << "x" << result.final_image.height << "\n";
    std::cout << "Final image channels: " << result.final_image.channels << "\n";
    
    if (std::abs(result.detected_skew_angle) > 0.01f) {
        std::cout << "Detected skew angle: " << result.detected_skew_angle << " degrees\n";
    }
    
    if (result.otsu_threshold > 0) {
        std::cout << "Otsu threshold value: " << static_cast<int>(result.otsu_threshold) << "\n";
    }
    
    if (!result.step_names.empty()) {
        std::cout << "Processing steps completed: " << result.step_names.size() << "\n";
        for (const std::string& step : result.step_names) {
            std::cout << "  - " << step << "\n";
        }
    }
    
    std::cout << "===================================\n\n";
}
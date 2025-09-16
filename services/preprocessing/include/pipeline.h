#pragma once
#include "image.h"
#include <string>
#include <vector>

struct PipelineConfig {
    // Deskewing parameters
    bool enable_deskewing = true;
    float max_skew_angle = 45.0f;
    
    // Noise reduction parameters
    bool enable_noise_reduction = true;
    int median_filter_size = 3;
    
    // Contrast enhancement parameters
    bool enable_contrast_enhancement = true;
    bool use_histogram_equalization = false;  // false = use normalization
    float percentile_low = 2.0f;
    float percentile_high = 98.0f;
    
    // Resizing parameters
    bool enable_resizing = false;
    int target_width = 0;   // 0 = no resizing
    int target_height = 0;  // 0 = no resizing
    float scale_factor = 1.0f;  // 1.0 = no scaling
    
    // Thresholding parameters
    bool enable_thresholding = true;
    bool use_adaptive_threshold = false;  // false = use Otsu
    int adaptive_block_size = 11;
    int adaptive_c = 2;
    
    // Output parameters
    bool save_intermediate_steps = false;
    std::string output_prefix = "processed";
};

struct PipelineResult {
    Image final_image;
    std::vector<Image> intermediate_steps;
    std::vector<std::string> step_names;
    float detected_skew_angle = 0.0f;
    uint8_t otsu_threshold = 0;
    bool success = false;
    std::string error_message;
};

// Main pipeline functions
PipelineResult process_for_ocr(const Image& input_image, const PipelineConfig& config = PipelineConfig{});
PipelineResult process_invoice_pipeline(const Image& input_image);
PipelineResult process_document_pipeline(const Image& input_image);
PipelineResult process_custom_pipeline(const Image& input_image, const PipelineConfig& config);

// Batch processing functions
std::vector<PipelineResult> process_batch(const std::vector<std::string>& image_paths, const PipelineConfig& config = PipelineConfig{});
bool process_directory(const std::string& input_dir, const std::string& output_dir, const PipelineConfig& config = PipelineConfig{});

// Utility functions
void save_pipeline_result(const PipelineResult& result, const std::string& output_path, const PipelineConfig& config);
PipelineConfig create_invoice_config();
PipelineConfig create_document_config();
void print_pipeline_summary(const PipelineResult& result);
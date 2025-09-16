#include "threshold.h"
#include "grayscale.h"
#include <algorithm>
#include <vector>
#include <cmath>

uint8_t calculate_otsu_threshold(const Image& input_image) {
    // Grayscale if needed
    Image gray_img = input_image.channels == 1 ? input_image : to_grayscale_luminance(input_image);
    
    // Calculate histogram
    std::vector<int> histogram(256, 0);
    int total_pixels = gray_img.width * gray_img.height;
    
    for (int y = 0; y < gray_img.height; ++y) {
        for (int x = 0; x < gray_img.width; ++x) {
            uint8_t pixel_val = const_cast<Image&>(gray_img).pixel(x, y)[0];
            histogram[pixel_val]++;
        }
    }
    
    // Calculate sum of all pixel values
    float sum = 0.0f;
    for (int i = 0; i < 256; ++i) {
        sum += i * histogram[i];
    }
    
    float sum_background = 0.0f;
    int weight_background = 0;
    float max_variance = 0.0f;
    uint8_t optimal_threshold = 0;
    
    // Try all possible threshold values
    for (int threshold = 0; threshold < 256; ++threshold) {
        weight_background += histogram[threshold];
        if (weight_background == 0) continue;
        
        int weight_foreground = total_pixels - weight_background;
        if (weight_foreground == 0) break;
        
        sum_background += threshold * histogram[threshold];
        
        float mean_background = sum_background / weight_background;
        float mean_foreground = (sum - sum_background) / weight_foreground;
        
        // Calculate between-class variance
        float variance = weight_background * weight_foreground * 
                        (mean_background - mean_foreground) * (mean_background - mean_foreground);
        
        if (variance > max_variance) {
            max_variance = variance;
            optimal_threshold = threshold;
        }
    }
    
    return optimal_threshold;
}

uint8_t calculate_mean_threshold(const Image& input_image) {
    // Grayscale if needed
    Image gray_img = input_image.channels == 1 ? input_image : to_grayscale_luminance(input_image);
    
    long long sum = 0;
    int total_pixels = gray_img.width * gray_img.height;
    
    for (int y = 0; y < gray_img.height; ++y) {
        for (int x = 0; x < gray_img.width; ++x) {
            sum += const_cast<Image&>(gray_img).pixel(x, y)[0];
        }
    }
    
    return static_cast<uint8_t>(sum / total_pixels);
}

Image threshold_otsu(const Image& input_image) {
    uint8_t threshold_value = calculate_otsu_threshold(input_image);
    return threshold_binary(input_image, threshold_value);
}

Image threshold_binary(const Image& input_image, uint8_t threshold_value) {
    // Convert to grayscale if needed
    Image gray_img = input_image.channels == 1 ? input_image : to_grayscale_luminance(input_image);
    Image thresholded_img(gray_img.width, gray_img.height, 1);
    
    for (int y = 0; y < gray_img.height; ++y) {
        for (int x = 0; x < gray_img.width; ++x) {
            uint8_t pixel_val = const_cast<Image&>(gray_img).pixel(x, y)[0];
            thresholded_img.pixel(x, y)[0] = pixel_val >= threshold_value ? 255 : 0;
        }
    }
    
    return thresholded_img;
}

Image threshold_binary_inverted(const Image& input_image, uint8_t threshold_value) {
    // Convert to grayscale if needed
    Image gray_img = input_image.channels == 1 ? input_image : to_grayscale_luminance(input_image);
    Image thresholded_img(gray_img.width, gray_img.height, 1);
    
    for (int y = 0; y < gray_img.height; ++y) {
        for (int x = 0; x < gray_img.width; ++x) {
            uint8_t pixel_val = const_cast<Image&>(gray_img).pixel(x, y)[0];
            thresholded_img.pixel(x, y)[0] = pixel_val >= threshold_value ? 0 : 255;
        }
    }
    
    return thresholded_img;
}

Image threshold_adaptive_mean(const Image& input_image, int block_size, int c) {
    if (block_size % 2 == 0) {
        block_size++;  // Ensure odd block size
    }
    
    // Grayscale if needed
    Image gray_img = input_image.channels == 1 ? input_image : to_grayscale_luminance(input_image);
    Image thresholded_img(gray_img.width, gray_img.height, 1);
    int half_block = block_size / 2;
    
    for (int y = 0; y < gray_img.height; ++y) {
        for (int x = 0; x < gray_img.width; ++x) {
            // Calculate mean in local neighborhood
            long long sum = 0;
            int count = 0;
            
            for (int by = -half_block; by <= half_block; ++by) {
                for (int bx = -half_block; bx <= half_block; ++bx) {
                    int px = std::max(0, std::min(x + bx, gray_img.width - 1));
                    int py = std::max(0, std::min(y + by, gray_img.height - 1));
                    sum += const_cast<Image&>(gray_img).pixel(px, py)[0];
                    count++;
                }
            }
            
            uint8_t local_mean = static_cast<uint8_t>(sum / count);
            uint8_t pixel_val = const_cast<Image&>(gray_img).pixel(x, y)[0];
            uint8_t adaptive_threshold = std::max(0, static_cast<int>(local_mean) - c);
            
            thresholded_img.pixel(x, y)[0] = pixel_val >= adaptive_threshold ? 255 : 0;
        }
    }
    
    return thresholded_img;
}

Image threshold_adaptive_gaussian(const Image& input_image, int block_size, int c) {
    if (block_size % 2 == 0) {
        block_size++;  // Ensure odd block size
    }
    
    // Grayscale if needed
    Image gray_img = input_image.channels == 1 ? input_image : to_grayscale_luminance(input_image);
    Image thresholded_img(gray_img.width, gray_img.height, 1);
    int half_block = block_size / 2;
    
    // Generate Gaussian weights
    std::vector<std::vector<float>> weights(block_size, std::vector<float>(block_size));
    float sigma = block_size / 6.0f;  // Standard deviation
    float sum_weights = 0.0f;
    
    for (int by = -half_block; by <= half_block; ++by) {
        for (int bx = -half_block; bx <= half_block; ++bx) {
            float weight = std::exp(-(bx*bx + by*by) / (2.0f * sigma * sigma));
            weights[by + half_block][bx + half_block] = weight;
            sum_weights += weight;
        }
    }
    
    // Normalize weights
    for (int by = 0; by < block_size; ++by) {
        for (int bx = 0; bx < block_size; ++bx) {
            weights[by][bx] /= sum_weights;
        }
    }
    
    for (int y = 0; y < gray_img.height; ++y) {
        for (int x = 0; x < gray_img.width; ++x) {
            // Calculate weighted mean in local neighborhood
            float weighted_sum = 0.0f;
            
            for (int by = -half_block; by <= half_block; ++by) {
                for (int bx = -half_block; bx <= half_block; ++bx) {
                    int px = std::max(0, std::min(x + bx, gray_img.width - 1));
                    int py = std::max(0, std::min(y + by, gray_img.height - 1));
                    float weight = weights[by + half_block][bx + half_block];
                    weighted_sum += const_cast<Image&>(gray_img).pixel(px, py)[0] * weight;
                }
            }
            
            uint8_t gaussian_mean = static_cast<uint8_t>(weighted_sum);
            uint8_t pixel_val = const_cast<Image&>(gray_img).pixel(x, y)[0];
            uint8_t adaptive_threshold = std::max(0, static_cast<int>(gaussian_mean) - c);
            
            thresholded_img.pixel(x, y)[0] = pixel_val >= adaptive_threshold ? 255 : 0;
        }
    }
    
    return thresholded_img;
}
#include "contrast.h"
#include <algorithm>
#include <vector>
#include <cmath>

Image normalize_contrast(const Image& input_image) {
    return normalize_contrast_minmax(input_image);
}

Image normalize_contrast_minmax(const Image& input_image) {
    Image normalized_img(input_image.width, input_image.height, input_image.channels);
    
    for (int c = 0; c < input_image.channels; ++c) {
        uint8_t min_val = 255;
        uint8_t max_val = 0;
        
        // Find min and max values for this channel
        for (int y = 0; y < input_image.height; ++y) {
            for (int x = 0; x < input_image.width; ++x) {
                uint8_t pixel_val = const_cast<Image&>(input_image).pixel(x, y)[c];
                min_val = std::min(min_val, pixel_val);
                max_val = std::max(max_val, pixel_val);
            }
        }
        
        // Normalize pixels for this channel
        float range = static_cast<float>(max_val - min_val);
        if (range > 0) {
            for (int y = 0; y < input_image.height; ++y) {
                for (int x = 0; x < input_image.width; ++x) {
                    uint8_t original_val = const_cast<Image&>(input_image).pixel(x, y)[c];
                    float normalized = (original_val - min_val) * 255.0f / range;
                    normalized_img.pixel(x, y)[c] = static_cast<uint8_t>(std::round(normalized));
                }
            }
        } else {
            // If all pixels have the same value, keep them as is
            for (int y = 0; y < input_image.height; ++y) {
                for (int x = 0; x < input_image.width; ++x) {
                    normalized_img.pixel(x, y)[c] = const_cast<Image&>(input_image).pixel(x, y)[c];
                }
            }
        }
    }
    
    return normalized_img;
}

Image normalize_contrast_percentile(const Image& input_image, float low_percentile, float high_percentile) {
    Image normalized_img(input_image.width, input_image.height, input_image.channels);
    
    for (int c = 0; c < input_image.channels; ++c) {
        std::vector<uint8_t> channel_values;
        channel_values.reserve(input_image.width * input_image.height);
        
        // Collect all pixel values for this channel
        for (int y = 0; y < input_image.height; ++y) {
            for (int x = 0; x < input_image.width; ++x) {
                channel_values.push_back(const_cast<Image&>(input_image).pixel(x, y)[c]);
            }
        }
        
        // Sort to find percentile values
        std::sort(channel_values.begin(), channel_values.end());
        
        int low_idx = static_cast<int>(channel_values.size() * low_percentile / 100.0f);
        int high_idx = static_cast<int>(channel_values.size() * high_percentile / 100.0f);
        low_idx = std::max(0, std::min(low_idx, static_cast<int>(channel_values.size()) - 1));
        high_idx = std::max(0, std::min(high_idx, static_cast<int>(channel_values.size()) - 1));
        
        uint8_t low_val = channel_values[low_idx];
        uint8_t high_val = channel_values[high_idx];
        
        // Normalize pixels for this channel using percentile range
        float range = static_cast<float>(high_val - low_val);
        if (range > 0) {
            for (int y = 0; y < input_image.height; ++y) {
                for (int x = 0; x < input_image.width; ++x) {
                    uint8_t original_val = const_cast<Image&>(input_image).pixel(x, y)[c];
                    float normalized = std::max(0.0f, std::min(255.0f, (original_val - low_val) * 255.0f / range));
                    normalized_img.pixel(x, y)[c] = static_cast<uint8_t>(std::round(normalized));
                }
            }
        } else {
            for (int y = 0; y < input_image.height; ++y) {
                for (int x = 0; x < input_image.width; ++x) {
                    normalized_img.pixel(x, y)[c] = const_cast<Image&>(input_image).pixel(x, y)[c];
                }
            }
        }
    }
    
    return normalized_img;
}

Image histogram_equalization(const Image& input_image) {
    Image equalized_img(input_image.width, input_image.height, input_image.channels);
    
    for (int c = 0; c < input_image.channels; ++c) {
        // Calculate histogram
        std::vector<int> histogram(256, 0);
        for (int y = 0; y < input_image.height; ++y) {
            for (int x = 0; x < input_image.width; ++x) {
                uint8_t pixel_val = const_cast<Image&>(input_image).pixel(x, y)[c];
                histogram[pixel_val]++;
            }
        }
        
        // Calculate cumulative distribution function (CDF)
        std::vector<float> cdf(256, 0.0f);
        cdf[0] = static_cast<float>(histogram[0]);
        for (int i = 1; i < 256; ++i) {
            cdf[i] = cdf[i-1] + histogram[i];
        }
        
        // Normalize CDF
        float total_pixels = static_cast<float>(input_image.width * input_image.height);
        for (int i = 0; i < 256; ++i) {
            cdf[i] = cdf[i] / total_pixels * 255.0f;
        }
        
        // Apply histogram equalization
        for (int y = 0; y < input_image.height; ++y) {
            for (int x = 0; x < input_image.width; ++x) {
                uint8_t original_val = const_cast<Image&>(input_image).pixel(x, y)[c];
                equalized_img.pixel(x, y)[c] = static_cast<uint8_t>(std::round(cdf[original_val]));
            }
        }
    }
    
    return equalized_img;
}

Image adaptive_histogram_equalization(const Image& input_image, int tile_size) {
    Image equalized_img(input_image.width, input_image.height, input_image.channels);
    
    for (int c = 0; c < input_image.channels; ++c) {
        for (int tile_y = 0; tile_y < input_image.height; tile_y += tile_size) {
            for (int tile_x = 0; tile_x < input_image.width; tile_x += tile_size) {
                int end_x = std::min(tile_x + tile_size, input_image.width);
                int end_y = std::min(tile_y + tile_size, input_image.height);
                
                // Calculate histogram for this tile
                std::vector<int> histogram(256, 0);
                int tile_pixels = 0;
                for (int y = tile_y; y < end_y; ++y) {
                    for (int x = tile_x; x < end_x; ++x) {
                        uint8_t pixel_val = const_cast<Image&>(input_image).pixel(x, y)[c];
                        histogram[pixel_val]++;
                        tile_pixels++;
                    }
                }
                
                // Calculate CDF for this tile
                std::vector<float> cdf(256, 0.0f);
                cdf[0] = static_cast<float>(histogram[0]);
                for (int i = 1; i < 256; ++i) {
                    cdf[i] = cdf[i-1] + histogram[i];
                }
                
                // Normalize CDF
                for (int i = 0; i < 256; ++i) {
                    cdf[i] = cdf[i] / tile_pixels * 255.0f;
                }
                
                // Apply equalization to this tile
                for (int y = tile_y; y < end_y; ++y) {
                    for (int x = tile_x; x < end_x; ++x) {
                        uint8_t original_val = const_cast<Image&>(input_image).pixel(x, y)[c];
                        equalized_img.pixel(x, y)[c] = static_cast<uint8_t>(std::round(cdf[original_val]));
                    }
                }
            }
        }
    }
    
    return equalized_img;
}
#include "deskew.h"
#include "grayscale.h"
#include "threshold.h"
#include <algorithm>
#include <vector>
#include <cmath>

const float PI = 3.14159265359f;

float estimate_skew_angle(const Image& input_image, float min_angle, float max_angle, float angle_step) {
    return estimate_skew_angle_projection(input_image, min_angle, max_angle);
}

float estimate_skew_angle_projection(const Image& input_image, float min_angle, float max_angle) {
    // Convert to grayscale and threshold for better edge detection
    Image gray_img = input_image.channels == 1 ? input_image : to_grayscale_luminance(input_image);
    Image binary_img = threshold_otsu(gray_img);
    
    float best_angle = 0.0f;
    float max_variance = 0.0f;
    
    // Test angles from min_angle to max_angle
    for (float angle = min_angle; angle <= max_angle; angle += 0.5f) {
        float rad = angle * PI / 180.0f;
        float cos_a = std::cos(rad);
        float sin_a = std::sin(rad);
        
        // Calculate projection profile variance for this angle
        std::vector<int> projection(binary_img.height, 0);
        
        for (int y = 0; y < binary_img.height; ++y) {
            for (int x = 0; x < binary_img.width; ++x) {
                // Rotate point and project onto y-axis
                float rotated_x = x * cos_a - y * sin_a;
                float rotated_y = x * sin_a + y * cos_a;
                
                int proj_y = static_cast<int>(rotated_y);
                if (proj_y >= 0 && proj_y < binary_img.height) {
                    uint8_t pixel_val = const_cast<Image&>(binary_img).pixel(x, y)[0];
                    if (pixel_val == 0) {  // Black pixels (text)
                        projection[proj_y]++;
                    }
                }
            }
        }
        
        // Calculate variance of projection profile
        float mean = 0.0f;
        for (int count : projection) {
            mean += count;
        }
        mean /= projection.size();
        
        float variance = 0.0f;
        for (int count : projection) {
            variance += (count - mean) * (count - mean);
        }
        variance /= projection.size();
        
        // Higher variance indicates better text line alignment
        if (variance > max_variance) {
            max_variance = variance;
            best_angle = angle;
        }
    }
    
    return best_angle;
}

float estimate_skew_angle_hough(const Image& input_image, float min_angle, float max_angle) {
    // Convert to grayscale and threshold
    Image gray_img = input_image.channels == 1 ? input_image : to_grayscale_luminance(input_image);
    Image binary_img = threshold_otsu(gray_img);
    
    // Simple Hough transform for line detection
    int angle_range = static_cast<int>((max_angle - min_angle) * 2); // 0.5 degree steps
    int max_rho = static_cast<int>(std::sqrt(binary_img.width * binary_img.width + binary_img.height * binary_img.height));
    
    std::vector<std::vector<int>> accumulator(angle_range, std::vector<int>(max_rho * 2, 0));
    
    // Find edge pixels and vote in Hough space
    for (int y = 1; y < binary_img.height - 1; ++y) {
        for (int x = 1; x < binary_img.width - 1; ++x) {
            uint8_t current = const_cast<Image&>(binary_img).pixel(x, y)[0];
            uint8_t right = const_cast<Image&>(binary_img).pixel(x + 1, y)[0];
            uint8_t bottom = const_cast<Image&>(binary_img).pixel(x, y + 1)[0];
            
            // Simple edge detection
            if (std::abs(current - right) > 128 || std::abs(current - bottom) > 128) {
                // Vote for different angles
                for (int a = 0; a < angle_range; ++a) {
                    float angle = min_angle + a * 0.5f;
                    float rad = angle * PI / 180.0f;
                    int rho = static_cast<int>(x * std::cos(rad) + y * std::sin(rad)) + max_rho;
                    
                    if (rho >= 0 && rho < max_rho * 2) {
                        accumulator[a][rho]++;
                    }
                }
            }
        }
    }
    
    // Find peak in accumulator
    int max_votes = 0;
    int best_angle_idx = 0;
    for (int a = 0; a < angle_range; ++a) {
        for (int r = 0; r < max_rho * 2; ++r) {
            if (accumulator[a][r] > max_votes) {
                max_votes = accumulator[a][r];
                best_angle_idx = a;
            }
        }
    }
    
    return min_angle + best_angle_idx * 0.5f;
}

Image rotate_image(const Image& input_image, float angle_degrees, uint8_t background_color) {
    if (std::abs(angle_degrees) < 0.01f) {
        return input_image;  // No rotation needed
    }
    
    float rad = angle_degrees * PI / 180.0f;
    float cos_a = std::cos(rad);
    float sin_a = std::sin(rad);
    
    // Calculate new image dimensions
    int old_width = input_image.width;
    int old_height = input_image.height;
    
    float corners_x[] = {0.0f, static_cast<float>(old_width), static_cast<float>(old_width), 0.0f};
    float corners_y[] = {0.0f, 0.0f, static_cast<float>(old_height), static_cast<float>(old_height)};
    
    float min_x = 0, max_x = 0, min_y = 0, max_y = 0;
    for (int i = 0; i < 4; ++i) {
        float new_x = corners_x[i] * cos_a - corners_y[i] * sin_a;
        float new_y = corners_x[i] * sin_a + corners_y[i] * cos_a;
        
        min_x = std::min(min_x, new_x);
        max_x = std::max(max_x, new_x);
        min_y = std::min(min_y, new_y);
        max_y = std::max(max_y, new_y);
    }
    
    int new_width = static_cast<int>(max_x - min_x + 0.5f);
    int new_height = static_cast<int>(max_y - min_y + 0.5f);
    
    float offset_x = -min_x;
    float offset_y = -min_y;
    
    Image rotated_img(new_width, new_height, input_image.channels);
    
    // Fill with background color
    for (int y = 0; y < new_height; ++y) {
        for (int x = 0; x < new_width; ++x) {
            for (int c = 0; c < input_image.channels; ++c) {
                rotated_img.pixel(x, y)[c] = background_color;
            }
        }
    }
    
    // Inverse rotation mapping
    for (int y = 0; y < new_height; ++y) {
        for (int x = 0; x < new_width; ++x) {
            // Transform to original coordinate system
            float src_x = (x - offset_x) * cos_a + (y - offset_y) * sin_a;
            float src_y = -(x - offset_x) * sin_a + (y - offset_y) * cos_a;
            
            int src_x_int = static_cast<int>(src_x + 0.5f);
            int src_y_int = static_cast<int>(src_y + 0.5f);
            
            // Check bounds and copy pixel
            if (src_x_int >= 0 && src_x_int < old_width && 
                src_y_int >= 0 && src_y_int < old_height) {
                for (int c = 0; c < input_image.channels; ++c) {
                    rotated_img.pixel(x, y)[c] = const_cast<Image&>(input_image).pixel(src_x_int, src_y_int)[c];
                }
            }
        }
    }
    
    return rotated_img;
}

Image deskew(const Image& input_image, float angle_degrees) {
    return rotate_image(input_image, -angle_degrees, 255);  // Negative angle to correct skew
}

Image deskew_auto(const Image& input_image) {
    float skew_angle = estimate_skew_angle(input_image);
    return deskew(input_image, skew_angle);
}

Image deskew_manual(const Image& input_image, float angle_degrees) {
    return deskew(input_image, angle_degrees);
}
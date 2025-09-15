#include "resize.h"
#include <algorithm>
#include <cmath>

Image resize_nearest_neighbor(const Image& input_image, int new_width, int new_height) {
    Image resized_img(new_width, new_height, input_image.channels);
    
    float x_ratio = static_cast<float>(input_image.width) / new_width;
    float y_ratio = static_cast<float>(input_image.height) / new_height;
    
    for (int y = 0; y < new_height; ++y) {
        for (int x = 0; x < new_width; ++x) {
            int src_x = static_cast<int>(x * x_ratio);
            int src_y = static_cast<int>(y * y_ratio);
            
            src_x = std::min(src_x, input_image.width - 1);
            src_y = std::min(src_y, input_image.height - 1);
            
            const uint8_t* src_pixel = const_cast<Image&>(input_image).pixel(src_x, src_y);
            uint8_t* dst_pixel = resized_img.pixel(x, y);
            
            for (int c = 0; c < input_image.channels; ++c) {
                dst_pixel[c] = src_pixel[c];
            }
        }
    }
    
    return resized_img;
}

Image resize_bilinear(const Image& input_image, int new_width, int new_height) {
    Image resized_img(new_width, new_height, input_image.channels);
    
    float x_ratio = static_cast<float>(input_image.width - 1) / new_width;
    float y_ratio = static_cast<float>(input_image.height - 1) / new_height;
    
    for (int y = 0; y < new_height; ++y) {
        for (int x = 0; x < new_width; ++x) {
            float src_x = x * x_ratio;
            float src_y = y * y_ratio;
            
            int x1 = static_cast<int>(src_x);
            int y1 = static_cast<int>(src_y);
            int x2 = std::min(x1 + 1, input_image.width - 1);
            int y2 = std::min(y1 + 1, input_image.height - 1);
            
            float dx = src_x - x1;
            float dy = src_y - y1;
            
            uint8_t* dst_pixel = resized_img.pixel(x, y);
            
            for (int c = 0; c < input_image.channels; ++c) {
                uint8_t p11 = const_cast<Image&>(input_image).pixel(x1, y1)[c];
                uint8_t p12 = const_cast<Image&>(input_image).pixel(x1, y2)[c];
                uint8_t p21 = const_cast<Image&>(input_image).pixel(x2, y1)[c];
                uint8_t p22 = const_cast<Image&>(input_image).pixel(x2, y2)[c];
                
                float interpolated = p11 * (1 - dx) * (1 - dy) +
                                   p21 * dx * (1 - dy) +
                                   p12 * (1 - dx) * dy +
                                   p22 * dx * dy;
                
                dst_pixel[c] = static_cast<uint8_t>(std::round(interpolated));
            }
        }
    }
    
    return resized_img;
}

Image scale_image(const Image& input_image, float scale_factor) {
    int new_width = static_cast<int>(input_image.width * scale_factor);
    int new_height = static_cast<int>(input_image.height * scale_factor);
    
    return resize_bilinear(input_image, new_width, new_height);
}

Image scale_image_width(const Image& input_image, int target_width) {
    float scale_factor = static_cast<float>(target_width) / input_image.width;
    int new_height = static_cast<int>(input_image.height * scale_factor);
    
    return resize_bilinear(input_image, target_width, new_height);
}

Image scale_image_height(const Image& input_image, int target_height) {
    float scale_factor = static_cast<float>(target_height) / input_image.height;
    int new_width = static_cast<int>(input_image.width * scale_factor);
    
    return resize_bilinear(input_image, new_width, target_height);
}
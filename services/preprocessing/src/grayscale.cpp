#include "grayscale.h"
#include <algorithm>

Image to_grayscale(const Image& input_image) {
    return to_grayscale_luminance(input_image);
}

Image to_grayscale_luminance(const Image& input_image) {
    if (input_image.channels == 1) {
        return input_image;
    }
    
    Image grayscale_img(input_image.width, input_image.height, 1);
    
    for (int y = 0; y < input_image.height; ++y) {
        for (int x = 0; x < input_image.width; ++x) {
            const uint8_t* pixel = const_cast<Image&>(input_image).pixel(x, y);
            
            uint8_t gray_value;
            if (input_image.channels >= 3) {
                uint8_t r = pixel[0];
                uint8_t g = pixel[1];
                uint8_t b = pixel[2];
                gray_value = static_cast<uint8_t>(0.299 * r + 0.587 * g + 0.114 * b);
            } else {
                gray_value = pixel[0];
            }
            
            *grayscale_img.pixel(x, y) = gray_value;
        }
    }
    
    return grayscale_img;
}

Image to_grayscale_average(const Image& input_image) {
    if (input_image.channels == 1) {
        return input_image;
    }
    
    Image grayscale_img(input_image.width, input_image.height, 1);
    
    for (int y = 0; y < input_image.height; ++y) {
        for (int x = 0; x < input_image.width; ++x) {
            const uint8_t* pixel = const_cast<Image&>(input_image).pixel(x, y);
            
            uint8_t gray_value;
            if (input_image.channels >= 3) {
                uint8_t r = pixel[0];
                uint8_t g = pixel[1];
                uint8_t b = pixel[2];
                gray_value = static_cast<uint8_t>((r + g + b) / 3);
            } else {
                gray_value = pixel[0];
            }
            
            *grayscale_img.pixel(x, y) = gray_value;
        }
    }
    
    return grayscale_img;
}
#include "filter.h"
#include <algorithm>
#include <vector>
#include <cmath>

Image median_filter(const Image& input_image, int kernel_size) {
    if (kernel_size % 2 == 0) {
        kernel_size++;  // Odd kernel size
    }
    
    Image filtered_img(input_image.width, input_image.height, input_image.channels);
    int half_kernel = kernel_size / 2;
    
    for (int c = 0; c < input_image.channels; ++c) {
        for (int y = 0; y < input_image.height; ++y) {
            for (int x = 0; x < input_image.width; ++x) {
                std::vector<uint8_t> values;
                
                // Collect values in kernel neighborhood
                for (int ky = -half_kernel; ky <= half_kernel; ++ky) {
                    for (int kx = -half_kernel; kx <= half_kernel; ++kx) {
                        int px = std::max(0, std::min(x + kx, input_image.width - 1));
                        int py = std::max(0, std::min(y + ky, input_image.height - 1));
                        values.push_back(const_cast<Image&>(input_image).pixel(px, py)[c]);
                    }
                }
                
                // Find median
                std::sort(values.begin(), values.end());
                filtered_img.pixel(x, y)[c] = values[values.size() / 2];
            }
        }
    }
    
    return filtered_img;
}

Image median_filter_3x3(const Image& input_image) {
    return median_filter(input_image, 3);
}

Image median_filter_5x5(const Image& input_image) {
    return median_filter(input_image, 5);
}

Image gaussian_blur(const Image& input_image, float sigma, int kernel_size) {
    if (kernel_size == 0) {
        kernel_size = static_cast<int>(std::ceil(6.0f * sigma));
        if (kernel_size % 2 == 0) kernel_size++;
    }
    if (kernel_size % 2 == 0) {
        kernel_size++;  // Odd kernel size
    }
    
    // Generate Gaussian kernel
    int half_kernel = kernel_size / 2;
    std::vector<std::vector<float>> kernel(kernel_size, std::vector<float>(kernel_size));
    float sum = 0.0f;
    
    for (int y = -half_kernel; y <= half_kernel; ++y) {
        for (int x = -half_kernel; x <= half_kernel; ++x) {
            float value = std::exp(-(x*x + y*y) / (2.0f * sigma * sigma));
            kernel[y + half_kernel][x + half_kernel] = value;
            sum += value;
        }
    }
    
    // Normalize kernel
    for (int y = 0; y < kernel_size; ++y) {
        for (int x = 0; x < kernel_size; ++x) {
            kernel[y][x] /= sum;
        }
    }
    
    Image filtered_img(input_image.width, input_image.height, input_image.channels);
    
    for (int c = 0; c < input_image.channels; ++c) {
        for (int y = 0; y < input_image.height; ++y) {
            for (int x = 0; x < input_image.width; ++x) {
                float sum_val = 0.0f;
                
                for (int ky = -half_kernel; ky <= half_kernel; ++ky) {
                    for (int kx = -half_kernel; kx <= half_kernel; ++kx) {
                        int px = std::max(0, std::min(x + kx, input_image.width - 1));
                        int py = std::max(0, std::min(y + ky, input_image.height - 1));
                        float pixel_val = const_cast<Image&>(input_image).pixel(px, py)[c];
                        sum_val += pixel_val * kernel[ky + half_kernel][kx + half_kernel];
                    }
                }
                
                filtered_img.pixel(x, y)[c] = static_cast<uint8_t>(std::round(std::max(0.0f, std::min(255.0f, sum_val))));
            }
        }
    }
    
    return filtered_img;
}

Image gaussian_blur_3x3(const Image& input_image) {
    return gaussian_blur(input_image, 0.8f, 3);
}

Image gaussian_blur_5x5(const Image& input_image) {
    return gaussian_blur(input_image, 1.4f, 5);
}

Image gaussian_blur_strong(const Image& input_image) {
    return gaussian_blur(input_image, 3.0f, 15);
}

Image box_blur(const Image& input_image, int kernel_size) {
    if (kernel_size % 2 == 0) {
        kernel_size++;  // Odd kernel size
    }
    
    Image filtered_img(input_image.width, input_image.height, input_image.channels);
    int half_kernel = kernel_size / 2;
    float kernel_weight = 1.0f / (kernel_size * kernel_size);
    
    for (int c = 0; c < input_image.channels; ++c) {
        for (int y = 0; y < input_image.height; ++y) {
            for (int x = 0; x < input_image.width; ++x) {
                float sum_val = 0.0f;
                
                for (int ky = -half_kernel; ky <= half_kernel; ++ky) {
                    for (int kx = -half_kernel; kx <= half_kernel; ++kx) {
                        int px = std::max(0, std::min(x + kx, input_image.width - 1));
                        int py = std::max(0, std::min(y + ky, input_image.height - 1));
                        sum_val += const_cast<Image&>(input_image).pixel(px, py)[c];
                    }
                }
                
                filtered_img.pixel(x, y)[c] = static_cast<uint8_t>(std::round(sum_val * kernel_weight));
            }
        }
    }
    
    return filtered_img;
}
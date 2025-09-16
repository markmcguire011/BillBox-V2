#pragma once
#include "image.h"

Image median_filter(const Image& input_image, int kernel_size = 3);
Image median_filter_3x3(const Image& input_image);
Image median_filter_5x5(const Image& input_image);

Image gaussian_blur(const Image& input_image, float sigma = 1.0f, int kernel_size = 0);
Image gaussian_blur_3x3(const Image& input_image);
Image gaussian_blur_5x5(const Image& input_image);
Image gaussian_blur_strong(const Image& input_image);

Image box_blur(const Image& input_image, int kernel_size = 3);
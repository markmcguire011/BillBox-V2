#pragma once
#include "image.h"

Image threshold_otsu(const Image& input_image);
Image threshold_binary(const Image& input_image, uint8_t threshold_value);
Image threshold_binary_inverted(const Image& input_image, uint8_t threshold_value);
Image threshold_adaptive_mean(const Image& input_image, int block_size = 11, int c = 2);
Image threshold_adaptive_gaussian(const Image& input_image, int block_size = 11, int c = 2);

uint8_t calculate_otsu_threshold(const Image& input_image);
uint8_t calculate_mean_threshold(const Image& input_image);
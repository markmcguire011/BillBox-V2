#pragma once
#include "image.h"

Image normalize_contrast(const Image& input_image);
Image normalize_contrast_minmax(const Image& input_image);
Image normalize_contrast_percentile(const Image& input_image, float low_percentile = 2.0f, float high_percentile = 98.0f);
Image histogram_equalization(const Image& input_image);
Image adaptive_histogram_equalization(const Image& input_image, int tile_size = 64);
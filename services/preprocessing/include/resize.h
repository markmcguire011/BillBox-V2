#pragma once
#include "image.h"

Image resize_nearest_neighbor(const Image& input_image, int new_width, int new_height);
Image resize_bilinear(const Image& input_image, int new_width, int new_height);
Image scale_image(const Image& input_image, float scale_factor);
Image scale_image_width(const Image& input_image, int target_width);
Image scale_image_height(const Image& input_image, int target_height);
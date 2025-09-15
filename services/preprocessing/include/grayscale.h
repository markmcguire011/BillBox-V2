#pragma once
#include "image.h"

Image to_grayscale(const Image& input_image);
Image to_grayscale_luminance(const Image& input_image);
Image to_grayscale_average(const Image& input_image);
#pragma once
#include "image.h"

float estimate_skew_angle(const Image& input_image, float min_angle = -45.0f, float max_angle = 45.0f, float angle_step = 0.5f);
float estimate_skew_angle_hough(const Image& input_image, float min_angle = -45.0f, float max_angle = 45.0f);
float estimate_skew_angle_projection(const Image& input_image, float min_angle = -45.0f, float max_angle = 45.0f);

Image deskew(const Image& input_image, float angle_degrees);
Image deskew_auto(const Image& input_image);
Image deskew_manual(const Image& input_image, float angle_degrees);

Image rotate_image(const Image& input_image, float angle_degrees, uint8_t background_color = 255);
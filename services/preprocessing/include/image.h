#pragma once
#include <vector>
#include <cstdint>
#include <string>

struct Image {
    int width;
    int height;
    int channels; // 1 for grayscale, 3 for RGB, 4 for RGBA
    std::vector<uint8_t> data; // row-major order

    Image(int w, int h, int c) : width(w), height(h), channels(c), data(w*h*c) {}
    uint8_t* pixel(int x, int y) { return &data[(y * width + x) * channels]; }
    const uint8_t* pixel(int x, int y) const { return &data[(y * width + x) * channels]; }
};

Image load_image_rgb(const std::string& filename);
Image load_image_grayscale(const std::string& filename);
Image load_image_rgba(const std::string& filename);
Image load_image_channels(const std::string& filename, int desired_channels);

void save_image_png(const std::string& filename, const Image& img);
void save_image_jpg(const std::string& filename, const Image& img, int quality = 95);
void save_image_auto(const std::string& filename, const Image& img);
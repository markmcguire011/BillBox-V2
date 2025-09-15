#pragma once
#include <vector>
#include <cstdint>

struct Image {
    int width;
    int height;
    int channels; // 1 for grayscale, 3 for RGB, 4 for RGBA
    std::vector<uint8_t> data; // row-major order

    Image(int w, int h, int c) : width(w), height(h), channels(c), data(w*h*c) {}
    uint8_t* pixel(int x, int y) { return &data[(y * width + x) * channels]; }
};
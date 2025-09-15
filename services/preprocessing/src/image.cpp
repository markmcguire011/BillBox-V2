#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION

#include "image.h"
#include "stb_image.h"
#include "stb_image_write.h"
#include <iostream>
#include <stdexcept>

Image load_image_rgb(const std::string& filename) {
    return load_image_channels(filename, 3);
}

Image load_image_grayscale(const std::string& filename) {
    return load_image_channels(filename, 1);
}

Image load_image_rgba(const std::string& filename) {
    return load_image_channels(filename, 4);
}

Image load_image_channels(const std::string& filename, int desired_channels) {
    int w, h, c;
    unsigned char* img_data = stbi_load(filename.c_str(), &w, &h, &c, desired_channels);
    if (!img_data) {
        throw std::runtime_error("Failed to load image: " + filename);
    }

    Image img(w, h, desired_channels);
    std::copy(img_data, img_data + (w*h*desired_channels), img.data.begin());
    stbi_image_free(img_data);
    return img;
}

void save_image_png(const std::string& filename, const Image& img) {
    int success = stbi_write_png(filename.c_str(), img.width, img.height, img.channels, img.data.data(), img.width * img.channels);
    if (!success) {
        throw std::runtime_error("Failed to save PNG image: " + filename);
    }
}

void save_image_jpg(const std::string& filename, const Image& img, int quality) {
    int success = stbi_write_jpg(filename.c_str(), img.width, img.height, img.channels, img.data.data(), quality);
    if (!success) {
        throw std::runtime_error("Failed to save JPG image: " + filename);
    }
}

void save_image_auto(const std::string& filename, const Image& img) {
    std::string extension = filename.substr(filename.find_last_of(".") + 1);
    
    if (extension == "png") {
        save_image_png(filename, img);
    } else if (extension == "jpg" || extension == "jpeg") {
        save_image_jpg(filename, img, 95);
    } else {
        throw std::runtime_error("Unsupported file format for saving: " + filename);
    }
}
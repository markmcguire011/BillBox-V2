#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION

#include "image.h"
#include "stb_image.h"
#include "stb_image_write.h"
#include <iostream>

Image load_image(const std::string& filename, int desired_channels) {
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

void save_image(const std::string& filename, const Image& img) {
    int success = 0;
    if (filename.substr(filename.find_last_of(".") + 1) == "png") {
        success = stbi_write_png(filename.c_str(), img.width, img.height, img.channels, img.data.data(), img.width * img.channels);
    } else if (filename.substr(filename.find_last_of(".") + 1) == "jpg" || 
    filename.substr(filename.find_last_of(".") + 1) == "jpeg") {
        success = stbi_write_jpg(filename.c_str(), img.width, img.height, img.channels, img.data.data(), 95); // 95% quality
    } else {
        throw std::runtime_error("Unsupported file format for saving: " + filename);
    }
    
    if (!success) {
        throw std::runtime_error("Failed to save image: " + filename);
    }
}
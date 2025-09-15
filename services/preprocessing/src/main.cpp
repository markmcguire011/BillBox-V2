#include "image.h"
#include <iostream>

int main() {
    try {
        // Load image
        Image img = load_image("/Users/markmcguire/Downloads/test.png", 3); // Force RGB
        std::cout << "Loaded image: " << img.width << "x" << img.height << " channels=" << img.channels << "\n";

        // Access a pixel (top-left)
        uint8_t* p = img.pixel(0,240);
        std::cout << "Selected pixel RGB: " 
                  << (int)p[0] << ", " << (int)p[1] << ", " << (int)p[2] << "\n";

        // Save a copy
        save_image("invoice_copy.png", img);

    } catch (const std::exception& e) {
        std::cerr << e.what() << "\n";
    }
    return 0;
}
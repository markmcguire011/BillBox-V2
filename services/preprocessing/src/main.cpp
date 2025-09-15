#include "image.h"
#include "grayscale.h"
#include <iostream>
#include <filesystem>

int main() {
    try {
        // Create output directory
        std::filesystem::create_directories("output");
        std::cout << "Created output directory\n";

        // Load image
        Image img = load_image("/Users/markmcguire/Documents/Projects/BillBox-V2/services/preprocessing/examples/Invoice Example 2.png", 3); // Force RGB
        std::cout << "Loaded image: " << img.width << "x" << img.height << " channels=" << img.channels << "\n";

        // Access a pixel (top-left)
        uint8_t* p = img.pixel(0,240);
        std::cout << "Selected pixel RGB: " 
                  << (int)p[0] << ", " << (int)p[1] << ", " << (int)p[2] << "\n";

        // Save original copy
        save_image("output/original.png", img);
        std::cout << "Saved original image as 'output/original.png'\n";

        // Test grayscale conversions
        std::cout << "\nTesting grayscale conversions...\n";

        // Luminance method (default)
        Image gray_luminance = to_grayscale_luminance(img);
        save_image("output/grayscale_luminance.png", gray_luminance);
        std::cout << "Saved luminance grayscale as 'output/grayscale_luminance.png'\n";

        // Average method
        Image gray_average = to_grayscale_average(img);
        save_image("output/grayscale_average.png", gray_average);
        std::cout << "Saved average grayscale as 'output/grayscale_average.png'\n";

        // Default method (should be same as luminance)
        Image gray_default = to_grayscale(img);
        save_image("output/grayscale_default.png", gray_default);
        std::cout << "Saved default grayscale as 'output/grayscale_default.png'\n";

        std::cout << "\nGrayscale conversion complete! Check the output files in the 'output' folder.\n";

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }
    return 0;
}
#include "image.h"
#include "grayscale.h"
#include "resize.h"
#include <iostream>
#include <filesystem>

int main() {
    try {
        // Create output directory
        std::filesystem::create_directories("output");
        std::cout << "Created output directory\n";

        // Load image
        Image img = load_image_rgb("/Users/markmcguire/Documents/Projects/BillBox-V2/services/preprocessing/examples/Invoice Example 2.png");
        std::cout << "Loaded image: " << img.width << "x" << img.height << " channels=" << img.channels << "\n";

        // Access a pixel (top-left)
        uint8_t* p = img.pixel(0,240);
        std::cout << "Selected pixel RGB: " 
                  << (int)p[0] << ", " << (int)p[1] << ", " << (int)p[2] << "\n";

        // Save original copy
        save_image_auto("output/original.png", img);
        std::cout << "Saved original image as 'output/original.png'\n";

        // Test grayscale conversions
        std::cout << "\nTesting grayscale conversions...\n";

        // Luminance method (default)
        Image gray_luminance = to_grayscale_luminance(img);
        save_image_auto("output/grayscale_luminance.png", gray_luminance);
        std::cout << "Saved luminance grayscale as 'output/grayscale_luminance.png'\n";

        // Average method
        Image gray_average = to_grayscale_average(img);
        save_image_auto("output/grayscale_average.png", gray_average);
        std::cout << "Saved average grayscale as 'output/grayscale_average.png'\n";

        // Default method (should be same as luminance)
        Image gray_default = to_grayscale(img);
        save_image_auto("output/grayscale_default.png", gray_default);
        std::cout << "Saved default grayscale as 'output/grayscale_default.png'\n";

        std::cout << "\nGrayscale conversion complete!\n";

        // Test resize and scaling operations
        std::cout << "\nTesting resize and scaling operations...\n";

        // Resize using nearest neighbor
        Image resized_nn = resize_nearest_neighbor(img, img.width / 2, img.height / 2);
        save_image_auto("output/resized_nearest_neighbor.png", resized_nn);
        std::cout << "Saved nearest neighbor resize as 'output/resized_nearest_neighbor.png' (" 
                  << resized_nn.width << "x" << resized_nn.height << ")\n";

        // Resize using bilinear interpolation
        Image resized_bilinear = resize_bilinear(img, img.width / 3, img.height / 3);
        save_image_auto("output/resized_bilinear.png", resized_bilinear);
        std::cout << "Saved bilinear resize as 'output/resized_bilinear.png' (" 
                  << resized_bilinear.width << "x" << resized_bilinear.height << ")\n";

        // Scale by factor
        Image scaled_half = scale_image(img, 0.5f);
        save_image_auto("output/scaled_half.png", scaled_half);
        std::cout << "Saved 50% scaled image as 'output/scaled_half.png' (" 
                  << scaled_half.width << "x" << scaled_half.height << ")\n";

        Image scaled_double = scale_image(img, 2.0f);
        save_image_auto("output/scaled_double.png", scaled_double);
        std::cout << "Saved 200% scaled image as 'output/scaled_double.png' (" 
                  << scaled_double.width << "x" << scaled_double.height << ")\n";

        // Scale to specific width
        Image scaled_width = scale_image_width(img, 800);
        save_image_auto("output/scaled_width_800.png", scaled_width);
        std::cout << "Saved width-scaled image as 'output/scaled_width_800.png' (" 
                  << scaled_width.width << "x" << scaled_width.height << ")\n";

        // Scale to specific height
        Image scaled_height = scale_image_height(img, 600);
        save_image_auto("output/scaled_height_600.png", scaled_height);
        std::cout << "Saved height-scaled image as 'output/scaled_height_600.png' (" 
                  << scaled_height.width << "x" << scaled_height.height << ")\n";

        // Combine grayscale and resize operations
        Image gray_small = resize_bilinear(gray_luminance, gray_luminance.width / 4, gray_luminance.height / 4);
        save_image_auto("output/grayscale_small.png", gray_small);
        std::cout << "Saved small grayscale image as 'output/grayscale_small.png' (" 
                  << gray_small.width << "x" << gray_small.height << ")\n";

        std::cout << "\nAll image processing operations complete! Check the output files in the 'output' folder.\n";

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }
    return 0;
}
#include "image.h"
#include "grayscale.h"
#include "resize.h"
#include "contrast.h"
#include "filter.h"
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

        std::cout << "\nResize operations complete!\n";

        // Test contrast normalization operations
        std::cout << "\nTesting contrast normalization operations...\n";

        // Min-max normalization
        Image contrast_minmax = normalize_contrast_minmax(img);
        save_image_auto("output/contrast_minmax.png", contrast_minmax);
        std::cout << "Saved min-max normalized image as 'output/contrast_minmax.png'\n";

        // Percentile normalization
        Image contrast_percentile = normalize_contrast_percentile(img, 5.0f, 95.0f);
        save_image_auto("output/contrast_percentile.png", contrast_percentile);
        std::cout << "Saved percentile normalized image as 'output/contrast_percentile.png'\n";

        // Default normalization (should be same as min-max)
        Image contrast_default = normalize_contrast(img);
        save_image_auto("output/contrast_default.png", contrast_default);
        std::cout << "Saved default normalized image as 'output/contrast_default.png'\n";

        // Histogram equalization
        Image hist_equalized = histogram_equalization(img);
        save_image_auto("output/histogram_equalized.png", hist_equalized);
        std::cout << "Saved histogram equalized image as 'output/histogram_equalized.png'\n";

        // Adaptive histogram equalization
        Image adaptive_equalized = adaptive_histogram_equalization(img, 32);
        save_image_auto("output/adaptive_histogram_equalized.png", adaptive_equalized);
        std::cout << "Saved adaptive histogram equalized image as 'output/adaptive_histogram_equalized.png'\n";

        // Combine operations: grayscale + contrast normalization
        Image gray_contrast = normalize_contrast(gray_luminance);
        save_image_auto("output/grayscale_contrast_normalized.png", gray_contrast);
        std::cout << "Saved grayscale contrast normalized image as 'output/grayscale_contrast_normalized.png'\n";

        // Combine operations: resize + histogram equalization
        Image small_equalized = histogram_equalization(scaled_half);
        save_image_auto("output/small_histogram_equalized.png", small_equalized);
        std::cout << "Saved small histogram equalized image as 'output/small_histogram_equalized.png'\n";

        std::cout << "\nContrast operations complete!\n";

        // Test filtering operations
        std::cout << "\nTesting filtering operations...\n";

        // Median filters
        Image median_3x3 = median_filter_3x3(img);
        save_image_auto("output/median_filter_3x3.png", median_3x3);
        std::cout << "Saved 3x3 median filtered image as 'output/median_filter_3x3.png'\n";

        Image median_5x5 = median_filter_5x5(img);
        save_image_auto("output/median_filter_5x5.png", median_5x5);
        std::cout << "Saved 5x5 median filtered image as 'output/median_filter_5x5.png'\n";

        Image median_custom = median_filter(img, 7);
        save_image_auto("output/median_filter_7x7.png", median_custom);
        std::cout << "Saved 7x7 median filtered image as 'output/median_filter_7x7.png'\n";

        // Gaussian blur filters
        Image gaussian_3x3 = gaussian_blur_3x3(img);
        save_image_auto("output/gaussian_blur_3x3.png", gaussian_3x3);
        std::cout << "Saved 3x3 Gaussian blur image as 'output/gaussian_blur_3x3.png'\n";

        Image gaussian_5x5 = gaussian_blur_5x5(img);
        save_image_auto("output/gaussian_blur_5x5.png", gaussian_5x5);
        std::cout << "Saved 5x5 Gaussian blur image as 'output/gaussian_blur_5x5.png'\n";

        Image gaussian_strong = gaussian_blur_strong(img);
        save_image_auto("output/gaussian_blur_strong.png", gaussian_strong);
        std::cout << "Saved strong Gaussian blur image as 'output/gaussian_blur_strong.png'\n";

        Image gaussian_custom = gaussian_blur(img, 2.0f, 9);
        save_image_auto("output/gaussian_blur_custom.png", gaussian_custom);
        std::cout << "Saved custom Gaussian blur image as 'output/gaussian_blur_custom.png'\n";

        // Box blur filter
        Image box_blur_img = box_blur(img, 5);
        save_image_auto("output/box_blur_5x5.png", box_blur_img);
        std::cout << "Saved 5x5 box blur image as 'output/box_blur_5x5.png'\n";

        // Combine operations: grayscale + median filter
        Image gray_median = median_filter_3x3(gray_luminance);
        save_image_auto("output/grayscale_median_filtered.png", gray_median);
        std::cout << "Saved grayscale median filtered image as 'output/grayscale_median_filtered.png'\n";

        // Combine operations: resize + gaussian blur
        Image small_blurred = gaussian_blur_3x3(scaled_half);
        save_image_auto("output/small_gaussian_blur.png", small_blurred);
        std::cout << "Saved small Gaussian blurred image as 'output/small_gaussian_blur.png'\n";

        // Complex combination: grayscale + contrast + filter
        Image processed = median_filter_3x3(gray_contrast);
        save_image_auto("output/grayscale_contrast_filtered.png", processed);
        std::cout << "Saved grayscale contrast filtered image as 'output/grayscale_contrast_filtered.png'\n";

        std::cout << "\nAll image processing operations complete! Check the output files in the 'output' folder.\n";

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }
    return 0;
}
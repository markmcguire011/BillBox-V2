#include "image.h"
#include "grayscale.h"
#include "resize.h"
#include "contrast.h"
#include "filter.h"
#include <iostream>
#include <filesystem>
#include <string>

void display_main_menu() {
    std::cout << "\n======================================\n";
    std::cout << "  BillBox Image Preprocessing Tool\n";
    std::cout << "======================================\n";
    std::cout << "1. Grayscale Conversion\n";
    std::cout << "2. Image Resizing/Scaling\n";
    std::cout << "3. Contrast Normalization\n";
    std::cout << "4. Image Filtering\n";
    std::cout << "5. Run All Techniques (Demo)\n";
    std::cout << "0. Exit\n";
    std::cout << "======================================\n";
    std::cout << "Choose an option: ";
}

void display_grayscale_menu() {
    std::cout << "\n--- Grayscale Conversion ---\n";
    std::cout << "1. Luminance Method (Recommended)\n";
    std::cout << "2. Average Method\n";
    std::cout << "3. Default Method\n";
    std::cout << "0. Back to Main Menu\n";
    std::cout << "Choose method: ";
}

void display_resize_menu() {
    std::cout << "\n--- Image Resizing/Scaling ---\n";
    std::cout << "1. Resize with Nearest Neighbor\n";
    std::cout << "2. Resize with Bilinear Interpolation\n";
    std::cout << "3. Scale by Factor\n";
    std::cout << "4. Scale to Specific Width\n";
    std::cout << "5. Scale to Specific Height\n";
    std::cout << "0. Back to Main Menu\n";
    std::cout << "Choose method: ";
}

void display_contrast_menu() {
    std::cout << "\n--- Contrast Normalization ---\n";
    std::cout << "1. Min-Max Normalization\n";
    std::cout << "2. Percentile Normalization\n";
    std::cout << "3. Histogram Equalization\n";
    std::cout << "4. Adaptive Histogram Equalization\n";
    std::cout << "5. Default Normalization\n";
    std::cout << "0. Back to Main Menu\n";
    std::cout << "Choose method: ";
}

void display_filter_menu() {
    std::cout << "\n--- Image Filtering ---\n";
    std::cout << "1. Median Filter 3x3\n";
    std::cout << "2. Median Filter 5x5\n";
    std::cout << "3. Median Filter (Custom Size)\n";
    std::cout << "4. Gaussian Blur 3x3\n";
    std::cout << "5. Gaussian Blur 5x5\n";
    std::cout << "6. Strong Gaussian Blur\n";
    std::cout << "7. Custom Gaussian Blur\n";
    std::cout << "8. Box Blur\n";
    std::cout << "0. Back to Main Menu\n";
    std::cout << "Choose method: ";
}

void process_grayscale(const Image& img) {
    int choice;
    display_grayscale_menu();
    std::cin >> choice;
    
    Image result = img;
    std::string filename;
    
    switch (choice) {
        case 1:
            result = to_grayscale_luminance(img);
            filename = "output/grayscale_luminance.png";
            std::cout << "Applied luminance grayscale conversion.\n";
            break;
        case 2:
            result = to_grayscale_average(img);
            filename = "output/grayscale_average.png";
            std::cout << "Applied average grayscale conversion.\n";
            break;
        case 3:
            result = to_grayscale(img);
            filename = "output/grayscale_default.png";
            std::cout << "Applied default grayscale conversion.\n";
            break;
        case 0:
            return;
        default:
            std::cout << "Invalid choice. Returning to main menu.\n";
            return;
    }
    
    save_image_auto(filename, result);
    std::cout << "Saved result to: " << filename << "\n";
}

void process_resize(const Image& img) {
    int choice;
    display_resize_menu();
    std::cin >> choice;
    
    Image result = img;
    std::string filename;
    
    switch (choice) {
        case 1: {
            int width, height;
            std::cout << "Enter new width: ";
            std::cin >> width;
            std::cout << "Enter new height: ";
            std::cin >> height;
            result = resize_nearest_neighbor(img, width, height);
            filename = "output/resized_nearest_neighbor.png";
            std::cout << "Applied nearest neighbor resize to " << width << "x" << height << ".\n";
            break;
        }
        case 2: {
            int width, height;
            std::cout << "Enter new width: ";
            std::cin >> width;
            std::cout << "Enter new height: ";
            std::cin >> height;
            result = resize_bilinear(img, width, height);
            filename = "output/resized_bilinear.png";
            std::cout << "Applied bilinear resize to " << width << "x" << height << ".\n";
            break;
        }
        case 3: {
            float factor;
            std::cout << "Enter scale factor (e.g., 0.5 for 50%, 2.0 for 200%): ";
            std::cin >> factor;
            result = scale_image(img, factor);
            filename = "output/scaled_factor.png";
            std::cout << "Applied scale factor of " << factor << ".\n";
            break;
        }
        case 4: {
            int width;
            std::cout << "Enter target width: ";
            std::cin >> width;
            result = scale_image_width(img, width);
            filename = "output/scaled_width.png";
            std::cout << "Scaled to width " << width << ".\n";
            break;
        }
        case 5: {
            int height;
            std::cout << "Enter target height: ";
            std::cin >> height;
            result = scale_image_height(img, height);
            filename = "output/scaled_height.png";
            std::cout << "Scaled to height " << height << ".\n";
            break;
        }
        case 0:
            return;
        default:
            std::cout << "Invalid choice. Returning to main menu.\n";
            return;
    }
    
    save_image_auto(filename, result);
    std::cout << "Saved result to: " << filename << "\n";
}

void process_contrast(const Image& img) {
    int choice;
    display_contrast_menu();
    std::cin >> choice;
    
    Image result = img;
    std::string filename;
    
    switch (choice) {
        case 1:
            result = normalize_contrast_minmax(img);
            filename = "output/contrast_minmax.png";
            std::cout << "Applied min-max contrast normalization.\n";
            break;
        case 2: {
            float low, high;
            std::cout << "Enter low percentile (e.g., 2.0): ";
            std::cin >> low;
            std::cout << "Enter high percentile (e.g., 98.0): ";
            std::cin >> high;
            result = normalize_contrast_percentile(img, low, high);
            filename = "output/contrast_percentile.png";
            std::cout << "Applied percentile normalization (" << low << "% - " << high << "%).\n";
            break;
        }
        case 3:
            result = histogram_equalization(img);
            filename = "output/histogram_equalized.png";
            std::cout << "Applied histogram equalization.\n";
            break;
        case 4: {
            int tile_size;
            std::cout << "Enter tile size (e.g., 32, 64): ";
            std::cin >> tile_size;
            result = adaptive_histogram_equalization(img, tile_size);
            filename = "output/adaptive_histogram_equalized.png";
            std::cout << "Applied adaptive histogram equalization with tile size " << tile_size << ".\n";
            break;
        }
        case 5:
            result = normalize_contrast(img);
            filename = "output/contrast_default.png";
            std::cout << "Applied default contrast normalization.\n";
            break;
        case 0:
            return;
        default:
            std::cout << "Invalid choice. Returning to main menu.\n";
            return;
    }
    
    save_image_auto(filename, result);
    std::cout << "Saved result to: " << filename << "\n";
}

void process_filter(const Image& img) {
    int choice;
    display_filter_menu();
    std::cin >> choice;
    
    Image result = img;
    std::string filename;
    
    switch (choice) {
        case 1:
            result = median_filter_3x3(img);
            filename = "output/median_filter_3x3.png";
            std::cout << "Applied 3x3 median filter.\n";
            break;
        case 2:
            result = median_filter_5x5(img);
            filename = "output/median_filter_5x5.png";
            std::cout << "Applied 5x5 median filter.\n";
            break;
        case 3: {
            int size;
            std::cout << "Enter kernel size (odd number, e.g., 7, 9): ";
            std::cin >> size;
            result = median_filter(img, size);
            filename = "output/median_filter_custom.png";
            std::cout << "Applied " << size << "x" << size << " median filter.\n";
            break;
        }
        case 4:
            result = gaussian_blur_3x3(img);
            filename = "output/gaussian_blur_3x3.png";
            std::cout << "Applied 3x3 Gaussian blur.\n";
            break;
        case 5:
            result = gaussian_blur_5x5(img);
            filename = "output/gaussian_blur_5x5.png";
            std::cout << "Applied 5x5 Gaussian blur.\n";
            break;
        case 6:
            result = gaussian_blur_strong(img);
            filename = "output/gaussian_blur_strong.png";
            std::cout << "Applied strong Gaussian blur.\n";
            break;
        case 7: {
            float sigma;
            int kernel_size;
            std::cout << "Enter sigma value (e.g., 1.0, 2.0): ";
            std::cin >> sigma;
            std::cout << "Enter kernel size (0 for auto): ";
            std::cin >> kernel_size;
            result = gaussian_blur(img, sigma, kernel_size);
            filename = "output/gaussian_blur_custom.png";
            std::cout << "Applied custom Gaussian blur (sigma=" << sigma << ").\n";
            break;
        }
        case 8: {
            int size;
            std::cout << "Enter kernel size (odd number, e.g., 5, 7): ";
            std::cin >> size;
            result = box_blur(img, size);
            filename = "output/box_blur.png";
            std::cout << "Applied " << size << "x" << size << " box blur.\n";
            break;
        }
        case 0:
            return;
        default:
            std::cout << "Invalid choice. Returning to main menu.\n";
            return;
    }
    
    save_image_auto(filename, result);
    std::cout << "Saved result to: " << filename << "\n";
}

void run_demo(const Image& img) {
    std::cout << "\n--- Running Demo (All Techniques) ---\n";
    std::cout << "This will apply various techniques and save results...\n";
    
    // Create output directory
    std::filesystem::create_directories("output");
    
    // Save original
    save_image_auto("output/demo_original.png", img);
    std::cout << "Saved original image\n";
    
    // Grayscale
    Image gray = to_grayscale_luminance(img);
    save_image_auto("output/demo_grayscale.png", gray);
    std::cout << "Saved grayscale conversion\n";
    
    // Resize
    Image resized = scale_image(img, 0.5f);
    save_image_auto("output/demo_resized.png", resized);
    std::cout << "Saved resized image (50%)\n";
    
    // Contrast
    Image contrast = histogram_equalization(img);
    save_image_auto("output/demo_contrast.png", contrast);
    std::cout << "Saved contrast enhanced image\n";
    
    // Filter
    Image filtered = gaussian_blur_3x3(img);
    save_image_auto("output/demo_filtered.png", filtered);
    std::cout << "Saved filtered image\n";
    
    // Combination
    Image combo = median_filter_3x3(normalize_contrast(gray));
    save_image_auto("output/demo_combination.png", combo);
    std::cout << "Saved combination (grayscale + contrast + filter)\n";
    
    std::cout << "Demo complete! Check the 'output' folder for results.\n";
}

int main() {
    try {
        std::cout << "BillBox Image Preprocessing Tool\n";
        std::cout << "Loading image...\n";
        
        // Load image
        Image img = load_image_rgb("/Users/markmcguire/Documents/Projects/BillBox-V2/services/preprocessing/examples/Invoice Example 2.png");
        std::cout << "Loaded image: " << img.width << "x" << img.height << " channels=" << img.channels << "\n";
        
        // Create output directory
        std::filesystem::create_directories("output");
        
        int choice;
        do {
            display_main_menu();
            std::cin >> choice;
            
            switch (choice) {
                case 1:
                    process_grayscale(img);
                    break;
                case 2:
                    process_resize(img);
                    break;
                case 3:
                    process_contrast(img);
                    break;
                case 4:
                    process_filter(img);
                    break;
                case 5:
                    run_demo(img);
                    break;
                case 0:
                    std::cout << "Exiting...\n";
                    break;
                default:
                    std::cout << "Invalid choice. Please try again.\n";
                    break;
            }
        } while (choice != 0);
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
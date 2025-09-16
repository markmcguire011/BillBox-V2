#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "image.h"
#include "pipeline.h"
#include "grayscale.h"
#include "resize.h"
#include "contrast.h"
#include "filter.h"
#include "threshold.h"
#include "deskew.h"

namespace py = pybind11;

// Helper function to convert numpy array to Image
Image numpy_to_image(py::array_t<uint8_t> input) {
    py::buffer_info buf_info = input.request();
    
    if (buf_info.ndim != 3) {
        throw std::runtime_error("Input array must be 3-dimensional (height, width, channels)");
    }
    
    int height = buf_info.shape[0];
    int width = buf_info.shape[1];
    int channels = buf_info.shape[2];
    
    Image img(width, height, channels);
    
    uint8_t* input_ptr = static_cast<uint8_t*>(buf_info.ptr);
    
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            for (int c = 0; c < channels; ++c) {
                img.pixel(x, y)[c] = input_ptr[y * width * channels + x * channels + c];
            }
        }
    }
    
    return img;
}

// Helper function to convert Image to numpy array
py::array_t<uint8_t> image_to_numpy(const Image& img) {
    auto result = py::array_t<uint8_t>(
        {img.height, img.width, img.channels},
        {sizeof(uint8_t) * img.width * img.channels, sizeof(uint8_t) * img.channels, sizeof(uint8_t)}
    );
    
    py::buffer_info buf_info = result.request();
    uint8_t* output_ptr = static_cast<uint8_t*>(buf_info.ptr);
    
    for (int y = 0; y < img.height; ++y) {
        for (int x = 0; x < img.width; ++x) {
            for (int c = 0; c < img.channels; ++c) {
                output_ptr[y * img.width * img.channels + x * img.channels + c] = 
                    const_cast<Image&>(img).pixel(x, y)[c];
            }
        }
    }
    
    return result;
}

PYBIND11_MODULE(billbox_preprocessing, m) {
    m.doc() = "BillBox Image Preprocessing - C++ image processing pipeline for OCR preparation";
    
    // Image class
    py::class_<Image>(m, "Image")
        .def(py::init<int, int, int>(), "Create empty image", 
             py::arg("width"), py::arg("height"), py::arg("channels"))
        .def_readwrite("width", &Image::width)
        .def_readwrite("height", &Image::height)
        .def_readwrite("channels", &Image::channels)
        .def("to_numpy", &image_to_numpy, "Convert Image to numpy array")
        .def_static("from_numpy", &numpy_to_image, "Create Image from numpy array", py::arg("array"));
    
    // PipelineConfig class
    py::class_<PipelineConfig>(m, "PipelineConfig")
        .def(py::init<>())
        .def_readwrite("enable_deskewing", &PipelineConfig::enable_deskewing)
        .def_readwrite("max_skew_angle", &PipelineConfig::max_skew_angle)
        .def_readwrite("enable_noise_reduction", &PipelineConfig::enable_noise_reduction)
        .def_readwrite("median_filter_size", &PipelineConfig::median_filter_size)
        .def_readwrite("enable_contrast_enhancement", &PipelineConfig::enable_contrast_enhancement)
        .def_readwrite("use_histogram_equalization", &PipelineConfig::use_histogram_equalization)
        .def_readwrite("percentile_low", &PipelineConfig::percentile_low)
        .def_readwrite("percentile_high", &PipelineConfig::percentile_high)
        .def_readwrite("enable_resizing", &PipelineConfig::enable_resizing)
        .def_readwrite("target_width", &PipelineConfig::target_width)
        .def_readwrite("target_height", &PipelineConfig::target_height)
        .def_readwrite("scale_factor", &PipelineConfig::scale_factor)
        .def_readwrite("enable_thresholding", &PipelineConfig::enable_thresholding)
        .def_readwrite("use_adaptive_threshold", &PipelineConfig::use_adaptive_threshold)
        .def_readwrite("adaptive_block_size", &PipelineConfig::adaptive_block_size)
        .def_readwrite("adaptive_c", &PipelineConfig::adaptive_c)
        .def_readwrite("save_intermediate_steps", &PipelineConfig::save_intermediate_steps)
        .def_readwrite("output_prefix", &PipelineConfig::output_prefix);
    
    // PipelineResult class
    py::class_<PipelineResult>(m, "PipelineResult")
        .def(py::init<>())
        .def_readwrite("final_image", &PipelineResult::final_image)
        .def_readwrite("intermediate_steps", &PipelineResult::intermediate_steps)
        .def_readwrite("step_names", &PipelineResult::step_names)
        .def_readwrite("detected_skew_angle", &PipelineResult::detected_skew_angle)
        .def_readwrite("otsu_threshold", &PipelineResult::otsu_threshold)
        .def_readwrite("success", &PipelineResult::success)
        .def_readwrite("error_message", &PipelineResult::error_message)
        .def("get_final_numpy", [](const PipelineResult& result) { 
            return image_to_numpy(result.final_image); 
        }, "Get final processed image as numpy array")
        .def("get_intermediate_numpy", [](const PipelineResult& result, int step_index) {
            if (step_index < 0 || step_index >= static_cast<int>(result.intermediate_steps.size())) {
                throw std::out_of_range("Step index out of range");
            }
            return image_to_numpy(result.intermediate_steps[step_index]);
        }, "Get intermediate step as numpy array", py::arg("step_index"));
    
    // Pipeline functions
    m.def("process_for_ocr", [](py::array_t<uint8_t> input_array, const PipelineConfig& config) {
        Image img = numpy_to_image(input_array);
        return process_for_ocr(img, config);
    }, "Main OCR preprocessing pipeline", py::arg("image"), py::arg("config") = PipelineConfig{});
    
    m.def("process_invoice_pipeline", [](py::array_t<uint8_t> input_array) {
        Image img = numpy_to_image(input_array);
        return process_invoice_pipeline(img);
    }, "Invoice-optimized preprocessing pipeline", py::arg("image"));
    
    m.def("process_document_pipeline", [](py::array_t<uint8_t> input_array) {
        Image img = numpy_to_image(input_array);
        return process_document_pipeline(img);
    }, "Document-optimized preprocessing pipeline", py::arg("image"));
    
    m.def("process_custom_pipeline", [](py::array_t<uint8_t> input_array, const PipelineConfig& config) {
        Image img = numpy_to_image(input_array);
        return process_custom_pipeline(img, config);
    }, "Custom preprocessing pipeline", py::arg("image"), py::arg("config"));
    
    // Utility functions
    m.def("create_invoice_config", &create_invoice_config, "Create optimized config for invoice processing");
    m.def("create_document_config", &create_document_config, "Create optimized config for document processing");
    
    // File I/O functions
    m.def("load_image_from_file", [](const std::string& filepath) {
        Image img = load_image_rgb(filepath);
        return image_to_numpy(img);
    }, "Load image from file as numpy array", py::arg("filepath"));
    
    m.def("save_image_to_file", [](const std::string& filepath, py::array_t<uint8_t> input_array) {
        Image img = numpy_to_image(input_array);
        save_image_auto(filepath, img);
    }, "Save numpy array as image file", py::arg("filepath"), py::arg("image"));
    
    // Individual processing functions for flexibility
    m.def("to_grayscale_luminance", [](py::array_t<uint8_t> input_array) {
        Image img = numpy_to_image(input_array);
        Image result = to_grayscale_luminance(img);
        return image_to_numpy(result);
    }, "Convert to grayscale using luminance method", py::arg("image"));
    
    m.def("threshold_otsu", [](py::array_t<uint8_t> input_array) {
        Image img = numpy_to_image(input_array);
        Image result = threshold_otsu(img);
        return image_to_numpy(result);
    }, "Apply Otsu's thresholding", py::arg("image"));
    
    m.def("estimate_skew_angle_projection", [](py::array_t<uint8_t> input_array, float min_angle = -45.0f, float max_angle = 45.0f) {
        Image img = numpy_to_image(input_array);
        return estimate_skew_angle_projection(img, min_angle, max_angle);
    }, "Estimate skew angle using projection profile", py::arg("image"), py::arg("min_angle") = -45.0f, py::arg("max_angle") = 45.0f);
    
    m.def("deskew", [](py::array_t<uint8_t> input_array, float angle_degrees) {
        Image img = numpy_to_image(input_array);
        Image result = deskew(img, angle_degrees);
        return image_to_numpy(result);
    }, "Deskew image by specified angle", py::arg("image"), py::arg("angle_degrees"));
    
    // Module version info
    m.attr("__version__") = "1.0.0";
}
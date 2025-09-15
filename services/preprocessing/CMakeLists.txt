# CMakeLists.txt for BillBox Image Preprocessing Service
# Minimum CMake version required
cmake_minimum_required(VERSION 3.16)

# Project configuration
project(billbox_preprocessing 
    VERSION 1.0.0
    DESCRIPTION "Image preprocessing service for BillBox invoice processing"
    LANGUAGES CXX
)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set build type if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

# =============================================================================
# DIRECTORIES AND INCLUDES
# =============================================================================

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include        # Project headers
    ${CMAKE_CURRENT_SOURCE_DIR}/external       # External single-header libraries
)

# =============================================================================
# SOURCE FILES
# =============================================================================

# Main executable sources
set(MAIN_SOURCES
    src/main.cpp
    src/image.cpp
    src/grayscale.cpp
    # TODO: Add future source files here, for example:
    # src/filters.cpp          # Image filtering operations
    # src/preprocessing.cpp    # Core preprocessing pipeline
    # src/ocr_prep.cpp        # OCR preparation functions
    # src/deskew.cpp          # Document deskewing
    # src/noise_reduction.cpp # Noise reduction algorithms
)

# Header files (for IDE support and organization)
set(HEADERS
    include/image.h
    include/grayscale.h
    # TODO: Add future header files here, for example:
    # include/filters.h
    # include/preprocessing.h
    # include/ocr_prep.h
    # include/deskew.h
    # include/noise_reduction.h
)

# External libraries (single-header libraries)
set(EXTERNAL_HEADERS
    external/stb_image.h
    external/stb_image_write.h
)

# =============================================================================
# EXECUTABLE TARGETS
# =============================================================================

# Main preprocessing executable
add_executable(${PROJECT_NAME} ${MAIN_SOURCES} ${HEADERS})

# =============================================================================
# COMPILER DEFINITIONS
# =============================================================================

# Required for STB libraries
target_compile_definitions(${PROJECT_NAME} PRIVATE
    STB_IMAGE_IMPLEMENTATION
    STB_IMAGE_WRITE_IMPLEMENTATION
)

# =============================================================================
# INSTALLATION
# =============================================================================

# TODO: Configure installation targets
# install(TARGETS ${PROJECT_NAME}
#     RUNTIME DESTINATION bin
# )
# 
# install(FILES ${HEADERS}
#     DESTINATION include/billbox
# )

# print build info
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Project version: ${PROJECT_VERSION}")
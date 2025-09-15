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
    # TODO: Add future external libraries here, for example:
    # external/json.hpp        # JSON processing
    # external/base64.hpp      # Base64 encoding/decoding
)

# =============================================================================
# EXECUTABLE TARGETS
# =============================================================================

# Main preprocessing executable
add_executable(${PROJECT_NAME} ${MAIN_SOURCES} ${HEADERS})

# TODO: Add additional executables here, for example:
# add_executable(preprocessing_test src/test_main.cpp ${MAIN_SOURCES})
# add_executable(batch_processor src/batch_main.cpp ${MAIN_SOURCES})

# =============================================================================
# OPTIONAL: LIBRARY TARGET
# =============================================================================
# If you want to create a library for other services to use:
# add_library(preprocessing_lib STATIC
#     src/image.cpp
#     # Add other implementation files here
# )
# target_include_directories(preprocessing_lib PUBLIC include)

# =============================================================================
# COMPILER DEFINITIONS
# =============================================================================

# Required for STB libraries
target_compile_definitions(${PROJECT_NAME} PRIVATE
    STB_IMAGE_IMPLEMENTATION
    STB_IMAGE_WRITE_IMPLEMENTATION
)

# TODO: Add conditional compilation flags, for example:
# if(ENABLE_DEBUG_LOGGING)
#     target_compile_definitions(${PROJECT_NAME} PRIVATE DEBUG_LOGGING)
# endif()

# =============================================================================
# EXTERNAL DEPENDENCIES
# =============================================================================

# TODO: Add external library dependencies here using find_package, for example:

# OpenCV for advanced image processing
# find_package(OpenCV QUIET)
# if(OpenCV_FOUND)
#     target_link_libraries(${PROJECT_NAME} ${OpenCV_LIBS})
#     target_compile_definitions(${PROJECT_NAME} PRIVATE USE_OPENCV)
# endif()

# Tesseract OCR
# find_package(PkgConfig QUIET)
# if(PkgConfig_FOUND)
#     pkg_check_modules(TESSERACT tesseract)
#     if(TESSERACT_FOUND)
#         target_link_libraries(${PROJECT_NAME} ${TESSERACT_LIBRARIES})
#         target_include_directories(${PROJECT_NAME} PRIVATE ${TESSERACT_INCLUDE_DIRS})
#         target_compile_definitions(${PROJECT_NAME} PRIVATE USE_TESSERACT)
#     endif()
# endif()

# Threading support (if needed for parallel processing)
# find_package(Threads REQUIRED)
# target_link_libraries(${PROJECT_NAME} Threads::Threads)

# =============================================================================
# TESTING
# =============================================================================

# TODO: Enable testing and add test targets
# enable_testing()
# 
# find_package(GTest QUIET)
# if(GTest_FOUND)
#     add_executable(unit_tests
#         tests/test_image.cpp
#         tests/test_preprocessing.cpp
#         ${MAIN_SOURCES}
#     )
#     target_link_libraries(unit_tests GTest::GTest GTest::Main)
#     add_test(NAME UnitTests COMMAND unit_tests)
# endif()

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

# =============================================================================
# PACKAGING
# =============================================================================

# TODO: Configure CPack for creating distribution packages
# set(CPACK_PACKAGE_NAME "BillBox-Preprocessing")
# set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
# set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Image preprocessing service for BillBox")
# include(CPack)

# =============================================================================
# CUSTOM TARGETS
# =============================================================================

# TODO: Add custom build targets, for example:

# Format code using clang-format
# add_custom_target(format
#     COMMAND clang-format -i ${MAIN_SOURCES} ${HEADERS}
#     WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
#     COMMENT "Formatting source code"
# )

# Static analysis with clang-tidy
# add_custom_target(lint
#     COMMAND clang-tidy ${MAIN_SOURCES} -- -I${CMAKE_CURRENT_SOURCE_DIR}/include
#     WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
#     COMMENT "Running static analysis"
# )

# Print build information
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Project version: ${PROJECT_VERSION}")
cmake_minimum_required(VERSION 3.28)
project(smals VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR
   NOT CMAKE_CXX_COMPILER_VERSION VERSION_GREATER_EQUAL 21 OR
   CMAKE_CXX_COMPILER_VERSION VERSION_GREATER_EQUAL 22)
  message(FATAL_ERROR "The build requires clang major version 21")
endif()

add_library(smil_core STATIC src/support/version.cpp src/support/diagnostic.cpp)
target_include_directories(smil_core PUBLIC src)
target_compile_features(smil_core PUBLIC cxx_std_23)
set_target_properties(smil_core PROPERTIES CXX_EXTENSIONS OFF)

add_executable(smil_tests test/main.cpp test/cases/diagnostics.cpp test/support/runner.cpp)
add_executable(smil src/main.cpp)
target_link_libraries(smil PRIVATE smil_core)
target_link_libraries(smil_tests PRIVATE smil_core)

include(CTest)
if(BUILD_TESTING)
  add_test(NAME version_check COMMAND smil_tests)
  add_test(NAME controlled_failure COMMAND smil_tests --fail)
  set_tests_properties(controlled_failure PROPERTIES WILL_FAIL TRUE)
endif()

find_program(SMIL_CLANG_FORMAT NAMES clang-format-21 clang-format REQUIRED)
find_program(SMIL_CLANG_TIDY NAMES clang-tidy-21 clang-tidy REQUIRED)
file(GLOB_RECURSE format_files CONFIGURE_DEPENDS "src/*.cpp" "src/*.hpp" "test/*.cpp" "test/*.hpp")
file(GLOB_RECURSE lint_files CONFIGURE_DEPENDS "src/*.cpp" "test/*.cpp")
foreach(mode format-check format-fix lint)
  if(mode STREQUAL "lint")
    set(tool "${SMIL_CLANG_TIDY}")
    set(inputs "${lint_files}")
  else()
    set(tool "${SMIL_CLANG_FORMAT}")
    set(inputs "${format_files}")
  endif()
  add_custom_target(${mode}
    COMMAND "${CMAKE_COMMAND}" "-DFILES=${inputs}" "-DTOOL=${tool}"
      "-DMODE=${mode}" "-DBUILD_DIR=${CMAKE_BINARY_DIR}"
      -P "${CMAKE_SOURCE_DIR}/tools/cmake/cpp_quality.cmake"
    VERBATIM)
endforeach()
add_custom_target(quality ALL DEPENDS format-check lint)

find_program(SMIL_UV NAMES uv REQUIRED)
add_custom_target(python-check
  COMMAND "${SMIL_UV}" run --locked python tools/check_python.py
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
add_custom_target(python-format
  COMMAND "${SMIL_UV}" run --locked python tools/check_python.py --fix
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
add_dependencies(quality python-check)

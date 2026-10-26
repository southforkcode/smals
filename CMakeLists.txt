cmake_minimum_required(VERSION 3.28)
project(smals VERSION 0.1.0 LANGUAGES CXX)

if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR
   NOT CMAKE_CXX_COMPILER_VERSION VERSION_GREATER_EQUAL 21 OR
   CMAKE_CXX_COMPILER_VERSION VERSION_GREATER_EQUAL 22)
  message(FATAL_ERROR "The build requires clang major version 21")
endif()

add_library(smil_core STATIC src/support/version.cpp)
target_include_directories(smil_core PUBLIC src)
target_compile_features(smil_core PUBLIC cxx_std_23)
set_target_properties(smil_core PROPERTIES CXX_EXTENSIONS OFF)

add_executable(smil_tests test/main.cpp)
target_link_libraries(smil_tests PRIVATE smil_core)

include(CTest)
if(BUILD_TESTING)
  add_test(NAME version_check COMMAND smil_tests)
  add_test(NAME controlled_failure COMMAND smil_tests --fail)
  set_tests_properties(controlled_failure PROPERTIES WILL_FAIL TRUE)
endif()

#include "support/runner.hpp"

#include <iostream>
#include <string_view>
#include <vector>

int main(int argc, char **argv) {
  std::clog << "debug: entering test main\n";
  if (argc == 2 && std::string_view{argv[1]} == "--fail") {
    std::cerr << "controlled failure\n";
    return 1;
  }
  const std::vector<std::string_view> args(argv + 1, argv + argc);
  return run_cases(args);
}

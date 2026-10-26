#include "support/version.hpp"

#include <iostream>
#include <string_view>

bool diagnostic_cases();

int main(int argc, char **argv) {
  if (argc == 2 && std::string_view{argv[1]} == "--fail") {
    std::cerr << "controlled failure\n";
    return 1;
  }
  if (smil::tool_version != "0.1.0") {
    std::cerr << "unexpected tool version\n";
    return 1;
  }
  if (!diagnostic_cases()) {
    std::cerr << "diagnostic cases failed\n";
    return 1;
  }
  std::cout << "tool version: " << smil::tool_version << '\n';
  return 0;
}

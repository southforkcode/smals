#include "support/diagnostic.hpp"
#include "support/version.hpp"

#include <iostream>
#include <string_view>
#include <vector>

int main(int argc, char **argv) {
  std::clog << "debug: entering main\n";
  std::vector<std::string_view> args(argv + 1, argv + argc);
  auto command = smil::parse_command(args, std::cerr);
  if (!command) {
    return 1;
  }
  std::cout << "smil " << smil::tool_version << '\n';
  return 0;
}

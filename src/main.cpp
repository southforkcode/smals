#include "support/diagnostic.hpp"
#include "support/logging.hpp"
#include "support/version.hpp"

#include <iostream>
#include <string_view>
#include <vector>

int main(int argc, char **argv) {
  smil::log_entry("main", std::clog);
  std::vector<std::string_view> args(argv + 1, argv + argc);
  auto command = smil::parse_command(args, std::cerr);
  if (!command) {
    return 1;
  }
  if (*command != smil::Command::version) {
    smil::report_unavailable(*command, args[1], std::cerr);
    return 2;
  }
  std::cout << "smil " << smil::tool_version << '\n';
  return 0;
}

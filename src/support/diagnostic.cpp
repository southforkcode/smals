#include "support/diagnostic.hpp"

#include <array>
#include <iostream>
#include <utility>

namespace smil {
std::string_view phase_name(Phase phase) {
  std::clog << "debug: entering phase_name\n";
  static constexpr std::array<std::string_view, 6> names{
      "command-line", "parsing", "verification",
      "binding",      "linking", "execution"};
  const auto index = static_cast<std::size_t>(phase);
  return index < names.size() ? names[index] : "unknown";
}

Result<Command> parse_command(std::span<const std::string_view> args,
                              std::ostream &log) {
  log << "debug: entering parse_command\n";
  if (args.size() == 1 && args[0] == "--version") {
    return Command::version;
  }
  Diagnostic error{
      Phase::command_line,
      "CLI001",
      {"<command-line>", 0, args.empty() ? 0 : args[0].size(), 1, 1},
      "expected exactly --version"};
  const auto phase = phase_name(error.phase);
  log << "error[" << error.code << "] " << phase << ' ' << error.span.source
      << ':' << error.span.line << ':' << error.span.column << " ["
      << error.span.byte_begin << ',' << error.span.byte_end
      << "): " << error.reason << '\n';
  return std::unexpected(std::move(error));
}
} // namespace smil

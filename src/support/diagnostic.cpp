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

namespace {
struct Stage {
  std::string_view name;
  Command command;
  Phase phase;
};
constexpr std::array<Stage, 5> stages{
    {{"parse", Command::parse, Phase::parsing},
     {"verify", Command::verify, Phase::verification},
     {"bind", Command::bind, Phase::binding},
     {"link", Command::link, Phase::linking},
     {"run", Command::run, Phase::execution}}};
Diagnostic emit(Diagnostic error, std::ostream &log) {
  const auto phase = phase_name(error.phase);
  log << "error[" << error.code << "] " << phase << ' ' << error.span.source
      << ':' << error.span.line << ':' << error.span.column << " ["
      << error.span.byte_begin << ',' << error.span.byte_end
      << "): " << error.reason << '\n';
  return error;
}
} // namespace

Result<Command> parse_command(std::span<const std::string_view> args,
                              std::ostream &log) {
  log << "debug: entering parse_command\n";
  if (args.size() == 1 && args[0] == "--version") {
    return Command::version;
  }
  if (args.size() == 2 && !args[1].empty()) {
    for (const auto &stage : stages) {
      if (args[0] == stage.name) {
        return stage.command;
      }
    }
  }
  return std::unexpected(
      emit({Phase::command_line,
            "CLI001",
            {"<command-line>", 0, args.empty() ? 0 : args[0].size(), 1, 1},
            "expected --version or <parse|verify|bind|link|run> <input>"},
           log));
}

Result<void> report_unavailable(Command command, std::string_view input,
                                std::ostream &log) {
  log << "debug: entering report_unavailable\n";
  for (const auto &stage : stages) {
    if (stage.command == command) {
      return std::unexpected(
          emit({stage.phase,
                "CAP001",
                {std::string(input), 0, input.size(), 1, 1},
                std::string(stage.name) + " stage is unavailable"},
               log));
    }
  }
  return std::unexpected(emit({Phase::command_line,
                               "CLI002",
                               {"<command-line>", 0, 0, 1, 1},
                               "command has no unavailable stage"},
                              log));
}
} // namespace smil

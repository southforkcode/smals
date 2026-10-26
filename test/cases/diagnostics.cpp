#include "support/diagnostic.hpp"

#include <array>
#include <sstream>

bool diagnostic_cases() {
  const std::array<std::string_view, 1> good{"--version"};
  std::ostringstream log;
  auto accepted = smil::parse_command(good, log);
  if (!accepted || *accepted != smil::Command::version ||
      log.str().find("error[") != std::string::npos) {
    return false;
  }
  const std::array<std::string_view, 1> bad{"invalid"};
  log.str("");
  auto rejected = smil::parse_command(bad, log);
  if (rejected) {
    return false;
  }
  const auto &error = rejected.error();
  if (error.phase != smil::Phase::command_line || error.code != "CLI001" ||
      error.span.source != "<command-line>" || error.span.byte_begin != 0 ||
      error.span.byte_end != 7 || error.span.line != 1 ||
      error.span.column != 1 ||
      error.reason !=
          "expected --version or <parse|verify|bind|link|run> <input>") {
    return false;
  }
  const auto first = log.str().find("error[CLI001]");
  if (first == std::string::npos ||
      log.str().find("error[CLI001]", first + 1) != std::string::npos) {
    return false;
  }
  auto empty = smil::parse_command({}, log);
  if (empty || empty.error().span.byte_end != 0) {
    return false;
  }
  auto no_stage = smil::report_unavailable(smil::Command::version, "", log);
  if (no_stage || no_stage.error().code != "CLI002") {
    return false;
  }
  const std::array<std::string_view, 6> names{"command-line", "parsing",
                                              "verification", "binding",
                                              "linking",      "execution"};
  for (std::size_t index = 0; index < names.size(); ++index) {
    if (smil::phase_name(static_cast<smil::Phase>(index)) != names[index]) {
      return false;
    }
  }
  return smil::phase_name(smil::Phase::unknown) == "unknown";
}

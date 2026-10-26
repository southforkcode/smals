#pragma once

#include <cstddef>
#include <expected>
#include <ostream>
#include <span>
#include <string>
#include <string_view>

namespace smil {
enum class Phase {
  command_line,
  parsing,
  verification,
  binding,
  linking,
  execution,
  unknown = 255
};
struct SourceSpan {
  std::string source;
  std::size_t byte_begin{};
  std::size_t byte_end{};
  std::size_t line{1};
  std::size_t column{1};
};
struct Diagnostic {
  Phase phase;
  std::string code;
  SourceSpan span;
  std::string reason;
};
template <typename T> using Result = std::expected<T, Diagnostic>;
enum class Command { version };
std::string_view phase_name(Phase phase);
Result<Command> parse_command(std::span<const std::string_view> args,
                              std::ostream &log);
} // namespace smil

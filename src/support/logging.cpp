#include "support/logging.hpp"

#include <array>
#include <cassert>

namespace smil {
namespace {
void write_string(std::string_view text, std::ostream &out) {
  constexpr std::string_view hex = "0123456789abcdef";
  out << '"';
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') {
      out << '\\' << static_cast<char>(byte);
    } else if (byte < 0x20) {
      out << "\\u00" << hex[byte >> 4] << hex[byte & 0xf];
    } else {
      out << static_cast<char>(byte);
    }
  }
  out << '"';
}
} // namespace

LogStatus write_log(LogLevel level, std::string_view unit,
                    std::string_view event, std::string_view message,
                    std::ostream &out) {
  assert(!unit.empty());
  constexpr std::array<std::string_view, 4> levels{"debug", "info", "warning",
                                                   "error"};
  const auto index = static_cast<std::size_t>(level);
  if (index >= levels.size()) {
    return LogStatus::invalid_level;
  }
  out << "{\"level\":";
  write_string(levels[index], out);
  out << ",\"unit\":";
  write_string(unit, out);
  out << ",\"event\":";
  write_string(event, out);
  out << ",\"message\":";
  write_string(message, out);
  out << "}\n";
  return out ? LogStatus::written : LogStatus::io_error;
}

LogStatus log_entry(std::string_view unit, std::ostream &out) {
  return write_log(LogLevel::debug, unit, "entry", "enter", out);
}
LogStatus log_debug(std::string_view unit, std::string_view message,
                    std::ostream &out) {
  return write_log(LogLevel::debug, unit, "debug", message, out);
}
LogStatus log_error(std::string_view unit, std::string_view reason,
                    std::ostream &out) {
  return write_log(LogLevel::error, unit, "error", reason, out);
}
} // namespace smil

#include "support/logging.hpp"

#include <array>
#include <sstream>

bool logging_cases() {
  std::ostringstream out;
  if (smil::log_entry("sample", out) != smil::LogStatus::written ||
      out.str() != "{\"level\":\"debug\",\"unit\":\"sample\",\"event\":"
                   "\"entry\",\"message\":\"enter\"}\n") {
    return false;
  }
  out.str("");
  if (smil::log_debug("sample", "\"\\\n\1", out) != smil::LogStatus::written ||
      out.str() != "{\"level\":\"debug\",\"unit\":\"sample\",\"event\":"
                   "\"debug\",\"message\":\"\\\"\\\\\\u000a\\u0001\"}\n") {
    return false;
  }
  for (const auto level :
       {smil::LogLevel::info, smil::LogLevel::warning, smil::LogLevel::error}) {
    if (smil::write_log(level, "sample", "probe", "", out) !=
        smil::LogStatus::written) {
      return false;
    }
  }
  out.str("");
  if (smil::log_debug("sample", "λ\t\r", out) != smil::LogStatus::written ||
      out.str().find("λ\\u0009\\u000d") == std::string::npos) {
    return false;
  }
  out.str("");
  if (smil::log_error("sample", "actionable reason", out) !=
          smil::LogStatus::written ||
      out.str() != "{\"level\":\"error\",\"unit\":\"sample\",\"event\":"
                   "\"error\",\"message\":\"actionable reason\"}\n") {
    return false;
  }
  if (smil::write_log(smil::LogLevel::unknown, "sample", "probe", "", out) !=
      smil::LogStatus::invalid_level) {
    return false;
  }
  out.setstate(std::ios::badbit);
  return smil::log_entry("sample", out) == smil::LogStatus::io_error;
}

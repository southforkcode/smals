#pragma once

#include <ostream>
#include <string_view>

namespace smil {
enum class LogLevel { debug, info, warning, error, unknown = 255 };
enum class LogStatus { written, invalid_level, io_error };
LogStatus write_log(LogLevel level, std::string_view unit,
                    std::string_view event, std::string_view message,
                    std::ostream &out);
LogStatus log_entry(std::string_view unit, std::ostream &out);
LogStatus log_debug(std::string_view unit, std::string_view message,
                    std::ostream &out);
LogStatus log_error(std::string_view unit, std::string_view reason,
                    std::ostream &out);
} // namespace smil

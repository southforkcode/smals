#include "support/trace.hpp"
#include "support/logging.hpp"

#include <sstream>
#include <tuple>
#include <utility>

namespace smil {
namespace {
Result<void> trace_error(std::string code, std::string reason,
                         std::size_t index, std::ostream &log) {
  std::ostringstream message;
  message << "error[" << code << "]: " << reason << " at event " << index;
  log_error("trace", message.str(), log);
  return std::unexpected(Diagnostic{Phase::execution,
                                    std::move(code),
                                    {"<trace>", index, index + 1, 1, index + 1},
                                    std::move(reason)});
}
Result<void> validate(std::span<const Event> trace, std::ostream &log) {
  log_entry("trace.validate", log);
  for (std::size_t index = 0; index < trace.size(); ++index) {
    if (static_cast<unsigned>(trace[index].kind) >= 6) {
      return trace_error("TRACE_KIND", "unknown observable event kind", index,
                         log);
    }
    if (index > 0 && trace[index].sequence <= trace[index - 1].sequence) {
      return trace_error("TRACE_ORDER", "event sequence must strictly increase",
                         index, log);
    }
  }
  return {};
}
} // namespace

Result<void> compare_traces(std::span<const Event> expected,
                            std::span<const Event> actual, std::ostream &log) {
  log_entry("compare_traces", log);
  auto expected_valid = validate(expected, log);
  if (!expected_valid) {
    return expected_valid;
  }
  auto actual_valid = validate(actual, log);
  if (!actual_valid) {
    return actual_valid;
  }
  if (expected.size() != actual.size()) {
    return trace_error("TRACE_LENGTH", "observable event counts differ", 0,
                       log);
  }
  for (std::size_t index = 0; index < expected.size(); ++index) {
    const auto &left = expected[index];
    const auto &right = actual[index];
    if (std::tie(left.sequence, left.kind, left.subject, left.value,
                 left.bytes) != std::tie(right.sequence, right.kind,
                                         right.subject, right.value,
                                         right.bytes)) {
      return trace_error("TRACE_MISMATCH", "observable event fields differ",
                         index, log);
    }
  }
  return {};
}
} // namespace smil

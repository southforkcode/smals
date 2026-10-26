#pragma once

#include "support/diagnostic.hpp"
#include <cstdint>
#include <span>
#include <vector>

namespace smil {
enum class EventKind {
  value,
  memory,
  device,
  fault,
  lifecycle,
  resource,
  unknown = 255
};
struct Event {
  std::uint64_t sequence;
  EventKind kind;
  std::string subject;
  std::uint64_t value;
  std::vector<std::uint8_t> bytes;
  std::string debug;
};
using Trace = std::vector<Event>;
Result<void> compare_traces(std::span<const Event> expected,
                            std::span<const Event> actual, std::ostream &log);
} // namespace smil

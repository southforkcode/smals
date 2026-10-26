#include "support/guarded.hpp"

#include <array>
#include <limits>

bool guarded_cases() {
  using fixture::Fault;
  fixture::Buffer buffer(4);
  std::array<std::uint8_t, 2> bytes{7, 9};
  std::array<std::uint8_t, 2> output{};
  if (buffer.read(0, output) != Fault::uninitialized ||
      buffer.write(1, bytes) != Fault::none ||
      buffer.read(1, output) != Fault::none || output != bytes ||
      !buffer.canaries_intact()) {
    return false;
  }
  if (buffer.write(3, bytes) != Fault::bounds ||
      buffer.write(std::numeric_limits<std::size_t>::max(), bytes) !=
          Fault::bounds ||
      buffer.read(1, output) != Fault::none || output != bytes ||
      !buffer.canaries_intact()) {
    return false;
  }
  std::array<std::uint8_t, 1> neighbor{};
  if (buffer.read(0, neighbor) != Fault::uninitialized ||
      buffer.read(4, output) != Fault::bounds) {
    return false;
  }
  std::array<std::uint8_t, 2> untouched{0xcc, 0xdd};
  const auto saved = untouched;
  if (buffer.read(2, untouched) != Fault::uninitialized || untouched != saved ||
      buffer.read(std::numeric_limits<std::size_t>::max(), output) !=
          Fault::bounds ||
      buffer.write(4, {}) != Fault::none || buffer.read(4, {}) != Fault::none) {
    return false;
  }
  fixture::Buffer invalid(65);
  fixture::Buffer empty(0);
  if (invalid.write(0, bytes) != Fault::bounds ||
      invalid.read(0, output) != Fault::bounds || invalid.canaries_intact() ||
      empty.write(0, {}) != Fault::none || !empty.canaries_intact()) {
    return false;
  }
  for (std::size_t guard = 0; guard < 4; ++guard) {
    fixture::Buffer damaged(4);
    if (damaged.damage_guard(guard) != Fault::none ||
        damaged.canaries_intact()) {
      return false;
    }
  }
  if (buffer.damage_guard(4) != Fault::bounds || !buffer.canaries_intact() ||
      invalid.damage_guard(0) != Fault::bounds) {
    return false;
  }
  fixture::Budget budget(4);
  budget.fail_next();
  if (budget.reserve(1) != Fault::injected || budget.used() != 0 ||
      budget.reserve(4) != Fault::none || budget.used() != 4 ||
      budget.reserve(1) != Fault::capacity || budget.used() != 4 ||
      budget.release(5) != Fault::capacity || budget.used() != 4 ||
      budget.release(4) != Fault::none || budget.used() != 0) {
    return false;
  }
  fixture::Budget wide(std::numeric_limits<std::uint64_t>::max());
  return wide.reserve(std::numeric_limits<std::uint64_t>::max()) ==
             Fault::none &&
         wide.reserve(1) == Fault::capacity &&
         wide.used() == std::numeric_limits<std::uint64_t>::max();
}

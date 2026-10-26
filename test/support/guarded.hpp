#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>

namespace fixture {
enum class Fault { none, bounds, uninitialized, capacity, injected };
class Buffer {
public:
  explicit Buffer(std::size_t size) : size_(size) { storage_.fill(0xa5); }
  Fault write(std::size_t offset, std::span<const std::uint8_t> bytes);
  Fault read(std::size_t offset, std::span<std::uint8_t> bytes) const;
  bool canaries_intact() const;
  Fault damage_guard(std::size_t guard);

private:
  std::size_t size_;
  std::array<std::uint8_t, 68> storage_{};
  std::array<bool, 64> initialized_{};
};
class Budget {
public:
  explicit Budget(std::uint64_t limit) : limit_(limit) {}
  Fault reserve(std::uint64_t amount);
  Fault release(std::uint64_t amount);
  void fail_next() { fail_ = true; }
  std::uint64_t used() const { return used_; }

private:
  std::uint64_t limit_;
  std::uint64_t used_{};
  bool fail_{};
};
} // namespace fixture

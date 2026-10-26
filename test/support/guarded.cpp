#include "guarded.hpp"

#include <iostream>

namespace fixture {
Fault Buffer::write(std::size_t offset, std::span<const std::uint8_t> bytes) {
  std::clog << "debug: entering fixture buffer write\n";
  if (size_ > 64 || offset > size_ || bytes.size() > size_ - offset) {
    std::clog << "error: buffer write exceeds payload extent\n";
    return Fault::bounds;
  }
  for (std::size_t index = 0; index < bytes.size(); ++index) {
    storage_[offset + index + 2] = bytes[index];
    initialized_[offset + index] = true;
  }
  return Fault::none;
}
Fault Buffer::read(std::size_t offset, std::span<std::uint8_t> bytes) const {
  std::clog << "debug: entering fixture buffer read\n";
  if (size_ > 64 || offset > size_ || bytes.size() > size_ - offset) {
    std::clog << "error: buffer read exceeds payload extent\n";
    return Fault::bounds;
  }
  for (std::size_t index = 0; index < bytes.size(); ++index) {
    if (!initialized_[offset + index]) {
      std::clog << "error: buffer read includes uninitialized bytes\n";
      return Fault::uninitialized;
    }
  }
  for (std::size_t index = 0; index < bytes.size(); ++index) {
    bytes[index] = storage_[offset + index + 2];
  }
  return Fault::none;
}
bool Buffer::canaries_intact() const {
  std::clog << "debug: entering fixture canary check\n";
  if (size_ > 64) {
    return false;
  }
  for (std::size_t guard = 0; guard < 4; ++guard) {
    const auto position = guard < 2 ? guard : size_ + guard;
    if (storage_[position] != 0xa5) {
      return false;
    }
  }
  return true;
}
Fault Buffer::damage_guard(std::size_t guard) {
  std::clog << "debug: entering guard damage injection\n";
  if (size_ > 64 || guard > 3) {
    std::clog << "error: guard injection index exceeds fixture bounds\n";
    return Fault::bounds;
  }
  storage_[guard < 2 ? guard : size_ + guard] = 0;
  return Fault::none;
}
Fault Budget::reserve(std::uint64_t amount) {
  std::clog << "debug: entering fixture reserve\n";
  if (fail_) {
    fail_ = false;
    std::clog << "error: injected reservation failure\n";
    return Fault::injected;
  }
  if (amount > limit_ - used_) {
    std::clog << "error: reservation exceeds remaining capacity\n";
    return Fault::capacity;
  }
  used_ += amount;
  return Fault::none;
}
Fault Budget::release(std::uint64_t amount) {
  std::clog << "debug: entering fixture release\n";
  if (amount > used_) {
    std::clog << "error: release exceeds charged amount\n";
    return Fault::capacity;
  }
  used_ -= amount;
  return Fault::none;
}
} // namespace fixture

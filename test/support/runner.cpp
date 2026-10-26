#include "runner.hpp"
#include "support/diagnostic.hpp"
#include "support/version.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <expected>
#include <iostream>
#include <optional>
#include <string>

bool diagnostic_cases();
bool trace_cases();
bool guarded_cases();

namespace {
struct Options {
  std::optional<std::string_view> selected;
  std::uint64_t seed{};
  std::uint64_t limit{32};
  bool invert{};
};

std::expected<Options, std::string>
parse_options(std::span<const std::string_view> args) {
  std::clog << "debug: entering parse_options\n";
  Options options;
  for (std::size_t index = 0; index < args.size(); ++index) {
    const auto flag = args[index];
    if (flag == "--invert") {
      options.invert = true;
      continue;
    }
    if ((flag != "--case" && flag != "--seed" && flag != "--limit") ||
        ++index == args.size()) {
      std::cerr << "invalid or incomplete runner option: " << flag << '\n';
      return std::unexpected("invalid option");
    }
    if (flag == "--case") {
      options.selected = args[index];
      continue;
    }
    std::uint64_t value{};
    const auto text = args[index];
    const auto parsed =
        std::from_chars(text.data(), text.data() + text.size(), value);
    if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size() ||
        (flag == "--limit" && (value == 0 || value > 32))) {
      std::cerr << "invalid runner numeric value: " << text << '\n';
      return std::unexpected("invalid numeric value");
    }
    if (flag == "--seed") {
      options.seed = value;
    } else {
      options.limit = value;
    }
  }
  return options;
}

struct Observation {
  bool accepted;
  std::string input;
};
struct Case {
  std::string_view id;
  bool expected;
  Observation (*observe)(std::uint64_t);
};

Observation version_case(std::uint64_t) {
  return {smil::tool_version == "0.1.0", std::string(smil::tool_version)};
}
Observation fields_case(std::uint64_t) {
  return {diagnostic_cases(), "diagnostic-fields"};
}
Observation reject_case(std::uint64_t seed) {
  auto input = "invalid." + std::to_string(seed);
  const std::array<std::string_view, 1> args{input};
  return {smil::parse_command(args, std::clog).has_value(), input};
}
Observation traces_case(std::uint64_t) {
  return {trace_cases(), "observable-records"};
}
Observation guards_case(std::uint64_t) {
  return {guarded_cases(), "guarded-buffer-and-budget"};
}
constexpr std::array<Case, 5> registry{
    {{"runtime.guards", true, guards_case},
     {"trace.records", true, traces_case},
     {"version", true, version_case},
     {"diagnostics", true, fields_case},
     {"command.reject", false, reject_case}}};
} // namespace

int run_cases(std::span<const std::string_view> args) {
  std::clog << "debug: entering run_cases\n";
  auto parsed = parse_options(args);
  if (!parsed) {
    return 2;
  }
  const auto &options = *parsed;
  auto selected = [&](const Case &item) {
    return !options.selected || item.id == *options.selected;
  };
  const auto count = std::count_if(registry.begin(), registry.end(), selected);
  if (count == 0 || static_cast<std::uint64_t>(count) > options.limit) {
    std::cerr << "empty or oversized case selection\n";
    return 2;
  }
  bool passed = true;
  for (const auto &item : registry) {
    if (!selected(item)) {
      continue;
    }
    const auto observed = item.observe(options.seed);
    const bool expected = item.expected != options.invert;
    std::cout << "case=" << item.id << " seed=" << options.seed
              << " input=" << observed.input
              << " expected=" << (expected ? "accept" : "reject")
              << " observed=" << (observed.accepted ? "accept" : "reject")
              << '\n';
    if (observed.accepted != expected) {
      std::cerr << "case mismatch: " << item.id << " seed=" << options.seed
                << " input=" << observed.input << '\n';
      passed = false;
    }
  }
  return passed ? 0 : 1;
}

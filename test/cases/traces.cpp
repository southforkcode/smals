#include "support/trace.hpp"

#include <array>
#include <sstream>
#include <utility>

bool trace_cases() {
  using smil::EventKind;
  const smil::Trace expected{
      {1, EventKind::value, "r0", 42, {42}, "oracle"},
      {2, EventKind::memory, "allocation", 4, {1, 2}, "oracle"},
      {3, EventKind::device, "port", 1, {7}, "oracle"},
      {4, EventKind::fault, "probe", 7, {}, "oracle"},
      {5, EventKind::lifecycle, "startup", 0, {}, "oracle"},
      {6, EventKind::resource, "scratch", 8, {}, "oracle"}};
  smil::Trace actual{
      {1, EventKind::value, "r0", 42, {42}, "implementation debug"},
      {2, EventKind::memory, "allocation", 4, {1, 2}, "other debug"},
      {3, EventKind::device, "port", 1, {7}, ""},
      {4, EventKind::fault, "probe", 7, {}, ""},
      {5, EventKind::lifecycle, "startup", 0, {}, ""},
      {6, EventKind::resource, "scratch", 8, {}, ""}};
  std::ostringstream log;
  if (!smil::compare_traces(expected, actual, log) ||
      !smil::compare_traces({}, {}, log)) {
    return false;
  }
  for (int field = 0; field < 5; ++field) {
    auto changed = actual;
    switch (field) {
    case 0:
      changed[0].sequence = 0;
      break;
    case 1:
      changed[0].kind = EventKind::memory;
      break;
    case 2:
      changed[0].subject = "different";
      break;
    case 3:
      changed[0].value = 43;
      break;
    case 4:
      changed[0].bytes = {41};
      break;
    }
    auto result = smil::compare_traces(expected, changed, log);
    if (result || result.error().code != "TRACE_MISMATCH") {
      return false;
    }
  }
  auto changed = actual;
  std::swap(changed[0], changed[1]);
  auto order = smil::compare_traces(expected, changed, log);
  auto oracle_order = smil::compare_traces(changed, actual, log);
  if (order || oracle_order || smil::compare_traces(changed, changed, log) ||
      order.error().code != "TRACE_ORDER") {
    return false;
  }
  changed = actual;
  changed[1].sequence = changed[0].sequence;
  if (smil::compare_traces(expected, changed, log)) {
    return false;
  }
  changed = actual;
  changed.pop_back();
  auto length = smil::compare_traces(expected, changed, log);
  if (length || length.error().code != "TRACE_LENGTH") {
    return false;
  }
  changed = actual;
  changed[0].kind = EventKind::unknown;
  auto kind = smil::compare_traces(expected, changed, log);
  return !kind && kind.error().code == "TRACE_KIND";
}

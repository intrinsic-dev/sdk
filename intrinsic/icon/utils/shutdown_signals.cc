// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/shutdown_signals.h"

#include <unistd.h>

#include <atomic>
#include <csignal>
#include <optional>

#include "absl/log/log.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/release/source_location.h"

namespace intrinsic::icon {
namespace {

// We use an atomic here because callers of ShutdownSignalHandler and
// IsShutdownRequested trigger activity on other threads, and
// ShutdownSignalHandler must be signal-safe.
std::atomic<ShutdownType> shutdown_requested = ShutdownType::kNotRequested;
// Exit code is only set if the shutdown was requested by a user.
std::atomic<std::optional<int>> user_shutdown_exit_code = {};

// Signal safe function to convert a signal number into a string.
absl::string_view ToString(int signum) {
  switch (signum) {
    case SIGHUP:
      return "SIGHUP";
    case SIGINT:
      return "SIGINT";
    case SIGQUIT:
      return "SIGQUIT";
    case SIGILL:
      return "SIGILL";
    case SIGTRAP:
      return "SIGTRAP";
    case SIGABRT:
      return "SIGABRT";
    case SIGBUS:
      return "SIGBUS";
    case SIGFPE:
      return "SIGFPE";
    case SIGKILL:
      return "SIGKILL";
    case SIGUSR1:
      return "SIGUSR1";
    case SIGSEGV:
      return "SIGSEGV";
    case SIGUSR2:
      return "SIGUSR2";
    case SIGPIPE:
      return "SIGPIPE";
    case SIGALRM:
      return "SIGALRM";
    case SIGTERM:
      return "SIGTERM";
    case SIGCHLD:
      return "SIGCHLD";
    case SIGCONT:
      return "SIGCONT";
    case SIGSTOP:
      return "SIGSTOP";
    case SIGTSTP:
      return "SIGTSTP";
    case SIGTTIN:
      return "SIGTTIN";
    case SIGTTOU:
      return "SIGTTOU";
    case SIGURG:
      return "SIGURG";
    case SIGXCPU:
      return "SIGXCPU";
    case SIGXFSZ:
      return "SIGXFSZ";
    case SIGVTALRM:
      return "SIGVTALRM";
    case SIGPROF:
      return "SIGPROF";
    case SIGWINCH:
      return "SIGWINCH";
    case SIGIO:
      return "SIGIO";
    case SIGPWR:
      return "SIGPWR";
    case SIGSYS:
      return "SIGSYS";
    default:
      return "Unknown Signal";
  }
}

}  // namespace

// We do not use logging or printf in the signal handler to be signal-safe.
void ShutdownSignalHandler(int sig) {
  const char message[] = "Got signal ";
  (void)write(STDERR_FILENO, message, sizeof(message));
  auto signal_name = ToString(sig);
  (void)write(STDERR_FILENO, signal_name.data(), signal_name.size());
  const char message2[] = ", shutting down.\n";
  (void)write(STDERR_FILENO, message2, sizeof(message2));
  shutdown_requested.store(ShutdownType::kSignalledRequest);
}

void RequestShutdownByUser(absl::string_view shutdown_reason,
                           std::optional<int> exit_code,
                           intrinsic::SourceLocation loc) {
  LOG(INFO).AtLocation(loc.file_name(), loc.line())
      << "Shutting down per user request: " << shutdown_reason;
  user_shutdown_exit_code.store(exit_code);
  shutdown_requested.store(ShutdownType::kUserRequest);
}

ShutdownType IsShutdownRequested() { return shutdown_requested.load(); }

std::optional<int> GetShutdownExitCode() {
  return user_shutdown_exit_code.load();
}
}  // namespace intrinsic::icon

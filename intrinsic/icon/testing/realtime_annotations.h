// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_TESTING_REALTIME_ANNOTATIONS_H_
#define INTRINSIC_ICON_TESTING_REALTIME_ANNOTATIONS_H_

// Annotation macros to tell the Intrinsic static analyzer what functions are
// to be checked, and what functions are allowed or disallowed in the
// transitive call stack.

#if defined(__clang__) && (!defined(SWIG))
#define INTRINSIC_CLANG_ATTRIBUTE__(x) __attribute__((x))
#else
#define INTRINSIC_CLANG_ATTRIBUTE__(x)  // no-op
#endif

// INTRINSIC_CHECK_REALTIME_SAFE
//
// The developer intends for the annotated function to be used in a realtime
// context. The realtime analysis tool will check this function for realtime
// safety. If the annotated function transitively calls any
// INTRINSIC_NON_REALTIME_ONLY functions or a hardcoded denylist of forbidden
// functions, an analyzer error will result.
#define INTRINSIC_CHECK_REALTIME_SAFE \
  INTRINSIC_CLANG_ATTRIBUTE__(annotate("intrinsic-realtime-safe"))

// INTRINSIC_NON_REALTIME_ONLY
//
// The developer declares that the annotated function should NEVER be used in a
// realtime context. If invoked from a realtime context, an analyzer error will
// result.
#define INTRINSIC_NON_REALTIME_ONLY \
  INTRINSIC_CLANG_ATTRIBUTE__(annotate("intrinsic-realtime-unsafe"))

// INTRINSIC_SUPPRESS_REALTIME_CHECK
//
// The developer intends for the annotated function to be used in a realtime
// context, even though it may violate realtime safety rules.
//
// ***
// THIS SHOULD ONLY BE USED AS A LAST RESORT TO SUPPRESS VIOLATIONS WHEN THE
// DEVELOPER KNOWS WHAT THEY ARE DOING IS SAFE.
// ***
//
// During analysis of functions annotated INTRINSIC_CHECK_REALTIME_SAFE, any
// encountered callees annotated INTRINSIC_SUPPRESS_REALTIME_CHECK will
// be treated as realtime-safe, regardless of the callee's contents.
//
// Example:
//
//  void Foo() INTRINSIC_SUPPRESS_REALTIME_CHECK {
//    sleep(1);
//  }
//
//  void Bar() INTRINSIC_CHECK_REALTIME_SAFE {
//    Foo();  // OK (no violation).
//  }
#define INTRINSIC_SUPPRESS_REALTIME_CHECK \
  INTRINSIC_CLANG_ATTRIBUTE__(annotate("intrinsic-realtime-suppress"))

#endif  // INTRINSIC_ICON_TESTING_REALTIME_ANNOTATIONS_H_

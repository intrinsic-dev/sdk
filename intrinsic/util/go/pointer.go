// Copyright 2023 Intrinsic Innovation LLC

// Package pointer contains utility functions for generically working with pointers.
package pointer

// To returns a pointer to the value of a constant, since it is not possible to
// get a pointer to a const value.  This often is useful for assigning to
// optional fields in the golang proto API.
func To[T any](value T) *T {
	return &value
}

// NotNil returns true if a pointer is not nil.  This is primarily useful in
// filtering results from an iterator that may return nil results.
func NotNil[T any](p *T) bool {
	return p != nil
}

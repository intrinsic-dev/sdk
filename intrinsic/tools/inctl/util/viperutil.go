// Copyright 2023 Intrinsic Innovation LLC

// Package viperutil provides utilities that make the integration of viper and cobra easier.
package viperutil

import (
	"github.com/spf13/pflag"
	"github.com/spf13/viper"
)

var (
	viperEnvPrefix = "intrinsic"
)

var nothingToBindToEnv = func(name string) bool { return false }

// BindToViper takes a flagset populated for use with pflags or cobra and binds the flags to viper.
//
// Flags are bound to a variable of the same name if bindToEnv returns true for it
func BindToViper(flags *pflag.FlagSet, bindToEnv func(name string) bool) *viper.Viper {
	v := viper.New()

	BindFlags(v, flags, bindToEnv)

	return v
}

// BindFlags takes a flagset populated for use with pflags or cobra and binds the flags to viper.
//
// Flags are bound to a variable of the same name if bindToEnv returns true for it
func BindFlags(v *viper.Viper, flags *pflag.FlagSet, bindToEnv func(name string) bool) {
	// Prefix have to be set before we are going to bind ANY flags into ENV.
	// This behavior is weirdly implemented in Viper.
	v.SetEnvPrefix(viperEnvPrefix)
	if bindToEnv == nil {
		bindToEnv = nothingToBindToEnv
	}
	flags.VisitAll(func(flag *pflag.Flag) {
		_ = v.BindPFlag(flag.Name, flag)
		if bindToEnv(flag.Name) {
			_ = v.BindEnv(flag.Name)
		}
	})
}

// BindToListEnv provides a suitable 2nd argument to BindToViper that binds for all flags provides as arguments.
func BindToListEnv(names ...string) func(name string) bool {
	return func(name string) bool {
		return contains(names, name)
	}
}

func contains[E comparable](in []E, e E) bool {
	if len(in) == 0 {
		return false
	}
	for _, elm := range in {
		if elm == e {
			return true
		}
	}
	return false
}

// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// Package color contains helper functions to simplify color-printing to the terminal.
package color

import (
	"fmt"
	"io"
	"os"
)

const reset = "\x1b[0m"

type x struct {
	fg string
	bg string
}

func newX() x { return x{} }

// C initializes a builder-like object. Call color modification functions on it, and run [Printf] in
// the end. E.g. `color.C.Red().Printf("hello")` will print "hello" in red foreground.
var C = newX()

// Black changes foreground color to black.
func (c x) Black() x {
	return x{fg: "\x1b[30m", bg: c.bg}
}

// Red changes foreground color to red.
func (c x) Red() x {
	return x{fg: "\x1b[31m", bg: c.bg}
}

// Green changes foreground color to green.
func (c x) Green() x {
	return x{fg: "\x1b[32m", bg: c.bg}
}

// Yellow changes foreground color to yellow.
func (c x) Yellow() x {
	return x{fg: "\x1b[33m", bg: c.bg}
}

// Blue changes foreground color to blue.
func (c x) Blue() x {
	return x{fg: "\x1b[34m", bg: c.bg}
}

// Magenta changes foreground color to magenta.
func (c x) Magenta() x {
	return x{fg: "\x1b[35m", bg: c.bg}
}

// Cyan changes foreground color to cyan.
func (c x) Cyan() x {
	return x{fg: "\x1b[36m", bg: c.bg}
}

// White changes foreground color to white.
func (c x) White() x {
	return x{fg: "\x1b[37m", bg: c.bg}
}

// Default changes foreground color to default.
func (c x) Default() x {
	return x{fg: "\x1b[39m", bg: c.bg}
}

// LightGray changes foreground color to light gray.
func (c x) LightGray() x {
	return x{fg: "\x1b[90m", bg: c.bg}
}

// LightRed changes foreground color to light red.
func (c x) LightRed() x {
	return x{fg: "\x1b[91m", bg: c.bg}
}

// LightGreen changes foreground color to light green.
func (c x) LightGreen() x {
	return x{fg: "\x1b[92m", bg: c.bg}
}

// LightYellow changes foreground color to light yellow.
func (c x) LightYellow() x {
	return x{fg: "\x1b[93m", bg: c.bg}
}

// LightBlue changes foreground color to light blue.
func (c x) LightBlue() x {
	return x{fg: "\x1b[94m", bg: c.bg}
}

// LightMagenta changes foreground color to light magenta.
func (c x) LightMagenta() x {
	return x{fg: "\x1b[95m", bg: c.bg}
}

// LightCyan changes foreground color to light cyan.
func (c x) LightCyan() x {
	return x{fg: "\x1b[96m", bg: c.bg}
}

// LightWhite changes foreground color to light white.
func (c x) LightWhite() x {
	return x{fg: "\x1b[97m", bg: c.bg}
}

// BlackBackground changes background color to black.
func (c x) BlackBackground() x {
	return x{fg: c.fg, bg: "\x1b[40m"}
}

// RedBackground changes background color to red.
func (c x) RedBackground() x {
	return x{fg: c.fg, bg: "\x1b[41m"}
}

// GreenBackground changes background color to green.
func (c x) GreenBackground() x {
	return x{fg: c.fg, bg: "\x1b[42m"}
}

// YellowBackground changes background color to yellow.
func (c x) YellowBackground() x {
	return x{fg: c.fg, bg: "\x1b[43m"}
}

// BlueBackground changes background color to blue.
func (c x) BlueBackground() x {
	return x{fg: c.fg, bg: "\x1b[44m"}
}

// MagentaBackground changes background color to magenta.
func (c x) MagentaBackground() x {
	return x{fg: c.fg, bg: "\x1b[45m"}
}

// CyanBackground changes background color to cyan.
func (c x) CyanBackground() x {
	return x{fg: c.fg, bg: "\x1b[46m"}
}

// WhiteBackground changes background color to white.
func (c x) WhiteBackground() x {
	return x{fg: c.fg, bg: "\x1b[47m"}
}

// DefaultBackground changes background color to default.
func (c x) DefaultBackground() x {
	return x{fg: c.fg, bg: "\x1b[49m"}
}

// LightGrayBackground changes background color to light gray.
func (c x) LightGrayBackground() x {
	return x{fg: c.fg, bg: "\x1b[100m"}
}

// LightRedBackground changes background color to light red.
func (c x) LightRedBackground() x {
	return x{fg: c.fg, bg: "\x1b[101m"}
}

// LightGreenBackground changes background color to light green.
func (c x) LightGreenBackground() x {
	return x{fg: c.fg, bg: "\x1b[102m"}
}

// LightYellowBackground changes background color to light yellow.
func (c x) LightYellowBackground() x {
	return x{fg: c.fg, bg: "\x1b[103m"}
}

// LightBlueBackground changes background color to light blue.
func (c x) LightBlueBackground() x {
	return x{fg: c.fg, bg: "\x1b[104m"}
}

// LightMagentaBackground changes background color to light magenta.
func (c x) LightMagentaBackground() x {
	return x{fg: c.fg, bg: "\x1b[105m"}
}

// LightCyanBackground changes background color to light cyan.
func (c x) LightCyanBackground() x {
	return x{fg: c.fg, bg: "\x1b[106m"}
}

// LightWhiteBackground changes background color to light white.
func (c x) LightWhiteBackground() x {
	return x{fg: c.fg, bg: "\x1b[107m"}
}

// Printf formats according to a format specifier and writes to standard output. The foreground
// and background colors are controlled by the [C] object. It returns the number of bytes written
// and any write error encountered.
func (c x) Printf(format string, a ...any) (int, error) {
	return c.Fprintf(os.Stdout, format, a...)
}

// Fprintf formats according to a format specifier and writes to w. The foreground
// and background colors are controlled by the [C] object. It returns the number of bytes written
// and any write error encountered.
func (c x) Fprintf(w io.Writer, format string, a ...any) (int, error) {
	return fmt.Fprintf(w, c.fg+c.bg+format+reset, a...)
}

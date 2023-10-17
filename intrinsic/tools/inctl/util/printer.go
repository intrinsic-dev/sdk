// Copyright 2023 Intrinsic Innovation LLC

// Package printer provides utilities for inctl printing.
package printer

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

const (
	// KeyOutput is a string used to refer the output flag.
	KeyOutput = "output"
	// JSONOutputFormat is a string indicating JSON output format.
	JSONOutputFormat = "json"
	// TextOutputFormat is a string indicating human-readable text output format.
	TextOutputFormat = ""
)

// AllowedFormats is a list of possible output formats.
var AllowedFormats = []string{JSONOutputFormat}

type any = interface{}

// Message defines a struct for printing a single message in JSON format.
type Message struct {
	Msg string `json:"msg"`
}

// Printer is the interface that wraps the basic Print methods.
type Printer interface {
	io.Writer
	Print(val any)
	PrintS(str string)
	PrintSf(format string, a ...any)
}

// JSONPrinter implements Printer.
type JSONPrinter struct {
	enc *json.Encoder
}

func (p *JSONPrinter) Write(c []byte) (n int, err error) {
	p.PrintS(string(c))
	return len(c), nil
}

// Print prints val in JSON format.
func (p *JSONPrinter) Print(val any) {
	p.enc.Encode(val)
}

// PrintS prints a string as a JSON object with a single "msg" field.
func (p *JSONPrinter) PrintS(str string) {
	p.Print(&Message{Msg: str})
}

// PrintSf prints the formatted string as a JSON object with a single "msg" field.
func (p *JSONPrinter) PrintSf(format string, a ...any) {
	p.PrintS(fmt.Sprintf(format, a...))
}

// TextPrinter implements Printer.
type TextPrinter struct {
	w io.Writer
}

func (p *TextPrinter) Write(c []byte) (n int, err error) {
	return p.w.Write(c)
}

// Print prints val in human-readable text format.
func (p *TextPrinter) Print(val any) {
	var s string
	if ta, ok := val.(fmt.Stringer); ok {
		s = ta.String()
	} else {
		s = fmt.Sprintf("%v", val)
	}
	fmt.Fprintln(p.w, s)
}

// PrintS prints a string as a JSON object with a single "msg" field.
func (p *TextPrinter) PrintS(str string) {
	p.Print(str)
}

// PrintSf prints the formatted string as a JSON object with a single "msg" field.
func (p *TextPrinter) PrintSf(format string, a ...any) {
	p.PrintS(fmt.Sprintf(format, a...))
}

// NewPrinterWithWriter returns a new Printer which writes to the given writer
// using the given output format.
func NewPrinterWithWriter(outputFormat string, w io.Writer) (Printer, error) {
	if outputFormat == JSONOutputFormat {
		return &JSONPrinter{enc: json.NewEncoder(w)}, nil
	} else if outputFormat == TextOutputFormat {
		return &TextPrinter{w: w}, nil
	}
	return nil, fmt.Errorf("unknown output format %q", outputFormat)
}

// NewPrinter returns a new Printer which writes to os.Stdout using the given
// output format.
func NewPrinter(outputFormat string) (Printer, error) {
	return NewPrinterWithWriter(outputFormat, os.Stdout)
}

// AsPrinter tries to convert supplied io.Writer to Printer.
// If in parameter is of type Printer, it returns it without modification
//
// If in parameter is not of type Printer, returns new Printer with in as its
// internal writer if orElseType is specified or indicates failure if new
// Printer cannot be constructed.
//
// If in is not Printer and orElseType is not specified, method returns
// nil Printer indicating conversion didn't happen
func AsPrinter(in io.Writer, orElseType ...string) (Printer, bool) {
	if prt, ok := in.(Printer); ok {
		return prt, ok
	} else if len(orElseType) > 0 {
		prt, err := NewPrinterWithWriter(orElseType[0], in)
		return prt, err == nil
	}
	return nil, false
}

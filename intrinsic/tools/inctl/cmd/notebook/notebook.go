// Copyright 2023 Intrinsic Innovation LLC

// Package notebook for commands that work with Solution Building library enabled Jupyter notebooks.
package notebook

import (
	"intrinsic/tools/inctl/cmd/root"
	"intrinsic/tools/inctl/util/cobrautil"
)

var notebookCmd = cobrautil.ParentOfNestedSubcommands("notebook", "Work with Solution Building library enabled Jupyter notebooks.")

func init() {
	root.RootCmd.AddCommand(notebookCmd)
}

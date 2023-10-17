// Copyright 2023 Intrinsic Innovation LLC

package main

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"flag"
	log "github.com/golang/glog"

	"github.com/google/subcommands"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	fileuploadgrpcpb "intrinsic/platform/file_upload/file_upload_service_go_grpc_proto"
)

type fileServiceClient struct {
	conn   *grpc.ClientConn
	client fileuploadgrpcpb.FileUploadServiceClient
}

func connect(addr string) (*fileServiceClient, error) {
	conn, err := grpc.Dial(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}
	return &fileServiceClient{
		conn:   conn,
		client: fileuploadgrpcpb.NewFileUploadServiceClient(conn),
	}, nil

}

func (c *fileServiceClient) close() error {
	err := c.conn.Close()
	// Log the error, since this may have been called with `defer client.Close()`.
	if err != nil {
		log.Fatalf("Failed to close file service client connection: %v", err)
	}
	return err
}

func (c *fileServiceClient) listFiles(ctx context.Context) ([]*fileuploadgrpcpb.FileInfo, error) {
	resp, err := c.client.ListFiles(ctx, &fileuploadgrpcpb.ListFilesRequest{})
	if err != nil {
		return nil, err
	}
	return resp.GetFiles(), nil
}

func (c *fileServiceClient) removeFiles(ctx context.Context, files []string) error {
	req := &fileuploadgrpcpb.RemoveFilesRequest{Filenames: files}
	_, err := c.client.RemoveFiles(ctx, req)
	return err
}

func (c *fileServiceClient) uploadFile(ctx context.Context, localFilePath string, remoteFileName string) error {
	contents, err := os.ReadFile(localFilePath)
	if err != nil {
		return fmt.Errorf("unable to read file %q: %w", localFilePath, err)
	}
	req := &fileuploadgrpcpb.UploadFileRequest{
		Filename: remoteFileName,
		Contents: contents,
	}
	_, err = c.client.UploadFile(ctx, req)
	return err
}

type listFilesCommand struct {
	stdout io.Writer
	stderr io.Writer
	server string // --server flag
}

func (*listFilesCommand) Name() string     { return "list" }
func (*listFilesCommand) Synopsis() string { return "Lists files available to the ICON server." }
func (*listFilesCommand) Usage() string    { return "list --server=<addr>" }

func (cmd *listFilesCommand) SetFlags(f *flag.FlagSet) {
	f.StringVar(&cmd.server, "server", "xfa.lan:17080", "file manager server address")
}

func (cmd *listFilesCommand) Execute(ctx context.Context, f *flag.FlagSet, _ ...interface{}) subcommands.ExitStatus {
	client, err := connect(cmd.server)
	if err != nil {
		fmt.Fprintf(cmd.stderr, "Failed to connect to file service: %s\n", err)
		return subcommands.ExitFailure
	}
	defer client.close()
	files, err := client.listFiles(ctx)
	if err != nil {
		fmt.Fprintf(cmd.stderr, "Failed to list files: %s\n", err)
		return subcommands.ExitFailure
	}
	anyFound := false
	for _, p := range files {
		fmt.Fprintln(cmd.stdout, p.GetFilename())
		anyFound = true
	}
	if !anyFound {
		fmt.Fprintln(cmd.stdout, "(none)")
	}
	return subcommands.ExitSuccess
}

type removeFilesCommand struct {
	stdout io.Writer
	stderr io.Writer
	server string // --server flag
}

func (*removeFilesCommand) Name() string     { return "remove" }
func (*removeFilesCommand) Synopsis() string { return "Removes files from the server." }
func (*removeFilesCommand) Usage() string    { return "remove --server=<addr> <file0> [<fileN>...]" }

func (cmd *removeFilesCommand) SetFlags(f *flag.FlagSet) {
	f.StringVar(&cmd.server, "server", "xfa.lan:17080", "file manager server address")
}

func (cmd *removeFilesCommand) Execute(ctx context.Context, f *flag.FlagSet, _ ...interface{}) subcommands.ExitStatus {
	if len(f.Args()) == 0 {
		fmt.Fprintf(cmd.stderr, "No files specified.\nUSAGE: %s\n", cmd.Usage())
		return subcommands.ExitFailure
	}
	client, err := connect(cmd.server)
	if err != nil {
		fmt.Fprintf(cmd.stderr, "Failed to connect to file service: %s\n", err)
		return subcommands.ExitFailure
	}
	defer client.close()
	for _, file := range f.Args() {
		if err := client.removeFiles(ctx, []string{file}); err != nil {
			fmt.Fprintf(cmd.stderr, "Failed to remove file %s: %s\n", file, err)
			return subcommands.ExitFailure
		}
		fmt.Fprintf(cmd.stdout, "Removed %s.\n", file)
	}
	return subcommands.ExitSuccess
}

type uploadFileCommand struct {
	stdout io.Writer
	stderr io.Writer
	server string // --server flag
	name   string // --name flag
	enable bool   // --enable flag
}

func (*uploadFileCommand) Name() string     { return "upload" }
func (*uploadFileCommand) Synopsis() string { return "Upload a files to the server." }
func (*uploadFileCommand) Usage() string {
	return "upload --server=<addr> [--name=<name>] [--enable] <file_filename>"
}

func (cmd *uploadFileCommand) SetFlags(f *flag.FlagSet) {
	f.StringVar(&cmd.server, "server", "xfa.lan:17080", "file manager server address")
	f.StringVar(&cmd.name, "name", "", "sets the file name on the server. By default, the file's basename is used.")
}

func (cmd *uploadFileCommand) Execute(ctx context.Context, f *flag.FlagSet, _ ...interface{}) subcommands.ExitStatus {
	client, err := connect(cmd.server)
	if err != nil {
		fmt.Fprintf(cmd.stderr, "Failed to connect to file service: %s\n", err)
		return subcommands.ExitFailure
	}
	defer client.close()
	if len(f.Args()) > 1 {
		fmt.Fprintf(cmd.stderr, "Unexpected arguments %v: Only one file may be uploaded at a time.\n", f.Args()[1:])
		return subcommands.ExitFailure
	} else if len(f.Args()) == 0 {
		fmt.Fprintf(cmd.stderr, "No file file specified.\nUSAGE: %s\n", cmd.Usage())
		return subcommands.ExitFailure
	}
	if cmd.name == "" {
		cmd.name = filepath.Base(f.Args()[0])
	}
	if err := client.uploadFile(ctx, f.Args()[0], cmd.name); err != nil {
		fmt.Fprintf(cmd.stderr, "Failed to upload files %s\n", err)
		return subcommands.ExitFailure
	}
	fmt.Fprintln(cmd.stdout, "Uploaded.")
	return subcommands.ExitSuccess
}

func main() {
	subcommands.Register(subcommands.HelpCommand(), "")
	subcommands.Register(subcommands.FlagsCommand(), "")
	subcommands.Register(subcommands.CommandsCommand(), "")
	subcommands.Register(&listFilesCommand{
		stderr: os.Stderr,
		stdout: os.Stdout,
	}, "")
	subcommands.Register(&removeFilesCommand{
		stderr: os.Stderr,
		stdout: os.Stdout,
	}, "")
	subcommands.Register(&uploadFileCommand{
		stderr: os.Stderr,
		stdout: os.Stdout,
	}, "")
	flag.Parse()
	ctx := context.Background()
	os.Exit(int(subcommands.Execute(ctx)))
}

# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Make sure versions of gppcio from PyPI and grpc from github are synchronized."""

import argparse
import pathlib


def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("--deps-0", required=True, type=pathlib.Path)
  parser.add_argument("--requirements-in", required=True, type=pathlib.Path)
  parser.add_argument("--requirements-txt", required=True, type=pathlib.Path)
  args = parser.parse_args()

  assert args.deps_0.exists()
  assert args.requirements_in.exists()
  assert args.requirements_txt.exists()

  return args


def main():
  args = parse_args()
  sha = "315dbe5aa9235ccc5fcb4e40e6ada4c1135d4377238bf9ea65534fa38f7c695a"
  assert f'sha256 = "{sha}"' in args.deps_0.read_text()
  assert "grpcio==1.55.0" in args.requirements_in.read_text()
  assert "grpcio==1.55.0" in args.requirements_txt.read_text()


if __name__ == "__main__":
  main()

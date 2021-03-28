"""
A simple python script to compile, generate and clean LaTeX files
"""
import argparse

from typing import Optional, List
from sys import argv as sys_argv

# ============================
# Constants
# ============================

class TexmgrConstants:
	"""
	Constants used by Texmgr
	"""
	NAME = "texmgr"
	VERSION = "0.0.1"


	# Files with name <file>.<ext> are remove by clean. With
	#   <file> such the name of the .tex file (or any tex file)
	#   <ext> an extension from this list
	CLEAN_EXTENSIONS = [
		"log", "nav", "out", "synctez.gz", "snm", "vrb", "toc", "bbl"
	]

	USE_COLOR = True # use ansi in output
	COLOR_START = "\033[33;1m" # bold orange text
	COLOR_END = "\033[38;22m" # Reset

	@classmethod
	def color(cls, string: str) -> str:
		"""Wraps the string in ansi color if USE_COLOR is True"""
		if cls.USE_COLOR:
			return "{}{}{}".format(cls.COLOR_START, string, cls.COLOR_END)
		return string

	@classmethod
	def pretty_name(cls) -> str:
		"""Display colored name if USE_COLOR is True"""
		return cls.color(cls.NAME)

# ============================
# Argument parser and main
# ============================

parser = argparse.ArgumentParser(TexmgrConstants.NAME, add_help=False,
	usage="{} [--flags] [file list]\n  see --help for details.".format(TexmgrConstants.NAME)
)
parser.add_argument("file", nargs="*", action="append")
parser.add_argument("--init", "-i", action="store_true")
parser.add_argument("--init-beamer", "-b", action="store_true")
parser.add_argument("--no-clean", "-n", action="store_true")
parser.add_argument("--clean", "-c", action="store_true")
parser.add_argument("--version", "-v", action="store_true")
parser.add_argument("--help", "-h", action="store_true")

def get_help() -> str:
	"""Returns the help string"""
	color_s = ""
	color_e = ""
	if TexmgrConstants.USE_COLOR:
		color_s = "\033[93m"
		color_e = "\033[38m"
	return """{name} version {version}
	Small utility script to compile, generate and clean LaTeX.

	Usage: {name} {s}[--flags] [file list]{e}

	Compiles all files in the file list (defaut, all *.tex files
	in current working directory). Compile three times and clean
	build files afterward

	Flags:
	  {s}--init -i{e}         create files in file list rather than compile them
	  {s}--init-beamer -b{e}  same as --init, but uses the beamer template to create files
	  {s}--no-clean -n{e}     don't remove build files after compiling
	  {s}--clean -c{e}        only clean files (removes build files)
	                          Files removed match a .tex file in the list
	                          and have the following extensions:
	                          {ext}
	  {s}--version{e}         show version number
	  {s}--help -h{e}         show this help
	""".replace("\n\t", "\n").format(
		name = TexmgrConstants.pretty_name(),
		version = TexmgrConstants.VERSION,
		s = color_s, e = color_e,
		ext = ", ".join(TexmgrConstants.CLEAN_EXTENSIONS)
	)


def main(argv: Optional[List[str]] = None):
	"""
	The main function - parses arguments and
	calls appropriate functions for each
	Arguments:
	 - argv: the argument list, default to sys.argv
	"""

	if argv is None:
		args = parser.parse_args()
	else:
		args = parser.parse_args(argv)

	# version and help
	if args.version:
		print("{} version {}".format(TexmgrConstants.pretty_name(), TexmgrConstants.VERSION))
		exit(0)
	if args.help:
		print(get_help())
		exit(0)
	print(args.file)
	print("hello world!")

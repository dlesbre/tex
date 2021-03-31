"""
A simple python script to compile, generate and clean LaTeX files
"""
import argparse

from os import system, listdir
from os.path import exists, isdir, basename, join, dirname
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
	VERSION = "0.1.1"

	# Path to templates copied on init
	TEMPLATE_DOCUMENT = join(dirname(__file__), "../templates/document.tex")
	TEMPLATE_BEAMER = join(dirname(__file__), "../templates/beamer.tex")

	OPEN_EDITOR_COMMAND = 'codium {file_parent} && codium {file}'
	OPEN_PDF_COMMAND  = 'okular {pdf} &'

	# Files with name <file>.<ext> are remove by clean. With
	#   <file> such the name of the .tex file (or any tex file)
	#   <ext> an extension from this list
	CLEAN_EXTENSIONS = [
		"aux", "log", "nav", "out", "synctez.gz", "snm", "vrb", "toc", "bbl"
	]

	TEX_COMMAND = (
		'texfot pdflatex -file-line-error  -interaction=nonstopmode --enable-write18 '
		'"{file}" | grep --color=auto -E "Warning|Missing|Undefined|Emergency|Fatal|$"'
	)

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

	@classmethod
	def command_format(cls, command: str, file: str) -> str:
		"""Formats a command: replaces
		- {file} with given file
		- {file_parent} with file basedir
		- {pdf} with the generated pdf file
		"""
		parent = dirname(file)
		if parent == "":
			parent = "."
		pdf = file
		if pdf.endswith(".tex"):
			pdf = pdf[:-4]
		pdf += ".pdf"
		return command.format(
			file = file,
			file_parent = parent,
			pdf = pdf,
		)


# ============================
# Functions
# ============================


def run_command(command: str, verbose = False, dry_run = False) -> int:
	"""Runs a command and returns it's exit status"""
	if verbose or dry_run:
		print(command)
	if dry_run:
		return 0
	return system(command)

def clean(file: str, verbose = False, dry_run = False) -> int:
	"""Cleans all build files related to file"""
	if file.endswith(".tex"):
		file = file[:-4]
	command = 'rm -f "{}.{}"'.format(
		file, '" "{}.'.format(file).join(TexmgrConstants.CLEAN_EXTENSIONS)
	)
	return run_command(command, verbose, dry_run)

def init(file: str, template: str, verbose = False, dry_run = False) -> int:
	"""Copies template to file"""
	if isdir(file):
		file = join(file, basename(template))
	if exists(file):
		inp = input(
			"File '{}' aldready exists, overwrite with new LaTeX file (y/n) ? ".format(file)
		)
		if not inp or inp.lower()[0] != "y":
			return 0
	if not file.endswith(".tex"):
		file = file + ".tex"
	command = 'cp "{}" "{}"'.format(template, file)
	return run_command(command, verbose, dry_run)

def init_wrapper(
		file_list: str, template: str, open_tex: bool,
		verbose = False, dry_run = False
	) -> int:
	"""Initializes all files and checks if editor openning is needed"""
	if not file_list:
		file_list = ["."]
	for file in file_list:
		code = init(file, template, verbose, dry_run)
		if code != 0:
			print("Error when creating file '{}'".format(file))
			exit(code)
		if open_tex:
			command = TexmgrConstants.command_format(TexmgrConstants.OPEN_EDITOR_COMMAND, file)
			code = run_command(command, verbose, dry_run)
			if code != 0:
				print("Error when opening editor for '{}'".format(file))
				exit(code)
	exit(0)

def compile(file: str, rounds: int, verbose = False, dry_run = False) -> int:
	"""compiles the given file"""
	command = TexmgrConstants.command_format(TexmgrConstants.TEX_COMMAND, file)
	color_s = TexmgrConstants.COLOR_START if TexmgrConstants.USE_COLOR else ""
	color_e = TexmgrConstants.COLOR_END if TexmgrConstants.USE_COLOR else ""
	for ii in range(rounds):
		if not dry_run:
			print("{}================== {}: compiling '{}' (round {} of {}) =================={}".format(
				color_s, TexmgrConstants.NAME, file, ii+1, rounds, color_e
			))
		code = run_command(command, verbose, dry_run)
		if code != 0:
			return code
	return 0

# ============================
# Argument parser and main
# ============================


parser = argparse.ArgumentParser(TexmgrConstants.NAME, add_help=False,
	usage="{} [--flags] [file list]\n  see --help for details.".format(TexmgrConstants.NAME)
)
parser.add_argument("file", nargs="*", action="append")
parser.add_argument("--init", "-i", action="store_true")
parser.add_argument("--init-beamer", "-b", action="store_true")
parser.add_argument("--open-tex", "-t", action="store_true")
parser.add_argument("--open-pdf", "-p", action="store_true")
parser.add_argument("--rounds", "-r", type=int, default=3)
parser.add_argument("--no-clean", "-n", action="store_true")
parser.add_argument("--clean", "-c", action="store_true")
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--dry-run", "-d", action="store_true")
parser.add_argument("--version", action="store_true")
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
	  {s}-n --no-clean{e}     don't remove build files after compiling
	  {s}-r --rounds{e} <int> number of compile rounds, default = 3

	  {s}-i --init{e}         doesn't compile, creates files in file list
	  {s}-b --init-beamer{e}  same as --init, but uses the beamer template to create files
	  {s}-t --open-tex{e}     doesn't compile, opens tex files in editor (can run with -i/-b)
	  {s}-p --open-pdf{e}     compiles and opens PDF files in viewer

	  {s}-c --clean{e}        doesn't compile, removes build files
	  {s}{e}                  Files removed match a .tex file in the list
	  {s}{e}                  and have the following extensions:
	  {s}{e}                    {ext}

	  {s}-v --verbose{e}      print the commands called
	  {s}-d --dry-run{e}      print the commands but don't run them
	  {s}--version{e}         show version number
	  {s}-h --help{e}         show this help
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

	file_list = args.file[0]

	## initizations
	if args.init:
		init_wrapper(
			file_list, TexmgrConstants.TEMPLATE_DOCUMENT, args.open_tex, args.verbose, args.dry_run
		)
	if args.init_beamer:
		init_wrapper(
			file_list, TexmgrConstants.TEMPLATE_BEAMER, args.open_tex, args.verbose, args.dry_run
		)

	if not file_list:
		## Generate file list based on all tex files in CWD
		file_list = [file for file in listdir() if file.endswith(".tex")]

	if args.clean:
		for file in file_list:
			code = clean(file, args.verbose, args.dry_run)
			if code != 0:
				print("Error removing build files for '{}'".format(file))
				exit(code)
		exit(0)

	if args.open_tex:
		for file in file_list:
			command = TexmgrConstants.command_format(TexmgrConstants.OPEN_EDITOR_COMMAND, file)
			code = run_command(command, args.verbose, args.dry_run)
			if code != 0:
				print("Error when opening '{}' in editor".format(file))
				exit(code)
		exit(0)

	for file in file_list:
		code = compile(file, args.rounds, args.verbose, args.dry_run)
		if code != 0:
			print("Error when compiling '{}'".format(file))
			exit(code)
		if not args.no_clean:
			code = clean(file, args.verbose, args.dry_run)
			if code != 0:
				print("Error cleaning build files for '{}'".format(file))
				exit(code)

	if args.open_pdf:
		for file in file_list:
			command = TexmgrConstants.command_format(TexmgrConstants.OPEN_PDF_COMMAND, file)
			code = run_command(command, args.verbose, args.dry_run)
			if code != 0:
				print("Error when opening '{}' in viewer".format(file))
				exit(code)

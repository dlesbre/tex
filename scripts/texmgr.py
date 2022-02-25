"""
A simple python script to compile, generate and clean LaTeX files

Useful contents:
 - main(List[str])      main function, exits when done
 - get_help() -> str    list of command line arguments for main
 - Constants      class containing many useful constants
                        like the commands used and the tex compile sequence
"""
import argparse
import subprocess

from os import listdir, stat
from os.path import exists, isdir, basename, join, dirname
from time import sleep
from typing import Dict, Optional, List, Tuple
from sys import argv as sys_argv


# ============================
# Constants
# ============================

Command = str
CompletedProcess = subprocess.CompletedProcess

class Constants:
	"""
	Constants used by Texmgr
	"""
	NAME = "texmgr"
	VERSION = "0.1.2"

	# Path to templates copied on init
	TEMPLATE_DOCUMENT = join(dirname(__file__), "../templates/document.tex")
	TEMPLATE_BEAMER = join(dirname(__file__), "../templates/beamer.tex")

	# Files with name <file>.<ext> are removed by clean. With
	#   <file> the name of the .tex file (or any tex file)
	#   <ext> an extension from this list
	CLEAN_EXTENSIONS = [
		"aux", "bak", "bbl", "blg", "fdb_latexmk", "fls", "log", "nav",
		"out", "snm", "synctex.gz", "synctez.gz", "toc", "vrb", "vtc"
	]
	# Full file/folder names cleaned
	CLEAN_FOLDERS = [
		"_minted-{file}",
	]

	# Command called when running tex
	TEX_COMMAND : Command = (
		'texfot --tee=/dev/null --quiet --ignore="This is pdfTeX, Version" pdflatex -file-line-error -interaction=nonstopmode --enable-write18 '
		'"{tex_file}" | grep --color=always -E "Warning|Missing|Undefined|Emergency|Fatal|$"'
	)
	# Command called when running bibtex, ignores errors
	BIBTEX_COMMAND : Command = 'bibtex "{file}" || true'
	OPEN_EDITOR_COMMAND : Command = 'codium {file_parent} && codium {tex_file}'
	OPEN_PDF_COMMAND : Command  = 'okular {pdf_file} &'

	COMPILE_SEQUENCE : List[Tuple[Command, str]] = [
		(TEX_COMMAND, 'compiling "{tex_file}"'),
		(BIBTEX_COMMAND, 'running bibtex on "{file}"'),
		(TEX_COMMAND, 'compiling "{tex_file}"'),
		(TEX_COMMAND, 'compiling "{tex_file}"'),
	]

	USE_COLOR = True # use ansi in output
	COLOR_START = "\033[33;1m" # bold orange text
	COLOR_ERROR = "\033[31m" # red text
	COLOR_END = "\033[38;22m" # Reset

	COMMAND_TIMEOUT = 10.0 # in seconds
	POLLING_TIME = 1.0 # in seconds

	PRINT_INFO = True # unless silent is set
	PRINT_COMMANDS = False # unless verbose is set

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

	@staticmethod
	def with_tex_ext(file: str) -> str:
		"""Ensures file endwith '.tex'"""
		if not file.endswith(".tex"):
			file += '.tex'
		return file

	@classmethod
	def command_format(cls, command: str, file: str) -> str:
		"""Formats a command: replaces
		- {tex_file} with given file (including path, adds .tex if absent)
		- {file} with the filename (same as tex_file without .tex extension)
		- {file_parent} with file basedir (or '.' if empty)
		- {pdf_file} with the generated pdf file
		"""
		# ensure file has the .tex extension
		file = cls.with_tex_ext(file)
		filename = file[:-4]
		parent = dirname(file)
		if parent == "":
			parent = "."
		pdf = file[:-4] + ".pdf"
		return command.format(
			tex_file = file,
			file = filename,
			file_parent = parent,
			pdf_file = pdf,
		)

	@classmethod
	def print_error(cls, error_msg:str) -> None:
		"""Prints the error message (with color is cls.USE_COLOR)"""
		color_start = ""
		color_error = ""
		color_end = ""
		if cls.USE_COLOR:
			color_start = cls.COLOR_START
			color_error = cls.COLOR_ERROR
			color_end = cls.COLOR_END
		print("{}{}:{} ERROR:{} {}".format(
			color_start, cls.NAME, color_error, color_end, error_msg
		))

	@classmethod
	def print_info(cls, msg:str) -> None:
		if cls.PRINT_INFO:
			print(cls.color("{}: {}".format(cls.NAME, msg)))


def check_error(process:CompletedProcess, error_msg:str) -> bool:
	"""Check process return code
	If non-zero, display's an error message and process stderr/stdout
	returns False if all is fine, True otherwise"""
	if process.returncode != 0:
		Constants.print_error(error_msg)
		if process.stderr:
			print(process.stderr.decode())
		if process.stdout:
			print(process.stdout.decode())
		return True
	return False

# ============================
# Functions
# ============================

def get_mtime(filepath: str) -> float:
	"""Return the modified time of a file"""
	return stat(filepath).st_mtime


def run_command(command: str, dry_run = False) -> CompletedProcess:
	"""Formats and runs a command and returns it's exit status"""
	if Constants.PRINT_COMMANDS:
		print("{}: {}".format(Constants.pretty_name(), command))
	if dry_run:
		return CompletedProcess("", 0, stderr=bytes(), stdout=bytes())
	try:
		return subprocess.run(
			command, shell=True,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			timeout=Constants.COMMAND_TIMEOUT,
		)
	except subprocess.TimeoutExpired:
		Constants.print_error("Command timeout")
		return CompletedProcess("", 1, stderr=bytes(), stdout=bytes())

def format_and_run_command(command: str, file: str, dry_run = False) -> CompletedProcess:
	"""Formats and runs a command and returns it's exit status"""
	command = Constants.command_format(command, file)
	return run_command(command, dry_run)

def clean(file: str, dry_run = False) -> None:
	"""Cleans all build files related to file"""
	if file.endswith(".tex"):
		file = file[:-4]
	Constants.print_info('Cleaning build files for "{}"'.format(file))
	command = 'rm -f "{}.{}"'.format(
		file, '" "{}.'.format(file).join(Constants.CLEAN_EXTENSIONS)
	)
	process = run_command(command, dry_run)
	if check_error(process, 'when cleaning build files for "{}"'.format(file)):
		return
	command = 'rm -rf "{}"'.format(
		'" "'.join(Constants.CLEAN_FOLDERS)
	)
	process = format_and_run_command(command, file, dry_run)
	check_error(process, 'when cleaning build files for "{}"'.format(file))


def make_file_name(file: str, template: str) -> str:
	"""Make a valid tex file name
	- if file is a directory, adds template basename
	- if file doesn't end in .tex, adds it"""
	if isdir(file):
		file = join(file, basename(template))
	return Constants.with_tex_ext(file)

def init(file: str, template: str, dry_run = False) -> None:
	"""Copies template to file"""
	if exists(file):
		inp = input(
			'File "{}" aldready exists, overwrite with new LaTeX file (y/n) ? '.format(file)
		)
		if not inp or inp.lower()[0] != "y":
			exit(0)
	command = 'cp "{}" "{}"'.format(template, file)
	Constants.print_info('Creating "{}"'.format(file))
	process = run_command(command, dry_run)
	if check_error(process, 'when initializing file "{}"'.format(file)):
		exit(1)

def init_wrapper(file_list: List[str], template: str, open_tex: bool, dry_run = False) -> int:
	"""Initializes all files and checks if editor opening is needed"""
	if not file_list:
		file_list = ["."]
	for file in file_list:
		filename = make_file_name(file, template)
		init(filename, template, dry_run)
		if open_tex:
			process = format_and_run_command(Constants.OPEN_EDITOR_COMMAND, filename, dry_run)
			if check_error(process, 'when opening editor for "{}"'.format(filename)):
				exit(1)
	exit(0)

def error_tex_in_output(output: str) -> bool:
	"""parses tex output looking for fatal errors"""
	return ("Fatal error" in output) or ("no output PDF" in output)

def compile(file: str, dry_run = False) -> None:
	"""compiles the given file"""
	command = Constants.command_format(Constants.TEX_COMMAND, file)
	total = len(Constants.COMPILE_SEQUENCE)
	for ii, (command, doc) in enumerate(Constants.COMPILE_SEQUENCE):
		if not dry_run:
			Constants.print_info(("step {}/{} - {}").format(
				ii+1, total, Constants.command_format(doc, file),
			))
		process = format_and_run_command(command, file, dry_run)
		if error_tex_in_output(process.stdout.decode()):
			process.returncode = 1
		if check_error(process, 'when compiling "{}"'.format(file)):
			return
	if not dry_run:
		print(process.stdout.decode().strip())

def compile_and_clean(file:str, args) -> None:
	"""Calls compile with the correct argument and cleans if args specifies it"""
	compile(file, args.dry_run)
	if not args.no_clean:
		clean(file, args.dry_run)

# ============================
# Argument parser and main
# ============================


parser = argparse.ArgumentParser(Constants.NAME, add_help=False,
	usage="{} [--flags] [file list]\n  see --help for details.".format(Constants.NAME)
)
parser.add_argument("file", nargs="*", action="append")
parser.add_argument("--init", "-i", action="store_true")
parser.add_argument("--init-beamer", "-b", action="store_true")
parser.add_argument("--open-tex", "-t", action="store_true")
parser.add_argument("--open-pdf", "-p", action="store_true")
parser.add_argument("--no-clean", "-n", action="store_true")
parser.add_argument("--clean", "-c", action="store_true")
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--silent", "-s", action="store_false")
parser.add_argument("--dry-run", "-d", action="store_true")
parser.add_argument("--version", action="store_true")
parser.add_argument("--help", "-h", action="store_true")
parser.add_argument("--watch", "-w", action="store_true")

def get_help() -> str:
	"""Returns the help string"""
	color_s = ""
	color_e = ""
	if Constants.USE_COLOR:
		color_s = "\033[33m"
		color_e = "\033[38m"
	return """{name} version {version}
	Small utility script to compile, generate and clean LaTeX.

	Usage: {name} {s}[--flags] [file list]{e}

	Compiles all files in the file list (default, all *.tex files
	in current working directory).
	Compiles once, runs bibtex, then compiles twice.

	Flags:
	  {s}-n --no-clean{e}     don't remove build files after compiling

	  {s}-i --init{e}         doesn't compile, creates files in file list
	  {s}-b --init-beamer{e}  same as --init, but uses the beamer template to create files
	  {s}-t --open-tex{e}     doesn't compile, opens tex files in editor (can run with -i/-b)
	  {s}-p --open-pdf{e}     compiles and opens PDF files in viewer

	  {s}-w --watch{e}        watches the tex file and recompiles when it is changed

	  {s}-c --clean{e}        doesn't compile, removes build files
	  {s}{e}                  Files removed match a .tex file in the list
	  {s}{e}                  and have the following extensions:
	  {s}{e}                    {ext}

	  {s}-v --verbose{e}      print the commands called
	  {s}-s --silent{e}       don't show info messages (keeps tex output and error messages)
	  {s}-d --dry-run{e}      print the commands but don't run them
	  {s}--version{e}         show version number
	  {s}-h --help{e}         show this help
	""".replace("\n\t", "\n").format(
		name = Constants.pretty_name(),
		version = Constants.VERSION,
		s = color_s, e = color_e,
		ext = ", ".join(Constants.CLEAN_EXTENSIONS)
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
		print("{} version {}".format(Constants.pretty_name(), Constants.VERSION))
		exit(0)
	if args.help:
		print(get_help())
		exit(0)

	Constants.PRINT_COMMANDS = args.verbose or args.dry_run
	Constants.PRINT_INFO = args.silent

	file_list = args.file[0]

	## initizations
	if args.init:
		init_wrapper(
			file_list, Constants.TEMPLATE_DOCUMENT, args.open_tex, args.dry_run
		)
	if args.init_beamer:
		init_wrapper(
			file_list, Constants.TEMPLATE_BEAMER, args.open_tex, args.dry_run
		)

	if not file_list:
		## Generate file list based on all tex files in CWD
		file_list = [file for file in listdir() if file.endswith(".tex")]

	if args.clean:
		for file in file_list:
			clean(file, args.dry_run)
		exit(0)

	if args.open_tex:
		for file in file_list:
			process = format_and_run_command(Constants.OPEN_EDITOR_COMMAND, file, args.dry_run)
			check_error(process, 'when opening editor for "{}"'.format(file))
		exit(0)

	for file in file_list:
		compile_and_clean(file, args)

	if args.open_pdf:
		for file in file_list:
			process = format_and_run_command(Constants.OPEN_PDF_COMMAND, file, args.dry_run)
			check_error(process, 'when opening pdf file "{}"'.format(file))

	if args.watch:
		times : Dict[str, float] = {}
		file_list = [Constants.with_tex_ext(file) for file in file_list]
		for file in file_list:
			Constants.print_info('watching "{}"'.format(file))
			times[file] = get_mtime(file)

		try:
			while True:
				sleep(Constants.POLLING_TIME)
				for file in file_list:
					time = get_mtime(file)
					if time > times[file]:
						compile_and_clean(file, args)
						times[file] = time
		except KeyboardInterrupt:
			Constants.print_info("stop watching files")

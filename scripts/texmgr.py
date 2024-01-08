"""
A simple python script to compile, generate and clean LaTeX files

Useful contents:
 - main(List[str])      main function, exits when done
 - get_help() -> str    list of command line arguments for main
 - Constants            class containing many useful constants
                        like the commands used and the tex compile sequence
"""
import argparse
import subprocess

from os import getpgid, listdir, stat, killpg
from os.path import exists, isdir, basename, join, dirname
from re import findall
from time import sleep
from typing import Dict, Optional, List, Tuple, Set
from signal import SIGTERM


# ============================
# Constants
# ============================

Command = str


class CompletedProcess:
    """Information about a completed process"""

    returncode: int
    stdout: str
    stderr: str

    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class Constants:
    """
    Constants used by Texmgr
    """

    NAME = "texmgr"
    VERSION = "0.1.3"

    # Path to templates copied on init
    TEMPLATE_DOCUMENT = join(dirname(__file__), "../templates/document.tex")
    TEMPLATE_BEAMER = join(dirname(__file__), "../templates/beamer.tex")

    # Files with name <file>.<ext> are removed by clean. With
    #   <file> the name of the .tex file (or any tex file)
    #   <ext> an extension from this list
    CLEAN_EXTENSIONS = [
        "aux",
        "bak",
        "bbl",
        "blg",
        "fdb_latexmk",
        "func0.gnuplot",
        "func0.table",
        "fls",
        "log",
        "lof",
        "lot",
        "nav",
        "out",
        "snm",
        "synctex.gz",
        "synctez.gz",
        "toc",
        "vrb",
        "vtc",
    ]
    # Full file/folder names cleaned
    CLEAN_FOLDERS = [
        "_minted-{file}",
    ]

    # Command called when running tex
    TEX_COMMAND: Command = (
        'TEXINPUTS=./packages//:$TEXINPUTS texfot --tee=/dev/null --quiet --ignore="This is pdfTeX, Version" '
        "pdflatex -file-line-error -interaction=nonstopmode --enable-write18 --synctex=1 "
        '"{tex_file}" | grep --color=always -E "Warning|Missing|Undefined|Emergency|Fatal|$"'
    )
    # Command called when running bibtex, ignores errors
    BIBTEX_COMMAND: Command = 'bibtex "{file}" || true'
    OPEN_EDITOR_COMMAND: Command = "codium {file_parent} && codium {tex_file}"
    OPEN_PDF_COMMAND: Command = "okular {pdf_file} &"

    COMPILE_SEQUENCE: List[Tuple[Command, str]] = [
        (TEX_COMMAND, 'compiling "{tex_file}"'),
        (BIBTEX_COMMAND, 'running bibtex on "{file}"'),
        (TEX_COMMAND, 'compiling "{tex_file}"'),
        (TEX_COMMAND, 'compiling "{tex_file}"'),
    ]
    UPDATE_SEQUENCE: List[Tuple[Command, str]] = [
        (TEX_COMMAND, 'compiling "{tex_file}"'),
    ]

    USE_COLOR = True  # use ansi in output
    COLOR_START = "\033[33;1m"  # bold orange text
    COLOR_ERROR = "\033[31m"  # red text
    COLOR_END = "\033[38;22m"  # Reset

    COMMAND_TIMEOUT = 10.0  # in seconds
    POLLING_TIME = 1.0  # in seconds

    PRINT_INFO = True  # unless silent is set
    PRINT_COMMANDS = False  # unless verbose is set

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
            file += ".tex"
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
            tex_file=file,
            file=filename,
            file_parent=parent,
            pdf_file=pdf,
        )

    @classmethod
    def print_error(cls, error_msg: str) -> None:
        """Prints the error message (with color is cls.USE_COLOR)"""
        color_start = ""
        color_error = ""
        color_end = ""
        if cls.USE_COLOR:
            color_start = cls.COLOR_START
            color_error = cls.COLOR_ERROR
            color_end = cls.COLOR_END
        print(
            "{}{}:{} ERROR:{} {}".format(
                color_start, cls.NAME, color_error, color_end, error_msg
            )
        )

    @classmethod
    def print_info(cls, msg: str) -> None:
        if cls.PRINT_INFO:
            print(cls.color("{}: {}".format(cls.NAME, msg)))


def check_error(process: CompletedProcess, error_msg: str) -> bool:
    """Check process return code
    If non-zero, display's an error message and process stderr/stdout
    returns False if all is fine, True otherwise"""
    if process.returncode != 0:
        Constants.print_error(error_msg)
        if process.stderr:
            print(process.stderr)
        if process.stdout:
            print(process.stdout)
        return True
    return False


# ============================
# Functions
# ============================


def get_mtime(filepath: str) -> float:
    """Return the modified time of a file"""
    return stat(filepath).st_mtime


def run_command(command: str, dry_run=False) -> CompletedProcess:
    """Formats and runs a command and returns it's exit status"""
    if Constants.PRINT_COMMANDS:
        print("{} {}".format(Constants.color(Constants.NAME + ":"), command))
    if dry_run:
        return CompletedProcess(0, "", "")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        start_new_session=True,
    )
    try:
        output, errors = process.communicate(timeout=Constants.COMMAND_TIMEOUT)
        returncode = process.returncode
    except subprocess.TimeoutExpired:
        Constants.print_error("Command timeout")
        # kill process and all children
        killpg(getpgid(process.pid), SIGTERM)
        output, errors = process.communicate(timeout=Constants.COMMAND_TIMEOUT)
        returncode = -1
    return CompletedProcess(returncode, stdout=output.decode(), stderr=errors.decode())


def format_and_run_command(command: str, file: str, dry_run=False) -> CompletedProcess:
    """Formats and runs a command and returns it's exit status"""
    command = Constants.command_format(command, file)
    return run_command(command, dry_run)


def clean(file: str, dry_run=False) -> None:
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
    command = 'rm -rf "{}"'.format('" "'.join(Constants.CLEAN_FOLDERS))
    process = format_and_run_command(command, file, dry_run)
    check_error(process, 'when cleaning build files for "{}"'.format(file))


def make_file_name(file: str, template: str) -> str:
    """Make a valid tex file name
    - if file is a directory, adds template basename
    - if file doesn't end in .tex, adds it"""
    if isdir(file):
        file = join(file, basename(template))
    return Constants.with_tex_ext(file)


def init(file: str, template: str, dry_run=False) -> None:
    """Copies template to file"""
    if exists(file):
        inp = input(
            'File "{}" aldready exists, overwrite with new LaTeX file (y/n) ? '.format(
                file
            )
        )
        if not inp or inp.lower()[0] != "y":
            exit(0)
    command = 'cp "{}" "{}"'.format(template, file)
    Constants.print_info('Creating "{}"'.format(file))
    process = run_command(command, dry_run)
    if check_error(process, 'when initializing file "{}"'.format(file)):
        exit(1)


def init_wrapper(
    file_list: List[str], template: str, open_tex: bool, dry_run=False
) -> int:
    """Initializes all files and checks if editor opening is needed"""
    if not file_list:
        file_list = ["."]
    for file in file_list:
        filename = make_file_name(file, template)
        init(filename, template, dry_run)
        if open_tex:
            process = format_and_run_command(
                Constants.OPEN_EDITOR_COMMAND, filename, dry_run
            )
            if check_error(process, 'when opening editor for "{}"'.format(filename)):
                exit(1)
    exit(0)


def error_tex_in_output(output: str) -> bool:
    """parses tex output looking for fatal errors"""
    return ("Fatal error" in output) or ("no output PDF" in output)


def print_clean(msg: str) -> None:
    """print msg if not empty (avoids empty lines)"""
    if msg != "" and not msg.isspace():
        msg = msg.strip()
    hbox = 0
    vbox = 0
    img = 0
    to_print = []
    for line in msg.split("\n"):
        if line.startswith("Overfull \\hbox") or line.startswith("Underfull \\hbox"):
            hbox += 1
        elif line.startswith("Overfull \\vbox") or line.startswith("Underfull \\vbox"):
            vbox += 1
        elif line.startswith("Class acmart") and "A possible image without description on input line" in line:
            img += 1
        else:
            to_print.append(line)
    if hbox or vbox:
        to_print.append(f"{hbox} under/overfull hboxes; {vbox} under/overfull vboxes; {img} images without description")
    print("\n".join(to_print))


def compile(file: str, dry_run=False, sequence=Constants.COMPILE_SEQUENCE) -> None:
    """compiles the given file"""
    command = Constants.command_format(Constants.TEX_COMMAND, file)
    total = len(sequence)
    for ii, (command, doc) in enumerate(sequence):
        if not dry_run:
            Constants.print_info(
                ("step {}/{} - {}").format(
                    ii + 1,
                    total,
                    Constants.command_format(doc, file),
                )
            )
        process = format_and_run_command(command, file, dry_run)
        if error_tex_in_output(process.stdout):
            process.returncode = 1
        if check_error(process, 'when compiling "{}"'.format(file)):
            break
    if not dry_run:
        print_clean(process.stdout)
        print_clean(process.stderr)


def compile_and_clean(file: str, args, sequence=Constants.COMPILE_SEQUENCE) -> None:
    """Calls compile with the correct argument and cleans if args specifies it"""
    compile(file, args.dry_run, sequence)
    if not args.no_clean:
        clean(file, args.dry_run)


def find_dependencies(filepath: str, seen: Set[str] = set()) -> Set[str]:
    """Finds dependencies of a main LaTeX file
    looking for \\input{some other file}"""
    try:
        with open(filepath, "r") as file:
            contents = file.read()
    except IOError as err:
        Constants.print_error(
            f"When searching for dependencies: could not read '{filepath}' : {err}"
        )
        contents = ""
    # Remove comments (fails on escaped % but unlikely)
    contents = "\n".join(line.split("%")[0] for line in contents.split("\n"))
    patterns = findall(r"\\input{([^\\\{\}]*)}", contents)
    tex_files = [Constants.with_tex_ext(pat) for pat in patterns]
    seen.add(filepath)
    for tex in tex_files:
        seen = find_dependencies(tex, seen)
    return seen


class FileWatcher:
    times: Dict[str, float] = dict()
    files: List[str] = []

    @classmethod
    def update(cls) -> List[str]:
        """Get times on all files, returns list of outdated filed"""
        new_times: Dict[str, float] = dict()
        to_update = set()
        for file in cls.files:
            dependencies = find_dependencies(file)
            for tex in dependencies:
                try:
                    time = new_times[tex] if tex in new_times else get_mtime(tex)
                    new_times[tex] = time
                    if tex not in cls.times or time > cls.times[tex]:
                        to_update.add(file)
                except IOError as err:
                    Constants.print_error(
                        f"When getting modified times for {file} : {err}"
                    )
        cls.times = new_times
        return list(sorted(to_update))


# ============================
# Argument parser and main
# ============================


parser = argparse.ArgumentParser(
    Constants.NAME,
    add_help=False,
    usage="{} [--flags] [file list]\n  see --help for details.".format(Constants.NAME),
)
parser.add_argument("file", nargs="*", action="append")

parser.add_argument("--no-clean", "-n", action="store_true")

parser.add_argument("--init", "-i", action="store_true")
parser.add_argument("--init-beamer", "-b", action="store_true")
parser.add_argument("--open-tex", "-t", action="store_true")
parser.add_argument("--open-pdf", "-p", action="store_true")

parser.add_argument("--watch", "-w", action="store_true")
parser.add_argument("--clean-last", "-l", action="store_true")
parser.add_argument("--find-deps", "-f", action="store_true")

parser.add_argument("--clean", "-c", action="store_true")

parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--silent", "-s", action="store_false")
parser.add_argument("--dry-run", "-d", action="store_true")
parser.add_argument("--version", action="store_true")
parser.add_argument("--help", "-h", action="store_true")


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
          {s}-l --clean-last{e}   only clean build files when watcher is stopped
          {s}-f --find-deps{e}    print dependencies (\\input{{...}}) of a LaTeX file

          {s}-c --clean{e}        doesn't compile, removes build files
          {s}{e}                  Files removed match a .tex file in the list
          {s}{e}                  and have the following extensions:
          {s}{e}                    {ext}

          {s}-v --verbose{e}      print the commands called
          {s}-s --silent{e}       don't show info messages (keeps tex output and error messages)
          {s}-d --dry-run{e}      print the commands but don't run them
          {s}--version{e}         show version number
          {s}-h --help{e}         show this help
        """.replace(
        "\n        ", "\n"
    ).format(
        name=Constants.pretty_name(),
        version=Constants.VERSION,
        s=color_s,
        e=color_e,
        ext=", ".join(Constants.CLEAN_EXTENSIONS),
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

    args.no_clean = args.no_clean or args.clean_last
    args.watch = args.watch or args.clean_last
    file_list = args.file[0]

    # initizations
    if args.init:
        init_wrapper(
            file_list, Constants.TEMPLATE_DOCUMENT, args.open_tex, args.dry_run
        )
    if args.init_beamer:
        init_wrapper(file_list, Constants.TEMPLATE_BEAMER, args.open_tex, args.dry_run)

    if not file_list:
        # Generate file list based on all tex files in CWD
        file_list = [file for file in listdir() if file.endswith(".tex")]

    if args.clean:
        for file in file_list:
            clean(file, args.dry_run)
        exit(0)

    if args.open_tex:
        for file in file_list:
            process = format_and_run_command(
                Constants.OPEN_EDITOR_COMMAND, file, args.dry_run
            )
            check_error(process, 'when opening editor for "{}"'.format(file))
        exit(0)

    if args.find_deps:
        for file in file_list:
            tex = Constants.with_tex_ext(file)
            Constants.print_info(f"Dependencies for {file}:")
            dependencies = find_dependencies(tex)
            print("\n".join(sorted(dependencies)))
        exit(0)

    for file in file_list:
        compile_and_clean(file, args)

    if args.open_pdf:
        for file in file_list:
            process = format_and_run_command(
                Constants.OPEN_PDF_COMMAND, file, args.dry_run
            )
            check_error(process, 'when opening pdf file "{}"'.format(file))

    if args.watch:
        FileWatcher.files = [Constants.with_tex_ext(file) for file in file_list]
        for file in FileWatcher.files:
            Constants.print_info('watching "{}" and dependencies.'.format(file))
        FileWatcher.update()
        try:
            while True:
                sleep(Constants.POLLING_TIME)
                for file in FileWatcher.update():
                    compile(file, args.dry_run, sequence=Constants.UPDATE_SEQUENCE)
        except KeyboardInterrupt:
            Constants.print_info("stop watching files")
            if args.clean_last and not args.clean:
                for file in file_list:
                    clean(file, args.dry_run)

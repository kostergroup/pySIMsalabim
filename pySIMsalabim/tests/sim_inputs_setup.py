"""Prepare the SIMsalabim input files used by the pySIMsalabim tests.

The tests use their own input files, stored in ``sim_inputs/default/{SimSS,ZimT}`` and named
``*_test.txt`` so that they never overwrite the user's own files in the SIMsalabim folder.

``prepare_test_inputs()``:
  1. compares the version of every ``simulation_setup*.txt`` in sim_inputs (and of the layer files
     it references) with the SIMsalabim version (``version = 'X.YY'`` in simss.pas / zimt.pas);
  2. on a mismatch, compiles SIMsalabim's Updater (Tools/Updater/Updater.pas) if needed, places a
     temporary copy next to the input files and runs it *interactively* (the user answers its questions),
     converting them *in place* in sim_inputs
     (the converted files show up in ``git status`` and can be committed as the new baseline);
  3. copies the input files into SIMsalabim/SimSS and SIMsalabim/ZimT, where the tests run.

``cleanup_test_inputs()`` deletes the copied files again, plus the Block.txt created by the
contactless-device tests (trPL) if it did not exist before.

Both are called by conftest.py (pytest session start/finish), by the ``__main__`` block of
each test file when it is run directly, and by the example notebooks in Notebooks/.
The notebooks call ``prepare_test_inputs(convert=False)``: a Jupyter kernel cannot give the
interactive Updater a terminal, so on a version mismatch they stop and ask the user to convert the
files from a terminal with

    python pySIMsalabim/tests/sim_inputs_setup.py

which only checks/converts the files in sim_inputs (nothing is copied).
"""

import contextlib
import glob
import os
import re
import shutil
import subprocess
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_INPUTS_DIR = os.path.join(TESTS_DIR, 'sim_inputs', 'default')
SIMSALABIM_DIR = os.path.abspath(os.path.join(TESTS_DIR, '..', '..', 'SIMsalabim'))
UPDATER_DIR = os.path.join(SIMSALABIM_DIR, 'Tools', 'Updater')

IS_WINDOWS = os.name == 'nt'
EXE_EXT = '.exe' if IS_WINDOWS else ''

# Program folder in SIMsalabim -> name of its executable / source file
PROGRAMS = {'SimSS': 'simss', 'ZimT': 'zimt'}

# Files created in SIMsalabim by the tests themselves, removed at cleanup only if they did not exist before
GENERATED_FILES = [os.path.join('ZimT', 'Block.txt')]

_FILE_VERSION_RE = re.compile(r'^\*\*\s*version:\s*(\d+\.\d+)', re.IGNORECASE | re.MULTILINE)
_SOURCE_VERSION_RE = re.compile(r"^\s*version\s*=\s*'(\d+\.\d+)'", re.IGNORECASE | re.MULTILINE)
_LAYER_RE = re.compile(r'^l\d+\s*=\s*(\S+)', re.MULTILINE)

# State shared between prepare_test_inputs() and cleanup_test_inputs()
_copied_files = []
_generated_to_remove = []


class TestInputsError(RuntimeError):
    """Raised when the test input files cannot be prepared."""


######### Version handling #########################################################################

def get_simsalabim_version(program_dir):
    """Return the version string (e.g. '5.37') declared in SIMsalabim's <prog>.pas source."""
    source = os.path.join(SIMSALABIM_DIR, program_dir, PROGRAMS[program_dir] + '.pas')
    if not os.path.isfile(source):
        raise TestInputsError(f'SIMsalabim source not found: {source}. Install SIMsalabim first '
                              '(see pySIMsalabim.install.get_SIMsalabim.install_SIMsalabim).')
    with open(source, encoding='utf-8', errors='replace') as fp:
        match = _SOURCE_VERSION_RE.search(fp.read())
    if match is None:
        raise TestInputsError(f'Could not find the version number in {source}.')
    return match.group(1)


def get_input_versions(input_dir, setup_name):
    """Return {file name: version} for a simulation setup file and every layer file it references."""
    setup = os.path.join(input_dir, setup_name)
    with open(setup, encoding='utf-8') as fp:
        files = [setup_name] + _LAYER_RE.findall(fp.read())

    versions = {}
    for name in dict.fromkeys(files):  # keep order, drop duplicates
        path = os.path.join(input_dir, name)
        if not os.path.isfile(path):
            raise TestInputsError(f'Test input file {path} (referenced by {setup}) does not exist.')
        with open(path, encoding='utf-8') as fp:
            match = _FILE_VERSION_RE.search(fp.read())
        versions[name] = match.group(1) if match else None
    return versions


def _version_key(version):
    major, minor = version.split('.')
    return int(major), int(minor)


######### Updater ##################################################################################

def compile_updater():
    """Compile SIMsalabim's Updater if the binary is missing or older than Updater.pas.
    Returns the path to the binary."""
    source = os.path.join(UPDATER_DIR, 'Updater.pas')
    binary = os.path.join(UPDATER_DIR, 'Updater' + EXE_EXT)
    if not os.path.isfile(source):
        raise TestInputsError(f'Cannot convert the test input files: {source} not found.')

    if os.path.isfile(binary) and os.path.getmtime(binary) >= os.path.getmtime(source):
        return binary

    if shutil.which('fpc') is None:
        raise TestInputsError('The test input files need converting, but the Free Pascal Compiler (fpc) '
                              'needed to compile the Updater was not found.')

    # Must run from the Updater folder: Updater.pas locates SIMsalabim's units via ../../Units/
    result = subprocess.run(['fpc', 'Updater.pas'], cwd=UPDATER_DIR, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.isfile(binary):
        raise TestInputsError(f'Compiling the Updater failed (exit code {result.returncode}):\n'
                              f'{result.stdout}\n{result.stderr}')
    return binary


def run_updater(updater_binary, input_dir, setup_name, terminal_access=contextlib.nullcontext):
    """Run a temporary copy of the Updater in input_dir to convert setup_name and its layer files in place.

    The Updater runs interactively in the user's terminal: its output is shown and the user answers its
    questions (overwrite confirmation, warnings) themselves. terminal_access is a context manager that
    gives the subprocess the real terminal (conftest.py uses it to suspend pytest's capturing).
    Returns the Updater's exit code."""
    tmp_updater = os.path.join(input_dir, os.path.basename(updater_binary))
    shutil.copy2(updater_binary, tmp_updater)
    try:
        cmd = [tmp_updater if IS_WINDOWS else './' + os.path.basename(tmp_updater), setup_name]
        with terminal_access():
            print(f'\n--- Running the SIMsalabim Updater on {os.path.join(input_dir, setup_name)} ---', flush=True)
            returncode = subprocess.run(cmd, cwd=input_dir).returncode
            print('--- Updater finished ---\n', flush=True)
    finally:
        os.remove(tmp_updater)
    return returncode


def _sync_setup(input_dir, setup_name, target, log=print, terminal_access=contextlib.nullcontext, convert=True):
    versions = get_input_versions(input_dir, setup_name)
    if all(v == target for v in versions.values()):
        return

    found = ', '.join(f'{name}: {v}' for name, v in versions.items())
    if any(v is None for v in versions.values()):
        raise TestInputsError(f'No version number found in some test input files in {input_dir} ({found}).')
    if any(_version_key(v) > _version_key(target) for v in versions.values()):
        raise TestInputsError(f'Test input files in {input_dir} are newer than SIMsalabim {target} ({found}). '
                              'The Updater can only upgrade files: update SIMsalabim.')

    # The Updater steps a setup file and its layer files up together, one version at a time, and only
    # updates layer files that are at the same version as the setup file. A mixed set cannot be converted.
    setup_version = versions[setup_name]
    mismatched = [name for name, v in versions.items() if v != setup_version]
    if mismatched:
        raise TestInputsError(
            f'{setup_name} is at version {setup_version}, but some of its layer files are not ({found}) in '
            f'{input_dir}.\nThe Updater only converts layer files that are at the same version as their setup '
            f'file, so it cannot fix this. Bring {", ".join(mismatched)} to version {setup_version} '
            f'(or the whole set to the same version) first.')

    if not convert:
        raise TestInputsError(
            f'{setup_name} and its layer files in {input_dir} are at version {setup_version}, but SIMsalabim is '
            f'at version {target}.\nConvert them with the SIMsalabim Updater by running, from a terminal in the '
            f'pySIMsalabim folder:\n    python {os.path.join("pySIMsalabim", "tests", "sim_inputs_setup.py")}')

    returncode = run_updater(compile_updater(), input_dir, setup_name, terminal_access)
    new_versions = get_input_versions(input_dir, setup_name)
    if returncode != 0 or any(v != target for v in new_versions.values()):
        new_found = ', '.join(f'{name}: {v}' for name, v in new_versions.items())
        raise TestInputsError(f'The test input files in {input_dir} were not converted to SIMsalabim {target} '
                              f'(Updater exit code {returncode}; versions now {new_found}). '
                              'Either the conversion was declined or the Updater stopped with an error (see its output above).')
    log(f'Converted {setup_name} (and its layer files) in {input_dir} from ({found}) to {target}.')


def sync_input_versions(input_dir, program_dir, log=print, terminal_access=contextlib.nullcontext, convert=True):
    """Make sure every simulation_setup*.txt in input_dir (and the layer files it references)
    matches the SIMsalabim version, converting them if needed (or raising TestInputsError if convert is False)."""
    target = get_simsalabim_version(program_dir)
    setups = sorted(os.path.basename(f) for f in glob.glob(os.path.join(input_dir, 'simulation_setup*.txt')))
    if not setups:
        raise TestInputsError(f'No simulation_setup*.txt found in {input_dir}.')
    for setup_name in setups:
        _sync_setup(input_dir, setup_name, target, log, terminal_access, convert)


######### Copy / cleanup ###########################################################################

def sync_all_inputs(log=print, terminal_access=contextlib.nullcontext, convert=True):
    """Check (and convert if needed and allowed) the SimSS and ZimT test input files.
    Returns the list of (program folder, input folder) that exist."""
    if not os.path.isdir(SIMSALABIM_DIR):
        raise TestInputsError(f'SIMsalabim folder not found at {SIMSALABIM_DIR}.')
    input_dirs = []
    for program_dir in PROGRAMS:
        input_dir = os.path.join(SIM_INPUTS_DIR, program_dir)
        if os.path.isdir(input_dir):
            sync_input_versions(input_dir, program_dir, log, terminal_access, convert)
            log(f'Test inputs for {program_dir}: version matches SIMsalabim {get_simsalabim_version(program_dir)}')
            input_dirs.append((program_dir, input_dir))
    return input_dirs


def prepare_test_inputs(log=print, terminal_access=contextlib.nullcontext, convert=True):
    """Bring the test input files to the SIMsalabim version and copy them into SIMsalabim/SimSS and ZimT.
    log is called with each progress message (print by default; conftest.py passes pytest's terminal writer).
    terminal_access is a context manager giving the interactive Updater access to the terminal.
    With convert=False (used by the notebooks) a version mismatch raises TestInputsError instead of
    running the Updater. All versions are checked before anything is copied."""
    input_dirs = sync_all_inputs(log, terminal_access, convert)

    _generated_to_remove[:] = [f for f in GENERATED_FILES if not os.path.exists(os.path.join(SIMSALABIM_DIR, f))]

    for program_dir, input_dir in input_dirs:
        dest_dir = os.path.join(SIMSALABIM_DIR, program_dir)
        log(f'Copying the {program_dir} test inputs to {dest_dir}')
        for name in sorted(os.listdir(input_dir)):
            src = os.path.join(input_dir, name)
            if os.path.isfile(src):
                dest = os.path.join(dest_dir, name)
                shutil.copy2(src, dest)
                if dest not in _copied_files:
                    _copied_files.append(dest)


def cleanup_test_inputs():
    """Delete the files copied by prepare_test_inputs() and the files generated by the tests."""
    for path in _copied_files + [os.path.join(SIMSALABIM_DIR, f) for f in _generated_to_remove]:
        if os.path.isfile(path):
            os.remove(path)
    _copied_files.clear()
    _generated_to_remove.clear()


if __name__ == '__main__':
    # Check the test input files against the SIMsalabim version and convert them interactively if
    # needed (nothing is copied to the SIMsalabim folder).
    try:
        sync_all_inputs()
    except TestInputsError as e:
        print(f'Error: {e}')
        sys.exit(1)

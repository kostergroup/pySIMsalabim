"""pytest hooks for the pySIMsalabim tests.

Before the session, the test input files (sim_inputs/default) are brought to the SIMsalabim
version and copied into SIMsalabim/SimSS and SIMsalabim/ZimT; after the session they are removed.
See sim_inputs_setup.py for details.
"""

import contextlib

import pytest

from .sim_inputs_setup import TestInputsError, cleanup_test_inputs, prepare_test_inputs


def _terminal_access_factory(config):
    """Return a context manager that suspends pytest's capturing (stdin included), so the
    interactive Updater can show its output and read the user's answers."""
    capman = config.pluginmanager.get_plugin('capturemanager')

    @contextlib.contextmanager
    def terminal_access():
        if capman is None:
            yield
            return
        capman.suspend_global_capture(in_=True)
        try:
            yield
        finally:
            capman.resume_global_capture()

    return terminal_access


@pytest.hookimpl(wrapper=True)
def pytest_sessionstart(session):
    # Wrapper: the code after `yield` runs once every other sessionstart hook is done, i.e. after
    # the terminal reporter has printed the session header and before collection / the first test.
    result = yield
    # Write through the terminal reporter: plain prints are captured by pytest at this stage
    reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    log = reporter.write_line if reporter is not None else print
    try:
        prepare_test_inputs(log=log, terminal_access=_terminal_access_factory(session.config))
    except TestInputsError as e:
        cleanup_test_inputs()
        pytest.exit(str(e), returncode=1)
    return result


def pytest_sessionfinish(session, exitstatus):
    cleanup_test_inputs()

# coding=utf-8
import shlex
import unittest
from os import getcwd, chdir, makedirs
from os.path import join, dirname
from subprocess import check_output, STDOUT, CalledProcessError
from functools import wraps
from textwrap import dedent
from contextlib import contextmanager

from mock import patch
from git import Repo

from becareful.runner import Runner
from becareful.plugins import initializer
from becareful.diffconvert import GitDiffIndex
from becareful.tools import NumberedDirectoriesToGit
from becareful.output import ConsoleView


def strip_paint(payload):
    """
    Removes any console specific color characters.

    Where ``payload`` is a string containing special characters used to print
    colored output to the terminal.

    Returns a unicode string without the paint.
    """
    strip = [u'\x1b[31;1m', u'\x1b[32;1m', u'\x1b[33;1m', u'\x1b[39;22m']
    for paint in strip:
        payload = payload.replace(paint, '')
    return payload


@contextmanager
def cwd_bounce(dir):
    """
    Temporarily changes to a directory and changes back in the end.

    Where ``dir`` is the directory you wish to change to. When the context
    manager exits it will change back to the original working directory.

    Context manager will yield the original working directory and make that
    available to the context manager's assignment target.
    """
    original_dir = getcwd()

    try:
        chdir(dir)

        yield original_dir
    finally:
        chdir(original_dir)


def cd_gitrepo(func):
    """
    Change the current working directory to the test case's Git repository.

    This uses ``self.gitrepodir`` which is created by the
    :py:module:`becareful.tests.noseplugin`.
    """
    @wraps(func)
    def wrapper(testcase, *args, **kwargs):
        with cwd_bounce(testcase.gitrepodir):
            func(testcase, *args, **kwargs)

    return wrapper


class BeCarefulTestCase(unittest.TestCase):

    """
    Base test case for all BeCareful tests.

    """
    def setUp(self):
        self.fixturesdir = join(dirname(__file__), 'fixtures')

    def assertResults(self, expected, actual):
        """
        Assert that output matches expected argument.

        This method has some special handling intended to ease testing of the
        the output we get from :py:module:`becareful.output`.

        As an example, it can be used like this::

            self.assertResults(u'''
                ▾  Plugin 1

                ✓  commit

                Ran 1 plugin
                    Info 1 Warn 0 Stop 0
                ''', self.output)

        This method will automatically dedent and strip the expected and clear
        off any console formatting characters (those that turn text colors or
        bold text).
        """
        expected = dedent(expected).strip()

        actual = strip_paint(actual.strip())

        self.assertEqual(expected, actual)

    def runcmd(self, cmd):
        """
        Takes a string and runs it, returning the output and exit code.

        Return is a tuple ``(exit_code, output_str)``.
        """
        cmd_args = shlex.split(cmd)

        try:
            output = check_output(cmd_args, stderr=STDOUT)
            retcode = 0
        except CalledProcessError as cpe:
            output = cpe.output
            retcode = cpe.returncode
        except OSError:
            output = None
            retcode = None

        return (retcode, output)

    def repo_from_fixture(self, repo_name):
        """
        Creates a ``git.Repo`` from the given fixture.

        The fixture should be a directory containing numbered directories
        suitable for creating a ``NumberedDirectoriesToGit``.

        Returns a tuple of 3 objects: repo, working_dir, diffs.
        """
        ndgit = NumberedDirectoriesToGit(
            join(self.fixturesdir, repo_name))

        repo = ndgit.repo

        return (ndgit.repo, repo.working_dir, ndgit.diffs())

    def git_diff_index(self, repo, diffs):
        """
        Retrieves the ``GitDiffIndex`` for the repository and diffs.
        """
        return GitDiffIndex(self.testrepodir, diffs)

    def create_file(self, gitrepodir, name, content):
        """
        Create or a file in the Git repository.

        The name of the file can contain directories, they will be created
        automatically.

        The directory ``gitrepodir`` represents the full path to the Git
        repository. ``name`` will be a string like ``a/b/c.txt``. ``content``
        will be written to the file.

        Return ``True`` if it complete.
        """
        try:
            makedirs(dirname(join(gitrepodir, name)))
        except OSError:
            # Directory may already exist
            pass

        with open(join(gitrepodir, name), 'w') as fh:
            fh.write(content)

        return True

    def stage(self, gitrepodir, name, content):
        """
        Create or modify a file in a Git repository and stage it in the index.

        A ``git.Index`` object will be returned.
        """
        self.create_file(gitrepodir, name, content)

        repo = Repo(gitrepodir)
        repo.index.add([name])

        return repo.index

    def stage_remove(self, gitrepodir, name):
        """
        Stage a file for removal from the Git repository.

        Where ``name`` is the path to the file.
        """
        repo = Repo(gitrepodir)
        repo.index.remove([name])

        return repo.index

    def commit(self, gitrepodir, name, content):
        """
        Create or modify a file in a Git repository and commit it.

        A ``git.Commit`` object will be returned representing the commit.

        """
        index = self.stage(gitrepodir, name, content)

        return index.commit(name)


class ViewTestCase(BeCarefulTestCase):

    """
    Access to captured output for test cases that interact with a view.

    To use this test case, the ``setUp`` method of the sub-class must set
    ``self.view`` equal to the target view.

    """
    @property
    def output(self):
        """
        Gets any output from the view that has been collected.

        Returns an empty string if the view doesn't exist or no output has
        been collected.
        """
        if not hasattr(self, 'view'):
            return ''

        return self.view._collect['stdout'].getvalue()

    @property
    def error(self):
        """
        Gets any error messages generated by the view.

        Returns an empty string if the view doesn't exist or has no output.
        """
        if not hasattr(self, 'view'):
            return ''

        return self.view._collect['stderr'].getvalue()


class RunnerTestCase(ViewTestCase):

    """
    Test case for working with :py:class:`Runner` instances

    """
    def setUp(self):
        super(RunnerTestCase, self).setUp()

        self.runner = self._init_runner()

    def _init_runner(self):
        """
        Initialize a :py:class:`Runner` and returns it.

        This will configure the runner to collect output and not exit when it
        encounters an exceptions
        """
        runner = Runner()

        # Tell the view to collect output instead of printing it
        runner.view.collect_output = True
        # Don't exit when an exception occurs so our test can continue
        runner.view.exit_on_exception = False

        # Set this up so output() and error() can read the data
        self.view = runner.view

        return runner


class PluginTestCase(BeCarefulTestCase):

    """
    Base test case for plugin tests.

    """
    def setUp(self):
        super(PluginTestCase, self).setUp()

        # Initialize the repo and grab it's config file
        self.bcconfig = initializer(self.gitrepodir)

    def _add_plugin(self, config, plugindir):
        """
        Adds the plugin to a main BeCareful config.
        """
        section = 'plugin:test01:{}'.format(plugindir)
        config.add_section(section)
        config.set(section, 'path',
            join(self.fixturesdir, plugindir))


class CommandTestCase(ViewTestCase):

    """
    Base test case for command tests.

    """
    def run_command(self, command=None):
        """
        Run a subcommand.
        """
        with patch('becareful.commands.base.create_view') as cv:
            # We hijack the create_view function so we can tell it to collect
            # output and not exit on exception.
            view = ConsoleView()

            # Collect, don't print
            view.collect_output = True
            # Don't call sys.exit() on exception
            view.exit_on_exception = False

            cv.return_value = view

            # Keep a reference to this so output() and error() will work
            self.view = view

            return self.command(shlex.split(command or ''))

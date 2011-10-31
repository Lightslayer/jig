"""
Convert changes in a Git repository to JSON.
"""
import json
from difflib import SequenceMatcher

from git.exc import BadObject


def describe_diff(a, b):
    """
    Takes two strings and calculates the diff between them.

    Output format is::

        (line_number, type, line)

    ``type`` is one of: ``' '``, ``'-'``, ``'+'``.

    Example::

        >>> list(describe_diff('a\nb\nc', 'a\nc\nd'))
        [(1, ' ', 'a'),
         (2, '-', 'b'),
         (2, ' ', 'c'),
         (3, '+', 'd')]
    """
    a = a.splitlines()
    b = b.splitlines()

    for tag, i1, i2, j1, j2 in SequenceMatcher(None,a,b).get_opcodes():
        if tag == 'equal':
            for idx, line in enumerate(b[j1:j2]):
                yield (idx + j1 + 1, ' ', line)
            continue
        if tag == 'replace' or tag == 'delete':
            for idx, line in enumerate(a[i1:i2]):
                yield (idx + i1 + 1, '-', line)
        if tag == 'replace' or tag == 'insert':
            for idx, line in enumerate(b[j1:j2]):
                yield (idx + j1 + 1, '+', line)


class DiffType(object):

    """
    What kind of operation does this diff represent.

    """
    A = 'added'
    D = 'deleted'
    R = 'renamed'
    M = 'modified'

    @classmethod
    def for_diff(cls, diff):
        """
        Determines what type of diff this represents
        """
        if diff.new_file:
            return cls.A
        elif diff.deleted_file:
            return cls.D
        elif diff.renamed:
            return cls.R
        elif diff.a_blob and diff.b_blob and diff.a_blob != diff.b_blob:
            return cls.M


class GitDiffIndex(object):

    """
    Converts diff index object to something useful for pre-commit hooks.

    The expected argument when creating an instance is a
    :py:class:`git.diff.DiffIndex` object.

    The following information is extracted from the list

    """
    def __init__(self, gitrepo, difflist):
        """
        Where ``gitrepo`` is the path to the root of the Git repository.
        """
        self.gitrepo = gitrepo
        self.difflist = difflist

    def files(self):
        """
        A generator for returning human-readable information about the diffs.

        Generator yields dictionaries that contain filename, name, diff, and
        type.

        ``filename`` is the absolute path to the file that was modified.

        ``name`` is the path of the file relative to the Git repository.

        ``diff`` is a list of ``(line_number, '+'|'-'|' ', line)`` describing
        the changes that occurred between the a_blob and b_blob from the
        commit.

        ``type`` is ``added``, ``deleted``, ``renamed``, ``modified`` and
        describes the overall action that occurred on this file.
        """
        for diff in self.difflist:
            a_blob = diff.a_blob
            b_blob = diff.b_blob

            a_data = ''
            b_data = ''

            try:
                a_data = a_blob.data_stream.read()
            except BadObject:
                pass

            try:
                b_data = b_blob.data_stream.read()
            except BadObject:
                pass

            linediff = describe_diff(a_data, b_data)

            yield {
                'filename': a_blob.abspath,
                'name': a_blob.name,
                'diff': linediff,
                'type': DiffType.for_diff(diff)}



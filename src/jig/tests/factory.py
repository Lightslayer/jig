# coding=utf-8
from jig.tests.mocks import MockPlugin

try:
    from collections import OrderedDict
except ImportError:   # pragma: no cover
    from ordereddict import OrderedDict

anon_obj = object()


def error():
    return OrderedDict([
        (MockPlugin(), (1, '', 'Plugin failed'))
    ])


def no_results():
    return OrderedDict([
        (MockPlugin(), (0, None, '')),
        (MockPlugin(), (0, '', '')),
        (MockPlugin(), (0, [''], '')),
        (MockPlugin(), (0, [['w', '']], '')),
        (MockPlugin(), (0, {'a.txt': ''}, '')),
        (MockPlugin(), (0, {'a.txt': [[]]}, '')),
        (MockPlugin(), (0, {'a.txt': [['']]}, '')),
        (MockPlugin(), (0, {'a.txt': [['', '']]}, '')),
        (MockPlugin(), (0, {'a.txt': [[None, '', '']]}, '')),
        (MockPlugin(), (0, {'a.txt': [[1, '', '']]}, ''))
    ])


def commit_specific_message():
    return OrderedDict([
        (MockPlugin(), (0, 'default', '')),
        (MockPlugin(), (0, [['warn', 'warning']], ''))
    ])


def file_specific_message():
    # Line number of None will be recognized as file-specific.
    stdout1 = OrderedDict([
        ('a.txt', [[None, 'warn', 'Problem with this file']])
    ])

    # Will a length of 2 be recognized as file-specific?
    stdout2 = OrderedDict([
        ('a.txt', [['warn', 'Problem with this file']])
    ])

    # Can we handle more than one file and different argument signatures
    # for the type?
    stdout3 = OrderedDict([
        ('a.txt', [['Info A']]),
        ('b.txt', [['warn', 'Warn B']]),
        ('c.txt', [['s', 'Stop C']])
    ])

    return OrderedDict([
        (MockPlugin(), (0, stdout1, '')),
        (MockPlugin(), (0, stdout2, '')),
        (MockPlugin(), (0, stdout3, ''))
    ])


def line_specific_message():
    stdout = OrderedDict([
        ('a.txt', [[1, None, 'Info A']]),
        ('b.txt', [[2, 'warn', 'Warn B']]),
        ('c.txt', [[3, 'stop', 'Stop C']])
    ])

    return OrderedDict([
        (MockPlugin(), (0, stdout, ''))
    ])


def one_of_each():
    return OrderedDict([
        (MockPlugin(), (0, ['C'], '')),
        (MockPlugin(), (0, {'a.txt': 'F'}, '')),
        (MockPlugin(), (0, {'a.txt': [[1, None, 'L']]}, ''))
    ])


def commit_specific_bad_syntax():
    return OrderedDict([
        (MockPlugin(), (0, anon_obj, '')),
        (MockPlugin(), (0, [[1, 2, 3, 4, 5]], ''))
    ])


def commit_specific_error():
    return OrderedDict([
        (MockPlugin(), (1, anon_obj, '')),
        (MockPlugin(), (1, [[1, 2, 3, 4, 5]], ''))
    ])


def file_specific_bad_syntax():
    return OrderedDict([
        (MockPlugin(), (0, {'a.txt': anon_obj}, '')),
        (MockPlugin(), (0, {'a.txt': [anon_obj]}, '')),
        (MockPlugin(), (0, {'a.txt': [1,  None]}, '')),
        (MockPlugin(), (0, {'a.txt': [[1, 2, 3, 4, 5]]}, ''))
    ])


def file_specific_error():
    return OrderedDict([
        (MockPlugin(), (1, {'a.txt': anon_obj}, '')),
        (MockPlugin(), (1, {'a.txt': [anon_obj]}, '')),
        (MockPlugin(), (1, {'a.txt': [1,  None]}, '')),
        (MockPlugin(), (1, {'a.txt': [[1, 2, 3, 4, 5]]}, ''))
    ])

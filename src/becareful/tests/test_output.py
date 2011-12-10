# coding=utf-8
from collections import OrderedDict

from becareful.tests.testcase import BeCarefulTestCase, ViewTestCase
from becareful.tests.mocks import MockPlugin
from becareful.output import ConsoleView, Message, ResultsCollater


class TestConsoleView(ViewTestCase):

    """
    With plugin results we can format them to the console.

    """
    def setUp(self):
        self.view = ConsoleView()

        self.view.collect_output = True
        self.view.exit_on_exception = False

    def test_commit_specific_message(self):
        plugin = MockPlugin()
        plugin.name = 'Plugin 1'

        self.view.print_results({
            plugin: (0, 'commit', '')})

        self.assertResults(u"""
            ▾  Plugin 1

            ✓  commit

            Ran 1 plugin
                Info 1 Warn 0 Stop 0
            """, self.output)

    def test_file_specific_message(self):
        plugin = MockPlugin()
        plugin.name = 'Plugin 1'

        self.view.print_results({
            plugin: (0, {u'a.txt': [[None, u'w', 'file']]}, '')})

        self.assertResults(u"""
            ▾  Plugin 1

            ⚠  a.txt
                file

            Ran 1 plugin
                Info 0 Warn 1 Stop 0
            """, self.output)

    def test_line_specific_message(self):
        plugin = MockPlugin()
        plugin.name = 'Plugin 1'

        self.view.print_results({
            plugin: (0, {u'a.txt': [[1, 's', 'stop']]}, '')})

        self.assertResults(u"""
            ▾  Plugin 1

            ✕  line 1: a.txt
                stop

            Ran 1 plugin
                Info 0 Warn 0 Stop 1
            """, self.output)

    def test_two_plugins(self):
        plugin1 = MockPlugin()
        plugin1.name = 'Plugin 1'

        plugin2 = MockPlugin()
        plugin2.name = 'Plugin 2'

        results = OrderedDict()

        results[plugin1] = (0, ['a', 'b'], '')
        results[plugin2] = (0, ['a', 'b'], '')

        self.view.print_results(results)

        self.assertResults(u"""
            ▾  Plugin 1

            ✓  a

            ✓  b

            ▾  Plugin 2

            ✓  a

            ✓  b

            Ran 2 plugins
                Info 4 Warn 0 Stop 0
            """, self.output)


class TestResultsCollater(BeCarefulTestCase):

    """
    Collate results into digestible summaries.

    """
    def test_no_results(self):
        """
        We have results but no real content.
        """
        results = {
            MockPlugin(): (0, None, ''),
            MockPlugin(): (0, '', ''),
            MockPlugin(): (0, [''], ''),
            MockPlugin(): (0, {u'a.txt': u''}, ''),
            MockPlugin(): (0, {u'a.txt': [[]]}, ''),
            MockPlugin(): (0, {u'a.txt': [[u'']]}, ''),
            MockPlugin(): (0, {u'a.txt': [['', u'']]}, ''),
            MockPlugin(): (0, {u'a.txt': [[None, '', u'']]}, ''),
            MockPlugin(): (0, {u'a.txt': [[1, '', u'']]}, '')}

        rc = ResultsCollater(results)

        cm, fm, lm = rc.messages

        # Should all be empty since nothing of interest was found
        self.assertEqual([], cm)
        self.assertEqual([], fm)
        self.assertEqual([], lm)

        # And we should have no errors
        self.assertEqual([], rc.errors)

    def test_commit_specific_message(self):
        """
        Results that are commit specific are collated correctly.
        """
        results = OrderedDict()
        results[MockPlugin()] = (0, 'default', '')
        results[MockPlugin()] = (0, [[u'warn', u'warning']], '')

        rc = ResultsCollater(results)

        messages, fm, lm = rc.messages

        # Defaults to info type
        self.assertEqual(Message(None, type='info', body='default'),
            messages[0])
        self.assertEqual(Message(None, type='warn', body='warning'),
            messages[1])

        # And our type counts should be 1 info 1 warning
        self.assertEqual({u'info': 1, u'warn': 1, u'stop': 0}, rc.counts)

        # The rest of these should be empty
        self.assertEqual([], fm)
        self.assertEqual([], lm)

        # And we should have no errors
        self.assertEqual([], rc.errors)

    def test_file_specific_message(self):
        """
        Results that are file-specific are collated correctly.
        """
        # Line number of None will be recognized as file-specific.
        stdout1 = {u'a.txt': [
            [None, u'warn', 'Problem with this file']]}
        # Will a length of 2 be recognized as file-specific?
        stdout2 = {u'a.txt': [
            [u'warn', 'Problem with this file']]}
        # Can we handle more than one file and different argument signatures
        # for the type?
        stdout3 = OrderedDict()
        stdout3[u'a.txt'] = [['Info A']]
        stdout3[u'b.txt'] = [[u'warn', 'Warn B']]
        stdout3[u'c.txt'] = [[u's', 'Stop C']]

        results = OrderedDict()
        results[MockPlugin()] = (0, stdout1, '')
        results[MockPlugin()] = (0, stdout2, '')
        results[MockPlugin()] = (0, stdout3, '')

        rc = ResultsCollater(results)

        self.assertEqual({u'info': 1, u'warn': 3, u'stop': 1}, rc.counts)

        cm, messages, lm = rc.messages

        for msg in messages:
            # They all lack a line number, making them file-specific.
            self.assertIsNone(msg.line)
            # But they have a file
            self.assertIsNotNone(msg.file)

        # First set's None get's recognized as file-specific
        self.assertEqual(
            Message(None, type='warn', body='Problem with this file',
                file='a.txt'),
            messages[0])

        # Second set get's recognized as a warning
        self.assertEqual(
            Message(None, type='warn', body='Problem with this file',
                file='a.txt'),
            messages[1])

        self.assertEqual(
            Message(None, type='info', body='Info A',
                file='a.txt'),
            messages[2])
        self.assertEqual(
            Message(None, type='warn', body='Warn B',
                file='b.txt'),
            messages[3])
        self.assertEqual(
            Message(None, type='stop', body='Stop C',
                file='c.txt'),
            messages[4])

        # The other messages should be empty
        self.assertEqual([], cm)
        self.assertEqual([], lm)

        # And we should have no errors
        self.assertEqual([], rc.errors)

    def test_line_specific_message(self):
        stdout = OrderedDict()
        stdout[u'a.txt'] = [[1, None, 'Info A']]
        stdout[u'b.txt'] = [[2, u'warn', 'Warn B']]
        stdout[u'c.txt'] = [[3, u'stop', 'Stop C']]

        results = OrderedDict()
        results[MockPlugin()] = (0, stdout, '')

        rc = ResultsCollater(results)

        self.assertEqual({u'info': 1, u'warn': 1, u'stop': 1}, rc.counts)

        cm, fm, messages = rc.messages

        self.assertEqual(
            Message(None, type='info', body='Info A', file=u'a.txt', line=1),
            messages[0])
        self.assertEqual(
            Message(None, type='warn', body='Warn B', file=u'b.txt', line=2),
            messages[1])
        self.assertEqual(
            Message(None, type='stop', body='Stop C', file=u'c.txt', line=3),
            messages[2])

        # The other messages should be empty
        self.assertEqual([], cm)
        self.assertEqual([], fm)

        # And we should have no errors
        self.assertEqual([], rc.errors)

    def test_one_of_each(self):
        results = {
            MockPlugin(): (0, ['C'], ''),
            MockPlugin(): (0, {u'a.txt': u'F'}, ''),
            MockPlugin(): (0, {u'a.txt': [[1, None, u'L']]}, '')}

        rc = ResultsCollater(results)

        self.assertEqual({u'info': 3, u'warn': 0, u'stop': 0}, rc.counts)

        cm, fm, lm = rc.messages

        self.assertEqual(1, len(cm))
        self.assertEqual(1, len(fm))
        self.assertEqual(1, len(lm))

        self.assertEqual(
            Message(None, type="info", body="C"),
            cm[0])
        self.assertEqual(
            Message(None, type="info", body="F", file=u'a.txt'),
            fm[0])
        self.assertEqual(
            Message(None, type="info", body="L", file=u'a.txt', line=1),
            lm[0])

    def test_plugin_count(self):
        rc1 = ResultsCollater({})

        rc2 = ResultsCollater({
            MockPlugin(): (0, [''], ''),
            MockPlugin(): (0, {u'a.txt': u'F'}, '')})

        rc3 = ResultsCollater({
            MockPlugin(): (0, ['C'], ''),
            MockPlugin(): (0, {u'a.txt': u'F'}, ''),
            MockPlugin(): (0, {u'a.txt': [[1, None, u'L']]}, '')})

        # First collator had no results
        self.assertEqual(0, len(rc1.plugins))
        self.assertEqual(0, len(rc1.reporters))

        # Second had a result with no meaningful content
        self.assertEqual(2, len(rc2.plugins))
        self.assertEqual(1, len(rc2.reporters))

        # Third had something to report for all plugins
        self.assertEqual(3, len(rc3.plugins))
        self.assertEqual(3, len(rc3.reporters))

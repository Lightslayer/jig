# coding=utf-8
from jig.output import INFO, WARN, STOP
from jig.formatters.utils import green_bold, yellow_bold, red_bold

OK_SIGN = '\U0001f44c'
ATTENTION = '\U0001f449'
EXPLODE = '\U0001f4a5'


class FancyFormatter(object):

    """
    Fancy unicode symbol results formatter.

    """
    # What is the simple name used to specify this formatter on the command line
    name = 'fancy'

    def print_results(self, printer, collator):
        """
        Format and print plugins results.

        :param function printer: called to send output to the view
        :param ResultsCollator collator: access to the results
        """
        plugins = collator.plugins
        errors = collator.errors
        reporters = collator.reporters

        form = 'plugin' if len(plugins) == 1 else 'plugins'

        if len(reporters) == 0 and len(errors) == 0:
            # Nothing to report
            form = 'plugin' if len(plugins) == 1 else 'plugins'
            printer(
                '{ok_sign}  Jig ran {plen} {form}, '
                'nothing to report'.format(
                    ok_sign=OK_SIGN, plen=len(plugins), form=form
                )
            )
            return

        # Gather the distinct message types from the results
        cm, fm, lm = collator.messages

        # Order them from least specific to most specific, put the errors last
        messages = cm + fm + lm + errors

        # How do our message types map to a symbol
        type_to_symbol = {
            INFO: green_bold('\u2713'),
            WARN: yellow_bold('\u26a0'),
            STOP: red_bold('\u2715')}

        ic, wc, sc = (0, 0, 0)
        last_plugin = None
        for msg in messages:
            if last_plugin != msg.plugin:
                printer('\u25be  {0}'.format(msg.plugin.name))
                printer('')
                last_plugin = msg.plugin
            colorized = '{0}  {1}'.format(
                type_to_symbol[msg.type], self._format_message(msg))
            printer(colorized)
            printer('')

        ic, wc, sc = [i[1] for i in list(collator.counts.items())]
        info = green_bold(ic) if ic else ic
        warn = yellow_bold(wc) if wc else wc
        stop = red_bold(sc) if sc else sc

        sign = EXPLODE if sc > 0 else ATTENTION
        printer('{explode}  Jig ran {plen} {form}'.format(
            explode=sign, plen=len(plugins), form=form))

        printer('    Info {ic} Warn {wc} Stop {sc}'.format(
            ic=info, wc=warn, sc=stop))

        if len(errors):
            printer('    ({ec} {form} reported errors)'.format(
                ec=len(errors), form=form))

        # Return the counts for the different types of messages
        return (ic, wc, sc)

    def _format_message(self, msg):
        """
        Formats a single message to a string.
        """
        out = []
        header = ''
        body = ''

        if msg.line:
            header += 'line {0}: '.format(msg.line)

        if msg.file:
            header += msg.file

        if header:
            body = '    {0}'.format(msg.body)
        else:
            body = '{0}'.format(msg.body)

        if header:
            out.append(header)

        out.append(body)

        return '\n'.join(out)

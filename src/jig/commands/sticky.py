import argparse

from jig.exc import PluginError
from jig.commands.base import BaseCommand

_parser = argparse.ArgumentParser(
    description='Make Jig auto-init every time you git clone',
    usage='jig sticky [-h]')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        with self.out() as out:
            out.extend('...')

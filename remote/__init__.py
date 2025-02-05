from __future__ import absolute_import, print_function, unicode_literals

from .repl import REPL


def create_instance(c_instance):
    return REPL(c_instance=c_instance)

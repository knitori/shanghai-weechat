# -*- coding: utf-8 -*-
from collections import namedtuple
import re

parsed_line = namedtuple('ParsedLine', 'prefix command middle trailing raw')
parsed_prefix = namedtuple('Prefix', 'nick user host raw')

prefix_pattern = re.compile(
    r'^(?P<nick>[^!@]+)(?:!(?P<user>[^!@]+))?(?:@(?P<host>[^!@]+))?$')
tag_pattern = re.compile(
    r'(\x0F)|(\x1F)|(\x1D)|(\x01)|(\x02)|(\x03((0[0-9])|(1[0-6])|([0-9]))'
    r'(,((0[0-9])|(1[0-6])|([0-9])))?)')


def ischannel(channel):
    # this might actually be server dependent. but for now it works.
    return channel.startswith(('#', '+', '&'))


def rfc_lower(name):
    return str(name).lower()


def rfc_upper(name):
    return str(name).upper()


def rfc_comp(name, name2):
    return rfc_lower(name) == rfc_lower(name2)


def strip_tags(text):
    return tag_pattern.sub('', text)


def split_prefix(prefix):
    m = prefix_pattern.match(prefix)
    if m is None:
        raise ValueError('prefix mismatch! {!r}'.format(prefix))
    return parsed_prefix(m.group('nick'), m.group('user'),
                         m.group('host'), prefix)


def parse_line(line):
    raw_line = line
    prefix = None
    command = None
    middle = []
    trailing = None

    if line.startswith(':'):
        prefix, line = line[1:].split(None, 1)

    if ' :' in line:
        line, trailing = line.split(' :', 1)

    middle = line.split()
    command = middle.pop(0)
    command = command.upper()

    if prefix is not None:
        prefix = split_prefix(prefix)

    # special case, where we look into the message
    if command in ('PRIVMSG', 'NOTICE'):
        if trailing and trailing.startswith('\x01') and \
                trailing.endswith('\x01'):
            ctcp_params = trailing[1:-1].split(None, 1)
            if ctcp_params:
                ctcp_cmd = ctcp_params.pop(0).upper()
                if command == 'PRIVMSG':
                    command = 'CTCP_' + ctcp_cmd
                else:
                    command = 'CTCPR_' + ctcp_cmd
                trailing = ' '.join(ctcp_params)

    return parsed_line(prefix, command, middle, trailing, raw_line)


def reset(text):
    return '\x0f' + text


def color(text, fg, bg=None):
    if bg:
        return '\x03{fg:02d},{bg:02d}{text}\x0f'\
            .format(text=text, fg=fg, bg=bg)
    else:
        return '\x03{fg:02d}{text}\x0f'\
            .format(text=text, fg=fg, bg=bg)

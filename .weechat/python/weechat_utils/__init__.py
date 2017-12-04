# -*- coding: utf-8 -*-
# あいうえお
from __future__ import absolute_import, division
from collections import namedtuple
import pipes
import functools
import random
import re
random = random.SystemRandom()

import weechat
from .irc import parse_line, split_prefix, strip_tags, color


class Context(object):
    def __init__(self, server, channel='', encoding='utf-8', **kwargs):
        self.server = server
        self.channel = channel
        self.encoding = encoding
        self.nickname = weechat.info_get("irc_nick", self.server)
        if channel:
            buffer_str = '{},{}'.format(server, channel)
        else:
            buffer_str = server
        self.buffer = weechat.info_get('irc_buffer', buffer_str)
        self._extra_data = {}
        if kwargs:
            self.extra_data(**kwargs)

    def set_buffer(self, buffer):
        self.buffer = buffer

    def to_channel(self, channel):
        self.buffer = weechat.info_get(
            'irc_buffer', '{},{}'.format(self.server, channel))

    def prnt(self, *args):
        # simulate the way the print-statement works
        outstr = " ".join(
            str(arg) if not isinstance(arg, unicode)
            else arg.encode(self.encoding) for arg in args)
        weechat.prnt(self.buffer, outstr)

    def debug(self, *args):
        buffer = self.buffer
        self.buffer = ""
        self.prnt(*args)
        self.buffer = buffer

    def command(self, cmd):
        if isinstance(cmd, unicode):
            cmd = cmd.encode(self.encoding)
        weechat.command(self.buffer, cmd)

    def extra_data(self, **kwargs):
        for key, arg in kwargs.iteritems():
            self._extra_data[key] = arg

    def get(self, name, default=None):
        return self._extra_data.get(name, default)

    def is_channel(self, channel):
        return weechat.info_get(
            "irc_is_channel", "{},{}"
            .format(self.server, channel)) == '1'


class hook_signal(object):
    mapped_user_data = {}

    def __init__(self, signal, server='*', userdata=None, encoding='utf-8'):
        if userdata is not None:
            self.data_key = '{:x}'.format(id(userdata))
            hook_signal.mapped_user_data[self.data_key] = userdata
        else:
            self.data_key = ''

        self.encoding = encoding
        self.signal = signal
        self.server = server

    def __call__(self, func):
        self.func = func
        weechat.hook_signal(
            '{},irc_in2_{}'.format(self.server, self.signal.lower()),
            func.func_name, self.data_key)
        return self.wrapper

    def wrapper(self, data, signal, signal_data):
        userdata = hook_signal.mapped_user_data.get(data, None)
        parsed_line = parse_line(signal_data)

        server = signal.split(',', 1)[0]
        ctx = Context(server, encoding=self.encoding)
        result = self.func(ctx, parsed_line, signal, userdata)
        if result is None:
            return weechat.WEECHAT_RC_OK
        return result


class hook_irc_command(hook_signal):
    # self.signal is now the "irc command", i.e. a message in privmsg
    # that starts with the signal, e.g. "!slap"
    def __call__(self, func):
        self.func = func
        weechat.hook_signal(
            '{},irc_in2_privmsg'.format(self.server),
            func.func_name, self.data_key)
        return self.wrapper

    def wrapper(self, data, signal, signal_data):
        userdata = hook_signal.mapped_user_data.get(data, None)
        parsed_line = parse_line(signal_data)

        # does this line start with the specified signal?
        tr_parts = parsed_line.trailing.split(None, 1)

        signals = self.signal
        if not isinstance(self.signal, list):
            signals = [self.signal]

        retype = type(re.compile('^$'))

        for cmd_signal in signals:
            if isinstance(cmd_signal, retype):
                if tr_parts and cmd_signal.search(tr_parts[0]):
                    break
            else:
                if tr_parts and tr_parts[0].lower() == cmd_signal.lower():
                    break
        else:
            return weechat.WEECHAT_RC_OK  # ignore

        server = signal.split(',')[0]
        channel = parsed_line.middle[0]
        ctx = Context(server, channel, self.encoding, signal=signal)
        result = self.func(ctx, parsed_line, userdata)
        if result is None:
            return weechat.WEECHAT_RC_OK
        return result


def inject_func(func, func_name=None):
    import __main__
    if func_name is None:
        func_name = '__{:032x}'.format(random.getrandbits(128))
    setattr(__main__, func_name, func)
    return func_name


def remove_func(func_name):
    import __main__
    delattr(__main__, func_name)


def hook_timer(seconds, callback, userdata=None):
    # Inject a random name for the helper function into the __main__ module
    # so weechat can find it, because weechat only takes strings as callbacks
    # and only looks in the __main__ module globals dict (afaik)
    # https://github.com/weechat/weechat/blob/master/src/plugins/python/weechat-python.c#L328-L330

    # use a random name to avoid name conflicts (assuming rational naming).

    @functools.wraps(callback)
    def _hook_timer_helper(genfuncname, remaining_calls):
        # nonlocal callback, userdata, generated_func_name  # py2.7 duh!
        try:
            result = callback(userdata)
        except:
            raise
        finally:
            remove_func(genfuncname)

        if result is None:
            result = weechat.WEECHAT_RC_OK
        return result

    genfuncname = inject_func(_hook_timer_helper)

    # align_seconds/maxcalls won't be implemented for now.
    return weechat.hook_timer(int(seconds*1000), 0, 1, genfuncname, genfuncname)


def hook_process(args, callback, stdin=None, userdata=None):
    # same as hook_timer. injects a random name in __main__ to
    # wrap around the actual callback.
    state = {
        'stdout': '',
        'stderr': '',
    }

    @functools.wraps(callback)
    def _hook_process_helper(genfuncname, command, rc, out, err):
        state['stdout'] += out
        state['stderr'] += err
        if rc == weechat.WEECHAT_HOOK_PROCESS_RUNNING:
            return weechat.WEECHAT_RC_OK
        try:
            result = callback(rc, state['stdout'], state['stderr'], userdata)
        except:
            raise
        finally:
            remove_func(genfuncname)

        if result is None:
            result = weechat.WEECHAT_RC_OK
        return result

    genfuncname = inject_func(_hook_process_helper)

    cmd = ' '.join(pipes.quote(arg) for arg in args)
    return weechat.hook_process(cmd, 30*1000, genfuncname, genfuncname)


def gen_infolist_get(infolist_name, arguments, pointer=""):
    """
    Same as infolist_get(), but yields it's elements.
    Be sure to iterate through the whole list, to ensure
    weechat.infolist_free() is called.
    """
    infolist = weechat.infolist_get(infolist_name, pointer, arguments)
    if infolist:
        while weechat.infolist_next(infolist):
            fields = weechat.infolist_fields(infolist).split(',')
            field_names = []
            list_element = {}
            for field in fields:
                field_type, field_name = field.split(':')
                field_names.append(field_name)

                # decide which function to use
                info_func = {
                    'i': weechat.infolist_integer,
                    's': weechat.infolist_string,
                    'p': weechat.infolist_pointer,
                    # 'b': weechat.infolist_buffer,
                    't': weechat.infolist_time,
                }[field_type]
                value = info_func(infolist, field_name)
                list_element[field_name] = value
            # create a temporary namedtuple type using field_names
            item_tpl = namedtuple('InfolistItem', field_names)
            yield item_tpl(**list_element)
        weechat.infolist_free(infolist)


def infolist_get(infolist_name, arguments, pointer=""):
    """
    function to ease the access to weechat.infolist_get in a more
    pythonic way.
    @infolist_name and @arguments is the same as for
    weechat.infolist_get(infolist_name, ..., arguments)
    """
    return list(gen_infolist_get(infolist_name, arguments, pointer))

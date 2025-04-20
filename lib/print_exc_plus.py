import os
import re
import sys
import traceback
from itertools import islice
from typing import Sized, Dict, Tuple

from types import FrameType

from lib.threading_timer_decorator import exit_after

try:
    import numpy
except ImportError:
    numpy = None

FORMATTING_OPTIONS = {
    'MAX_LINE_LENGTH': 1024,
    'SHORT_LINE_THRESHOLD': 128,
    'MAX_NEWLINES': 20,
}
ID = int


# noinspection PyPep8Naming
def name_or_str(X):
    try:
        return re.search(r"<class '?(.*?)'?>", str(X))[1]
    except TypeError:  # if not found
        return str(X)


@exit_after(2)
def type_string(x):
    if numpy is not None and isinstance(x, numpy.ndarray):
        return name_or_str(type(x)) + str(x.shape)
    elif isinstance(x, Sized):
        return name_or_str(type(x)) + f'({len(x)})'
    else:
        return name_or_str(type(x))


@exit_after(2)
def to_string_with_timeout(x):
    return str(x)


def nth_index(iterable, value, n):
    matches = (idx for idx, val in enumerate(iterable) if val == value)
    return next(islice(matches, n - 1, n), None)


def print_exc_plus():
    """
    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.
    """
    limit = FORMATTING_OPTIONS['MAX_LINE_LENGTH']
    max_newlines = FORMATTING_OPTIONS['MAX_NEWLINES']
    tb = sys.exc_info()[2]
    if numpy is not None:
        options = numpy.get_printoptions()
        numpy.set_printoptions(precision=2, edgeitems=2, floatmode='maxprec', threshold=20, linewidth=120)
    else:
        options = {}
    stack = []
    long_printed_objs: Dict[ID, Tuple[str, FrameType]] = {}

    while tb:
        stack.append(tb.tb_frame)
        tb = tb.tb_next
    for frame in stack:
        if frame is not stack[0]:
            print('-' * 40)
        try:
            print("Frame %s in %s at line %s" % (frame.f_code.co_name,
                                                 os.path.relpath(frame.f_code.co_filename),
                                                 frame.f_lineno))
        except ValueError:  # if path is not relative
            print("Frame %s in %s at line %s" % (frame.f_code.co_name,
                                                 frame.f_code.co_filename,
                                                 frame.f_lineno))
        for key, value in frame.f_locals.items():
            # We have to be careful not to cause a new error in our error
            # printer! Calling str() on an unknown object could cause an
            # error we don't want.

            # noinspection PyBroadException
            try:
                key_string = to_string_with_timeout(key)
            except KeyboardInterrupt:
                key_string = "<TIMEOUT WHILE PRINTING KEY>"
            except Exception:
                key_string = "<ERROR WHILE PRINTING KEY>"

            # noinspection PyBroadException
            try:
                type_as_string = type_string(value)
            except KeyboardInterrupt:
                type_as_string = "<TIMEOUT WHILE PRINTING TYPE>"
            except Exception as e:
                # noinspection PyBroadException
                try:
                    type_as_string = f"<{type(e).__name__} WHILE PRINTING TYPE>"
                except Exception:
                    type_as_string = "<ERROR WHILE PRINTING TYPE>"

            if id(value) in long_printed_objs:
                prev_key_string, prev_frame = long_printed_objs[id(value)]
                if prev_frame is frame:
                    print("\t%s is the same as '%s'" %
                          (key_string + ' : ' + type_as_string,
                           prev_key_string))
                else:
                    print("\t%s is the same as '%s' in frame %s in %s at line %s." %
                          (key_string + ' : ' + type_as_string,
                           prev_key_string,
                           prev_frame.f_code.co_name,
                           os.path.relpath(prev_frame.f_code.co_filename),
                           prev_frame.f_lineno))
                continue

            # noinspection PyBroadException
            try:
                value_string = to_string_with_timeout(value)
            except KeyboardInterrupt:
                value_string = "<TIMEOUT WHILE PRINTING VALUE>"
            except Exception:
                value_string = "<ERROR WHILE PRINTING VALUE>"
            line: str = '\t' + key_string + ' : ' + type_as_string + ' = ' + value_string
            if limit is not None and len(line) > limit:
                line = line[:limit - 1] + '...'
            if max_newlines is not None and line.count('\n') > max_newlines:
                line = line[:nth_index(line, '\n', max_newlines)].strip() + '... (' + str(
                    line[nth_index(line, '\n', max_newlines):].count('\n')) + ' more lines)'
            if len(line) > FORMATTING_OPTIONS['SHORT_LINE_THRESHOLD']:
                long_printed_objs[id(value)] = key_string, frame
            print(line)

    traceback.print_exc()
    if numpy is not None:
        numpy.set_printoptions(**options)


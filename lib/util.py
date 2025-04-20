import datetime
import functools
import gc
import json
import math
import os
import re
import sys
import threading
import time
from bisect import bisect_left
from enum import Enum
from itertools import chain, combinations
from math import log, isnan, nan, floor, log10, gcd
from shutil import copyfile
# noinspection PyUnresolvedReferences
from subprocess import check_output, PIPE, CalledProcessError
from threading import RLock
from types import FunctionType
from typing import Tuple

import hanging_threads
import tabulate

X = Y = Z = float


class KnownIssue(Exception):
    """
    This means the code is not working and should not be used but still too valuable to be deleted
    """
    pass


def powerset(iterable):
    """powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"""
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def rename(newname):
    def decorator(f):
        f.__name__ = newname
        return f

    return decorator


def local_timezone():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo


def print_attributes(obj, include_methods=False, ignore=None):
    if ignore is None:
        ignore = []
    for attr in dir(obj):
        if attr in ignore:
            continue
        if attr.startswith('_'):
            continue
        if not include_methods and callable(obj.__getattr__(attr)):
            continue
        print(attr, ':', obj.__getattr__(attr).__class__.__name__, ':', obj.__getattr__(attr))


def attr_dir(obj, include_methods=False, ignore=None):
    if ignore is None:
        ignore = []
    return {attr: obj.__getattr__(attr)
            for attr in dir(obj)
            if not attr.startswith('_') and (
                    include_methods or not callable(obj.__getattr__(attr))) and attr not in ignore}


def dummy_computation(*_args, **_kwargs):
    pass


def main_decorator(func):
    @functools.wraps(func)
    def wrapper_count_calls(*args, **kwargs):
        wrapper_count_calls.num_calls += 1
        print(f"Call {wrapper_count_calls.num_calls} of {func.__name__!r}")
        return func(*args, **kwargs)

    wrapper_count_calls.num_calls = 0
    return wrapper_count_calls


def backup_file(filename):
    copyfile(filename, filename + time.strftime("%Y%m%d-%H%M%S") + '.bak')


# noinspection SpellCheckingInspection
def my_tabulate(data, tablefmt='pipe', **params):
    if data == [] and 'headers' in params:
        data = [(None for _ in params['headers'])]
    tabulate.MIN_PADDING = 0
    return tabulate.tabulate(data, tablefmt=tablefmt, **params)


def ce_loss(y_true, y_predicted):
    return -(y_true * log(y_predicted) + (1 - y_true) * log(1 - y_predicted))


class DontSaveResultsError(Exception):
    pass


class UnknownTypeError(Exception):
    pass


try:
    import winsound as win_sound


    def beep(*args, **kwargs):
        win_sound.Beep(*args, **kwargs)
except ImportError:
    win_sound = None


    def beep(*_args, **_kwargs):
        pass


def round_to_digits(x, d):
    if x == 0:
        return 0
    if isnan(x):
        return nan
    try:
        return round(x, d - 1 - int(floor(log10(abs(x)))))
    except OverflowError:
        return x


def gc_if_memory_error(f, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except MemoryError:
        print('Starting garbage collector')
        gc.collect()
        return f(*args, **kwargs)


def round_to_closest_value(x, values, assume_sorted=False):
    if not assume_sorted:
        values = sorted(values)
    next_largest = bisect_left(values, x)  # binary search
    if next_largest == 0:
        return values[0]
    if next_largest == len(values):
        return values[-1]
    next_smallest = next_largest - 1
    smaller = values[next_smallest]
    larger = values[next_largest]
    if abs(smaller - x) < abs(larger - x):
        return smaller
    else:
        return larger


def assert_not_empty(x):
    assert len(x)
    return x


def validation_steps(validation_dataset_size, maximum_batch_size):
    batch_size = gcd(validation_dataset_size, maximum_batch_size)
    steps = validation_dataset_size // batch_size
    assert batch_size * steps == validation_dataset_size
    return batch_size, steps


def strptime(date_string, fmt):
    return datetime.datetime(*(time.strptime(date_string, fmt)[0:6]))


class PrintLineRLock(RLock().__class__):
    def __init__(self, *args, name='', **kwargs):
        # noinspection PyArgumentList
        super().__init__(*args, **kwargs)
        self.name = name

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        print(f'Trying to acquire Lock {self.name}')
        result = RLock.acquire(self, blocking, timeout)
        print(f'Acquired Lock {self.name}')
        return result

    def release(self) -> None:
        print(f'Trying to release Lock {self.name}')
        # noinspection PyNoneFunctionAssignment
        result = RLock.release(self)
        print(f'Released Lock {self.name}')
        return result

    def __enter__(self, *args, **kwargs):
        print('Trying to enter Lock')
        # noinspection PyArgumentList
        super().__enter__(*args, **kwargs)
        print('Entered Lock')

    def __exit__(self, *args, **kwargs):
        print('Trying to exit Lock')
        super().__exit__(*args, **kwargs)
        print('Exited Lock')


def fixed_get_current_frames():
    """Return current threads prepared for
    further processing.
    """
    threads = {thread.ident: thread for thread in threading.enumerate()}
    return {
        thread_id: {
            'frame': hanging_threads.thread2list(frame),
            'time': None,
            'id': thread_id,
            'name': threads[thread_id].name,
            'object': threads[thread_id]
        } for thread_id, frame in sys._current_frames().items()
        if thread_id in threads  # otherwise keyerrors might happen because of race conditions
    }


hanging_threads.get_current_frames = fixed_get_current_frames


def required_size_for_safe_rotation(base: Tuple[X, Y, Z], rotate_range_deg) -> Tuple[X, Y, Z]:
    if abs(rotate_range_deg) > 45:
        raise NotImplementedError
    if abs(rotate_range_deg) > 0:
        x_length = base[2] * math.sin(rotate_range_deg / 180 * math.pi) + base[1] * math.cos(
            rotate_range_deg / 180 * math.pi)
        y_length = base[2] * math.cos(rotate_range_deg / 180 * math.pi) + base[1] * math.sin(
            rotate_range_deg / 180 * math.pi)
        result = (base[0],
                  x_length,
                  y_length,)
    else:
        result = base
    return result


def print_progress_bar(iteration, total, prefix='Progress:', suffix='', decimals=1, length=50, fill='█',
                       print_eta=True):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:" + str(4 + decimals) + "." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    if getattr(print_progress_bar, 'last_printed_value', None) == (prefix, bar, percent, suffix):
        return
    print_progress_bar.last_printed_value = (prefix, bar, percent, suffix)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='')
    # Print New Line on Complete
    if iteration == total:
        print()


def copy_and_rename_method(func, new_name):
    funcdetails = [
        func.__code__,
        func.__globals__,
        func.__name__,
        func.__defaults__,
        func.__closure__
    ]
    old_name = func.__name__
    # copy
    # new_func = dill.loads(dill.dumps(func))
    new_func = FunctionType(*funcdetails)
    assert new_func is not funcdetails
    # rename
    new_func.__name__ = new_name
    assert func.__name__ is old_name
    return new_func


class LogicError(Exception):
    pass


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def shorten_name(name):
    name = re.sub(r'\s+', r' ', str(name))
    name = name.replace(', ', ',')
    name = name.replace(', ', ',')
    name = name.replace(' ', '_')
    return re.sub(r'([A-Za-z])[a-z]*_?', r'\1', str(name))


def val_fold_by_test_fold(test_fold, num_folds):
    return (test_fold + 1) % num_folds


def remove_duplicates_using_identity(xs):
    return list({id(x): x for x in xs}.values())


class EBC:
    def __eq__(self, other):
        return self is other or type(other) == type(self) and self.__dict__ == other.__dict__

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return f'{type(self).__name__}(**' + str(self.__dict__) + ')'

    def to_json(self):
        def _obj_to_json(obj):
            try:
                return obj.to_json()
            except AttributeError:
                return _list_to_json(obj) if isinstance(obj, list) else _dict_to_json(obj) if isinstance(obj, dict) else obj

        def _dict_to_json(d):
            return {_key_to_json(k): _obj_to_json(v)
                    for k, v in d.items()}

        def _list_to_json(xs):
            return [_obj_to_json(obj) for obj in xs]

        def _key_to_json(k) -> str:
            if isinstance(k,str):
                return k
            else:
                return json.dumps(_obj_to_json(k))

        json_info = {
            **self.__dict__,
            'type': type(self).__name__,
        }
        for k in json_info:
            json_info[k] = _obj_to_json(json_info[k])
        return json_info


class EBE(Enum):
    def __int__(self):
        return self.value

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __lt__(self, other):
        return list(type(self)).index(self) < list(type(self)).index(other)


def underscore(name):
    """
    source: https://stackoverflow.com/a/1176023
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def set_additional_keys(obj, json_data):
    additional_keys = {k for k in json_data if underscore(k) not in obj.__dict__}
    if len(additional_keys) > 0:
        print(f'{type(obj).__name__}: Storing additional keys:', additional_keys)
    obj.__dict__.update({underscore(k): json_data[k] for k in additional_keys})


def call_tool(command, cwd=None):
    try:
        print(f'Calling `{" ".join(command)}`...')
        sub_env = os.environ.copy()
        output: bytes = check_output(command, stderr=PIPE, env=sub_env, cwd=cwd)
        output: str = output.decode('utf-8', errors='ignore')
        return output
    except CalledProcessError as e:
        stdout = e.stdout.decode('utf-8', errors='ignore')
        stderr = e.stderr.decode('utf-8', errors='ignore')
        if len(stdout) == 0:
            print('stdout was empty.')
        else:
            print('stdout was: ')
            print(stdout)
        if len(stderr) == 0:
            print('stderr was empty.')
        else:
            print('stderr was: ')
            print(stderr)
        raise

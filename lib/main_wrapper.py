import functools
import inspect
import os
import time

from lib.print_exc_plus import print_exc_plus

try:
    import winsound as win_sound


    def beep(*args, **kwargs):
        win_sound.Beep(*args, **kwargs)
except ImportError:
    win_sound = None
    beep = lambda x, y: ...

ENABLE_PROFILING = False
LIMIT_MEMORY_USAGE = False


def start_profiling():
    try:
        import yappi
    except ModuleNotFoundError:
        return
    yappi.set_clock_type("wall")
    print(f'Starting yappi profiler.')
    yappi.start()


def profile_wall_time_instead_if_profiling():
    try:
        import yappi
    except ModuleNotFoundError:
        return
    currently_profiling = len(yappi.get_func_stats())
    if currently_profiling and yappi.get_clock_type() != 'wall':
        yappi.stop()
        print('Profiling wall time instead of cpu time.')
        yappi.clear_stats()
        yappi.set_clock_type("wall")
        yappi.start()

def dump_pstats_if_profiling(relating_to_object):
    try:
        import yappi
    except ModuleNotFoundError:
        return
    currently_profiling = len(yappi.get_func_stats())
    if currently_profiling:
        try:
            pstats_file = 'logs/profiling/' + os.path.normpath(inspect.getfile(relating_to_object)).replace(os.path.abspath('.'), '') + '.pstat'
        except AttributeError:
            print('WARNING: unable to set pstat file path for profiling.')
            return
        os.makedirs(os.path.dirname(pstats_file), exist_ok=True)
        yappi.get_func_stats()._save_as_PSTAT(pstats_file)
        print(f'Saved profiling log to {pstats_file}.')


class YappiProfiler():
    def __init__(self, relating_to_object):
        self.relating_to_object=relating_to_object

    def __enter__(self):
        start_profiling()
        profile_wall_time_instead_if_profiling()

    def __exit__(self, exc_type, exc_val, exc_tb):
        dump_pstats_if_profiling(self.relating_to_object)


def main_wrapper(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if ENABLE_PROFILING:
            start_profiling()
        if LIMIT_MEMORY_USAGE:
            MemoryLimiter.limit_memory_usage()
        start = time.perf_counter()
        # import lib.stack_tracer
        import __main__
        # does not help much
        # monitoring_thread = hanging_threads.start_monitoring(seconds_frozen=180, test_interval=1000)
        os.makedirs('logs', exist_ok=True)
        # stack_tracer.trace_start('logs/' + os.path.split(__main__.__file__)[-1] + '.html', interval=5)
        # faulthandler.enable()
        profile_wall_time_instead_if_profiling()

        # noinspection PyBroadException
        try:
            f(*args, **kwargs)
        except Exception:
            print_exc_plus()
        finally:
            total_time = time.perf_counter() - start
            # faulthandler.disable()
            # stack_tracer.trace_stop()
            frequency = 2000
            duration = 500
            beep(frequency, duration)
            if ENABLE_PROFILING:
                dump_pstats_if_profiling(f)
            print('Total time', total_time)

    return wrapper

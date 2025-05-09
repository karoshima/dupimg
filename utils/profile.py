import cProfile
import pstats
from functools import wraps
from datetime import datetime

# プロファイリング有効フラグ
profiling_enabled = False

def enable_profiling(enabled: bool) -> None:
    """
    プロファイリングを有効にするかどうかを設定する関数。
    :param enabled: プロファイリングを有効にする場合はTrue、無効にする場合はFalse
    """
    global profiling_enabled
    profiling_enabled = enabled

def profile(func):
    """
    プロファイリングを行うデコレータ。
    :param func: プロファイリング対象の関数
    :return: プロファイリング結果を返す関数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if profiling_enabled:
            profiler = cProfile.Profile()
            profiler.enable()
            result = func(*args, **kwargs)
            profiler.disable()
            # プロファイリング結果を表示する
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"profile_{func.__name__}_{timestamp}.prof"
            with open(filename, "w") as f:
                ps = pstats.Stats(profiler, stream=f).sort_stats(pstats.SortKey.CUMULATIVE)
                ps.print_stats()
            print(f"プロファイリング結果は {filename} に保存されました。")
            return result
        else:
            return func(*args, **kwargs)
    return wrapper

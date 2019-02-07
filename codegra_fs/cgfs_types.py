from mypy_extensions import TypedDict

PartialStat = TypedDict(
    'PartialStat',
    {
        'st_size': int,
        'st_atime': float,
        'st_mtime': float,
        'st_ctime': float,
        'st_uid': int,
        'st_gid': int,
    },
    total=True,
)

class FullStat(PartialStat, total=True):
    st_nlink: int
    st_mode: int

__APIHandlerResponse = TypedDict(
    '__APIHandlerResponse',
    {
        'ok': bool,
    },
    total=True,
)

class APIHandlerResponse(__APIHandlerResponse, total=False):
    error: str
    data: str

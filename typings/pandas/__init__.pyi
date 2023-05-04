from typing import (
    Generic,
    Hashable,
    Iterable,
    Literal,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from pandas._libs import lib
from pandas._typing import (
    FilePath,
)

__all__ = ["DataFrame", "Series", "read_csv"]

# Not sure if this is comprehensive, as Pandas doesn't document this anywhere.
# I think this is where they infer types:
# https://github.com/pandas-dev/pandas/blob/042ebab0248193b343ede6d87397871bf8931fca/pandas/_libs/lib.pyx#L2394
# NOTE: For empty fields (eg ,,), Julia CSV.jl parses them as missing, while
# Pandas parses them as NaN
CsvInferTypes = Union[str, int, float, bool]

T = TypeVar("T")

class DataFrame(Generic[T]):
    columns: Sequence[Hashable]
    shape: Tuple[int, int]

    def iterrows(self) -> Iterable[tuple[Hashable, Series[T]]]: ...
    def nunique(self) -> Series[Hashable]: ...

class Series(Generic[T]):
    def __getitem__(self, key: str) -> T: ...

# default case -> DataFrame
def read_csv(
    filepath_or_buffer: FilePath,
    *,
    delimiter: str | None | lib.NoDefault = ...,
    header: int | Sequence[int] | None | Literal["infer"] = ...,
    nrows: int | None = ...,
) -> DataFrame[CsvInferTypes]: ...
def concat(
    objs: Iterable[DataFrame[T]],
    *,
    axis: Literal[0, 1, "index", "columns"] = 0,
) -> DataFrame[T]: ...

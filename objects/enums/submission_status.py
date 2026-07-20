from enum import IntEnum, unique


@unique
class SubmissionStatus(IntEnum):
    FAILED = 0
    SUBMITTED = 1
    BEST = 2

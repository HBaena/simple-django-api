from dataclasses import dataclass

@dataclass(frozen=True)
class StatusMsg:
    ERROR: str = 'error'
    OK: str = 'ok'

@dataclass(frozen=True)
class ErrorMsg:
    INVALID_VALUE: str = 'invalid value for ({})'
    VALIDATION: str = 'validation error'
    NOT_FOUND: str = 'not found'

@dataclass(frozen=True)
class SuccessMsg:
    CREATED: str = 'created'

@dataclass(frozen=True)
class InfoMsg:
    AVAILABLE_VALUES: str = 'Available values are ({})'

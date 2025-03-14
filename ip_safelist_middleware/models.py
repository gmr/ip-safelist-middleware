import enum
import re

import pydantic


class ListType(enum.Enum):
    aws = 'aws'
    env = 'env'


class ListItem(pydantic.BaseModel):
    """Configuration entry for a path and the type of list to use"""
    path: str
    type: ListType | list[ListType]
    _compiled: re.Pattern | None = pydantic.PrivateAttr(default=None)

    @property
    def regex(self) -> re.Pattern:
        """Return a regex pattern for the blocklist entry."""
        if not self._compiled:
            self._compiled = re.compile(self.path)
        return self._compiled
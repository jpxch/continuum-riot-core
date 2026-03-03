from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.dialects.postgresql import JSONB


class JSONType(TypeDecorator):
    """
    Dialect-aware JSON type.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
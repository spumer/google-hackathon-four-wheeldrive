import typing

import peewee as pw
from playhouse.pool import PooledPostgresqlExtDatabase

from .config import config

database = PooledPostgresqlExtDatabase(
    **{
        'max_connections': 10,
        'database': config.DB_NAME,
        'user': config.DB_USER,
        'password': config.DB_PASSWORD,
        'host': config.DB_HOST,
        'port': config.DB_PORT,
        'autorollback': True,
    }
)


class Metadata(pw.Metadata):
    def __init__(self, model, abstract=False, **kwargs):
        super().__init__(model, **kwargs)
        self.abstract = abstract


ModelType = typing.TypeVar('ModelType', bound='BaseModel')


class MultipleObjectsReturned(Exception):
    ...


class BaseModel(pw.Model):
    class Meta:
        model_metadata_class = Metadata
        abstract = True
        database = database

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._meta.abstract:
            abstract_models.append(cls)

        exc_name = '%sMultipleObjectsReturned' % cls.__name__
        exc_attrs = {'__module__': cls.__module__}
        exception_class = type(exc_name, (MultipleObjectsReturned,), exc_attrs)
        cls.MultipleObjectsReturned = exception_class

    @classmethod
    def get_meta(cls) -> Meta.model_metadata_class:
        return cls._meta

    @classmethod
    def get_exact(cls, *query, **filters) -> ModelType:
        """Like Django `.objects.get` ensure only one instance exists in database"""

        sq = cls.select()
        if query:
            # Handle simple lookup using just the primary key.
            if len(query) == 1 and isinstance(query[0], int):
                sq = sq.where(cls._meta.primary_key == query[0])
            else:
                sq = sq.where(*query)

        if filters:
            sq = sq.filter(**filters)

        sq._cursor_wrapper = None
        result = sq.execute(database)

        num = len(result)
        if num == 1:
            return result[0]

        if not num:
            sql, params = sq.sql()
            raise cls.DoesNotExist(
                '%s instance matching query does '
                'not exist:\nSQL: %s\nParams: %s' %
                (cls.get_meta().model.__name__, sql, params),
            )

        raise cls.MultipleObjectsReturned(
            'get() returned more than one %s -- it returned %s!' %
            (cls.get_meta().model.__name__, num),
        )


abstract_models: typing.List[typing.Type[BaseModel]] = [BaseModel]

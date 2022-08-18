from sqlalchemy import Column, String, Sequence, Integer
from sqlalchemy.orm import registry

mapper_registry = registry()
BASE = mapper_registry.generate_base()


@mapper_registry.mapped
class Item:
    """ ORM model of Items table """
    __tablename__ = 'items'
    seq = Sequence('id_seq', start=1)
    id = Column('id', Integer, seq, server_default=seq.next_value(), primary_key=True, comment='primary key')
    title = Column('title', String, comment='name of the element from sreality.cz page')
    image = Column('image', String, comment='image url reference')

from sqlalchemy import (TIMESTAMP, Column, Index, Integer, Numeric, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class CandleOHLC(Base):
    __tablename__ = 'candle_ohlc'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    currency_pair = Column(Text, nullable=False)
    period = Column(Text, nullable=False)
    time = Column(TIMESTAMP, nullable=False)
    open = Column(Numeric(24, 8), nullable=False)
    high = Column(Numeric(24, 8), nullable=False)
    low = Column(Numeric(24, 8), nullable=False)
    close = Column(Numeric(24, 8), nullable=False)

    __table_args__ = (
        Index("ui_candle_ohlc_01", currency_pair, period, time, unique=True),
    )


class DBContext:

    def __init__(self, connection_str: str = "sqlite:///mt.sqlite"):
        engine = create_engine(connection_str, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self._session = Session()

    @property
    def session(self):
        return self._session

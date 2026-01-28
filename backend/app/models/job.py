from datetime import date

from sqlmodel import Field, SQLModel


class Job(SQLModel, table=True):
    __tablename__ = "job"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    company: str = Field()
    url: str = Field(unique=True)
    location: str = Field()
    date_posted: date | None = Field(default_factory=None)
    expires: date = Field()
    img: str = Field()
    source: str = Field()

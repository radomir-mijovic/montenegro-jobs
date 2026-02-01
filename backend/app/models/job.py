from datetime import date

from sqlmodel import Field, Relationship, SQLModel


class CategoryJobLink(SQLModel, table=True):
    category_id: int | None = Field(default=None, foreign_key="category.id", primary_key=True)
    job_id: int | None = Field(default=None, foreign_key="job.id", primary_key=True)


class Category(SQLModel, table=True):
    __tablename__ = "category"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field()
    jobs: list["Job"] = Relationship(
        back_populates="categories", link_model=CategoryJobLink
    )


class Job(SQLModel, table=True):
    __tablename__ = "job"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    company: str = Field()
    url: str = Field(unique=True)
    location: str = Field()
    date_posted: date | None = Field(default_factory=None)
    expires: date | None = Field(default_factory=None)
    img: str = Field()
    source: str = Field()
    categories: list["Category"] = Relationship(
        back_populates="jobs", link_model=CategoryJobLink
    )

#!/usr/bin/env python3
import asyncio

from oxen.models import Model
from oxen.fields.data import CharField, IntegerField
from oxen.fields.relational import ForeignKeyField
from oxen.engine import connect, disconnect


class Author(Model):
    name = CharField(max_length=100, null=False)

    class Meta:
        table_name = "authors"


class Book(Model):
    title = CharField(max_length=200, null=False)
    pages = IntegerField(null=False, default=0)
    author = ForeignKeyField(Author, related_name="books", null=False)

    class Meta:
        table_name = "books"


async def main():
    engine = await connect("sqlite:////Users/developer/Desktop/OxenORM/smoke_test.db")

    # Bind engine to our models and auto-sync minimal schema
    for m in (Author, Book):
        m._set_rust_engine(engine)

    # Create rows
    a1 = await Author.create(name="Jane Austen")
    a2 = await Author.create(name="Mark Twain")
    await Book.create(title="Pride and Prejudice", pages=432, author=a1.pk)
    await Book.create(title="Emma", pages=378, author=a1.pk)
    await Book.create(title="Adventures of Huckleberry Finn", pages=366, author=a2.pk)

    # select_related join + order/limit
    books = await Book.select_related("author").order_by("id").limit(5)
    print("\n-- select_related results --")
    for b in books:
        # access related FK id directly; select_related makes join available for future enhancements
        print(f"{b.title} (author_id={getattr(b.author, 'pk', b.author)})")

    # values_list (flat)
    ids = await Book.filter(title__icontains="a").order_by("id").values_list("id", flat=True)
    print("\n-- values_list ids --")
    print(ids)

    # values with aliases
    rows = await Book.filter(pages__gte=300).order_by("id").values(t="title")
    print("\n-- values (aliased) --")
    print(rows)

    await disconnect(engine)


if __name__ == "__main__":
    asyncio.run(main())



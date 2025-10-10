import os
import asyncio
from typing import List

from oxen.engine import connect, disconnect
from oxen.schema import sync_model
from .models import User, Post, Comment


DB_URL = os.environ.get("OXEN_BLOG_DB", "sqlite:////Users/developer/Desktop/OxenORM/smoke_test.db")


async def seed() -> None:
    engine = await connect(DB_URL)
    # Bind and ensure schema
    for m in (User, Post, Comment):
        m._set_rust_engine(engine)
        sync_model(engine, m)

    # Users
    alice, _ = await User.get_or_create(defaults={"display_name": "Alice"}, username="alice")
    bob, _ = await User.get_or_create(defaults={"display_name": "Bob"}, username="bob")
    carol, _ = await User.get_or_create(defaults={"display_name": "Carol"}, username="carol")

    # Posts (explicit create to ensure FK binding is set correctly)
    try:
        p1 = await Post.create(title="First Post", body="Hello World", author=alice)
    except Exception:
        p1, _ = await Post.get_or_create(title="First Post", defaults={"body": "Hello World", "author": alice.pk})

    try:
        p2 = await Post.create(title="Oxen Speed", body="Oxen is fast", author=alice)
    except Exception:
        p2, _ = await Post.get_or_create(title="Oxen Speed", defaults={"body": "Oxen is fast", "author": alice.pk})

    try:
        p3 = await Post.create(title="Stack Notes", body="SQL + Rust + Python", author=bob)
    except Exception:
        p3, _ = await Post.get_or_create(title="Stack Notes", defaults={"body": "SQL + Rust + Python", "author": bob.pk})

    # Comments (explicit create for robust FK assignment)
    try:
        await Comment.create(post=p1, author=bob, body="Nice!")
    except Exception:
        try:
            await Comment.get_or_create(post=p1.pk, defaults={"author": bob.pk, "body": "Nice!"})
        except Exception:
            pass

    try:
        await Comment.create(post=p1, author=carol, body="Great read")
    except Exception:
        try:
            await Comment.get_or_create(post=p1.pk, defaults={"author": carol.pk, "body": "Great read"})
        except Exception:
            pass

    try:
        await Comment.create(post=p3, author=alice, body="Welcome")
    except Exception:
        try:
            await Comment.get_or_create(post=p3.pk, defaults={"author": alice.pk, "body": "Welcome"})
        except Exception:
            pass

    # Summary output
    users = await User._db_queryset().order_by("id").values(id="id", username="username", display_name="display_name")
    posts = await Post._db_queryset().order_by("id").values(id="id", title="title", author_id="author")
    comments = await Comment._db_queryset().order_by("id").values(id="id", post_id="post", author_id="author", body="body")

    print("Seed complete:")
    print(f"  Users:    {len(users)} -> {users}")
    print(f"  Posts:    {len(posts)} -> {posts}")
    print(f"  Comments: {len(comments)} -> {comments}")

    await disconnect(engine)


if __name__ == "__main__":
    asyncio.run(seed())



import os
import sys
import time
import argparse

# Ensure project root on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DB_URL = os.environ.get("OXEN_BLOG_DB", "sqlite:////Users/developer/Desktop/OxenORM/smoke_test.db")


def bench_oxen(iterations: int = 500) -> dict:
    import asyncio
    from examples.blog_app.models import User, Post
    from oxen.engine import connect, disconnect
    from oxen.schema import sync_model

    async def run():
        engine = await connect(DB_URL)
        for m in (User, Post):
            m._set_rust_engine(engine)
            sync_model(engine, m)

        # read_one: get user by pk=1 (or first existing id)
        start = time.time()
        for _ in range(iterations):
            try:
                _ = await User.get(pk=1)
            except Exception:
                pass
        read_one_s = time.time() - start

        # read_many: fetch 10 posts values
        start = time.time()
        for _ in range(iterations):
            _ = await Post._db_queryset().order_by("id").limit(10).values(id="id", title="title", author_id="author")
        read_many_s = time.time() - start

        await disconnect(engine)
        return {
            "read_one_qps": iterations / max(read_one_s, 1e-9),
            "read_many_qps": iterations / max(read_many_s, 1e-9),
        }

    return asyncio.run(run())


def bench_sqlalchemy(iterations: int = 500) -> dict:
    # Lazy import; SQLAlchemy may not be installed
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, text
    from sqlalchemy.orm import declarative_base, sessionmaker, relationship

    # SQLite URL must be converted for SQLAlchemy
    sqla_url = DB_URL.replace("sqlite:////", "sqlite:////")
    engine = create_engine(sqla_url, future=True)
    Base = declarative_base()

    class User(Base):
        __tablename__ = "blog_users"
        id = Column(Integer, primary_key=True)
        username = Column(String)
        display_name = Column(String)
        created_at = Column(DateTime)

    class Post(Base):
        __tablename__ = "blog_posts"
        id = Column(Integer, primary_key=True)
        title = Column(String)
        body = Column(String)
        author = Column(Integer, ForeignKey("blog_users.id"))
        created_at = Column(DateTime)
        user = relationship(User, primaryjoin=author == User.id)

    Session = sessionmaker(bind=engine, future=True)
    sess = Session()

    # read_one
    start = time.time()
    for _ in range(iterations):
        _ = sess.get(User, 1)
    read_one_s = time.time() - start

    # read_many (LIMIT 10)
    start = time.time()
    for _ in range(iterations):
        _ = sess.query(Post.id, Post.title, Post.author).order_by(Post.id).limit(10).all()
    read_many_s = time.time() - start

    sess.close()
    engine.dispose()
    return {
        "read_one_qps": iterations / max(read_one_s, 1e-9),
        "read_many_qps": iterations / max(read_many_s, 1e-9),
    }


def bench_django(iterations: int = 500) -> dict:
    # Configure Django on the fly with unmanaged models that map to existing tables
    import django
    from django.conf import settings as dj_settings

    if not dj_settings.configured:
        dj_settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": DB_URL.replace("sqlite:////", "/"),
                }
            },
            TIME_ZONE="UTC",
            USE_TZ=True,
        )
    django.setup()

    from django.db import models

    class User(models.Model):
        id = models.AutoField(primary_key=True)
        username = models.CharField(max_length=50)
        display_name = models.CharField(max_length=100)
        created_at = models.DateTimeField()

        class Meta:
            managed = False
            db_table = "blog_users"

    class Post(models.Model):
        id = models.AutoField(primary_key=True)
        title = models.CharField(max_length=200)
        body = models.TextField()
        author = models.IntegerField()
        created_at = models.DateTimeField()

        class Meta:
            managed = False
            db_table = "blog_posts"

    # read_one
    start = time.time()
    for _ in range(iterations):
        try:
            _ = User.objects.filter(id=1).first()
        except Exception:
            pass
    read_one_s = time.time() - start

    # read_many (LIMIT 10)
    start = time.time()
    for _ in range(iterations):
        list(User.objects.order_by("id").all()[:10])
    read_many_s = time.time() - start

    return {
        "read_one_qps": iterations / max(read_one_s, 1e-9),
        "read_many_qps": iterations / max(read_many_s, 1e-9),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter", type=int, default=500)
    parser.add_argument("--orms", type=str, default="oxen,sqlalchemy,django")
    args = parser.parse_args()

    orms = [s.strip() for s in args.orms.split(",") if s.strip()]

    results = {}
    for orm in orms:
        try:
            if orm == "oxen":
                results["Oxen"] = bench_oxen(args.iter)
            elif orm == "sqlalchemy":
                results["SQLAlchemy"] = bench_sqlalchemy(args.iter)
            elif orm == "django":
                results["Django"] = bench_django(args.iter)
        except Exception as e:
            results[orm] = {"error": str(e)}

    # Print table
    print("\nModel Read QPS (iterations=%d)" % args.iter)
    print("ORM           | read_one | read_many")
    print("------------- | -------- | ---------")
    for name in ("Oxen", "SQLAlchemy", "Django"):
        r = results.get(name)
        if not r or "error" in r:
            print(f"{name:<13} | ERROR    | ERROR     ")
            continue
        print(f"{name:<13} | {r['read_one_qps']:8.1f} | {r['read_many_qps']:9.1f}")

    # Deltas vs Oxen
    if "Oxen" in results:
        ox = results["Oxen"]
        print("\nDelta vs Oxen (x = competitor / Oxen)")
        for name in ("SQLAlchemy", "Django"):
            r = results.get(name)
            if not r or "error" in r:
                print(f"{name:<13} | ERROR")
                continue
            d1 = (r["read_one_qps"] / ox["read_one_qps"]) if ox["read_one_qps"] else 0
            d2 = (r["read_many_qps"] / ox["read_many_qps"]) if ox["read_many_qps"] else 0
            print(f"{name:<13} | read_one: {d1:.2f}x, read_many: {d2:.2f}x")


if __name__ == "__main__":
    main()



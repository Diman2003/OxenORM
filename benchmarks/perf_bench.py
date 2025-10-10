import os
import time
import json
import asyncio
from dataclasses import dataclass
from typing import Callable, Awaitable, Any, Dict, List


DB_URL = os.environ.get("OXEN_BENCH_DB", "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")
ITER = int(os.environ.get("OXEN_BENCH_ITER", "500"))


@dataclass
class BenchResult:
    name: str
    iterations: int
    elapsed_s: float
    qps: float


def measure(name: str, fn: Callable[[], Any], iterations: int) -> BenchResult:
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - start
    qps = iterations / elapsed if elapsed > 0 else 0.0
    return BenchResult(name, iterations, elapsed, qps)


async def measure_async(name: str, fn: Callable[[], Awaitable[Any]], iterations: int) -> BenchResult:
    start = time.perf_counter()
    for _ in range(iterations):
        await fn()
    elapsed = time.perf_counter() - start
    qps = iterations / elapsed if elapsed > 0 else 0.0
    return BenchResult(name, iterations, elapsed, qps)


# --- Tortoise ORM models (module-level for discovery) ---
try:
    from tortoise import fields as t_fields  # type: ignore
    from tortoise.models import Model as TModel  # type: ignore

    class TUser(TModel):
        id = t_fields.IntField(pk=True)
        username = t_fields.CharField(max_length=50)
        display_name = t_fields.CharField(max_length=100)

        class Meta:
            table = "blog_users"

    class TPost(TModel):
        id = t_fields.IntField(pk=True)
        title = t_fields.CharField(max_length=200)
        body = t_fields.TextField()
        author = t_fields.IntField()

        class Meta:
            table = "blog_posts"
except Exception:
    TUser = None  # type: ignore
    TPost = None  # type: ignore


# Oxen
async def bench_oxen() -> Dict[str, Any]:
    from oxen.engine import connect, disconnect
    from examples.blog_app.models import User, Post
    from oxen.schema import sync_model
    import os

    e = await connect(DB_URL)
    for m in (User, Post):
        m._set_rust_engine(e)
        sync_model(e, m)

    # Default hot path: tuples (avoid hydration)
    async def read_one():
        await User._db_queryset().filter(username="alice").only("id", "username").as_tuples()

    async def read_many():
        await Post._db_queryset().order_by("id").only("id", "title").limit(50).as_tuples()

    # Tuple fast paths (avoid hydration cost on hot reads)
    async def read_one_tuples():
        rows = await User._db_queryset().filter(username="alice").only("id", "username").as_tuples()
        return rows

    async def read_many_tuples():
        rows = await Post._db_queryset().order_by("id").only("id", "title").limit(50).as_tuples()
        return rows

    # Hydrated models (for comparison)
    async def read_one_models():
        await User._db_queryset().filter(username="alice").first()

    async def read_many_models():
        await Post._db_queryset().order_by("id").limit(50)

    r1 = await measure_async("oxen_read_one", read_one, ITER)
    r2 = await measure_async("oxen_read_many", read_many, ITER)
    r3 = await measure_async("oxen_read_one_tuples", read_one_tuples, ITER)
    r4 = await measure_async("oxen_read_many_tuples", read_many_tuples, ITER)
    r5 = await measure_async("oxen_read_one_models", read_one_models, ITER)
    r6 = await measure_async("oxen_read_many_models", read_many_models, ITER)
    await disconnect(e)
    return {"oxen": [r1.__dict__, r2.__dict__, r3.__dict__, r4.__dict__, r5.__dict__, r6.__dict__]}


async def bench_oxen_tuple_only() -> Dict[str, Any]:
    from oxen.engine import connect, disconnect
    from examples.blog_app.models import User, Post
    from oxen.schema import sync_model

    e = await connect(DB_URL)
    for m in (User, Post):
        m._set_rust_engine(e)
        sync_model(e, m)

    async def read_one_tuple_once():
        rows = await User._db_queryset().filter(username="alice").only("id", "username").as_tuples()
        return rows

    async def read_many_tuple_once():
        rows = await Post._db_queryset().order_by("id").only("id", "title").limit(50).as_tuples()
        return rows

    r1 = await measure_async("oxen_tuple_read_one", read_one_tuple_once, ITER)
    r2 = await measure_async("oxen_tuple_read_many", read_many_tuple_once, ITER)
    await disconnect(e)
    return {"oxen_tuple": [r1.__dict__, r2.__dict__]}


# SQLAlchemy
def bench_sqlalchemy() -> Dict[str, Any]:
    import sqlalchemy as sa
    from sqlalchemy.orm import declarative_base, Session

    engine = sa.create_engine(DB_URL)
    Base = declarative_base()

    class SAUser(Base):
        __tablename__ = "blog_users"
        id = sa.Column(sa.Integer, primary_key=True)
        username = sa.Column(sa.String)
        display_name = sa.Column(sa.String)

    class SAPost(Base):
        __tablename__ = "blog_posts"
        id = sa.Column(sa.Integer, primary_key=True)
        title = sa.Column(sa.String)
        body = sa.Column(sa.Text)
        author = sa.Column(sa.Integer, sa.ForeignKey("blog_users.id"))
        user = sa.orm.relationship("SAUser", backref="posts")

    Base.metadata.create_all(engine)
    session = Session(engine)

    def read_one():
        session.query(SAUser).filter(SAUser.username == "alice").first()

    def read_many():
        session.query(SAPost).order_by(SAPost.id).limit(50).all()

    r1 = measure("sqlalchemy_read_one", read_one, ITER)
    r2 = measure("sqlalchemy_read_many", read_many, ITER)
    session.close()
    engine.dispose()
    return {"sqlalchemy": [r1.__dict__, r2.__dict__]}


# Tortoise
async def bench_tortoise() -> Dict[str, Any]:
    from tortoise import Tortoise
    tortoise_url = DB_URL.replace("postgresql://", "postgres://")
    await Tortoise.init(db_url=tortoise_url, modules={"models": [__name__]})
    await Tortoise.generate_schemas()

    async def read_one():
        await TUser.filter(username="alice").first()

    async def read_many():
        await TPost.all().limit(50)

    r1 = await measure_async("tortoise_read_one", read_one, ITER)
    r2 = await measure_async("tortoise_read_many", read_many, ITER)
    await Tortoise.close_connections()
    return {"tortoise": [r1.__dict__, r2.__dict__]}


# Extended benches: writes, joins, window
async def bench_oxen_extended() -> Dict[str, Any]:
    from oxen.engine import connect, disconnect
    from examples.blog_app.models import User, Post
    from oxen.schema import sync_model
    import json as _json
    import uuid

    e = await connect(DB_URL)
    for m in (User, Post):
        m._set_rust_engine(e)
        sync_model(e, m)

    # Reset tables to avoid unique collisions in repeated runs (truncate both at once if possible)
    try:
        await e.execute_query(
            f'TRUNCATE TABLE "{Post._meta.table_name}", "{User._meta.table_name}" RESTART IDENTITY CASCADE'
        )
    except Exception:
        # Fallback: delete posts then users
        try:
            await e.execute_query(f'DELETE FROM "{Post._meta.table_name}"')
        except Exception:
            pass
        try:
            await e.execute_query(f'DELETE FROM "{User._meta.table_name}"')
        except Exception:
            pass

    users = [User(username=f"bench_{uuid.uuid4().hex}", display_name="B") for _ in range(200)]

    async def bulk_insert_copy_txn():
        # Single transaction: TRUNCATE then COPY insert via IR
        try:
            await e.execute_query("BEGIN")
        except Exception:
            pass
        try:
            try:
                await e.execute_query(
                    f'TRUNCATE TABLE "{Post._meta.table_name}", "{User._meta.table_name}" RESTART IDENTITY CASCADE'
                )
            except Exception:
                # fallback deletes
                try:
                    await e.execute_query(f'DELETE FROM "{Post._meta.table_name}"')
                except Exception:
                    pass
                try:
                    await e.execute_query(f'DELETE FROM "{User._meta.table_name}"')
                except Exception:
                    pass

            eng = getattr(e, '_rust_engine', None)
            rows = [{"username": u.username, "display_name": u.display_name} for u in users]
            if eng is not None:
                ir = {
                    'dialect': 'postgres',
                    'table': User._meta.table_name,
                    'action': 'insert',
                    'rows': rows,
                    'returning': ['id'],
                }
                await asyncio.get_running_loop().run_in_executor(None, eng.execute_ir_json, _json.dumps(ir))
            else:
                # fallback
                await User.bulk_create(users)
        except Exception:
            try:
                await e.execute_query("ROLLBACK")
            except Exception:
                pass
            raise
        else:
            try:
                await e.execute_query("COMMIT")
            except Exception:
                pass

    async def bulk_update():
        await Post._db_queryset().update(title="bench")

    async def join_select_related():
        await Post._db_queryset().select_related('author').limit(100)

    async def window_count():
        try:
            from oxen.expressions import WindowFunction
            await Post._db_queryset().window(num_posts=WindowFunction('COUNT(*)', partition_by=['author']))
        except Exception:
            rows = await Post._db_queryset().values_list("author")
            counts: Dict[int, int] = {}
            for r in rows:
                a = int(r[0]) if isinstance(r, (list, tuple)) else int(r)
                counts[a] = counts.get(a, 0) + 1

    r0 = await measure_async("oxen_bulk_insert_copy_200", bulk_insert_copy_txn, 1)
    # Skip separate non-COPY bulk insert to avoid duplicate runs after truncate
    # r1 = await measure_async("oxen_bulk_insert_200", bulk_insert, 1)
    r2 = await measure_async("oxen_bulk_update_all", bulk_update, 1)
    r3 = await measure_async("oxen_join_select_related", join_select_related, ITER)
    r4 = await measure_async("oxen_window_count", window_count, ITER)
    await disconnect(e)
    return {"oxen_ext": [r0.__dict__, r2.__dict__, r3.__dict__, r4.__dict__]}


async def bench_oxen_columnar() -> Dict[str, Any]:
    from oxen.engine import connect, disconnect
    from examples.blog_app.models import Post
    from oxen.schema import sync_model
    import os

    e = await connect(DB_URL)
    Post._set_rust_engine(e)
    sync_model(e, Post)

    async def scan_columns():
        try:
            import importlib
            import os as _os
            _os.environ.setdefault('OXEN_ARROW', '1')
            importlib.import_module('pyarrow')
            _ = await Post._db_queryset().order_by("id").only("id", "title").as_arrow()
            return _
        except Exception:
            cols = await Post._db_queryset().order_by("id").only("id", "title").as_columns()
            return cols

    r = await measure_async("oxen_scan_columns", scan_columns, ITER)
    await disconnect(e)
    return {"oxen_columnar": [r.__dict__]}


def bench_sqlalchemy_extended() -> Dict[str, Any]:
    import sqlalchemy as sa
    from sqlalchemy.orm import declarative_base, Session, joinedload
    import uuid

    engine = sa.create_engine(DB_URL)
    Base = declarative_base()

    class SAUser(Base):
        __tablename__ = "blog_users"
        id = sa.Column(sa.Integer, primary_key=True)
        username = sa.Column(sa.String)
        display_name = sa.Column(sa.String)

    class SAPost(Base):
        __tablename__ = "blog_posts"
        id = sa.Column(sa.Integer, primary_key=True)
        title = sa.Column(sa.String)
        body = sa.Column(sa.Text)
        author = sa.Column(sa.Integer, sa.ForeignKey("blog_users.id"))
        user = sa.orm.relationship("SAUser", backref="posts")

    Base.metadata.create_all(engine)
    session = Session(engine)

    def bulk_insert():
        objs = [SAUser(username=f"sa_{uuid.uuid4().hex[:8]}", display_name="B") for _ in range(200)]
        session.bulk_save_objects(objs)
        session.commit()

    def bulk_update():
        session.query(SAPost).update({SAPost.title: "bench"})
        session.commit()

    def join_eager():
        session.query(SAPost).options(joinedload(SAPost.user)).limit(100).all()

    def window_count():
        from sqlalchemy import func, over
        session.query(over(func.count(), partition_by=SAPost.author)).limit(100).all()

    r1 = measure("sa_bulk_insert_200", bulk_insert, 1)
    r2 = measure("sa_bulk_update_all", bulk_update, 1)
    r3 = measure("sa_join_eager", join_eager, ITER)
    r4 = measure("sa_window_count", window_count, ITER)
    session.close()
    engine.dispose()
    return {"sqlalchemy_ext": [r1.__dict__, r2.__dict__, r3.__dict__, r4.__dict__]}


async def bench_tortoise_extended() -> Dict[str, Any]:
    from tortoise import Tortoise
    from tortoise.functions import Count
    import uuid
    tortoise_url = DB_URL.replace("postgresql://", "postgres://")
    await Tortoise.init(db_url=tortoise_url, modules={"models": [__name__]})
    await Tortoise.generate_schemas()

    async def bulk_insert():
        objs = [TUser(username=f"t_{uuid.uuid4().hex[:8]}", display_name="B") for _ in range(200)]
        await TUser.bulk_create(objs)

    async def bulk_update():
        await TPost.all().update(title="bench")

    async def join_select_related():
        await TPost.all().limit(100)

    async def aggregate_count():
        await TPost.all().group_by('author').annotate(num_posts=Count('id')).limit(100).values('author', 'num_posts')

    r1 = await measure_async("tortoise_bulk_insert_200", bulk_insert, 1)
    r2 = await measure_async("tortoise_bulk_update_all", bulk_update, 1)
    r3 = await measure_async("tortoise_read_many_again", join_select_related, ITER)
    r4 = await measure_async("tortoise_aggregate_count", aggregate_count, ITER)
    await Tortoise.close_connections()
    return {"tortoise_ext": [r1.__dict__, r2.__dict__, r3.__dict__, r4.__dict__]}


# Django
async def bench_django() -> Dict[str, Any]:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            INSTALLED_APPS=[
                'benchmarks.django_app',
            ],
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': 'oxenorm',
                    'USER': 'oxenorm',
                    'PASSWORD': 'oxenorm',
                    'HOST': 'localhost',
                    'PORT': '5432',
                }
            },
            TIME_ZONE='UTC',
            USE_TZ=True,
        )
        django.setup()
    from benchmarks.django_app.models import DJUser, DJPost

    # Run synchronously using thread executor to avoid async context issues
    loop = asyncio.get_running_loop()

    def read_one_sync():
        DJUser.objects.filter(username='alice').first()

    def read_many_sync():
        list(DJPost.objects.order_by('id')[:50])

    r1 = await loop.run_in_executor(None, lambda: measure('django_read_one', read_one_sync, ITER))
    r2 = await loop.run_in_executor(None, lambda: measure('django_read_many', read_many_sync, ITER))
    return {'django': [r1.__dict__, r2.__dict__]}


async def bench_django_extended() -> Dict[str, Any]:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            INSTALLED_APPS=[
                'benchmarks.django_app',
            ],
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': 'oxenorm',
                    'USER': 'oxenorm',
                    'PASSWORD': 'oxenorm',
                    'HOST': 'localhost',
                    'PORT': '5432',
                }
            },
            TIME_ZONE='UTC',
            USE_TZ=True,
        )
        django.setup()
    from benchmarks.django_app.models import DJUser, DJPost
    from django.db.models import Count
    import uuid

    loop = asyncio.get_running_loop()

    def bulk_insert_sync():
        DJUser.objects.bulk_create([
            DJUser(username=f'dj_{uuid.uuid4().hex[:8]}', display_name='B') for _ in range(200)
        ])

    def bulk_update_sync():
        DJPost.objects.all().update(title='bench')

    def join_select_related_sync():
        list(DJPost.objects.select_related('author').all()[:100])

    def aggregate_count_sync():
        list(DJPost.objects.values('author').annotate(num_posts=Count('id'))[:100])

    r1 = await loop.run_in_executor(None, lambda: measure('django_bulk_insert_200', bulk_insert_sync, 1))
    r2 = await loop.run_in_executor(None, lambda: measure('django_bulk_update_all', bulk_update_sync, 1))
    r3 = await loop.run_in_executor(None, lambda: measure('django_join_select_related', join_select_related_sync, ITER))
    r4 = await loop.run_in_executor(None, lambda: measure('django_aggregate_count', aggregate_count_sync, ITER))
    return {'django_ext': [r1.__dict__, r2.__dict__, r3.__dict__, r4.__dict__]}


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for r in results:
        out.update(r)
    return out


async def main() -> None:
    results: List[Dict[str, Any]] = []
    only_tuples = os.environ.get('OXEN_ONLY_TUPLES', '0') == '1'
    if only_tuples:
        results.append(await bench_oxen_tuple_only())
    else:
        results.append(await bench_oxen())
        results.append(bench_sqlalchemy())
        results.append(await bench_tortoise())
        results.append(await bench_oxen_extended())
        results.append(await bench_oxen_columnar())
        results.append(bench_sqlalchemy_extended())
        results.append(await bench_tortoise_extended())
        # Django (optional): import and run if available
        try:
            results.append(await bench_django())
            results.append(await bench_django_extended())
        except Exception:
            pass

    print(json.dumps(aggregate(results), indent=2))


if __name__ == "__main__":
    asyncio.run(main())



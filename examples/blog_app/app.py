import os
import asyncio
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from oxen.engine import connect, disconnect
from oxen.expressions import WindowFunction, Q
from oxen.schema import sync_model
from .models import User, Post, Comment
from oxen.exceptions import IntegrityError, DoesNotExist, OperationalError


DB_URL = os.environ.get("OXEN_BLOG_DB", "sqlite:////Users/developer/Desktop/OxenORM/smoke_test.db")


app = FastAPI(title="OxenORM Blog")


class UserIn(BaseModel):
    username: str
    display_name: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str


class PostIn(BaseModel):
    title: str
    body: str
    author_id: int


class PostOut(BaseModel):
    id: int
    title: str
    body: str
    author_id: int


class CommentIn(BaseModel):
    post_id: int
    author_id: int
    body: str


class CommentOut(BaseModel):
    id: int
    post_id: int
    author_id: int
    body: str


@app.on_event("startup")
async def startup():
    engine = await connect(DB_URL)
    # Attach engine to models and sync schema (create-only; avoids legacy tables)
    for m in (User, Post, Comment):
        m._set_rust_engine(engine)
        sync_model(engine, m)


@app.on_event("shutdown")
async def shutdown():
    engine = User._meta.db
    if engine:
        await disconnect(engine)


# Users
@app.post("/users", response_model=UserOut)
async def create_user(data: UserIn):
    try:
        user = await User.create(username=data.username, display_name=data.display_name)
        return UserOut(id=int(user.pk), username=user.username, display_name=user.display_name)
    except Exception as e:
        # On duplicate or transient errors, resolve by lookup
        try:
            fetched = await User.get(username=data.username)
            return UserOut(id=int(fetched.pk), username=fetched.username, display_name=fetched.display_name)
        except Exception as e2:
            raise HTTPException(status_code=400, detail=str(e2))


@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    try:
        user = await User.get(pk=user_id)
        return UserOut(id=user.pk, username=user.username, display_name=user.display_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/users", response_model=List[UserOut])
async def list_users():
    rows = await User._db_queryset().order_by("id").values(id="id", username="username", display_name="display_name")
    return rows


# Posts
@app.post("/posts", response_model=PostOut)
async def create_post(data: PostIn):
    try:
        post = await Post.create(title=data.title, body=data.body, author=data.author_id)
        return PostOut(id=int(post.pk), title=post.title, body=post.body, author_id=post.author)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/posts/{post_id}", response_model=PostOut)
async def get_post(post_id: int):
    try:
        post = await Post.get(pk=post_id)
        return PostOut(id=post.pk, title=post.title, body=post.body, author_id=post.author)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/posts", response_model=List[PostOut])
async def list_posts(author_id: Optional[int] = None):
    qs = Post._db_queryset().order_by("id")
    if author_id:
        qs = qs.filter(author=author_id)
    rows = await qs.values(id="id", title="title", body="body", author_id="author")
    return rows


# Comments
@app.post("/comments", response_model=CommentOut)
async def create_comment(data: CommentIn):
    try:
        c = await Comment.create(post=data.post_id, author=data.author_id, body=data.body)
        return CommentOut(id=int(c.pk), post_id=c.post, author_id=c.author, body=c.body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/comments", response_model=List[CommentOut])
async def list_comments(post_id: Optional[int] = None):
    qs = Comment._db_queryset().order_by("id")
    if post_id:
        qs = qs.filter(post=post_id)
    rows = await qs.values(id="id", post_id="post", author_id="author", body="body")
    return rows


# Advanced analytics & search endpoints

class TopAuthor(BaseModel):
    author_id: int
    author_name: str
    num_posts: int
    rank: int


@app.get("/analytics/top-authors", response_model=List[TopAuthor])
async def top_authors():
    # Use window COUNT(*) OVER (PARTITION BY author) to compute per-row num_posts
    qs = Post._db_queryset().window(num_posts=WindowFunction('COUNT(*)', partition_by=['author']))
    posts = await qs
    # Aggregate to one row per author in Python
    author_to_count: dict[int, int] = {}
    for p in posts:
        count = getattr(p, 'num_posts', None)
        if count is None:
            continue
        aid = p.author if isinstance(p.author, int) else getattr(p.author, 'pk', None)
        if aid is None:
            continue
        current = author_to_count.get(aid, 0)
        author_to_count[aid] = max(current, int(count))
    # Fetch author names
    author_ids = list(author_to_count.keys())
    if not author_ids:
        return []
    user_rows = await User._db_queryset().filter(id__in=author_ids).values(id="id", display_name="display_name")
    id_to_name = {int(r['id']): r['display_name'] for r in user_rows}
    # Build ranked result
    sorted_items = sorted(author_to_count.items(), key=lambda kv: kv[1], reverse=True)
    out: List[TopAuthor] = []
    for idx, (aid, cnt) in enumerate(sorted_items, start=1):
        out.append(TopAuthor(author_id=aid, author_name=id_to_name.get(aid, ""), num_posts=cnt, rank=idx))
    return out


class PostWithAuthor(BaseModel):
    id: int
    title: str
    author_name: str


@app.get("/posts/with-authors", response_model=List[PostWithAuthor])
async def posts_with_authors():
    # Use ORM select_related to make join available; then resolve author names
    qs = Post._db_queryset().select_related('author').order_by('id')
    posts = await qs
    out: List[PostWithAuthor] = []
    for p in posts:
        author_name = ""
        a = getattr(p, 'author', None)
        if a is not None:
            if hasattr(a, '_load'):
                try:
                    loaded = await a._load()
                    if loaded is not None:
                        author_name = getattr(loaded, 'display_name', "")
                except Exception:
                    pass
            elif hasattr(a, 'display_name'):
                author_name = getattr(a, 'display_name', "")
        out.append(PostWithAuthor(id=int(p.pk), title=p.title, author_name=author_name))
    return out


class PostSearchOut(BaseModel):
    id: int
    title: str
    body: str


@app.get("/posts/search", response_model=List[PostSearchOut])
async def search_posts(query: str, author_id: Optional[int] = None):
    # Demonstrate ORM filters with OR groups and icontains
    from oxen.expressions import Q

    qs = Post._db_queryset().order_by("id")
    # (title ILIKE or body ILIKE)
    or_q = Q(title__icontains=query) | Q(body__icontains=query)
    qs = qs.filter(or_q)
    if author_id is not None:
        qs = qs.filter(author=author_id)
    rows = await qs.values(id="id", title="title", body="body")
    return rows


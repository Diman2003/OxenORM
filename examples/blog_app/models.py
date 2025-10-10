from oxen.models import Model
from oxen.fields.data import CharField, TextField, DateTimeField, IntegerField
from oxen.fields.relational import ForeignKeyField


class User(Model):
    username = CharField(max_length=50, unique=True, null=False)
    display_name = CharField(max_length=100, null=False)
    created_at = DateTimeField(auto_now_add=True, null=False)

    class Meta:
        table_name = "blog_users"


class Post(Model):
    title = CharField(max_length=200, null=False)
    body = TextField(null=False)
    author = ForeignKeyField(User, related_name="posts", null=False)
    created_at = DateTimeField(auto_now_add=True, null=False)

    class Meta:
        table_name = "blog_posts"


class Comment(Model):
    post = ForeignKeyField(Post, related_name="comments", null=False)
    author = ForeignKeyField(User, related_name="comments", null=False)
    body = TextField(null=False)
    created_at = DateTimeField(auto_now_add=True, null=False)

    class Meta:
        table_name = "blog_comments"



from django.db import models


class DJUser(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100)

    class Meta:
        db_table = "blog_users"
        managed = False


class DJPost(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(
        DJUser,
        db_column="author",
        on_delete=models.DO_NOTHING,
        related_name="posts",
    )

    class Meta:
        db_table = "blog_posts"
        managed = False



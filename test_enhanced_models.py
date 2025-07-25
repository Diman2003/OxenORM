#!/usr/bin/env python3
"""
Test Enhanced Models and Query Building

This script demonstrates the enhanced model definitions and query building
capabilities copied from Tortoise ORM and implemented for OxenORM.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from oxen.models import Model
from oxen.fields.data import (
    IntField, CharField, TextField, BooleanField, DateTimeField,
    FloatField, DecimalField, JSONField, UUIDField
)
from oxen.fields.relational import (
    ForeignKeyField, ManyToManyField, OneToOneField
)
from oxen.expressions import Q, F
from oxen.validators import email, min_value, max_value, min_length, max_length
from oxen.signals import pre_save, post_save


# Example models demonstrating the enhanced functionality
class User(Model):
    """User model with various field types and validators."""
    
    username = CharField(max_length=50, unique=True, validators=[min_length(3)])
    email = CharField(max_length=255, validators=[email()])
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    age = IntField(null=True, validators=[min_value(0), max_value(150)])
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    profile_data = JSONField(null=True)
    uuid = UUIDField(default=uuid.uuid4)
    
    class Meta:
        table_name = "users"
        ordering = ("username",)


class Category(Model):
    """Category model for blog posts."""
    
    name = CharField(max_length=100, unique=True)
    description = TextField(null=True)
    slug = CharField(max_length=100, unique=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = "categories"
        ordering = ("name",)


class Post(Model):
    """Blog post model with relationships."""
    
    title = CharField(max_length=200)
    content = TextField()
    slug = CharField(max_length=200, unique=True)
    excerpt = TextField(null=True)
    is_published = BooleanField(default=False)
    published_at = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    # Relationships
    author = ForeignKeyField(User, related_name="posts")
    category = ForeignKeyField(Category, related_name="posts")
    tags = ManyToManyField("Tag", related_name="posts")
    
    class Meta:
        table_name = "posts"
        ordering = ("-created_at",)


class Tag(Model):
    """Tag model for blog posts."""
    
    name = CharField(max_length=50, unique=True)
    slug = CharField(max_length=50, unique=True)
    description = TextField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = "tags"
        ordering = ("name",)


class Comment(Model):
    """Comment model for blog posts."""
    
    content = TextField()
    is_approved = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    # Relationships
    post = ForeignKeyField(Post, related_name="comments")
    author = ForeignKeyField(User, related_name="comments")
    parent = ForeignKeyField("self", null=True, related_name="replies")
    
    class Meta:
        table_name = "comments"
        ordering = ("-created_at",)


class Profile(Model):
    """User profile model with one-to-one relationship."""
    
    bio = TextField(null=True)
    avatar_url = CharField(max_length=255, null=True)
    website = CharField(max_length=255, null=True)
    location = CharField(max_length=100, null=True)
    birth_date = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    # One-to-one relationship
    user = OneToOneField(User, related_name="profile")
    
    class Meta:
        table_name = "profiles"


# Signal handlers
@pre_save(User)
async def user_pre_save(sender, instance, **kwargs):
    """Pre-save signal handler for User model."""
    print(f"About to save user: {instance.username}")
    if not instance.username:
        instance.username = f"user_{uuid.uuid4().hex[:8]}"


@post_save(User)
async def user_post_save(sender, instance, created, **kwargs):
    """Post-save signal handler for User model."""
    if created:
        print(f"Created new user: {instance.username}")
    else:
        print(f"Updated user: {instance.username}")


@pre_save(Post)
async def post_pre_save(sender, instance, **kwargs):
    """Pre-save signal handler for Post model."""
    print(f"About to save post: {instance.title}")
    if instance.is_published and not instance.published_at:
        instance.published_at = datetime.now()


async def test_model_creation():
    """Test model creation and basic operations."""
    print("=== Testing Model Creation ===")
    
    # Create users
    user1 = User(
        username="john_doe",
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        age=30
    )
    
    user2 = User(
        username="jane_smith",
        email="jane@example.com",
        first_name="Jane",
        last_name="Smith",
        age=25
    )
    
    print(f"User 1: {user1}")
    print(f"User 2: {user2}")
    print(f"User 1 PK: {user1.pk}")
    print(f"User 2 PK: {user2.pk}")
    
    # Test field access
    print(f"User 1 username: {user1.username}")
    print(f"User 1 email: {user1.email}")
    print(f"User 1 age: {user1.age}")
    print(f"User 1 is_active: {user1.is_active}")
    print(f"User 1 created_at: {user1.created_at}")
    
    # Test model methods
    print(f"User 1 string representation: {str(user1)}")
    print(f"User 1 repr: {repr(user1)}")
    
    # Test field iteration
    print("User 1 fields:")
    for field_name, value in user1:
        print(f"  {field_name}: {value}")


async def test_queryset_operations():
    """Test queryset operations and query building."""
    print("\n=== Testing QuerySet Operations ===")
    
    # Simulate some data
    users = [
        User(username="user1", email="user1@example.com", age=25),
        User(username="user2", email="user2@example.com", age=30),
        User(username="user3", email="user3@example.com", age=35),
    ]
    
    # Test filtering
    print("Testing filtering:")
    queryset = User.objects.filter(age__gte=30)
    print(f"Users age >= 30: {queryset}")
    
    queryset = User.objects.filter(username__contains="user")
    print(f"Users with 'user' in username: {queryset}")
    
    # Test Q objects
    print("Testing Q objects:")
    queryset = User.objects.filter(
        Q(age__gte=30) | Q(username__startswith="user")
    )
    print(f"Complex filter: {queryset}")
    
    # Test ordering
    print("Testing ordering:")
    queryset = User.objects.order_by("-age")
    print(f"Users ordered by age desc: {queryset}")
    
    # Test annotations
    print("Testing annotations:")
    queryset = User.objects.annotate(
        name_length=F("username").length()
    )
    print(f"Users with name length: {queryset}")
    
    # Test values and values_list
    print("Testing values:")
    queryset = User.objects.values("username", "email")
    print(f"User values: {queryset}")
    
    print("Testing values_list:")
    queryset = User.objects.values_list("username", flat=True)
    print(f"Username list: {queryset}")


async def test_relationships():
    """Test relationship operations."""
    print("\n=== Testing Relationships ===")
    
    # Create related objects
    user = User(username="blogger", email="blogger@example.com")
    category = Category(name="Technology", slug="tech")
    post = Post(
        title="My First Post",
        content="This is my first blog post content.",
        slug="my-first-post",
        author=user,
        category=category
    )
    
    print(f"Post: {post}")
    print(f"Post author: {post.author}")
    print(f"Post category: {post.category}")
    
    # Test reverse relationships
    print(f"User posts: {user.posts}")
    print(f"Category posts: {category.posts}")


async def test_bulk_operations():
    """Test bulk operations."""
    print("\n=== Testing Bulk Operations ===")
    
    # Create multiple users
    users = [
        User(username=f"bulk_user_{i}", email=f"user{i}@example.com", age=20+i)
        for i in range(5)
    ]
    
    print(f"Created {len(users)} users for bulk operations")
    
    # Test bulk create
    print("Testing bulk create:")
    created_users = await User.objects.bulk_create(users)
    print(f"Bulk created {len(created_users)} users")
    
    # Test bulk update
    print("Testing bulk update:")
    for user in created_users:
        user.age += 1
    
    updated_count = await User.objects.bulk_update(created_users, ["age"])
    print(f"Bulk updated {updated_count} users")


async def test_advanced_queries():
    """Test advanced query features."""
    print("\n=== Testing Advanced Queries ===")
    
    # Test select_related
    print("Testing select_related:")
    queryset = Post.objects.select_related("author", "category")
    print(f"Posts with related data: {queryset}")
    
    # Test prefetch_related
    print("Testing prefetch_related:")
    queryset = Post.objects.prefetch_related("tags", "comments")
    print(f"Posts with prefetched data: {queryset}")
    
    # Test complex filtering
    print("Testing complex filtering:")
    queryset = Post.objects.filter(
        Q(is_published=True) & 
        Q(author__age__gte=25) &
        Q(category__name="Technology")
    )
    print(f"Complex filtered posts: {queryset}")
    
    # Test aggregation
    print("Testing aggregation:")
    queryset = User.objects.annotate(
        post_count=F("posts").count()
    )
    print(f"Users with post count: {queryset}")


async def test_model_validation():
    """Test model validation."""
    print("\n=== Testing Model Validation ===")
    
    try:
        # Test invalid email
        user = User(username="test", email="invalid-email")
        print("Should have failed validation for invalid email")
    except Exception as e:
        print(f"Validation error (expected): {e}")
    
    try:
        # Test invalid age
        user = User(username="test", email="test@example.com", age=-5)
        print("Should have failed validation for negative age")
    except Exception as e:
        print(f"Validation error (expected): {e}")
    
    try:
        # Test short username
        user = User(username="ab", email="test@example.com")
        print("Should have failed validation for short username")
    except Exception as e:
        print(f"Validation error (expected): {e}")


async def test_signals():
    """Test signal handling."""
    print("\n=== Testing Signals ===")
    
    # Create a user to trigger signals
    user = User(
        username="signal_test",
        email="signal@example.com",
        first_name="Signal",
        last_name="Test"
    )
    
    print("Creating user (should trigger pre_save and post_save signals):")
    await user.save()
    
    print("Updating user (should trigger post_save signal):")
    user.first_name = "Updated"
    await user.save()


async def main():
    """Main test function."""
    print("🚀 Testing Enhanced OxenORM Models and Query Building")
    print("=" * 60)
    
    try:
        await test_model_creation()
        await test_queryset_operations()
        await test_relationships()
        await test_bulk_operations()
        await test_advanced_queries()
        await test_model_validation()
        await test_signals()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 
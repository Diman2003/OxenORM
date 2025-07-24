"""
Basic OxenORM Usage Example

This example demonstrates how to use OxenORM with the familiar Tortoise-like API
while getting the performance benefits of the Rust backend.
"""

import asyncio
from datetime import datetime
from typing import Optional

from oxen import Model, init_db, close_db
from oxen.fields import IntField, CharField, TextField, DateTimeField, BooleanField


class User(Model):
    """User model example."""
    
    id = IntField(primary_key=True)
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100, unique=True)
    bio = TextField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        table = "users"


class Post(Model):
    """Post model example."""
    
    id = IntField(primary_key=True)
    title = CharField(max_length=200)
    content = TextField()
    author_id = IntField()  # Foreign key to User
    published = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        table = "posts"


async def main():
    """Main example function."""
    
    # Initialize database connection
    await init_db({
        'default': 'postgresql://user:password@localhost/oxenorm_test'
    })
    
    try:
        # Create tables (in a real app, you'd use migrations)
        # await generate_schemas()
        
        print("=== OxenORM Basic Usage Example ===\n")
        
        # Create a user
        print("1. Creating a user...")
        user = await User.create(
            username="john_doe",
            email="john@example.com",
            bio="Software developer and Rust enthusiast"
        )
        print(f"Created user: {user.username} (ID: {user.id})")
        
        # Create another user
        user2 = await User.create(
            username="jane_smith",
            email="jane@example.com",
            bio="Python developer"
        )
        print(f"Created user: {user2.username} (ID: {user2.id})")
        
        # Create posts
        print("\n2. Creating posts...")
        post1 = await Post.create(
            title="Getting Started with OxenORM",
            content="OxenORM is a high-performance Python ORM backed by Rust...",
            author_id=user.id,
            published=True
        )
        
        post2 = await Post.create(
            title="Why Rust for Database Operations?",
            content="Rust provides memory safety and performance...",
            author_id=user.id,
            published=False
        )
        
        post3 = await Post.create(
            title="Python and Rust: The Perfect Pair",
            content="Combining Python's ease of use with Rust's performance...",
            author_id=user2.id,
            published=True
        )
        
        print(f"Created {3} posts")
        
        # Query users
        print("\n3. Querying users...")
        all_users = await User.all()
        print(f"Total users: {len(all_users)}")
        
        for user in all_users:
            print(f"  - {user.username} ({user.email})")
        
        # Filter users
        print("\n4. Filtering users...")
        active_users = await User.filter(is_active=True)
        print(f"Active users: {len(active_users)}")
        
        # Get specific user
        print("\n5. Getting specific user...")
        john = await User.get(username="john_doe")
        print(f"Found user: {john.username} - {john.bio}")
        
        # Update user
        print("\n6. Updating user...")
        john.bio = "Software developer, Rust enthusiast, and OxenORM contributor"
        await john.save()
        print(f"Updated bio: {john.bio}")
        
        # Query posts
        print("\n7. Querying posts...")
        published_posts = await Post.filter(published=True)
        print(f"Published posts: {len(published_posts)}")
        
        for post in published_posts:
            print(f"  - {post.title} (by user ID: {post.author_id})")
        
        # Count operations
        print("\n8. Counting records...")
        total_users = await User.count()
        total_posts = await Post.count()
        published_count = await Post.filter(published=True).count()
        
        print(f"Total users: {total_users}")
        print(f"Total posts: {total_posts}")
        print(f"Published posts: {published_count}")
        
        # Bulk operations
        print("\n9. Bulk operations...")
        # Create multiple users at once
        users_data = [
            {"username": "alice", "email": "alice@example.com", "bio": "Data scientist"},
            {"username": "bob", "email": "bob@example.com", "bio": "DevOps engineer"},
            {"username": "charlie", "email": "charlie@example.com", "bio": "Frontend developer"},
        ]
        
        users = []
        for data in users_data:
            user = User(**data)
            users.append(user)
        
        # Bulk create (this would use the Rust backend for performance)
        # await User.bulk_create(users)
        print("Bulk create would be handled by Rust backend for performance")
        
        # Raw SQL (when you need custom queries)
        print("\n10. Raw SQL queries...")
        # This would be executed by the Rust backend
        # results = await User.raw("SELECT username, COUNT(*) as post_count FROM users u JOIN posts p ON u.id = p.author_id GROUP BY u.id, u.username")
        print("Raw SQL queries are executed by the Rust backend")
        
        print("\n=== Example completed successfully! ===")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Close database connections
        await close_db()


if __name__ == "__main__":
    asyncio.run(main()) 
from oxen.models import Model
from oxen.fields.data import IntegerField, CharField, FloatField, BooleanField, DateTimeField
from oxen.fields.relational import ForeignKeyField, OneToOneField


class Account(Model):
    username = CharField(max_length=100)
    email = CharField(max_length=200)

    class Meta:
        table_name = "account"


class CustomerProfile(Model):
    profile_type = CharField(max_length=20)
    kt_id = CharField(max_length=20)
    auth_id = OneToOneField("Account", related_name="customer_profile", null=False)
    profile_pic = CharField(max_length=255)
    qr_code = CharField(max_length=255)

    class Meta:
        table_name = "customer_profile"

    async def save(self, *args, **kwargs):  # type: ignore[override]
        if not getattr(self, 'kt_id', None) or self.kt_id == 'KT':
            prefix = "KTCP" if getattr(self, 'profile_type', 'Personal') == 'Personal' else "KTCO"
            db = self._meta.db
            temp_id = 1
            if db is not None:
                try:
                    res = await db.execute_query('SELECT COUNT(*) as cnt FROM customer_profile')
                    cnt = (res.get('data') or [{}])[0].get('cnt') or (res.get('data') or [{}])[0].get('count') or 0
                    temp_id = int(cnt) + 1
                except Exception:
                    temp_id = 1
            self.kt_id = f"{prefix}{100000 + temp_id}"
        await super().save(*args, **kwargs)


class Address(Model):
    add_user = ForeignKeyField("Account", related_name="user_address", null=False)
    add_line1 = CharField(max_length=200)
    add_line2 = CharField(max_length=200, null=True)
    landmark = CharField(max_length=100, null=True)
    city = CharField(max_length=50)
    state = CharField(max_length=50)
    country = CharField(max_length=50)
    zipcode = IntegerField()
    is_default = BooleanField(default=False)

    class Meta:
        table_name = "address"

    def full_address(self) -> str:
        return f"{self.add_line1}{(' ' + self.add_line2) if getattr(self, 'add_line2', None) else ''}"


class Product(Model):
    name = CharField(max_length=200)
    price = FloatField()

    class Meta:
        table_name = "product"


class Order(Model):
    account = ForeignKeyField("Account", related_name="orders", null=False)
    created_at = DateTimeField()

    class Meta:
        table_name = "orders"


class OrderItem(Model):
    order_ref = ForeignKeyField("Order", related_name="items", null=False)
    product = ForeignKeyField("Product", related_name="order_items", null=False)
    quantity = IntegerField()
    unit_price = FloatField()

    class Meta:
        table_name = "order_item"



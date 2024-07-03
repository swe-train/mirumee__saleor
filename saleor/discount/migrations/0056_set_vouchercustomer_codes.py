# Generated by Django 3.2.21 on 2023-09-26 08:51

from django.db import migrations
from django.db.models import Exists, OuterRef

# The batch of size 1000 took about 0.2s
BATCH_SIZE = 1000


def queryset_in_batches(queryset):
    start_pk = 0

    while True:
        qs = queryset.order_by("pk").filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


def set_voucher_code_to_voucher_customer(apps, schema_editor):
    VoucherCustomer = apps.get_model("discount", "VoucherCustomer")
    Voucher = apps.get_model("discount", "Voucher")
    VoucherCode = apps.get_model("discount", "VoucherCode")
    queryset = VoucherCustomer.objects.filter(voucher_code__isnull=True).order_by("pk")
    for ids in queryset_in_batches(queryset):
        qs = VoucherCustomer.objects.filter(pk__in=ids)
        set_voucher_code(VoucherCustomer, Voucher, VoucherCode, qs)


def set_voucher_code(VoucherCustomer, Voucher, VoucherCode, voucher_customers):
    voucher_id_to_code_map = get_voucher_id_to_code_map(
        Voucher, VoucherCode, voucher_customers
    )
    voucher_customers_list = []
    for voucher_customer in voucher_customers:
        code = voucher_id_to_code_map[voucher_customer.voucher_id]
        voucher_customer.voucher_code = code
        voucher_customers_list.append(voucher_customer)
    VoucherCustomer.objects.bulk_update(voucher_customers_list, ["voucher_code"])


def get_voucher_id_to_code_map(Voucher, VoucherCode, voucher_customers):
    voucher_id_to_code_map = {}
    vouchers = Voucher.objects.filter(
        Exists(voucher_customers.filter(voucher_id=OuterRef("pk")))
    )
    codes = VoucherCode.objects.filter(
        Exists(vouchers.filter(id=OuterRef("voucher_id")))
    )
    for code in codes:
        voucher_id_to_code_map[code.voucher_id] = code

    return voucher_id_to_code_map


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0055_vouchercustomer_voucher_code_index"),
    ]

    operations = [
        migrations.RunPython(
            set_voucher_code_to_voucher_customer,
            migrations.RunPython.noop,
        ),
    ]
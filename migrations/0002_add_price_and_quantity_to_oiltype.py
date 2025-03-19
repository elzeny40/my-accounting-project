# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='oiltype',
            name='price_per_liter',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='oiltype',
            name='current_quantity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0011_remove_vehiclemovement_transportation_cost_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehiclemovement',
            name='movement_id',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, verbose_name='رقم الحركة'),
        ),
    ]
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('one_c', '0003_status_status_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='number',
            field=models.CharField(max_length=20),
        ),
    ]

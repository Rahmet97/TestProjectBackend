# Generated by Django 4.0.6 on 2022-09-30 15:04

from django.conf import settings
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.CharField(blank=True, max_length=100)),
                ('comment', models.TextField()),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('prefix', models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='YurUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255)),
                ('short_name', models.CharField(blank=True, max_length=100)),
                ('opf', models.CharField(blank=True, max_length=3)),
                ('soogu', models.CharField(blank=True, max_length=5)),
                ('oked', models.CharField(blank=True, max_length=5)),
                ('status', models.CharField(blank=True, max_length=5)),
                ('vatNumber', models.CharField(blank=True, max_length=12)),
                ('taxpayerType', models.CharField(blank=True, max_length=255)),
                ('businessType', models.CharField(blank=True, max_length=255)),
                ('activityCode', models.CharField(blank=True, max_length=4)),
                ('individualEntrepreneurType', models.CharField(blank=True, max_length=2)),
                ('countryCode', models.CharField(blank=True, max_length=3)),
                ('soato', models.CharField(blank=True, max_length=10)),
                ('villageCode', models.CharField(blank=True, max_length=5)),
                ('sectorCode', models.CharField(blank=True, max_length=1)),
                ('streetName', models.CharField(blank=True, max_length=100)),
                ('house', models.IntegerField(blank=True)),
                ('flat', models.IntegerField(blank=True)),
                ('postCode', models.CharField(blank=True, max_length=20)),
                ('cadastreNumber', models.CharField(blank=True, max_length=36)),
                ('billingCountryCode', models.CharField(blank=True, max_length=3)),
                ('billingSoato', models.CharField(blank=True, max_length=10)),
                ('billingVillageCode', models.CharField(blank=True, max_length=5)),
                ('billingSectorCode', models.CharField(blank=True, max_length=1)),
                ('billingStreetName', models.CharField(blank=True, max_length=100)),
                ('billingHouse', models.IntegerField(blank=True)),
                ('billingFlat', models.IntegerField(blank=True)),
                ('billingPostCode', models.CharField(blank=True, max_length=20)),
                ('billingCadastreNumber', models.CharField(blank=True, max_length=36)),
                ('director_lastname', models.CharField(blank=True, max_length=50)),
                ('director_firstname', models.CharField(blank=True, max_length=50)),
                ('director_middlename', models.CharField(blank=True, max_length=50)),
                ('director_gender', models.CharField(blank=True, max_length=1)),
                ('director_nationality', models.CharField(blank=True, max_length=4)),
                ('director_ctzn', models.CharField(blank=True, max_length=3)),
                ('director_passportSeries', models.CharField(blank=True, max_length=2)),
                ('director_passportNumber', models.IntegerField(blank=True)),
                ('director_pinfl', models.CharField(blank=True, max_length=14)),
                ('director_tin', models.CharField(blank=True, max_length=9)),
                ('director_phone', models.CharField(blank=True, max_length=12)),
                ('director_email', models.CharField(blank=True, max_length=40)),
                ('mfo', models.CharField(blank=True, max_length=5)),
                ('paymentAccount', models.CharField(blank=True, max_length=20)),
                ('extraActivityType', models.CharField(blank=True, max_length=4)),
                ('birth_date', models.DateField()),
                ('ctzn', models.CharField(max_length=50)),
                ('per_adr', models.CharField(max_length=255)),
                ('tin', models.CharField(max_length=9)),
                ('pport_issue_place', models.CharField(max_length=255)),
                ('sur_name', models.CharField(max_length=50)),
                ('gd', models.IntegerField()),
                ('natn', models.CharField(max_length=50)),
                ('pport_issue_date', models.DateField()),
                ('pport_expr_date', models.DateField()),
                ('pport_no', models.CharField(max_length=20)),
                ('pin', models.CharField(max_length=14)),
                ('mob_phone_no', models.CharField(max_length=20)),
                ('user_id', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254)),
                ('birth_place', models.CharField(max_length=50)),
                ('mid_name', models.CharField(max_length=50)),
                ('user_type', models.CharField(max_length=1)),
                ('sess_id', models.CharField(max_length=255)),
                ('ret_cd', models.IntegerField()),
                ('first_name', models.CharField(max_length=50)),
                ('full_name', models.CharField(max_length=100)),
                ('userdata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create', models.BooleanField(default=False)),
                ('read', models.BooleanField(default=False)),
                ('update', models.BooleanField(default=False)),
                ('delete', models.BooleanField(default=False)),
                ('permissions', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.permission')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.role')),
            ],
        ),
        migrations.AddField(
            model_name='role',
            name='partition',
            field=models.ManyToManyField(through='accounts.RolePermission', to='accounts.permission'),
        ),
        migrations.CreateModel(
            name='LogPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(max_length=50)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.permission')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LogGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(max_length=30)),
                ('created_date', models.DateTimeField()),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.group')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FizUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('birth_date', models.DateField()),
                ('ctzn', models.CharField(max_length=50)),
                ('per_adr', models.CharField(max_length=255)),
                ('tin', models.CharField(max_length=9)),
                ('pport_issue_place', models.CharField(max_length=255)),
                ('sur_name', models.CharField(max_length=50)),
                ('gd', models.IntegerField()),
                ('natn', models.CharField(max_length=50)),
                ('pport_issue_date', models.DateField()),
                ('pport_expr_date', models.DateField()),
                ('pport_no', models.CharField(max_length=20)),
                ('pin', models.CharField(max_length=14)),
                ('mob_phone_no', models.CharField(max_length=20)),
                ('user_id', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254)),
                ('birth_place', models.CharField(max_length=50)),
                ('mid_name', models.CharField(max_length=50)),
                ('user_type', models.CharField(max_length=1)),
                ('sess_id', models.CharField(max_length=255)),
                ('ret_cd', models.IntegerField()),
                ('first_name', models.CharField(max_length=50)),
                ('full_name', models.CharField(max_length=100)),
                ('userdata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='userdata',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.group'),
        ),
        migrations.AddField(
            model_name='userdata',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='userdata',
            name='role',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.role'),
        ),
        migrations.AddField(
            model_name='userdata',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]

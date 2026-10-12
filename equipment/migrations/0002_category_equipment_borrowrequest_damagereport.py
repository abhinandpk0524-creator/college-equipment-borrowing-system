from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('icon_class', models.CharField(default='bi-box-seam', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.AlterField(
            model_name='customuser',
            name='department',
            field=models.CharField(blank=True, help_text='Department the user belongs to', max_length=100),
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('code', models.CharField(help_text='e.g. EQ-PRJ-001', max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('location', models.CharField(default='Central Store Room', max_length=100)),
                ('total_quantity', models.PositiveIntegerField(default=1)),
                ('available_quantity', models.PositiveIntegerField(default=1)),
                ('condition', models.CharField(choices=[('GOOD', 'Good / Working'), ('DAMAGED', 'Damaged'), ('MAINTENANCE', 'Under Maintenance')], default='GOOD', max_length=20)),
                ('image_url', models.CharField(blank=True, help_text='Image URL or icon representation', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equipments', to='equipment.category')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='BorrowRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('start_date', models.DateField()),
                ('expected_return_date', models.DateField()),
                ('purpose', models.TextField(help_text='Purpose of borrowing equipment')),
                ('status', models.CharField(choices=[('PENDING', 'Pending Approval'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('ISSUED', 'Issued / On Loan'), ('RETURNED', 'Returned'), ('OVERDUE', 'Overdue')], default='PENDING', max_length=20)),
                ('admin_remarks', models.TextField(blank=True, help_text='Remarks by Admin upon approval/rejection')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('issued_at', models.DateTimeField(blank=True, null=True)),
                ('returned_at', models.DateTimeField(blank=True, null=True)),
                ('return_condition', models.CharField(blank=True, choices=[('GOOD', 'Good / Working'), ('DAMAGED', 'Damaged'), ('MAINTENANCE', 'Under Maintenance')], max_length=20)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrow_requests', to='equipment.equipment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrow_requests', to='equipment.customuser')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DamageReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('OPEN', 'Reported / Open'), ('IN_REPAIR', 'In Repair'), ('RESOLVED', 'Resolved / Repaired'), ('REPLACED', 'Replaced / Written Off')], default='OPEN', max_length=20)),
                ('action_taken', models.TextField(blank=True)),
                ('reported_at', models.DateTimeField(auto_now_add=True)),
                ('borrow_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='damage_reports', to='equipment.borrowrequest')),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='damage_reports', to='equipment.equipment')),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='equipment.customuser')),
            ],
            options={
                'ordering': ['-reported_at'],
            },
        ),
    ]

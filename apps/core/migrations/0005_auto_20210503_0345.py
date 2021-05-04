# Generated by Django 2.2.19 on 2021-05-02 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_inquirymail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inquirymail',
            name='email',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='inquirymail',
            name='userInfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inquiry_mail', to='core.UserProfile'),
        ),
    ]
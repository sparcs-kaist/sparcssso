# Generated by Django 2.2.19 on 2021-05-02 18:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_longer_service_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='InquiryMail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('email', models.CharField(blank=True, max_length=50)),
                ('topic', models.CharField(choices=[('bugs', 'Bug Report'), ('suggestions', 'Suggestions'), ('accounts', 'Accounts'), ('etc', 'etc')], default='etc', max_length=11)),
                ('title', models.CharField(max_length=50)),
                ('content', models.TextField()),
                ('userInfo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inquiry_mail', to='core.UserProfile')),
            ],
        ),
    ]
# Generated manually for Story 12-5
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('artworks', '0004_shotversion'),
    ]

    operations = [
        migrations.AddField(
            model_name='shot',
            name='is_head_frame',
            field=models.BooleanField(
                default=False,
                blank=True,
                null=True,
                verbose_name='是否首帧'
            ),
        ),
        migrations.AddField(
            model_name='shot',
            name='is_tail_frame',
            field=models.BooleanField(
                default=False,
                blank=True,
                null=True,
                verbose_name='是否尾帧'
            ),
        ),
    ]

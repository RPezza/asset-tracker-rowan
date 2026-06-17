from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0007_alter_usermessage_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="booking_group",
            field=models.CharField(blank=True, db_index=True, default="", max_length=36),
        ),
    ]

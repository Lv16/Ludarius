from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="collectionitem",
            new_name="accounts_co_media_t_ad8ad7_idx",
            old_name="accounts_co_media_t_3dd94d_idx",
        ),
        migrations.RenameIndex(
            model_name="mediastatus",
            new_name="accounts_me_user_id_7f29c9_idx",
            old_name="accounts_me_user_id_d43673_idx",
        ),
        migrations.RenameIndex(
            model_name="mediastatus",
            new_name="accounts_me_media_t_662d4f_idx",
            old_name="accounts_me_media_t_dbec4f_idx",
        ),
        migrations.RenameIndex(
            model_name="mediastatus",
            new_name="accounts_me_status_084b47_idx",
            old_name="accounts_me_status_7bb8e2_idx",
        ),
        migrations.RenameIndex(
            model_name="notification",
            new_name="accounts_no_user_id_cabb0a_idx",
            old_name="accounts_no_user_id_748d7e_idx",
        ),
    ]

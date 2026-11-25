from django.db import migrations
from django.contrib.auth.management import create_permissions

# Grupo com acesso às áreas de gerenciamento da Dashboard
# (Contatos, Serviços, Equipe e Relatórios). Para liberar essas áreas
# a um cliente, basta adicioná-lo ao grupo "Gerência" no /admin/.
NOME_GRUPO = "Gerência"
PERMISSOES = [
    "view_contato", "delete_contato",
    "view_servico", "add_servico", "change_servico", "delete_servico",
    "gerenciar_equipe", "ver_relatorios",
]


def criar_grupo(apps, schema_editor):
    # As permissões normalmente só são criadas depois do migrate;
    # aqui forçamos a criação para poder associá-las ao grupo.
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    grupo, _ = Group.objects.get_or_create(name=NOME_GRUPO)
    grupo.permissions.set(
        Permission.objects.filter(content_type__app_label="app", codename__in=PERMISSOES)
    )


def remover_grupo(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name=NOME_GRUPO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0006_permissoes_dashboard"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(criar_grupo, remover_grupo),
    ]

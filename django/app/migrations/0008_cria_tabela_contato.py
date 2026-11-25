from django.db import migrations

# A migration 0003_contato só registrou o model Contato no estado do Django
# (a tabela "contato_contato" vinha de um app "contato" antigo, já removido).
# Em um banco novo (PostgreSQL do Render, PC novo) a tabela nunca era criada.
# Esta migration cria a tabela apenas se ela ainda não existir.


def criar_tabela_contato(apps, schema_editor):
    Contato = apps.get_model("app", "Contato")
    tabelas = schema_editor.connection.introspection.table_names()
    if Contato._meta.db_table not in tabelas:
        schema_editor.create_model(Contato)


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0007_grupo_gerencia"),
    ]

    operations = [
        migrations.RunPython(criar_tabela_contato, migrations.RunPython.noop),
    ]

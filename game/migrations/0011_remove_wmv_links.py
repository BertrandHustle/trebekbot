from django.db import migrations
from django.db.models import Q


def remove_wmv_questions(apps, schema_editor):
    Question = apps.get_model('game', 'Question')
    for question in Question.objects.filter(~Q(valid_links=[])):
        links = question.valid_links
        for link in links:
            if link.endswith('.wmv'):
                question.delete()
                break


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0010_fix_invalid_links'),
    ]

    operations = [
        migrations.RunPython(
            remove_wmv_questions, migrations.RunPython.noop
        ),
    ]

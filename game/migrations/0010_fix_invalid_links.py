from django.db import migrations
from django.db.models import Q


def fix_invalid_links(apps, schema_editor):
    Question = apps.get_model('game', 'Question')
    for question in Question.objects.filter(~Q(valid_links=[])):
        links = question.valid_links
        fixed_links = []
        for link in links:
            ext = '.' + link.rsplit('.', 1)[1]
            match ext:
                case '.j':
                    fixed_links.append(link + 'pg')
                case '.jp':
                    fixed_links.append(link + 'g')
                case '.w':
                    fixed_links.append(link + 'mv')
                case '.wm':
                    fixed_links.append(link + 'v')
                case '.m':
                    fixed_links.append(link + 'p3')
                case '.mp':
                    fixed_links.append(link + '3')
                case _:
                    fixed_links.append(link)
        if set(links) != set(fixed_links):
            question.valid_links = fixed_links
            question.save()


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_alter_question_valid_links'),
    ]

    operations = [
        migrations.RunPython(
            fix_invalid_links, migrations.RunPython.noop
        ),
    ]

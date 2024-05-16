from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from game.models import Question


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-p', '--printout', help='print questions with valid links', action='store_true')

    def handle(self, *args, **options):
        valid_link_questions = Question.objects.filter(~Q(valid_links=[]))
        if options['printout']:
            print([q.valid_links for q in valid_link_questions])
        else:
            for question in valid_link_questions:
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
                    print(f'links: {links}')
                    print(f'fixed_links: {fixed_links}')
                    question.valid_links = fixed_links
                    question.save()
                    print(type(question))

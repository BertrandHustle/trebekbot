from django.db import models

from .Board import Board
from .Question import Question


class QuestionTile(models.Model):
    """
    represents a single question tile on the game board
    :param board: Board to which QuestionTile belongs
    :param alive: whether or not the tile is live (read: question hasn't been asked yet)
    :param question: Question associated with this QuestionTile
    """
    alive = models.BooleanField(default=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

from django.db import models


class Board(models.Model):
    """
    represents a game board of QuestionTiles
    :param columns: number of columns on the board
    :param column_size: how many tiles tall a column is
    :param rows: number of rows on the board
    :param row_size: how many tiles wide a row is
    """
    columns = models.IntegerField(default=6)
    rows = models.IntegerField(default=5)

from Board import Board
from game.serializers import QuestionSerializer
from Question import Question
from QuestionTile import QuestionTile


class BoardUtils:
    @staticmethod
    def fill_board(board: Board) -> Board:
        """
        creates question tiles to fill up board
        :param board: Board instance
        :return: newly filled Board instance
        """
        questions = Question.get_random_category(board.columns)
        for question in questions:
            QuestionTile.objects.create(
                board=board,
                question=question,
            )
        return board

    @staticmethod
    def tiles_to_dict(board: Board) -> dict:
        """
        convert all QuestionTiles that belong to a board into a dict
        :param board:
        :return: dict
        """
        board_dict = {}
        for question_tile in board.questiontile_set.all():
            question_dict = QuestionSerializer(question_tile.question).data
            board_dict[question_tile.id] = question_dict | {'alive': question_tile.alive}
        return board_dict

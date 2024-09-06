from game.models.Board import Board
from game.models.Question import Question
from game.models.QuestionTile import QuestionTile
from game.serializers import QuestionSerializer


class BoardUtils:
    @staticmethod
    def fill_board(board: Board) -> Board:
        """
        creates question tiles to fill up board
        :param board: Board instance
        :return: newly filled Board instance
        """
        for _ in range(board.columns):
            questions = Question.get_random_category(board.rows)
            for question in questions:
                QuestionTile.objects.create(
                    board=board,
                    question=question
                )
        return board

    @staticmethod
    def tiles_to_dict(board: Board) -> list[dict]:
        """
        convert all QuestionTiles that belong to a board into a dict
        :param board:
        :return: dict
        """
        board_list = []
        for question_tile in board.questiontile_set.all():
            question_dict = QuestionSerializer(question_tile.question).data
            board_list.append(question_dict | {'alive': question_tile.alive})
        return board_list

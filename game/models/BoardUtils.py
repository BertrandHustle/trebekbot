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
        used_categories = []
        for _ in range(board.columns):
            questions = Question.get_random_category(excluded_categories=used_categories, num_questions=board.rows)
            # this should yield only one category
            category = next(iter(set(questions.values_list('category', flat=True))))
            used_categories.append(category)
            for question in questions:
                QuestionTile.objects.create(
                    board=board,
                    question=question
                )
        return board

    @staticmethod
    def tiles_to_dict(board: Board) -> dict:
        """
        convert all QuestionTiles that belong to a board into a dict of lists of question dicts
        :param board: Board instance pre-populated with question tiles
        :return: dict
        """
        board_tiles = board.questiontile_set.all()
        board_dict = {category: [] for category in {tile.question.category for tile in board_tiles}}
        for question_tile in board_tiles:
            question_dict = QuestionSerializer(question_tile.question).data
            board_dict[question_tile.question.category].append(question_dict | {'alive': question_tile.alive})
        return board_dict

from game.models.Board import Board
from game.models.Question import Question
from game.models.QuestionTile import QuestionTile
from game.serializers import QuestionSerializer


class BoardUtils:
    @staticmethod
    def fill_board(board: Board, round: str) -> Board:
        """
        creates question tiles to fill up board
        :param board: Board instance
        :param round: which round to build board for (Jeopardy!, Double Jeopardy!, or Final Jeopardy!)
        :return: newly filled Board instance
        """
        used_categories = []
        for _ in range(board.columns):
            questions, category = [], ''
            while not questions:
                questions, category = Question.get_random_category(
                    excluded_categories=used_categories,
                    num_questions=board.rows,
                    round=round
                )
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
            question_tile_dict = {
                'question': question_dict,
                'alive': question_tile.alive,
                'id': question_tile.id
            }
            board_dict[question_tile.question.category].append(question_tile_dict)
        return board_dict

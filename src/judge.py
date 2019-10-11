import difflib
import editdistance
from re import sub, match
from unidecode import unidecode


class Judge:
    """
    Class that checks and verifies user answers to Questions
    """

    def __init__(self):
        # initialize dictionary
        self.eng_dict = open('support_files/words.txt').read().splitlines()

    '''
    check if user needs to be more specific or less specific in their answer
    :string user_answer: answer given by user
    :string correct_answer: correct answer to question
    '''
    def check_closeness(self, user_answer, correct_answer):
        # this will be either 'more' or 'less' depending on closeness to answer
        closeness = None
        # if user answer has equal or less words than correct answer
        if len(user_answer.split(' ')) <= len(correct_answer.split(' ')):
            closeness = 'more'
        # if both answers have the same number of words we know it's a
        # spelling issue
        elif len(user_answer.split(' ')) == len(correct_answer.split(' ')):
            return 'Please fix your spelling.'
        # if user answer has more words than correct answer
        else:
            closeness = 'less'
        return 'Please be {} specific.'.format(closeness)

    def check_answer(self, question, user_answer, user_name, user_id, wager=None):
        '''
        checks if the answer to a question is correct and updates score accordingly
        :param slack_output: the output we hear coming from slack_output
        :param question: the question object
        :param user_answer: the answer given by user
        :param user_name: name of user answering question
        :param user_id: id of user answering question
        :param wager: optional, the wager if the question is a Daily Double
        '''
        user_address = self.create_user_address(user_name, user_id)
        correct_answer = question.answer
        # check if answer is correct
        answer_check = self.fuzz_answer(user_answer, correct_answer)
        # if answer is close but not wrong
        if answer_check is 'close':
            return user_address + ' ' + \
            self.check_closeness(user_answer, correct_answer)
        # right answer
        elif answer_check is True:
            # award points to user
            if question.daily_double:
                self.user_db.update_score(
                self.user_db.connection, user_name, wager
                )
            else:
                self.user_db.update_score(
                self.user_db.connection, user_name, question.value
                )
            return user_address + \
            ' :white_check_mark: That is correct. The answer is ' \
            +correct_answer
        # wrong answer
        elif answer_check is False:
            # take away points from user
            if question.daily_double and wager:
                self.user_db.update_score(
                self.user_db.connection, user_name, -wager
                )
            else:
                self.user_db.update_score(
                self.user_db.connection, user_name, -question.value
                )
            return user_address + ' :x: Sorry, that is incorrect.'

    # strips answers of extraneous punctuation, whitespace, etc.
    def strip_answer(self, answer):
        # ok, not technically ALL articles
        articles = ['and', 'the', 'an', 'a', 'of']
        '''
        remove casing, we also prefix a space so the next regex will
        catch articles that start the string (otherwise we'd need a
        '^' in addition to a '\s')
        '''
        answer = ' ' + answer.lower()
        # remove diacritical marks
        answer = unidecode(answer)
        # remove anything in parentheses
        # https://stackoverflow.com/questions/17779744/regular-expression-to-get-a-string-between-parentheses-in-javascript
        answer = sub(r'\(([^)]+)\)', '', answer)
        '''
        remove articles and conjunctions that are alone, at the start of
        quotations, or at the beginning of the string
        '''
        for a in articles:
            answer = sub(r'\s{}\s|\"{}\s|^{}\s'.format(a, a, a), ' ', answer)
        # exception for "spelling bee" answers e.g. S-P-E-L-L
        # if ' s-p-e-l-l' in answer:
             #pdb.set_trace()
        if not match(r'\s|\w-\w-.+', answer):
            # replace hyphens with whitespace
            answer = sub(r'-', ' ', answer)
        else:
            answer = sub(r'-', '', answer)
        # remove anything that's not alphanumeric
        answer = sub(r'[^A-Za-z0-9\s]', '', answer)
        # remove apostrophes
        answer = sub(r'\'', '', answer)
        # clean up extra whitespace (change spaces w/more than one space to
        # a single space, and removes leading and trailing spaces)
        answer = sub(r'\s{2,}', ' ', answer)
        answer = sub(r'^\s*|\s*$', '', answer)
        return answer.split(' ')

    # makes list of word-pairs out of given/correct answer arrays (arrays of words)
    # these arrays will always be filtered through strip_answer() first
    def pair_off_answers(self, answer1, answer2):
        matrix = []
        for word in answer1:
            for comp_word in answer2:
                # convert to set so order doesn't matter in pairs and ignore
                # exact matches
                if not set([word, comp_word]) in [set(m) for m in matrix]:
                    matrix.append((word, comp_word))
        return matrix

    '''
    if the word is:
    - long enough
    - in the spell check results for both itself and correct word
    - identical to the correct word
    - one levenshtein distance off from correct word
    then keep looping through the words
    elif word is:
    - in the correct word and long enough or in the correct answer
    - or vice versa (but we dont check if correct word is in given answer)
    then it's close enough
    '''

    def fuzz_word(self, given_word, correct_word):
        given_word, correct_word = given_word.lower(), correct_word.lower()
        if given_word == correct_word:
            return True
        else:
            # use lambda to pare down comparison dictionary
            first_letter_eng_dict = list(filter(lambda x: x[:1] == given_word[:1], self.eng_dict))

            # get lists of close words (spell check)
            check_given_word_closeness = difflib.get_close_matches \
            (given_word, first_letter_eng_dict, n=5, cutoff=0.8)

            check_correct_word_closeness = difflib.get_close_matches \
            (correct_word, first_letter_eng_dict, n=5, cutoff=0.8)

            # remove newline chars from spell check lists
            check_given_word_closeness = sub(r'\n', ' ', ' '.join(check_given_word_closeness)).split(' ')
            check_correct_word_closeness = sub(r'\n', ' ', ' '.join(check_correct_word_closeness)).split(' ')

            # get levenshtein distance
            lev_dist = editdistance.eval(given_word, correct_word)
            # check to see if word is in spell check list for both words
            is_in_both_dicts = given_word in check_given_word_closeness \
            and given_word in check_correct_word_closeness
            # check for proper nouns (in other words: is the word
            # in a standard dictionary?)
            not_in_dict = not given_word in check_given_word_closeness \
            and not given_word in check_correct_word_closeness
            # difference between the lengths of the two words
            length_diff = abs(len(given_word) - len(correct_word))
            # is the length of the guessed word close enough to the correct word?
            is_long_enough = length_diff <= \
            max(len(given_word), len(correct_word)) * 0.3

            if is_long_enough and is_in_both_dicts or lev_dist <= 1:
                return True
            elif is_in_both_dicts and \
            (given_word in correct_word or correct_word in given_word) \
            and lev_dist <= 2:
                return 'close'
            elif not_in_dict and lev_dist <=2 and len(given_word) == len(correct_word):
                return 'close'
            else:
                return False

    # checks if given answer is close enough to correct answer
    # TODO: rename this
    # TODO: make conjunctions/disjunctions behave as logical operators

    def fuzz_answer(self, given_answer, correct_answer):
        # we need a copy of the answer with the parenthesized words left in if the correct answer contains parentheses
        paren_answer = None
        paren_close = 0
        paren_right = 0
        # if we get an empty string, don't bother
        if not given_answer:
            return False
        # exception for single letter answers
        if len(given_answer) == 1 and len(correct_answer) == 1:
            return given_answer == correct_answer
        # TODO: make this handle ampersands, etc.
        # account for slashes
        '''
        if '/' in correct_answer:
            correct_answer = correct_answer.split('/')
        correct_answer = list(correct_answer)
        for answer in correct_answer:
        '''
        # we only want exact matches if the answer is a number
        try:
            # prevents cases like '0' or '00'
            if given_answer.startswith('0'):
                raise ValueError
            elif int(given_answer) != int(correct_answer):
                return False
            elif int(given_answer) == int(correct_answer):
                return True
        except (ValueError):
            # flag if the answer contains parentheses
            parentheses = '(' and ')' in correct_answer
            # total up how many word pair comparisons are right, wrong, etc.
            # that is: is the word close enough to the word we're comparing it to?
            right = 0
            close = 0
            '''
            this gives us two copies of the right answer: one with parentheses and one without
            we check both and use the copy with the higher score
            '''
            if parentheses:
                paren_answer = ''.join(list(filter(lambda x: x not in ['(', ')'], correct_answer)))
                paren_answer = self.strip_answer(paren_answer)
                paren_pair_list = self.pair_off_answers(self.strip_answer(given_answer), paren_answer)
                for pair in paren_pair_list:
                    # check equality first for performance boost
                    result = pair[0] == pair[1] or self.fuzz_word(pair[0], pair[1])
                    if result == 'close':
                        paren_close += 1
                    elif result == True:
                        paren_right += 1
            # remove casing, punctuation, and articles
            given_answer = self.strip_answer(given_answer)
            correct_answer = self.strip_answer(correct_answer)
            pair_list = self.pair_off_answers(given_answer, correct_answer)
            # if 'wells' in given_answer:
                # pdb.set_trace()
            if given_answer == correct_answer or given_answer == paren_answer:
                return True
            # compare pairs and adjust totals accordingly
            for pair in pair_list:
                # check equality first for performance boost
                result = pair[0] == pair[1] or self.fuzz_word(pair[0], pair[1])
                if result == 'close':
                    close += 1
                elif result == True:
                    right += 1
            # use whichever answer copy has the higher score
            if parentheses:
                close = max(paren_close, close)
                right = max(paren_right, right)
            # check if the answer is close enough
            if right >= round(0.75 * max(len(correct_answer), len(given_answer))):
                return True
            # prevents rounding down to 0
            elif right + close >= max(round(0.5 * max(len(correct_answer), len(given_answer))), 1):
                return 'close'
            else:
                return False

import difflib
import editdistance
from re import sub, match
from unidecode import unidecode
from paths import WORDS


class Judge:
    """
    Class that checks and verifies user answers to Questions
    """

    # initialize dictionary
    eng_dict = open(WORDS).read().splitlines()

    @staticmethod
    def check_closeness(user_answer, correct_answer):
        """
        check if user needs to be more specific or less specific in their answer
        :string user_answer: answer given by user
        :string correct_answer: correct answer to question
        """
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

    # strips answers of extraneous punctuation, whitespace, etc.
    @staticmethod
    def strip_answer(answer):
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
        answer = sub(r'\(([^)]+)\)', '', answer)
        '''
        remove articles and conjunctions that are alone, at the start of
        quotations, or at the beginning of the string
        '''
        for a in articles:
            answer = sub(r'\s{}\s|\"{}\s|^{}\s'.format(a, a, a), ' ', answer)
        # exception for "spelling bee" answers e.g. S-P-E-L-L
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
    @staticmethod
    def pair_off_answers(answer1, answer2):
        matrix = []
        for word in answer1:
            for comp_word in answer2:
                # convert to set so order doesn't matter in pairs and ignore
                # exact matches
                if not {word, comp_word} in [{m} for m in matrix]:
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
    @staticmethod
    def fuzz_word(given_word, correct_word):
        given_word, correct_word = given_word.lower(), correct_word.lower()
        if given_word == correct_word:
            return True
        else:
            # use lambda to pare down comparison dictionary
            first_letter_eng_dict = list(filter(lambda x: x[:1] == given_word[:1], Judge.eng_dict))

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

    # TODO: rename this
    @staticmethod
    def fuzz_answer(given_answer, correct_answer):
        """
        checks if given answer is close enough to correct answer
        :param self:
        :param given_answer: answer given by user
        :param correct_answer: correct answer to the Question
        :return: True, False, or 'close' (if answer is close enough but not correct)
        """

        # words/symbols that signify that either answer is correct
        or_words = [' or ', '/', ' / ']
        # if we get an empty string, don't bother
        if not given_answer:
            return False
        # exception for single letter answers
        if len(given_answer) == 1 and len(correct_answer) == 1:
            return given_answer == correct_answer
        # we only want exact matches if the answer is a number
        try:
            # prevents cases like '0' or '00'
            if given_answer.startswith('0'):
                raise ValueError
            elif int(given_answer) != int(correct_answer):
                return False
            elif int(given_answer) == int(correct_answer):
                return True
        except ValueError:
            # single word answers
            if len(given_answer.split(' ')) == 1 and \
               len(correct_answer.split(' ')) == 1 and \
               (given_answer + correct_answer).isalnum():
                return Judge.fuzz_word(correct_answer, given_answer)
            # totals for how many word pair comparisons are right, wrong, etc.
            # that is: is the word close enough to the word we're comparing it to?
            right, close = 0, 0
            answer_is_close = False
            possible_answers = []
            '''
            account for hyphens by providing two versions, one with a space for the hyphen and one without
            e.g: two-toned turns into ('two toned', 'twotoned')
            '''
            # or/and answers
            for w in [word for word in or_words if word in correct_answer]:
                or_split = correct_answer.split(w)
                possible_answers.extend(or_split)
            if '-' in correct_answer:
                possible_answers.append(''.join(correct_answer.split('-')))
                possible_answers.append(' '.join(correct_answer.split('-')))
            # answers with parentheses
            elif '(' and ')' in correct_answer:
                possible_answers.append(''.join(list(filter(lambda x: x not in ['(', ')'], correct_answer))))
            else:
                possible_answers.append(correct_answer)
            # remove casing, punctuation, and articles
            given_answer = Judge.strip_answer(given_answer)
            possible_answers = [Judge.strip_answer(answer) for answer in possible_answers]
            for answer in possible_answers:
                pair_list = Judge.pair_off_answers(given_answer, answer)
                if given_answer == answer:
                    return True
                # compare pairs and adjust totals accordingly
                for pair in pair_list:
                    # check equality first for performance boost
                    result = pair[0] == pair[1] or Judge.fuzz_word(pair[0], pair[1])
                    if result == 'close':
                        close += 1
                    elif result == True:
                        right += 1
                # this lets us get len() by number of words in answer
                print(correct_answer)
                # in case correct_answer is a list
                if type(correct_answer) == str:
                    correct_answer = correct_answer.split()
                # check if the answer is close enough
                # we split correct_answer only because it's a string and given_answer is a list
                if right >= round(0.75 * max(len(correct_answer), len(given_answer))):
                    return True
                # prevents rounding down to 0
                elif right + close >= max(round(0.5 * max(len(correct_answer), len(given_answer))), 1):
                    answer_is_close = True
                else:
                    right, close = 0, 0
            if answer_is_close:
                return 'close'
            else:
                return False

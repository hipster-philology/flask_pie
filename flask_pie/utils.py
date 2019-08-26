from pie.tagger import simple_tokenizer
from typing import Callable, Iterable, List, Tuple
import string
import re


Tokenizer = Callable[[str, bool], Iterable[List[str]]]
PUNKT = re.compile("^["+string.punctuation+"]+$")


class DataIterator:
    def __init__(self, tokenizer: Tokenizer = None, remove_from_input: Callable = None):
        """ Iterator used to parse the text and returns bits to tag

        :param tokenizer: Tokenizer
        """
        self.tokenizer = tokenizer or simple_tokenizer
        self.remove_from_input = remove_from_input
        if self.remove_from_input is None:
            self.remove_from_input = lambda x: (x, {})

    @staticmethod
    def remove_punctuation(sentence: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
        """ Removes punctuation from a list and keeps its index

        :param sentence:
        :return: First the sentence with things removed, then the list of things to reinsert with their index

        >>> from flask_pie.utils import DataIterator
        >>> x = DataIterator.remove_punctuation(["Je", "suis", "content",",", "mais", "...", '"', "fatigué", '"', "."])
        >>> assert x == (['Je', 'suis', 'content', 'mais', 'fatigué'], [(',', 3), ('...', 5),
        >>>    ('"', 6), ('"', 8), ('.', 9)])
        """
        clean, removed = [], {}
        for index, token in enumerate(sentence):
            if PUNKT.match(token):
                removed[index] = token
            else:
                clean.append(token)
        return clean, removed

    def __call__(self, data: str, lower: bool = False) -> Iterable[Tuple[List[str], int]]:
        """ Default iter data takes a text, an option to make lower
        and yield lists of words along with the length of the list

        :param data: A plain text
        :param lower: Whether or not to lower the text
        :yields: (Sentence as a list of word, Size of the sentence)
        """
        for sentence in self.tokenizer(data, lower=lower):
            clean_sentence, removed_from_input = self.remove_from_input(sentence)
            yield clean_sentence, len(clean_sentence), removed_from_input


class Formatter:  # Default is TSV
    def __init__(self, tasks: List[str]):
        self.tasks: List[str] = tasks

    def format_line(self, token: str, tags: Iterable[str], ignored=False) -> List[str]:
        """ Format the tags"""
        return [token] + list(tags)

    def write_line(self, formatted):
        return "\t".join(formatted) + "\r\n"

    def write_sentence_beginning(self) -> str:
        return ""

    def write_sentence_end(self) -> str:
        return ""

    def write_footer(self) -> str:
        return ""

    def get_headers(self):
        return ["token"] + self.tasks

    def write_headers(self)-> str:
        """ Format the headers """
        return self.write_line(self.get_headers())


class MemoryzingTokenizer(object):
    @staticmethod
    def _sentence_tokenizer(string):
        for s in string.split("."):
            if s.strip():
                yield s.strip() + " " + "."

    @staticmethod
    def _word_tokenizer(string):
        for s in string.split():
            if s.strip:
                yield s.strip()

    @staticmethod
    def _replacer(inp: str):
        return inp

    def __init__(self, sentence_tokenizer=None, word_tokenizer=None, replacer=None):
        self.tokens = [
        ]

        self.sentence_tokenizer = sentence_tokenizer or self._sentence_tokenizer
        self.word_tokenizer = word_tokenizer or self._word_tokenizer
        self.replacer = replacer or self._replacer

    def __call__(self, data, lower=True):
        if lower:
            data = data.lower()

        for sentence in self.sentence_tokenizer(data):
            toks = self.word_tokenizer(sentence)
            new_sentence = []

            for tok in toks:
                out = self.replacer(tok)
                self.tokens.append((len(self.tokens), tok, out))
                new_sentence.append(out)

            yield new_sentence

from pie.tagger import simple_tokenizer
from typing import Callable, Iterable, List, Tuple


Tokenizer = Callable[[str, bool], Iterable[List[str]]]


class DataIterator:
    def __init__(self, tokenizer: Tokenizer = None):
        """ Iterator used to parse the text and returns bits to tag

        :param tokenizer: Tokenizer
        """
        self.tokenizer = tokenizer or simple_tokenizer

    def __call__(self, data: str, lower: bool = False) -> Iterable[Tuple[List[str], int]]:
        """ Default iter data takes a text, an option to make lower
        and yield lists of words along with the length of the list

        :param data: A plain text
        :param lower: Whether or not to lower the text
        :yields: (Sentence as a list of word, Size of the sentence)
        """
        for sentence in self.tokenizer(data, lower=lower):
            yield sentence, len(sentence)


class Formatter:
    def __init__(self, tasks: List[str]):
        self.tasks = tasks

    def format_headers(self)-> List[str]:
        """ Format the headers """
        return ["token"] + self.tasks

    def format_line(self, token: str, tags: Iterable[str]) -> List[str]:
        """ Format the tags"""
        return [token] + list(tags)


class MemoryzingTokenizer(object):
    @staticmethod
    def _sentence_tokenizer(string):
        for s in string.split("."):
            if s.strip():
                yield s.strip()

    @staticmethod
    def _word_tokenizer(string):
        for s in string.split():
            if s.strip:
                yield s.strip()

    @staticmethod
    def _replacer(inp: str):
        inp = inp.replace("U", "V").replace("v", "u").replace("J", "I").replace("j", "i")
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

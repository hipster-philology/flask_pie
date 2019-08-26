from ..utils import MemoryzingTokenizer


class LatinMemoryTokenizer(MemoryzingTokenizer):
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


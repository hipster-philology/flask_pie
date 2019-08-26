import regex as re
from ..utils import Formatter


class GlueFormatter(Formatter):
    """ Need replacing of morph_part for specific corpora

    """

    HEADERS = ["form", "lemma", "POS", "morph", "treated_token"]
    MORPH_PART = ["Case", "Numb", "Deg", "Mood", "Tense", "Voice", "Person"]
    PONCTU = re.compile("\W")

    def __init__(self, tokenizer_memory):
        super(GlueFormatter, self).__init__([])
        self.tokenizer_memory = tokenizer_memory

    def __call__(self, tasks):
        super(GlueFormatter, self).__init__(tasks)
        self.pos_tag = "POS"
        if "POS" not in self.tasks and "pos" in self.tasks:
            self.pos_tag = "pos"
        return self

    def format_headers(self):
        return GlueFormatter.HEADERS

    def format_line(self, token, tags, ignored=False):
        tags = list(tags)
        lemma = tags[self.tasks.index("lemma")]
        input_token = out_token = token

        if ignored is False:
            index, input_token, out_token = self.tokenizer_memory.tokens.pop(0)
            if token != out_token:
                raise Exception("The output token does not match our inputs %s : %s" % (token, out_token))

        if GlueFormatter.PONCTU.match(token):
            return [
                token,
                token,
                "PUNC",
                "MORPH=empty",
                token
            ]

        return [
            input_token,
            lemma.upper().replace("U", "V"),
            tags[self.tasks.index(self.pos_tag)],
            "|".join(
                "{cat}={tag}".format(
                    cat=morph_part,
                    tag=tags[self.tasks.index(morph_part)]
                )
                for morph_part in GlueFormatter.MORPH_PART
                if morph_part in self.tasks and
                tags[self.tasks.index(morph_part)] != "_"
            ) or "MORPH=empty",
            out_token
        ]

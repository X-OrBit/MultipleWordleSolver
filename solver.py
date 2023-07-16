import random
from dict_utils import load_dict
from typing import Optional
from collections import UserString

ALPHABET = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'


class Word(UserString):
    def __setitem__(self, key: int, value: str):
        assert len(value) == 1
        assert 0 <= key < len(self)
        self.data = self.data[:key] + value + self.data[key + 1:]

    def __delitem__(self, key: int):
        assert 0 <= key < len(self)
        self.data = self.data[:key] + self.data[key + 1:]

    def __getitem__(self, key):
        if isinstance(key, slice):
            return super().__getitem__(key)
        return self.data[key]

    def is_fit(self, other: 'Word', pattern: str, max_chars: Optional[dict[str, int]] = None) -> bool:
        assert len(self) == len(other)
        count = {}
        for i in range(len(pattern)):
            if pattern[i] == '+':
                if self[i] != other[i]:
                    return False
                continue
            if self[i] == other[i]:
                return False
            count[self[i]] = count.get(self[i], 0) + 1
        return max_chars is None or all(max_chars.get(c) is None or cnt <= max_chars[c] for c, cnt in count.items())


def copy_word_list(word_list: list[Word]):
    return [Word(word) for word in word_list]


class Solver:
    left_words: list[list[Word]]
    matched_words = list[list[Word]]
    max_chars = list[str, int]
    word_shadows = list[Word]

    def __init__(self, dict_path: str, word_sizes: list[int]):
        self.word_sizes = word_sizes
        self.dict = {size: [Word(word) for word in load_dict(dict_path, size)] for size in set(word_sizes)}
        self.reset()

    def reset(self):
        self.left_words = [copy_word_list(self.dict[size]) for size in self.word_sizes]
        self.matched_words = [Word(word_size) for word_size in self.word_sizes]
        self.max_chars = {c: None for c in ALPHABET}
        self.word_shadows = [Word('_' * word_size) for word_size in self.word_sizes]

    def get_left_words(self, left_words, word: Word, pattern: str) -> list[Word]:
        new_left_words = []
        for left_word in left_words:
            if left_word.is_fit(word, pattern, self.max_chars):
                new_left_words.append(left_word)
        return new_left_words

    def get_best_guesses(self, cnt: int = 5) -> list[list[Word]]:
        raise NotImplementedError()

    def get_random_guesses(self, cnt: int = 5) -> list[list[Word]]:
        return [random.sample(self.left_words[i], cnt) if len(self.left_words[i]) >= cnt else self.left_words[i] for i in range(len(self.word_sizes))]

    def update_max_chars(self, words: list[Word], patterns: list[str]):
        word = ''.join(map(str, words))
        pattern = ''.join(patterns)
        counts = {}
        fixed = set()
        for i in range(len(pattern)):
            if pattern[i] == '+':
                continue
            if pattern[i] == '-':
                fixed.add(word[i])
            if pattern[i] == '?':
                counts[word[i]] = counts.get(word[i], 0) + 1
        for c in fixed:
            self.max_chars[c] = counts.get(c, 0)

    def update_left_words(self, words: list[Word], patterns: list[str]):
        new_left_words = []
        for index in range(len(self.word_sizes)):
            new_left_words.append(self.get_left_words(self.left_words[index], words[index], patterns[index]))
        self.left_words = new_left_words

    def update_shadow(self, words: list[Word], patterns: list[str]):
        for index in range(len(words)):
            for i in range(len(words[index])):
                if patterns[index][i] != '+':
                    continue
                self.word_shadows[index][i] = words[index][i]
            if len(self.left_words[index]) == 1:
                self.word_shadows[index] = self.left_words[index][0]

    def update(self, words: list[Word], patterns: list[str]):
        self.update_max_chars(words, patterns)
        self.update_left_words(words, patterns)
        self.update_shadow(words, patterns)

    def get_word_shadows(self) -> list[Word]:
        return self.word_shadows

    def is_correct_sizes(self, strings: list[str]) -> bool:
        return len(strings) == len(self.word_sizes) and all([len(strings[i]) == word_size for i, word_size in enumerate(self.word_sizes)])

    def answer(self):
        return self.word_shadows if self.is_finished() else [None] * len(self.word_sizes)

    def is_finished(self):
        return '_' not in ''.join(map(str, self.word_shadows))

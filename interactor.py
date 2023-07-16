import re
import requests
import json

from typing import Optional

from solver import Solver, Word

MAIN_URL = 'https://its-gnvoerk-vts21o2l.spbctf.ru/'
API_URL = 'https://its-gnvoerk-vts21o2l.spbctf.ru/check'


class Interactor:
    def __init__(self, solver: Solver):
        self.solver = solver


class RequestInteractor(Interactor):
    def __init__(self, solver: Solver):
        super().__init__(solver)
        self.last_words = []
        self.current_pointer = []
        self.session = requests.session()

    def update_guesses(self):
        self.last_words = self.solver.get_random_guesses()
        self.current_pointer = [0] * len(self.last_words)

    def try_guess(self) -> dict:
        shadows = self.solver.get_word_shadows()
        print("New try\n" + '\n'.join([
            f"{i + 1} {shadows[i]} Guesses: {' '.join([f'>{guess}<' if index == self.current_pointer[i] else str(guess) for index, guess in enumerate(self.last_words[i])])}"
            for i in range(len(self.last_words))
        ]))
        current_guess = '-'.join([str(last_words[self.current_pointer[i]]) for i, last_words in enumerate(self.last_words)])
        r = self.session.post(API_URL, data={
            'words': current_guess
        })
        print(current_guess)
        try:
            response = json.loads(json.dumps(r.json(), ensure_ascii=False))
        except requests.exceptions.JSONDecodeError:
            print(r.status_code, r.text)
            exit(0)
        if r.status_code == 200 and response.get('next') == 'next' or response.get('win') == 'win':
            response['words'] = current_guess.split('-')
            response['status'] = 'finished'
            if 'flag' in response:
                print('FLAG', response['flag'])
            return response
        if r.status_code == 472:
            for index in range(len(self.current_pointer)):
                if self.last_words[index][self.current_pointer[index]] in response['words']:
                    self.current_pointer[index] += 1
            return {'status': 'retry'}
        response['words'] = current_guess.split('-')
        response['status'] = 'ok'
        return response

    def send_guesses(self):
        while (response := self.try_guess())['status'] == 'retry':
            pass
        return response

    def __generate_patterns(self, response: dict):
        global_word = ''.join(response['words'])

        if response.get('next') == 'next' or response.get('win') == 'win':
            global_pattern = Word('+' * sum(self.solver.word_sizes))
        else:
            global_pattern = Word('-' * sum(self.solver.word_sizes))
            for pos in response['all_positions']:
                global_pattern[int(pos)] = '+'

            for char, count in response['existence'].items():
                for i in range(len(global_pattern)):
                    if global_word[i] == char and global_pattern[i] == '-':
                        global_pattern[i] = '?'
                        count -= 1
                    if count <= 0:
                        break

        patterns = []
        sm = 0
        for word_size in self.solver.word_sizes:
            patterns.append(str(global_pattern[sm:sm + word_size]))
            sm += word_size
        return patterns

    def update_solver(self, response: dict):
        words = [Word(word) for word in response['words']]
        patterns = self.__generate_patterns(response)
        print('Guess:  ', ' '.join(response['words']))
        print('Pattern:', ' '.join(patterns))
        self.solver.update(words, patterns)

    def one_tour(self):
        while True:
            self.update_guesses()
            response = self.send_guesses()
            if response['status'] == 'finished':
                self.update_solver(response)
                break
            self.update_solver(response)
        print('Tour finished')
        print(f"Answer: {' '.join(map(str, self.solver.answer()))}")

    def play_tours(self, count: int):
        for tour in range(count):
            self.one_tour()
            print('\n' * 5, '-' * 10, '[RESET]', '-' * 10, '\n', sep='')
            self.solver.reset()

    def start(self):
        self.session.get(MAIN_URL)
        print('Cookies:', self.session.cookies.items())
        # try:
        self.play_tours(10)
        # except Exception as e:
            # print(e)
            # print('Cookies:', self.session.cookies.items())


class ConsoleInteractor(Interactor):
    def __init__(self, solver: Solver):
        super().__init__(solver)
        self.last_words = []

    def update_guesses(self):
        self.last_words = self.solver.get_random_guesses()

    def print_guesses(self):
        shadows = self.solver.get_word_shadows()
        print('\n'.join([f"{i + 1} {shadows[i]} Guesses: {' '.join(map(str, self.last_words[i]))}" for i in range(len(self.last_words))]))

    def get_words(self) -> (list[Word], list[str]):
        words, patterns = [], []
        while True:
            inp = input()
            if not re.fullmatch(r'[\sа-яА-ЯёЁ]+', inp):
                print('Incorrect')
                continue
            words = re.sub(r'\s+', ' ', inp).lower().split()
            if not self.solver.is_correct_sizes(words):
                print('Incorrect')
                continue
            break
        while True:
            inp = input()
            if not re.fullmatch(r'[\s+\-?]+', inp):
                print('Incorrect')
                continue
            patterns = re.sub(r'\s+', ' ', inp).lower().split()
            if not self.solver.is_correct_sizes(patterns):
                print('Incorrect')
                continue
            break
        return [Word(word) for word in words], patterns

    def update_solver(self, words: list[Word], patterns: list[str]):
        self.solver.update(words, patterns)

    def start(self):
        while not self.solver.is_finished():
            self.update_guesses()
            self.print_guesses()
            words, patterns = self.get_words()
            self.update_solver(words, patterns)
        print('Finished!')
        print(f"Answer: {' '.join(map(str, self.solver.answer()))}")


class FileInteractor(Interactor):
    def __init__(self, solver: Solver, path: str):
        super().__init__(solver)
        self.last_words = []

        self.move_index = 0
        self.guesses = []
        self.patterns = []
        self.load_moves(path)

    def load_moves(self, path: str):
        self.move_index = 0
        with open(path, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]
            for i in range(0, len(lines), 2):
                self.guesses.append(lines[i].split(' '))
                self.patterns.append(lines[i + 1].split(' '))

    def update_guesses(self):
        self.last_words = self.solver.get_random_guesses()

    def print_guesses(self):
        shadows = self.solver.get_word_shadows()
        print('\n'.join([f"{i + 1} {shadows[i]} Guesses: {' '.join(map(str, self.last_words[i]))}" for i in range(len(self.last_words))]))

    def get_words(self) -> (list[Word], list[str]):
        words, patterns = self.guesses[self.move_index], self.patterns[self.move_index]
        print('Guess:   ', ' '.join(words))
        print('Patterns:', ' '.join(patterns))
        return words, patterns

    def update_solver(self, words: list[Word], patterns: list[str]):
        self.solver.update(words, patterns)
        self.move_index += 1

    def start(self):
        while not self.solver.is_finished():
            self.update_guesses()
            self.print_guesses()
            words, patterns = self.get_words()
            self.update_solver(words, patterns)
        print('Finished!')
        print(f"Answer: {' '.join(map(str, self.solver.answer()))}")

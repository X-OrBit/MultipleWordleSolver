from typing import Optional
import os


def convert(path: str):
    with open(path, 'r', encoding='utf-8') as file:
        words = [line.split('	')[0].strip() for line in file.readlines() if line.strip()]
    with open(path.split('.')[0] + '_converted.txt', 'w', encoding='utf-8') as file:
        file.write('\n'.join(words))


def load_dict(path: str, word_size: Optional[int] = None):
    with open(path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip() and (word_size is None or len(line.strip()) == word_size)]


def save_dict(words: list[str], path: str):
    with open(path, 'w', encoding='utf-8') as file:
        file.write('\n'.join(words))


def sort(path: str):
    words = load_dict(path)
    words.sort(key=lambda x: (len(x), x))
    save_dict(words, path)


def remove_dashes(path: str):
    words = load_dict(path)
    words = [word for word in words if '-' not in word]
    save_dict(words, path)


def to_lower(path: str):
    words = load_dict(path)
    words = [word.lower() for word in words]
    save_dict(words, path)


def replace_yo(path: str):
    words = load_dict(path)
    words = [word.replace('ё', 'е') for word in words]
    save_dict(words, path)


def remove_copies(path: str):
    words = load_dict(path)
    words = list(set(words))
    save_dict(words, path)


def main():
    # convert('nouns.csv')
    # os.rename('nouns_converted.txt', 'rus.txt')
    remove_dashes('rus.txt')
    replace_yo('rus.txt')
    to_lower('rus.txt')
    remove_copies('rus.txt')
    sort('rus.txt')
    print('\n'.join(load_dict('rus.txt', 5)))


if __name__ == '__main__':
    main()

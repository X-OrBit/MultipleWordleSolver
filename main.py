import time
from solver import Solver
from interactor import ConsoleInteractor, RequestInteractor, FileInteractor


def main():
    start = time.time()
    solver = Solver('rus.txt', [5] * 5)
    interactor = RequestInteractor(solver)
    # interactor = FileInteractor(solver, 'moves.txt')
    interactor.start()
    print('Time:', time.time() - start)


if __name__ == '__main__':
    main()

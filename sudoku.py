from collections import deque
import random
import copy
import math

class Sudoku:
    def __init__(self, puzzle):
        self.N = 9
        self.H = 3
        self.W = 3
        self.symbols = {i for i in "123456789"}

        self.row_idxs = {}
        self.col_idxs = {}
        self.block_idxs = {}
        self.neighbors = {}

        self.pos_list = {}
        
        # Load in row, col, block groups
        for x in range(self.N):
            self.row_idxs[x] = set()
            self.col_idxs[x] = set()
            self.block_idxs[x] = set()
        for x in range(self.N * self.N):
            self.row_idxs[x // self.N].add(x)
            self.col_idxs[x % self.N].add(x)
            a = int((x % self.N) // self.W)
            b = x // (self.H * self.N)
            self.block_idxs[int(a + b * (self.N // self.W))].add(x)
            self.neighbors[x] = self.row_idxs[x // self.N] | self.col_idxs[x % self.N] | self.block_idxs[a + b * (self.N // self.W)]

    def solve(self, puzzle):
        self.create_constraint(puzzle)
        changes = set()
        for i in range(self.N * self.N):
            if len(self.pos_list[i]) == 1 and puzzle[i] == '.':
                changes.add(i)
        constraint_set = self.pos_list.copy()
        puzzle = self.forward_looking(puzzle, constraint_set, changes)
        puzzle = self.constraint_propagation(puzzle, constraint_set)
        puzzle = self.sudoku_back_with_forward(puzzle, constraint_set)
        return puzzle

    def create_constraint(self, puzzle):
        drow = {}
        dcol = {}
        dblock = {}
        for i in range(0, self.N):
            drow[i] = set()
            dcol[i] = set()
            dblock[i] = set()
        for i in range(self.N * self.N):
            a = int((i % self.N) // self.W)
            b = i // (self.H * self.N)
            if not puzzle[i] == '.':
                drow[i // self.N].add(puzzle[i])
                dcol[i % self.N].add(puzzle[i])
                dblock[int(a + b * (self.N // self.W))].add(puzzle[i])
        for i in range(self.N * self.N):
            if not puzzle[i] == '.':
                self.pos_list[i] = puzzle[i]
            else:
                ret = ''
                a = (i % self.N) // self.W
                b = i // (self.H * self.N)
                dtot = drow[i // self.N] | dcol[i % self.N] | dblock[a + b * (self.N // self.W)]
                for k in self.symbols:
                    if k not in dtot:
                        ret += k
                self.pos_list[i] = ret
    
    # checks board is filled properly
    def gut_check(self, puzzle):
        for x in self.symbols:
            ct = puzzle.count(x)
            if ct != self.N:
                return False
        return True

    # returns most constrained cell index
    def get_next_unassigned_var(self, constraints):
        smallest = 9
        min_constraint = [0]
        for i in range(self.N * self.N):
            constraint_len = len(constraints[i])
            if constraint_len > 1 and constraint_len < smallest:
                smallest = constraint_len
                min_constraint = [i]
            if constraint_len == smallest:
                min_constraint.append(i)
        return random.choice(min_constraint)

    # pretty prints the puzzle
    def display_puzzle(self, puzzle):
        n = ''
        for x in range(self.N):
            for y in range(self.N):
                if y % self.W == 0 and not y == 0:
                    n += '| '
                n += puzzle[x * self.N + y] + ' '
            n += '\n'
            if (x + 1) % self.H == 0 and not (x + 1) == self.N:
                n += '-' * (self.W * 2) + '+'
                for _ in range(self.H - 2):
                    n += '-' * (self.W * 2 + 1) + '+'
                n += '-' * (self.W * 2) + '\n'
        print(n)

    def forward_looking(self, puzzle, constraints, changed):
        if puzzle == None:
            return None
        puzzle = list(puzzle)
        while len(changed) > 0:
            x = changed.pop()
            for y in self.neighbors[x]:
                if not y == x:
                    if constraints[x] in constraints[y]:
                        ind_of_value = constraints[y].index(constraints[x])
                        constraints[y] = constraints[y][:ind_of_value] + constraints[y][ind_of_value + 1:]
                        if len(constraints[y]) == 0:
                            return None
                        if len(constraints[y]) == 1 and puzzle[y] == '.':
                            puzzle[y] = constraints[y]
                            changed.add(y)
        puzzle = ''.join(puzzle)
        return puzzle

    def constraint_propagation(self, puzzle, constraints):
        changes = set()
        if self.gut_check(puzzle):
            return puzzle
        puzzle = list(puzzle)
        for x in range(self.N):
            for pos_num in self.symbols:
                for cons in [self.row_idxs, self.col_idxs, self.block_idxs]:
                    con_count = 0
                    con_index = -1
                    for constraint_pos in cons[x]:
                        constraint_pos = int(constraint_pos)
                        if pos_num in constraints[constraint_pos]:
                            con_count += 1
                            con_index = constraint_pos
                        if con_count > 1:
                            break
                    if con_count == 1:
                        constraints[con_index] = str(pos_num)
                        puzzle[con_index] = str(pos_num)
                        changes.add(con_index)
                    elif con_count == 0:
                        return None

        new_puzzle = ''.join(puzzle)
        if len(changes) > 0:
            return self.forward_looking(new_puzzle, constraints, changes)
        else:
            return new_puzzle

    def sudoku_back_with_forward(self, puzzle, constraints):
        # self.display_puzzle(puzzle)
        if self.gut_check(puzzle):
            return puzzle
        # finds empty spaces, returns most constrained
        var = self.get_next_unassigned_var(constraints)
        # chooses most constrained cell, places one of the possible values
        for k in constraints[var]:
            new_puzzle = puzzle[:var] + k + puzzle[var + 1:]
            new_constraints = constraints.copy()
            new_constraints[var] = k
            # forward looking
            new_puzzle = self.forward_looking(new_puzzle, new_constraints, {var})
            if new_puzzle is not None:
                # constraint propagation
                new_puzzle = self.constraint_propagation(new_puzzle, new_constraints)
                if new_puzzle is not None:
                    updated_constraints = new_constraints.copy()
                    # repeat process with recursion
                    f_result = self.sudoku_back_with_forward(new_puzzle, updated_constraints)
                    if f_result is not None:
                        return f_result
        return None

import sys
import sudoku
import cv2
import numpy as np
import convert
import imutils
from werkzeug.utils import secure_filename


class Solver: 
    def __init__(self, imagePath):
        image = cv2.imread(imagePath)
        image = imutils.resize(image, width=600)
        self.image = image
        conv = convert.Converter(image)
        boardStr, cellLocs, originalLocs = conv.find_puzzle()
        self.puzzleImage = conv.getPuzzleImage()
        self.boardStr = boardStr
        self.cellLocs = cellLocs
        self.originalLocs = originalLocs

    def solve(self):
        game = sudoku.Sudoku(self.boardStr)
        # game.display_puzzle(self.board)
        solved = game.solve(self.boardStr)
        return solved

    def displaySolved(self):
        complete = self.solve()
        solved = np.array(list(complete)).reshape(9,9)
        for (cellRow, boardRow) in zip(self.cellLocs, solved):
        # loop over individual cell in the row
            for (box, digit) in zip(cellRow, boardRow):
                # unpack the cell coordinates
                startX, startY, endX, endY = box
                # compute the coordinates of where the digit will be drawn
                # on the output puzzle image
                textX = int((endX - startX) * 0.33)
                textY = int((endY - startY) * -0.2)
                textX += startX
                textY += endY
                # draw the result digit on the Sudoku puzzle image
                if box not in self.originalLocs:
                    cv2.putText(self.puzzleImage, str(digit), (textX, textY),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        return self.puzzleImage
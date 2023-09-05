from imutils.perspective import four_point_transform
from skimage.segmentation import clear_border
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
import keras
import numpy as np
import imutils
import cv2
from PIL import Image
import pytesseract
from number_recognition import NumberRecognizer

class Converter:
    def __init__(self, image):
        self.image = image
        self.puzzleImage = None
        self.warped = None
    def find_puzzle(self):
        # convert the image to grayscale and blur it slightly
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 3)
        # apply adaptive thresholding and then invert the threshold map
        thresh = cv2.adaptiveThreshold(blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        thresh = cv2.bitwise_not(thresh)
    
        # find contours in the thresholded image and sort them by size in
        # descending order
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        # initialize a contour that corresponds to the puzzle outline
        puzzleCnt = None
        # loop over the contours
        for c in cnts:
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            # if our approximated contour has four points, then we can
            # assume we have found the outline of the puzzle
            if len(approx) == 4:
                puzzleCnt = approx
                break

    # if the puzzle contour is empty then our script could not find
        # the outline of the Sudoku puzzle so raise an error
        if puzzleCnt is None:
            raise Exception(("Could not find Sudoku puzzle outline. "))
        # apply a four point perspective transform to both the original
        # image and grayscale image to obtain a top-down bird's eye view
        # of the puzzle
        puzzle = four_point_transform(self.image, puzzleCnt.reshape(4, 2))
        warped = four_point_transform(gray, puzzleCnt.reshape(4, 2))
        # return a 2-tuple of puzzle in both RGB and grayscale
        # find the puzzle in the image and then
        # (self.puzzleImage, self.warped) = self.find_puzzle()
        self.puzzleImage = puzzle
        self.warped = warped
        # initialize our 9x9 Sudoku board
        board = np.zeros((9, 9), dtype="int")
        # a Sudoku puzzle is a 9x9 grid (81 individual cells), so we can
        # infer the location of each cell by dividing the warped image
        # into a 9x9 grid
        stepX = warped.shape[1] // 9
        stepY = warped.shape[0] // 9
        # initialize a list to store the (x, y)-coordinates of each cell location
        cellLocs = []
        originalLocs = set()
        # loop over the grid locations
        for y in range(0, 9):
        # initialize the current list of cell locations
            row = []
            for x in range(0, 9):
                # compute the starting and ending (x, y)-coordinates of the
                # current cell
                startX = x * stepX
                startY = y * stepY
                endX = (x + 1) * stepX
                endY = (y + 1) * stepY
                # add the (x, y)-coordinates to our cell locations list
                row.append((startX, startY, endX, endY))
                # crop the cell from the warped transform image and then
                # extract the digit from the cell
                cell = warped[startY:endY, startX:endX]
                digit = self.extract_digit(cell)
                # verify that the digit is not empty
                if digit is not None:
                    originalLocs.add((startX, startY, endX, endY))
                    # invert image colors
                    digit = cv2.resize(digit, (28, 50))
                    digit = cv2.bitwise_not(digit)
                    # cv2_imshow(digit)
                    # classify the digit and update the Sudoku board with ocr
                    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                    preds = {}
                    for i in [6, 7, 10]:
                        guess = pytesseract.image_to_string(digit, config=f'--psm {i} --oem 3 -c tessedit_char_whitelist=0123456789').strip()
                        # print(guess) 
                        if guess == "":
                            if guess in preds:
                                preds["1"] += 1
                            else:
                                preds["1"] = 1
                        else:
                            if guess in preds:
                                preds[guess] += 1
                            else:
                                preds[guess] = 1
                    pred = sorted(preds, key=lambda i: preds[i], reverse=True)[0]
                    pred = pred.replace("{", "1")
                    pred = pred.replace("|", "1")
                    pred = pred.replace("&", "8")
                    pred = pred.replace("41", "1")
                    pred = pred.replace("Z", "3") 
                    board[y, x] = int(pred)
                    # guess = pytesseract.image_to_string(digit, config="digits").strip()
                    # print("GUESS:", guess)
                    # model = keras.models.load_model('cnn-mnist-model.h5')
                    # batch = np.array([[digit]])  # Create a batch (batch_size * size * size * color_channel)
                    # guess = model.predict(digit, verbose=0)
                    # board[y, x] = guess
            # add the row to our cell locations
            cellLocs.append(row)
        board = board.flatten()
        board = "".join(str(board)[1:-1].split()).replace("0", ".")
        print(board)
        return board, cellLocs, originalLocs

    def extract_digit(self, cell):
        # apply automatic thresholding to the cell and then clear any
        # connected borders that touch the border of the cell
        thresh = cv2.threshold(cell, 0, 255,
            cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        thresh = clear_border(thresh)
        # find contours in the thresholded cell
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        # if no contours were found than this is an empty cell
        if len(cnts) == 0:
            return None
        # otherwise, find the largest contour in the cell and create a
        # mask for the contour
        c = max(cnts, key=cv2.contourArea)
        mask = np.zeros(thresh.shape, dtype="uint8")
        cv2.drawContours(mask, [c], -1, 255, -1)
        # compute the percentage of masked pixels relative to the total
        # area of the image
        (h, w) = thresh.shape
        percentFilled = cv2.countNonZero(mask) / float(w * h)
        # if less than 3% of the mask is filled then we are looking at
        # noise and can safely ignore the contour
        if percentFilled < 0.03:
            return None
        # apply the mask to the thresholded cell
        digit = cv2.bitwise_and(thresh, thresh, mask=mask)
        # return the digit to the calling function
        return digit
    
    def getPuzzleImage(self):
        return self.puzzleImage



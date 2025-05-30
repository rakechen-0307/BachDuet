from PyQt5 import QtGui, QtCore, QtSvg
from PyQt5.QtWidgets import (QMainWindow, QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget,QLCDNumber, QDoubleSpinBox,QGraphicsItem, QGraphicsItemGroup, QGraphicsEllipseItem, QGraphicsObject, QGraphicsLineItem,
                         QGraphicsScene, QGraphicsView, QStyle, QWidget, QLabel, QHBoxLayout, QMenuBar, QTextEdit, QGridLayout, QAction, QActionGroup, QToolBar, QToolBox, QToolButton)
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt, pyqtSlot, QThread, QPointF, QRectF, QLineF, QRect
from PyQt5.QtGui import (QPen, QTransform)
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgWidget
import pickle
import copy
class Memory(QObject):
    """
    Memory keeps the whole generated result.

    It maintains the self.history list, with all the notes 
    played so far. It updates this list in sync with the clock.

    Attributes
    ----------
    parent : QWidget()
        A pointer to the parent object BachDuet()
    notesDict : dict()
        notesDict contains all the information about the spelling
        of a midi note, depending on the current key. I.e midi note
        61 is a C# in the contxt of A major, but Db in the context 
        of Eb major.
    experimentPath : pathlib.Path()
        The path of the current session/experiment, so the memory
        module knows where to save the results when needed
    
    Methods
    -------
    saveHistory() : None
        A slot, which is activated when the user a) presses the "save" 
        button, b) presses the "reset" button, or c) closes the app
        Every time it saves the history, it emptys the self.history list
    getNewNoteEvent(currentNotes) : None
        A slot, which is activated by a signal emitted from Manager()
        on every clock "tick". It receives the last notes (currentNotes)
        from all the agents/players and pushes them in the self.history list

    """
    def __init__(self, parent, notesDict, experimentPath):
        super().__init__()
        self.parent = parent
        self.notesDict = notesDict
        self.experimentPath = experimentPath
        # During one session/expeirment, the user may save the result
        # multiple times. This counter ensures the saved files have
        # different names
        self.savesCounter=1
        # the actual history list. On every clock "tick" if will be 
        # filled with a dictionary which contains info about the notes
        # played in that "tick"
        self.history = []
    @pyqtSlot()
    def saveHistory(self):
        # before dumping the list in a file, we add a final element
        # which contains information about the type of players involved
        infos = [player.modules['asyncModule'].info for player in self.parent.players if player.type != 'metronome']
        self.history.append({
            'title' : self.parent.sessionName,
            'info' : {
                'player1' : infos[0],
                'player2' : infos[1]
            }
        })
        with open(self.experimentPath / f'generatedDuet{self.savesCounter}.dict', 'wb') as f :
            pickle.dump(self.history, f)
        self.savesCounter+=1
        self.history = []
    @pyqtSlot(list)
    def getNewNoteEvent(self, currentNotes):
        [newNoteDnn, newNoteKeyboard, newMetronomeBeep] = currentNotes
        newNoteDnn = copy.deepcopy(newNoteDnn)
        newNoteKeyboard = copy.deepcopy(newNoteKeyboard)
        keyString = newNoteDnn['keyEstimation']
        
        #TODO make a for loop over all players
        #### FIRST FOR DNN
        midiNumber = newNoteDnn['midi']
        if (keyString is not None) and (keyString != 'None'):
            primOrSec = 'primary' if keyString in self.notesDict[midiNumber]['primary']['keys'] else 'secondary'
        else:
            primOrSec = 'primary'
        noteAddProps = self.notesDict[midiNumber][primOrSec]
        newNoteDnn['dpc'] = noteAddProps['dpc']
        newNoteDnn['acc'] = noteAddProps['acc']
        newNoteDnn['octave'] = noteAddProps['octave']
        newNoteDnn['name'] = noteAddProps['name']
        #### THEN FOR HUMAN ####
        midiNumber2 = newNoteKeyboard['midi']
        if (keyString is not None) and (keyString != 'None'):
            primOrSec = 'primary' if keyString in self.notesDict[midiNumber2]['primary']['keys'] else 'secondary'
        else:
            primOrSec = 'primary'
        noteAddProps2 = self.notesDict[midiNumber2][primOrSec]
        newNoteKeyboard['dpc'] = noteAddProps2['dpc']
        newNoteKeyboard['acc'] = noteAddProps2['acc']
        newNoteKeyboard['octave'] = noteAddProps2['octave']
        newNoteKeyboard['name'] = noteAddProps2['name']
        self.history.append({
            'player1': newNoteKeyboard, 
            'player2' : newNoteDnn,
            'metronome' : newMetronomeBeep, 
            'key' : keyString 
            })
        #print(f"saved in history {newNoteDnn} \n {newNoteKeyboard}")
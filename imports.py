import sys
import textwrap
import traceback

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, numbers
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtGui import QColor, QRegExpValidator, QFont, QKeySequence, QPalette
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QListWidget,
                             QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QGridLayout,
                             QSizePolicy, QButtonGroup, QHeaderView, QRadioButton, QAction, QShortcut, QFileDialog,
                             QMenu)
from PyQt5.QtCore import Qt, QRegExp, QTimer
from backend import AHPBackend

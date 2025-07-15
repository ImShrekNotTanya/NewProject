import sys
import textwrap

import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtGui import QColor, QRegExpValidator, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QListWidget,
                             QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QGridLayout,
                             QSizePolicy, QButtonGroup, QHeaderView)
from PyQt5.QtCore import Qt, QRegExp, QTimer
from backend import AHPBackend

class AHPFrontend(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчетный сервис МАИ")

        # 1. Сначала создаем все виджеты
        self._create_widgets()
        self._setup_ui()

        self.display_percent = False

        # 2. Настраиваем параметры окна
        self.setWindowState(Qt.WindowMaximized)  # Альтернативный способ максимизации
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        # 3. Принудительно показываем максимизированное окно
        QTimer.singleShot(100, self.force_maximize)  # Даем время на инициализацию

        self.backend = AHPBackend()
        self.current_matrix = None
        self.current_items = []
        self.result_display_mode = "chart"
        self.result_data = None
        self.matrix_entries = {}

    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(self.tabs)
        self.setCentralWidget(central_widget)

        # Настраиваем растягивание содержимого
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Обновляем layout при изменении размера
        self.centralWidget().updateGeometry()
        QApplication.processEvents()

    def force_maximize(self):
        """Принудительная максимизация окна"""
        if not self.isMaximized():
            self.showMaximized()
        # Дополнительно: подгоняем размеры содержимого
        self.resize(self.size().width(), self.size().height() - 1)
        self.resize(self.size().width() + 1, self.size().height())


    def _create_widgets(self):
        self.tabs = QTabWidget()

        # Вкладки
        self._create_hierarchy_tab()
        self._create_comparison_tab()
        self._create_consistency_tab()
        self._create_results_tab()

        # Блокировка вкладок
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.tabs.setTabEnabled(3, False)

    def _create_hierarchy_tab(self):
        """Вкладка для определения иерархии"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 1. Альтернативы
        alt_group = QGroupBox("1. Ввод альтернатив")
        alt_layout = QHBoxLayout()

        self.alt_entry = QLineEdit()
        self.alt_entry.setFixedWidth(200)
        add_alt_btn = QPushButton("Добавить")
        add_alt_btn.clicked.connect(self._add_alternative)

        alt_layout.addWidget(QLabel("Альтернатива:"))
        alt_layout.addWidget(self.alt_entry)
        alt_layout.addWidget(add_alt_btn)
        alt_layout.addStretch()

        self.alt_list_widget = QWidget()
        self.alt_list_layout = QVBoxLayout(self.alt_list_widget)
        self.alt_list_layout.setAlignment(Qt.AlignTop)

        alt_group.setLayout(QVBoxLayout())
        alt_group.layout().addLayout(alt_layout)
        alt_group.layout().addWidget(self.alt_list_widget)

        # 2. Критерии
        crit_group = QGroupBox("2. Ввод критериев")
        crit_layout = QHBoxLayout()

        self.crit_entry = QLineEdit()
        self.crit_entry.setFixedWidth(200)
        add_crit_btn = QPushButton("Добавить")
        add_crit_btn.clicked.connect(self._add_criterion)

        crit_layout.addWidget(QLabel("Критерий:"))
        crit_layout.addWidget(self.crit_entry)
        crit_layout.addWidget(add_crit_btn)
        crit_layout.addStretch()

        self.crit_list_widget = QWidget()
        self.crit_list_layout = QVBoxLayout(self.crit_list_widget)
        self.crit_list_layout.setAlignment(Qt.AlignTop)

        crit_group.setLayout(QVBoxLayout())
        crit_group.layout().addLayout(crit_layout)
        crit_group.layout().addWidget(self.crit_list_widget)

        # 3. Типы критериев (обновленная версия с поиском)
        type_group = QGroupBox("3. Ввод видов критериев")
        type_layout = QVBoxLayout()

        # Строка ввода вида критериев
        type_name_layout = QHBoxLayout()
        type_name_layout.addWidget(QLabel("Вид критериев:"))
        self.type_entry = QLineEdit()
        self.type_entry.setFixedWidth(150)
        self.type_entry.setPlaceholderText("Название вида")
        type_name_layout.addWidget(self.type_entry)
        type_name_layout.addStretch()
        type_layout.addLayout(type_name_layout)

        # Строка поиска критериев
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск критериев:"))
        self.criteria_search = QLineEdit()
        self.criteria_search.setPlaceholderText("Введите текст для поиска...")
        self.criteria_search.textChanged.connect(self._filter_criteria_list)
        search_layout.addWidget(self.criteria_search)
        type_layout.addLayout(search_layout)

        # Список критериев
        self.type_criteria = QListWidget()
        self.type_criteria.setSelectionMode(QListWidget.MultiSelection)
        self.type_criteria.setFixedHeight(100)
        type_layout.addWidget(self.type_criteria)

        # Кнопка добавления
        add_type_btn = QPushButton("Добавить вид критериев")
        add_type_btn.clicked.connect(self._add_criterion_type)
        type_layout.addWidget(add_type_btn)

        # Список добавленных видов
        self.type_list_widget = QWidget()
        self.type_list_layout = QVBoxLayout(self.type_list_widget)
        self.type_list_layout.setAlignment(Qt.AlignTop)
        type_layout.addWidget(self.type_list_widget)

        type_group.setLayout(type_layout)
        scroll_layout.addWidget(type_group)

        # Кнопка генерации матриц
        gen_btn = QPushButton("Сгенерировать матрицы сравнений →")
        gen_btn.clicked.connect(self._generate_matrices)

        scroll_layout.addWidget(alt_group)
        scroll_layout.addWidget(crit_group)
        scroll_layout.addWidget(type_group)
        scroll_layout.addWidget(gen_btn)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)

        self.tabs.addTab(tab, "1. Определение элементов иерархии")
        return tab

    def _create_consistency_tab(self):
        """Вкладка для проверки согласованности матриц с правильным выравниванием"""
        self.consistency_tab = QWidget()
        self.consistency_tab.setLayout(QVBoxLayout())
        self.consistency_tab.layout().setContentsMargins(10, 10, 10, 10)
        self.consistency_tab.layout().setSpacing(15)

        # Основной скроллируемый контейнер
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # Контейнер для содержимого
        content_widget = QWidget()
        self.consistency_layout = QVBoxLayout(content_widget)
        self.consistency_layout.setContentsMargins(5, 5, 5, 5)
        self.consistency_layout.setSpacing(15)
        self.consistency_layout.setAlignment(Qt.AlignTop)  # Выравнивание по верху

        scroll.setWidget(content_widget)
        self.consistency_tab.layout().addWidget(scroll)

        # Кнопка проверки согласованности (будет добавлена внизу)
        self.recalc_btn = QPushButton("Проверить согласованность →")
        self.recalc_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding: 8px;
                margin: 10px;
                min-width: 200px;
            }
        """)
        self.recalc_btn.clicked.connect(self._check_all_consistency)

        # Добавляем кнопку в отдельный контейнер для выравнивания
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        btn_layout.addWidget(self.recalc_btn)
        btn_layout.addStretch()

        self.consistency_tab.layout().addWidget(btn_container)
        self.tabs.addTab(self.consistency_tab, "3. Проверка согласованности")

    def _create_comparison_tab(self):
        """Вкладка для парных сравнений"""
        self.comp_tab = QWidget()
        self.comp_tab.setLayout(QVBoxLayout())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)

        scroll.setWidget(scroll_content)
        self.comp_tab.layout().addWidget(scroll)

        self.tabs.addTab(self.comp_tab, "2. Метод парных сравнений")

    def _check_all_consistency(self):
        """Проверка согласованности всех матриц с контролем доступности вкладки результатов"""
        # Очищаем предыдущие результаты
        for i in reversed(range(self.consistency_layout.count())):
            widget = self.consistency_layout.itemAt(i).widget()
            if widget and widget != self.recalc_btn:
                widget.deleteLater()

        all_consistent = True
        matrices_to_check = []

        # 1. Проверка матрицы типов критериев
        if 'criteria_types' in self.backend.matrices:
            matrices_to_check.append(('Виды критериев', 'criteria_types'))

        # 2. Проверка матриц критериев по типам
        for type_name in self.backend.criteria_types:
            matrices_to_check.append((f"Критерии: {type_name}", f'criteria_{type_name}'))

        # 3. Проверка матриц альтернатив
        if hasattr(self.backend, 'alternatives') and self.backend.alternatives:
            for criterion in self.backend.criteria:
                matrices_to_check.append((f"Альтернативы по {criterion}", f'alternatives_{criterion}'))

        # Проверяем все матрицы
        for name, key in matrices_to_check:
            matrix = self.backend.matrices[key]
            consistency = self.backend.check_consistency(matrix)

            # Создаем группу для отображения результатов
            group = QGroupBox(name)
            layout = QVBoxLayout()

            # Добавляем показатели согласованности
            layout.addWidget(QLabel(f"λmax: {consistency['lambda_max']:.3f}"))
            layout.addWidget(QLabel(f"Индекс согласованности (CI): {consistency['CI']:.3f}"))
            layout.addWidget(QLabel(f"Отношение согласованности (CR): {consistency['CR']:.3f}"))

            # Добавляем статус с цветовой индикацией
            status_label = QLabel(f"Статус: {consistency['status']}")
            if "ТРЕБУЕТСЯ пересмотр" in consistency['status']:
                status_label.setStyleSheet("color: red; font-weight: bold;")
                all_consistent = False
            elif "Приемлемая согласованность" in consistency['status']:
                status_label.setStyleSheet("color: orange;")
            else:
                status_label.setStyleSheet("color: green;")

            layout.addWidget(status_label)
            layout.addWidget(QLabel("(CR < 0.1 - отличная, CR < 0.2 - приемлемая, CR ≥ 0.2 - требует пересмотра)"))

            group.setLayout(layout)
            self.consistency_layout.addWidget(group)

        # Управление доступностью вкладки результатов
        self.tabs.setTabEnabled(3, all_consistent)  # Вкладка с результатами (индекс 3)

        # Показываем сообщение о результате проверки
        if all_consistent:
            QMessageBox.information(self, "Проверка завершена",
                                    "Все матрицы имеют отличную или приемлемую согласованность!\n"
                                    "Теперь доступны результаты анализа.")
        else:
            QMessageBox.warning(self, "Внимание",
                                "Некоторые матрицы требуют пересмотра!\n"
                                "Исправьте оценки в матрицах с плохой согласованностью.")


    def _create_results_tab(self):
        """Вкладка с результатами"""
        self.res_tab = QWidget()
        self.res_tab.setLayout(QVBoxLayout())

        # Frame for result display controls
        self.res_controls_frame = QWidget()
        self.res_controls_layout = QHBoxLayout(self.res_controls_frame)

        # Frame for actual results display
        self.res_display_frame = QScrollArea()
        self.res_display_frame.setWidgetResizable(True)
        self.res_display_content = QWidget()
        self.res_display_layout = QVBoxLayout(self.res_display_content)

        self.res_display_frame.setWidget(self.res_display_content)

        self.res_tab.layout().addWidget(self.res_controls_frame)
        self.res_tab.layout().addWidget(self.res_display_frame)

        self.tabs.addTab(self.res_tab, "4. Результаты анализа")

    def _add_alternative(self):
        text = self.alt_entry.text().strip()
        if text and self.backend.add_alternative(text):
            self.alt_entry.clear()
            self._update_alt_list()
            self._update_criteria_listbox()

    def _add_criterion(self):
        text = self.crit_entry.text().strip()
        if text and self.backend.add_criterion(text):
            self.crit_entry.clear()
            self._update_crit_list()
            self._update_criteria_listbox()

    def _add_criterion_type(self):
        """Добавление нового вида критериев"""
        type_name = self.type_entry.text().strip()
        selected = [item.text() for item in self.type_criteria.selectedItems()]

        if not type_name:
            QMessageBox.warning(self, "Ошибка", "Введите название вида критериев")
            return
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один критерий")
            return

        if self.backend.add_criterion_type(type_name, selected):
            self.type_entry.clear()
            self.criteria_search.clear()
            self.type_criteria.clearSelection()
            self._update_type_list()

    def _update_alt_list(self):
        # Clear existing widgets
        for i in reversed(range(self.alt_list_layout.count())):
            widget = self.alt_list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for i, alt in enumerate(self.backend.alternatives):
            frame = QWidget()
            frame.setLayout(QHBoxLayout())

            label = QLabel(alt)
            btn = QPushButton("Удалить")
            btn.clicked.connect(lambda _, idx=i: self._remove_item('alternatives', idx))

            frame.layout().addWidget(label)
            frame.layout().addWidget(btn)
            frame.layout().addStretch()

            self.alt_list_layout.addWidget(frame)

    def _update_crit_list(self):
        # Clear existing widgets
        for i in reversed(range(self.crit_list_layout.count())):
            widget = self.crit_list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for i, crit in enumerate(self.backend.criteria):
            frame = QWidget()
            frame.setLayout(QHBoxLayout())

            label = QLabel(crit)
            btn = QPushButton("Удалить")
            btn.clicked.connect(lambda _, idx=i: self._remove_item('criteria', idx))

            frame.layout().addWidget(label)
            frame.layout().addWidget(btn)
            frame.layout().addStretch()

            self.crit_list_layout.addWidget(frame)

    def _update_type_list(self):
        # Clear existing widgets
        for i in reversed(range(self.type_list_layout.count())):
            widget = self.type_list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for type_name, criteria in self.backend.criteria_types.items():
            frame = QWidget()
            frame.setLayout(QHBoxLayout())

            label = QLabel(f"{type_name}: {', '.join(criteria)}")
            btn = QPushButton("Удалить")
            btn.clicked.connect(lambda _, tn=type_name: self._remove_criterion_type(tn))

            frame.layout().addWidget(label)
            frame.layout().addWidget(btn)
            frame.layout().addStretch()

            self.type_list_layout.addWidget(frame)

    def _filter_criteria_list(self):
        """Фильтрация списка критериев по введенному тексту"""
        search_text = self.criteria_search.text().lower()
        for i in range(self.type_criteria.count()):
            item = self.type_criteria.item(i)
            item.setHidden(search_text not in item.text().lower())

    def _update_criteria_listbox(self):
        """Обновление списка критериев с сохранением фильтра"""
        current_search = self.criteria_search.text()
        self.type_criteria.clear()
        for crit in self.backend.criteria:
            self.type_criteria.addItem(crit)
        if current_search:
            self._filter_criteria_list()

    def _remove_item(self, item_type, index):
        if item_type == 'alternatives':
            if 0 <= index < len(self.backend.alternatives):
                del self.backend.alternatives[index]
                self._update_alt_list()
        elif item_type == 'criteria':
            if 0 <= index < len(self.backend.criteria):
                crit = self.backend.criteria[index]
                # Удаляем из типов критериев
                for type_name in list(self.backend.criteria_types.keys()):
                    if crit in self.backend.criteria_types[type_name]:
                        self.backend.criteria_types[type_name].remove(crit)
                        if not self.backend.criteria_types[type_name]:
                            del self.backend.criteria_types[type_name]

                del self.backend.criteria[index]
                self._update_crit_list()
                self._update_type_list()
                self._update_criteria_listbox()

    def _remove_criterion_type(self, type_name):
        if type_name in self.backend.criteria_types:
            del self.backend.criteria_types[type_name]
            self._update_type_list()

    def _generate_matrices(self):
        """Генерация всех необходимых матриц"""
        if not self.backend.alternatives:
            QMessageBox.critical(self, "Ошибка", "Добавьте хотя бы одну альтернативу")
            return
        if not self.backend.criteria:
            QMessageBox.critical(self, "Ошибка", "Добавьте хотя бы один критерий")
            return
        if not self.backend.criteria_types:
            QMessageBox.critical(self, "Ошибка", "Добавьте хотя бы один вид критериев")
            return

        # Активируем вкладку сравнений
        self.tabs.setTabEnabled(1, True)
        self.tabs.setCurrentIndex(1)
        self._setup_comparison_tab()

    def _setup_comparison_tab(self):
        """Настройка вкладки с матрицами сравнения без скролла"""
        # Очищаем предыдущие виджеты
        self._clear_layout(self.scroll_layout)

        # Создаем основной фрейм для всех матриц
        main_frame = QFrame()
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(20)

        # Очищаем записи матриц
        self.matrix_entries.clear()

        # 1. Матрица сравнения типов критериев (первый уровень)
        title1 = QLabel("Первый уровень: Сравнение видов критериев")
        title1.setStyleSheet("font-weight: bold; font-size: 12pt;")
        main_layout.addWidget(title1)

        type_names = list(self.backend.criteria_types.keys())
        if type_names:
            self._create_matrix_ui(type_names, 'criteria_types', main_layout)

        # 2. Матрицы сравнения критериев (второй уровень)
        title2 = QLabel("Второй уровень: Сравнение критериев по видам")
        title2.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 20px;")
        main_layout.addWidget(title2)

        for type_name in type_names:
            subtitle = QLabel(f"Вид критериев: {type_name}")
            subtitle.setStyleSheet("font-weight: bold; margin-top: 10px;")
            main_layout.addWidget(subtitle)

            criteria = self.backend.criteria_types.get(type_name, [])
            if criteria:
                self._create_matrix_ui(criteria, f'criteria_{type_name}', main_layout)

        # 3. Матрицы сравнения альтернатив (третий уровень)
        if getattr(self.backend, 'alternatives', None):
            title3 = QLabel("Третий уровень: Сравнение альтернатив по критериям")
            title3.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 20px;")
            main_layout.addWidget(title3)

            for criterion in getattr(self.backend, 'criteria', []):
                subtitle = QLabel(f"Критерий: {criterion}")
                subtitle.setStyleSheet("font-weight: bold; margin-top: 10px;")
                main_layout.addWidget(subtitle)

                self._create_matrix_ui(self.backend.alternatives, f'alternatives_{criterion}', main_layout)

        # Кнопка расчета
        calc_btn = QPushButton("Рассчитать приоритеты →")
        calc_btn.setStyleSheet("font-weight: bold; margin: 20px 0;")
        calc_btn.clicked.connect(self._calculate_priorities)
        main_layout.addWidget(calc_btn)

        # Добавляем основной фрейм в scroll_layout
        self.scroll_layout.addWidget(main_frame)
        self.scroll_layout.addStretch()

    def _setup_results_controls(self):
        """Настройка элементов управления для результатов с выделением активной кнопки"""
        # Очищаем предыдущие элементы
        for i in reversed(range(self.res_controls_layout.count())):
            widget = self.res_controls_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Улучшенный стиль кнопок
        button_style = """
            QPushButton {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f8f8f8;
                margin-right: 5px;
                min-width: 80px;
                transition: background 0.2s;
            }
            QPushButton:hover {
                background: #e8e8e8;
            }
            QPushButton:checked {
                background: #4CAF50;
                color: white;
                border-color: #3e8e41;
                font-weight: bold;
            }
            QPushButton:pressed {
                background: #3e8e41;
            }
        """

        # Создаем кнопки с возможностью выделения
        self.view_buttons = {}
        formats = [
            ("График", "chart"),
            ("Таблица", "table"),
            ("Диаграмма", "diagram"),
            ("Тепловая карта", "heatmap")
        ]

        # Группа кнопок для исключительного выбора
        self.button_group = QButtonGroup()

        for text, mode in formats:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(lambda _, m=mode: self._set_result_display_mode(m))
            self.res_controls_layout.addWidget(btn)
            self.button_group.addButton(btn)
            self.view_buttons[mode] = btn

        # Кнопка переключения процентов
        self.percent_toggle = QPushButton("Показать в процентах")
        self.percent_toggle.setCheckable(True)
        self.percent_toggle.setChecked(self.display_percent)
        self.percent_toggle.clicked.connect(self._toggle_percent_display)
        self.percent_toggle.setStyleSheet(button_style)
        self.res_controls_layout.addWidget(self.percent_toggle)

        self.res_controls_layout.addStretch()

    def _toggle_percent_display(self):
        """Переключает между отображением в процентах и абсолютных значениях"""
        try:
            self.display_percent = not self.display_percent
            if hasattr(self, 'percent_toggle'):
                self.percent_toggle.setChecked(self.display_percent)
                self.percent_toggle.setText(
                    "Показать в процентах" if not self.display_percent
                    else "Показать абсолютные значения"
                )
            self._display_results()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка переключения режима: {str(e)}")

    def resizeEvent(self, event):
        """Автомасштабирование при изменении размера окна"""
        super().resizeEvent(event)
        # Обновляем размеры матриц
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'adjustSize'):
                widget.adjustSize()

    def _create_matrix_ui(self, items, matrix_key, parent_layout):
        """Создание матрицы сравнения"""
        try:
            if not items or not isinstance(items, list):
                raise ValueError("Некорректный список элементов")

            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            grid = QGridLayout()
            grid.setSpacing(1)
            grid.setContentsMargins(2, 2, 2, 2)

            n = len(items)
            if n == 0:
                return

            # Размеры и стили ячеек
            cell_size = 80
            header_style = f"""
                QLabel {{
                    font-weight: bold;
                    border: 1px solid #999;
                    padding: 5px;
                    background-color: #f5f5f5;
                    min-width: {cell_size}px;
                    min-height: 30px;
                    text-align: center;
                }}
            """

            cell_style = f"""
                QLineEdit, QLabel {{
                    border: 1px solid #ddd;
                    padding: 5px;
                    min-width: {cell_size}px;
                    min-height: 30px;
                    text-align: center;
                    background-color: white;
                }}
                QLineEdit:focus {{
                    border: 1px solid #4CAF50;
                }}
            """

            # Заголовки столбцов
            for j in range(n):
                label = QLabel(items[j] if j < len(items) else "")
                label.setStyleSheet(header_style)
                grid.addWidget(label, 0, j + 1)

            # Создаем матрицу
            for i in range(n):
                # Заголовок строки
                row_label = QLabel(items[i] if i < len(items) else "")
                row_label.setStyleSheet(header_style)
                grid.addWidget(row_label, i + 1, 0)

                for j in range(n):
                    if i == j:
                        # Диагональ
                        label = QLabel("1")
                        label.setStyleSheet(cell_style)
                        grid.addWidget(label, i + 1, j + 1)
                    elif i < j:
                        # Редактируемое поле
                        entry = QLineEdit()
                        entry.setStyleSheet(cell_style)
                        entry.setValidator(QRegExpValidator(QRegExp(r"^([1-9]|1/[2-9])$")))

                        # Используем partial вместо lambda для сохранения значений
                        from functools import partial
                        entry.editingFinished.connect(
                            partial(self._safe_update_reciprocal, matrix_key, i, j)
                        )
                        grid.addWidget(entry, i + 1, j + 1)
                        self.matrix_entries[(matrix_key, i, j)] = entry
                    else:
                        # Вычисляемое поле
                        label = QLabel("")
                        label.setStyleSheet(cell_style)
                        grid.addWidget(label, i + 1, j + 1)
                        self.matrix_entries[(matrix_key, i, j)] = label

            frame.setLayout(grid)
            parent_layout.addWidget(frame)

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка создания матрицы: {str(e)}")
            import traceback
            traceback.print_exc()

    def _clear_layout(self, layout):
        """Безопасная очистка layout"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _safe_update_reciprocal(self, matrix_key, i, j):
        """Безопасное обновление обратного значения"""
        try:
            entry = self.matrix_entries.get((matrix_key, i, j))
            recip_entry = self.matrix_entries.get((matrix_key, j, i))

            if not entry or not recip_entry:
                return

            value = entry.text().strip()
            if not value:
                return

            if value.startswith("1/"):
                recip_value = value[2:]
            else:
                recip_value = f"1/{value}" if value != "1" else "1"

            if isinstance(recip_entry, QLabel):
                recip_entry.setText(recip_value)
        except Exception as e:
            print(f"Ошибка обновления: {str(e)}")

    def _update_reciprocal_value(self, matrix_key, i, j):
        """Безопасное обновление обратного значения"""
        try:
            entry = self.matrix_entries.get((matrix_key, i, j))
            recip_entry = self.matrix_entries.get((matrix_key, j, i))

            if not isinstance(entry, QLineEdit) or not isinstance(recip_entry, QLabel):
                return

            value = entry.text().strip()
            if not value:
                return

            try:
                if value.startswith("1/"):
                    recip_value = value[2:]
                else:
                    if value == "1":
                        recip_value = "1"
                    else:
                        recip_value = f"1/{value}"

                recip_entry.setText(recip_value)
            except:
                pass

        except Exception as e:
            print(f"Ошибка обновления обратного значения: {str(e)}")

    def _check_all_consistency(self):
        """Проверка согласованности всех матриц с группировкой по уровням"""
        # Очищаем предыдущие результаты
        for i in reversed(range(self.consistency_layout.count())):
            widget = self.consistency_layout.itemAt(i).widget()
            if widget and widget != self.recalc_btn:
                widget.deleteLater()

        all_consistent = True

        # 1. Заголовок для первого уровня
        title1 = QLabel("Первый уровень: Согласованность видов критериев")
        title1.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.consistency_layout.addWidget(title1)

        # Проверка матрицы типов критериев
        if 'criteria_types' in self.backend.matrices:
            matrix = self.backend.matrices['criteria_types']
            consistency = self.backend.check_consistency(matrix)

            group = QGroupBox("Сравнение видов критериев")
            layout = QVBoxLayout()

            # Добавляем показатели согласованности
            self._add_consistency_widgets(layout, consistency)
            group.setLayout(layout)
            self.consistency_layout.addWidget(group)

            if consistency['status'] == "ТРЕБУЕТСЯ пересмотр":
                all_consistent = False

        # 2. Заголовок для второго уровня
        title2 = QLabel("Второй уровень: Согласованность критериев по видам")
        title2.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 20px;")
        self.consistency_layout.addWidget(title2)

        # Проверка матриц критериев по видам
        for type_name in self.backend.criteria_types:
            matrix_key = f'criteria_{type_name}'
            if matrix_key in self.backend.matrices:
                matrix = self.backend.matrices[matrix_key]
                consistency = self.backend.check_consistency(matrix)

                group = QGroupBox(f"Вид критериев: {type_name}")
                layout = QVBoxLayout()

                self._add_consistency_widgets(layout, consistency)
                group.setLayout(layout)
                self.consistency_layout.addWidget(group)

                if consistency['status'] == "ТРЕБУЕТСЯ пересмотр":
                    all_consistent = False

        # 3. Заголовок для третьего уровня (если есть альтернативы)
        if self.backend.alternatives:
            title3 = QLabel("Третий уровень: Согласованность альтернатив по критериям")
            title3.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 20px;")
            self.consistency_layout.addWidget(title3)

            # Проверка матриц альтернатив
            for criterion in self.backend.criteria:
                matrix_key = f'alternatives_{criterion}'
                if matrix_key in self.backend.matrices:
                    matrix = self.backend.matrices[matrix_key]
                    consistency = self.backend.check_consistency(matrix)

                    group = QGroupBox(f"Критерий: {criterion}")
                    layout = QVBoxLayout()

                    self._add_consistency_widgets(layout, consistency)
                    group.setLayout(layout)
                    self.consistency_layout.addWidget(group)

                    if consistency['status'] == "ТРЕБУЕТСЯ пересмотр":
                        all_consistent = False

        # Кнопка перерасчета внизу
        self.consistency_layout.addWidget(self.recalc_btn)

        # Активируем/деактивируем вкладку результатов
        self.tabs.setTabEnabled(3, all_consistent)

        if all_consistent:
            QMessageBox.information(self, "Проверка завершена",
                                    "Все матрицы имеют отличную или приемлемую согласованность!")
        else:
            QMessageBox.warning(self, "Внимание",
                                "Некоторые матрицы требуют пересмотра!\n"
                                "Исправьте оценки в матрицах с плохой согласованностью.")

    def _add_consistency_group(self, title, consistency_data):
        """Добавляет группу с результатами проверки согласованности"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                margin-top: 10px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(8)

        # Добавляем показатели
        metrics = [
            ("λmax:", f"{consistency_data['lambda_max']:.3f}"),
            ("Индекс согласованности (CI):", f"{consistency_data['CI']:.3f}"),
            ("Отношение согласованности (CR):", f"{consistency_data['CR']:.3f}")
        ]

        for name, value in metrics:
            row = QHBoxLayout()
            row.addWidget(QLabel(name))
            row.addWidget(QLabel(value))
            row.addStretch()
            layout.addLayout(row)

        # Добавляем статус
        status_label = QLabel(f"Статус: {consistency_data['status']}")
        if "требует" in consistency_data['status'].lower():
            status_label.setStyleSheet("color: red; font-weight: bold;")
        elif "приемлемая" in consistency_data['status'].lower():
            status_label.setStyleSheet("color: orange;")
        else:
            status_label.setStyleSheet("color: green;")

        layout.addWidget(status_label)

        # Добавляем пояснение
        note = QLabel("(CR < 0.1 - отличная, CR < 0.2 - приемлемая, CR ≥ 0.2 - требует пересмотра)")
        note.setStyleSheet("font-size: 11px; color: #666;")
        layout.addWidget(note)

        group.setLayout(layout)
        self.consistency_layout.addWidget(group)

    def _add_consistency_widgets(self, layout, consistency):
        """Добавляет виджеты с показателями согласованности в layout"""
        layout.addWidget(QLabel(f"λmax: {consistency['lambda_max']:.3f}"))
        layout.addWidget(QLabel(f"Индекс согласованности (CI): {consistency['CI']:.3f}"))
        layout.addWidget(QLabel(f"Отношение согласованности (CR): {consistency['CR']:.3f}"))

        status_label = QLabel(f"Статус: {consistency['status']}")
        if consistency['status'] == "ТРЕБУЕТСЯ пересмотр":
            status_label.setStyleSheet("color: red; font-weight: bold;")
        elif consistency['status'] == "Приемлемая согласованность":
            status_label.setStyleSheet("color: orange;")
        else:
            status_label.setStyleSheet("color: green;")

        layout.addWidget(status_label)
        layout.addWidget(QLabel("(CR < 0.1 - отличная, CR < 0.2 - приемлемая, CR ≥ 0.2 - требует пересмотра)"))

    def _calculate_priorities(self):
        """Сбор данных и расчет приоритетов с проверкой заполнения всех матриц"""
        # Проверяем, что все матрицы заполнены
        if not self._check_all_matrices_filled():
            QMessageBox.warning(self, "Ошибка",
                                "Не все матрицы сравнений заполнены!\n"
                                "Заполните все необходимые матрицы перед расчетом.")
            return

        # 1. Собираем все матрицы сравнений
        matrices = {}

        # Матрица типов критериев
        type_names = list(self.backend.criteria_types.keys())
        type_comparisons = {}
        for i in range(len(type_names)):
            for j in range(i + 1, len(type_names)):
                entry = self.matrix_entries.get(('criteria_types', i, j))
                if entry and isinstance(entry, QLineEdit):
                    value = entry.text().strip()
                    if value:
                        type_comparisons[(i, j)] = value

        matrices['criteria_types'] = self.backend.build_matrix(type_names, type_comparisons)
        if matrices['criteria_types'] is None:
            QMessageBox.critical(self, "Ошибка", "Проверьте заполнение матрицы сравнения видов критериев")
            return

        # Матрицы критериев по типам
        for type_name, type_criteria in self.backend.criteria_types.items():
            comparisons = {}
            n = len(type_criteria)
            for i in range(n):
                for j in range(i + 1, n):
                    entry = self.matrix_entries.get((f'criteria_{type_name}', i, j))
                    if entry and isinstance(entry, QLineEdit):
                        value = entry.text().strip()
                        if value:
                            comparisons[(i, j)] = value

            matrix = self.backend.build_matrix(type_criteria, comparisons)
            if matrix is None:
                QMessageBox.critical(self, "Ошибка",
                                     f"Проверьте матрицу сравнения критериев для вида '{type_name}'")
                return
            matrices[f'criteria_{type_name}'] = matrix

        # Матрицы альтернатив по критериям
        if self.backend.alternatives:
            for criterion in self.backend.criteria:
                comparisons = {}
                n = len(self.backend.alternatives)
                for i in range(n):
                    for j in range(i + 1, n):
                        entry = self.matrix_entries.get((f'alternatives_{criterion}', i, j))
                        if entry and isinstance(entry, QLineEdit):
                            value = entry.text().strip()
                            if value:
                                comparisons[(i, j)] = value

                matrix = self.backend.build_matrix(self.backend.alternatives, comparisons)
                if matrix is None:
                    QMessageBox.critical(self, "Ошибка",
                                         f"Проверьте матрицу сравнения альтернатив для критерия '{criterion}'")
                    return
                matrices[f'alternatives_{criterion}'] = matrix

        # 2. Сохраняем матрицы в backend
        self.backend.matrices = matrices

        # 3. Выполняем расчет AHP
        try:
            results = self.backend.calculate_ahp()
            if results is None:
                QMessageBox.critical(self, "Ошибка", "Ошибка при расчете приоритетов")
                return

            # 4. Показываем результаты
            self._show_results(results)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при расчетах: {str(e)}")

            # После успешного расчета активируем вкладку согласованности
            self.tabs.setTabEnabled(2, True)
            self.tabs.setCurrentIndex(2)  # Переходим на вкладку проверки согласованности
            self._check_all_consistency()  # Запускаем проверку

    def _check_all_matrices_filled(self):
        """Проверяет, что все необходимые матрицы заполнены"""
        # 1. Проверка матрицы типов критериев
        type_names = list(self.backend.criteria_types.keys())
        for i in range(len(type_names)):
            for j in range(i + 1, len(type_names)):
                entry = self.matrix_entries.get(('criteria_types', i, j))
                if not entry or not entry.text().strip():
                    return False

        # 2. Проверка матриц критериев по типам
        for type_name in self.backend.criteria_types:
            criteria = self.backend.criteria_types[type_name]
            for i in range(len(criteria)):
                for j in range(i + 1, len(criteria)):
                    entry = self.matrix_entries.get((f'criteria_{type_name}', i, j))
                    if not entry or not entry.text().strip():
                        return False

        # 3. Проверка матриц альтернатив (если есть)
        if self.backend.alternatives:
            for criterion in self.backend.criteria:
                for i in range(len(self.backend.alternatives)):
                    for j in range(i + 1, len(self.backend.alternatives)):
                        entry = self.matrix_entries.get((f'alternatives_{criterion}', i, j))
                        if not entry or not entry.text().strip():
                            return False

        return True

    def _show_results(self, results):
        """Отображение результатов анализа с проверкой согласованности матриц"""
        # Проверяем согласованность всех матриц
        all_consistent = all(
            self.backend.check_consistency(matrix)['status'] in ["Отличная согласованность",
                                                                 "Приемлемая согласованность"]
            for matrix in self.backend.matrices.values()
        )

        # Управление доступностью вкладок
        self.tabs.setTabEnabled(2, True)  # Вкладка проверки согласованности
        self.tabs.setTabEnabled(3, all_consistent)  # Вкладка результатов

        # Переходим на вкладку проверки согласованности, независимо от результата
        self.tabs.setCurrentIndex(2)

        # Если все матрицы согласованы, сохраняем результаты и готовим отображение
        if all_consistent:
            # Очищаем предыдущие результаты
            for i in reversed(range(self.res_display_layout.count())):
                widget = self.res_display_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Сохраняем данные результатов
            self.result_data = results

            # Настраиваем элементы управления
            self._setup_results_controls()

            # Отображаем результаты в текущем режиме
            self._display_results()

    def _create_heatmap(self, labels, values, title):
        """Создание тепловой карты с улучшенной видимостью на темных фонах"""
        try:
            fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')

            # Используем стиль по умолчанию, если seaborn не доступен
            try:
                plt.style.use('seaborn-v0_8-whitegrid')
            except:
                plt.style.use('default')

            # Нормализуем значения для цветовой шкалы
            normalized = (values - np.min(values)) / (np.max(values) - np.min(values))

            # Используем цветовую карту viridis с улучшенной контрастностью
            colors = plt.cm.viridis(normalized)

            # Создаем тепловую карту с полосами
            for i, (label, value, color) in enumerate(zip(labels, values, colors)):
                # Полоса во всю ширину с белой границей
                rect = plt.Rectangle((0, i), 1, 0.8, color=color, alpha=0.8, ec='white', lw=1)
                ax.add_patch(rect)

                # Определяем цвет текста - светлый для темных фонов (но не чисто белый)
                text_color = '#f0f0f0' if normalized[i] < 0.4 else '#333333'

                # Название элемента (слева)
                ax.text(0.05, i + 0.4, f"{label}",
                        ha='left', va='center',
                        fontsize=12, fontweight='bold',
                        color=text_color)

                # Значение (справа) с улучшенным форматированием
                ax.text(0.95, i + 0.4, f"{value:.3f}",
                        ha='right', va='center',
                        fontsize=12, fontweight='bold',
                        color=text_color,
                        bbox=dict(facecolor='white' if normalized[i] < 0.3 or normalized[i] > 0.7 else 'none',
                                  alpha=0.2, edgecolor='none', pad=2))

            # Настройки осей
            ax.set_xlim(0, 1)
            ax.set_ylim(0, len(labels))
            ax.set_yticks([])
            ax.set_xticks([])

            # Горизонтальные линии-разделители
            for i in range(len(labels) + 1):
                ax.axhline(i, color='lightgray', linestyle='-', linewidth=0.5, alpha=0.5)

            # Заголовок с улучшенным оформлением
            ax.set_title(title, fontsize=16, pad=20, fontweight='bold')

            # Цветовая шкала с подписью
            sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis,
                                       norm=plt.Normalize(vmin=np.min(values),
                                                          vmax=np.max(values)))
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax, orientation='vertical',
                                pad=0.02, shrink=0.5, aspect=10)
            cbar.set_label('Значение приоритета', fontsize=12, labelpad=10)
            cbar.ax.tick_params(labelsize=10)

            plt.tight_layout()

            canvas = FigureCanvas(fig)
            self.res_display_layout.addWidget(canvas)

        except Exception as e:
            QMessageBox.warning(self, "Ошибка визуализации",
                                f"Не удалось создать тепловую карту: {str(e)}")

    def _set_result_display_mode(self, mode):
        """Установка режима отображения с выделением кнопки"""
        self.result_display_mode = mode

        # Снимаем выделение со всех кнопок
        for btn in self.view_buttons.values():
            btn.setChecked(False)

        # Выделяем активную кнопку
        if mode in self.view_buttons:
            self.view_buttons[mode].setChecked(True)

        self._display_results()

    def _display_results(self):
        """Отображение результатов в выбранном формате"""
        # Очищаем область отображения
        for i in reversed(range(self.res_display_layout.count())):
            widget = self.res_display_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if self.result_data is None:
            return

        if self.result_display_mode == "chart":
            self._display_chart_results()
        elif self.result_display_mode == "table":
            self._display_table_results()
        elif self.result_display_mode == "diagram":
            self._display_diagram_results()
        elif self.result_display_mode == "heatmap":
            self._display_heatmap_results()

    def _display_chart_results(self):
        """Отображение результатов в виде интерактивных графиков"""
        try:
            # 1. Приоритеты типов критериев
            type_names = list(self.backend.criteria_types.keys())
            type_priority = self.result_data['type_priority']
            self._create_interactive_bar_chart(
                type_names,
                type_priority,
                "Приоритеты видов критериев (Первый уровень)",
                color='#4C72B0'
            )

            # 2. Приоритеты критериев
            self._create_interactive_bar_chart(
                self.backend.criteria,
                self.result_data['criteria_priority'],
                "Приоритеты критериев (Второй уровень)",
                color='#55A868'
            )

            # 3. Приоритеты альтернатив
            if 'alternatives_priority' in self.result_data:
                self._create_interactive_bar_chart(
                    self.backend.alternatives,
                    self.result_data['alternatives_priority'],
                    "Итоговые приоритеты альтернатив",
                    color='#DD8452'
                )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании графиков: {str(e)}")

    def _create_interactive_bar_chart(self, labels, values, title, color=None):
        """Создание столбчатой диаграммы с улучшенным отображением подписей"""
        try:
            # Преобразуем значения в массив numpy
            values_array = np.array(values, dtype=float)

            # Проверяем данные
            if len(labels) != len(values_array):
                raise ValueError("Количество меток и значений не совпадает")

            # Создаем фигуру с увеличенными отступами
            fig, ax = plt.subplots(figsize=(10, 7))  # Увеличили высоту
            fig.subplots_adjust(top=0.9, bottom=0.3, left=0.15, right=0.95)  # Настроили отступы

            # Определяем формат отображения
            if hasattr(self, 'display_percent') and self.display_percent:
                total = np.sum(values_array)
                if total > 0:
                    values_to_plot = (values_array / total) * 100
                    ylabel = "Приоритет, %"
                    fmt = "{:.1f}%"
                    ylim = (0, 100)
                else:
                    raise ValueError("Невозможно отобразить в процентах: сумма значений равна 0")
            else:
                values_to_plot = values_array
                ylabel = "Значение приоритета"
                fmt = "{:.3f}"
                ylim = (0, np.max(values_array) * 1.15)

            # Создаем столбцы с увеличенным расстоянием между ними
            x_pos = np.arange(len(labels))
            bars = ax.bar(x_pos, values_to_plot,
                          color=color or '#4C72B0',
                          alpha=0.85,
                          width=0.7)  # Увеличили ширину столбцов

            # Настройка оформления
            ax.set_title(title, pad=25, fontsize=14, fontweight='bold')  # Увеличили отступ заголовка
            ax.set_ylabel(ylabel, fontsize=12, labelpad=15)
            ax.set_ylim(ylim)

            # Настройка осей X
            ax.set_xticks(x_pos)

            # Форматирование подписей на оси X (перенос длинных текстов)
            formatted_labels = [label.replace(' ', '\n') if len(label) > 10 else label
                                for label in labels]
            ax.set_xticklabels(formatted_labels,
                               fontsize=11,
                               rotation=45,
                               ha='right',
                               rotation_mode='anchor')

            # Добавляем подписи значений с улучшенным позиционированием
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2.,
                        height + 0.01 * ylim[1],  # Уменьшили отступ от столбца
                        fmt.format(height),
                        ha='center',
                        va='bottom',
                        fontsize=11,
                        fontweight='bold')

            # Включаем сетку для лучшей читаемости
            ax.yaxis.grid(True, linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)

            # Убираем лишние линии рамки
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)

            # Добавляем холст в интерфейс
            canvas = FigureCanvas(fig)
            canvas.setMinimumSize(800, 500)  # Установили минимальный размер
            self.res_display_layout.addWidget(canvas)

        except Exception as e:
            error_msg = f"Ошибка при создании столбчатой диаграммы: {str(e)}"
            print(error_msg)
            QMessageBox.warning(self, "Ошибка", error_msg)
            if 'fig' in locals():
                plt.close(fig)

    def _display_table_results(self):
        """Отображение результатов в виде таблиц"""
        # 1. Приоритеты типов критериев
        type_names = list(self.backend.criteria_types.keys())
        type_priority = self.result_data['type_priority']
        self._create_table(type_names, type_priority,
                           "Приоритеты видов критериев (Первый уровень)")

        # 2. Приоритеты критериев (второй уровень)
        self._create_table(self.backend.criteria,
                           self.result_data['criteria_priority'],
                           "Приоритеты критериев (Второй уровень)")

        # 3. Приоритеты альтернатив (третий уровень)
        if 'alternatives_priority' in self.result_data:
            self._create_table(
                self.backend.alternatives,
                self.result_data['alternatives_priority'],
                "Итоговые приоритеты альтернатив",
                show_percent=True
            )

    def _display_diagram_results(self):
        """Отображение результатов в виде круговых диаграмм"""
        try:
            # Очищаем предыдущие результаты
            for i in reversed(range(self.res_display_layout.count())):
                widget = self.res_display_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            if not self.result_data:
                raise ValueError("Нет данных для отображения")

            # 1. Приоритеты типов критериев
            if 'type_priority' in self.result_data and self.backend.criteria_types:
                type_names = list(self.backend.criteria_types.keys())
                if len(type_names) == len(self.result_data['type_priority']):
                    self._create_pie_chart(
                        type_names,
                        self.result_data['type_priority'],
                        "Приоритеты видов критериев (Первый уровень)"
                    )

            # 2. Приоритеты критериев
            if 'criteria_priority' in self.result_data and self.backend.criteria:
                if len(self.backend.criteria) == len(self.result_data['criteria_priority']):
                    self._create_pie_chart(
                        self.backend.criteria,
                        self.result_data['criteria_priority'],
                        "Приоритеты критериев (Второй уровень)"
                    )

            # 3. Приоритеты альтернатив
            if ('alternatives_priority' in self.result_data and
                    self.backend.alternatives and
                    len(self.backend.alternatives) == len(self.result_data['alternatives_priority'])):
                self._create_pie_chart(
                    self.backend.alternatives,
                    self.result_data['alternatives_priority'],
                    "Итоговые приоритеты альтернатив"
                )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка отображения диаграмм: {str(e)}")

    def _create_table(self, labels, values, title, show_percent=False, is_comparison_matrix=False,
                      is_second_level=False, first_level_weights=None):
        """
        Создает таблицу с результатами расчетов AHP
        """
        try:
            # Проверка входных данных
            if not labels or values is None:
                raise ValueError("Не переданы labels или values")

            if is_second_level and first_level_weights is None:
                raise ValueError("Для таблицы второго уровня нужны first_level_weights")

            # Создание GUI элементов
            group = QGroupBox(title)
            group.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)

            layout = QVBoxLayout(group)
            layout.setContentsMargins(5, 15, 5, 10)
            layout.setSpacing(10)

            # Настройка таблицы
            column_count = 5 if is_second_level else 4
            table = QTableWidget()
            table.setColumnCount(column_count)

            headers = ["№", "Элемент", "Главный вектор (ΓB)", "Вектор приоритетов (w)"]
            if is_second_level:
                headers.append("ВП второго уровня")
            table.setHorizontalHeaderLabels(headers)

            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionMode(QTableWidget.NoSelection)
            table.setMinimumHeight(min(300, len(labels) * 35 + 40))

            # Настройка ширины столбцов
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            if is_second_level:
                table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

            # Преобразуем входные данные
            values_array = np.array(values, dtype=float)

            # Единый расчет ΓB и w для всех таблиц (как в первой таблице)
            if values_array.ndim == 1:
                # Если передан уже вектор приоритетов
                w = values_array
                CB = np.array([np.prod([w[i] / w[j] for j in range(len(w))]) ** (1 / len(w)) for i in range(len(w))])
            else:
                # Для матрицы сравнения
                CB, w = self.backend.calculate_priority_vector(values_array)

            # Расчет приоритетов второго уровня (если требуется)
            if is_second_level:
                try:
                    if len(w) != len(first_level_weights):
                        raise ValueError("Размеры векторов не совпадают")
                    second_level_w = w * first_level_weights
                    second_level_w /= np.sum(second_level_w)  # Нормализация
                except Exception as e:
                    second_level_w = np.zeros(len(w))
                    print(f"Ошибка расчета второго уровня: {str(e)}")

            # Проверка согласованности (только для матриц сравнения)
            if is_comparison_matrix and values_array.ndim > 1 and values_array.shape[0] > 2:
                consistency = self.backend.check_consistency(values_array, CB)
                consistency_label = QLabel(
                    f"Согласованность: λmax = {consistency['lambda_max']:.3f}, "
                    f"ИС = {consistency['CI']:.3f}, ОС = {consistency['CR']:.3f} - "
                    f"{consistency['status']}"
                )
                if consistency['CR'] < 0.1:
                    consistency_label.setStyleSheet("color: green;")
                elif consistency['CR'] < 0.2:
                    consistency_label.setStyleSheet("color: orange;")
                else:
                    consistency_label.setStyleSheet("color: red; font-weight: bold;")
                layout.addWidget(consistency_label)

            # Заполнение таблицы
            table.setRowCount(len(labels))
            max_w = np.max(w) if len(w) > 0 else 0

            for row in range(len(labels)):
                # Столбец №
                item_num = QTableWidgetItem(str(row + 1))
                item_num.setTextAlignment(Qt.AlignCenter)

                # Название элемента
                item_label = QTableWidgetItem(labels[row])
                item_label.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                # Главный вектор (ΓB)
                item_cb = QTableWidgetItem(f"{CB[row]:.6f}")
                item_cb.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                # Вектор приоритетов (w)
                w_value = w[row] * 100 if show_percent else w[row]
                w_text = f"{w_value:.2f}%" if show_percent else f"{w_value:.6f}"
                item_w = QTableWidgetItem(w_text)
                item_w.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                # ВП второго уровня (только для таблицы второго уровня)
                if is_second_level:
                    slp_value = second_level_w[row] * 100 if show_percent else second_level_w[row]
                    slp_text = f"{slp_value:.2f}%" if show_percent else f"{slp_value:.6f}"
                    item_slp = QTableWidgetItem(slp_text)
                    item_slp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    table.setItem(row, 4, item_slp)

                # Выделение строки с максимальным приоритетом
                if w[row] == max_w:
                    highlight_color = QColor(235, 245, 235)
                    text_color = QColor(0, 100, 0)
                    font = QFont()
                    font.setBold(True)

                    cols = [0, 1, 2, 3]
                    if is_second_level:
                        cols.append(4)

                    for col in cols:
                        item = table.item(row, col)
                        if item:
                            item.setBackground(highlight_color)
                            item.setForeground(text_color)
                            item.setFont(font)

                table.setItem(row, 0, item_num)
                table.setItem(row, 1, item_label)
                table.setItem(row, 2, item_cb)
                table.setItem(row, 3, item_w)

            layout.addWidget(table)
            self.res_display_layout.addWidget(group)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать таблицу:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _get_color_for_value(self, value, min_val, max_val):
        """Возвращает цвет в зависимости от значения"""
        normalized = (value - min_val) / (max_val - min_val)
        # Градиент от красного (0) через желтый (0.5) к зеленому (1)
        red = min(255, int(255 * (1 - normalized * 2) if normalized < 0.5 else 0))
        green = min(255, int(255 * normalized * 2 if normalized < 0.5 else 255))
        blue = 0
        return QColor(red, green, blue)

    def _create_bar_chart(self, labels, values, title, show_percent=False):
        """Создание столбчатой диаграммы"""
        fig, ax = plt.subplots(figsize=(10, 4))

        if show_percent:
            total = np.sum(values)
            if total > 0:
                values = [v / total * 100 for v in values]
            ylabel = "Приоритет, %"
        else:
            ylabel = "Значение приоритета"

        bars = ax.bar(labels, values)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        plt.xticks(rotation=45, ha='right')

        # Добавляем значения на столбцы
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{height:.1f}%' if show_percent else f'{height:.3f}',
                ha='center', va='bottom'
            )

        canvas = FigureCanvas(fig)
        self.res_display_layout.addWidget(canvas)

    def _create_pie_chart(self, labels, values, title):
        """Создание оптимизированной круговой диаграммы с улучшенной читаемостью"""
        try:
            # Преобразование и проверка данных
            values_array = np.array(values, dtype=float)
            if len(labels) != len(values_array):
                raise ValueError("Количество меток и значений не совпадает")

            # Фильтрация данных
            positive_mask = values_array > 0
            filtered_labels = [label for label, keep in zip(labels, positive_mask) if keep]
            filtered_values = values_array[positive_mask]

            if len(filtered_values) == 0:
                raise ValueError("Нет положительных значений для отображения")

            # Создание фигуры с увеличенными отступами
            fig, ax = plt.subplots(figsize=(10, 8))  # Увеличенный размер
            fig.subplots_adjust(left=0.1, right=0.7, top=0.9, bottom=0.1)  # Отступы для легенды

            # Генерация цветовой палитры
            color_palette = plt.cm.tab20c(np.linspace(0, 1, len(filtered_labels)))

            # Форматирование подписей (автоматический перенос длинных текстов)
            wrapped_labels = ['\n'.join(textwrap.wrap(label, width=12)) for label in filtered_labels]

            # Настройка отображения значений
            def autopct_format(pct):
                total = np.sum(filtered_values)
                val = pct / 100. * total
                if hasattr(self, 'display_percent') and self.display_percent:
                    return f'{pct:.1f}%'
                return f'{val:.3f}\n({pct:.1f}%)'

            # Построение диаграммы
            wedges, texts, autotexts = ax.pie(
                filtered_values,
                labels=wrapped_labels,
                autopct=autopct_format,
                startangle=90,
                counterclock=False,
                colors=color_palette,
                wedgeprops={'linewidth': 1.5, 'edgecolor': 'white', 'width': 0.6},
                textprops={'fontsize': 10, 'fontweight': 'normal'},
                pctdistance=0.8,
                labeldistance=1.1
            )

            # Настройка заголовка
            ax.set_title(title, pad=25, fontsize=14, fontweight='bold')

            # Улучшенная легенда
            legend = ax.legend(
                wedges,
                [f"{label}: {value:.3f}" for label, value in zip(filtered_labels, filtered_values)],
                title="Детализация:",
                loc="center left",
                bbox_to_anchor=(1.05, 0.5),
                fontsize=10,
                title_fontsize=11,
                framealpha=0.9
            )
            legend.get_frame().set_edgecolor('#DDDDDD')

            # Настройка подписей процентов
            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')
                autotext.set_color('white')

            # Добавление тени для эффекта объема
            for wedge in wedges:
                wedge.set_edgecolor('#F0F0F0')
                wedge.set_linewidth(0.5)

            # Создание и настройка холста
            canvas = FigureCanvas(fig)
            canvas.setMinimumSize(900, 700)  # Фиксированный минимальный размер
            self.res_display_layout.addWidget(canvas)

        except Exception as e:
            error_msg = f"Ошибка при создании круговой диаграммы: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Ошибка визуализации", error_msg)
            if 'fig' in locals():
                plt.close(fig)

    def _display_heatmap_results(self):
        """Отображение всех результатов в виде тепловых карт"""
        # 1. Приоритеты типов критериев
        type_names = list(self.backend.criteria_types.keys())
        type_priority = self.result_data['type_priority']
        self._create_heatmap(type_names, type_priority,
                             "Приоритеты видов критериев (Первый уровень)")

        # 2. Приоритеты критериев (второй уровень)
        self._create_heatmap(self.backend.criteria,
                             self.result_data['criteria_priority'],
                             "Приоритеты критериев (Второй уровень)")

        # 3. Приоритеты альтернатив (третий уровень)
        if 'alternatives_priority' in self.result_data:
            self._create_heatmap(
                self.backend.alternatives,
                self.result_data['alternatives_priority'],
                "Итоговые приоритеты альтернатив"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AHPFrontend()
    window.show()
    sys.exit(app.exec_())

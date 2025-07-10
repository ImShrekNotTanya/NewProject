import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from backend import AHPBackend
import numpy as np
import pandas as pd
from tkinter import scrolledtext


class AHPFrontend:
    def __init__(self, root):
        self.root = root
        self.root.title("Метод анализа иерархий (AHP)")
        self.root.state('zoomed')

        self.backend = AHPBackend()
        self.current_matrix = None
        self.current_items = []
        self.result_display_mode = "chart"  # chart/table/diagram
        self.result_data = None

        self._setup_styles()
        self._create_widgets()
        self._bind_mousewheel()

    def _bind_mousewheel(self):
        """Bind mousewheel scrolling to all scrollable widgets except first tab"""
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)  # Linux up
        self.root.bind_all("<Button-5>", self._on_mousewheel)  # Linux down

    def _bind_mousewheel(self):
        """Bind mousewheel scrolling to all scrollable widgets except first tab"""
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)  # Linux up
        self.root.bind_all("<Button-5>", self._on_mousewheel)  # Linux down

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling only for comparison and results tabs"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:  # Skip for first tab
            return

        widget = event.widget
        if isinstance(widget, tk.Canvas):
            if event.num == 5 or event.delta == -120:
                widget.yview_scroll(1, "units")
            elif event.num == 4 or event.delta == 120:
                widget.yview_scroll(-1, "units")
        return "break"

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'))
        self.style.configure('Matrix.TLabel', font=('Arial', 10), relief='ridge')
        self.style.configure('MatrixHeader.TLabel', font=('Arial', 10, 'bold'), relief='ridge')
        self.style.configure('ResultBtn.TButton', font=('Arial', 10, 'bold'), padding=5)

    def _create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        # Вкладки
        self._create_hierarchy_tab()
        self._create_comparison_tab()
        self._create_results_tab()

        # Блокировка вкладок
        self.notebook.tab(1, state='disabled')
        self.notebook.tab(2, state='disabled')

    def _create_hierarchy_tab(self):
        """Вкладка для определения иерархии"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="1. Определение элементов иерархии")

        # Основной фрейм с прокруткой
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 1. Альтернативы
        alt_frame = ttk.LabelFrame(scrollable_frame, text="1. Ввод альтернатив")
        alt_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(alt_frame, text="Альтернатива:").pack(side='left', padx=5)
        self.alt_entry = ttk.Entry(alt_frame, width=30)
        self.alt_entry.pack(side='left', padx=5)

        ttk.Button(alt_frame, text="Добавить", command=self._add_alternative).pack(side='left', padx=5)
        self.alt_list_frame = ttk.Frame(alt_frame)
        self.alt_list_frame.pack(fill='x', pady=5)

        # 2. Критерии
        crit_frame = ttk.LabelFrame(scrollable_frame, text="2. Ввод критериев")
        crit_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(crit_frame, text="Критерий:").pack(side='left', padx=5)
        self.crit_entry = ttk.Entry(crit_frame, width=30)
        self.crit_entry.pack(side='left', padx=5)

        ttk.Button(crit_frame, text="Добавить", command=self._add_criterion).pack(side='left', padx=5)
        self.crit_list_frame = ttk.Frame(crit_frame)
        self.crit_list_frame.pack(fill='x', pady=5)

        # 3. Типы критериев
        type_frame = ttk.LabelFrame(scrollable_frame, text="3. Ввод видов критериев")
        type_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(type_frame, text="Вид критериев:").pack(side='left', padx=5)
        self.type_entry = ttk.Entry(type_frame, width=20)
        self.type_entry.pack(side='left', padx=5)

        self.type_criteria = tk.Listbox(type_frame, selectmode='multiple', height=4)
        self.type_criteria.pack(side='left', padx=5, fill='x', expand=True)

        ttk.Button(type_frame, text="Добавить", command=self._add_criterion_type).pack(side='left', padx=5)
        self.type_list_frame = ttk.Frame(type_frame)
        self.type_list_frame.pack(fill='x', pady=5)

        # Кнопка генерации матриц
        ttk.Button(
            scrollable_frame,
            text="Сгенерировать матрицы сравнений →",
            command=self._generate_matrices
        ).pack(pady=10)

    def _create_comparison_tab(self):
        """Вкладка для парных сравнений"""
        self.comp_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.comp_tab, text="2. Метод парных сравнений")

    def _create_results_tab(self):
        """Вкладка с результатами"""
        self.res_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.res_tab, text="3. Результаты анализа")

        # Frame for result display controls
        self.res_controls_frame = ttk.Frame(self.res_tab)
        self.res_controls_frame.pack(fill='x', padx=10, pady=5)

        # Frame for actual results display
        self.res_display_frame = ttk.Frame(self.res_tab)
        self.res_display_frame.pack(fill='both', expand=True)

    def _add_alternative(self):
        if self.backend.add_alternative(self.alt_entry.get()):
            self.alt_entry.delete(0, 'end')
            self._update_alt_list()
            self._update_criteria_listbox()

    def _add_criterion(self):
        if self.backend.add_criterion(self.crit_entry.get()):
            self.crit_entry.delete(0, 'end')
            self._update_crit_list()
            self._update_criteria_listbox()

    def _add_criterion_type(self):
        type_name = self.type_entry.get().strip()
        selected = [self.type_criteria.get(i) for i in self.type_criteria.curselection()]

        if type_name and selected and self.backend.add_criterion_type(type_name, selected):
            self.type_entry.delete(0, 'end')
            self._update_type_list()

    def _update_alt_list(self):
        for widget in self.alt_list_frame.winfo_children():
            widget.destroy()

        for i, alt in enumerate(self.backend.alternatives):
            frame = ttk.Frame(self.alt_list_frame)
            frame.pack(fill='x', pady=2)

            ttk.Label(frame, text=alt).pack(side='left', padx=5)
            ttk.Button(frame, text="Удалить", command=lambda idx=i: self._remove_item('alternatives', idx)).pack(
                side='right', padx=5)

    def _update_crit_list(self):
        for widget in self.crit_list_frame.winfo_children():
            widget.destroy()

        for i, crit in enumerate(self.backend.criteria):
            frame = ttk.Frame(self.crit_list_frame)
            frame.pack(fill='x', pady=2)

            ttk.Label(frame, text=crit).pack(side='left', padx=5)
            ttk.Button(frame, text="Удалить", command=lambda idx=i: self._remove_item('criteria', idx)).pack(
                side='right', padx=5)

    def _update_type_list(self):
        for widget in self.type_list_frame.winfo_children():
            widget.destroy()

        for type_name, criteria in self.backend.criteria_types.items():
            frame = ttk.Frame(self.type_list_frame)
            frame.pack(fill='x', pady=2)

            ttk.Label(frame, text=f"{type_name}: {', '.join(criteria)}").pack(side='left', padx=5)
            ttk.Button(frame, text="Удалить", command=lambda tn=type_name: self._remove_criterion_type(tn)).pack(
                side='right', padx=5)

    def _update_criteria_listbox(self):
        self.type_criteria.delete(0, 'end')
        for crit in self.backend.criteria:
            self.type_criteria.insert('end', crit)

    def _remove_item(self, item_type, index):
        if item_type == 'alternatives':
            del self.backend.alternatives[index]
            self._update_alt_list()
        elif item_type == 'criteria':
            # Удаляем из типов критериев
            crit = self.backend.criteria[index]
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
        del self.backend.criteria_types[type_name]
        self._update_type_list()

    def _generate_matrices(self):
        """Генерация всех необходимых матриц"""
        if not self.backend.alternatives or not self.backend.criteria or not self.backend.criteria_types:
            messagebox.showerror("Ошибка", "Заполните все разделы иерархии")
            return

        # Активируем вкладку сравнений
        self.notebook.tab(1, state='normal')
        self.notebook.select(1)
        self._setup_comparison_tab()

    def _setup_comparison_tab(self):
        """Настройка вкладки с матрицами сравнений"""
        for widget in self.comp_tab.winfo_children():
            widget.destroy()

        # Основной фрейм с прокруткой
        canvas = tk.Canvas(self.comp_tab)
        scrollbar = ttk.Scrollbar(self.comp_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 1. Матрица сравнения типов критериев (первый уровень)
        ttk.Label(
            scrollable_frame,
            text="Первый уровень: Сравнение видов критериев",
            font=('Arial', 12, 'bold')
        ).pack(pady=(10, 5))

        type_names = list(self.backend.criteria_types.keys())
        self._create_matrix_ui(scrollable_frame, type_names, 'criteria_types')

        # 2. Матрицы сравнения критериев (второй уровень)
        ttk.Label(
            scrollable_frame,
            text="Второй уровень: Сравнение критериев по видам",
            font=('Arial', 12, 'bold')
        ).pack(pady=(20, 5))

        for type_name in type_names:
            ttk.Label(
                scrollable_frame,
                text=f"Вид критериев: {type_name}",
                font=('Arial', 11)
            ).pack(pady=(10, 5))

            criteria = self.backend.criteria_types[type_name]
            self._create_matrix_ui(scrollable_frame, criteria, f'criteria_{type_name}')

        # 3. Матрицы сравнения альтернатив (третий уровень)
        if self.backend.alternatives:
            ttk.Label(
                scrollable_frame,
                text="Третий уровень: Сравнение альтернатив по критериям",
                font=('Arial', 12, 'bold')
            ).pack(pady=(20, 5))

            for criterion in self.backend.criteria:
                ttk.Label(
                    scrollable_frame,
                    text=f"Критерий: {criterion}",
                    font=('Arial', 11)
                ).pack(pady=(10, 5))

                self._create_matrix_ui(scrollable_frame, self.backend.alternatives, f'alternatives_{criterion}')

        # Кнопка расчета
        ttk.Button(
            scrollable_frame,
            text="Рассчитать приоритеты →",
            command=self._calculate_priorities
        ).pack(pady=20)

    def _create_matrix_ui(self, parent, items, matrix_key):
        """Создание UI для одной матрицы сравнений"""
        frame = ttk.Frame(parent, borderwidth=1, relief='solid')
        frame.pack(fill='x', padx=10, pady=5)

        # Заголовки столбцов
        for j, item in enumerate(items):
            ttk.Label(
                frame,
                text=item,
                style='MatrixHeader.TLabel',
                width=15,
                anchor="center"
            ).grid(row=0, column=j + 1, padx=2, pady=2, sticky="nsew")

        # Тело матрицы
        for i, row_item in enumerate(items):
            # Заголовок строки
            ttk.Label(
                frame,
                text=row_item,
                style='MatrixHeader.TLabel',
                width=15,
                anchor="e"
            ).grid(row=i + 1, column=0, padx=2, pady=2, sticky="nsew")

            for j, col_item in enumerate(items):
                if i == j:
                    # Диагональ
                    ttk.Label(
                        frame,
                        text="1",
                        style='Matrix.TLabel',
                        width=8,
                        anchor="center"
                    ).grid(row=i + 1, column=j + 1, padx=2, pady=2, sticky="nsew")
                elif i < j:
                    # Верхний треугольник - редактируемое поле
                    entry = ttk.Entry(
                        frame,
                        font=('Arial', 10),
                        width=8,
                        justify='center'
                    )
                    entry.insert(0, "")
                    entry.grid(row=i + 1, column=j + 1, padx=2, pady=2, sticky="nsew")

                    # Сохраняем ссылку на виджет
                    if not hasattr(self, 'matrix_entries'):
                        self.matrix_entries = {}
                    self.matrix_entries[(matrix_key, i, j)] = entry

                    # Привязываем обработчик изменения
                    entry.bind('<FocusOut>', lambda e, k=matrix_key, r=i, c=j: self._update_reciprocal_value(k, r, c))
                else:
                    # Нижний треугольник - вычисляемое поле
                    label = ttk.Label(
                        frame,
                        text="",
                        style='Matrix.TLabel',
                        width=8,
                        anchor="center"
                    )
                    label.grid(row=i + 1, column=j + 1, padx=2, pady=2, sticky="nsew")
                    self.matrix_entries[(matrix_key, i, j)] = label

    def _update_reciprocal_value(self, matrix_key, i, j):
        """Обновление обратного значения в матрице"""
        entry = self.matrix_entries.get((matrix_key, i, j))
        recip_entry = self.matrix_entries.get((matrix_key, j, i))

        if entry and recip_entry:
            value = entry.get()
            try:
                if value.startswith("1/"):
                    recip_value = value[2:]
                else:
                    if value == "1":
                        recip_value = "1"
                    else:
                        recip_value = f"1/{value}"

                # Обновляем нижний треугольник
                if isinstance(recip_entry, ttk.Label):
                    recip_entry.config(text=recip_value)
            except:
                pass

    def _calculate_priorities(self):
        """Сбор данных и расчет приоритетов"""
        # 1. Собираем все матрицы сравнений
        matrices = {}

        # Матрица типов критериев
        type_names = list(self.backend.criteria_types.keys())
        type_comparisons = {}
        for i in range(len(type_names)):
            for j in range(i + 1, len(type_names)):
                entry = self.matrix_entries.get(('criteria_types', i, j))
                if entry:
                    value = entry.get()
                    type_comparisons[(i, j)] = value
                    # Обновляем нижний треугольник
                    self._update_reciprocal_value('criteria_types', i, j)

        matrices['criteria_types'] = self.backend.build_matrix(type_names, type_comparisons)
        if matrices['criteria_types'] is None:
            messagebox.showerror("Ошибка", "Проверьте заполнение матрицы сравнения видов критериев")
            return

        # Матрицы критериев по типам
        for type_name, criteria in self.backend.criteria_types.items():
            comparisons = {}
            n = len(criteria)
            for i in range(n):
                for j in range(i + 1, n):
                    entry = self.matrix_entries.get((f'criteria_{type_name}', i, j))
                    if entry:
                        value = entry.get()
                        comparisons[(i, j)] = value
                        # Обновляем нижний треугольник
                        self._update_reciprocal_value(f'criteria_{type_name}', i, j)

            matrix = self.backend.build_matrix(criteria, comparisons)
            if matrix is None:
                messagebox.showerror("Ошибка", f"Проверьте матрицу сравнения критериев для вида '{type_name}'")
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
                        if entry:
                            value = entry.get()
                            comparisons[(i, j)] = value
                            # Обновляем нижний треугольник
                            self._update_reciprocal_value(f'alternatives_{criterion}', i, j)

                matrix = self.backend.build_matrix(self.backend.alternatives, comparisons)
                if matrix is None:
                    messagebox.showerror("Ошибка",
                                         f"Проверьте матрицу сравнения альтернатив для критерия '{criterion}'")
                    return
                matrices[f'alternatives_{criterion}'] = matrix

        # 2. Сохраняем матрицы в backend
        self.backend.matrices = matrices

        # 3. Выполняем расчет AHP
        results = self.backend.calculate_ahp()
        if results is None:
            messagebox.showerror("Ошибка", "Ошибка при расчете приоритетов")
            return

        # 4. Показываем результаты
        self._show_results(results)

    def _show_results(self, results):
        """Отображение результатов анализа"""
        self.notebook.tab(2, state='normal')
        self.notebook.select(2)

        # Очищаем предыдущие результаты
        for widget in self.res_display_frame.winfo_children():
            widget.destroy()
        for widget in self.res_controls_frame.winfo_children():
            widget.destroy()

        # Сохраняем данные результатов
        self.result_data = results

        # Создаем элементы управления для выбора представления
        ttk.Label(self.res_controls_frame, text="Формат отображения:").pack(side='left', padx=5)

        ttk.Button(
            self.res_controls_frame,
            text="График",
            command=lambda: self._set_result_display_mode("chart"),
            style='ResultBtn.TButton'
        ).pack(side='left', padx=5)

        ttk.Button(
            self.res_controls_frame,
            text="Таблица",
            command=lambda: self._set_result_display_mode("table"),
            style='ResultBtn.TButton'
        ).pack(side='left', padx=5)

        ttk.Button(
            self.res_controls_frame,
            text="Диаграмма",
            command=lambda: self._set_result_display_mode("diagram"),
            style='ResultBtn.TButton'
        ).pack(side='left', padx=5)

        # Отображаем результаты в текущем режиме
        self._display_results()

    def _set_result_display_mode(self, mode):
        """Установка режима отображения результатов"""
        self.result_display_mode = mode
        self._display_results()

    def _display_results(self):
        """Отображение результатов в выбранном формате"""
        # Очищаем область отображения
        for widget in self.res_display_frame.winfo_children():
            widget.destroy()

        if self.result_display_mode == "chart":
            self._display_chart_results()
        elif self.result_display_mode == "table":
            self._display_table_results()
        elif self.result_display_mode == "diagram":
            self._display_diagram_results()

    def _display_chart_results(self):
        """Отображение результатов в виде графиков"""
        # 1. Приоритеты типов критериев
        type_names = list(self.backend.criteria_types.keys())
        type_priority = self.result_data['type_priority']
        self._create_bar_chart(self.res_display_frame, type_names, type_priority,
                               "Приоритеты видов критериев (Первый уровень)")

        # 2. Приоритеты критериев (второй уровень)
        self._create_bar_chart(self.res_display_frame, self.backend.criteria,
                               self.result_data['criteria_priority'],
                               "Приоритеты критериев (Второй уровень)")

        # 3. Приоритеты альтернатив (третий уровень)
        if 'alternatives_priority' in self.result_data:
            self._create_bar_chart(
                self.res_display_frame,
                self.backend.alternatives,
                self.result_data['alternatives_priority'],
                "Итоговые приоритеты альтернатив",
                show_percent=True
            )

    def _display_table_results(self):
        """Отображение результатов в виде таблиц"""
        # Основной фрейм с прокруткой
        canvas = tk.Canvas(self.res_display_frame)
        scrollbar = ttk.Scrollbar(self.res_display_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 1. Приоритеты типов критериев
        type_names = list(self.backend.criteria_types.keys())
        type_priority = self.result_data['type_priority']
        self._create_table(scrollable_frame, type_names, type_priority,
                           "Приоритеты видов критериев (Первый уровень)")

        # 2. Приоритеты критериев (второй уровень)
        self._create_table(scrollable_frame, self.backend.criteria,
                           self.result_data['criteria_priority'],
                           "Приоритеты критериев (Второй уровень)")

        # 3. Приоритеты альтернатив (третий уровень)
        if 'alternatives_priority' in self.result_data:
            self._create_table(
                scrollable_frame,
                self.backend.alternatives,
                self.result_data['alternatives_priority'],
                "Итоговые приоритеты альтернатив",
                show_percent=True
            )

    def _display_diagram_results(self):
        """Отображение результатов в виде круговых диаграмм"""
        # 1. Приоритеты типов критериев
        type_names = list(self.backend.criteria_types.keys())
        type_priority = self.result_data['type_priority']
        self._create_pie_chart(self.res_display_frame, type_names, type_priority,
                               "Приоритеты видов критериев (Первый уровень)")

        # 2. Приоритеты критериев (второй уровень)
        self._create_pie_chart(self.res_display_frame, self.backend.criteria,
                               self.result_data['criteria_priority'],
                               "Приоритеты критериев (Второй уровень)")

        # 3. Приоритеты альтернатив (третий уровень)
        if 'alternatives_priority' in self.result_data:
            self._create_pie_chart(
                self.res_display_frame,
                self.backend.alternatives,
                self.result_data['alternatives_priority'],
                "Итоговые приоритеты альтернатив"
            )

    def _create_table(self, parent, labels, values, title, show_percent=False):
        """Создание таблицы с результатами"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(frame, text=title, font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        # Создаем DataFrame для удобного отображения
        if show_percent:
            total = np.sum(values)
            values = [v / total * 100 for v in values]
            df = pd.DataFrame({
                "Элемент": labels,
                "Приоритет, %": [f"{v:.1f}" for v in values]
            })
        else:
            df = pd.DataFrame({
                "Элемент": labels,
                "Значение приоритета": [f"{v:.3f}" for v in values]
            })

        # Создаем текстовое поле с таблицей
        text = scrolledtext.ScrolledText(frame, width=60, height=min(len(labels) + 2, 10))
        text.pack(fill='x', padx=10, pady=5)
        text.insert('end', df.to_string(index=False))
        text.config(state='disabled')

    def _create_bar_chart(self, parent, labels, values, title, show_percent=False):
        """Создание столбчатой диаграммы"""
        fig, ax = plt.subplots(figsize=(10, 4))

        if show_percent:
            total = np.sum(values)
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

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='x', padx=20, pady=10)

    def _create_pie_chart(self, parent, labels, values, title):
        """Создание круговой диаграммы"""
        fig, ax = plt.subplots(figsize=(8, 8))

        # Нормализуем значения для отображения в процентах
        total = np.sum(values)
        if total > 0:
            values = [v / total * 100 for v in values]

        # Создаем круговую диаграмму
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
        )

        ax.set_title(title)
        ax.axis('equal')  # Круг выглядит кругом

        # Улучшаем читаемость подписей
        for text in texts + autotexts:
            text.set_fontsize(10)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', padx=20, pady=10, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = AHPFrontend(root)
    root.mainloop()

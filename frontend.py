import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from backend import PairwiseComparisonBackend


class PairwiseComparisonFrontend:
    def __init__(self, root):
        self.root = root
        self.root.title("Метод парных сравнений")
        self.root.state('zoomed')

        self.backend = PairwiseComparisonBackend()
        self.entry_widgets = {}

        self._setup_styles()
        self._create_widgets()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'))
        self.style.configure('Matrix.TLabel', font=('Arial', 10), relief='ridge')
        self.style.configure('MatrixHeader.TLabel', font=('Arial', 10, 'bold'), relief='ridge')

    def _create_widgets(self):
        # Основной Notebook с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        # Вкладки
        self._create_criteria_tab()
        self._create_matrix_tab()
        self._create_results_tab()

        # Блокируем вкладки до выполнения предыдущих шагов
        self.notebook.tab(1, state='disabled')
        self.notebook.tab(2, state='disabled')

    def _create_criteria_tab(self):
        """Вкладка для ввода критериев"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="1. Определение критериев")

        # Заголовок
        ttk.Label(frame, text="Определение критериев", font=('Arial', 14, 'bold')).pack(pady=10)

        # Поле ввода
        input_frame = ttk.Frame(frame)
        input_frame.pack(pady=10)

        ttk.Label(input_frame, text="Критерий:").pack(side='left', padx=5)
        self.criteria_entry = ttk.Entry(input_frame, width=30)
        self.criteria_entry.pack(side='left', padx=5)

        ttk.Button(
            input_frame,
            text="Добавить",
            command=self._add_criterion
        ).pack(side='left', padx=5)

        # Список критериев
        self.criteria_list_frame = ttk.Frame(frame)
        self.criteria_list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Кнопка перехода к матрице
        ttk.Button(
            frame,
            text="Создать матрицу сравнений →",
            command=self._enable_matrix_tab
        ).pack(pady=10)

    def _create_matrix_tab(self):
        """Вкладка с матрицей сравнений"""
        self.matrix_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.matrix_tab, text="2. Матрица парных сравнений")

    def _create_results_tab(self):
        """Вкладка с результатами"""
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="3. Результат анализа")

    def _add_criterion(self):
        """Добавление нового критерия"""
        if self.backend.add_criterion(self.criteria_entry.get()):
            self.criteria_entry.delete(0, 'end')
            self._update_criteria_list()
        else:
            messagebox.showerror("Ошибка", "Некорректное имя критерия или уже существует")

    def _update_criteria_list(self):
        """Обновление списка критериев"""
        for widget in self.criteria_list_frame.winfo_children():
            widget.destroy()

        for i, criterion in enumerate(self.backend.get_criteria()):
            frame = ttk.Frame(self.criteria_list_frame)
            frame.pack(fill='x', pady=2)

            ttk.Label(frame, text=criterion).pack(side='left', padx=5)
            ttk.Button(
                frame,
                text="Удалить",
                command=lambda idx=i: self._remove_criterion(idx)
            ).pack(side='right', padx=5)

    def _remove_criterion(self, index: int):
        """Удаление критерия"""
        self.backend.remove_criterion(index)
        self._update_criteria_list()

    def _enable_matrix_tab(self):
        """Активация вкладки с матрицей"""
        if len(self.backend.get_criteria()) >= 2:
            self.notebook.tab(1, state='normal')
            self.notebook.select(1)
            self._build_matrix_ui()
        else:
            messagebox.showerror("Ошибка", "Нужно минимум 2 критерия")

    def _build_matrix_ui(self):
        """Построение интерфейса матрицы"""
        for widget in self.matrix_tab.winfo_children():
            widget.destroy()

        # Заголовок
        ttk.Label(
            self.matrix_tab,
            text="Матрица парных сравнений",
            font=('Arial', 14, 'bold')
        ).pack(pady=10)

        # Шкала Саати
        saati_scale = "Шкала Саати: 1 - равная важность, 3 - умеренное превосходство, " + \
                      "5 - сильное превосходство, 7 - очень сильное превосходство, " + \
                      "9 - крайнее превосходство"
        ttk.Label(
            self.matrix_tab,
            text=saati_scale,
            font=('Arial', 10),
            wraplength=600
        ).pack(pady=5)

        # Прокручиваемая область
        canvas = tk.Canvas(self.matrix_tab)
        scrollbar = ttk.Scrollbar(self.matrix_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Построение матрицы
        self._build_matrix_grid(scrollable_frame)

        # Кнопка расчета
        ttk.Button(
            self.matrix_tab,
            text="Рассчитать приоритеты",
            command=self._calculate_priorities
        ).pack(pady=10)

    def _build_matrix_grid(self, parent_frame):
        """Построение сетки матрицы"""
        criteria = self.backend.get_criteria()
        n = len(criteria)

        # Заголовки столбцов
        for j in range(n):
            ttk.Label(
                parent_frame,
                text=criteria[j],
                style='MatrixHeader.TLabel',
                width=15,
                anchor="center"
            ).grid(row=0, column=j + 1, padx=2, pady=2, sticky="nsew")

        # Тело матрицы
        self.entry_widgets = {}
        for i in range(n):
            # Заголовок строки
            ttk.Label(
                parent_frame,
                text=criteria[i],
                style='MatrixHeader.TLabel',
                width=15,
                anchor="e"
            ).grid(row=i + 1, column=0, padx=2, pady=2, sticky="nsew")

            for j in range(n):
                if i == j:
                    ttk.Label(
                        parent_frame,
                        text="1",
                        style='Matrix.TLabel',
                        width=8,
                        anchor="center"
                    ).grid(row=i + 1, column=j + 1, padx=2, pady=2, sticky="nsew")
                else:
                    entry = ttk.Entry(
                        parent_frame,
                        font=('Arial', 10),
                        width=8,
                        justify='center'
                    )
                    if i < j:
                        entry.insert(0, "")
                    entry.grid(row=i + 1, column=j + 1, padx=2, pady=2, sticky="nsew")
                    self.entry_widgets[(i, j)] = entry
                    entry.bind("<FocusOut>", lambda e, row=i, col=j: self._update_cell(row, col))

    def _update_cell(self, row: int, col: int):
        """Обновление симметричной ячейки"""
        widget = self.entry_widgets[(row, col)]
        value = widget.get()

        if not self.backend.validate_matrix_value(value):
            messagebox.showerror("Ошибка", "Используйте значения из шкалы Саати")
            widget.delete(0, 'end')
            return

        symmetric_value = self.backend.get_symmetric_value(value)
        if symmetric_value and (col, row) in self.entry_widgets:
            self.entry_widgets[(col, row)].delete(0, 'end')
            self.entry_widgets[(col, row)].insert(0, symmetric_value)

    def _calculate_priorities(self):
        """Расчет и отображение результатов"""
        # Сбор данных из матрицы
        matrix_data = {(i, j): widget.get() for (i, j), widget in self.entry_widgets.items()}

        if not self.backend.build_comparison_matrix(matrix_data):
            messagebox.showerror("Ошибка", "Проверьте заполнение матрицы")
            return

        if not self.backend.calculate_priorities():
            messagebox.showerror("Ошибка", "Ошибка при расчете приоритетов")
            return

        # Выбор формата отображения
        format_type = self._ask_result_format()
        if not format_type:
            return

        # Активация вкладки результатов
        self.notebook.tab(2, state='normal')
        self.notebook.select(2)
        self._show_results(format_type)

    def _ask_result_format(self) -> Optional[str]:
        """Диалог выбора формата результатов"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Формат результатов")
        dialog.geometry("280x160")

        ttk.Label(dialog, text="Выберите формат отображения:", font=('Arial', 12)).pack(pady=10)

        format_var = tk.StringVar(value="table")

        formats = [
            ("Таблица", "table"),
            ("Столбчатая диаграмма", "bar"),
            ("Круговая диаграмма", "pie")
        ]

        for text, mode in formats:
            ttk.Radiobutton(
                dialog,
                text=text,
                variable=format_var,
                value=mode
            ).pack(anchor='w', padx=20, pady=2)

        confirmed = False

        def on_confirm():
            nonlocal confirmed
            confirmed = True
            dialog.destroy()

        ttk.Button(dialog, text="Показать", command=on_confirm).pack(pady=10)

        dialog.wait_window()
        return format_var.get() if confirmed else None

    def _show_results(self, format_type: str):
        """Отображение результатов в выбранном формате"""
        for widget in self.results_tab.winfo_children():
            widget.destroy()

        # Заголовок
        ttk.Label(
            self.results_tab,
            text="Результаты анализа",
            font=('Arial', 14, 'bold')
        ).pack(pady=10)

        # Панель выбора формата
        format_frame = ttk.Frame(self.results_tab)
        format_frame.pack(pady=10)

        for text, mode in [("Таблица", "table"), ("Диаграмма", "bar"), ("График", "pie")]:
            ttk.Button(
                format_frame,
                text=text,
                command=lambda m=mode: self._show_results(m)
            ).pack(side='left', padx=5)

        # Отображение результатов
        if format_type == "table":
            self._show_table()
        elif format_type == "bar":
            self._show_bar_chart()
        else:
            self._show_pie_chart()

    def _show_table(self):
        """Табличное представление"""
        tree = ttk.Treeview(self.results_tab, columns=('criteria', 'priority'), show='headings')
        tree.heading('criteria', text='Критерий')
        tree.heading('priority', text='Приоритет')

        for crit, prio in zip(self.backend.get_criteria(), self.backend.get_priorities()):
            tree.insert('', 'end', values=(crit, f"{prio:.4f}"))

        tree.pack(fill='both', expand=True, padx=20, pady=10)

    def _show_bar_chart(self):
        """Столбчатая диаграмма"""
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(self.backend.get_criteria(), self.backend.get_priorities())
        ax.set_title('Приоритеты критериев')
        ax.set_ylabel('Значение')
        plt.xticks(rotation=45)

        canvas = FigureCanvasTkAgg(fig, master=self.results_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=20, pady=10)

    def _show_pie_chart(self):
        """Круговая диаграмма"""
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.pie(
            self.backend.get_priorities(),
            labels=self.backend.get_criteria(),
            autopct='%1.1f%%',
            startangle=90
        )
        ax.set_title('Распределение приоритетов')

        canvas = FigureCanvasTkAgg(fig, master=self.results_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=20, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = PairwiseComparisonFrontend(root)
    root.mainloop()
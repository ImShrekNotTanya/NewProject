import numpy as np
from typing import List, Dict, Tuple, Optional, Union

import numpy as np
from typing import List, Dict, Tuple, Optional, Union

class AHPBackend:
    # Константы для проверки значений по шкале Саати
    VALID_SAATY_VALUES = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    RI_VALUES = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12,
                 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45,
                 10: 1.49, 11: 1.51, 12: 1.54, 13: 1.56,
                 14: 1.57, 15: 1.59}

    def convert_to_percent(self, values: np.ndarray) -> np.ndarray:
        """Преобразует значения в проценты"""
        total = np.sum(values)
        if total > 0:
            return values / total * 100
        return values


    def __init__(self):
        self.alternatives: List[str] = []
        self.criteria: List[str] = []
        self.criteria_types: Dict[str, List[str]] = {}
        self.matrices: Dict[str, np.ndarray] = {}
        self.priorities: Dict[str, np.ndarray] = {}
        self.eigenvectors: Dict[str, np.ndarray] = {}
        self.consistency_data: Dict[str, Dict[str, float]] = {}

    def add_alternative(self, name: str) -> bool:
        """Добавляет альтернативу, если она не пустая и не дублируется"""
        name = name.strip()
        if name and name not in self.alternatives:
            self.alternatives.append(name)
            return True
        return False

    def add_criterion(self, name: str) -> bool:
        """Добавляет критерий, если он не пустой и не дублируется"""
        name = name.strip()
        if name and name not in self.criteria:
            self.criteria.append(name)
            return True
        return False

    def add_criterion_type(self, type_name: str, criteria: List[str]) -> bool:
        """Добавляет тип критериев с проверкой валидности"""
        type_name = type_name.strip()
        if not type_name or not criteria:
            return False

        # Фильтруем только существующие критерии
        valid_criteria = [c for c in criteria if c in self.criteria]
        if valid_criteria:
            self.criteria_types[type_name] = valid_criteria
            return True
        return False

    def validate_matrix_value(self, value: str) -> bool:
        """Проверяет значение по шкале Саати (1-9 или 1/1-1/9)"""
        try:
            if value.startswith("1/"):
                num = float(value[2:])
                return num in self.VALID_SAATY_VALUES
            num = float(value)
            return num in self.VALID_SAATY_VALUES
        except (ValueError, AttributeError):
            return False

    def build_matrix(self, items: List[str], comparisons: Dict[Tuple[int, int], str]) -> Optional[np.ndarray]:
        """Строит матрицу парных сравнений из введенных данных"""
        n = len(items)
        if n == 0:
            return None

        matrix = np.eye(n)  # Начинаем с единичной матрицы

        for (i, j), value in comparisons.items():
            if not (0 <= i < n and 0 <= j < n) or not self.validate_matrix_value(value):
                return None

            try:
                if value.startswith("1/"):
                    val = 1 / float(value[2:])
                else:
                    val = float(value)

                matrix[i, j] = val
                matrix[j, i] = 1 / val
            except (ValueError, ZeroDivisionError):
                return None

        return matrix

    def calculate_priority_vector(self, matrix: np.ndarray) -> np.ndarray:
        """Вычисляет **главный вектор (ΓB)** — геометрическое среднее строк матрицы.
        Нормализацию (получение w) делаем отдельно!
        """
        n = matrix.shape[0]
        # Геометрическое среднее каждой строки (это и есть ΓB)
        CB = np.array([np.prod(matrix[i, :]) ** (1 / n) for i in range(n)])
        return CB  # Возвращаем НЕнормализованный вектор!

    def normalize_priority_vector(self, CB: np.ndarray) -> np.ndarray:
        """Преобразует главный вектор (ΓB) в вектор приоритетов (w)"""
        return CB / np.sum(CB)  # Нормализация

    def calculate_ahp(self) -> Optional[Dict[str, np.ndarray]]:
        if not self.matrices:
            return None

        results = {}
        type_names = list(self.criteria_types.keys())

        try:
            # 1. Расчет для типов критериев
            type_matrix = self.matrices.get('criteria_types')
            if type_matrix is None:
                return None

            CB_types = self.calculate_priority_vector(type_matrix)  # ΓB
            w_types = self.normalize_priority_vector(CB_types)  # w
            results['type_priority'] = w_types
            results['CB_types'] = CB_types  # Сохраняем ΓB для согласованности

            # 2. Расчет для критериев
            criteria_priority = np.zeros(len(self.criteria))

            for type_name, type_criteria in self.criteria_types.items():
                type_idx = type_names.index(type_name)
                criteria_matrix = self.matrices.get(f'criteria_{type_name}')
                if criteria_matrix is None:
                    return None

                CB_criteria = self.calculate_priority_vector(criteria_matrix)  # ΓB
                w_criteria = self.normalize_priority_vector(CB_criteria)  # w
                criteria_priority[[self.criteria.index(c) for c in type_criteria]] = w_criteria * w_types[type_idx]

            results['criteria_priority'] = criteria_priority

            # 3. Расчет для альтернатив (если есть)
            if self.alternatives:
                alternatives_priority = np.zeros(len(self.alternatives))
                for i, criterion in enumerate(self.criteria):
                    alt_matrix = self.matrices.get(f'alternatives_{criterion}')
                    if alt_matrix is None:
                        return None

                    CB_alt = self.calculate_priority_vector(alt_matrix)  # ΓB
                    w_alt = self.normalize_priority_vector(CB_alt)  # w
                    alternatives_priority += w_alt * criteria_priority[i]

                results['alternatives_priority'] = alternatives_priority

            return results

        except Exception as e:
            print(f"Ошибка: {str(e)}")
            return None

    def calculate_second_level_priorities(self, criteria_weights, first_level_weights):
        """Вычисляет приоритеты второго уровня путем умножения векторов"""
        try:
            if len(criteria_weights) != len(first_level_weights):
                raise ValueError("Размеры векторов должны совпадать")
            second_level = criteria_weights * first_level_weights
            return second_level / np.sum(second_level)  # Нормализация
        except Exception as e:
            print(f"Ошибка расчета второго уровня: {str(e)}")
            return None

    def check_consistency(self, matrix: np.ndarray) -> dict:
        """Расчет показателей согласованности для матрицы"""
        n = matrix.shape[0]

        if n <= 2:
            return {
                'lambda_max': float(n),
                'CI': 0.0,
                'RI': 0.0,
                'CR': 0.0,
                'status': 'Отличная согласованность'
            }

        # Получаем ΓB (главный вектор)
        CB, _ = self.calculate_priority_vector(matrix)  # игнорируем w, берем только ΓB

        # Вычисляем lambda_max
        weighted_sum = np.dot(matrix, CB)
        lambda_max = np.mean(weighted_sum / CB)

        # Индекс согласованности
        CI = (lambda_max - n) / (n - 1)

        # Случайный индекс
        RI = self.RI_VALUES.get(n, 1.49)

        # Отношение согласованности
        CR = CI / RI if RI != 0 else 0

        # Определение статуса
        if CR < 0.1:
            status = "Отличная согласованность"
        elif CR < 0.2:
            status = "Приемлемая согласованность"
        else:
            status = "ТРЕБУЕТСЯ пересмотр"

        return {
            'lambda_max': lambda_max,
            'CI': round(CI, 3),
            'RI': round(RI, 3),
            'CR': round(CR, 3),
            'status': status
        }

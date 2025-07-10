import numpy as np
from typing import List, Dict, Tuple, Optional


class AHPBackend:
    def __init__(self):
        self.alternatives: List[str] = []
        self.criteria: List[str] = []
        self.criteria_types: Dict[str, List[str]] = {}
        self.matrices: Dict[str, np.ndarray] = {}
        self.priorities: Dict[str, np.ndarray] = {}

    def add_alternative(self, name: str) -> bool:
        name = name.strip()
        if name and name not in self.alternatives:
            self.alternatives.append(name)
            return True
        return False

    def add_criterion(self, name: str) -> bool:
        name = name.strip()
        if name and name not in self.criteria:
            self.criteria.append(name)
            return True
        return False

    def add_criterion_type(self, type_name: str, criteria: List[str]) -> bool:
        type_name = type_name.strip()
        if not type_name or not criteria:
            return False

        # Проверяем что все указанные критерии существуют
        valid_criteria = [c for c in criteria if c in self.criteria]
        if not valid_criteria:
            return False

        self.criteria_types[type_name] = valid_criteria
        return True

    def validate_matrix_value(self, value: str) -> bool:
        """Проверка по шкале Саати"""
        try:
            if value.startswith("1/"):
                num = float(value[2:])
                return num in {1, 2, 3, 4, 5, 6, 7, 8, 9}
            else:
                num = float(value)
                return num in {1, 2, 3, 4, 5, 6, 7, 8, 9}
        except ValueError:
            return False

    def build_matrix(self, items: List[str], comparisons: Dict[Tuple[int, int], str]) -> Optional[np.ndarray]:
        n = len(items)
        matrix = np.ones((n, n))

        for (i, j), value in comparisons.items():
            if not self.validate_matrix_value(value):
                return None

            try:
                if value.startswith("1/"):
                    matrix[i, j] = 1 / float(value[2:])
                else:
                    matrix[i, j] = float(value)
                matrix[j, i] = 1 / matrix[i, j]
            except (ValueError, IndexError):
                return None

        return matrix

    def calculate_priority_vector(self, matrix: np.ndarray) -> np.ndarray:
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        max_idx = np.argmax(eigenvalues.real)
        priority_vector = eigenvectors[:, max_idx].real
        return priority_vector / np.sum(priority_vector)

    def calculate_ahp(self):
        """Основной метод расчета AHP"""
        results = {}

        # 1. Расчет приоритетов для типов критериев (первый уровень)
        type_names = list(self.criteria_types.keys())
        type_matrix = self.matrices.get('criteria_types')
        if type_matrix is None or len(type_matrix) != len(type_names):
            return None

        type_priority = self.calculate_priority_vector(type_matrix)
        results['type_priority'] = type_priority

        # 2. Расчет приоритетов для критериев (второй уровень)
        criteria_priority = np.zeros(len(self.criteria))

        for type_name, type_criteria in self.criteria_types.items():
            type_idx = type_names.index(type_name)
            criteria_indices = [self.criteria.index(c) for c in type_criteria]
            criteria_matrix = self.matrices.get(f'criteria_{type_name}')

            if criteria_matrix is None or len(criteria_matrix) != len(type_criteria):
                return None

            local_priority = self.calculate_priority_vector(criteria_matrix)
            criteria_priority[criteria_indices] = local_priority * type_priority[type_idx]

        results['criteria_priority'] = criteria_priority

        # 3. Расчет приоритетов для альтернатив (третий уровень)
        if not self.alternatives:
            return results

        alternatives_priority = np.zeros(len(self.alternatives))

        for i, criterion in enumerate(self.criteria):
            alt_matrix = self.matrices.get(f'alternatives_{criterion}')
            if alt_matrix is None or len(alt_matrix) != len(self.alternatives):
                return None

            local_priority = self.calculate_priority_vector(alt_matrix)
            alternatives_priority += local_priority * criteria_priority[i]

        results['alternatives_priority'] = alternatives_priority
        return results

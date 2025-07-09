import numpy as np
from typing import List, Dict, Tuple, Optional

class PairwiseComparisonBackend:
    def __init__(self):
        self.criteria: List[str] = []
        self.comparison_matrix: Optional[np.ndarray] = None
        self.priorities: Optional[np.ndarray] = None

    def add_criterion(self, name: str) -> bool:
        """Добавление нового критерия"""
        name = name.strip()
        if not name or name in self.criteria:
            return False
        self.criteria.append(name)
        return True

    def remove_criterion(self, index: int) -> None:
        """Удаление критерия по индексу"""
        if 0 <= index < len(self.criteria):
            del self.criteria[index]

    def validate_matrix_value(self, value: str) -> bool:
        """Проверка значения по шкале Саати"""
        if not value:
            return False
        try:
            if value.startswith("1/"):
                num = float(value[2:])
                return num in {1, 2, 3, 4, 5, 6, 7, 8, 9}
            else:
                num = float(value)
                return num in {1, 2, 3, 4, 5, 6, 7, 8, 9}
        except ValueError:
            return False

    def get_symmetric_value(self, value: str) -> Optional[str]:
        """Получение обратного значения для симметричной ячейки"""
        if not value:
            return None
        try:
            if value.startswith("1/"):
                return str(int(float(value[2:])))
            else:
                return f"1/{int(float(value))}"
        except ValueError:
            return None

    def build_comparison_matrix(self, matrix_data: Dict[Tuple[int, int], str]) -> bool:
        """Построение числовой матрицы из введенных данных"""
        if len(self.criteria) < 2:
            return False

        n = len(self.criteria)
        self.comparison_matrix = np.ones((n, n))

        for (i, j), value in matrix_data.items():
            if not value:
                return False
            try:
                if value.startswith("1/"):
                    self.comparison_matrix[i, j] = 1 / float(value[2:])
                else:
                    self.comparison_matrix[i, j] = float(value)
            except ValueError:
                return False
        return True

    def calculate_priorities(self) -> bool:
        """Вычисление приоритетов методом собственного вектора"""
        if self.comparison_matrix is None:
            return False

        try:
            eigenvalues, eigenvectors = np.linalg.eig(self.comparison_matrix)
            max_idx = np.argmax(eigenvalues.real)
            self.priorities = eigenvectors[:, max_idx].real
            self.priorities = self.priorities / np.sum(self.priorities)
            return True
        except Exception:
            return False

    def get_priorities(self) -> Optional[List[float]]:
        """Получение рассчитанных приоритетов"""
        return self.priorities.tolist() if self.priorities is not None else None

    def get_criteria(self) -> List[str]:
        """Получение списка критериев"""
        return self.criteria.copy()
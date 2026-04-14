"""
Онлайн-платформа курсів (LMS)
Реалізація сутностей: Content, VideoLesson, TextLesson, Quiz, Question,
CourseModule, Course, Student, Certificate
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from typing import Iterator
import uuid
import re


# ---------------------------------------------------------------------------
# Валідація
# ---------------------------------------------------------------------------

def validate_email(email: str) -> str:
    pattern = r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError(f"Невалідний email: {email!r}")
    return email


def validate_non_negative(value: float, name: str = "Значення") -> float:
    if value < 0:
        raise ValueError(f"{name} не може бути від'ємним: {value}")
    return value


def validate_percent(value: int | float, name: str = "Відсоток") -> float:
    if not (0 <= value <= 100):
        raise ValueError(f"{name} повинен бути у діапазоні 0–100: {value}")
    return float(value)


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------

class Question:
    """Питання для тесту з варіантами відповідей."""

    def __init__(self, text: str, options: list[str], correct: str) -> None:
        if correct not in options:
            raise ValueError(f"Правильна відповідь {correct!r} відсутня у варіантах.")
        self.text = text
        self.options: list[str] = list(options)
        self.correct = correct

    def check(self, answer: str) -> bool:
        """Повертає True, якщо відповідь правильна."""
        return answer == self.correct

    def __repr__(self) -> str:
        return f"Question({self.text!r})"


# ---------------------------------------------------------------------------
# Content (абстрактний базовий клас)
# ---------------------------------------------------------------------------

class Content(ABC):
    """Абстрактний контент курсу."""

    def __init__(self, title: str, duration: int) -> None:
        self.title = title
        self.duration: int = int(validate_non_negative(duration, "Тривалість"))

    @abstractmethod
    def display(self) -> None:
        """Друкує тип контенту та назву."""

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.title!r})"


# ---------------------------------------------------------------------------
# VideoLesson
# ---------------------------------------------------------------------------

class VideoLesson(Content):
    """Відеоурок із посиланням та роздільною здатністю."""

    def __init__(self, title: str, duration: int, url: str, resolution: str = "1080p") -> None:
        super().__init__(title, duration)
        self.url = url
        self.resolution = resolution

    def display(self) -> None:
        print(f"[Відео] {self.title}  |  {self.resolution}  |  {self.url}")


# ---------------------------------------------------------------------------
# TextLesson
# ---------------------------------------------------------------------------

class TextLesson(Content):
    """Текстовий урок."""

    def __init__(self, title: str, text: str) -> None:
        words = text.split()
        # duration = приблизно 200 слів/хв
        super().__init__(title, max(1, len(words) // 200))
        self.text = text
        self.word_count: int = len(words)

    def display(self) -> None:
        print(f"[Текст] {self.title}  |  {self.word_count} слів")


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------

class Quiz(Content):
    """Тест, що складається з питань."""

    def __init__(self, title: str, questions: list[Question], passing_score: int = 60) -> None:
        super().__init__(title, duration=len(questions) * 2)   # 2 хв на питання
        self.questions: list[Question] = list(questions)
        self.passing_score: float = validate_percent(passing_score, "Прохідний бал")

    def evaluate(self, answers: list[str]) -> dict:
        """
        Оцінює відповіді студента.

        :param answers: список відповідей у порядку питань
        :returns: dict з ключами 'score', 'passed', 'correct', 'total'
        """
        if len(answers) != len(self.questions):
            raise ValueError(
                f"Очікується {len(self.questions)} відповідей, отримано {len(answers)}."
            )
        correct = sum(q.check(a) for q, a in zip(self.questions, answers))
        total = len(self.questions)
        score = (correct / total * 100) if total else 0.0
        return {
            "score": round(score, 1),
            "passed": score >= self.passing_score,
            "correct": correct,
            "total": total,
        }

    def display(self) -> None:
        print(f"[Тест] {self.title}  |  {len(self.questions)} питань  |  прохідний бал: {self.passing_score}%")


# ---------------------------------------------------------------------------
# CourseModule
# ---------------------------------------------------------------------------

class CourseModule:
    """Модуль курсу — іменований контейнер контенту."""

    def __init__(self, name: str, content: list[Content] | None = None) -> None:
        self.name = name
        self._content: list[Content] = list(content) if content else []

    def add(self, item: Content) -> None:
        if not isinstance(item, Content):
            raise TypeError(f"Очікується Content, отримано {type(item).__name__}.")
        self._content.append(item)

    @property
    def total_duration(self) -> int:
        return sum(c.duration for c in self._content)

    def __len__(self) -> int:
        return len(self._content)

    def __iter__(self) -> Iterator[Content]:
        return iter(self._content)

    def __repr__(self) -> str:
        return f"CourseModule({self.name!r}, {len(self)} елементів)"


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course:
    """Курс — набір модулів з ціною."""

    def __init__(
        self,
        title: str,
        author: str,
        price: float = 0.0,
        modules: list[CourseModule] | None = None,
    ) -> None:
        self.title = title
        self.author = author
        self.price: float = validate_non_negative(price, "Ціна")
        self.modules: list[CourseModule] = list(modules) if modules else []
        self._reviews: list[dict] = []

    def add_module(self, module: CourseModule) -> None:
        self.modules.append(module)

    def total_duration(self) -> int:
        """Повертає загальну тривалість всіх модулів у хвилинах."""
        return sum(m.total_duration for m in self.modules)

    def all_content(self) -> list[Content]:
        """Плаский список усього контенту курсу."""
        return [item for module in self.modules for item in module]

    def add_review(self, student_name: str, rating: int, comment: str = "") -> None:
        validate_percent(rating * 20, "Рейтинг (1–5)")   # 1–5 → 20–100
        self._reviews.append({"student": student_name, "rating": rating, "comment": comment})

    @property
    def average_rating(self) -> float | None:
        if not self._reviews:
            return None
        return round(sum(r["rating"] for r in self._reviews) / len(self._reviews), 2)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Course):
            return NotImplemented
        return self.title == other.title

    def __lt__(self, other: "Course") -> bool:
        return self.price < other.price

    def __repr__(self) -> str:
        return f"Course({self.title!r}, {self.price} грн)"


# ---------------------------------------------------------------------------
# Student
# ---------------------------------------------------------------------------

class Student:
    """Студент, який може записуватись на курси та відстежувати прогрес."""

    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email: str = validate_email(email)
        self.courses: list[Course] = []
        self._progress: dict[str, set[int]] = {}   # course.title → {content_ids}

    def enroll(self, course: Course) -> None:
        """Записатись на курс (ідемпотентно)."""
        if course not in self.courses:
            self.courses.append(course)
            self._progress[course.title] = set()
            print(f"{self.name} записався(лась) на курс «{course.title}».")
        else:
            print(f"{self.name} вже записаний(а) на курс «{course.title}».")

    def complete_content(self, course: Course, content: Content) -> None:
        """Відзначити одиницю контенту як пройдену."""
        if course not in self.courses:
            raise ValueError(f"Студент не записаний на курс «{course.title}».")
        self._progress[course.title].add(id(content))
        print(f"✓  «{content.title}» позначено як завершено.")

    def progress(self, course: Course) -> float:
        """Повертає відсоток пройденого контенту (0.0 – 100.0)."""
        if course not in self.courses:
            raise ValueError(f"Студент не записаний на курс «{course.title}».")
        all_items = course.all_content()
        if not all_items:
            return 0.0
        done = self._progress.get(course.title, set())
        return round(len(done) / len(all_items) * 100, 1)

    def __repr__(self) -> str:
        return f"Student({self.name!r}, {self.email!r})"


# ---------------------------------------------------------------------------
# Certificate
# ---------------------------------------------------------------------------

class Certificate:
    """Сертифікат про завершення курсу."""

    def __init__(self, student: Student, course: Course, issue_date: date | None = None) -> None:
        self.student = student
        self.course = course
        self.issue_date: date = issue_date or date.today()
        self.uid: str = str(uuid.uuid4())[:8].upper()

    def __str__(self) -> str:
        return (
            f"Сертифікат #{self.uid}\n"
            f"  Студент : {self.student.name} ({self.student.email})\n"
            f"  Курс    : {self.course.title} — {self.course.author}\n"
            f"  Дата    : {self.issue_date.strftime('%d.%m.%Y')}"
        )

    def __repr__(self) -> str:
        return f"Certificate(uid={self.uid!r})"


# ---------------------------------------------------------------------------
# Демонстрація
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Контент ---
    v1 = VideoLesson("Вступ до Python", duration=15, url="https://example.com/py-intro", resolution="1080p")
    v2 = VideoLesson("Функції та замикання", duration=20, url="https://example.com/py-closures")
    t1 = TextLesson("Що таке ООП?", text="Об'єктно-орієнтоване програмування — це парадигма " * 50)

    q_list = [
        Question("Що виводить print(2**3)?", ["6", "8", "9", "23"], "8"),
        Question("Яке ключове слово визначає клас?", ["def", "class", "struct", "type"], "class"),
        Question("Що таке список у Python?", ["незмінна колекція", "змінна впорядкована колекція",
                                               "словник", "кортеж"], "змінна впорядкована колекція"),
    ]
    quiz1 = Quiz("Тест: основи Python", q_list, passing_score=66)

    # --- Модулі ---
    module1 = CourseModule("Модуль 1: Основи")
    module1.add(v1)
    module1.add(t1)

    module2 = CourseModule("Модуль 2: Функції та тест")
    module2.add(v2)
    module2.add(quiz1)

    # --- Курс ---
    course = Course("Python з нуля", author="Олена Коваль", price=499.0)
    course.add_module(module1)
    course.add_module(module2)

    print("=" * 55)
    print(f"Курс: {course.title}")
    print(f"Тривалість: {course.total_duration()} хв")
    print(f"Модулів: {len(course.modules)}, одиниць контенту: {len(course.all_content())}")
    print()

    # Відображення контенту
    for item in course.all_content():
        item.display()
    print()

    # --- Студент ---
    student = Student("Тарас Мельник", "taras@example.com")
    student.enroll(course)
    print(f"Прогрес: {student.progress(course)}%")

    # Проходження уроків
    all_content = course.all_content()
    student.complete_content(course, all_content[0])
    student.complete_content(course, all_content[1])
    print(f"Прогрес: {student.progress(course)}%")

    # --- Тест ---
    result = quiz1.evaluate(["8", "class", "змінна впорядкована колекція"])
    print(f"\nРезультат тесту: {result['score']}% — {'✅ Складено' if result['passed'] else '❌ Не складено'}")
    student.complete_content(course, all_content[2])
    student.complete_content(course, all_content[3])
    print(f"Фінальний прогрес: {student.progress(course)}%")

    # --- Відгук ---
    course.add_review(student.name, rating=5, comment="Чудовий курс!")
    print(f"\nСередній рейтинг курсу: {course.average_rating} / 5")

    # --- Сертифікат ---
    cert = Certificate(student, course)
    print("\n" + "=" * 55)
    print(cert)

    # --- Порівняння курсів ---
    course2 = Course("JavaScript для початківців", author="Іван Сидоренко", price=299.0)
    print(f"\n«{course2.title}» дешевший? {course2 < course}")
    print(f"Курси однакові? {course == course2}")
    print(f"CourseModule __len__: {len(module1)}")
    print(f"CourseModule __iter__: {[str(c) for c in module1]}")

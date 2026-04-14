# ============================================
# Назва завдання: Онлайн-платформа курсів (LMS)
# Студент: Большак Микита Чергійович
# Додатковий функціонал: система відгуків із середнім рейтингом,
#   об'єднання модулів через __add__, автоматичний підрахунок
#   word_count і duration для TextLesson, видача Certificate
#   лише при 100% прогресу.
# ============================================

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Iterator
import re
import uuid


# ============================================================
#  Допоміжні функції валідації
#  Винесені окремо, щоб не дублювати перевірки у конструкторах.
# ============================================================

def validate_email(email: str) -> str:
    """Перевіряє формат email і повертає його, або кидає ValueError.

    Args:
        email: рядок для перевірки.

    Returns:
        Той самий рядок, якщо він відповідає шаблону.

    Raises:
        ValueError: якщо формат email некоректний.
    """
    pattern = r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError(f"Невалідний email: {email!r}")
    return email


def validate_non_negative(value: float, name: str = "Значення") -> float:
    """Перевіряє, що числове значення >= 0.

    Args:
        value: число, яке перевіряється.
        name:  людська назва поля (для повідомлення про помилку).

    Returns:
        Те саме значення як float.

    Raises:
        ValueError: якщо value < 0.
    """
    if value < 0:
        raise ValueError(f"{name} не може бути від'ємним: {value}")
    return float(value)


def validate_percent(value: int | float, name: str = "Відсоток") -> float:
    """Перевіряє, що значення знаходиться в діапазоні 0–100.

    Args:
        value: число у відсотках.
        name:  людська назва поля.

    Returns:
        Те саме значення як float.

    Raises:
        ValueError: якщо value < 0 або value > 100.
    """
    if not (0 <= value <= 100):
        raise ValueError(f"{name} повинен бути у діапазоні 0–100: {value}")
    return float(value)


# ============================================================
#  Question — одне питання тесту
# ============================================================

class Question:
    """Одне питання Quiz із варіантами відповідей і правильною відповіддю.

    Attributes:
        text:    текст питання.
        options: список варіантів відповідей.
        correct: єдина правильна відповідь (має бути серед options).
    """

    def __init__(self, text: str, options: list[str], correct: str) -> None:
        """Ініціалізує питання.

        Args:
            text:    текст питання.
            options: список варіантів (≥ 2).
            correct: правильна відповідь.

        Raises:
            TypeError:  якщо text або correct не є str, або options не list.
            ValueError: якщо correct відсутній у options, або options порожній.
        """
        if not isinstance(text, str):
            raise TypeError(f"text повинен бути str, отримано {type(text).__name__}.")
        if not isinstance(options, list) or not options:
            raise ValueError("options повинен бути непорожнім списком рядків.")
        if correct not in options:
            raise ValueError(f"Правильна відповідь {correct!r} відсутня у варіантах.")

        self.text: str = text
        self.options: list[str] = list(options)
        self.correct: str = correct

    def check(self, answer: str) -> bool:
        """Перевіряє одну відповідь.

        Args:
            answer: відповідь студента.

        Returns:
            True, якщо відповідь збігається з правильною.
        """
        return answer == self.correct

    def __repr__(self) -> str:
        return f"Question({self.text!r})"


# ============================================================
#  Content — абстрактний базовий клас (рівень 1 ієрархії)
# ============================================================

class Content(ABC):
    """Абстрактна одиниця навчального контенту.

    Усі конкретні типи контенту (відео, текст, тест) наслідують цей клас.
    Забороняє пряме створення екземплярів завдяки ABC.

    Attributes:
        title:    назва контенту.
        duration: орієнтовна тривалість у хвилинах (≥ 0).
    """

    def __init__(self, title: str, duration: int) -> None:
        """Ініціалізує базові поля контенту.

        Args:
            title:    назва контенту (непорожній рядок).
            duration: тривалість у хвилинах.

        Raises:
            TypeError:  якщо title не str.
            ValueError: якщо duration < 0 або title порожній.
        """
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title повинен бути непорожнім рядком.")
        self.title: str = title
        self.duration: int = int(validate_non_negative(duration, "Тривалість"))

    @abstractmethod
    def display(self) -> None:
        """Друкує тип контенту та його назву.

        Кожен нащадок зобов'язаний реалізувати цей метод.
        """

    def __str__(self) -> str:
        """Повертає назву контенту (зручно при print і str())."""
        return self.title

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.title!r})"


# ============================================================
#  VideoLesson — рівень 2 ієрархії
# ============================================================

class VideoLesson(Content):
    """Відеоурок із посиланням та роздільною здатністю.

    Attributes:
        url:        пряме посилання на відео.
        resolution: роздільна здатність (наприклад, '1080p', '4K').
    """

    # Допустимі роздільні здатності
    VALID_RESOLUTIONS: frozenset[str] = frozenset({"360p", "480p", "720p", "1080p", "4K"})

    def __init__(
        self,
        title: str,
        duration: int,
        url: str,
        resolution: str = "1080p",
    ) -> None:
        """Ініціалізує відеоурок.

        Args:
            title:      назва уроку.
            duration:   тривалість у хвилинах.
            url:        посилання на відео.
            resolution: роздільна здатність; за замовчуванням '1080p'.

        Raises:
            ValueError: якщо resolution не входить до VALID_RESOLUTIONS.
        """
        super().__init__(title, duration)

        if resolution not in self.VALID_RESOLUTIONS:
            raise ValueError(
                f"Непідтримувана роздільна здатність {resolution!r}. "
                f"Допустимі: {sorted(self.VALID_RESOLUTIONS)}."
            )
        self.url: str = url
        self.resolution: str = resolution

    def display(self) -> None:
        """Виводить інформацію про відеоурок."""
        print(f"[Відео] {self.title}  |  {self.resolution}  |  {self.duration} хв  |  {self.url}")


# ============================================================
#  TextLesson — рівень 2 ієрархії
# ============================================================

class TextLesson(Content):
    """Текстовий урок.

    Тривалість обчислюється автоматично: ~200 слів на хвилину.

    Attributes:
        text:       повний текст уроку.
        word_count: кількість слів (обчислюється автоматично).
    """

    # Середня швидкість читання (слів на хвилину)
    WORDS_PER_MINUTE: int = 200

    def __init__(self, title: str, text: str) -> None:
        """Ініціалізує текстовий урок і автоматично розраховує тривалість.

        Args:
            title: назва уроку.
            text:  текст уроку (непорожній).

        Raises:
            ValueError: якщо text порожній.
        """
        if not text.strip():
            raise ValueError("Текст уроку не може бути порожнім.")

        words = text.split()
        duration = max(1, len(words) // self.WORDS_PER_MINUTE)
        super().__init__(title, duration)

        self.text: str = text
        self.word_count: int = len(words)

    def display(self) -> None:
        """Виводить інформацію про текстовий урок."""
        print(f"[Текст] {self.title}  |  {self.word_count} слів  |  ~{self.duration} хв")


# ============================================================
#  Quiz — рівень 2 ієрархії; агрегує Question
# ============================================================

class Quiz(Content):
    """Тест, що складається з питань.

    Attributes:
        questions:     список об'єктів Question.
        passing_score: мінімальний прохідний бал у відсотках (0–100).
    """

    def __init__(
        self,
        title: str,
        questions: list[Question],
        passing_score: int = 60,
    ) -> None:
        """Ініціалізує тест.

        Args:
            title:         назва тесту.
            questions:     непорожній список питань.
            passing_score: прохідний бал у відсотках.

        Raises:
            ValueError: якщо questions порожній або passing_score поза 0–100.
            TypeError:  якщо елементи questions — не Question.
        """
        if not questions:
            raise ValueError("Тест повинен містити хоча б одне питання.")
        for i, q in enumerate(questions):
            if not isinstance(q, Question):
                raise TypeError(f"Елемент [{i}] повинен бути Question, отримано {type(q).__name__}.")

        # Приблизно 2 хвилини на кожне питання
        super().__init__(title, duration=len(questions) * 2)
        self.questions: list[Question] = list(questions)
        self.passing_score: float = validate_percent(passing_score, "Прохідний бал")

    def evaluate(self, answers: list[str]) -> dict[str, object]:
        """Оцінює відповіді студента.

        Args:
            answers: список відповідей у тому ж порядку, що й питання.

        Returns:
            Словник із ключами:
                'score'   — результат у відсотках (float),
                'passed'  — чи студент склав тест (bool),
                'correct' — кількість правильних відповідей (int),
                'total'   — загальна кількість питань (int).

        Raises:
            ValueError: якщо кількість відповідей не збігається з кількістю питань.
        """
        if len(answers) != len(self.questions):
            raise ValueError(
                f"Очікується {len(self.questions)} відповідей, отримано {len(answers)}."
            )
        correct_count: int = sum(
            q.check(a) for q, a in zip(self.questions, answers)
        )
        total: int = len(self.questions)
        score: float = (correct_count / total * 100) if total else 0.0
        return {
            "score": round(score, 1),
            "passed": score >= self.passing_score,
            "correct": correct_count,
            "total": total,
        }

    def display(self) -> None:
        """Виводить інформацію про тест."""
        print(
            f"[Тест] {self.title}  |  "
            f"{len(self.questions)} питань  |  "
            f"прохідний бал: {self.passing_score}%"
        )


# ============================================================
#  CourseModule — контейнер контенту (рівень 1)
# ============================================================

class CourseModule:
    """Тематичний модуль курсу — іменований список одиниць Content.

    Підтримує ітерацію, вимірювання довжини та об'єднання модулів
    через оператор + (__add__).

    Attributes:
        name:     назва модуля.
        _content: внутрішній список одиниць Content (інкапсульований).
    """

    def __init__(self, name: str, content: list[Content] | None = None) -> None:
        """Ініціалізує модуль курсу.

        Args:
            name:    назва модуля.
            content: початковий список Content (необов'язково).

        Raises:
            ValueError: якщо name порожній.
            TypeError:  якщо елементи content — не Content.
        """
        if not name.strip():
            raise ValueError("Назва модуля не може бути порожньою.")

        self.name: str = name
        self._content: list[Content] = []

        # Додаємо через .add(), щоб спрацювала перевірка типів
        for item in (content or []):
            self.add(item)

    def add(self, item: Content) -> None:
        """Додає одиницю контенту до модуля.

        Args:
            item: об'єкт, що наслідує Content.

        Raises:
            TypeError: якщо item не є підкласом Content.
        """
        if not isinstance(item, Content):
            raise TypeError(
                f"Очікується Content, отримано {type(item).__name__}."
            )
        self._content.append(item)

    @property
    def total_duration(self) -> int:
        """Сумарна тривалість усього контенту модуля (хвилини)."""
        return sum(c.duration for c in self._content)

    def __len__(self) -> int:
        """Кількість одиниць контенту в модулі."""
        return len(self._content)

    def __iter__(self) -> Iterator[Content]:
        """Ітерація по одиницях контенту модуля."""
        return iter(self._content)

    def __add__(self, other: "CourseModule") -> "CourseModule":
        """Об'єднує два модулі в новий із назвою 'A + B'.

        Args:
            other: інший CourseModule.

        Returns:
            Новий CourseModule, що містить контент обох модулів.

        Raises:
            TypeError: якщо other не є CourseModule.

        Example:
            >>> m3 = module1 + module2
        """
        if not isinstance(other, CourseModule):
            raise TypeError(
                f"Не вдається об'єднати CourseModule з {type(other).__name__}."
            )
        merged = CourseModule(f"{self.name} + {other.name}")
        for item in self:
            merged.add(item)
        for item in other:
            merged.add(item)
        return merged

    def __repr__(self) -> str:
        return f"CourseModule({self.name!r}, {len(self)} елементів)"


# ============================================================
#  Course — навчальний курс (рівень 1)
# ============================================================

class Course:
    """Навчальний курс — набір CourseModule з ціною та системою відгуків.

    Підтримує порівняння за назвою (__eq__) та ціною (__lt__).

    Attributes:
        title:   назва курсу.
        author:  автор (викладач).
        price:   ціна у гривнях (≥ 0).
        modules: список CourseModule.
    """

    def __init__(
        self,
        title: str,
        author: str,
        price: float = 0.0,
        modules: list[CourseModule] | None = None,
    ) -> None:
        """Ініціалізує курс.

        Args:
            title:   назва курсу.
            author:  ім'я автора.
            price:   ціна (≥ 0).
            modules: початкові модулі (необов'язково).

        Raises:
            ValueError: якщо title або author порожні, або price < 0.
            TypeError:  якщо елементи modules — не CourseModule.
        """
        if not title.strip():
            raise ValueError("Назва курсу не може бути порожньою.")
        if not author.strip():
            raise ValueError("Ім'я автора не може бути порожнім.")

        self.title: str = title
        self.author: str = author
        self.price: float = validate_non_negative(price, "Ціна")
        self.modules: list[CourseModule] = []
        self._reviews: list[dict[str, object]] = []

        for m in (modules or []):
            self.add_module(m)

    def add_module(self, module: CourseModule) -> None:
        """Додає модуль до курсу.

        Args:
            module: об'єкт CourseModule.

        Raises:
            TypeError: якщо module не є CourseModule.
        """
        if not isinstance(module, CourseModule):
            raise TypeError(
                f"Очікується CourseModule, отримано {type(module).__name__}."
            )
        self.modules.append(module)

    def total_duration(self) -> int:
        """Повертає загальну тривалість курсу у хвилинах.

        Returns:
            Сума тривалостей усіх модулів.
        """
        return sum(m.total_duration for m in self.modules)

    def all_content(self) -> list[Content]:
        """Повертає плаский список усього контенту курсу.

        Returns:
            Список Content у порядку модулів.
        """
        return [item for module in self.modules for item in module]

    def add_review(self, student_name: str, rating: int, comment: str = "") -> None:
        """Додає відгук студента.

        Args:
            student_name: ім'я студента.
            rating:       оцінка від 1 до 5.
            comment:      текстовий коментар (необов'язково).

        Raises:
            ValueError: якщо rating поза діапазоном 1–5.
        """
        if not (1 <= rating <= 5):
            raise ValueError(f"Рейтинг повинен бути від 1 до 5, отримано {rating}.")
        self._reviews.append({
            "student": student_name,
            "rating": rating,
            "comment": comment,
        })

    @property
    def average_rating(self) -> float | None:
        """Середній рейтинг курсу, або None якщо відгуків ще немає.

        Returns:
            Середнє арифметичне rating усіх відгуків, округлене до 2 знаків.
        """
        if not self._reviews:
            return None
        return round(
            sum(r["rating"] for r in self._reviews) / len(self._reviews),  # type: ignore[operator]
            2,
        )

    def __eq__(self, other: object) -> bool:
        """Два курси вважаються однаковими, якщо у них однакова назва.

        Args:
            other: об'єкт для порівняння.

        Returns:
            True, якщо назви збігаються.
        """
        if not isinstance(other, Course):
            return NotImplemented
        return self.title == other.title

    def __lt__(self, other: "Course") -> bool:
        """Порівнює курси за ціною (менша ціна — 'менший' курс).

        Args:
            other: інший Course.

        Returns:
            True, якщо self.price < other.price.
        """
        if not isinstance(other, Course):
            return NotImplemented
        return self.price < other.price

    def __repr__(self) -> str:
        return f"Course({self.title!r}, {self.price} грн)"


# ============================================================
#  Student — студент (рівень 1)
# ============================================================

class Student:
    """Студент, що записується на курси та відстежує власний прогрес.

    Прогрес зберігається як множина Python id() пройдених об'єктів Content,
    тому той самий об'єкт не зараховується двічі.

    Attributes:
        name:     повне ім'я студента.
        email:    email-адреса (валідується).
        courses:  список курсів, на які студент записаний.
    """

    def __init__(self, name: str, email: str) -> None:
        """Ініціалізує студента.

        Args:
            name:  ім'я студента.
            email: email (перевіряється на коректний формат).

        Raises:
            ValueError: якщо name порожній або email некоректний.
        """
        if not name.strip():
            raise ValueError("Ім'я студента не може бути порожнім.")

        self.name: str = name
        self.email: str = validate_email(email)
        self.courses: list[Course] = []
        # Словник: назва курсу → множина id пройдених Content-об'єктів
        self._progress: dict[str, set[int]] = {}

    def enroll(self, course: Course) -> None:
        """Записує студента на курс (ідемпотентна операція).

        Якщо студент вже записаний, видає повідомлення і нічого не змінює.

        Args:
            course: курс для запису.

        Raises:
            TypeError: якщо course не є Course.
        """
        if not isinstance(course, Course):
            raise TypeError(f"Очікується Course, отримано {type(course).__name__}.")

        if course not in self.courses:
            self.courses.append(course)
            self._progress[course.title] = set()
            print(f"{self.name} записався(лась) на курс «{course.title}».")
        else:
            print(f"{self.name} вже записаний(а) на курс «{course.title}».")

    def complete_content(self, course: Course, content: Content) -> None:
        """Відзначає одиницю контенту як пройдену.

        Args:
            course:  курс, до якого належить контент.
            content: одиниця Content, яку студент пройшов.

        Raises:
            ValueError: якщо студент не записаний на цей курс.
        """
        if course not in self.courses:
            raise ValueError(f"Студент не записаний на курс «{course.title}».")
        # id(content) — унікальний ідентифікатор об'єкта в пам'яті
        self._progress[course.title].add(id(content))
        print(f"✓  «{content.title}» позначено як завершено.")

    def progress(self, course: Course) -> float:
        """Повертає відсоток пройденого контенту курсу.

        Args:
            course: курс, для якого перевіряється прогрес.

        Returns:
            Число від 0.0 до 100.0 включно.

        Raises:
            ValueError: якщо студент не записаний на цей курс.
        """
        if course not in self.courses:
            raise ValueError(f"Студент не записаний на курс «{course.title}».")

        all_items: list[Content] = course.all_content()
        if not all_items:
            return 0.0
        done: set[int] = self._progress.get(course.title, set())
        return round(len(done) / len(all_items) * 100, 1)

    def __repr__(self) -> str:
        return f"Student({self.name!r}, {self.email!r})"


# ============================================================
#  Certificate — сертифікат про завершення (рівень 1)
# ============================================================

class Certificate:
    """Сертифікат, що підтверджує завершення курсу студентом.

    Видається лише тоді, коли студент має 100% прогресу.
    Кожен сертифікат має унікальний ідентифікатор (uid).

    Attributes:
        student:    студент-власник сертифіката.
        course:     пройдений курс.
        issue_date: дата видачі.
        uid:        унікальний 8-символьний код (UUID-фрагмент).
    """

    def __init__(
        self,
        student: Student,
        course: Course,
        issue_date: date | None = None,
    ) -> None:
        """Ініціалізує сертифікат.

        Args:
            student:    студент.
            course:     курс.
            issue_date: дата видачі (за замовчуванням — сьогодні).

        Raises:
            ValueError: якщо студент не має 100% прогресу на курсі.
        """
        # Перевіряємо, що студент дійсно завершив курс
        prog: float = student.progress(course)
        if prog < 100.0:
            raise ValueError(
                f"Сертифікат можна видати лише при 100% прогресу. "
                f"Поточний прогрес: {prog}%."
            )

        self.student: Student = student
        self.course: Course = course
        self.issue_date: date = issue_date or date.today()
        # Беремо перші 8 символів UUID і переводимо у верхній регістр
        self.uid: str = str(uuid.uuid4())[:8].upper()

    def __str__(self) -> str:
        """Повертає форматований текст сертифіката."""
        return (
            f"Сертифікат #{self.uid}\n"
            f"  Студент : {self.student.name} ({self.student.email})\n"
            f"  Курс    : {self.course.title} — {self.course.author}\n"
            f"  Дата    : {self.issue_date.strftime('%d.%m.%Y')}"
        )

    def __repr__(self) -> str:
        return f"Certificate(uid={self.uid!r})"


# ============================================================
#  Демонстрація роботи (запускається лише напряму)
# ============================================================

if __name__ == "__main__":
    print("=" * 55)
    print("        LMS — Онлайн-платформа курсів")
    print("=" * 55)

    # --- Контент ---
    v1 = VideoLesson(
        "Вступ до Python",
        duration=15,
        url="https://example.com/py-intro",
        resolution="1080p",
    )
    v2 = VideoLesson(
        "Функції та замикання",
        duration=20,
        url="https://example.com/py-closures",
    )
    # TextLesson сам рахує duration і word_count
    t1 = TextLesson(
        "Що таке ООП?",
        text="Об'єктно-орієнтоване програмування — це парадигма " * 50,
    )

    questions = [
        Question(
            "Що виводить print(2**3)?",
            ["6", "8", "9", "23"],
            "8",
        ),
        Question(
            "Яке ключове слово визначає клас?",
            ["def", "class", "struct", "type"],
            "class",
        ),
        Question(
            "Що таке список у Python?",
            ["незмінна колекція", "змінна впорядкована колекція", "словник", "кортеж"],
            "змінна впорядкована колекція",
        ),
    ]
    quiz1 = Quiz("Тест: основи Python", questions, passing_score=66)

    # --- Модулі ---
    module1 = CourseModule("Модуль 1: Основи")
    module1.add(v1)
    module1.add(t1)

    module2 = CourseModule("Модуль 2: Функції та тест")
    module2.add(v2)
    module2.add(quiz1)

    # Додатковий функціонал: об'єднання модулів через __add__
    combined = module1 + module2
    print(f"Об'єднаний модуль: {combined!r}\n")

    # --- Курс ---
    course = Course("Python з нуля", author="Олена Коваль", price=499.0)
    course.add_module(module1)
    course.add_module(module2)

    print(f"Курс: {course.title}")
    print(f"Тривалість: {course.total_duration()} хв")
    print(f"Модулів: {len(course.modules)}, одиниць контенту: {len(course.all_content())}")
    print()

    for item in course.all_content():
        item.display()
    print()

    # --- Студент ---
    student = Student("Тарас Мельник", "taras@example.com")
    student.enroll(course)
    print(f"Прогрес після запису: {student.progress(course)}%\n")

    # Проходимо весь контент послідовно
    all_content: list[Content] = course.all_content()
    for item in all_content:
        student.complete_content(course, item)

    print(f"\nПрогрес після проходження: {student.progress(course)}%\n")

    # --- Тест ---
    result = quiz1.evaluate(["8", "class", "змінна впорядкована колекція"])
    status = "✅ Складено" if result["passed"] else "❌ Не складено"
    print(f"Результат тесту: {result['score']}% — {status}")

    # --- Відгук ---
    course.add_review(student.name, rating=5, comment="Чудовий курс!")
    print(f"Середній рейтинг: {course.average_rating} / 5")

    # --- Сертифікат (лише при 100% прогресу) ---
    cert = Certificate(student, course)
    print("\n" + "=" * 55)
    print(cert)

    # --- Порівняння курсів ---
    course2 = Course("JavaScript для початківців", author="Іван Сидоренко", price=299.0)
    print(f"\n«{course2.title}» дешевший за «{course.title}»? {course2 < course}")
    print(f"Курси однакові (за назвою)? {course == course2}")

    # --- __len__ і __iter__ модуля ---
    print(f"\nУ модулі '{module1.name}' — {len(module1)} елементи:")
    for c in module1:
        print(f"  • {c}")

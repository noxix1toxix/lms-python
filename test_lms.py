# ============================================================
#  Unit-тести для LMS-платформи
#  Запуск: python -m pytest test_lms.py -v
#          або: python test_lms.py
# ============================================================

import unittest
from datetime import date

from lms import (
    Certificate,
    Content,
    Course,
    CourseModule,
    Question,
    Quiz,
    Student,
    TextLesson,
    VideoLesson,
    validate_email,
    validate_non_negative,
    validate_percent,
)


# ============================================================
#  Допоміжні функції (фікстури)
# ============================================================

def make_video() -> VideoLesson:
    """Повертає простий VideoLesson для тестів."""
    return VideoLesson("Вступ", duration=10, url="https://x.com/v", resolution="720p")


def make_text() -> TextLesson:
    """Повертає TextLesson із 400 словами (~2 хв)."""
    return TextLesson("Текст", text="слово " * 400)


def make_question() -> Question:
    """Повертає одне тестове питання."""
    return Question("2+2?", ["3", "4", "5"], "4")


def make_quiz() -> Quiz:
    """Повертає Quiz з одним питанням."""
    return Quiz("Міні-тест", [make_question()], passing_score=50)


def make_module(*items: Content) -> CourseModule:
    """Повертає модуль із переданим контентом."""
    m = CourseModule("Тестовий модуль")
    for item in items:
        m.add(item)
    return m


def make_course(price: float = 100.0) -> Course:
    """Повертає курс із одним модулем і одним відеоуроком."""
    c = Course("Тест-курс", author="Автор", price=price)
    m = make_module(make_video())
    c.add_module(m)
    return c


def make_student() -> Student:
    """Повертає студента з коректним email."""
    return Student("Іван Іванов", "ivan@example.com")


# ============================================================
#  Тести валідаційних функцій
# ============================================================

class TestValidators(unittest.TestCase):
    """Перевіряє допоміжні функції валідації."""

    def test_email_valid(self) -> None:
        self.assertEqual(validate_email("a@b.com"), "a@b.com")

    def test_email_invalid(self) -> None:
        with self.assertRaises(ValueError):
            validate_email("not-an-email")

    def test_non_negative_zero(self) -> None:
        self.assertEqual(validate_non_negative(0), 0.0)

    def test_non_negative_negative(self) -> None:
        with self.assertRaises(ValueError):
            validate_non_negative(-1)

    def test_percent_boundary(self) -> None:
        self.assertEqual(validate_percent(0), 0.0)
        self.assertEqual(validate_percent(100), 100.0)

    def test_percent_out_of_range(self) -> None:
        with self.assertRaises(ValueError):
            validate_percent(101)
        with self.assertRaises(ValueError):
            validate_percent(-1)


# ============================================================
#  Тести Question
# ============================================================

class TestQuestion(unittest.TestCase):
    """Перевіряє Question."""

    def setUp(self) -> None:
        self.q = make_question()

    def test_correct_answer(self) -> None:
        self.assertTrue(self.q.check("4"))

    def test_wrong_answer(self) -> None:
        self.assertFalse(self.q.check("3"))

    def test_correct_not_in_options(self) -> None:
        with self.assertRaises(ValueError):
            Question("?", ["a", "b"], "c")

    def test_empty_options(self) -> None:
        with self.assertRaises(ValueError):
            Question("?", [], "a")

    def test_repr(self) -> None:
        self.assertIn("Question", repr(self.q))


# ============================================================
#  Тести Content (через конкретні підкласи)
# ============================================================

class TestContent(unittest.TestCase):
    """Перевіряє базову поведінку Content через VideoLesson / TextLesson."""

    def test_str_returns_title(self) -> None:
        v = make_video()
        self.assertEqual(str(v), v.title)

    def test_repr_contains_class_name(self) -> None:
        self.assertIn("VideoLesson", repr(make_video()))
        self.assertIn("TextLesson", repr(make_text()))

    def test_negative_duration_raises(self) -> None:
        with self.assertRaises(ValueError):
            VideoLesson("X", duration=-1, url="u")

    def test_empty_title_raises(self) -> None:
        with self.assertRaises(ValueError):
            VideoLesson("", duration=5, url="u")

    def test_content_is_abstract(self) -> None:
        # Не можна створити екземпляр абстрактного класу напряму
        with self.assertRaises(TypeError):
            Content("X", 1)  # type: ignore[abstract]


# ============================================================
#  Тести VideoLesson
# ============================================================

class TestVideoLesson(unittest.TestCase):
    """Перевіряє VideoLesson-специфічну логіку."""

    def test_invalid_resolution(self) -> None:
        with self.assertRaises(ValueError):
            VideoLesson("X", 5, "u", resolution="8K")

    def test_default_resolution(self) -> None:
        v = VideoLesson("X", 5, "u")
        self.assertEqual(v.resolution, "1080p")

    def test_display_runs(self) -> None:
        # Просто перевіряємо, що display не кидає виняток
        make_video().display()


# ============================================================
#  Тести TextLesson
# ============================================================

class TestTextLesson(unittest.TestCase):
    """Перевіряє автоматичний підрахунок word_count і duration."""

    def test_word_count(self) -> None:
        t = TextLesson("T", "один два три чотири п'ять")
        self.assertEqual(t.word_count, 5)

    def test_duration_auto(self) -> None:
        # 400 слів / 200 = 2 хв
        t = make_text()
        self.assertEqual(t.duration, 2)

    def test_duration_minimum_one(self) -> None:
        # 10 слів / 200 = 0 → max(1, 0) = 1
        t = TextLesson("T", "слово " * 10)
        self.assertEqual(t.duration, 1)

    def test_empty_text_raises(self) -> None:
        with self.assertRaises(ValueError):
            TextLesson("T", "   ")


# ============================================================
#  Тести Quiz
# ============================================================

class TestQuiz(unittest.TestCase):
    """Перевіряє Quiz.evaluate і валідацію."""

    def setUp(self) -> None:
        self.q = make_quiz()

    def test_perfect_score(self) -> None:
        result = self.q.evaluate(["4"])
        self.assertEqual(result["score"], 100.0)
        self.assertTrue(result["passed"])

    def test_zero_score(self) -> None:
        result = self.q.evaluate(["3"])
        self.assertEqual(result["score"], 0.0)
        self.assertFalse(result["passed"])

    def test_wrong_answer_count(self) -> None:
        with self.assertRaises(ValueError):
            self.q.evaluate(["4", "extra"])

    def test_passing_score_validation(self) -> None:
        with self.assertRaises(ValueError):
            Quiz("X", [make_question()], passing_score=110)

    def test_empty_questions(self) -> None:
        with self.assertRaises(ValueError):
            Quiz("X", [])

    def test_duration_proportional(self) -> None:
        # 3 питання × 2 хв = 6 хв
        q = Quiz("X", [make_question()] * 3)
        self.assertEqual(q.duration, 6)


# ============================================================
#  Тести CourseModule
# ============================================================

class TestCourseModule(unittest.TestCase):
    """Перевіряє CourseModule: len, iter, add, total_duration, __add__."""

    def setUp(self) -> None:
        self.v = make_video()   # duration=10
        self.t = make_text()    # duration=2
        self.m = make_module(self.v, self.t)

    def test_len(self) -> None:
        self.assertEqual(len(self.m), 2)

    def test_iter(self) -> None:
        items = list(self.m)
        self.assertEqual(items, [self.v, self.t])

    def test_total_duration(self) -> None:
        self.assertEqual(self.m.total_duration, 12)

    def test_add_wrong_type(self) -> None:
        with self.assertRaises(TypeError):
            self.m.add("не контент")  # type: ignore[arg-type]

    def test_merge_modules(self) -> None:
        m2 = make_module(make_quiz())
        merged = self.m + m2
        self.assertEqual(len(merged), 3)
        self.assertIn("+", merged.name)

    def test_merge_wrong_type(self) -> None:
        with self.assertRaises(TypeError):
            _ = self.m + "не модуль"  # type: ignore[operator]

    def test_empty_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            CourseModule("")


# ============================================================
#  Тести Course
# ============================================================

class TestCourse(unittest.TestCase):
    """Перевіряє Course: total_duration, eq, lt, reviews."""

    def setUp(self) -> None:
        self.c1 = make_course(price=500.0)
        self.c2 = make_course(price=300.0)

    def test_total_duration(self) -> None:
        # Один VideoLesson з duration=10
        self.assertEqual(self.c1.total_duration(), 10)

    def test_all_content_flat(self) -> None:
        self.assertEqual(len(self.c1.all_content()), 1)

    def test_eq_same_title(self) -> None:
        # Обидва курси мають назву "Тест-курс"
        self.assertEqual(self.c1, self.c2)

    def test_lt_by_price(self) -> None:
        self.assertLess(self.c2, self.c1)

    def test_negative_price_raises(self) -> None:
        with self.assertRaises(ValueError):
            Course("X", "A", price=-1)

    def test_average_rating_none_when_no_reviews(self) -> None:
        self.assertIsNone(self.c1.average_rating)

    def test_average_rating_computed(self) -> None:
        self.c1.add_review("А", 4)
        self.c1.add_review("Б", 2)
        self.assertEqual(self.c1.average_rating, 3.0)

    def test_invalid_rating_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.c1.add_review("А", 6)

    def test_add_wrong_module_type(self) -> None:
        with self.assertRaises(TypeError):
            self.c1.add_module("не модуль")  # type: ignore[arg-type]


# ============================================================
#  Тести Student
# ============================================================

class TestStudent(unittest.TestCase):
    """Перевіряє Student: enroll, complete_content, progress."""

    def setUp(self) -> None:
        self.student = make_student()
        self.course = make_course()
        # Зберігаємо посилання на конкретний об'єкт контенту
        self.content_item = self.course.all_content()[0]

    def test_enroll(self) -> None:
        self.student.enroll(self.course)
        self.assertIn(self.course, self.student.courses)

    def test_enroll_idempotent(self) -> None:
        self.student.enroll(self.course)
        self.student.enroll(self.course)  # другий виклик не дублює
        self.assertEqual(self.student.courses.count(self.course), 1)

    def test_progress_zero_after_enroll(self) -> None:
        self.student.enroll(self.course)
        self.assertEqual(self.student.progress(self.course), 0.0)

    def test_progress_after_complete(self) -> None:
        self.student.enroll(self.course)
        self.student.complete_content(self.course, self.content_item)
        self.assertEqual(self.student.progress(self.course), 100.0)

    def test_complete_without_enroll_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.student.complete_content(self.course, self.content_item)

    def test_progress_without_enroll_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.student.progress(self.course)

    def test_invalid_email_raises(self) -> None:
        with self.assertRaises(ValueError):
            Student("X", "not-email")

    def test_enroll_wrong_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            self.student.enroll("не курс")  # type: ignore[arg-type]


# ============================================================
#  Тести Certificate
# ============================================================

class TestCertificate(unittest.TestCase):
    """Перевіряє Certificate: видача, блокування при неповному прогресі."""

    def _full_student(self) -> tuple[Student, Course]:
        """Повертає студента з 100% прогресом."""
        course = make_course()
        student = make_student()
        student.enroll(course)
        for item in course.all_content():
            student.complete_content(course, item)
        return student, course

    def test_certificate_issued_at_100(self) -> None:
        student, course = self._full_student()
        cert = Certificate(student, course)
        self.assertIsInstance(cert, Certificate)

    def test_certificate_blocked_below_100(self) -> None:
        course = make_course()
        student = make_student()
        student.enroll(course)
        # Не проходимо жодного контенту — 0%
        with self.assertRaises(ValueError):
            Certificate(student, course)

    def test_str_contains_uid(self) -> None:
        student, course = self._full_student()
        cert = Certificate(student, course)
        self.assertIn(cert.uid, str(cert))

    def test_uid_unique(self) -> None:
        s1, c1 = self._full_student()
        s2, c2 = self._full_student()
        cert1 = Certificate(s1, c1)
        cert2 = Certificate(s2, c2)
        self.assertNotEqual(cert1.uid, cert2.uid)

    def test_default_issue_date_is_today(self) -> None:
        student, course = self._full_student()
        cert = Certificate(student, course)
        self.assertEqual(cert.issue_date, date.today())


# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)

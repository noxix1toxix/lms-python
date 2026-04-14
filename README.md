#  LMS - Онлайн-платформа курсів

Навчальний проєкт з об'єктно-орієнтованого програмування на Python.  
Реалізує спрощену систему управління навчанням (Learning Management System) - курси, модулі, відеоуроки, текстові уроки, тести, студенти та сертифікати.

---

##  Структура проєкту

```
lms/
├── lms.py        # Основна реалізація класів
├── test_lms.py   # Unit-тести (58 тестів)
└── README.md
```

---

##  Архітектура класів

```
Content (ABC)
├── VideoLesson     - відеоурок із URL та роздільною здатністю
├── TextLesson      - текстовий урок (duration рахується автоматично)
└── Quiz            - тест із питаннями та прохідним балом
        └── Question    - одне питання з варіантами відповідей

CourseModule        - іменований контейнер Content
Course              - набір CourseModule з ціною та відгуками
Student             - записується на курси, відстежує прогрес
Certificate         - видається лише при 100% прогресу
```

### Магічні методи

| Клас | Методи |
|------|--------|
| `Content` | `__str__`, `__repr__` |
| `CourseModule` | `__len__`, `__iter__`, `__add__`, `__repr__` |
| `Course` | `__eq__` (за назвою), `__lt__` (за ціною), `__repr__` |
| `Certificate` | `__str__`, `__repr__` |

---

##  Додатковий функціонал

- **Система відгуків** - студенти можуть залишати оцінку (1–5) і коментар; `Course.average_rating` рахує середнє
- **Об'єднання модулів** - `module1 + module2` повертає новий `CourseModule` з контентом обох
- **Автоматична тривалість** - `TextLesson` сам рахує `word_count` і `duration` (~200 слів/хв)
- **Захист сертифіката** - `Certificate` кидає `ValueError`, якщо прогрес студента < 100%
- **Валідація роздільної здатності** - `VideoLesson` приймає лише `360p`, `480p`, `720p`, `1080p`, `4K`

---

##  Запуск

### Вимоги

- Python 3.10+
- pytest (для тестів)

```bash
pip install pytest
```

### Демонстрація

```bash
python lms.py
```

### Тести

```bash
pytest test_lms.py -v
```

Очікуваний результат: **58 passed**.

---

##  Приклад використання

```python
from lms import VideoLesson, CourseModule, Course, Student, Certificate

# Створення контенту
video = VideoLesson("Вступ до Python", duration=15,
                    url="https://example.com/intro", resolution="1080p")

# Модуль і курс
module = CourseModule("Основи")
module.add(video)

course = Course("Python з нуля", author="Олена Коваль", price=499.0)
course.add_module(module)

# Студент
student = Student("Тарас Мельник", "taras@example.com")
student.enroll(course)
student.complete_content(course, video)

print(f"Прогрес: {student.progress(course)}%")  # 100.0%

# Сертифікат
cert = Certificate(student, course)
print(cert)
```

---

##  Покриття тестами

| Клас | Тести |
|------|-------|
| Валідатори | 6 |
| `Question` | 5 |
| `Content` | 5 |
| `VideoLesson` | 3 |
| `TextLesson` | 4 |
| `Quiz` | 6 |
| `CourseModule` | 7 |
| `Course` | 9 |
| `Student` | 8 |
| `Certificate` | 5 |
| **Разом** | **58** |
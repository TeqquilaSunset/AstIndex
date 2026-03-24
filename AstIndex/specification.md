# Спецификация: Инструмент структурного поиска кода (AST Index)

**Дата:** 2026-03-22
**Версия:** 1.0
**Статус:** Черновик спецификации

---

## 1. Обзор проекта

### 1.1 Назначение

Инструмент структурного поиска предназначен для индексации кодовой базы и выполнения запросов к структуре программы на основе анализа абстрактных синтаксических деревьев (AST). Система обеспечивает точный поиск синтаксических конструкций, отслеживание связей между элементами кода и предоставление структурированной информации для дополнения контекста ИИ-агентов.

### 1.2 Поддерживаемые языки

- **C#** (C Sharp)
- **Python**
- **JavaScript** (JS)
- **TypeScript** (TS)

### 1.3 Ключевые архитектурные решения

| Решение | Обоснование | Tradeoffs |
|---------|-------------|-----------|
| Полное переписание с нуля | Максимальная гибкость архитектуры | Дольше разрабатывать, потеря существующего опыта |
| Tree-sitter для всех языков | Единый API, высокая скорость | Потеря глубокой семантики, зависимость от upstream |
| Единая SQLite БД на проект | Простота деплоя, универсальные запросы | Сложные миграции, language-agnostic схема |
| Пакетная запись (500 файлов) | 10-50x ускорение индексации | Потеря данных при краше |
| Прагматичные лимиты (10MB) | Защита от edge cases | Неполный индекс больших файлов |
| Fail fast при ошибках | Гарантия корректности | Плохой UX для больших проектов |

---

## 2. Функциональные требования

### 2.1 Категория: Индексация кода

#### FR-1: Автоматическое определение типа проекта
**Приоритет:** Высокий


**Критерии приемки:**
- Определение работает в 95% случаев для стандартных проектов
- Polyglot проекты определяются по доминирующему языку
- Корень проекта определяется как ближайший предок с маркером

#### FR-2: AST парсинг исходного кода
**Приоритет:** Критический

Система должна извлекать следующие синтаксические конструкции:

**Для всех языков:**
- Классы (Classes)
- Интерфейсы (Interfaces)
- Структуры (Structs)
- Функции (Functions)
- Методы (Methods)
- Свойства (Properties/Fields)
- Константы (Constants)
- Пространства имен/Модули (Namespaces/Modules)
- Перечисления (Enums)

**Извлекаемые атрибуты символа:**
- `name` — имя символа
- `kind` — тип символа (Class, Interface, Method, etc.)
- `line` — номер строки объявления
- `signature` — сигнатура с параметрами (без типов для динамических языков)
- `file_id` — ссылка на файл
- `parent_id` — родительский символ (для вложенности)

#### FR-3: Отслеживание наследования
**Приоритет:** Высокий

Система должна отслеживать иерархические отношения:

**Наследование классов:**
- `class UserRepository : Repository` — UserRepository наследует Repository
- Кросс-файловое наследование

**Реализация интерфейсов:**
- `class UserRepo : IRepository, IDisposable` — реализует интерфейсы
- Множественная реализация

**Вложенность:**
- Вложенные классы
- Пространства имен
- Модули

**Хранение:** Таблица `inheritance` с полями:
- `child_id` — ссылка на дочерний символ
- `parent_name` — имя родительского класса/интерфейса
- `kind` — тип наследования (extends, implements)

#### FR-4: Извлечение сигнатур методов
**Приоритет:** Высокий

Система должна извлекать сигнатуры с параметрами:

**Формат для статических языков (C#):**
```csharp
public async Task<Result> ParseFileAsync(string path, Options opts)
```

**Формат для динамических языков (Python):**
```python
def parse_file(path: str, opts: Options) -> Result:
```

**Извлекаемые данные:**
- Имя метода/функции
- Список параметров (имена)
- Типы возвращаемого значения (если указаны)
- Модификаторы (public, private, async, static)

**Ограничения:** Для динамических языков (Python, JS) типы не гарантируются.

#### FR-5: Поддержка нестандартных синтаксических конструкций
**Приоритет:** Средний

**C#:**
- Generic типы: `Repository<T>`
- Attributes: `[HttpGet]`, `[Obsolete]`
- Partial классы
- Records (C# 9+)
- Pattern matching

**Python:**
- Декораторы: `@dataclass`, `@staticmethod`
- Type hints: `Optional[str]`, `List[int]`
- Async/await
- Context managers

**JavaScript/TypeScript:**
- Arrow functions
- Generics (TypeScript)
- Decorators (TypeScript)
- JSX/TSX (опционально)

### 2.2 Категория: Хранение данных

#### FR-6: Реляционная база данных (SQLite)
**Приоритет:** Критический

**Расположение:** `~/.cache/ast-index/{project_hash}/index.db`

**Хеширование:** djb2 алгоритм для детерминированного хеша пути проекта

**Схема базы данных:**

```sql
-- Файлы
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    mtime INTEGER NOT NULL,
    size INTEGER NOT NULL,
    language TEXT NOT NULL  -- 'csharp', 'python', 'javascript', 'typescript'
);

-- Символы (все языки)
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,        -- Class, Function, Method, Interface, etc.
    line INTEGER NOT NULL,
    parent_id INTEGER,         -- Для вложенных символов
    signature TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- FTS5 полнотекстовый поиск
CREATE VIRTUAL TABLE symbols_fts USING fts5(
    name, signature,
    content=symbols,
    content_rowid=id
);

-- Триггеры для FTS5 синхронизации
CREATE TRIGGER symbols_ai AFTER INSERT ON symbols BEGIN
    INSERT INTO symbols_fts(rowid, name, signature)
    VALUES (new.id, new.name, new.signature);
END;

CREATE TRIGGER symbols_ad AFTER DELETE ON symbols BEGIN
    INSERT INTO symbols_fts(symbols_fts, rowid, name, signature)
    VALUES('delete', old.id, old.name, old.signature);
END;

-- Наследование
CREATE TABLE inheritance (
    id INTEGER PRIMARY KEY,
    child_id INTEGER NOT NULL,
    parent_name TEXT NOT NULL,
    kind TEXT,  -- 'extends', 'implements'
    FOREIGN KEY (child_id) REFERENCES symbols(id) ON DELETE CASCADE
);

-- Ссылки на символы (usages)
CREATE TABLE refs (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    symbol_name TEXT NOT NULL,
    line INTEGER NOT NULL,
    context TEXT,  -- Строка кода с использованием
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Метаданные проекта
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Индексы для производительности
CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_kind ON symbols(kind);
CREATE INDEX idx_symbols_file ON symbols(file_id);
CREATE INDEX idx_inheritance_child ON inheritance(child_id);
CREATE INDEX idx_refs_symbol ON refs(symbol_name);
```

#### FR-7: Пакетная запись в БД
**Приоритет:** Высокий

**Настройки:**
- `BATCH_SIZE = 500` файлов
- Параллельный парсинг с rayon (max 8 потоков)
- Пакетная вставка в одной транзакции

**Процесс:**
1. Парсить 500 файлов параллельно
2. Собрать результаты в памяти
3. Открыть транзакцию
4. Вставить все 500 файлов
5. Commit transaction
6. Освободить память
7. Повторить для следующей пачки

**Преимущества:**
- 10-50x ускорение по сравнению с пофайловой записью
- Меньше дисковых I/O
- Управляемое потребление памяти

**Недостатки:**
- Потеря последней пачки при краше процесса

### 2.3 Категория: Поиск и запросы

#### FR-8: Универсальный поиск (search)
**Приоритет:** Критический

**Команда:** `ast-index search <query> [options]`

**Стратегия поиска (трёхуровневая):**

1. **Точный матч:**
   ```sql
   SELECT * FROM symbols WHERE name = 'Repository'
   ```

2. **Префиксный поиск (FTS5):**
   ```sql
   SELECT * FROM symbols_fts
   WHERE name MATCH 'Repos*'
   ```

3. **Частичный поиск (contains):**
   ```sql
   SELECT * FROM symbols WHERE name LIKE '%Repository%'
   ```

**Опции:**
- `--exact` — только точный матч
- `--prefix` — только префиксный поиск
- `--fuzzy` — все три уровня (по умолчанию)
- `--kind Class,Interface` — фильтр по типу символа
- `--lang csharp,python` — фильтр по языку
- `--format json` — JSON вывод
- `--limit 50` — ограничение результатов

**Вывод (JSON):**
```json
{
  "symbols": [
    {
      "name": "UserRepository",
      "kind": "Class",
      "line": 42,
      "file": "src/data/UserRepository.cs",
      "signature": "public class UserRepository : IRepository"
    }
  ],
  "total": 1
}
```

#### FR-9: Поиск типов (class)
**Приоритет:** Высокий

**Команда:** `ast-index class <query> [options]`

**Функциональность:**
- Найти только классы, интерфейсы, структуры, enums
- Фильтр по kind: `--kind Interface,Class,Struct,Trait,Enum`
- Показать наследование: `--show-inheritance`
- Показать потомков: `--show-descendants`

**Пример:**
```bash
ast-index class 'Repository' --show-inheritance
```

**Вывод:**
```
IRepository (Interface)
  ├── UserRepository (Class)
  └── MemoryRepository (Class)
```

#### FR-10: Поиск использований (usages)
**Приоритет:** Высокий

**Команда:** `ast-index usages <symbol> [options]`

**Функциональность:**
- Найти все использования символа (вызовы функций, использования типов)
- Cross-file references
- Опция `--include-declarations` — включить объявления

**Ограничения:** Tree-sitter не даёт полной семантики, поэтому:
- Поиск по имени (string-based)
- Возможны false positives (одноименные символы)
- Не разрешает перегрузки функций

**Пример:**
```bash
ast-index usages 'parseFile' --format json
```

#### FR-11: Поиск иерархии (inheritance)
**Приоритет:** Средний

**Команда:** `ast-index inheritance <symbol> [options]`

**Функциональность:**
- Показать всех наследников класса/интерфейса
- Показать ancestry (предков)
- Опции: `--descendants`, `--ancestors`, `--both`

**Пример:**
```bash
ast-index inheritance 'IRepository' --descendants
```

**Вывод:**
```
IRepository
  └── Repository
      ├── UserRepository
      └── AdminRepository
```

### 2.4 Категория: Инкрементные обновления

#### FR-12: Перепарсинг изменённых файлов
**Приоритет:** Высокий

**Команда:** `ast-index update`

**Процесс:**
1. Получить все файлы из БД с их mtime
2. Просканировать файловую систему
3. Найти изменённые файлы (file_mtime > db_mtime)
4. Найти новые файлы (отсутствуют в БД)
5. Найти удалённые файлы (есть в БД, но отсутствуют на диске)
6. Удалить из БД данные об изменённых/удалённых файлах
7. Перепарсить изменённые и новые файлы
8. Обновить связи

**Ограничения:**
- Не отслеживает move/rename операций (удаляет старое, добавляет новое)
- Каскадное удаление зависимостей (foreign keys)

### 2.5 Категория: Управление

#### FR-13: Пересборка индекса
**Приоритет:** Средний

**Команда:** `ast-index rebuild [--force]`

**Функциональность:**
- Полностью удалить существующий индекс
- Переиндексировать весь проект с нуля
- Опция `--force` — пропустить подтверждение
- File locking для предотвращения параллельной пересборки

#### FR-14: Статистика индекса
**Приоритет:** Низкий

**Команда:** `ast-index stats`

**Вывод:**
```
Index Statistics:
  Files: 1,234
  Symbols: 15,678
    Classes: 456
    Functions: 3,421
    Methods: 8,901
  Inheritance relations: 892
  DB size: 45.6 MB
  Last updated: 2026-03-22 10:42:15
  Languages: C#, Python, TypeScript
```

### 2.6 Категория: AI интеграция

#### FR-15: JSON API для ИИ-агентов
**Приоритет:** Критический

**Формат вывода:** `--format json`

**Все команды поддерживают JSON вывод:**
```bash
ast-index search 'Repository' --format json
ast-index class 'User' --format json
ast-index usages 'parseFile' --format json
ast-index stats --format json
```

**Структура JSON ответа:**
```json
{
  "version": "1.0",
  "command": "search",
  "query": "Repository",
  "results": [...],
  "meta": {
    "total": 42,
    "duration_ms": 8,
    "project_root": "/path/to/project"
  }
}
```

**Преимущества для AI:**
- Структурированные данные
- Мгновенный доступ к контексту
- Понимание связей (наследование, использование)
- Universality для всех языков

---

## 3. Нефункциональные требования

### 3.1 Производительность

#### NFR-1: Скорость индексации
**Требование:** Индексировать 1000 файлов средней сложности (300-500 строк) за < 60 секунд

**Бенчмарки:**
- Small project (< 100 files): < 5 секунд
- Medium project (1k-5k files): < 60 секунд
- Large project (10k+ files): < 10 минут

#### NFR-2: Скорость поиска
**Требование:** Среднее время запроса < 20ms

**Бенчмарки (крупный проект ~29k файлов):**
- `search` (точный матч): < 5ms
- `search` (FTS5 префикс): < 10ms
- `search` (LIKE contains): < 50ms
- `class` (с inheritance): < 20ms
- `usages`: < 30ms

#### NFR-3: Память
**Требование:** Пиковое потребление памяти < 2GB при индексации

**Ограничения:**
- `MAX_FILE_SIZE = 10MB` — пропускать файлы больше
- Пакетная запись для освобождения памяти
- Skip minified файлов (> 1000 символов на строку)

### 3.2 Надёжность

#### NFR-4: Обработка ошибок
**Стратегия:** Fail fast

**Поведение:**
- Синтаксическая ошибка в коде → error + stop
- Ошибка парсера → error + stop
- Out of memory → error + stop
- Пользователь должен исправить ошибку и перезапустить

**Логирование:**
```rust
error!("Failed to parse file: {}", path);
error!("Line {}, column {}: {}", line, col, err_msg);
error!("Fix syntax errors and run 'ast-index rebuild'");
```

#### NFR-5: Конкурентность
**Требование:** Безопасная работа с SQLite из multiple threads

**Реализация:**
- `busy_timeout = 5000ms` для предотвращения "database is locked"
- File locking для rebuild операции
- WAL mode (опционально)

### 3.3 Совместимость

#### NFR-6: Платформы
**Поддерживаемые ОС:**
- Linux (x86_64, aarch64)
- macOS (x86_64, aarch64)
- Windows (x86_64)

#### NFR-7: Дистрибуция
**Метод:** Системные пакеты

**Поддерживаемые менеджеры пакетов:**
- apt (Debian/Ubuntu)
- yum/dnf (Fedora/RHEL)
- Homebrew (macOS/Linux)
- Chocolatey (Windows)
- Scoop (Windows)

**Установка:**
```bash
# Linux (Debian/Ubuntu)
sudo apt install ast-index

# macOS
brew install ast-index

# Windows
choco install ast-index
```

### 3.4 Конфигурация

#### NFR-8: Конфигурационный файл
**Файл:** `.ast-index.yaml` в корне проекта

**Пример:**
```yaml
# Переопределение автоопределения
project_type: csharp  # или python, javascript, typescript

# Дополнительные корни для индексации
roots:
  - "../shared-lib"
  - "../common-modules"

# Исключения (glob patterns)
exclude:
  - "vendor/**"
  - "node_modules/**"
  - "**/dist/**"
  - "**/*.min.js"
  - "**/*.generated.cs"

# Явное указание языков
languages:
  - csharp
  - python

# Игнорировать .gitignore?
no_ignore: false
```

**Приоритет:** CLI flags > config file > auto-detection

### 3.5 Observability

#### NFR-9: Структурированное логирование
**Библиотека:** `tracing` / `env_logger`

**Уровни:**
- `ERROR` — критические ошибки (parse errors, DB errors)
- `WARN` — предупреждения (skipped large files, missing parents)
- `INFO` — прогресс (индексация, обновления)
- `DEBUG` — детальная диагностика (каждый символ)
- `TRACE` — максимально подробно (каждая операция БД)

**Использование:**
```bash
RUST_LOG=ast_index=info ast-index index
RUST_LOG=ast_index=debug ast-index search 'Repository'
```

**Формат лога:**
```log
[2026-03-22T10:42:15Z INFO  ast_index::indexer] Starting indexing...
[2026-03-22T10:42:16Z DEBUG ast_index::parsers] Parsing file: src/main.rs
[2026-03-22T10:42:16Z DEBUG ast_index::parsers] Found 12 symbols
[2026-03-22T10:42:17Z INFO  ast_index::indexer] Indexed 500 files (250 files/sec)
```

---

## 4. UML Диаграммы

Все UML диаграммы находятся в директории `uml/` в формате PlantUML.

### 4.1 Диаграмма вариантов использования

**Файл:** [`uml/uml-use-case.puml`](uml/uml-use-case.puml)

Описывает взаимодействие акторов (ИИ-агент, разработчик, CI/CD система) с системой. Показывает все основные варианты использования: создание индекса, поиск символов, поиск классов, поиск использований, анализ наследования, получение статистики и экспорт в JSON.

### 4.2 Диаграмма компонентов

**Файл:** [`uml/uml-component.puml`](uml/uml-component.puml)

Показывает архитектуру системы на уровне компонентов:
- **CLI** — интерфейс командной строки (clap)
- **Команды** — обработчики команд (management, search, class, usages, inheritance)
- **Основная логика** — индексатор и работа с БД
- **Парсеры** — tree-sitter и парсеры для C#, Python, JS/TS
- **Хранилище** — SQLite с расширением FTS5
- **Конфигурация** — файл .ast-index.yaml

### 4.3 Диаграмма классов

**Файл:** [`uml/uml-class.puml`](uml/uml-class.puml)

Показывает статическую структуру основных классов системы:
- **Symbol** — символ (класс, функция, метод)
- **File** — файл исходного кода
- **Inheritance** — отношение наследования
- **Reference** — ссылка на символ (использование)
- **Database** — интерфейс работы с БД
- **Indexer** — индексатор проекта
- **ParsedFile** — результат парсинга файла

### 4.4 Диаграмма последовательности: Индексация

**Файл:** [`uml/uml-sequence-index.puml`](uml/uml-sequence-index.puml)

Показывает процесс индексации проекта:
1. Пользователь запускает команду `ast-index index`
2. Индексатор сканирует файлы
3. Парсеры обрабатывают файлы (пакетами по 500)
4. База данных сохраняет результаты транзакциями

### 4.5 Диаграмма последовательности: Поиск

**Файл:** [`uml/uml-sequence-search.puml`](uml/uml-sequence-search.puml)

Показывает трёхуровневый поиск символов:
1. Точный матч (SELECT WHERE name = 'Repository')
2. Префиксный поиск через FTS5 (MATCH 'Repos*')
3. Частичный поиск через LIKE (LIKE '%Repository%')

### 4.6 Диаграмма развертывания

**Файл:** [`uml/uml-deployment.puml`](uml/uml-deployment.puml)

Показывает физическое развёртывание системы:
- **Рабочая станция разработчика** — CLI и конфигурация
- **Кэш хранилище** — SQLite база данных
- **Парсеры языков** — tree-sitter для C#, Python, JS/TS
- **CI/CD сервер** — автоматическая индексация

### Рендеринг диаграмм

Для просмотра диаграмм используйте:
- **Онлайн:** https://plantuml.com/ru/online
- **VS Code:** Расширение "PlantUML"
- **IntelliJ IDEA:** Плагин "PlantUML integration"
- **Командная строка:** `plantuml *.puml`

---

## 5. Риски и митигация

### 5.1 Технические риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Tree-sitter не парсит сложный код | Средняя | Высокое | Fallback к regex, graceful degradation с warning |
| ООМ на больших файлах | Средняя | Среднее | MAX_FILE_SIZE = 10MB, streaming parsing |
| Медленная индексация | Низкая | Среднее | Batch writes, rayon parallelism, FTS5 |
| SQLite lock contention | Низкая | Среднее | busy_timeout, WAL mode, file locking |
| False positives в usages | Высокая | Низкое | Документация ограничений, fuzzy поиск |

### 5.2 Архитектурные риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Сложность миграции схемы БД | Средняя | Высокое | Versioning in metadata table, migration scripts |
| Потеря данных при краше (batch) | Средняя | Среднее | Документация rebuild, auto-recovery опция |
| Cross-file resolution не работает | Высокая | Высокое | 80/20 семантика, LSP integration future |

### 5.3 Проектные риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Долгая разработка (с нуля) | Средняя | Высокое | MVP на 2 языках, расширять постепенно |
| Непокрытые edge cases | Высокая | Среднее | Golden tests, real projects testing |
| Сложность CI/CD (multi-package) | Средняя | Низкое | GitHub Actions matrix, стабильный релиз cycle |

---

## 7. Приложение: Справочник команд

### 7.1 Команды индексации

```bash
# Создать индекс
ast-index index [--project-type TYPE] [--root PATH]

# Обновить индекс (инкрементно)
ast-index update

# Пересобрать индекс
ast-index rebuild [--force]

# Статистика
ast-index stats
```

### 7.2 Команды поиска

```bash
# Универсальный поиск
ast-index search <query> [--exact|--prefix|--fuzzy] \
  [--kind KINDS] [--lang LANGS] [--format json] [--limit N]

# Поиск типов
ast-index class <query> [--show-inheritance] [--show-descendants]

# Поиск использований
ast-index usages <symbol> [--include-declarations]

# Поиск наследования
ast-index inheritance <symbol> [--descendants|--ancestors|--both]
```

### 7.3 Конфигурация

```bash
# Создать конфигурационный файл
ast-index init [--type TYPE]

# Показать текущую конфигурацию
ast-index config [--show-path]
```

---

## 8. Глоссарий

| Термин | Определение |
|--------|-------------|
| **AST** | Abstract Syntax Tree — абстрактное синтаксическое дерево |
| **FTS5** | Full-Text Search extension 5 для SQLite |
| **Tree-sitter** | Парсер генератор для создания AST |
| **LSP** | Language Server Protocol — протокол для language servers |
| **Symbols** | Элементы кода: классы, функции, методы, etc. |
| **Usages** | Использования символов в коде (ссылки) |
| **Inheritance** | Отношения наследования и реализации интерфейсов |
| **Индексация** | Процесс построения базы данных из кода |
| **Инкрементное обновление** | Обновление только изменённых файлов |
| **80/20 семантика** | Прагматичный подход: 80% пользы за 20% усилий |

---

**Конец спецификации**

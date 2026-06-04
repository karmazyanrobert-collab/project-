# University Data Platform

Демонстрационная Data Platform для университета без Docker: генерация данных, Bronze/Silver/Gold слои, Data Quality, Feature Store, DuckDB Warehouse, Streaming и Streamlit Dashboard.

Проект подготовлен для запуска в облаке:

- **Streamlit Community Cloud** запускает главный файл `dashboard/app.py`.
- При первом запуске dashboard сам проверяет `data/warehouse.duckdb` и автоматически строит данные через pipeline, если warehouse ещё не создан.
- **GitHub Codespaces** использует `.devcontainer/devcontainer.json`, устанавливает зависимости и пробрасывает порт `8501`.
- Локальный Windows-запуск через `.bat` остаётся доступен, но не обязателен.

## Архитектура

```text
Generated CSV source data
        ↓
Bronze Layer: raw Parquet
        ↓
Data Quality checks
        ↓
Silver Layer: cleaned Parquet
        ↓
Data Quality checks
        ↓
Gold Layer: analytical marts
        ↓
Feature Store: student_features.parquet
        ↓
DuckDB Warehouse: data/warehouse.duckdb
        ↓
Semantic Layer: business metrics
        ↓
Streamlit Dashboard
        ↓
Streaming demo: JSONL events → DuckDB streaming tables
```

## Основные команды

```bash
python -m pip install -r requirements.txt
python run_pipeline.py
python run_tests.py
streamlit run dashboard/app.py
```

> Если `data/warehouse.duckdb` отсутствует, `streamlit run dashboard/app.py` сам запустит pipeline при первом открытии dashboard.

## Streamlit Community Cloud

1. Загрузите репозиторий на GitHub.
2. В Streamlit Community Cloud выберите репозиторий.
3. В поле **Main file path** укажите:

   ```text
   dashboard/app.py
   ```

4. Нажмите **Deploy**.
5. Первый старт может занять больше времени, потому что приложение создаёт `data/`, CSV, Parquet-слои, Feature Store и DuckDB warehouse автоматически.

## GitHub Codespaces

1. Откройте репозиторий на GitHub.
2. Выберите **Code → Codespaces → Create codespace on current branch**.
3. Дождитесь выполнения `postCreateCommand`: зависимости установятся из `requirements.txt`.
4. Запустите dashboard:

   ```bash
   streamlit run dashboard/app.py
   ```

5. Откройте вкладку **Ports** в Codespaces.
6. Найдите порт **8501** с меткой **Streamlit Dashboard**.
7. Если preview не открылся автоматически, нажмите значок глобуса или **Open in Browser**.

## Локальный запуск на Windows

Можно использовать готовые `.bat` файлы:

1. `01_create_venv.bat` — создать виртуальное окружение и установить зависимости.
2. `02_run_pipeline.bat` — вручную построить данные и warehouse.
3. `03_run_dashboard.bat` — открыть Streamlit dashboard.
4. `04_run_streaming.bat` — запустить streaming demo.
5. `05_run_tests.bat` — запустить тесты.

Dashboard также умеет создать warehouse сам, поэтому ручной запуск `02_run_pipeline.bat` не обязателен для демонстрации.

## Что создаётся автоматически

Все runtime-артефакты создаются в относительных папках проекта через `pathlib`:

- `data/source` — сгенерированные CSV.
- `data/bronze` — сырые Parquet-таблицы.
- `data/silver` — очищенные Parquet-таблицы.
- `data/gold` — аналитические витрины.
- `data/features` — Feature Store.
- `data/events` — файловый stream.
- `data/warehouse.duckdb` — аналитический DuckDB warehouse.
- `logs/data_quality_report.csv` — отчёт Data Quality.

Папка `data/` и DuckDB-файл не коммитятся, чтобы Streamlit Cloud и Codespaces создавали свежие демонстрационные данные на первом запуске.

## Тесты

```bash
python run_tests.py
```

Если warehouse или Silver-данные отсутствуют, `run_tests.py` сначала выполнит pipeline, а затем запустит `pytest`.

## Streaming demo

В отдельном терминале запустите:

```bash
python run_streaming_demo.py
```

Producer пишет события в `data/events/event_stream.jsonl`, consumer обновляет таблицы `streaming_events` и `streaming_metrics` в DuckDB. После этого обновите dashboard.

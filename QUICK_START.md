# QUICK START — быстрый запуск проекта

## 1. Запуск через GitHub Codespaces

1. Открой репозиторий на GitHub.
2. Нажми **Code → Codespaces → Create codespace on current branch**.
3. Дождись, пока Codespaces выполнит настройку контейнера. Зависимости установятся автоматически командой из `.devcontainer/devcontainer.json`:

   ```bash
   python -m pip install --upgrade pip && python -m pip install -r requirements.txt
   ```

4. В терминале Codespaces запусти:

   ```bash
   streamlit run dashboard/app.py
   ```

5. Открой вкладку **Ports**.
6. Найди порт **8501** / **Streamlit Dashboard**.
7. Нажми **Open in Browser** или открой preview.
8. Если `data/warehouse.duckdb` ещё нет, dashboard сам запустит pipeline и создаст данные.

Дополнительные команды:

```bash
python run_pipeline.py
python run_tests.py
python run_streaming_demo.py
```

## 2. Деплой через Streamlit Community Cloud

1. Загрузи проект в GitHub-репозиторий.
2. Открой [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Нажми **New app**.
4. Выбери репозиторий и ветку.
5. В поле **Main file path** укажи:

   ```text
   dashboard/app.py
   ```

6. Нажми **Deploy**.
7. При первом запуске приложение автоматически:
   - создаст папку `data/`;
   - сгенерирует CSV-данные;
   - построит Bronze/Silver/Gold слои;
   - построит Feature Store;
   - создаст `data/warehouse.duckdb`;
   - покажет dashboard.

Важно: Docker, Windows и ручная загрузка данных не нужны.

## 3. Локальный запуск через `.bat` на Windows

Если всё-таки нужно запустить проект локально на Windows:

1. Двойной клик по `01_create_venv.bat` — создать `venv` и установить зависимости.
2. Двойной клик по `03_run_dashboard.bat` — открыть dashboard.
3. При первом открытии dashboard сам создаст warehouse.

Можно также вручную выполнить:

1. `02_run_pipeline.bat` — построить данные и warehouse.
2. `04_run_streaming.bat` — запустить streaming demo.
3. `05_run_tests.bat` — запустить тесты.

## 4. Самая короткая команда

После установки зависимостей достаточно:

```bash
streamlit run dashboard/app.py
```

Dashboard сам подготовит данные при первом запуске.

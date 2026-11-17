# Flask LLM Chat (GigaChat)

## Описание

Flask LLM Chat — это простое веб-приложение на Flask для общения с языковой моделью (LLM). Приложение сохраняет историю чата в базе данных SQLite и использует **GigaChat API** от Сбера через OpenAI-совместимый интерфейс.

---

## 1. Требования

Перед началом убедитесь, что у вас установлены:

- Python 3.8 или выше: [скачать Python](https://www.python.org/downloads/)
- Расширение Python в VSCode
- Git (для клонирования репозитория): [скачать Git](https://git-scm.com/downloads)
- Аккаунт **GigaChat** для получения ключа доступа (credentials)

---

## 2. Клонирование репозитория

Откройте терминал или командную строку и выполните:

```bash
git clone https://github.com/Lordounos/flask-llm_sber.git
cd flask-llm_sber
```

---

## 3. Создание виртуального окружения

Чтобы не «засорять» вашу систему, создайте виртуальное окружение:

```bash
python -m venv venv
```

- На **Windows**:
  ```bash
  venv\Scripts\activate
  ```
- На **macOS или Linux**:
  ```bash
  source venv/bin/activate
  ```

**Примечание**: В VSCode можно создать и активировать виртуальное окружение через меню справа внизу или через командную палитру (Ctrl+Shift+P → Python: Create Environment).

> ⚠️ Если у вас ошибка с отключённым выполнением сценариев в Windows, необходимо выполнить следующее:
>
> Открыть Терминал на ПК от Администратора (Windows PowerShell) — правой кн. мыши на кнопке «Пуск» → «Терминал (Администратор)».
>
> Далее пишем в командной строке:
> ```
> Set-ExecutionPolicy RemoteSigned
> ```
> На вопрос отвечаем: `A` (на английской раскладке).

---

## 4. Установка зависимостей

В активированном виртуальном окружении выполните:

```bash
pip install -r requirements.txt
```

---

## 5. Получение ключа API GigaChat

Для работы с GigaChat нужны **credentials** (авторизационные данные):

1. Перейдите в личный кабинет [GigaChat Studio](https://developers.sber.ru/studio/) или [GigaChat API](https://developers.sber.ru/docs/ru/gigachat/api/overview).
2. Создайте проект и получите **Client ID** и **Client Secret**.
3. Закодируйте пару `Client ID:Client Secret` в Base64 — это и есть `GIGACHAT_CREDENTIALS`:
   ```bash
   echo -n "CLIENT_ID:CLIENT_SECRET" | base64
   ```
   (На Windows PowerShell: `[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("CLIENT_ID:CLIENT_SECRET"))`)
4. Создайте файл `.env` в корневой папке проекта и добавьте туда:

```
GIGACHAT_CREDENTIALS=ваш_base64_ключ
GIGACHAT_SCOPE=GIGACHAT_API_PERS
```

> `GIGACHAT_SCOPE` — опционально. По умолчанию используется `GIGACHAT_API_PERS` (для физических лиц). Для юридических лиц укажите `GIGACHAT_API_CORP` или `GIGACHAT_API_B2B` в зависимости от вашего тарифа.

---

## 6. Сертификат Минцифры (обязательно!)

GigaChat API использует TLS-сертификаты, подписанные **корневым сертификатом Минцифры России**. Без него запросы к API будут падать с ошибкой SSL.

### Что нужно сделать:

1. Скачайте корневой сертификат Минцифры:  
   [https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt](https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt)
   (или с [официальной страницы Госуслуг](https://www.gosuslugi.ru/crt)).

2. Переименуйте скачанный файл в **`russian_trusted_root_ca.pem`** и положите его **в корень проекта** (рядом с `models.py`).

3. Убедитесь, что путь к сертификату в `models.py` корректный:
   ```python
   CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "russian_trusted_root_ca.pem")
   ```

> ⚠️ **Не отключайте проверку SSL** (`verify=False`) — это небезопасно и может привести к утечке токенов. Используйте сертификат.

---

## 7. Запуск приложения

Всё готово! Запустите приложение:

```bash
python app.py
```

При первом запуске автоматически создастся база данных SQLite (`site.db`) и таблица `ChatHistory`.

---

## 8. Откройте веб-интерфейс

В браузере перейдите по адресу: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 9. Использование

- Введите текст в поле чата и отправьте.
- Ответ от LLM появится ниже.
- История сообщений сохраняется в БД — при обновлении страницы вы увидите весь чат.

---

## 10. Структура проекта

```
flask-llm_sber/
├── app.py                          # Основной файл Flask-приложения
├── models.py                       # Работа с БД и сервисом GigaChat
├── russian_trusted_root_ca.pem     # Корневой сертификат Минцифры (нужно скачать отдельно)
├── prompts/
│   └── prompt_1.txt                # Системный промпт (роль ассистента)
├── templates/
│   └── index.html                  # HTML-шаблон чата
├── static/                         # Статические файлы (CSS, JS, изображения)
├── requirements.txt                # Список необходимых библиотек
├── .env                            # Переменные окружения (не коммитится!)
└── site.db                         # База данных SQLite (создаётся автоматически)
```

---

## 11. Как это работает

1. `app.py` принимает POST-запрос на `/chat` с сообщением пользователя.
2. `models.py` через `LLMService.chat()`:
   - Получает **access token** GigaChat через OAuth (`get_gigachat_token()`).
   - Создаёт OpenAI-клиент с `base_url="https://api.giga.chat/v1"`.
   - Отправляет запрос с системным промптом и сообщением пользователя.
3. Ответ сохраняется в `ChatHistory` и возвращается клиенту в JSON.

> 🔑 Токен GigaChat живёт 30 минут. В текущей реализации он запрашивается при **каждом** сообщении — для production рекомендуется кэшировать.

---

## 12. Частые проблемы и решения

**1. Не установлен Python**  
→ Проверьте `python --version`. Если не установлен — скачайте с [официального сайта](https://www.python.org/downloads/).

**2. Не работает pip**  
→ Проверьте `pip --version`. Если не установлен — [инструкция по установке pip](https://pip.pypa.io/en/stable/installation/).

**3. Ошибка при запуске app.py**  
→ Убедитесь, что виртуальное окружение активировано и все зависимости установлены.

**4. `FileNotFoundError: Файл .env не найден`**  
→ Создайте `.env` в корне проекта и добавьте `GIGACHAT_CREDENTIALS=...`.

**5. `KeyError: 'GIGACHAT_CREDENTIALS'`**  
→ Переменная не найдена в `.env`. Проверьте имя переменной (регистр важен) и отсутствие лишних пробелов.

**6. `SSLError` / `CERTIFICATE_VERIFY_FAILED`**  
→ Скачайте `russian_trusted_root_ca.pem` (см. раздел 6) и положите рядом с `models.py`. Проверьте, что путь в `CERT_PATH` корректен.

**7. `401 Unauthorized` от GigaChat**  
→ Проверьте `GIGACHAT_CREDENTIALS` — это должна быть строка Base64 от `ClientID:ClientSecret`, а не сам Client Secret.

**8. `403 Forbidden` / `scope` error**  
→ Проверьте `GIGACHAT_SCOPE`. Для физлиц — `GIGACHAT_API_PERS`, для юрлиц — `GIGACHAT_API_CORP`/`GIGACHAT_API_B2B`.

**9. Не открывается страница**  
→ Убедитесь, что приложение запущено, и используйте адрес [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

---

## 13. Безопасность

- ❗ **Никогда не коммитьте файл `.env`** в репозиторий — там лежит ваш секретный ключ.
- Добавьте в `.gitignore`:
  ```
  .env
  venv/
  __pycache__/
  site.db
  *.pyc
  ```
- Сертификат `russian_trusted_root_ca.pem` — публичный, его можно коммитить.

---

## 14. Дополнительные советы

- Для остановки приложения нажмите `Ctrl+C` в терминале.
- Для автоматической перезагрузки при изменениях используется `app.run(debug=True)` — это уже включено в `app.py`.
- Если хотите изменить системный промпт (роль ассистента), измените содержимое файла `prompts/prompt_1.txt` или в `models.py` укажите путь к новому файлу:
  ```python
  llm_1 = LLMService('prompts/prompt_2.txt')
  ```
- Модель задаётся в `models.py` в атрибуте `self.model`. Доступные варианты: `GigaChat-2`, `GigaChat-2-Pro`, `GigaChat-2-Max`, `GigaChat-3-Ultra` (зависит от вашего тарифа).

---

## 15. Лицензия

Проект распространяется под MIT лицензией.

---

**Если что-то не получилось — пишите в ТГ-чат!**

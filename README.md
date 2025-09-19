# Marvel Tribe Home Assistant Integration

Интеграция для Home Assistant, позволяющая управлять часами Marvel Tribe через WebSocket протокол.

## 📁 Структура проекта

```
marvel_tribe/
├── custom_components/marvel_tribe/    # Основная интеграция
│   ├── __init__.py                     # Инициализация
│   ├── const.py                        # Константы
│   ├── config_flow.py                  # Поток настройки
│   ├── coordinator.py                  # Координатор данных
│   ├── websocket_client.py             # WebSocket клиент
│   ├── sensor.py                       # Сенсоры
│   ├── binary_sensor.py                # Двоичные сенсоры
│   ├── button.py                       # Кнопки
│   ├── switch.py                       # Переключатели
│   └── manifest.json                   # Манифест
├── examples/                           # Примеры конфигурации
│   ├── automations.yaml               # Автоматизации
│   ├── scripts.yaml                   # Скрипты
│   └── configuration.yaml             # Конфигурация
├── README.md                          # Документация
├── INSTALL.md                         # Быстрая установка
└── requirements.txt                   # Зависимости
```

## 🎯 Возможности

- ✅ Подключение к часам Marvel Tribe через WebSocket
- ✅ **Полное управление RGB подсветкой** (6 индикаторов, 4 режима, яркость 10-100%)
- ✅ **Управление дисплеем** (яркость LCD 0-100%, полное выключение)
- ✅ **Система будильников** (мониторинг 6 слотов, состояние системы)
- ✅ **Auto-Sleep режим** (включение/выключение, настройка периода)
- ✅ **Аудио управление** (включение/выключение, громкость клавиш/запуска/будильника)
- ✅ **WiFi мониторинг** (статус подключения, SSID, IP адрес, сканирование сетей)
- ✅ **Системная информация** (прошивка, серийный номер, характеристики устройства)
- ✅ Мониторинг батареи (уровень заряда, напряжение, статус зарядки)
- ✅ Синхронизация времени (ручная и автоматическая)
- ✅ Автоматическое переподключение при потере связи

## 📋 Требования

- Home Assistant 2023.1.0 или новее
- Python 3.9+
- Часы Marvel Tribe с доступным WebSocket интерфейсом

## 🚀 Установка

### Способ 1: Ручная установка
1. Скопируйте папку `custom_components/marvel_tribe` в директорию `custom_components` вашего Home Assistant
2. Перезагрузите Home Assistant

## ⚙️ Настройка

1. Перейдите в **Настройки** → **Устройства и службы**
2. Нажмите **Добавить интеграцию**
3. Найдите **Marvel Tribe**
4. Введите IP адрес ваших часов (например: `192.168.0.57`)
5. Нажмите **Отправить**

### Параметры конфигурации

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| **Host** | IP адрес часов Marvel Tribe | `192.168.0.57` |
| **Port** | Порт WebSocket соединения | `80` |
| **Name** | Имя устройства в Home Assistant | `Marvel Tribe Watch` |

## 📱 Доступные сущности

После успешной настройки в Home Assistant появятся **37 сущностей** для полного управления часами:

### 📊 Сенсоры (14 штук)
- `sensor.marvel_tribe_battery_level` - уровень заряда батареи (%)
- `sensor.marvel_tribe_battery_voltage` - напряжение батареи (V)
- `sensor.marvel_tribe_connection_status` - статус подключения
- `sensor.marvel_tribe_last_update` - время последнего обновления
- `sensor.marvel_tribe_device_time` - время на устройстве
- `sensor.marvel_tribe_firmware_version` - версия прошивки
- `sensor.marvel_tribe_ip_address` - IP адрес устройства
- `sensor.marvel_tribe_wifi_ssid` - название WiFi сети
- `sensor.marvel_tribe_rgb_brightness` - яркость RGB подсветки
- `sensor.marvel_tribe_lcd_brightness` - яркость LCD дисплея
- `sensor.marvel_tribe_volume_key` - громкость клавиш
- `sensor.marvel_tribe_language` - язык интерфейса
- `sensor.marvel_tribe_auto_sleep_period` - период auto-sleep
- `sensor.marvel_tribe_active_alarms` - количество активных будильников

### 🔧 Переключатели (4 штуки)
- `switch.marvel_tribe_auto_sync_time` - автоматическая синхронизация времени
- `switch.marvel_tribe_rgb_light` - управление RGB подсветкой
- `switch.marvel_tribe_audio` - управление аудио
- `switch.marvel_tribe_auto_sleep` - режим auto-sleep

### 🎛️ Числовые настройки (6 штук)
- `number.marvel_tribe_rgb_brightness` - яркость RGB (10-100%)
- `number.marvel_tribe_rgb_speed` - скорость RGB эффектов (10-100%)
- `number.marvel_tribe_lcd_brightness` - яркость LCD (0-100%)
- `number.marvel_tribe_volume_key` - громкость клавиш (0-100%)
- `number.marvel_tribe_volume_startup` - громкость запуска (0-100%)
- `number.marvel_tribe_volume_alarm` - громкость будильника (0-100%)

### 🎨 Выбор режимов (1 штука)
- `select.marvel_tribe_rgb_effect` - RGB эффект (Rainbow/Flow/Breath/Mono)

### 🔲 Кнопки (5 штук)
- `button.marvel_tribe_sync_time` - синхронизация времени
- `button.marvel_tribe_ping_device` - проверка связи с устройством
- `button.marvel_tribe_refresh_data` - обновление данных
- `button.marvel_tribe_scan_wifi` - сканирование WiFi сетей
- `button.marvel_tribe_get_device_info` - получение информации об устройстве

### 🔘 Двоичные сенсоры (7 штук)
- `binary_sensor.marvel_tribe_connected` - статус подключения
- `binary_sensor.marvel_tribe_charging` - статус зарядки
- `binary_sensor.marvel_tribe_wifi_connected` - статус WiFi подключения
- `binary_sensor.marvel_tribe_rgb_enabled` - состояние RGB подсветки
- `binary_sensor.marvel_tribe_audio_enabled` - состояние аудио
- `binary_sensor.marvel_tribe_alarm_system` - состояние системы будильников
- `binary_sensor.marvel_tribe_auto_sleep_active` - состояние auto-sleep

## 🔧 Использование

### 🌈 RGB управление

```yaml
# Включение RGB подсветки с настройкой яркости
automation:
  - alias: "Marvel Tribe - Вечерняя RGB подсветка"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: switch.turn_on
        entity_id: switch.marvel_tribe_rgb_light
      - service: select.select_option
        entity_id: select.marvel_tribe_rgb_effect
        data:
          option: "Breath"
      - service: number.set_value
        entity_id: number.marvel_tribe_rgb_brightness
        data:
          value: 40
```

### 💻 Управление дисплеем

```yaml
# Автоматическая регулировка яркости дисплея
automation:
  - alias: "Marvel Tribe - Яркость по времени"
    trigger:
      - platform: time
        at: "22:00:00"  # Вечером
      - platform: time
        at: "07:00:00"  # Утром
    action:
      - service: number.set_value
        entity_id: number.marvel_tribe_lcd_brightness
        data:
          value: >
            {% if now().hour >= 22 or now().hour < 7 %}
              20
            {% else %}
              80
            {% endif %}
```

### 😴 Auto-Sleep режим

```yaml
# Включение auto-sleep на ночь
automation:
  - alias: "Marvel Tribe - Ночной режим"
    trigger:
      - platform: time
        at: "21:30:00"
    action:
      - service: switch.turn_on
        entity_id: switch.marvel_tribe_auto_sleep
      - service: number.set_value
        entity_id: number.marvel_tribe_lcd_brightness
        data:
          value: 10
```

### ⏰ Мониторинг будильников

```yaml
# Уведомление о активных будильниках
automation:
  - alias: "Marvel Tribe - Статус будильников"
    trigger:
      - platform: state
        entity_id: sensor.marvel_tribe_active_alarms
    action:
      - service: notify.persistent_notification
        data:
          message: |
            Активных будильников: {{ states('sensor.marvel_tribe_active_alarms') }}
            Система будильников: {{ 'Включена' if is_state('binary_sensor.marvel_tribe_alarm_system', 'on') else 'Выключена' }}
          title: "Marvel Tribe - Будильники"
```

## 🐛 Устранение неполадок

### Проблема: Интеграция не подключается

**Возможные причины:**
1. Неправильный IP адрес
2. Часы выключены или недоступны
3. Проблемы с сетью

**Решение:**
1. Проверьте IP адрес в веб-интерфейсе часов
2. Убедитесь, что часы подключены к сети
3. Проверьте доступность: `ping 192.168.0.57`

### Проблема: Сущности не обновляются

**Решение:**
1. Перезагрузите интеграцию в настройках
2. Проверьте логи Home Assistant на наличие ошибок
3. Убедитесь, что WebSocket соединение активно

### Проблема: Ошибки в логах

**Решение:**
1. Включите отладочные логи:
```yaml
logger:
  logs:
    custom_components.marvel_tribe: debug
```
2. Проверьте логи на наличие специфических ошибок

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🙏 Благодарности

- Разработчикам Home Assistant
- Сообществу за обратную связь и тестирование
- Проекту Marvel Tribe за создание интересного устройства

---

**Примечание:** Эта интеграция создана для образовательных целей и использования в личных проектах. Убедитесь, что вы соблюдаете все применимые законы и правила при использовании.
# xeno-ads.dat

[![build](https://github.com/why4m3/xeno-adblock-lists/actions/workflows/build.yml/badge.svg)](https://github.com/why4m3/xeno-adblock-lists/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/why4m3/xeno-adblock-lists?label=release)](https://github.com/why4m3/xeno-adblock-lists/releases/latest)

Список блокировки рекламы и трекеров для маршрутизации Xray и hysteria2, собранный под российский интернет. Один файл `geosite`-формата, два тега, обновляется каждый день и перед публикацией проверяется настоящим Xray.

- **`ads`** = HaGeZi Multi Pro + v2fly `category-ads-all` + доменные правила RU AdList, минус белый список. Рекомендуемый.
- **`ads-strict`** = то же, но HaGeZi Pro++ вместо Pro. Жёстче, режет больше партнёрских ссылок.

Главное отличие от `category-ads-all` из привычных `geosite.dat`: ловит российскую рекламу (`adfox.ru`, `ads.vk.ru`, `target.my.com`, `ads.sber.ru`, `adv.ozon.ru` и т.п.) и при этом не ломает переходы по ссылкам из писем и поиска, диплинки банков и маркетплейсов, пуши, чаты поддержки и антифрод при оплате.

| | `geosite.dat` Loyalsoldier, `category-ads-all` | `xeno-ads.dat`, `ads` |
|---|---|---|
| Реклама и трекеры из выборки в 56 доменов | 48 | **52** |
| Задеты хосты, которые нельзя ломать | `googleadservices.com`, `adjust.com`, `a.wb.ru` | `a.wb.ru` |
| Память Xray (RSS, одно правило) | 37,0 МБ | **34,6 МБ** |

## Скачать

| Файл | Ссылка |
|---|---|
| `xeno-ads.dat` | [последний релиз](https://github.com/why4m3/xeno-adblock-lists/releases/latest/download/xeno-ads.dat) |
| `xeno-ads.dat.sha256sum` | [последний релиз](https://github.com/why4m3/xeno-adblock-lists/releases/latest/download/xeno-ads.dat.sha256sum) |
| `ads.txt`, `ads-strict.txt` | плоские списки доменов, удобно искать, почему что-то заблокировано |

Те же файлы лежат в ветке [`release`](https://github.com/why4m3/xeno-adblock-lists/tree/release) (всегда последняя сборка) и в [релизах](https://github.com/why4m3/xeno-adblock-lists/releases) (14 последних). Новая сборка публикуется только если содержимое изменилось.

## Подключение

### Xray (в том числе 3x-ui)

Положить `xeno-ads.dat` рядом с `geosite.dat` (в 3x-ui это `/usr/local/x-ui/bin/`) и добавить правило в `routing.rules` перед остальными:

```json
{
  "type": "field",
  "domain": ["ext:xeno-ads.dat:ads"],
  "outboundTag": "blocked"
}
```

`blocked` здесь outbound типа `blackhole`. Старое правило с `geosite:category-ads-all` лучше убрать, иначе оно вернёт блокировку `googleadservices.com` и `adjust.com`, которые здесь разблокированы сознательно.

Блокировка по домену работает только со sniffing на входящих, причём с `quic`, иначе реклама Google по HTTP/3 пройдёт мимо:

```json
"sniffing": { "enabled": true, "destOverride": ["http", "tls", "quic"], "routeOnly": true }
```

Кнопка обновления geo-файлов в 3x-ui этот файл не трогает (у неё жёсткий список имён), обновлять его нужно отдельно.

### hysteria2

```yaml
acl:
  inline:
    - reject(geosite:ads)
    - direct(all)
  geosite: /etc/hysteria/xeno-ads.dat
```

hysteria читает файл только при старте, поэтому после замены нужен перезапуск. И она сама перекачивает geo-файл со своего источника, если он старше `geoUpdateInterval`: обновляйте файл ежедневно, чтобы его не подменили стандартным.

### Автообновление

Минимальный вариант для cron раз в сутки, после 13:00 UTC:

```sh
#!/bin/sh
set -e
base=https://github.com/why4m3/xeno-adblock-lists/releases/latest/download
dir=/usr/local/x-ui/bin
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cd "$tmp"
curl -fsSLO "$base/xeno-ads.dat.sha256sum"
cmp -s xeno-ads.dat.sha256sum "$dir/xeno-ads.dat.sha256sum" 2>/dev/null && exit 0
curl -fsSLO "$base/xeno-ads.dat"
sha256sum -c xeno-ads.dat.sha256sum
install -m 644 xeno-ads.dat xeno-ads.dat.sha256sum "$dir/"
systemctl restart x-ui
```

Перед заменой стоит прогнать файл через `xray run -test` той же версией, что работает на сервере, и держать прошлую версию для отката.

## Почему такой состав

### Сравнение списков

Проверено 24.10.2026 по самим репозиториям: git-история, ветки `release`, заголовки файлов. «RU» = записи в зонах .ru/.su/.рф/.by/.kz. «Выборка» = сколько из 56 известных рекламных и трекерных доменов блокируется (Яндекс, Mail.ru/VK, российские сети, AppLovin, Unity, ironSource, Vungle, Chartboost, InMobi, Mintegral, Pangle, Google Ads, TikTok). «Ложные срабатывания» = что задевается из хостов, которые нельзя ломать ([`config/critical.txt`](config/critical.txt), плюс кабинеты рекламодателей и редиректы ссылок).

| Список | Формат для Xray | Обновление | Записей | RU | Выборка | Ложные и спорные срабатывания |
|---|---|---|---|---|---|---|
| **Loyalsoldier** v2ray-rules-dat `category-ads-all` | geosite `.dat` | раз в сутки | 200 290 | 1 529 | 48 | `googleadservices.com`, `adjust.com`, `a.wb.ru` |
| **runetfreedom** russia-v2ray-rules-dat `category-ads-all` | geosite `.dat` | релизы каждые 6 ч, **данные стоят с 10.08.2026** | 148 872 | 1 330 | 45 | `googleadservices.com`, `a.wb.ru` |
| **v2fly** domain-list-community `category-ads-all` | `dlc.dat` или плоский `.txt` | несколько раз в сутки | 904 | 112 | 32 | `clck.yandex.ru`, `r.mail.ru`, `googleadservices.com`, `adjust.com`, `ads.vk.com`, `xapi.ozon.ru` |
| **Chocolate4U** Iran-v2ray-rules `category-ads-all` | geosite `.dat` | раз в сутки | 69 119 | 874 | 46 | `ads.vk.com`, `a.wb.ru` |
| **AdGuard DNS filter** | ABP, `\|\|domain^` в `domain:` | несколько раз в сутки | 190 349 | 1 362 | 42 | `www.googleadservices.com`, `app.adjust.com`, `a.wb.ru` |
| **HaGeZi** Light | плоский, wildcard | раз в сутки | 70 378 | 890 | 46 | `ads.vk.com`, `a.wb.ru` |
| **HaGeZi** Multi Normal | то же | то же | 172 593 | 2 347 | 47 | `ads.vk.com`, `a.wb.ru` |
| **HaGeZi** Multi Pro | то же | то же | 208 789 | 2 917 | 50 | `ads.vk.com`, `a.wb.ru` |
| **HaGeZi** Multi Pro++ | то же | то же | 222 535 | 3 124 | 53 | плюс `googleadservices.com`, `adjust.com`, часть партнёрских ссылок |
| **HaGeZi** Ultimate | то же | то же | 246 594 | 3 390 | 53 | плюс телеметрия Windows |
| **OISD** small | плоский, wildcard | несколько раз в сутки | 58 976 | 479 | 40 | `ads.vk.com`, `a.wb.ru` |
| **OISD** big | то же | то же | 236 120 | 1 906 | 45 | `ads.vk.com`, `a.wb.ru`; не режет `ad.doubleclick.net`, `pangle.io` |
| **1Hosts** Lite | плоский, wildcard | **заброшен с 03.09.2026** | 102 259 | 1 018 | 54 | `direct.yandex.ru`, `googleadservices.com`, `adjust.com` |
| **1Hosts** Xtra | то же | то же | 786 172 | 17 200 | 56 | 13 из 100, в том числе **`yastatic.net`** (ломает весь Яндекс), `static.yoomoney.ru`, `id.vk.com`, `xapi.ozon.ru` |
| **StevenBlack** hosts | hosts, только `full:` | раз в несколько дней | 71 493 | 531 | 40 | `www.googleadservices.com`, `app.adjust.com` |
| **RU AdList** (`adservers.txt`) | ABP, в домены переводится малая часть | ежедневно | 8 554 (чистых `\|\|domain^` 1 504) | 3 213 | 6 | `onelink.me` (правило `$third-party`) |
| **EasyList** `easylist_adservers.txt` | ABP | ежедневно | 51 458 | 74 | 9 | нет |
| **`xeno-ads.dat` `ads`** | geosite `.dat` | раз в сутки | 209 711 | 3 324 | **52** | `a.wb.ru`, см. ниже |
| **`xeno-ads.dat` `ads-strict`** | то же | то же | 223 555 | 3 527 | 53 | то же |

### Заметки по источникам

- **HaGeZi** сам собирает несколько сотен источников, включая RU AdList и русский фильтр AdGuard, чистит мёртвые домены и держит свой белый список. Поэтому AdGuard DNS поверх HaGeZi Pro добавляет ещё 108 тыс. записей, но это в основном домены, которые уже не резолвятся.
- **v2fly `category-ads-all`** маленький, но только в нём вручную размечены первичные рекламные хосты российских сервисов: `adfox.ru`, `ads.vk.ru`, `ads.sber.ru`, `adv.ozon.ru`, `ads.wildberries.ru`, `ads-integration.rustore.ru`, `mc.yandex.ru`, `appmetrica.yandex.*`, `target.my.com`. 267 его записей не покрыты HaGeZi Pro, 49 из них российские.
- **Loyalsoldier** заменяет файл v2fly целиком, поэтому российские `@ads`-записи v2fly (тот же `adfox.ru`) в него не попадают.
- **runetfreedom** `geosite_RU.dat`: новые релизы выходят, но данные внутри не менялись с 10.08.2026. Вдобавок фильтр `sed '/t.co/d'` в их сборке срезает каждую строку, где встречается `t?co` (7 269 доменов, например `alb.reddit.com`).
- **1Hosts** не обновляется с 03.09.2026, а Xtra ломает Яндекс и ЮMoney.
- **`a.wb.ru`** (аналитика Wildberries) блокируют все списки, жалоб на поломку не найдено, оставлен.

### Что теряется при переводе ABP-правил в домены

Xray видит только имя хоста (из SNI, HTTP Host или DNS через sniffing), без пути, типа ресурса и страницы, с которой идёт запрос. Поэтому:

- Переводятся только правила `||example.com^` без модификаторов: это ровно `domain:example.com`.
- `||example.com^$third-party` в Xray превратился бы в полную блокировку вместе с самим сайтом. В RU AdList таких правил 6 051 из 7 769, среди них обычные сайты. Сборка их не берёт.
- Правила с путём, `domain=`, `$script`, `$popup`, регулярки по URL, косметика `##` и скриптлеты на уровне маршрутизации невозможны.
- Исключения `@@||...` в одном правиле Xray не выразить, поэтому они вычитаются при сборке через [`config/allowlist.txt`](config/allowlist.txt). Если в списке стоит родитель разрешённого хоста (`domain:adjust.com` при разрешённом `app.adjust.com`), родитель удаляется целиком.
- hosts-файлы блокируют точное имя (`full:`), а Loyalsoldier и runetfreedom переводят их в `domain:`, то есть режут ещё и поддомены.

Вывод: браузерные списки (RU AdList, EasyList) для Xray почти бесполезны, нужны изначально доменные DNS-списки (HaGeZi, AdGuard DNS, OISD).

### Белый список

Принцип: ложное срабатывание хуже пропущенного трекера. Пользователь видит не «рекламы стало меньше», а «у меня не работает банк». Каждая строка [`config/allowlist.txt`](config/allowlist.txt) с причиной, сейчас там:

- редиректы ссылок Яндекса и Mail.ru (ссылки из писем и поиска), `www.googleadservices.com` (переход по рекламному результату Google);
- диплинки Adjust, AppsFlyer, Branch (ссылки из SMS и писем банков и маркетплейсов);
- кабинеты рекламодателей и селлеров VK, Яндекс Директа, Ozon, WB;
- пуш-сервисы и Mindbox (уведомления и бонусы приложений магазинов), онлайн-чат JivoSite;
- антифрод при входе и оплате (FingerprintJS, SEON, HUMAN), без которого банки отвечают капчей по кругу;
- `xapi.ozon.ru`: v2fly пометил его как рекламный по passive DNS, что там на самом деле, не выяснено.

Белый список дополнительно проверен по топ-30k Tranco: всё, что из популярных сайтов задевает только HaGeZi Pro и выглядит для пользователя как поломка, вынесено туда.

## Ограничения

- **YouTube.** Рекламные ролики идут с тех же `googlevideo.com`, что и видео, по домену их не отрезать. Список режет только вспомогательные домены (`googleads.g.doubleclick.net`, `pagead2.googlesyndication.com`). Сам YouTube проверяется в `critical.txt` и не ломается.
- **Реклама с первичных доменов** (лента VK, Дзен, рекомендации внутри приложений маркетплейсов, реклама в Telegram-каналах) приходит с тех же хостов, что и контент.
- **Награды за просмотр в мобильных играх** перестают работать: SDK AppLovin, Unity, ironSource, Mintegral заблокированы.
- **ECH.** Если браузер шифрует SNI (сейчас в основном сайты за Cloudflare), sniffing видит внешнее имя, и доменная блокировка не срабатывает.
- **Аналитика** (Яндекс Метрика, AppMetrica, Firebase Analytics, MyTracker) блокируется вместе с рекламой. Сайты от этого не ломаются.

## Как устроена сборка

```
config/sources.json       источники и состав тегов
config/allowlist.txt      белый список, вычитается из всех тегов
config/critical.txt       хосты, которые нельзя блокировать никогда (сборка падает)
scripts/build_lists.py    скачать, разобрать, слить, вычесть allowlist, проверить critical
scripts/build.sh          всё вместе: build_lists.py, domain-list-community, verify_dat.py
scripts/verify_dat.py     читает готовый .dat, проверяет теги, размер и critical.txt
scripts/xray_smoke.sh     проверка настоящим Xray: конфиг грузится, маршруты верные
scripts/geolib.py         чтение и разбор geosite .dat (protobuf)
.github/workflows/build.yml  ежедневная сборка в 12:17 UTC, после публикации HaGeZi
```

Защиты от плохой сборки:

- у каждого источника `min_entries`: обрезанная загрузка или смена формата роняет сборку;
- `critical.txt` проверяется и до, и после сборки `.dat`;
- файл проверяется настоящим Xray (`XRAY_VERSION` в workflow), рекламные домены должны уйти в `blocked`, критичные нет;
- при любой ошибке ветка `release` не обновляется, и серверы остаются на прошлой версии.

`.dat` собирается официальной утилитой `v2fly/domain-list-community` на зафиксированном коммите (`DLC_COMMIT` в `scripts/build.sh`), она же убирает поддомены, уже покрытые родителем.

Локальная сборка: нужны `python3`, `go` и `git`, дальше `scripts/build.sh`. Результат в `build/publish/`.

## Если что-то сломалось

1. Найти домен в `ads.txt` из [последнего релиза](https://github.com/why4m3/xeno-adblock-lists/releases/latest).
2. Открыть issue с доменом и тем, что именно не работает. Или сразу PR: строка в `config/allowlist.txt` с комментарием, почему; если сервис критичный, ещё и в `config/critical.txt`, чтобы он не сломался снова.
3. После слияния в `main` workflow пересобирает файл сразу.

## Источники

Каждый список остаётся под лицензией своего автора:
[HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists),
[v2fly domain-list-community](https://github.com/v2fly/domain-list-community),
[RU AdList](https://github.com/easylist/ruadlist).
Выборка рекламных (56) и критичных хостов собрана вручную. Это проверка на здравость, а не бенчмарк: на реальном трафике цифры будут другими.

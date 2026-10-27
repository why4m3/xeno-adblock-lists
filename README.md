# xeno-ads.dat

[![build](https://github.com/why4m3/xeno-adblock-lists/actions/workflows/build.yml/badge.svg)](https://github.com/why4m3/xeno-adblock-lists/actions/workflows/build.yml)
[![release](https://img.shields.io/github/v/release/why4m3/xeno-adblock-lists?label=release)](https://github.com/why4m3/xeno-adblock-lists/releases/latest)

Блок-лист рекламы и трекеров для Xray и hysteria2. Один geosite-файл, собирается каждый день. Делал под себя: у меня VPN с клиентами из России, и стандартный `category-ads-all` меня не устроил.

Что с ним не так. Российскую рекламу он пропускает: `adfox.ru`, `target.my.com`, `rs.mail.ru` проходят спокойно. А `googleadservices.com` и `adjust.com` режет. После этого не открываются рекламные ссылки в поиске Google и диплинки из SMS банков. Клиент такое воспринимает как «VPN сломал мне банк», а не как «стало меньше рекламы».

В файле два тега:

- `ads` = HaGeZi Multi Pro + v2fly `category-ads-all` + доменные правила RU AdList, минус мой белый список. Его и ставить.
- `ads-strict` = то же, только HaGeZi Pro++ вместо Pro. Режет больше, в том числе партнёрские ссылки, которыми забиты каналы со скидками. Я его не использую.

Что получилось на моей выборке:

| | Loyalsoldier `category-ads-all` | `xeno-ads.dat:ads` |
|---|---|---|
| Заблокировано из 56 рекламных доменов | 48 | 52 |
| Задето из хостов, которые ломать нельзя | `googleadservices.com`, `adjust.com`, `a.wb.ru` | `a.wb.ru` |
| Память Xray (RSS, одно правило) | 37,0 МБ | 34,6 МБ |

## Скачать

- [xeno-ads.dat](https://github.com/why4m3/xeno-adblock-lists/releases/latest/download/xeno-ads.dat) и [sha256](https://github.com/why4m3/xeno-adblock-lists/releases/latest/download/xeno-ads.dat.sha256sum) из последнего релиза
- `ads.txt` и `ads-strict.txt` там же. Это плоские списки доменов, по ним удобно грепать, если непонятно, почему что-то заблокировано.

Последняя сборка всегда лежит ещё и в ветке [`release`](https://github.com/why4m3/xeno-adblock-lists/tree/release). Релизов хранится 14. Если за день ничего не поменялось, новый не выходит.

## Подключение

### Xray / 3x-ui

Файл кладётся рядом с `geosite.dat`. В 3x-ui это `/usr/local/x-ui/bin/`. Правило в `routing.rules`, поставить повыше:

```json
{
  "type": "field",
  "domain": ["ext:xeno-ads.dat:ads"],
  "outboundTag": "blocked"
}
```

`blocked` тут обычный `blackhole`. Старое правило с `geosite:category-ads-all` уберите, иначе `googleadservices.com` и `adjust.com` снова начнут блокироваться.

Без sniffing на входящих доменная блокировка не работает вообще. И `quic` в нём нужен: без него реклама Google по HTTP/3 идёт мимо.

```json
"sniffing": { "enabled": true, "destOverride": ["http", "tls", "quic"], "routeOnly": true }
```

Кнопка «обновить geo-файлы» в 3x-ui этот файл не обновит. У неё зашит список из шести имён. Так что обновлять придётся самим, пример ниже.

### hysteria2

```yaml
acl:
  inline:
    - reject(geosite:ads)
    - direct(all)
  geosite: /etc/hysteria/xeno-ads.dat
```

Две грабли. hysteria читает файл только при старте, после замены её надо перезапускать. И если файл старше `geoUpdateInterval`, она сама скачает свой стандартный geosite поверх. Поэтому обновляйте ежедневно, тогда до этого не дойдёт.

### Автообновление

Сборка стартует в 12:17 UTC. Cron раз в сутки после 13:00 UTC, минимальный вариант:

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

У себя я перед заменой ещё гоняю файл через `xray run -test` той же версией, что на сервере, и держу прошлый файл для отката. Советую так же.

## Почему такой состав

### Сравнение списков

Смотрел 24.10.2026 прямо в репозиториях: git-история, ветки `release`, заголовки файлов.

Колонка «RU» считает записи в зонах .ru/.su/.рф/.by/.kz. «Выборка» показывает, сколько из 56 рекламных и трекерных доменов блокируется: Яндекс, Mail.ru/VK, российские сети, AppLovin, Unity, ironSource, Vungle, Chartboost, InMobi, Mintegral, Pangle, Google Ads, TikTok. В последней колонке то, что задевается из хостов, которые ломать нельзя ([`config/critical.txt`](config/critical.txt), плюс кабинеты рекламодателей и редиректы ссылок).

| Список | Формат для Xray | Обновление | Записей | RU | Выборка | Ложные и спорные срабатывания |
|---|---|---|---|---|---|---|
| Loyalsoldier v2ray-rules-dat `category-ads-all` | geosite `.dat` | раз в сутки | 200 290 | 1 529 | 48 | `googleadservices.com`, `adjust.com`, `a.wb.ru` |
| runetfreedom russia-v2ray-rules-dat `category-ads-all` | geosite `.dat` | релизы каждые 6 ч, но данные с 10.08.2026 не менялись | 148 872 | 1 330 | 45 | `googleadservices.com`, `a.wb.ru` |
| v2fly domain-list-community `category-ads-all` | `dlc.dat` или плоский `.txt` | несколько раз в сутки | 904 | 112 | 32 | `clck.yandex.ru`, `r.mail.ru`, `googleadservices.com`, `adjust.com`, `ads.vk.com`, `xapi.ozon.ru` |
| Chocolate4U Iran-v2ray-rules `category-ads-all` | geosite `.dat` | раз в сутки | 69 119 | 874 | 46 | `ads.vk.com`, `a.wb.ru` |
| AdGuard DNS filter | ABP, `\|\|domain^` в `domain:` | несколько раз в сутки | 190 349 | 1 362 | 42 | `www.googleadservices.com`, `app.adjust.com`, `a.wb.ru` |
| HaGeZi Light | плоский, wildcard | раз в сутки | 70 378 | 890 | 46 | `ads.vk.com`, `a.wb.ru` |
| HaGeZi Multi Normal | то же | то же | 172 593 | 2 347 | 47 | `ads.vk.com`, `a.wb.ru` |
| HaGeZi Multi Pro | то же | то же | 208 789 | 2 917 | 50 | `ads.vk.com`, `a.wb.ru` |
| HaGeZi Multi Pro++ | то же | то же | 222 535 | 3 124 | 53 | плюс `googleadservices.com`, `adjust.com`, часть партнёрских ссылок |
| HaGeZi Ultimate | то же | то же | 246 594 | 3 390 | 53 | плюс телеметрия Windows |
| OISD small | плоский, wildcard | несколько раз в сутки | 58 976 | 479 | 40 | `ads.vk.com`, `a.wb.ru` |
| OISD big | то же | то же | 236 120 | 1 906 | 45 | `ads.vk.com`, `a.wb.ru`; не режет `ad.doubleclick.net`, `pangle.io` |
| 1Hosts Lite | плоский, wildcard | заброшен с 03.09.2026 | 102 259 | 1 018 | 54 | `direct.yandex.ru`, `googleadservices.com`, `adjust.com` |
| 1Hosts Xtra | то же | то же | 786 172 | 17 200 | 56 | 13 из 100, в том числе `yastatic.net` (без него не работает весь Яндекс), `static.yoomoney.ru`, `id.vk.com`, `xapi.ozon.ru` |
| StevenBlack hosts | hosts, только `full:` | раз в несколько дней | 71 493 | 531 | 40 | `www.googleadservices.com`, `app.adjust.com` |
| RU AdList (`adservers.txt`) | ABP, в домены переводится малая часть | ежедневно | 8 554 (чистых `\|\|domain^` 1 504) | 3 213 | 6 | `onelink.me` (правило `$third-party`) |
| EasyList `easylist_adservers.txt` | ABP | ежедневно | 51 458 | 74 | 9 | нет |
| `xeno-ads.dat` `ads` | geosite `.dat` | раз в сутки | 209 711 | 3 324 | 52 | `a.wb.ru` |
| `xeno-ads.dat` `ads-strict` | то же | то же | 223 555 | 3 527 | 53 | то же |

### Пара слов про источники

HaGeZi сам собирает несколько сотен списков, RU AdList и русский фильтр AdGuard среди них. Мёртвые домены он чистит, белый список у него свой. Я пробовал добавить сверху AdGuard DNS. Вышло плюс 108 тысяч записей, почти все давно не резолвятся. В `sources.json` он остался, но ни в один тег не входит: если нужен, это одна строка.

v2fly `category-ads-all` крошечный, 904 записи. Но только там кто-то руками разметил рекламные хосты наших сервисов: `adfox.ru`, `ads.vk.ru`, `ads.sber.ru`, `adv.ozon.ru`, `ads.wildberries.ru`, `ads-integration.rustore.ru`, `mc.yandex.ru`, `appmetrica.yandex.*`, `target.my.com`. 267 его записей HaGeZi Pro не покрывает, 49 из них российские. Loyalsoldier, кстати, этот файл подменяет своим целиком, и `adfox.ru` у него поэтому нет.

runetfreedom выпускает `geosite_RU.dat` каждые 6 часов, а данные внутри не меняются с 10 августа. Там ещё баг: в сборке стоит `sed '/t.co/d'`, и он вырезает любую строку, где встречается `t?co`. Это 7 269 доменов, например `alb.reddit.com`.

1Hosts заброшен с 3 сентября. Xtra к тому же ломает Яндекс и ЮMoney.

`a.wb.ru` (аналитика Wildberries) режут вообще все. Жалоб на поломку я не нашёл, так что оставил.

### Что теряется при переводе ABP-правил в домены

Xray знает только имя хоста. Его он берёт из SNI, заголовка Host или DNS-запроса. Пути, типа ресурса и страницы-источника он не видит. Отсюда ограничения:

- Без потерь переводятся только `||example.com^` без модификаторов, это ровно `domain:example.com`.
- `||example.com^$third-party` в Xray стал бы блокировкой всего сайта целиком. В RU AdList таких правил 6 051 из 7 769, и среди них есть обычные сайты. Я их не беру.
- Правила с путём, `domain=`, `$script`, `$popup`, регулярки по URL, косметика `##` и скриптлеты выкидываются. На уровне маршрутизации их просто нечем выразить.
- Исключения `@@||...` одним правилом Xray не записать. Поэтому я вычитаю их при сборке через [`config/allowlist.txt`](config/allowlist.txt). Если в списке стоит родитель разрешённого хоста (`domain:adjust.com`, а разрешён `app.adjust.com`), родитель удаляется целиком.
- hosts-файлы блокируют точное имя, то есть `full:`. Loyalsoldier и runetfreedom переводят их в `domain:` и заодно режут все поддомены.

Короче, браузерные списки вроде RU AdList и EasyList для Xray почти бесполезны. Нужны те, что изначально доменные: HaGeZi, AdGuard DNS, OISD.

### Белый список

Тут я исхожу из простого. Пропущенный трекер никто не заметит, а сломанную оплату заметят сразу. Поэтому в [`config/allowlist.txt`](config/allowlist.txt) у каждой строки написано, зачем она там. Сейчас там:

- редиректы ссылок Яндекса и Mail.ru, иначе не открываются ссылки из писем и поиска;
- `www.googleadservices.com`, через него идёт клик по рекламному результату Google;
- диплинки Adjust, AppsFlyer, Branch, на них ссылки из SMS и писем банков и маркетплейсов;
- кабинеты рекламодателей и селлеров VK, Директа, Ozon, WB. Те, кто сам даёт рекламу или торгует, без них работать не могут;
- пуш-сервисы и Mindbox, на которых пуши и бонусы магазинных приложений, и онлайн-чат JivoSite;
- антифрод при входе и оплате (FingerprintJS, SEON, HUMAN). Без него банки гоняют по кругу капчу;
- `xapi.ozon.ru`. v2fly пометил его рекламным по passive DNS, а что там на самом деле, я так и не выяснил.

Ещё я прогнал список по топ-30k Tranco. Всё, что из популярных сайтов задевал только HaGeZi Pro и что выглядело бы как поломка, тоже ушло в белый список.

## Чего он не умеет

Рекламу на YouTube он не убирает. Ролики идут с тех же `googlevideo.com`, что и само видео. Режутся только вспомогательные домены вроде `googleads.g.doubleclick.net`. Сам YouTube проверяется в `critical.txt` и не ломается.

Не поможет и с рекламой, которая приходит с основного домена: лента VK, Дзен, рекомендации внутри приложений маркетплейсов, посты в Telegram-каналах.

Награды за просмотр рекламы в мобильных играх работать перестанут. SDK AppLovin, Unity, ironSource и Mintegral заблокированы, ролик просто не загрузится.

Если браузер шифрует SNI через ECH (сейчас это в основном сайты за Cloudflare), sniffing видит только внешнее имя. Блокировка по домену на таких сайтах не срабатывает.

Аналитика вроде Метрики, AppMetrica, Firebase Analytics и MyTracker блокируется вместе с рекламой. Сайтам это не мешает.

## Как собирается

```
config/sources.json       источники и какие теги из чего
config/allowlist.txt      белый список, вычитается из всех тегов
config/critical.txt       хосты, которые блокировать нельзя (если задеты, сборка падает)
scripts/build_lists.py    скачать, разобрать, слить, вычесть allowlist, проверить critical
scripts/build.sh          запускает всё по порядку
scripts/verify_dat.py     читает готовый .dat, проверяет теги, размер и critical.txt
scripts/xray_smoke.sh     прогон настоящим Xray
scripts/geolib.py         разбор geosite .dat (protobuf)
.github/workflows/build.yml  ежедневно в 12:17 UTC, после того как HaGeZi выложит свежую сборку
```

Если что-то пошло не так, сборка падает, и ветка `release` остаётся на прошлой версии. Что считается «не так»:

- источник оказался меньше своего `min_entries` (обрезанная загрузка или сменился формат);
- задет хост из `critical.txt`. Это проверяется дважды, до сборки `.dat` и после;
- настоящий Xray (`XRAY_VERSION` в workflow) отправил рекламный домен не в `blocked` или критичный в `blocked`.

Сам `.dat` собирает официальная утилита `v2fly/domain-list-community`, коммит зафиксирован в `DLC_COMMIT` в `scripts/build.sh`. Она же выкидывает поддомены, которые уже покрыты родителем.

Собрать локально: нужны `python3`, `go` и `git`, дальше `scripts/build.sh`. Результат появится в `build/publish/`.

## Что-то сломалось

Найдите домен в `ads.txt` из [последнего релиза](https://github.com/why4m3/xeno-adblock-lists/releases/latest) и заведите issue: какой домен и что именно не работает. PR тоже подойдёт. Это строка в `config/allowlist.txt` с комментарием, почему её надо пустить. Если сервис важный, добавьте его ещё и в `config/critical.txt`, чтобы он не сломался снова. После мержа в `main` файл пересоберётся сразу.

## Источники

[HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists), [v2fly domain-list-community](https://github.com/v2fly/domain-list-community), [RU AdList](https://github.com/easylist/ruadlist). Лицензии у каждого свои.

Обе выборки, 56 рекламных доменов и критичные хосты, я собирал руками. Это проверка на здравый смысл, не бенчмарк. На реальном трафике цифры будут другими.

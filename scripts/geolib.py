"""Общие функции: разбор списков, сопоставление доменов как в Xray, чтение geosite .dat."""
import re

# domain-list-community принимает только [a-z0-9.-], без подчёркиваний.
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
IPV4_RE = re.compile(r"^\d+\.\d+\.\d+\.\d+$")
ABP_RE = re.compile(r"^\|\|([a-z0-9_.-]+)\^$")


def valid_domain(d):
    return bool(DOMAIN_RE.match(d)) and not IPV4_RE.match(d) and "." in d


def parse_wildcard(text):
    """Домен на строку, покрывает поддомены (HaGeZi wildcard/*-onlydomains, OISD domainswild2)."""
    out, bad = [], 0
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if not line:
            continue
        line = line.removeprefix("*.").removeprefix(".")
        if valid_domain(line):
            out.append(("domain", line))
        else:
            bad += 1
    return out, bad


def parse_abp(text):
    """Только ||domain^ без модификаторов. Остальное (пути, $third-party, domain=,
    косметика, исключения @@) в домен без потерь не переводится и отбрасывается."""
    out, bad = [], 0
    for line in text.splitlines():
        line = line.strip().lower()
        if not line or line[0] in "![":
            continue
        m = ABP_RE.match(line)
        if m and valid_domain(m.group(1)):
            out.append(("domain", m.group(1)))
        else:
            bad += 1
    return out, bad


def parse_hosts(text):
    """hosts-файлы блокируют точное имя, поэтому full:, а не domain:."""
    out, bad = [], 0
    for line in text.splitlines():
        parts = line.split("#", 1)[0].split()
        if len(parts) < 2 or parts[0] not in ("0.0.0.0", "127.0.0.1"):
            continue
        d = parts[1].lower()
        if valid_domain(d):
            out.append(("full", d))
        else:
            bad += 1
    return out, bad


def parse_geosite_plain(text):
    """Плоский экспорт domain-list-community: type:value[:@attr,...]. Атрибуты отбрасываются."""
    out, bad = [], 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        typ, _, rest = line.partition(":")
        if typ in ("domain", "full"):
            value = rest.split(":", 1)[0].lower()
            if valid_domain(value):
                out.append((typ, value))
            else:
                bad += 1
        elif typ in ("regexp", "keyword"):
            value = re.sub(r":@[a-z0-9!,@-]+$", "", rest)
            out.append((typ, value))
        else:
            bad += 1
    return out, bad


PARSERS = {
    "wildcard": parse_wildcard,
    "abp": parse_abp,
    "hosts": parse_hosts,
    "geosite-plain": parse_geosite_plain,
}


class Matcher:
    """Семантика Xray: domain: сам домен и поддомены, full: точное имя,
    keyword: подстрока, regexp: поиск по регулярному выражению."""

    def __init__(self, entries):
        self.domain, self.full, self.keyword, self.regexp = set(), set(), [], []
        for typ, value in entries:
            if typ == "domain":
                self.domain.add(value)
            elif typ == "full":
                self.full.add(value)
            elif typ == "keyword":
                self.keyword.append(value)
            elif typ == "regexp":
                self.regexp.append((value, re.compile(value)))

    def match(self, host):
        if host in self.full:
            return "full:" + host
        labels = host.split(".")
        for i in range(len(labels)):
            cand = ".".join(labels[i:])
            if cand in self.domain:
                return "domain:" + cand
        for k in self.keyword:
            if k in host:
                return "keyword:" + k
        for src, rx in self.regexp:
            if rx.search(host):
                return "regexp:" + src
        return None


def read_hosts_file(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip().lower()
            if line:
                out.append(line)
    return out


def read_rules_file(path):
    """allowlist.txt: domain:x / full:x, без префикса = domain:."""
    out = []
    for line in read_hosts_file(path):
        typ, sep, value = line.partition(":")
        if not sep:
            typ, value = "domain", typ
        if typ not in ("domain", "full") or not valid_domain(value):
            raise ValueError(f"{path}: bad rule {line!r}")
        out.append((typ, value))
    return out


# --- минимальный разбор protobuf для geosite.dat (GeoSiteList) ---

def _varint(b, i):
    r = s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        s += 7
        if c < 0x80:
            return r, i


def _fields(b):
    i, n = 0, len(b)
    while i < n:
        key, i = _varint(b, i)
        f, t = key >> 3, key & 7
        if t == 0:
            v, i = _varint(b, i)
            yield f, v
        elif t == 2:
            ln, i = _varint(b, i)
            yield f, b[i:i + ln]
            i += ln
        elif t == 5:
            i += 4
        elif t == 1:
            i += 8
        else:
            raise ValueError("unsupported wire type %d" % t)


_DAT_TYPES = {0: "keyword", 1: "regexp", 2: "domain", 3: "full"}


def read_dat(path):
    """Возвращает {TAG: [(type, value), ...]}."""
    with open(path, "rb") as f:
        data = f.read()
    result = {}
    for f, site in _fields(data):
        if f != 1:
            continue
        tag, entries = None, []
        for g, v in _fields(site):
            if g == 1:
                tag = v.decode()
            elif g == 2:
                typ, value = 0, b""
                for h, x in _fields(v):
                    if h == 1:
                        typ = x
                    elif h == 2:
                        value = x
                entries.append((_DAT_TYPES.get(typ, str(typ)), value.decode()))
        result[tag.upper()] = entries
    return result

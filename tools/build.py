#!/usr/bin/env python3
"""Podstránky webu Cookpit: podpora, soukromí, podmínky, zrušení předplatného, smazání účtu a 404.

Právní texty se berou z repozitáře aplikace (docs/legal/*.md), aby web a aplikace říkaly totéž.
Úvodní stránku (index.html) skript nemění.

    python3 tools/build.py                     # texty z ~/uvarim/docs/legal
    LEGAL_DIR=/cesta/k/legal python3 tools/build.py

Co ještě chybí doplnit (vlastník, právník), skript vypíše a na stránce to zůstane žlutě označené.
"""
import html
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGAL = Path(os.environ.get('LEGAL_DIR', Path.home() / 'uvarim/docs/legal'))

SITE = 'https://cookpit.spaicestudio.cz'
EMAIL = 'cookpit@spaicestudio.cz'

# Údaje provozovatele doplněné do návrhů z docs/legal
KNOWN = {
    '[NÁZEV FIRMY]': 'Petr Chajda',
    '[IČO]': '23250607',
    '[ADRESA]': 'Průběžná 1033/4, 100 00 Praha 10',
    '[E-MAIL PRO OCHRANU ÚDAJŮ]': EMAIL,
    '[E-MAIL PODPORY]': EMAIL,
}

# Doplní vlastník s právníkem. Dokud je hodnota None, místo zůstane na stránce označené k doplnění.
PENDING = {
    '[DATUM SPUŠTĚNÍ]': None,
}

# Po schválení textů právníkem přepnout na False: zmizí upozornění „Návrh k revizi právníkem“.
DRAFT = False

# Aplikace se dřív jmenovala Uvařím. Návrhy v docs/legal ten název ještě používají.
RENAME = [('Uvařím', 'Cookpit')]

missing = []


def esc(s):
    return html.escape(s, quote=False)


def slug(s):
    s = s.lower()
    for a, b in zip('áčďéěíňóřšťúůýž', 'acdeeinorstuuyz'):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    s = re.sub(r'\b(www\.[a-z0-9.-]+\.[a-z]{2,})\b', r'<a href="https://\1">\1</a>', s)
    s = re.sub(r'\b(reportaproblem\.apple\.com)\b', r'<a href="https://\1">\1</a>', s)
    s = s.replace(EMAIL, f'<a href="mailto:{EMAIL}">{EMAIL}</a>')
    # Co v návrhu zůstalo v hranatých závorkách, je vidět jako místo k doplnění
    def todo(m):
        missing.append(m.group(0))
        return f'<mark class="todo">{m.group(0)}</mark>'
    return re.sub(r'\[[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^\]]*\]', todo, s)


def markdown(text):
    """Stejná malá podmnožina Markdownu jako scripts/web/build.mjs v aplikaci."""
    out, toc = [], []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        h = re.match(r'^(#{1,3}) (.*)', line)
        if h:
            level, title = len(h.group(1)), h.group(2)
            if level == 2:
                hid = slug(title)
                toc.append((hid, title))
                out.append(f'<h2 id="{hid}">{inline(title)}</h2>')
            else:
                out.append(f'<h{level}>{inline(title)}</h{level}>')
            i += 1
        elif line.startswith('> '):
            block = []
            while i < len(lines) and lines[i].startswith('> '):
                block.append(lines[i][2:])
                i += 1
            if DRAFT:
                out.append(f'<aside class="draft">{inline(" ".join(block))}</aside>')
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i])
                i += 1
            cells = lambda r: [c.strip() for c in r.split('|')[1:-1]]
            head, body = rows[0], rows[2:]
            thead = ''.join(f'<th scope="col">{inline(c)}</th>' for c in cells(head))
            tbody = ''.join(
                '<tr>' + ''.join(
                    f'<th scope="row">{inline(c)}</th>' if k == 0 else f'<td>{inline(c)}</td>'
                    for k, c in enumerate(cells(r))
                ) + '</tr>'
                for r in body
            )
            out.append(f'<div class="table"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>')
        elif re.match(r'^(- |\d+\. )', line):
            ordered = bool(re.match(r'^\d+\. ', line))
            items = []
            while i < len(lines) and re.match(r'^(- |\d+\. )', lines[i]):
                items.append(re.sub(r'^(- |\d+\. )', '', lines[i]))
                i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>')
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r'^(#|> |\||- |\d+\. )', lines[i]):
                para.append(lines[i])
                i += 1
            out.append(f'<p>{inline(" ".join(para))}</p>')
    return '\n'.join(out), toc


def legal(name):
    src = (LEGAL / f'{name}.md').read_text(encoding='utf-8')
    for a, b in RENAME:
        src = src.replace(a, b)
    for k, v in {**KNOWN, **{k: v for k, v in PENDING.items() if v}}.items():
        src = src.replace(k, v)
    title = re.search(r'^# (.*)', src, re.M).group(1)
    src = re.sub(r'^# .*\n', '', src, count=1, flags=re.M)
    body, toc = markdown(src)
    # „Účinné od …“ patří pod nadpis jako datum, zbytek odstavce je úvod
    m = re.search(r'<p>(Účinné od (?:\d{1,2}\.\s*){2}\d{4}|Účinné od [^.]+)\.?\s+(.*?)</p>', body)
    meta = ''
    if m:
        meta = f'<p class="meta">{m.group(1)}</p>'
        body = body.replace(m.group(0), f'<p class="lead">{m.group(2)}</p>', 1)
    else:
        body = re.sub(r'<p>', '<p class="lead">', body, count=1)
    return title, meta, body, toc


def page(path, title, main, description, current=None, index=True):
    nav = []
    for href, label, cls in [('/#jak', 'Jak to funguje', 'hide-sm'), ('/#plus', 'Plus', 'hide-sm'), ('/podpora/', 'Podpora', '')]:
        attrs = f' class="{cls}"' if cls else ''
        if current == href:
            attrs += ' aria-current="page"'
        nav.append(f'<a{attrs} href="{href}">{label}</a>')
    head_seo = (
        f'<link rel="canonical" href="{SITE}{path}">'
        if index else '<meta name="robots" content="noindex">'
    )
    return f'''<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{esc(title)} | Cookpit</title>
  <meta name="description" content="{html.escape(description)}">
  {head_seo}
  <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#0c0d0f" media="(prefers-color-scheme: dark)">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="cs_CZ">
  <meta property="og:site_name" content="Cookpit">
  <meta property="og:title" content="{html.escape(title)} | Cookpit">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:url" content="{SITE}{path}">
  <meta property="og:image" content="{SITE}/assets/img/og.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="/favicon.ico" sizes="48x48">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="preload" href="/assets/fonts/red-hat-display-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/red-hat-display-latin-ext.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<!--email_off-->
  <a class="skip" href="#obsah">Přeskočit na obsah</a>

  <header class="top" data-top>
    <div class="wrap top__in">
      <a class="brand" href="/" aria-label="Cookpit, úvod">
        <img src="/assets/img/app-icon.webp" alt="" width="30" height="30">
        <span>Cookpit</span>
      </a>
      <nav aria-label="Hlavní">
        {(chr(10) + ' ' * 8).join(nav)}
      </nav>
    </div>
  </header>

{main}

  <footer class="foot">
    <div class="wrap foot__in">
      <div>
        <a class="brand" href="/"><img src="/assets/img/app-icon.webp" alt="" width="30" height="30" loading="lazy"><span>Cookpit</span></a>
        <address>Provozuje Petr Chajda, IČO 23250607<br>Průběžná 1033/4, 100 00 Praha 10<br><a class="mail" href="mailto:{EMAIL}">{EMAIL}</a></address>
      </div>
      <nav aria-label="Patička">
        <ul>
          <li><a href="/podpora/">Podpora</a></li>
          <li><a href="/soukromi/">Soukromí</a></li>
          <li><a href="/podminky/">Podmínky</a></li>
          <li><a href="/smazani-uctu/">Smazání účtu</a></li>
        </ul>
      </nav>
      <p class="made"><span>© 2026 Petr Chajda</span><span>Navrhlo a vyvinulo <a href="https://spaicestudio.cz">spaice studio</a></span></p>
    </div>
  </footer>

  <script src="/assets/js/site.js" defer></script>
<!--/email_off-->
</body>
</html>
'''


def doc(title, meta, body, toc=None):
    nav = ''
    if toc:
        items = ''.join(f'<li><a href="#{hid}">{inline(t)}</a></li>' for hid, t in toc)
        nav = f'''
      <nav class="toc" aria-label="Obsah stránky">
        <p class="label">Obsah</p>
        <ol>{items}</ol>
      </nav>'''
    grid = 'doc__grid' if toc else 'doc__grid doc__grid--single'
    return f'''  <main id="obsah" class="doc">
    <div class="wrap {grid}">{nav}
      <article>
        <h1>{esc(title)}</h1>
        {meta}
{body}
      </article>
    </div>
  </main>'''


def contact(note):
    return f'''<div class="contact">
          <div><strong>{EMAIL}</strong><span>{note}</span></div>
          <a class="btn btn--ink" href="mailto:{EMAIL}">Napsat e-mail</a>
        </div>'''


def write(rel, text):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding='utf-8')
    print('ok', rel)


# Právní texty z aplikace
for slug_, name, desc in [
    ('soukromi', 'soukromi', 'Jaké údaje Cookpit zpracovává, proč a jaká máš práva.'),
    ('podminky', 'podminky', 'Podmínky používání aplikace Cookpit a předplatného Plus.'),
    ('zruseni', 'zruseni', 'Jak zrušit předplatné Cookpit Plus na iPhonu a na Androidu.'),
]:
    title, meta, body, toc = legal(name)
    write(f'{slug_}/index.html', page(f'/{slug_}/', title, doc(title, meta, body, toc if len(toc) > 3 else None), desc))

# Podpora
faq = [
    ('Funguje Cookpit bez registrace?',
     '<p>Ano. Po spuštění dostaneš anonymní účet bez jména a e-mailu. Přihlásit se přes Apple, Google nebo e-mail můžeš později, hlavně kvůli záloze dat a sdílení s domácností.</p>'),
    ('Kolik stojí Plus?',
     '<p>Základ je zdarma. Plus stojí 599 Kč ročně se 14 dny zdarma, nebo 79 Kč měsíčně se 7 dny zdarma. Platí pro celou domácnost, až pro 6 lidí. Platí cena, kterou ti App Store ukáže před potvrzením nákupu.</p>'),
    ('Jak zruším předplatné?',
     '<p>V nastavení App Store, nejpozději 24 hodin před koncem období. Postup krok za krokem najdeš na stránce <a href="/zruseni/">Jak zrušit předplatné</a>.</p>'),
    ('Jak smažu účet a data?',
     '<p>V aplikaci: <span class="path">Profil → Tvoje data → Smazat účet a data</span>. Data se smažou hned. Víc na stránce <a href="/smazani-uctu/">Smazání účtu</a>.</p>'),
    ('Jak si stáhnu svá data?',
     '<p>V aplikaci: <span class="path">Profil → Tvoje data → Stáhnout moje data</span>.</p>'),
    ('Cena v obchodě je jiná než v aplikaci.',
     '<p>U ceny v aplikaci klepni na „Cena nesedí?“ a dej nám vědět, opravíme ji. Ceny přebíráme z letáků obchodníků s uvedenou platností, v obchodě ale rozhoduje cena na místě.</p>'),
    ('Jak pozvu domácnost?',
     '<p>V aplikaci: <span class="path">Profil → Pozvat do domácnosti</span>. Druhý člen otevře odkaz, nebo zadá kód v <span class="path">Profil → Mám kód pozvánky</span>.</p>'),
    ('Ze kterých obchodů Cookpit bere akce?',
     '<p>Lidl, Kaufland, Albert, Billa, Penny, Tesco, Globus, Coop Jednota, Norma, Rohlík a Košík. Vybereš si až tři obchody, volitelně i PSČ pro regionální letáky.</p>'),
]
faq_html = '\n'.join(
    f'''          <details>
            <summary>{q}</summary>
            <div>{a}</div>
          </details>''' for q, a in faq
)
support = f'''        <p class="lead">Napiš nám, s čím potřebuješ pomoct. Odpovídáme v pracovní dny do 2 dnů.</p>
        {contact('Podpora aplikace Cookpit')}
        <h2 id="caste-otazky">Časté otázky</h2>
        <div class="faq">
{faq_html}
        </div>
        <h2 id="dokumenty">Dokumenty</h2>
        <ul>
          <li><a href="/soukromi/">Zásady ochrany soukromí</a></li>
          <li><a href="/podminky/">Podmínky používání</a></li>
          <li><a href="/zruseni/">Jak zrušit předplatné</a></li>
          <li><a href="/smazani-uctu/">Smazání účtu</a></li>
        </ul>'''
write('podpora/index.html', page('/podpora/', 'Podpora', doc('Podpora', '', support), 'Pomoc s aplikací Cookpit: kontakt a časté otázky.', current='/podpora/'))

# Smazání účtu (Google Play chce odkaz na web, Apple mazání v aplikaci)
deletion = f'''        <p class="lead">Účet i všechna data smažeš přímo v aplikaci. Nemusíš nám kvůli tomu psát.</p>
        <ol>
          <li>Otevři Cookpit a přejdi do <span class="path">Profilu</span>.</li>
          <li>V části <span class="path">Tvoje data</span> klepni na <span class="path">Smazat účet a data</span> a smazání potvrď.</li>
        </ol>
        <h2 id="co-se-smaze">Co se smaže</h2>
        <p>Účet a s ním profil domácnosti, plán, nákupní seznam, spíž, oblíbené recepty, hodnocení a úspory. Smazání proběhne hned. Fotky lednice mažeme už po přečtení, nejpozději do 24 hodin.</p>
        <p>Když sdílíš domácnost s dalšími lidmi, domácnost jim zůstane a správu převezme člen, který je v ní nejdéle.</p>
        <h2 id="predplatne">Předplatné se smazáním nezruší</h2>
        <p>Plus platíš přes App Store, proto ho zruš tam. Postup najdeš na stránce <a href="/zruseni/">Jak zrušit předplatné</a>.</p>
        <h2 id="export">Než účet smažeš</h2>
        <p>Pokud si chceš data nechat, stáhni si je: <span class="path">Profil → Tvoje data → Stáhnout moje data</span>.</p>
        <h2 id="bez-aplikace">Aplikaci už nemáš?</h2>
        <p>Napiš nám a účet smažeme za tebe. Pokud jsi přihlášený přes Apple, Google nebo e-mail, napiš z adresy, kterou u účtu používáš, ať ho najdeme. Anonymní účet bez přihlášení k nikomu přiřadit nedokážeme; smažeme ho sami po 12 měsících, kdy se k němu aplikace nepřipojí.</p>
        {contact('Žádost o smazání účtu')}'''
write('smazani-uctu/index.html', page('/smazani-uctu/', 'Smazání účtu', doc('Smazání účtu', '', deletion), 'Jak smazat účet Cookpit a všechna data.'))

# 404: na GitHub Pages zároveň záložní stránka pro odkazy na pozvánky a recepty, když aplikace není nainstalovaná
not_found = '''  <main id="obsah">
    <section class="handoff" data-handoff="chyba">
      <div class="wrap handoff__in">
        <img class="art" src="/assets/img/i-plan.webp" alt="" width="160" height="160">
        <h1>Tady nic není</h1>
        <p>Stránka neexistuje nebo se přesunula.</p>
        <a class="more-link" href="/">Zpět na úvod</a>
      </div>
    </section>

    <section class="handoff" data-handoff="pozvanka" hidden>
      <div class="wrap handoff__in">
        <img class="art" src="/assets/img/i-family.webp" alt="" width="160" height="160">
        <h1>Pozvánka do domácnosti</h1>
        <div data-invite-code>
          <div data-invite-valid hidden>
            <p>Otevři odkaz v telefonu, kde máš Cookpit. Když se aplikace neotevře, zadej kód ručně.</p>
            <p class="code"><span data-code></span><button type="button" data-copy>Kopírovat</button></p>
            <ol>
              <li>Otevři Cookpit a přejdi do Profilu.</li>
              <li>Klepni na Mám kód pozvánky.</li>
              <li>Vlož kód a potvrď.</li>
            </ol>
          </div>
          <p data-invite-invalid hidden>Odkaz na pozvánku je neúplný. Popros toho, kdo tě zve, ať ti ho pošle znovu.</p>
        </div>
        <a class="more-link" href="/">Co je Cookpit</a>
      </div>
    </section>

    <section class="handoff" data-handoff="recept" hidden>
      <div class="wrap handoff__in">
        <img class="art" src="/assets/img/i-pot.webp" alt="" width="160" height="160">
        <h1>Recept z aplikace Cookpit</h1>
        <p>Někdo ti poslal recept. Otevři odkaz v telefonu, kde máš Cookpit, a recept se ukáže v aplikaci.</p>
        <a class="more-link" href="/">Co je Cookpit</a>
      </div>
    </section>
  </main>

  <script>
    (function () {
      var first = location.pathname.split('/').filter(Boolean)[0];
      var shown = first === 'pozvanka' || first === 'recept' ? first : 'chyba';
      document.querySelectorAll('[data-handoff]').forEach(function (s) { s.hidden = s.dataset.handoff !== shown; });
      if (shown === 'pozvanka') document.title = 'Pozvánka do domácnosti | Cookpit';
      if (shown === 'recept') document.title = 'Recept | Cookpit';
    })();
  </script>'''
write('404.html', page('/404.html', 'Stránka nenalezena', not_found, 'Stránka nenalezena.', index=False))

if missing:
    print('\nK doplnění (vlastník, právník):', file=sys.stderr)
    for m in dict.fromkeys(missing):
        print('  ', m, file=sys.stderr)

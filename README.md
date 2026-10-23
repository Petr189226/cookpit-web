# cookpit.spaicestudio.cz

Web aplikace Cookpit. Statický, bez buildu: co je v repozitáři, to se nasadí. Běží na Railway (služba `cookpit` v projektu spaicestudio.cz): `Dockerfile` zabalí soubory do Caddy, `Caddyfile` řeší hlavičky, cache, záložní stránku pro `/pozvanka/*` a `/recept/*` a typ `apple-app-site-association`. Každý push do `main` web znovu nasadí. DNS popisuje README webu spaicestudio.cz.

| Cesta | Obsah |
|---|---|
| `index.html` | úvodní stránka |
| `podpora/` | kontakt a časté otázky |
| `soukromi/`, `podminky/`, `zruseni/` | zásady ochrany soukromí, podmínky používání, jak zrušit předplatné |
| `smazani-uctu/` | smazání účtu a dat (Google Play chce odkaz na web) |
| `404.html` | neexistující adresy a zároveň záložní stránka pro odkazy `/pozvanka/<kód>` a `/recept/<…>`, když aplikace není nainstalovaná |
| `tools/build.py` | vygeneruje všechny podstránky kromě `index.html` |

## Právní texty

Berou se z repozitáře aplikace (`~/uvarim/docs/legal/*.md`), aby web a aplikace říkaly totéž. Po změně textů:

```bash
python3 tools/build.py
```

Skript vypíše, co ještě chybí doplnit. Na stránkách je to žlutě označené. Hodnoty, které zná jen vlastník (datum spuštění, doby uchování), patří do `PENDING` ve skriptu, nebo rovnou do `docs/legal` v aplikaci. Po schválení textů právníkem přepni `DRAFT = False` a zmizí upozornění „Návrh k revizi právníkem“.

## Pro App Store Connect a Google Play

| Pole | Adresa |
|---|---|
| Support URL | `https://cookpit.spaicestudio.cz/podpora/` |
| Privacy Policy URL | `https://cookpit.spaicestudio.cz/soukromi/` |
| Marketing URL | `https://cookpit.spaicestudio.cz/` |
| Podmínky (odkaz v popisu kvůli předplatnému) | `https://cookpit.spaicestudio.cz/podminky/` |
| Smazání účtu (Google Play) | `https://cookpit.spaicestudio.cz/smazani-uctu/` |

## Universal links (později)

Až bude mít aplikace `EXPO_PUBLIC_WEB_URL=https://cookpit.spaicestudio.cz` a známé Team ID, přidej `.well-known/apple-app-site-association` (vygeneruje ho `apps/web` v repozitáři aplikace). `Caddyfile` ho servíruje jako `application/json`, jak iOS vyžaduje.

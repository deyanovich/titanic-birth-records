# Titanic Birth Records — the birth registry for the passengers of the Titanic

`titanic-birth-records.json` is a fictional but historically careful
reconstruction of **birth records for 1,146 of the 1,309
passengers** of the RMS Titanic — the same passengers as the
classic Kaggle tables (`titanic.csv`, ids 1–891, is included
for convenience).

The point of the dataset is its *shape*. The records come from
eight registration systems, and each archive has the structure
its real-world counterpart had in 1912:

| archive | system | quirks |
|---|---|---|
| `gro` | England & Wales GRO birth index | registration **quarter** only ("1889 Q4"), no father, mother's maiden name, volume/page |
| `irish_parishes` | Irish parish baptismal registers | grouped by parish, prose dates ("15 April 1889"), sponsors, townlands |
| `kyrkobocker` | Scandinavian & Finnish church books | grouped parish → household (farm), patronymics, `-dotter` maiden names, Swedish keys |
| `actes_de_naissance` | French état civil | French keys (`né_le`, `père`, `mère`), witnesses, professions |
| `us_state_records` | US state/county birth records | grouped state → county, informant, file numbers |
| `ottoman_nufus` | Ottoman nüfus registers (Mount Lebanon, Beirut) | **Rumi years** (`year_rumi` + 584 ≈ Gregorian), sparse — mother often missing |
| `matricula_baptizatorum` | Austro-Hungarian Catholic parish registers | **Latin keys** (`nomen`, `pater`, `mater`, `natus`/`nata` by sex), godparents |
| `metricheskie_knigi` | Russian Empire metrical books | **Julian-calendar** dates, patronymics (`otchestvo`), guberniya |

Every record carries a `passenger_id` — at whatever depth its
archive's structure puts it — referring to `PassengerId` in the
Kaggle tables.

## What's hidden inside

The dataset is built for data-wrangling practice, so it ships
with stories to find:

- **The world of 1912.** Lebanon and Syria are Ottoman;
  Croatia and Hungary are one empire; Finland keeps Lutheran
  church books under a Russian grand duchy; married women
  appear in their birth records under their **maiden names**.
- **Missing ages.** 177 passengers in `titanic.csv` have no
  `Age`. Most of them *do* have a birth record. Stop imputing
  the median — go look it up.
- **Age contradictions.** A few dozen passengers lied about
  their age to the shipping line. The registers did not.
- **Families.** Siblings share the same recorded parents —
  including pairs the `SibSp`/ticket columns cannot reveal,
  because one sibling married and boarded under another name.
- **Westernized names.** Some passengers travelled under
  Anglicized names; their records keep the original (the
  documented pattern for Syrian/Lebanese and Russian-Jewish
  emigrants of the period).
- **Calendars.** The metrical books date births in the
  Julian calendar, twelve days behind for these years — and
  one record crosses New Year in translation, so even its
  *year* is a coordinate-system artifact.
- **Passengers your table has never heard of.** Several
  hundred records cite `passenger_id`s above 891. They are not
  errors.
- **Coverage gaps.** Passengers born outside the eight
  systems (Belgium, Bulgaria, Greece, Italy, China, the
  Americas outside the US…) have no record at all — archives
  do not cover the world evenly.

Nothing in the JSON reveals survival.

## Files

- `titanic-birth-records.json` — the birth records: 1,146
  entries across the eight archive shapes (UTF-8, one JSON
  document). Every record cites a `passenger_id`; none carries
  survival information.
- `titanic.csv` — the classic Kaggle training table (891
  passengers), unchanged.
- `test.csv` — the classic test split (418 passengers, no
  `Survived`), so the archives can cite passengers beyond
  id 891.
- `titanic3.csv` — Thomas Cason's full 1,309-passenger
  compilation (survival for all, plus `boat`, `body`,
  `home.dest` — the column that anchors each passenger's
  origin). The generator's complete manifest.
- `gen-titanic-birth-records.py` — the seeded, deterministic
  generator (same inputs → same bytes): the dataset's entire
  methodology as reviewable code.
- `births.quarb` — a commented query-fragment library (the
  calendar conversions and per-archive year extraction).

Column-level documentation for all three tables lives on each
file's schema on this page. The two executed companion
notebooks — the Jupyter-kernel and native-session
walkthroughs — are attached as Kaggle notebooks on the
dataset, accompanying the article
[The rest of the iceberg](https://quarb.org/articles/the-rest-of-the-iceberg.html).

Source repository (issues, history, the promote flow):
[github.com/deyanovich/titanic-birth-records](https://github.com/deyanovich/titanic-birth-records),
mirroring
[gitlab.com/quarb/titanic-birth-records](https://gitlab.com/quarb/titanic-birth-records).

## Provenance and license

All birth records are **fiction**, generated from the public
passenger tables; names of parents, sponsors, villages and
registration districts are invented, chosen to be plausible
for the passenger's documented origin. No genealogical claim
is made about any real person.

The synthetic content and the generator are released under
**CC0 1.0**. The classic Titanic passenger tables are included
unchanged from their widely redistributed public copies.

**Cite as:** B. Durickovic, *Titanic Birth Records* (fictional,
generated), Kaggle, 2026 —
kaggle.com/datasets/deyanovich/titanic-birth-records.

Made as a companion to the Quarb query language's article
*The Rest of the Iceberg* — see
[quarb.org/articles/](https://quarb.org/articles/) — but the
dataset is tool-agnostic: point pandas, jq, DuckDB, or
anything else at it and see how far you get before you miss a
tree-shaped query language.

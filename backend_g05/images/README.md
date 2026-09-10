# G05 Bild-Logik

Die G05-Bilder sind einfacher aufgebaut als G73, aber ebenfalls mit klarer Benennung.

## Außenbilder

Format:

{FARBE}_{VARIANTE}_{SEITE}.jpg

Beispiele:
- 475_front.jpg
- 475_rear.jpg
- 475_authority_front.jpg
- 475_authority_rear.jpg

### Bedeutung der Teile
- FARBE = aktuell nur 475
- VARIANTE = authority oder normale Variante
- SEITE = front oder rear

## Innenbilder

Format:

{LEDER}_{SEITE}.jpg

Beispiele:
- VASW_interior_1.jpg
- KPSW_interior_2.jpg

### Bedeutung der Teile
- LEDER = Innenfarbe / Ausstattung, z. B. VASW, KPSW
- SEITE = Innenansicht

## Logik im Code

In [backend_g05/excel_builder.py](../excel_builder.py) wird die Auswahl so gemacht:

1. Nur Farbcode 475 wird als Außenbild aktiv
2. Wenn 141 oder 144 in der Sicherheitsliste ist, wird die authority-Version gewählt
3. Wenn Innenfarbe VASW oder KPSW ist, wird das passende Innenbild geladen

Damit ist schnell nachvollziehbar, welche Bild-Datei zu welcher Fahrzeuglogik gehört.

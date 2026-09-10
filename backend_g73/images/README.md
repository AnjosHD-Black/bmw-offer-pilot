# G73 Bild-Logik

Diese Bilder werden nach einem festen Muster benannt, damit man schnell erkennt, welche Kombination sie darstellen.

## Außenbilder

Format:

{FARBE}_{REIFEN}_{STYLE}_{AUTHORITY_OR_PRIVATE}_{FRONT_OR_REAR}.jpg

Beispiele:
- 475_10X_private_front.jpg
- 475_10X_authority_front.jpg
- 475_10X_346_private_rear.jpg
- 475_10X_7M9_authority_rear.jpg

### Bedeutung der Teile
- FARBE = Fahrzeugfarbe, z. B. 475, C64, C5A, A96
- REIFEN = Reifen-Set, z. B. 10X, 10Y
- STYLE = optionaler Stil-Trigger, z. B. 346 (Chrome Line), 7M9 (Shadow Line)
- AUTHORITY_OR_PRIVATE = Variante je nach Fahrzeugstatus
  - authority = mit Authority/Behörden-Variante
  - private = normale Privatvariante
- FRONT_OR_REAR = Bildseite
  - front = Frontansicht
  - rear = Heckansicht

## Innenbilder

Format:

{LEDER}_{TRIM}_interior_{1|2}.jpg

Beispiele:
- VDMY_43E_interior_1.jpg
- VDSW_4DQ_interior_2.jpg

### Bedeutung der Teile
- LEDER = Innenmaterial / Lederfarbe, z. B. VDMY, VDSW, VDF2, VDFU
- TRIM = Innenausstattung / Trim, z. B. 43E, 43B, 43D, 4DQ
- interior_1 / interior_2 = erste oder zweite Innenansicht

## Logik im Code

In [backend_g73/excel_builder.py](../excel_builder.py) wird die Bilddatei nach diesen Regeln ausgewählt:

1. Farbe muss in der Farbenliste aus [backend_g73/image_mappings_g73.json](../image_mappings_g73.json) stehen
2. Reifen muss in der Reifenliste stehen
3. Wenn 141 oder 144 im Sicherheitsbereich vorhanden ist, wird authority verwendet
4. Wenn 346 oder 7M9 vorhanden ist, wird die passende Style-Variante gewählt
5. Für Innenbilder wird Leder + Trim kombiniert

Damit sieht ein Kollege auf einen Blick:
- welche Farbe gemeint ist
- ob es private oder authority ist
- ob Chrome Line oder Shadow Line aktiv ist
- ob vorne oder hinten / Innenansicht 1 oder 2 gemeint ist

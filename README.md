# Harrastuskalenteri

Home Assistant -custom integraatio perheen harrastuskalentereiden kokoamiseen.

## Ominaisuudet

- Hakee valittavaksi Google Calendar -integraation kalenterientiteetit.
- Kalentereita voi liittää lapsille: Elias, Amanda, Lydia, Linda ja Linnea.
- Luo jokaiselle lapselle sensorin.
- Sensorin attribuuteissa näkyvät tämän päivän tapahtumat: nimi, alku, loppu, paikka ja lähdekalenteri.

## Asennus HACS:n kautta

1. Tee GitHub-reposta public.
2. HACS → kolmen pisteen valikko → Custom repositories.
3. Lisää repo: `https://github.com/jokkee1-max/harrastuskalenteri`
4. Tyyppi: Integration.
5. Asenna Harrastuskalenteri.
6. Käynnistä Home Assistant uudelleen.
7. Settings → Devices & services → Add integration → Harrastuskalenteri.
8. Valitse lapsille oikeat Google-kalenterit.

## Sensorit

Integraatio luo sensorit esimerkiksi:

- `sensor.elias_harrastukset`
- `sensor.amanda_harrastukset`
- `sensor.lydia_harrastukset`
- `sensor.linda_harrastukset`
- `sensor.linnea_harrastukset`

Sensorin tila on päivän ensimmäisen tapahtuman nimi tai `Ei harrastuksia`.
Kaikki päivän tapahtumat löytyvät `events`-attribuutista.

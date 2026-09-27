# Harrastuskalenteri v0.4.1

## Uutta
- Kaikki `notify.mobile_app_*` puhelimet löytyvät automaattisesti.
- Jokaiselle puhelimelle oma ON/OFF-kytkin ilmoituksia varten.
- Alku- ja hakumuistutusten ajat säädettävissä dashboardilta.
- Tänään, Huomenna ja Seuraavat päivät.
- Aikatauluristiriitojen tunnistus 30 min puskurilla.
- Kalenteritapahtumasta talteen:
  - otsikko
  - alku ja loppu
  - paikka / osoite
  - koko kuvaus
  - tiivistetty lisätieto
  - `Kyyti:` / `Kuljetus:` tieto
  - ensimmäinen URL sekä kaikki URL:t
  - lähdekalenteri
- MyClub-tyyppinen URL voidaan avata dashboardilta ja notifikaatiosta.

## Huomio
Kalenterin koko kuvaus säilytetään attribuuteissa, mutta pelaajalistaa ei näytetä oletusnäkymässä.


## v0.4.1
- Korjattu olemassa olevan integraation lataus: config flow -versionumero palautettu arvoon 1, jolloin Home Assistant ei yritä puuttuvaa migraatiota.

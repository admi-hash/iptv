# Custom 620-channel playlist

Hand-picked from this repo's streams plus the Pluto TV (US/UK/ES/MX/AR), Roku and Samsung TV Plus
line-ups: UK/IE, Spain, Latin America, US and international news, classic cartoons, anime, movies,
series, documentaries and lifestyle. Only official / FAST sources; every stream speed-tested
(start-up under 3 s, download comfortably faster than playback) and every channel matched to a
TV guide with at least 12 hours of real programme data.

- Playlist: `https://raw.githubusercontent.com/admi-hash/iptv/master/custom/channels.m3u`
- Guide (XMLTV): `https://raw.githubusercontent.com/admi-hash/iptv/guide/guide.xml.gz`

The guide is rebuilt every 4 hours by `.github/workflows/refresh-guide.yml` from
i.mjh.nz (Pluto/Plex/Roku) and epgshare01, filtered to the `tvg-id`s in `channels.m3u`.
The free sources only cover the next 15–48 hours, so the refresh has to keep running.

## Jellyfin

Dashboard → Live TV:

1. Tuner devices → add **M3U Tuner** → the playlist URL above.
2. TV guide data providers → add **XMLTV** → the guide URL above.
3. Scheduled tasks → **Refresh Guide** → add an interval trigger of 4–6 hours.

## Editing

Edit `channels.m3u` (keep each channel's `tvg-id`); the push re-runs the guide build.
`python3 refresh_guide.py channels.m3u guide.xml.gz` rebuilds the guide locally.

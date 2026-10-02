# Custom IPTV playlist (608 channels)

Free, official streams (Pluto TV, Roku, Samsung TV Plus, broadcasters) for UK/IE, Spain,
Latin America, US and international news, cartoons, anime, movies, series, documentaries,
lifestyle and travel. Every stream is speed-tested and every channel has a TV guide.

- Playlist: `https://raw.githubusercontent.com/admi-hash/iptv/master/custom/channels.m3u`
- Guide (XMLTV): `https://raw.githubusercontent.com/admi-hash/iptv/guide/guide.xml.gz`

`.github/workflows/refresh-guide.yml` rebuilds the guide every 4 hours with
`custom/refresh_guide.py`: it pulls i.mjh.nz and epgshare01 XMLTV, keeps only the playlist's
`tvg-id`s and the next 36 hours, and strips everything a guide doesn't show. The result is
force-pushed to the `guide` branch so the history doesn't grow.

## Jellyfin

Dashboard → Live TV:

1. Tuner devices → **M3U Tuner** → the playlist URL.
2. TV guide data providers → **XMLTV** → the guide URL.
3. Scheduled tasks → **Refresh Guide** → interval trigger every 4–6 hours.

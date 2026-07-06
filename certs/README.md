# Screen cast HTTPS certificates

Place the screen cast TLS certificate and private key in this folder using these exact names:

- `screen-cast.crt`
- `screen-cast.key`

When both files exist, `broSmartTV/py/screen_cast.py` will automatically start the screen cast server over HTTPS.

Environment variables still override these defaults:

- `SCREEN_CAST_SSL_CERT`
- `SCREEN_CAST_SSL_KEY`

For LAN screen sharing in browsers, open the HTTPS URL printed by the app after startup.

# Deploy TasteProbe on Render

The repository includes a Docker Blueprint (`render.yaml`) for one free web service.
The full backend is required; static hosting cannot execute the Qloo harness.

1. Sign in at https://dashboard.render.com/ using your own account.
2. Choose New > Blueprint and select Nourhan832/tasteprobe (or its public Git URL).
3. Review the free plan and Docker configuration before creating the service.
4. Enter QLOO_API_KEY privately in Render's secret field. Never paste it into chat.
5. Wait for the build and /health check. Open the URL Render actually assigns.
6. Confirm Live Qloo search, one full discovery round, export, and session deletion.

RENDER_EXTERNAL_URL supplies the HTTPS same-origin check. Keep one instance because
sessions are held in memory. Deploys and restarts erase sessions. Free services may
sleep while idle, so open the app before a judging demo. Credentials remain backend
secrets; do not put them in frontend build settings. The ten-minute ranking cache is
in memory and disappears on restart. Existing upstream and per-instance limits apply.

No public URL is claimed until deployment and its live walkthrough are verified.
Account authentication and secret entry must be performed by the account owner.

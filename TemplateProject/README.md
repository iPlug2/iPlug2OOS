# TemplateProject readme

iPlug2 template project

## Distribution docs

Installer text lives in `installer/*.md` and the user manual lives in `manual/TemplateProject manual.md`. The packaging scripts use Pandoc to generate installer-compatible RTF/TXT files and a PDF manual from those Markdown sources during release builds.

## Web build social media card

When the Wasm build is published to GitHub Pages (Build Wasm workflow), `scripts/make_social_card.js` adds a social media card, so that links to the site shared on Twitter/X, Facebook, Slack, Discord etc. show a screenshot of the plug-in with a title and short description.

The script loads the built plug-in in headless Chromium, screenshots its UI, writes `social-card.png` (1200x630) to the dist folder and adds the Open Graph / Twitter Card `<meta>` tags to `index.html`. Edit `config/TemplateProject-web.json` to customise it:

| Key | Meaning | Default |
| --- | --- | --- |
| `title` | Card title | `PLUG_NAME` |
| `description` | One or two sentences shown under the title | generic text |
| `author` | Line under the title on the image (`""` to hide) | `PLUG_MFR` |
| `url` | Public URL of the site, needed if you use a custom domain | `https://<owner>.github.io/<repo>/` in CI |
| `image` | Path (relative to the project folder) of a ready-made card image to use instead of the generated one | |
| `twitterSite` | `@handle` to attribute the card to | |
| `background`, `foreground` | Colours of the generated image | `#16181d`, `#ffffff` |
| `screenshotDelayMs` | How long to let the UI draw before the screenshot | `1000` |

To try it locally after `./scripts/makedist-wasm.sh off`:

```bash
npm install --no-save --no-package-lock playwright
npx playwright install chromium
node scripts/make_social_card.js --url https://example.com/TemplateProject/
```

Card images must be absolute URLs, so the site URL has to be known at build time (`--url`, `url` in the json or `$SITE_URL`). Social sites cache cards; use their card validators / post inspectors to refresh one.

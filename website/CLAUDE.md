# Website

- Never edit `website/docs/`, `scripts/generate-docs.py` generates it from `website/content/` and the markers in
  `README.md`, `CONTRIBUTING.md` and `CHANGELOG.md`
- `website/content/index.md` is the integration page:
  - sections in the order of the home-assistant.io integration pages
  - covers installation parameters, options, removal, supported devices, entities, data updates, use cases,
    examples, known limitations, troubleshooting
  - examples use placeholder entity IDs, no real meter point numbers
- Design after home-assistant.io:
  - `website/src/css/custom.css` and the wrapped `website/src/theme/TOC/`
  - the integration card in `website/src/components/ProjectInfo/` reads `manifest.json` and `hacs.json`
  - the brand images in `custom_components/netzooe_eservice/brand/` are served from the website root

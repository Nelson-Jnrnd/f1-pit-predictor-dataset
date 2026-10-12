# Replay Explorer mockup asset registry

Reviewed 12 October 2026. Assets below are used in the revised approval PDF, not installed into a production viewer. Predictions are illustrative.

| Local source | Purpose | Source | SHA-256 |
| --- | --- | --- | --- |
| `HAM-2024.png` | Lewis Hamilton, 2024 | [Source](https://github.com/Nelson-Jnrnd/F1_Telemetry_Charts/blob/ae3485d695f07137f6778e03c3437ca1464fb7df/frontend/public/portraits/2024/HAM.png) | `9b1549c999a73004f14767ca6eb6cb29c7d27fd0742566008cec5dbe1aab402c` |
| `medium.svg` | Medium tyre icon | [Source](https://github.com/Nelson-Jnrnd/F1_Telemetry_Charts/blob/ae3485d695f07137f6778e03c3437ca1464fb7df/frontend/public/tyres/tire_M_yellow.svg) | `df8b9a2c0fd881454a58cc3bce1879fdc52eb3e3c1a3031f82db29c16720e2b3` |
| `spain.svg` | catalunya-6; 2024 layout | [Source](https://github.com/f1db/f1db/blob/main/src/assets/circuits/black/catalunya-6.svg) | `7cfcc668fa6cb01c42836552141588d3f9699789e5f1c1a1775d2b636b6bff32` |
| `austria.svg` | spielberg-3; 2024 layout | [Source](https://github.com/f1db/f1db/blob/main/src/assets/circuits/black/spielberg-3.svg) | `53c8a10bbf92d222a73fda2a33b487edc62bdccf22bf09ab736c744f28a42f2f` |
| `britain.svg` | silverstone-8; 2024 layout | [Source](https://github.com/f1db/f1db/blob/main/src/assets/circuits/black/silverstone-8.svg) | `d00f4fa806a0431f3a498b2b3af23826c50fb6e25321f594799d535362196799` |
| `es.svg` | ES country flag | [Source](https://github.com/lipis/flag-icons/blob/main/flags/4x3/es.svg) | `f9cfaff858e95f830733ade9591037b5322dfb5827a53b70956a3d190bb49b9a` |
| `at.svg` | AT country flag | [Source](https://github.com/lipis/flag-icons/blob/main/flags/4x3/at.svg) | `c0e5cb3c1d59fd002afd6e2b0dd03787677ca3c9e7b2321f4af6d9e28256ebcd` |
| `gb.svg` | GB country flag | [Source](https://github.com/lipis/flag-icons/blob/main/flags/4x3/gb.svg) | `c8be1e7208798a4ae692ee1e937065d498bb29e741943f6172b29118b8ed8066` |

Hamilton original source, retained from the season-specific portrait manifest: https://media.formula1.com/content/dam/fom-website/2018-redesign-assets/drivers/2024/LEWHAM01.png. Cached hash matches the manifest. Photography rights are not inferred from the repository code license.

Circuit outlines: Jules Roy / F1DB, CC BY 4.0. Catalunya-6 applies from 2023, Spielberg-3 from 2014 in the modern era, Silverstone-8 from 2010. Country flags: flag-icons, MIT. SVGs were rasterized only for PDF embedding. Original geometry and portrait pixels were not edited.

Runtime imagery remains season-specific with a readable text fallback. A missing image must never block the replay. No circuit or driver likeness is generated.
